import csv
import io
import json
import logging
import os
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

# Try to import pandas for Excel support
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

from app.auth import get_current_active_user, require_permission, get_optional_current_user
from app.models.user import User
from typing import Optional as OptionalType
from app.models.work_order import WorkOrder
from app.services.work_order_service import work_order_service
from app.services.notification_service import NotificationService
from app.services.linesmart_intelligence import linesmart_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/work-orders", tags=["work-orders"])
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads/work_orders"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("", response_class=HTMLResponse)
async def work_orders_list(request: Request, current_user: User = Depends(get_current_active_user)):
    """Render the work orders list (filtered by organization)"""
    # Multi-tenant: filter by user's organization
    work_orders = await work_order_service.get_work_orders(
        organization_id=current_user.organization_id
    )
    return templates.TemplateResponse(
        "work_orders.html", {"request": request, "work_orders": work_orders, "user": current_user, "current_user": current_user, "is_demo": False}
    )

@router.get("/{wo_id}", response_class=HTMLResponse)
async def work_order_detail(request: Request, wo_id: str, current_user: User = Depends(get_current_active_user)):
    """Render work order details (validates organization ownership)"""
    # Multi-tenant: validate work order belongs to user's organization
    work_order = await work_order_service.get_work_order(
        wo_id, organization_id=current_user.organization_id
    )
    if not work_order:
        return RedirectResponse(url="/work-orders")
    
    # Media and other related data would be fetched by the service in a real app
    return templates.TemplateResponse(
        "work_order_detail.html",
        {"request": request, "wo": work_order, "media": [], "user": current_user, "current_user": current_user, "is_demo": False},
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
    current_user: User = Depends(require_permission("create_work_order_request")),
):
    """Create a new work order"""
    work_order_data = {
        "title": title, "description": description, "priority": priority, "status": status,
        "assigned_to_uid": assigned_to_uid, "asset_id": asset_id, "work_order_type": work_order_type,
        "due_date": due_date
    }
    # Multi-tenant: associate work order with user's organization
    wo_id = await work_order_service.create_work_order(
        work_order_data, organization_id=current_user.organization_id
    )
    
    # Notification logic would also be in the service layer
    if assigned_to_uid:
        await NotificationService.notify_work_order_assigned(
            work_order_id=wo_id, technician_id=assigned_to_uid, title=title, work_order_data=work_order_data
        )

    return RedirectResponse(url="/work-orders", status_code=303)

@router.post("/{wo_id}/update")
async def update_work_order(
    wo_id: str,
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    status: str = Form(...),
    assigned_to_uid: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    current_user: User = Depends(require_permission("update_status")),
):
    """Update an existing work order"""
    update_data = {
        "title": title, "description": description, "priority": priority,
        "status": status, "assigned_to_uid": assigned_to_uid, "due_date": due_date
    }
    # Multi-tenant: validate work order belongs to user's organization
    await work_order_service.update_work_order(
        wo_id, update_data, organization_id=current_user.organization_id
    )
    return RedirectResponse(url=f"/work-orders/{wo_id}", status_code=303)

# Other endpoints like media upload, completion, etc. would also be refactored
# to use the work_order_service.


# ==========================================
# 📋 MY WORK ORDERS API ENDPOINT
# ==========================================

@router.get("/api/my-work-orders", response_class=JSONResponse)
async def get_my_work_orders(
    status: Optional[str] = None,
    current_user: OptionalType[User] = Depends(get_optional_current_user)
):
    """Get work orders assigned to the current user"""
    from app.core.firestore_db import get_firestore_manager

    firestore_manager = get_firestore_manager()

    # Get user ID - use demo user if not authenticated
    user_id = current_user.id if current_user else "demo_user"

    # Get all work orders and filter by assigned_to_uid
    all_work_orders = await firestore_manager.get_collection("work_orders", order_by="-created_at")

    # Filter work orders assigned to this user
    my_work_orders = []
    for wo in all_work_orders:
        assigned_to = wo.get("assigned_to_uid") or wo.get("assigned_to")
        if assigned_to == user_id or assigned_to == (current_user.username if current_user else None):
            # Convert datetime objects to strings
            for key, value in wo.items():
                if hasattr(value, 'strftime'):
                    wo[key] = value.strftime("%Y-%m-%d %H:%M")
                elif hasattr(value, 'timestamp'):
                    wo[key] = str(value)
            my_work_orders.append(wo)

    # Apply status filter if provided
    if status and status != 'all':
        status_map = {
            'open': ['Open', 'Pending', 'New'],
            'in_progress': ['In Progress', 'Working', 'Started'],
            'completed': ['Completed', 'Done', 'Closed', 'Resolved']
        }
        allowed_statuses = status_map.get(status, [status])
        my_work_orders = [wo for wo in my_work_orders if wo.get('status') in allowed_statuses]

    # Calculate summary stats
    summary = {
        'total': len(my_work_orders),
        'open': len([wo for wo in my_work_orders if wo.get('status') in ['Open', 'Pending', 'New']]),
        'in_progress': len([wo for wo in my_work_orders if wo.get('status') in ['In Progress', 'Working', 'Started']]),
        'completed': len([wo for wo in my_work_orders if wo.get('status') in ['Completed', 'Done', 'Closed', 'Resolved']]),
        'high_priority': len([wo for wo in my_work_orders if wo.get('priority') in ['High', 'Critical', 'Urgent']])
    }

    return JSONResponse({
        "work_orders": my_work_orders,
        "summary": summary,
        "user_id": user_id
    })


# ==========================================
# 📋 BULK IMPORT ENDPOINTS FOR WORK ORDERS
# ==========================================

@router.get("/bulk-import", response_class=HTMLResponse)
async def bulk_import_work_orders_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """Render the bulk import page for work orders"""
    return templates.TemplateResponse(
        "work_orders_bulk_import.html",
        {"request": request, "user": current_user, "current_user": current_user, "is_demo": False, "pandas_available": PANDAS_AVAILABLE}
    )


@router.get("/api/work-orders/template")
async def download_work_orders_template(format: str = "csv"):
    """Download a template file for bulk work orders import"""
    headers = ["title", "description", "priority", "status", "work_order_type", "assigned_to", "asset_name", "due_date"]
    example_data = [
        ["HVAC Filter Replacement", "Replace air filters in building A HVAC units", "Medium", "Open", "Preventive", "john.smith", "HVAC-Unit-01", "2024-12-20"],
        ["Conveyor Belt Inspection", "Monthly inspection of conveyor belt system", "High", "Open", "Preventive", "jane.doe", "Conveyor-Main", "2024-12-18"],
        ["Pump Repair", "Fix leak in hydraulic pump seal", "Critical", "Open", "Corrective", "mike.tech", "Pump-HYD-05", "2024-12-16"],
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
            headers={"Content-Disposition": "attachment; filename=work_orders_import_template.csv"}
        )
    elif format.lower() == "xlsx" and PANDAS_AVAILABLE:
        df = pd.DataFrame(example_data, columns=headers)
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name="Work Orders")
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=work_orders_import_template.xlsx"}
        )
    else:
        return JSONResponse({"error": "Unsupported format. Use csv or xlsx."}, status_code=400)


@router.post("/api/work-orders/bulk-import")
async def bulk_import_work_orders(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk import work orders from CSV or Excel file"""
    from app.core.firestore_db import get_firestore_manager
    firestore_manager = get_firestore_manager()

    # Validate file type
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        return JSONResponse({
            "success": False,
            "error": "Invalid file format. Please upload a CSV or Excel file (.csv, .xlsx, .xls)"
        }, status_code=400)

    try:
        # Read file content
        content = await file.read()

        # Parse file based on type
        if filename.endswith('.csv'):
            text_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(text_content))
            rows = list(csv_reader)
        elif PANDAS_AVAILABLE:
            df = pd.read_excel(io.BytesIO(content))
            rows = df.to_dict('records')
        else:
            return JSONResponse({
                "success": False,
                "error": "Excel support not available. Please upload a CSV file."
            }, status_code=400)

        if not rows:
            return JSONResponse({
                "success": False,
                "error": "File is empty or has no valid data rows."
            }, status_code=400)

        # Process and import work orders
        imported = 0
        errors = []

        for idx, row in enumerate(rows, start=2):
            try:
                # Clean and validate required fields
                title = str(row.get('title', '')).strip()
                if not title:
                    errors.append(f"Row {idx}: Missing required field 'title'")
                    continue

                # Build work order data
                wo_data = {
                    "title": title,
                    "description": str(row.get('description', '')).strip(),
                    "priority": str(row.get('priority', 'Medium')).strip(),
                    "status": str(row.get('status', 'Open')).strip(),
                    "work_order_type": str(row.get('work_order_type', 'Corrective')).strip(),
                    "assigned_to": str(row.get('assigned_to', '')).strip(),
                    "assigned_to_uid": str(row.get('assigned_to', '')).strip(),
                    "asset_name": str(row.get('asset_name', '')).strip(),
                    "due_date": str(row.get('due_date', '')).strip(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "created_by": current_user.username if current_user else "bulk_import",
                }

                # Create work order in Firestore
                await firestore_manager.create_document("work_orders", wo_data)
                imported += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        return JSONResponse({
            "success": True,
            "imported": imported,
            "total_rows": len(rows),
            "errors": errors[:20],
            "error_count": len(errors),
            "message": f"Successfully imported {imported} of {len(rows)} work orders."
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Error processing file: {str(e)}"
        }, status_code=500)
