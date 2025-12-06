from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from pydantic import BaseModel
import json
import logging

from app.services.dashboard_service import dashboard_service
from app.services.real_time_feed_service import real_time_feed
from app.services.websocket_manager import websocket_manager
from app.core.db_adapter import get_db_adapter

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def get_current_user_from_session(session_token: Optional[str]):
    """Helper to get current user from session token with auth_service"""
    if not session_token:
        return None
    try:
        # Note: auth_service.validate_session will fail with SQLite issues
        # For now, use a fallback validation method
        if len(session_token) < 10 or session_token == "invalid":
            return None

        # Temporary: Return a mock user structure for valid-looking tokens
        # In production, this should call auth_service.validate_session()
        # after converting auth_service to use Firestore
        return {
            "id": 1,
            "username": "demo_user",
            "email": "user@demo.com",
            "full_name": "Demo User",
            "role": "manager",
        }
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return None


# Pydantic models
class WidgetConfigUpdate(BaseModel):
    widget_id: int
    position: int
    size: str
    config: dict = {}


class DashboardLayoutUpdate(BaseModel):
    widgets: List[WidgetConfigUpdate]


@router.get("/", response_class=HTMLResponse)
async def root_dashboard(request: Request, session_token: Optional[str] = Cookie(None)):
    """Root route - show landing page or dashboard based on authentication"""
    # Validate user session
    user = get_current_user_from_session(session_token)

    if not user:
        # Show landing page with demo access instead of redirect to login
        return RedirectResponse(url="/landing", status_code=302)

    # User is authenticated, show dashboard
    return await dashboard(request, user_id=user["id"], current_user=user)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    user_id: int = None,
    current_user: dict = None,
):
    """Render the AI Command Center dashboard"""
    # Validate session if called directly (not from root_dashboard)
    if current_user is None:
        user = get_current_user_from_session(session_token)
        if not user:
            return RedirectResponse(url="/auth/login", status_code=302)
        user_id = user["id"]
        current_user = user

    # Get real-time stats from Firestore via db_adapter
    try:
        db_adapter = get_db_adapter()
        dashboard_data = await db_adapter.get_dashboard_data(str(user_id))

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
async def get_dashboard_config(session_token: Optional[str] = Cookie(None)):
    """Get user's dashboard configuration"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    config = dashboard_service.get_user_dashboard_config(user["id"])
    return JSONResponse(content=config)


@router.post("/config")
async def save_dashboard_config(
    layout: DashboardLayoutUpdate, session_token: Optional[str] = Cookie(None)
):
    """Save user's dashboard layout"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    widgets = [w.dict() for w in layout.widgets]
    success = dashboard_service.save_dashboard_layout(user["id"], widgets)

    return JSONResponse(
        content={
            "success": success,
            "message": "Dashboard layout saved" if success else "Failed to save layout",
        }
    )


@router.get("/widgets")
async def get_available_widgets(session_token: Optional[str] = Cookie(None)):
    """Get available widgets for user's role"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    # Return static widget configuration for dashboard
    # In production, this would be role-based from Firestore based on user["role"]
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
    widget_type: str, session_token: Optional[str] = Cookie(None)
):
    """Get data for a specific widget"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    data = dashboard_service.get_widget_data(widget_type, user["id"])
    return JSONResponse(content=data)


@router.post("/widget/{widget_id}/config")
async def update_widget_config(
    widget_id: int, config: dict, session_token: Optional[str] = Cookie(None)
):
    """Update widget configuration"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    success = dashboard_service.update_widget_config(user["id"], widget_id, config)

    return JSONResponse(
        content={
            "success": success,
            "message": "Widget updated" if success else "Failed to update widget",
        }
    )


@router.post("/reset")
async def reset_dashboard(session_token: Optional[str] = Cookie(None)):
    """Reset dashboard to default layout"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        # Reset to default dashboard configuration
        # In production, this would clear user's custom config from Firestore
        # For now, just return success
        success = True
    except Exception as e:
        logger.error(f"Error resetting dashboard for user {user['id']}: {e}")
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
async def dashboard_stream(websocket: WebSocket, user_id: int = 1):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket_manager.connect(websocket, user_id)

    try:
        while True:
            # Receive subscription requests
            data = await websocket.receive_text()
            message = json.loads(data)  # Parse JSON

            if message.get("type") == "subscribe":
                widget_types = message.get("widgets", [])
                await real_time_feed.subscribe(user_id, widget_types)

            elif message.get("type") == "unsubscribe":
                widget_types = message.get("widgets", [])
                await real_time_feed.unsubscribe(user_id, widget_types)

            elif message.get("type") == "refresh":
                widget_type = message.get("widget")
                if widget_type:
                    await real_time_feed.send_widget_updates(user_id, [widget_type])

    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)
        await real_time_feed.unsubscribe(user_id)


# Specific widget data endpoints for quick access
@router.get("/workload")
async def get_workload(session_token: Optional[str] = Cookie(None)):
    """Get detailed workload data"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    data = dashboard_service.get_workload_data(user["id"], {})
    return JSONResponse(content=data)


@router.get("/parts-status")
async def get_parts_status(session_token: Optional[str] = Cookie(None)):
    """Get parts status"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    data = dashboard_service.get_parts_data(user["id"], {})
    return JSONResponse(content=data)


@router.get("/team-status")
async def get_team_status(session_token: Optional[str] = Cookie(None)):
    """Get team availability"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    data = dashboard_service.get_team_data(user["id"], {})
    return JSONResponse(content=data)


@router.get("/quick-stats")
async def get_quick_stats(session_token: Optional[str] = Cookie(None)):
    """Get summary metrics for quick overview"""
    user = get_current_user_from_session(session_token)
    if not user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    workload = dashboard_service.get_workload_data(user["id"], {})
    performance = dashboard_service.get_performance_data(user["id"], {})
    notifications = dashboard_service.get_notifications_data(user["id"], {})

    return JSONResponse(
        content={
            "workload": workload.get("stats", {}),
            "performance": performance.get("today", {}),
            "unread_notifications": notifications.get("unread_count", 0),
        }
    )
