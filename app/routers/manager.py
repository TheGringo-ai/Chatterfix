"""
Manager Dashboard Router
Comprehensive management interface for ChatterFix CMMS
"""
import asyncio
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_active_user, require_permission
from app.models.user import User
from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manager", tags=["manager"])
templates = Jinja2Templates(directory="app/templates")

# All routes in this router will require manager permissions
@router.get("/", response_class=HTMLResponse)
async def manager_dashboard(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Comprehensive Manager Dashboard - Central Command Center"""
    firestore_manager = get_firestore_manager()
    
    # In a real app, this would be a complex aggregation. For now, we get some recent data.
    users, work_orders, assets = await asyncio.gather(
        firestore_manager.get_collection("users"),
        firestore_manager.get_collection("work_orders", limit=50),
        firestore_manager.get_collection("assets", limit=50)
    )

    overview_stats = {
        "total_technicians": len([u for u in users if u.get("role") == "technician"]),
        "active_work_orders": len([w for w in work_orders if w.get("status") == "Open" or w.get("status") == "In Progress"]),
        "pending_onboarding": len([u for u in users if u.get("onboarding_status") == "In Progress"]),
        "critical_assets": len([a for a in assets if a.get("criticality") == "Critical"]),
    }
    
    # Mocking some data for demonstration
    recent_activities = []
    top_technicians = []
    critical_assets = []

    return templates.TemplateResponse(
        "manager_dashboard.html",
        {
            "request": request, "user": current_user, "overview_stats": overview_stats,
            "recent_activities": recent_activities, "top_technicians": top_technicians,
            "critical_assets": critical_assets,
        },
    )

@router.get("/technicians", response_class=HTMLResponse)
async def technician_management(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Technician Management - Onboarding, Performance, Scheduling"""
    firestore_manager = get_firestore_manager()
    users = await firestore_manager.get_collection("users", order_by="full_name")
    
    return templates.TemplateResponse(
        "manager_technicians.html",
        {"request": request, "user": current_user, "technicians": users, "onboarding_pipeline": []},
    )

@router.post("/technicians/onboard")
async def start_technician_onboarding(
    name: str = Form(...), email: str = Form(...), role: str = Form(...),
    department: str = Form(...), start_date: str = Form(...),
    current_user: User = Depends(require_permission("manager"))
):
    """Start onboarding process for new technician"""
    # This should be part of a more extensive user management service.
    # For now, we can create a placeholder onboarding document.
    firestore_manager = get_firestore_manager()
    onboarding_data = {
        "name": name, "email": email, "role": role, "department": department,
        "start_date": start_date, "status": "initiated", "progress": 0,
        "created_by": current_user.uid,
    }
    onboarding_id = await firestore_manager.create_document("onboarding_tasks", onboarding_data)
    
    return JSONResponse({
        "success": True, "message": f"Onboarding initiated for {name}",
        "onboarding_id": onboarding_id
    })
    
@router.get("/performance", response_class=HTMLResponse)
async def performance_analytics(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Performance Analytics - Technician & Asset Performance"""
    return templates.TemplateResponse(
        "manager_performance.html", {"request": request, "user": current_user}
    )

@router.get("/assets", response_class=HTMLResponse)
async def asset_monitoring(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Asset Performance Monitoring & Management"""
    firestore_manager = get_firestore_manager()
    assets = await firestore_manager.get_collection("assets", order_by="-criticality")
    
    return templates.TemplateResponse(
        "manager_assets.html",
        {"request": request, "user": current_user, "assets_overview": assets, "maintenance_schedule": [], "cost_analysis": []},
    )

@router.get("/inventory", response_class=HTMLResponse)
async def inventory_management(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Inventory & Cost Management Dashboard"""
    firestore_manager = get_firestore_manager()
    parts = await firestore_manager.get_collection("parts", order_by="name")
    
    return templates.TemplateResponse(
        "manager_inventory.html",
        {"request": request, "user": current_user, "inventory_overview": parts, "monthly_costs": [], "supplier_performance": [], "pending_orders": []},
    )

@router.get("/reports", response_class=HTMLResponse)
async def reports_analytics(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Comprehensive Reports & Analytics"""
    return templates.TemplateResponse(
        "manager_reports.html",
        {"request": request, "user": current_user, "kpis": {}, "performance_trends": []},
    )

@router.get("/admin", response_class=HTMLResponse)
async def system_administration(request: Request, current_user: User = Depends(require_permission("manager"))):
    """System Administration & Settings"""
    return templates.TemplateResponse(
        "manager_admin.html",
        {"request": request, "user": current_user, "system_health": {}, "user_summary": {}},
    )

@router.get("/table/work-orders", response_class=HTMLResponse)
async def work_orders_table_view(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Editable table view for work orders with bulk operations"""
    firestore_manager = get_firestore_manager()
    work_orders = await firestore_manager.get_collection("work_orders", order_by="-created_date")
    return templates.TemplateResponse(
        "manager_work_orders_table.html",
        {"request": request, "user": current_user, "work_orders": work_orders},
    )

@router.get("/table/assets", response_class=HTMLResponse)
async def assets_table_view(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Editable table view for assets with bulk operations"""
    firestore_manager = get_firestore_manager()
    assets = await firestore_manager.get_collection("assets", order_by="name")
    return templates.TemplateResponse(
        "manager_assets_table.html", {"request": request, "user": current_user, "assets": assets}
    )

@router.get("/table/parts", response_class=HTMLResponse)
async def parts_table_view(request: Request, current_user: User = Depends(require_permission("manager"))):
    """Editable table view for parts/inventory with bulk operations"""
    firestore_manager = get_firestore_manager()
    parts = await firestore_manager.get_collection("parts", order_by="name")
    return templates.TemplateResponse(
        "manager_parts_table.html", {"request": request, "user": current_user, "parts": parts}
    )

# Other endpoints like bulk operations, file uploads etc. would also need to be refactored
# to use FirestoreManager and appropriate permissions.
# This is a sample of the required refactoring.
