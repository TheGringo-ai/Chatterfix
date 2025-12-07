import logging
import os
import shutil

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.db_adapter import get_db_adapter
from app.core.firestore_db import get_db_connection
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directory exists
UPLOAD_DIR = "app/static/uploads/work_orders"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/work-orders", response_class=HTMLResponse)
async def work_orders_list(request: Request):
    """Render the work orders list"""
    try:
        db_adapter = get_db_adapter()
        work_orders = []

        if db_adapter.firestore_manager:
            # Get work orders from Firestore
            work_orders_data = await db_adapter.firestore_manager.get_collection(
                "work_orders", order_by="-created_date"  # Descending order
            )

            # Enrich with asset information
            for wo in work_orders_data:
                if wo.get("asset_id"):
                    asset_data = await db_adapter.firestore_manager.get_document(
                        "assets", wo["asset_id"]
                    )
                    if asset_data:
                        wo["asset_image_url"] = asset_data.get("image_url")
                        wo["asset_name"] = asset_data.get("name")

                work_orders.append(wo)
        else:
            logger.warning("Firestore not available for work orders list")

        return templates.TemplateResponse(
            "work_orders.html", {"request": request, "work_orders": work_orders}
        )
    except Exception as e:
        logger.error(f"Failed to load work orders: {e}")
        return templates.TemplateResponse(
            "work_orders.html",
            {
                "request": request,
                "work_orders": [],
                "error": "Failed to load work orders",
            },
        )


@router.get("/work-orders/{wo_id}", response_class=HTMLResponse)
async def work_order_detail(request: Request, wo_id: str):
    """Render work order details"""
    try:
        db_adapter = get_db_adapter()

        if not db_adapter.firestore_manager:
            logger.error("Firestore not available for work order detail")
            return RedirectResponse(url="/work-orders")

        # Get work order from Firestore
        wo = await db_adapter.firestore_manager.get_document("work_orders", wo_id)
        if not wo:
            return RedirectResponse(url="/work-orders")

        # Get media for this work order
        media_data = await db_adapter.firestore_manager.get_collection(
            "work_order_media",
            filters=[{"field": "work_order_id", "operator": "==", "value": wo_id}],
            order_by="-uploaded_date",
        )

        return templates.TemplateResponse(
            "work_order_detail.html",
            {"request": request, "wo": wo, "media": media_data},
        )
    except Exception as e:
        logger.error(f"Failed to load work order detail: {e}")
        return RedirectResponse(url="/work-orders")


@router.post("/work-orders/{wo_id}/media")
async def upload_wo_media(
    wo_id: int,
    file: UploadFile = File(...),
    file_type: str = Form("image"),
    title: str = Form(""),
    description: str = Form(""),
):
    """Upload media for work order"""
    # Create wo-specific directory
    wo_dir = os.path.join(UPLOAD_DIR, str(wo_id))
    os.makedirs(wo_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(wo_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store in database
    # Use relative path for serving
    rel_path = f"/static/uploads/work_orders/{wo_id}/{file.filename}"

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO work_order_media (work_order_id, file_path, file_type, title, description)
        VALUES (?, ?, ?, ?, ?)
    """,
        (wo_id, rel_path, file_type, title, description),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(f"/work-orders/{wo_id}", status_code=303)


@router.post("/work-orders")
async def create_work_order(
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    assigned_to: str = Form(...),
    due_date: str = Form(...),
    asset_id: str = Form(None),
    files: list[UploadFile] = File(None),
):
    """Create a new work order"""
    try:
        db_adapter = get_db_adapter()
        if not db_adapter.firestore_manager:
            logger.error("Firestore not available for work order creation")
            return RedirectResponse(
                url="/work-orders?error=database_unavailable", status_code=303
            )

        # Prepare work order data
        from datetime import datetime

        work_order_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "assigned_to": assigned_to,
            "due_date": due_date,
            "asset_id": asset_id,
            "status": "Open",
            "created_date": datetime.now().isoformat(),
        }

        # Create work order in Firestore
        wo_id = await db_adapter.firestore_manager.create_document(
            "work_orders", work_order_data
        )
        logger.info(f"Created work order {wo_id}: {title}")

        # Handle file uploads if provided
        media_files = []
        if files:
            wo_dir = os.path.join(UPLOAD_DIR, str(wo_id))
            os.makedirs(wo_dir, exist_ok=True)

            for file in files:
                if file.filename:
                    file_path = os.path.join(wo_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)

                    rel_path = f"/static/uploads/work_orders/{wo_id}/{file.filename}"
                    file_type = (
                        "image"
                        if file.content_type and file.content_type.startswith("image/")
                        else "document"
                    )

                    media_data = {
                        "work_order_id": wo_id,
                        "file_path": rel_path,
                        "file_type": file_type,
                        "title": file.filename,
                        "description": "Uploaded during creation",
                        "uploaded_date": datetime.now().isoformat(),
                    }

                    media_id = await db_adapter.firestore_manager.create_document(
                        "work_order_media", media_data
                    )
                    media_files.append(media_id)

        # Send notification if assigned to someone
        if assigned_to and assigned_to != "unassigned":
            try:
                # Convert assigned_to to user_id if needed (assuming it's user_id)
                technician_id = int(assigned_to) if assigned_to.isdigit() else None
                if technician_id:
                    # Add asset name to work order data if available
                    if asset_id:
                        asset_data = await db_adapter.firestore_manager.get_document(
                            "assets", asset_id
                        )
                        work_order_data["asset_name"] = (
                            asset_data.get("name", "Unknown Asset")
                            if asset_data
                            else "Unknown Asset"
                        )

                    await NotificationService.notify_work_order_assigned(
                        work_order_id=int(wo_id) if wo_id.isdigit() else hash(wo_id),
                        technician_id=technician_id,
                        title=title,
                        work_order_data=work_order_data,
                    )
                    logger.info(f"Sent work order assignment notification for {wo_id}")
            except Exception as e:
                logger.error(f"Failed to send work order notification: {e}")

        return RedirectResponse(url="/work-orders", status_code=303)

    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        return RedirectResponse(
            url="/work-orders?error=creation_failed", status_code=303
        )


@router.post("/work-orders/{wo_id}/complete")
async def complete_work_order(wo_id: str):
    """Mark a work order as completed"""
    try:
        db_adapter = get_db_adapter()

        if not db_adapter.firestore_manager:
            logger.error("Firestore not available for work order completion")
            return RedirectResponse(url="/work-orders", status_code=303)

        # Get work order for notification
        wo = await db_adapter.firestore_manager.get_document("work_orders", wo_id)

        # Update status to completed
        from datetime import datetime

        await db_adapter.firestore_manager.update_document(
            "work_orders",
            wo_id,
            {"status": "Completed", "completed_date": datetime.now().isoformat()},
        )

        # Send completion notification if work order has assignment
        if wo and wo.get("assigned_to"):
            try:
                technician_id = (
                    int(wo["assigned_to"]) if wo["assigned_to"].isdigit() else None
                )
                if technician_id:
                    work_order_info = {
                        "id": wo_id,
                        "title": wo.get("title", "Work Order"),
                        "description": wo.get("description", "No description"),
                        "priority": wo.get("priority", "normal"),
                        "asset_name": wo.get("asset_name", "Unknown Asset"),
                    }

                    # Get user data for email
                    user_data = await NotificationService._get_user_data(technician_id)
                    user_email = user_data.get("email")
                    user_name = user_data.get("fullName", "Technician")

                    if user_email:
                        from app.services.email_service import email_service

                        await email_service.send_work_order_notification(
                            to_email=user_email,
                            to_name=user_name,
                            work_order=work_order_info,
                            notification_type="completed",
                        )
                        logger.info(f"Sent work order completion email to {user_email}")

                        # Also send in-app notification
                        await NotificationService.send_notification(
                            user_id=technician_id,
                            notification_type="work_order_completed",
                            title="Work Order Completed",
                            message=f"Work order '{wo.get('title')}' has been completed",
                            link=f"/work-orders/{wo_id}",
                            priority="normal",
                        )

            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")

        return RedirectResponse(url="/work-orders", status_code=303)
    except Exception as e:
        logger.error(f"Failed to complete work order: {e}")
        return RedirectResponse(url="/work-orders", status_code=303)


@router.post("/work-orders/{wo_id}/update")
async def update_work_order(
    wo_id: int,
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    assigned_to: str = Form(...),
    due_date: str = Form(...),
):
    """Update an existing work order"""
    conn = get_db_connection()
    conn.execute(
        "UPDATE work_orders SET title = ?, description = ?, priority = ?, assigned_to = ?, due_date = ? WHERE id = ?",
        (title, description, priority, assigned_to, due_date, wo_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/work-orders/{wo_id}", status_code=303)
