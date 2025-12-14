import json
import logging
import os
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_active_user, require_permission
from app.models.user import User
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
    """Render the work orders list"""
    work_orders = await work_order_service.get_work_orders()
    return templates.TemplateResponse(
        "work_orders.html", {"request": request, "work_orders": work_orders, "user": current_user}
    )

@router.get("/{wo_id}", response_class=HTMLResponse)
async def work_order_detail(request: Request, wo_id: str, current_user: User = Depends(get_current_active_user)):
    """Render work order details"""
    work_order = await work_order_service.get_work_order(wo_id)
    if not work_order:
        return RedirectResponse(url="/work-orders")
    
    # Media and other related data would be fetched by the service in a real app
    return templates.TemplateResponse(
        "work_order_detail.html",
        {"request": request, "wo": work_order, "media": [], "user": current_user},
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
    wo_id = await work_order_service.create_work_order(work_order_data)
    
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
    await work_order_service.update_work_order(wo_id, update_data)
    return RedirectResponse(url=f"/work-orders/{wo_id}", status_code=303)

# Other endpoints like media upload, completion, etc. would also be refactored
# to use the work_order_service.
