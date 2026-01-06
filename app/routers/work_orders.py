import csv
import io
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates

# Try to import pandas for Excel support
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

from app.auth import (
    get_current_active_user,
    require_permission,
    require_permission_cookie,
    require_auth_cookie,
    get_optional_current_user,
    get_current_user_from_cookie,
)
from app.models.user import User
from typing import Optional as OptionalType
from app.services.work_order_service import work_order_service
from app.services.notification_service import NotificationService
from app.services.audit_log_service import (
    log_work_order_created,
    log_work_order_updated,
    log_work_order_completed,
)
from app.utils.sanitization import sanitize_text, sanitize_identifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/work-orders", tags=["work-orders"])
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads/work_orders"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Demo work orders for unauthenticated users
DEMO_WORK_ORDERS = [
    {
        "id": "WO-2024-001",
        "title": "Replace HVAC filters in Building B",
        "asset": "HVAC Unit B-2",
        "priority": "High",
        "status": "In Progress",
        "assigned_to": "Mike Johnson",
        "created_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "description": "Quarterly filter replacement for optimal air quality and system efficiency.",
    },
    {
        "id": "WO-2024-002",
        "title": "Compressor oil change and inspection",
        "asset": "Compressor C-5",
        "priority": "Critical",
        "status": "Overdue",
        "assigned_to": "Sarah Chen",
        "created_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "description": "Emergency maintenance required. Compressor showing signs of oil contamination.",
    },
    {
        "id": "WO-2024-003",
        "title": "Production line calibration",
        "asset": "Production Line A",
        "priority": "Medium",
        "status": "Scheduled",
        "assigned_to": "Alex Rodriguez",
        "created_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "description": "Monthly calibration of production line sensors and equipment.",
    },
    {
        "id": "WO-2024-004",
        "title": "Conveyor belt tension adjustment",
        "asset": "Conveyor System C-1",
        "priority": "Low",
        "status": "Open",
        "assigned_to": "Mike Johnson",
        "created_date": (datetime.now() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "description": "Routine tension check and adjustment for conveyor belt system.",
    },
    {
        "id": "WO-2024-005",
        "title": "Emergency lighting test",
        "asset": "Emergency Systems",
        "priority": "High",
        "status": "Completed",
        "assigned_to": "Sarah Chen",
        "created_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "description": "Quarterly emergency lighting system test and battery check.",
    },
]


@router.get("", response_class=HTMLResponse)
async def work_orders_list(request: Request):
    """Render work orders - demo data for guests, real Firestore data for authenticated"""
    # Use cookie-based auth for web pages
    current_user = await get_current_user_from_cookie(request)

    work_orders = []
    stats = {}

    # Key fix: is_demo should be False for ANY authenticated user (Lesson #8)
    if current_user:
        # Authenticated user - NOT demo mode
        is_demo = False
        if current_user.organization_id:
            # Has organization - show real Firestore data
            try:
                work_order_objects = await work_order_service.get_work_orders(
                    organization_id=current_user.organization_id
                )
                # Convert Pydantic objects to dicts for template compatibility
                work_orders = [wo.model_dump() if hasattr(wo, 'model_dump') else wo.dict() for wo in work_order_objects]
            except Exception as e:
                logger.error(f"Error loading work orders: {e}")
                # Show empty list on error, not demo data (user is still authenticated)
                work_orders = []
        else:
            # Authenticated but no org - show empty list (not demo data)
            work_orders = []
    else:
        # Not authenticated - show demo data
        is_demo = True
        work_orders = DEMO_WORK_ORDERS
        # Create demo user context for template
        current_user = type('obj', (object,), {
            'uid': 'demo',
            'id': 'demo',
            'role': 'technician',
            'full_name': 'Demo Visitor',
            'email': 'demo@chatterfix.com',
            'organization_id': None
        })()

    # Calculate stats
    stats = {
        "total": len(work_orders),
        "in_progress": len([w for w in work_orders if w.get("status") == "In Progress"]),
        "scheduled": len([w for w in work_orders if w.get("status") in ["Scheduled", "Open"]]),
        "overdue": len([w for w in work_orders if w.get("status") == "Overdue"]),
        "completed": len([w for w in work_orders if w.get("status") == "Completed"]),
    }

    return templates.TemplateResponse(
        "work_orders.html",
        {
            "request": request,
            "work_orders": work_orders,
            "stats": stats,
            "user": current_user,
            "current_user": current_user,
            "is_demo": is_demo,
            "demo_mode": is_demo,
        },
    )


@router.get("/{wo_id}", response_class=HTMLResponse)
async def work_order_detail(request: Request, wo_id: str):
    """Render work order details - demo data for guests, real data for authenticated"""
    current_user = await get_current_user_from_cookie(request)

    work_order = None

    # Key fix: is_demo should be False for ANY authenticated user (Lesson #8)
    if current_user:
        # Authenticated user - NOT demo mode
        is_demo = False
        if current_user.organization_id:
            # Has organization - get real work order from Firestore
            work_order = await work_order_service.get_work_order(
                wo_id, organization_id=current_user.organization_id
            )
        if not work_order:
            return RedirectResponse(url="/work-orders", status_code=302)
    else:
        # Not authenticated - show demo work order
        is_demo = True
        # Find demo work order by ID
        work_order = next((wo for wo in DEMO_WORK_ORDERS if wo.get("id") == wo_id), None)
        if not work_order:
            return RedirectResponse(url="/work-orders", status_code=302)
        # Create demo user context
        current_user = type('obj', (object,), {
            'uid': 'demo',
            'id': 'demo',
            'role': 'technician',
            'full_name': 'Demo Visitor',
            'email': 'demo@chatterfix.com',
            'organization_id': None
        })()

    return templates.TemplateResponse(
        "work_order_detail.html",
        {
            "request": request,
            "wo": work_order,
            "media": [],
            "user": current_user,
            "current_user": current_user,
            "is_demo": is_demo,
        },
    )


@router.post("")
async def create_work_order(
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    status: str = Form("Open"),
    assigned_to_uid: Optional[str] = Form(None),
    asset_id: Optional[str] = Form(None),
    work_order_type: str = Form("Corrective"),
    due_date: Optional[str] = Form(None),
    current_user: User = Depends(require_permission_cookie("create_work_order_request")),
):
    """Create a new work order"""
    # Sanitize user inputs to prevent XSS/injection
    safe_title = sanitize_text(title, max_length=200)
    safe_description = sanitize_text(description, max_length=5000, preserve_newlines=True)

    # Validate priority against whitelist
    allowed_priorities = {"Low", "Medium", "High", "Critical"}
    safe_priority = priority if priority in allowed_priorities else "Medium"

    # Validate status against whitelist
    allowed_statuses = {"Open", "In Progress", "On Hold", "Completed", "Cancelled"}
    safe_status = status if status in allowed_statuses else "Open"

    # Validate work order type against whitelist
    allowed_types = {"Corrective", "Preventive", "Emergency", "Inspection", "General"}
    safe_type = work_order_type if work_order_type in allowed_types else "Corrective"

    work_order_data = {
        "title": safe_title,
        "description": safe_description,
        "priority": safe_priority,
        "status": safe_status,
        "assigned_to_uid": sanitize_identifier(assigned_to_uid) if assigned_to_uid else None,
        "asset_id": sanitize_identifier(asset_id) if asset_id else None,
        "work_order_type": safe_type,
        "due_date": due_date,  # Validated by Pydantic/date parsing
    }
    # Multi-tenant: associate work order with user's organization
    wo_id = await work_order_service.create_work_order(
        work_order_data, organization_id=current_user.organization_id
    )

    # Log the work order creation for audit trail
    await log_work_order_created(
        wo_id=wo_id,
        wo_data=work_order_data,
        user_id=current_user.uid,
        user_name=current_user.full_name or current_user.email,
        organization_id=current_user.organization_id,
    )

    # Notification logic would also be in the service layer
    if assigned_to_uid:
        await NotificationService.notify_work_order_assigned(
            work_order_id=wo_id,
            technician_id=assigned_to_uid,
            title=title,
            work_order_data=work_order_data,
        )

    return RedirectResponse(url="/work-orders", status_code=303)


@router.post("/{wo_id}/update")
async def update_work_order(
    wo_id: str,
    title: str = Form(""),
    description: str = Form(""),
    priority: str = Form("Medium"),
    status: str = Form("Open"),
    assigned_to_uid: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    scheduled_time: Optional[str] = Form(None),
    current_user: User = Depends(require_permission_cookie("update_status")),
):
    """Update an existing work order - all fields have defaults for robustness"""
    # First, get the existing work order to preserve values if form fields are empty
    existing_wo = await work_order_service.get_work_order(wo_id, organization_id=current_user.organization_id)
    if not existing_wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    # Convert Pydantic model to dict for easier access
    existing_data = existing_wo.model_dump() if hasattr(existing_wo, 'model_dump') else existing_wo.dict()

    # Convert datetime to string for due_date if needed
    existing_due_date = existing_data.get("due_date")
    if hasattr(existing_due_date, 'strftime'):
        existing_due_date = existing_due_date.strftime("%Y-%m-%d")

    # Sanitize user inputs to prevent XSS/injection
    # Use existing values if form fields are empty (fallback for form issues)
    safe_title = sanitize_text(title, max_length=200) if title else existing_data.get("title", "Untitled")
    safe_description = sanitize_text(description, max_length=5000, preserve_newlines=True) if description else existing_data.get("description", "")

    # Validate priority against whitelist, fallback to existing
    allowed_priorities = {"Low", "Medium", "High", "Critical"}
    safe_priority = priority if priority in allowed_priorities else existing_data.get("priority", "Medium")

    # Validate status against whitelist, fallback to existing
    allowed_statuses = {"Open", "In Progress", "On Hold", "Completed", "Cancelled"}
    safe_status = status if status in allowed_statuses else existing_data.get("status", "Open")

    # If scheduled_time is provided, extract date for due_date (calendar uses due_date)
    effective_due_date = due_date if due_date else existing_due_date
    if scheduled_time:
        # Extract date portion from scheduled_time (format: YYYY-MM-DDTHH:MM)
        effective_due_date = scheduled_time[:10] if len(scheduled_time) >= 10 else effective_due_date

    # Log what we're saving for debugging
    logger.info(f"Updating work order {wo_id}: due_date={effective_due_date}, scheduled_time={scheduled_time}")

    update_data = {
        "title": safe_title,
        "description": safe_description,
        "priority": safe_priority,
        "status": safe_status,
        "assigned_to_uid": sanitize_identifier(assigned_to_uid) if assigned_to_uid else existing_data.get("assigned_to_uid"),
        "due_date": effective_due_date,
        "scheduled_time": scheduled_time if scheduled_time else existing_data.get("scheduled_time"),
    }
    # Multi-tenant: validate work order belongs to user's organization
    await work_order_service.update_work_order(
        wo_id, update_data, organization_id=current_user.organization_id
    )

    # Log the work order update for audit trail
    await log_work_order_updated(
        wo_id=wo_id,
        old_data=existing_data,
        new_data=update_data,
        user_id=current_user.uid,
        user_name=current_user.full_name or current_user.email,
        organization_id=current_user.organization_id,
    )

    # If status changed to Completed, also log completion
    if update_data.get("status") == "Completed" and existing_data.get("status") != "Completed":
        await log_work_order_completed(
            wo_id=wo_id,
            wo_data=update_data,
            user_id=current_user.uid,
            user_name=current_user.full_name or current_user.email,
            organization_id=current_user.organization_id,
        )

    return RedirectResponse(url=f"/work-orders/{wo_id}", status_code=303)


# ==========================================
# ✅ COMPLETE WORK ORDER ENDPOINT
# ==========================================


@router.post("/{wo_id}/complete")
async def complete_work_order(
    request: Request,
    wo_id: str,
    current_user: User = Depends(require_auth_cookie),
):
    """Complete a work order - sets status to Completed"""
    from app.core.firestore_db import get_firestore_manager

    firestore_manager = get_firestore_manager()

    # Get the existing work order
    existing_data = await firestore_manager.get_document("work_orders", wo_id)
    if not existing_data:
        raise HTTPException(status_code=404, detail="Work order not found")

    # Update status to Completed
    update_data = {
        "status": "Completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "completed_by_uid": current_user.uid,
        "completed_by_name": current_user.full_name or current_user.email,
    }

    await firestore_manager.update_document(
        "work_orders", wo_id, update_data
    )

    # Log the completion for audit trail
    await log_work_order_completed(
        wo_id=wo_id,
        wo_data={**existing_data, **update_data},
        user_id=current_user.uid,
        user_name=current_user.full_name or current_user.email,
        organization_id=current_user.organization_id,
    )

    # Update asset's last_maintenance_date if work order is linked to an asset
    asset_id = existing_data.get("asset_id")
    if asset_id:
        try:
            asset_update = {
                "last_maintenance_date": update_data["completed_at"],
                "base_health_score": 100.0,  # Reset health score after maintenance
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await firestore_manager.update_document("assets", asset_id, asset_update)
            logging.getLogger(__name__).info(
                f"Updated asset {asset_id} last_maintenance_date after WO {wo_id} completion"
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating asset after WO completion: {e}")

    return RedirectResponse(url=f"/work-orders/{wo_id}", status_code=303)


# ==========================================
# ✅ ENHANCED COMPLETE WORK ORDER ENDPOINT
# ==========================================


@router.post("/{wo_id}/complete-enhanced")
async def complete_work_order_enhanced(
    request: Request,
    wo_id: str,
    completion_notes: str = Form(""),
    completion_time: str = Form(None),
    labor_hours: float = Form(0),
    current_user: User = Depends(require_auth_cookie),
):
    """
    Enhanced work order completion with notes, parts used, and labor tracking.
    Handles parts checkout and inventory deduction.
    """
    from app.core.firestore_db import get_firestore_manager

    firestore_manager = get_firestore_manager()

    # Get the existing work order
    existing_data = await firestore_manager.get_document("work_orders", wo_id)
    if not existing_data:
        raise HTTPException(status_code=404, detail="Work order not found")

    # Parse form data for parts used and technicians
    form_data = await request.form()
    parts_used = []
    technicians_worked = []

    # Extract technicians from form (completion_technicians[0][technician_id], etc.)
    tech_index = 0
    while True:
        tech_id = form_data.get(f"completion_technicians[{tech_index}][technician_id]")
        if tech_id is None:
            break
        if tech_id:  # Only add if technician was selected
            hours_worked = form_data.get(f"completion_technicians[{tech_index}][hours_worked]", "0")
            try:
                hours = float(hours_worked) if hours_worked else 0
            except ValueError:
                hours = 0

            # Look up technician name from users collection
            tech_data = await firestore_manager.get_document("users", tech_id)
            tech_name = "Unknown"
            if tech_data:
                tech_name = tech_data.get("full_name") or tech_data.get("email", "Unknown")

            technicians_worked.append({
                "technician_id": tech_id,
                "technician_name": tech_name,
                "hours_worked": hours
            })
        tech_index += 1

    # Extract parts from form (completion_parts[0][part_id], completion_parts[0][quantity_used], etc.)
    part_index = 0
    while True:
        part_id = form_data.get(f"completion_parts[{part_index}][part_id]")
        if part_id is None:
            break
        quantity_used = form_data.get(f"completion_parts[{part_index}][quantity_used]")
        if part_id and quantity_used:
            try:
                qty = int(quantity_used)
                if qty > 0:
                    parts_used.append({
                        "part_id": part_id,
                        "quantity_used": qty
                    })
            except ValueError:
                pass
        part_index += 1

    # Process parts checkout - deduct from inventory
    parts_checkout_results = []
    for part in parts_used:
        try:
            # Get current part data
            part_data = await firestore_manager.get_document("parts", part["part_id"])
            if part_data:
                current_stock = part_data.get("current_stock", 0)
                new_stock = max(0, current_stock - part["quantity_used"])

                # Update part stock
                await firestore_manager.update_document(
                    "parts",
                    part["part_id"],
                    {"current_stock": new_stock}
                )

                parts_checkout_results.append({
                    "part_id": part["part_id"],
                    "part_name": part_data.get("name", "Unknown"),
                    "quantity_used": part["quantity_used"],
                    "previous_stock": current_stock,
                    "new_stock": new_stock
                })

                # Log the part checkout
                from app.services.audit_log_service import log_part_checkout
                await log_part_checkout(
                    part_id=part["part_id"],
                    part_name=part_data.get("name", "Unknown"),
                    quantity=part["quantity_used"],
                    work_order_id=wo_id,
                    user_id=current_user.uid,
                    user_name=current_user.full_name or current_user.email,
                    organization_id=current_user.organization_id,
                )
        except Exception as e:
            logging.getLogger(__name__).error(f"Error processing part checkout: {e}")

    # Update work order with completion data
    completion_timestamp = completion_time or datetime.now(timezone.utc).isoformat()

    # Calculate total labor hours from all technicians
    total_tech_hours = sum(t["hours_worked"] for t in technicians_worked) if technicians_worked else labor_hours

    update_data = {
        "status": "Completed",
        "completed_at": completion_timestamp,
        "completed_by_uid": current_user.uid,
        "completed_by_name": current_user.full_name or current_user.email,
        "completion_notes": completion_notes,
        "labor_hours": total_tech_hours,
        "parts_used": parts_checkout_results,
        "technicians_worked": technicians_worked,
    }

    await firestore_manager.update_document(
        "work_orders", wo_id, update_data
    )

    # Log the completion for audit trail
    await log_work_order_completed(
        wo_id=wo_id,
        wo_data={**existing_data, **update_data},
        user_id=current_user.uid,
        user_name=current_user.full_name or current_user.email,
        organization_id=current_user.organization_id,
        completion_notes=completion_notes,
    )

    # Update asset's last_maintenance_date if work order is linked to an asset
    asset_id = existing_data.get("asset_id")
    if asset_id:
        try:
            asset_update = {
                "last_maintenance_date": completion_timestamp,
                "base_health_score": 100.0,  # Reset health score after maintenance
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await firestore_manager.update_document("assets", asset_id, asset_update)
            logging.getLogger(__name__).info(
                f"Updated asset {asset_id} last_maintenance_date after WO {wo_id} completion"
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating asset after WO completion: {e}")

    return RedirectResponse(url=f"/work-orders/{wo_id}", status_code=303)


# Other endpoints like media upload, completion, etc. would also be refactored
# to use the work_order_service.


# ==========================================
# 📋 MY WORK ORDERS API ENDPOINT
# ==========================================


@router.get("/api/my-work-orders", response_class=JSONResponse)
async def get_my_work_orders(
    status: Optional[str] = None,
    current_user: OptionalType[User] = Depends(get_optional_current_user),
):
    """Get work orders assigned to the current user"""
    from app.core.firestore_db import get_firestore_manager

    firestore_manager = get_firestore_manager()

    # Get user ID - use demo user if not authenticated
    user_id = current_user.id if current_user else "demo_user"

    # Get all work orders and filter by assigned_to_uid
    all_work_orders = await firestore_manager.get_collection(
        "work_orders", order_by="-created_at"
    )

    # Filter work orders assigned to this user
    my_work_orders = []
    for wo in all_work_orders:
        assigned_to = wo.get("assigned_to_uid") or wo.get("assigned_to")
        if assigned_to == user_id or assigned_to == (
            current_user.username if current_user else None
        ):
            # Convert datetime objects to strings
            for key, value in wo.items():
                if hasattr(value, "strftime"):
                    wo[key] = value.strftime("%Y-%m-%d %H:%M")
                elif hasattr(value, "timestamp"):
                    wo[key] = str(value)
            my_work_orders.append(wo)

    # Apply status filter if provided
    if status and status != "all":
        status_map = {
            "open": ["Open", "Pending", "New"],
            "in_progress": ["In Progress", "Working", "Started"],
            "completed": ["Completed", "Done", "Closed", "Resolved"],
        }
        allowed_statuses = status_map.get(status, [status])
        my_work_orders = [
            wo for wo in my_work_orders if wo.get("status") in allowed_statuses
        ]

    # Calculate summary stats
    summary = {
        "total": len(my_work_orders),
        "open": len(
            [
                wo
                for wo in my_work_orders
                if wo.get("status") in ["Open", "Pending", "New"]
            ]
        ),
        "in_progress": len(
            [
                wo
                for wo in my_work_orders
                if wo.get("status") in ["In Progress", "Working", "Started"]
            ]
        ),
        "completed": len(
            [
                wo
                for wo in my_work_orders
                if wo.get("status") in ["Completed", "Done", "Closed", "Resolved"]
            ]
        ),
        "high_priority": len(
            [
                wo
                for wo in my_work_orders
                if wo.get("priority") in ["High", "Critical", "Urgent"]
            ]
        ),
    }

    return JSONResponse(
        {"work_orders": my_work_orders, "summary": summary, "user_id": user_id}
    )


# ==========================================
# 📋 BULK IMPORT ENDPOINTS FOR WORK ORDERS
# ==========================================


@router.get("/bulk-import", response_class=HTMLResponse)
async def bulk_import_work_orders_page(
    request: Request, current_user: User = Depends(require_auth_cookie)
):
    """Render the bulk import page for work orders"""
    return templates.TemplateResponse(
        "work_orders_bulk_import.html",
        {
            "request": request,
            "user": current_user,
            "current_user": current_user,
            "is_demo": False,
            "pandas_available": PANDAS_AVAILABLE,
        },
    )


@router.get("/api/work-orders/template")
async def download_work_orders_template(format: str = "csv"):
    """Download a template file for bulk work orders import"""
    headers = [
        "title",
        "description",
        "priority",
        "status",
        "work_order_type",
        "assigned_to",
        "asset_name",
        "due_date",
    ]
    example_data = [
        [
            "HVAC Filter Replacement",
            "Replace air filters in building A HVAC units",
            "Medium",
            "Open",
            "Preventive",
            "john.smith",
            "HVAC-Unit-01",
            "2024-12-20",
        ],
        [
            "Conveyor Belt Inspection",
            "Monthly inspection of conveyor belt system",
            "High",
            "Open",
            "Preventive",
            "jane.doe",
            "Conveyor-Main",
            "2024-12-18",
        ],
        [
            "Pump Repair",
            "Fix leak in hydraulic pump seal",
            "Critical",
            "Open",
            "Corrective",
            "mike.tech",
            "Pump-HYD-05",
            "2024-12-16",
        ],
    ]

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(example_data)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=work_orders_import_template.csv"
            },
        )
    elif format.lower() == "xlsx" and PANDAS_AVAILABLE:
        df = pd.DataFrame(example_data, columns=headers)
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name="Work Orders")
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=work_orders_import_template.xlsx"
            },
        )
    else:
        return JSONResponse(
            {"error": "Unsupported format. Use csv or xlsx."}, status_code=400
        )


@router.post("/api/work-orders/bulk-import")
async def bulk_import_work_orders(
    file: UploadFile = File(...), current_user: User = Depends(require_auth_cookie)
):
    """Bulk import work orders from CSV or Excel file"""
    from app.core.firestore_db import get_firestore_manager

    firestore_manager = get_firestore_manager()

    # Validate file type
    filename = file.filename.lower()
    if not (
        filename.endswith(".csv")
        or filename.endswith(".xlsx")
        or filename.endswith(".xls")
    ):
        return JSONResponse(
            {
                "success": False,
                "error": "Invalid file format. Please upload a CSV or Excel file (.csv, .xlsx, .xls)",
            },
            status_code=400,
        )

    try:
        # Read file content
        content = await file.read()

        # Parse file based on type
        if filename.endswith(".csv"):
            text_content = content.decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(text_content))
            rows = list(csv_reader)
        elif PANDAS_AVAILABLE:
            df = pd.read_excel(io.BytesIO(content))
            rows = df.to_dict("records")
        else:
            return JSONResponse(
                {
                    "success": False,
                    "error": "Excel support not available. Please upload a CSV file.",
                },
                status_code=400,
            )

        if not rows:
            return JSONResponse(
                {"success": False, "error": "File is empty or has no valid data rows."},
                status_code=400,
            )

        # Process and import work orders
        imported = 0
        errors = []

        for idx, row in enumerate(rows, start=2):
            try:
                # Clean and validate required fields
                title = str(row.get("title", "")).strip()
                if not title:
                    errors.append(f"Row {idx}: Missing required field 'title'")
                    continue

                # Build work order data
                wo_data = {
                    "title": title,
                    "description": str(row.get("description", "")).strip(),
                    "priority": str(row.get("priority", "Medium")).strip(),
                    "status": str(row.get("status", "Open")).strip(),
                    "work_order_type": str(
                        row.get("work_order_type", "Corrective")
                    ).strip(),
                    "assigned_to": str(row.get("assigned_to", "")).strip(),
                    "assigned_to_uid": str(row.get("assigned_to", "")).strip(),
                    "asset_name": str(row.get("asset_name", "")).strip(),
                    "due_date": str(row.get("due_date", "")).strip(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "created_by": (
                        current_user.full_name if current_user else "bulk_import"
                    ),
                }

                # Create work order in Firestore with organization scoping
                if current_user and current_user.organization_id:
                    # SECURITY: Use org-scoped method to ensure data isolation
                    wo_id = await firestore_manager.create_org_document(
                        "work_orders", wo_data, current_user.organization_id
                    )
                    # Log the bulk import creation
                    await log_work_order_created(
                        wo_id=wo_id or f"bulk_{idx}",
                        wo_data=wo_data,
                        user_id=current_user.uid,
                        user_name=current_user.full_name or "bulk_import",
                        organization_id=current_user.organization_id,
                    )
                else:
                    # Fallback for users without org (should not happen in production)
                    await firestore_manager.create_document("work_orders", wo_data)
                imported += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        return JSONResponse(
            {
                "success": True,
                "imported": imported,
                "total_rows": len(rows),
                "errors": errors[:20],
                "error_count": len(errors),
                "message": f"Successfully imported {imported} of {len(rows)} work orders.",
            }
        )

    except Exception as e:
        return JSONResponse(
            {"success": False, "error": f"Error processing file: {str(e)}"},
            status_code=500,
        )


# ==========================================
# 📋 AUDIT LOG API ENDPOINTS
# ==========================================


@router.get("/api/audit-logs", response_class=JSONResponse)
async def get_audit_logs(
    request: Request,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    days: int = 7,
    limit: int = 100,
):
    """Get audit logs for the current organization"""
    from app.services.audit_log_service import audit_log_service

    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    org_id = current_user.organization_id

    if entity_type and entity_id:
        # Get history for specific entity
        logs = await audit_log_service.get_entity_history(
            entity_type=entity_type,
            entity_id=entity_id,
            organization_id=org_id,
            limit=limit,
        )
    else:
        # Get all organization activity
        logs = await audit_log_service.get_organization_activity(
            organization_id=org_id,
            days=days,
            limit=limit,
        )

    return JSONResponse({
        "logs": logs,
        "count": len(logs),
        "organization_id": org_id,
    })


@router.get("/api/audit-logs/summary", response_class=JSONResponse)
async def get_audit_summary(
    request: Request,
    days: int = 30,
):
    """Get audit activity summary for the current organization"""
    from app.services.audit_log_service import audit_log_service

    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    summary = await audit_log_service.get_activity_summary(
        organization_id=current_user.organization_id,
        days=days,
    )

    return JSONResponse(summary)


@router.get("/{wo_id}/audit-history", response_class=JSONResponse)
async def get_work_order_audit_history(
    request: Request,
    wo_id: str,
):
    """Get audit history for a specific work order"""
    from app.services.audit_log_service import audit_log_service

    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    logs = await audit_log_service.get_entity_history(
        entity_type="work_order",
        entity_id=wo_id,
        organization_id=current_user.organization_id,
        limit=50,
    )

    return JSONResponse({
        "work_order_id": wo_id,
        "history": logs,
        "count": len(logs),
    })
