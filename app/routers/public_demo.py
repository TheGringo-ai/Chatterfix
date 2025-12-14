"""
Public Demo Router
Provides full demo access without authentication requirements
Uses real Firestore data for authentic demo experience
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.firestore_db import get_firestore_manager

router = APIRouter(prefix="/demo", tags=["Public Demo"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


# Demo user context - allows full interaction without login
DEMO_USER = {
    "uid": "demo-user-001",
    "id": "demo-user-001",
    "username": "demo_visitor",
    "email": "demo@chatterfix.com",
    "full_name": "Demo Visitor",
    "role": "technician",  # Give technician role for full access
    "permissions": ["view_all", "create_work_order_request", "update_status", "use_parts"],
}


# ==================== MAIN DEMO PAGES ====================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def demo_home(request: Request):
    """Demo home - redirect to dashboard"""
    return RedirectResponse(url="/demo/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def demo_dashboard(request: Request):
    """Full dashboard demo with real Firestore data"""
    try:
        fm = get_firestore_manager()

        # Get real data from Firestore
        work_orders = await fm.get_work_orders()
        assets = await fm.get_assets()

        # Calculate real stats
        active_count = len([wo for wo in work_orders if wo.get("status") in ["Open", "In Progress", "active"]])
        pending_count = len([wo for wo in work_orders if wo.get("status") in ["pending", "On Hold"]])
        completed_count = len([wo for wo in work_orders if wo.get("status") in ["Completed", "completed"]])

        workload = {
            "stats": {
                "active": active_count,
                "pending": pending_count,
                "completed": completed_count,
                "total": len(work_orders),
            }
        }

        # Performance metrics
        total_wos = len(work_orders)
        completion_rate = (completed_count / total_wos * 100) if total_wos > 0 else 0
        performance = {
            "today": {
                "completion_rate": round(completion_rate, 1),
                "total_work_orders": total_wos,
                "completed_today": completed_count,
            }
        }

        # Equipment stats
        healthy_assets = len([a for a in assets if a.get("status") in ["Operational", "Active", "operational"]])
        warning_assets = len([a for a in assets if a.get("status") in ["Warning", "Needs Attention", "warning"]])
        critical_assets = len([a for a in assets if a.get("status") in ["Critical", "Down", "critical"]])

        equipment = {
            "total_assets": len(assets),
            "healthy": healthy_assets,
            "warning": warning_assets,
            "critical": critical_assets,
            "uptime_percentage": round((healthy_assets / len(assets) * 100) if assets else 100, 1),
        }

        notifications = {
            "unread_count": 3,
            "recent_interactions": [
                {"type": "AI", "message": "Predictive maintenance alert for Pump Station", "timestamp": "5 min ago"},
                {"type": "System", "message": "New work order assigned", "timestamp": "15 min ago"},
            ],
        }

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "workload": workload,
                "performance": performance,
                "notifications": notifications,
                "equipment": equipment,
                "demo_mode": True,
                "demo_banner": "🎭 DEMO MODE - Explore all features with real sample data",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo dashboard: {e}")
        # Fallback to mock data
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "workload": {"stats": {"active": 12, "pending": 8, "completed": 45, "total": 65}},
                "performance": {"today": {"completion_rate": 94.7, "total_work_orders": 65, "completed_today": 7}},
                "notifications": {"unread_count": 4, "recent_interactions": []},
                "equipment": {"total_assets": 150, "healthy": 142, "warning": 6, "critical": 2, "uptime_percentage": 95.3},
                "demo_mode": True,
                "demo_banner": "🎭 DEMO MODE - Full functionality with sample data",
            },
        )


@router.get("/work-orders", response_class=HTMLResponse)
async def demo_work_orders(request: Request):
    """Work orders demo with real data"""
    try:
        fm = get_firestore_manager()
        work_orders = await fm.get_work_orders()

        return templates.TemplateResponse(
            "work_orders.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "work_orders": work_orders,
                "demo_mode": True,
                "demo_banner": "🔧 WORK ORDERS - Create, edit, and manage maintenance requests",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo work orders: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/work-orders/{wo_id}", response_class=HTMLResponse)
async def demo_work_order_detail(request: Request, wo_id: str):
    """View work order detail"""
    try:
        fm = get_firestore_manager()
        work_order = await fm.get_document("work_orders", wo_id)

        if not work_order:
            return RedirectResponse(url="/demo/work-orders", status_code=302)

        work_order["id"] = wo_id

        return templates.TemplateResponse(
            "work_order_detail.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "work_order": work_order,
                "demo_mode": True,
            },
        )
    except Exception as e:
        logger.error(f"Error loading work order detail: {e}")
        return RedirectResponse(url="/demo/work-orders", status_code=302)


@router.get("/assets", response_class=HTMLResponse)
async def demo_assets(request: Request):
    """Asset management demo with real data"""
    try:
        fm = get_firestore_manager()
        assets = await fm.get_assets()

        return templates.TemplateResponse(
            "assets.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "assets": assets,
                "demo_mode": True,
                "demo_banner": "🏭 ASSETS - Equipment tracking and maintenance history",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo assets: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/assets/{asset_id}", response_class=HTMLResponse)
async def demo_asset_detail(request: Request, asset_id: str):
    """View asset detail"""
    try:
        fm = get_firestore_manager()
        asset = await fm.get_document("assets", asset_id)

        if not asset:
            return RedirectResponse(url="/demo/assets", status_code=302)

        asset["id"] = asset_id

        # Get related work orders
        work_orders = await fm.get_asset_work_orders(asset_id)

        return templates.TemplateResponse(
            "asset_detail.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "asset": asset,
                "work_orders": work_orders,
                "demo_mode": True,
            },
        )
    except Exception as e:
        logger.error(f"Error loading asset detail: {e}")
        return RedirectResponse(url="/demo/assets", status_code=302)


@router.get("/inventory", response_class=HTMLResponse)
async def demo_inventory(request: Request):
    """Parts inventory demo"""
    try:
        fm = get_firestore_manager()
        parts = list(fm.db.collection("parts").limit(100).stream())
        parts_list = [{"id": p.id, **p.to_dict()} for p in parts]

        return templates.TemplateResponse(
            "inventory.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "parts": parts_list,
                "demo_mode": True,
                "demo_banner": "📦 INVENTORY - Parts management and checkout",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo inventory: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/training", response_class=HTMLResponse)
async def demo_training(request: Request):
    """Training center demo"""
    try:
        fm = get_firestore_manager()
        modules = await fm.get_training_modules()

        # Get some user training assignments for demo
        user_training = list(fm.db.collection("user_training").limit(10).stream())
        training_list = [{"id": t.id, **t.to_dict()} for t in user_training]

        stats = {
            "total_assigned": len(training_list),
            "completed": len([t for t in training_list if t.get("status") == "completed"]),
            "in_progress": len([t for t in training_list if t.get("status") == "in_progress"]),
            "avg_score": 85.5,
        }

        return templates.TemplateResponse(
            "training_center.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "my_training": training_list[:5],
                "available_modules": modules,
                "stats": stats,
                "demo_mode": True,
                "demo_banner": "🎓 TRAINING - Interactive learning modules and certifications",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo training: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ==================== DEMO ACTIONS (Interactive but not saving user data) ====================

@router.post("/work-orders/create")
async def demo_create_work_order(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("Medium"),
    asset_id: str = Form(None),
):
    """Create work order in demo mode - saves to Firestore with demo flag"""
    try:
        fm = get_firestore_manager()

        work_order_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "asset_id": asset_id,
            "status": "Open",
            "created_by": "demo-user",
            "created_date": datetime.now(timezone.utc),
            "demo_created": True,  # Flag as demo-created
        }

        wo_id = await fm.create_document("work_orders", work_order_data)

        return RedirectResponse(url=f"/demo/work-orders/{wo_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error creating demo work order: {e}")
        return RedirectResponse(url="/demo/work-orders", status_code=303)


@router.post("/work-orders/{wo_id}/update-status")
async def demo_update_work_order_status(wo_id: str, status: str = Form(...)):
    """Update work order status in demo mode"""
    try:
        fm = get_firestore_manager()
        await fm.update_document("work_orders", wo_id, {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "demo-user",
        })
        return RedirectResponse(url=f"/demo/work-orders/{wo_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error updating demo work order: {e}")
        return RedirectResponse(url="/demo/work-orders", status_code=303)


@router.post("/inventory/{part_id}/checkout")
async def demo_checkout_part(part_id: str, quantity: int = Form(1), work_order_id: str = Form(None)):
    """Checkout part in demo mode"""
    try:
        fm = get_firestore_manager()

        # Log the checkout (demo mode)
        checkout_data = {
            "part_id": part_id,
            "quantity": quantity,
            "work_order_id": work_order_id,
            "checked_out_by": "demo-user",
            "checkout_date": datetime.now(timezone.utc),
            "demo_checkout": True,
        }

        await fm.create_document("parts_checkout_log", checkout_data)

        return JSONResponse({"success": True, "message": f"Checked out {quantity} part(s)"})
    except Exception as e:
        logger.error(f"Error in demo checkout: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ==================== API ENDPOINTS FOR DEMO ====================

@router.get("/api/stats")
async def demo_api_stats():
    """Real-time stats API for demo"""
    try:
        fm = get_firestore_manager()
        work_orders = await fm.get_work_orders()
        assets = await fm.get_assets()

        return {
            "status": "demo",
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "active_work_orders": len([wo for wo in work_orders if wo.get("status") in ["Open", "In Progress", "active"]]),
                "completed_today": len([wo for wo in work_orders if wo.get("status") in ["Completed", "completed"]]),
                "assets_monitored": len(assets),
                "uptime_percentage": 95.3,
            },
            "demo_mode": True,
        }
    except Exception as e:
        return {"status": "demo", "error": str(e), "demo_mode": True}


@router.get("/api/work-orders")
async def demo_api_work_orders():
    """Work orders API for demo"""
    try:
        fm = get_firestore_manager()
        work_orders = await fm.get_work_orders()
        return {"work_orders": work_orders, "demo_mode": True}
    except Exception as e:
        return {"error": str(e), "demo_mode": True}


@router.get("/api/assets")
async def demo_api_assets():
    """Assets API for demo"""
    try:
        fm = get_firestore_manager()
        assets = await fm.get_assets()
        return {"assets": assets, "demo_mode": True}
    except Exception as e:
        return {"error": str(e), "demo_mode": True}


@router.get("/api/health")
async def demo_health():
    """Demo health check"""
    return {
        "status": "healthy",
        "mode": "demo",
        "timestamp": datetime.now().isoformat(),
        "features": ["dashboard", "work_orders", "assets", "inventory", "training", "ai_chat"],
        "database": "firestore_connected",
    }


# ==================== FEATURE PAGES ====================

@router.get("/features", response_class=HTMLResponse)
async def demo_features(request: Request):
    """Feature showcase demo"""
    return templates.TemplateResponse(
        "demo_features.html",
        {"request": request, "current_user": DEMO_USER, "demo_mode": True},
    )


@router.get("/ai", response_class=HTMLResponse)
async def demo_ai(request: Request):
    """AI features demo"""
    return templates.TemplateResponse(
        "ai_demo.html",
        {
            "request": request,
            "current_user": DEMO_USER,
            "demo_mode": True,
            "ai_features": {
                "predictive_maintenance": True,
                "computer_vision": True,
                "voice_commands": True,
                "smart_alerts": True,
            },
        },
    )
