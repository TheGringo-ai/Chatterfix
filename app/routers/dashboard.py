from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from pydantic import BaseModel

from app.services.dashboard_service import dashboard_service
from app.services.real_time_feed_service import real_time_feed
from app.services.websocket_manager import websocket_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Pydantic models
class WidgetConfigUpdate(BaseModel):
    widget_id: int
    position: int
    size: str
    config: dict = {}

class DashboardLayoutUpdate(BaseModel):
    widgets: List[WidgetConfigUpdate]

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: int = 1):
    """Render the AI Command Center dashboard"""
    # Get real-time stats for the dashboard
    try:
        workload = dashboard_service.get_workload_data(user_id, {})
    except Exception as e:
        print(f"Error fetching workload data: {e}")
        workload = {"stats": {"active": 0, "pending": 0, "completed": 0}}

    try:
        performance = dashboard_service.get_performance_data(user_id, {})
    except Exception as e:
        print(f"Error fetching performance data: {e}")
        performance = {"today": {"completion_rate": 0}}

    try:
        notifications = dashboard_service.get_notifications_data(user_id, {})
    except Exception as e:
        print(f"Error fetching notifications data: {e}")
        notifications = {"unread_count": 0}

    try:
        equipment = dashboard_service.get_equipment_data(user_id, {})
    except Exception as e:
        print(f"Error fetching equipment data: {e}")
        equipment = {}
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "workload": workload,
        "performance": performance,
        "notifications": notifications,
        "equipment": equipment
    })

@router.get("/config")
async def get_dashboard_config(user_id: int = 1):
    """Get user's dashboard configuration"""
    config = dashboard_service.get_user_dashboard_config(user_id)
    return JSONResponse(content=config)

@router.post("/config")
async def save_dashboard_config(layout: DashboardLayoutUpdate, user_id: int = 1):
    """Save user's dashboard layout"""
    widgets = [w.dict() for w in layout.widgets]
    success = dashboard_service.save_dashboard_layout(user_id, widgets)
    
    return JSONResponse(content={
        "success": success,
        "message": "Dashboard layout saved" if success else "Failed to save layout"
    })

@router.get("/widgets")
async def get_available_widgets(user_id: int = 1):
    """Get available widgets for user's role"""
    # This would filter based on user role
    # For now, return all widgets
    from app.core.database import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    widgets = cur.execute("""
        SELECT id, widget_type, title, description, default_roles
        FROM dashboard_widgets
        ORDER BY title
    """).fetchall()
    
    conn.close()
    
    return JSONResponse(content={
        "widgets": [dict(w) for w in widgets]
    })

@router.get("/widget/{widget_type}/data")
async def get_widget_data(widget_type: str, user_id: int = 1):
    """Get data for a specific widget"""
    data = dashboard_service.get_widget_data(widget_type, user_id)
    return JSONResponse(content=data)

@router.post("/widget/{widget_id}/config")
async def update_widget_config(widget_id: int, config: dict, user_id: int = 1):
    """Update widget configuration"""
    success = dashboard_service.update_widget_config(user_id, widget_id, config)
    
    return JSONResponse(content={
        "success": success,
        "message": "Widget updated" if success else "Failed to update widget"
    })

@router.post("/reset")
async def reset_dashboard(user_id: int = 1):
    """Reset dashboard to default layout"""
    from app.core.database import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Delete user's custom config
        cur.execute("DELETE FROM user_dashboard_config WHERE user_id = ?", (user_id,))
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error resetting dashboard: {e}")
        success = False
    finally:
        conn.close()
    
    return JSONResponse(content={
        "success": success,
        "message": "Dashboard reset to defaults" if success else "Failed to reset dashboard"
    })

# Real-time data endpoints
@router.websocket("/stream")
async def dashboard_stream(websocket: WebSocket, user_id: int = 1):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive subscription requests
            data = await websocket.receive_text()
            message = eval(data)  # Parse JSON
            
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
async def get_workload(user_id: int = 1):
    """Get detailed workload data"""
    data = dashboard_service.get_workload_data(user_id, {})
    return JSONResponse(content=data)

@router.get("/parts-status")
async def get_parts_status(user_id: int = 1):
    """Get parts status"""
    data = dashboard_service.get_parts_data(user_id, {})
    return JSONResponse(content=data)

@router.get("/team-status")
async def get_team_status(user_id: int = 1):
    """Get team availability"""
    data = dashboard_service.get_team_data(user_id, {})
    return JSONResponse(content=data)

@router.get("/quick-stats")
async def get_quick_stats(user_id: int = 1):
    """Get summary metrics for quick overview"""
    workload = dashboard_service.get_workload_data(user_id, {})
    performance = dashboard_service.get_performance_data(user_id, {})
    notifications = dashboard_service.get_notifications_data(user_id, {})
    
    return JSONResponse(content={
        "workload": workload.get("stats", {}),
        "performance": performance.get("today", {}),
        "unread_notifications": notifications.get("unread_count", 0)
    })
