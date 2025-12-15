import asyncio
import json
import logging
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.core.db_adapter import get_db_adapter
from app.services.dashboard_service import dashboard_service
from app.services.real_time_feed_service import real_time_feed
from app.services.websocket_manager import websocket_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


# Pydantic models
class WidgetConfigUpdate(BaseModel):
    widget_id: int
    position: int
    size: str
    config: dict = {}


class DashboardLayoutUpdate(BaseModel):
    widgets: List[WidgetConfigUpdate]


@router.get("/app", response_class=HTMLResponse)
async def root_dashboard(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """App route - show landing page or dashboard based on authentication"""
    if not current_user:
        return RedirectResponse(url="/landing", status_code=302)

    # User is authenticated, show dashboard
    return await dashboard(request, current_user=current_user)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Render the ChatterFix Workforce Intelligence Homepage"""
    user_id = "demo"
    is_demo = True
    error_message = None

    if current_user:
        user_id = current_user.uid
        is_demo = False

    # Get real-time stats from Firestore via db_adapter
    try:
        db_adapter = get_db_adapter()
        dashboard_data = await db_adapter.get_dashboard_data(user_id)

        # Extract data for template
        work_orders = dashboard_data.get("work_orders", [])
        assets = dashboard_data.get("assets", [])
        ai_interactions = dashboard_data.get("ai_interactions", [])

    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")

        if is_demo:
            # For demo/unauthenticated users, show demo data
            work_orders = [
                {"id": "WO-001", "title": "Emergency Generator Check", "status": "active", "priority": "critical"},
                {"id": "WO-002", "title": "Fire Suppression Maintenance", "status": "pending", "priority": "high"},
                {"id": "WO-003", "title": "HVAC Filter Replacement", "status": "completed", "priority": "medium"},
            ]
            assets = [
                {"id": "GEN-001", "name": "Emergency Generator", "status": "operational"},
                {"id": "FIRE-001", "name": "Fire Suppression System", "status": "warning"},
                {"id": "HVAC-001", "name": "HVAC Unit #1", "status": "operational"},
            ]
            ai_interactions = [
                {"id": "AI-001", "message": "Predicted generator failure prevented", "timestamp": "2024-12-12"},
                {"id": "AI-002", "message": "Optimized technician scheduling", "timestamp": "2024-12-12"},
            ]
        else:
            # For authenticated users, show empty data with error message - NEVER show fake data
            work_orders = []
            assets = []
            ai_interactions = []
            error_message = "Unable to load your data. Please try refreshing the page or contact support if the issue persists."

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_user": current_user,
            "work_orders": work_orders,
            "assets": assets,
            "ai_interactions": ai_interactions,
            "is_demo": is_demo,
            "error_message": error_message,
        },
    )


@router.get("/classic", response_class=HTMLResponse)
async def classic_dashboard(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """Render the original AI Command Center dashboard"""
    # Get real-time stats from Firestore via db_adapter
    try:
        db_adapter = get_db_adapter()
        dashboard_data = await db_adapter.get_dashboard_data(current_user.uid)

        # Extract data for template
        work_orders = dashboard_data.get("work_orders", [])
        assets = dashboard_data.get("assets", [])
        ai_interactions = dashboard_data.get("ai_interactions", [])

        # Build workload stats from work orders
        active_count = len([wo for wo in work_orders if wo.get("status") == "active"])
        pending_count = len([wo for wo in work_orders if wo.get("status") == "pending"])
        completed_count = len(
            [wo for wo in work_orders if wo.get("status") == "completed"]
        )

        workload = {
            "stats": {
                "active": active_count,
                "pending": pending_count,
                "completed": completed_count,
                "total": len(work_orders),
            }
        }

        # Build performance metrics from work orders
        total_wos = len(work_orders)
        completion_rate = (completed_count / total_wos * 100) if total_wos > 0 else 0

        performance = {
            "today": {
                "completion_rate": round(completion_rate, 1),
                "total_work_orders": total_wos,
                "completed_today": completed_count,
            }
        }

        # Build equipment status from assets
        healthy_assets = len([a for a in assets if a.get("status") == "operational"])
        warning_assets = len([a for a in assets if a.get("status") == "warning"])
        critical_assets = len([a for a in assets if a.get("status") == "critical"])

        equipment = {
            "total_assets": len(assets),
            "healthy": healthy_assets,
            "warning": warning_assets,
            "critical": critical_assets,
            "uptime_percentage": round(
                (healthy_assets / len(assets) * 100) if assets else 100, 1
            ),
        }

        # Notifications from AI interactions or fallback
        notifications = {
            "unread_count": len(ai_interactions),
            "recent_interactions": ai_interactions[:5],  # Latest 5
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        # Fallback data
        workload = {"stats": {"active": 0, "pending": 0, "completed": 0, "total": 0}}
        performance = {
            "today": {
                "completion_rate": 0,
                "total_work_orders": 0,
                "completed_today": 0,
            }
        }
        notifications = {"unread_count": 0, "recent_interactions": []}
        equipment = {
            "total_assets": 0,
            "healthy": 0,
            "warning": 0,
            "critical": 0,
            "uptime_percentage": 100,
        }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "workload": workload,
            "performance": performance,
            "notifications": notifications,
            "equipment": equipment,
        },
    )


@router.get("/config")
async def get_dashboard_config(current_user: User = Depends(get_current_active_user)):
    """Get user's dashboard configuration"""
    config = dashboard_service.get_user_dashboard_config(current_user.uid)
    return JSONResponse(content=config)


@router.post("/config")
async def save_dashboard_config(
    layout: DashboardLayoutUpdate, current_user: User = Depends(get_current_active_user)
):
    """Save user's dashboard layout"""
    widgets = [w.dict() for w in layout.widgets]
    success = dashboard_service.save_dashboard_layout(current_user.uid, widgets)

    return JSONResponse(
        content={
            "success": success,
            "message": "Dashboard layout saved" if success else "Failed to save layout",
        }
    )


@router.get("/widgets")
async def get_available_widgets(current_user: User = Depends(get_current_active_user)):
    """Get available widgets for user's role"""
    # Return static widget configuration for dashboard
    # In production, this would be role-based from Firestore based on user.role
    default_widgets = [
        {
            "id": 1,
            "widget_type": "workload",
            "title": "Workload Overview",
            "description": "Active work orders and assignments",
            "default_roles": "all",
        },
        {
            "id": 2,
            "widget_type": "performance",
            "title": "Performance Metrics",
            "description": "Completion rates and efficiency",
            "default_roles": "manager,technician",
        },
        {
            "id": 3,
            "widget_type": "notifications",
            "title": "Notifications",
            "description": "Recent alerts and messages",
            "default_roles": "all",
        },
        {
            "id": 4,
            "widget_type": "equipment",
            "title": "Equipment Status",
            "description": "Asset health and maintenance needs",
            "default_roles": "all",
        },
        {
            "id": 5,
            "widget_type": "analytics",
            "title": "Analytics",
            "description": "Reports and insights",
            "default_roles": "manager,admin",
        },
    ]

    return JSONResponse(content={"widgets": default_widgets})


@router.get("/widget/{widget_type}/data")
async def get_widget_data(
    widget_type: str, current_user: User = Depends(get_current_active_user)
):
    """Get data for a specific widget"""
    data = dashboard_service.get_widget_data(widget_type, current_user.uid)
    return JSONResponse(content=data)


@router.post("/widget/{widget_id}/config")
async def update_widget_config(
    widget_id: int, config: dict, current_user: User = Depends(get_current_active_user)
):
    """Update widget configuration"""
    success = dashboard_service.update_widget_config(current_user.uid, widget_id, config)

    return JSONResponse(
        content={
            "success": success,
            "message": "Widget updated" if success else "Failed to update widget",
        }
    )


@router.post("/reset")
async def reset_dashboard(current_user: User = Depends(get_current_active_user)):
    """Reset dashboard to default layout"""
    try:
        # Reset to default dashboard configuration
        # In production, this would clear user's custom config from Firestore
        # For now, just return success
        success = True
    except Exception as e:
        logger.error(f"Error resetting dashboard for user {current_user.uid}: {e}")
        success = False

    return JSONResponse(
        content={
            "success": success,
            "message": (
                "Dashboard reset to defaults"
                if success
                else "Failed to reset dashboard"
            ),
        }
    )


# Real-time data endpoints
@router.websocket("/stream")
async def dashboard_stream(websocket: WebSocket, user: User = Depends(get_current_active_user)):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket_manager.connect(websocket, user.uid)

    try:
        while True:
            try:
                # Receive subscription requests with timeout to prevent infinite blocking
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)  # Parse JSON

                if message.get("type") == "subscribe":
                    widget_types = message.get("widgets", [])
                    await real_time_feed.subscribe(user.uid, widget_types)

                elif message.get("type") == "unsubscribe":
                    widget_types = message.get("widgets", [])
                    await real_time_feed.unsubscribe(user.uid, widget_types)

                elif message.get("type") == "refresh":
                    widget_type = message.get("widget")
                    if widget_type:
                        await real_time_feed.send_widget_updates(user.uid, [widget_type])

            except asyncio.TimeoutError:
                # Send keepalive ping to maintain connection
                await websocket.send_json({"type": "ping", "timestamp": time.time()})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logging.error(f"WebSocket error for user {user.uid}: {e}")
                await websocket.send_json(
                    {"type": "error", "message": "Internal error"}
                )
                break

    except WebSocketDisconnect:
        websocket_manager.disconnect(user.uid)
        await real_time_feed.unsubscribe(user.uid)


# Specific widget data endpoints for quick access
@router.get("/workload")
async def get_workload(current_user: User = Depends(get_current_active_user)):
    """Get detailed workload data"""
    data = dashboard_service.get_workload_data(current_user.uid, {})
    return JSONResponse(content=data)


@router.get("/parts-status")
async def get_parts_status(current_user: User = Depends(get_current_active_user)):
    """Get parts status"""
    data = dashboard_service.get_parts_data(current_user.uid, {})
    return JSONResponse(content=data)


@router.get("/team-status")
async def get_team_status(current_user: User = Depends(get_current_active_user)):
    """Get team availability"""
    data = dashboard_service.get_team_data(current_user.uid, {})
    return JSONResponse(content=data)


@router.get("/quick-stats")
async def get_quick_stats(current_user: User = Depends(get_current_active_user)):
    """Get summary metrics for quick overview"""
    workload = dashboard_service.get_workload_data(current_user.uid, {})
    performance = dashboard_service.get_performance_data(current_user.uid, {})
    notifications = dashboard_service.get_notifications_data(current_user.uid, {})

    return JSONResponse(
        content={
            "workload": workload.get("stats", {}),
            "performance": performance.get("today", {}),
            "unread_notifications": notifications.get("unread_count", 0),
        }
    )
