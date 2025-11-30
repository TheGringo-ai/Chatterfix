"""
Team Collaboration Router
Handles team dashboard, messaging, parts requests, and user management
"""

from fastapi import (
    APIRouter,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Form,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core.database import get_db_connection
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team", tags=["team"])
templates = Jinja2Templates(directory="app/templates")

# ========== TEAM DASHBOARD ==========


@router.get("/", response_class=HTMLResponse)
async def team_dashboard(request: Request):
    """Team dashboard with live status and messaging"""
    conn = get_db_connection()
    try:
        # Get all team members
        users = conn.execute(
            """
            SELECT u.*,
                   COUNT(DISTINCT wo.id) as active_work_orders,
                   (SELECT COUNT(*) FROM user_skills WHERE user_id = u.id) as skill_count
            FROM users u
            LEFT JOIN work_orders wo ON wo.assigned_to = u.id AND wo.status != 'completed'
            GROUP BY u.id
            ORDER BY u.role, u.full_name
        """
        ).fetchall()

        # Get recent messages
        messages = conn.execute(
            """
            SELECT tm.*,
                   s.full_name as sender_name,
                   r.full_name as recipient_name
            FROM team_messages tm
            JOIN users s ON tm.sender_id = s.id
            LEFT JOIN users r ON tm.recipient_id = r.id
            ORDER BY tm.created_date DESC
            LIMIT 50
        """
        ).fetchall()

        # Get online users
        online_users = websocket_manager.get_online_users()

        return templates.TemplateResponse(
            "team_dashboard.html",
            {
                "request": request,
                "users": users,
                "messages": messages,
                "online_users": online_users,
            },
        )
    finally:
        conn.close()


# ========== WEBSOCKET ENDPOINT ==========


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket, user_id)

    # Update user status to online
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET status = 'available', last_seen = ? WHERE id = ?",
        (datetime.now(), user_id),
    )
    conn.commit()
    conn.close()

    # Broadcast user online status
    await websocket_manager.broadcast(
        {"type": "user_status", "user_id": user_id, "status": "online"}
    )

    try:
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            if data["type"] == "chat_message":
                # Save message to database
                conn = get_db_connection()
                conn.execute(
                    """
                    INSERT INTO team_messages
                    (sender_id, recipient_id, work_order_id, message_type, message, priority)
                    VALUES (?, ?, ?, 'chat', ?, ?)
                """,
                    (
                        user_id,
                        data.get("recipient_id"),
                        data.get("work_order_id"),
                        data["message"],
                        data.get("priority", "normal"),
                    ),
                )
                conn.commit()
                message_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.close()

                # Broadcast or send to specific user
                message_data = {
                    "type": "chat_message",
                    "id": message_id,
                    "sender_id": user_id,
                    "message": data["message"],
                    "timestamp": datetime.now().isoformat(),
                }

                if data.get("recipient_id"):
                    await websocket_manager.send_personal_message(
                        message_data, data["recipient_id"]
                    )
                else:
                    await websocket_manager.broadcast(
                        message_data, exclude_user=user_id
                    )

            elif data["type"] == "status_update":
                # Update user status
                conn = get_db_connection()
                conn.execute(
                    "UPDATE users SET status = ? WHERE id = ?",
                    (data["status"], user_id),
                )
                conn.commit()
                conn.close()

                await websocket_manager.broadcast(
                    {
                        "type": "user_status",
                        "user_id": user_id,
                        "status": data["status"],
                    }
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)

        # Update user status to offline
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET status = 'offline', last_seen = ? WHERE id = ?",
            (datetime.now(), user_id),
        )
        conn.commit()
        conn.close()

        # Broadcast user offline status
        await websocket_manager.broadcast(
            {"type": "user_status", "user_id": user_id, "status": "offline"}
        )


# ========== MESSAGING ==========


@router.get("/messages", response_class=JSONResponse)
async def get_messages(user_id: int = None, work_order_id: int = None, limit: int = 50):
    """Get messages, optionally filtered by user or work order"""
    conn = get_db_connection()
    try:
        query = """
            SELECT tm.*,
                   s.full_name as sender_name,
                   r.full_name as recipient_name
            FROM team_messages tm
            JOIN users s ON tm.sender_id = s.id
            LEFT JOIN users r ON tm.recipient_id = r.id
            WHERE 1=1
        """
        params = []

        if user_id:
            query += " AND (tm.sender_id = ? OR tm.recipient_id = ?)"
            params.extend([user_id, user_id])

        if work_order_id:
            query += " AND tm.work_order_id = ?"
            params.append(work_order_id)

        query += " ORDER BY tm.created_date DESC LIMIT ?"
        params.append(limit)

        messages = conn.execute(query, params).fetchall()
        return [dict(msg) for msg in messages]
    finally:
        conn.close()


@router.post("/messages")
async def send_message(
    sender_id: int = Form(...),
    message: str = Form(...),
    recipient_id: int = Form(None),
    work_order_id: int = Form(None),
    message_type: str = Form("chat"),
    priority: str = Form("normal"),
):
    """Send a message"""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO team_messages
            (sender_id, recipient_id, work_order_id, message_type, message, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (sender_id, recipient_id, work_order_id, message_type, message, priority),
        )
        conn.commit()
        message_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Send via WebSocket
        message_data = {
            "type": "chat_message",
            "id": message_id,
            "sender_id": sender_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        if recipient_id:
            await websocket_manager.send_personal_message(message_data, recipient_id)
        else:
            await websocket_manager.broadcast(message_data, exclude_user=sender_id)

        return {"success": True, "message_id": message_id}
    finally:
        conn.close()


# ========== PARTS REQUESTS ==========


@router.post("/parts-request")
async def create_parts_request(
    requester_id: int = Form(...),
    part_id: int = Form(...),
    quantity: int = Form(...),
    work_order_id: int = Form(None),
    priority: str = Form("normal"),
    notes: str = Form(None),
):
    """Create a parts request"""
    conn = get_db_connection()
    try:
        # Create request
        conn.execute(
            """
            INSERT INTO parts_requests
            (requester_id, work_order_id, part_id, quantity, priority, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
            (requester_id, work_order_id, part_id, quantity, priority, notes),
        )
        conn.commit()
        request_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Get part name
        part = conn.execute(
            "SELECT name FROM parts WHERE id = ?", (part_id,)
        ).fetchone()

        # Notify parts manager
        parts_managers = conn.execute(
            "SELECT id FROM users WHERE role = 'parts_manager'"
        ).fetchall()

        for manager in parts_managers:
            await notification_service.send_notification(
                user_id=manager[0],
                notification_type="parts_request",
                title="New Parts Request",
                message=f"{part[0]} - Qty: {quantity}",
                link=f"/inventory",
                priority=priority,
            )

        return {"success": True, "request_id": request_id}
    finally:
        conn.close()


@router.get("/parts-requests")
async def get_parts_requests(status: str = None):
    """Get parts requests"""
    conn = get_db_connection()
    try:
        query = """
            SELECT pr.*,
                   u.full_name as requester_name,
                   p.name as part_name,
                   p.part_number
            FROM parts_requests pr
            JOIN users u ON pr.requester_id = u.id
            JOIN parts p ON pr.part_id = p.id
        """
        params = []

        if status:
            query += " WHERE pr.status = ?"
            params.append(status)

        query += " ORDER BY pr.requested_date DESC"

        requests = conn.execute(query, params).fetchall()
        return [dict(req) for req in requests]
    finally:
        conn.close()


@router.post("/parts-requests/{request_id}/update-status")
async def update_parts_request_status(request_id: int, status: str = Form(...)):
    """Update parts request status"""
    conn = get_db_connection()
    try:
        # Get request details
        request = conn.execute(
            """
            SELECT pr.*, p.name as part_name
            FROM parts_requests pr
            JOIN parts p ON pr.part_id = p.id
            WHERE pr.id = ?
        """,
            (request_id,),
        ).fetchone()

        # Update status
        conn.execute(
            """
            UPDATE parts_requests
            SET status = ?, fulfilled_date = ?
            WHERE id = ?
        """,
            (status, datetime.now() if status == "delivered" else None, request_id),
        )
        conn.commit()

        # Notify requester if parts arrived
        if status == "arrived":
            await notification_service.notify_parts_arrived(
                requester_id=request["requester_id"],
                part_name=request["part_name"],
                work_order_id=request["work_order_id"],
            )

        return {"success": True}
    finally:
        conn.close()


# ========== USER MANAGEMENT ==========


@router.get("/users")
async def get_users(role: str = None):
    """Get all users"""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM users"
        params = []

        if role:
            query += " WHERE role = ?"
            params.append(role)

        query += " ORDER BY full_name"

        users = conn.execute(query, params).fetchall()
        return [dict(user) for user in users]
    finally:
        conn.close()


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_profile(request: Request, user_id: int):
    """User profile page"""
    conn = get_db_connection()
    try:
        # Get user info
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

        # Get skills
        skills = conn.execute(
            """
            SELECT * FROM user_skills WHERE user_id = ?
            ORDER BY proficiency_level DESC
        """,
            (user_id,),
        ).fetchall()

        # Get performance
        performance = conn.execute(
            """
            SELECT * FROM user_performance
            WHERE user_id = ?
            ORDER BY period_end DESC
            LIMIT 12
        """,
            (user_id,),
        ).fetchall()

        # Get training
        training = conn.execute(
            """
            SELECT ut.*, tm.title, tm.estimated_duration_minutes
            FROM user_training ut
            JOIN training_modules tm ON ut.training_module_id = tm.id
            WHERE ut.user_id = ?
            ORDER BY ut.started_date DESC
        """,
            (user_id,),
        ).fetchall()

        # Get work order stats
        wo_stats = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                AVG(CASE WHEN status = 'completed'
                    THEN julianday(completed_date) - julianday(created_date)
                    ELSE NULL END) as avg_completion_days
            FROM work_orders
            WHERE assigned_to = ?
        """,
            (user_id,),
        ).fetchone()

        return templates.TemplateResponse(
            "user_profile.html",
            {
                "request": request,
                "user": user,
                "skills": skills,
                "performance": performance,
                "training": training,
                "wo_stats": wo_stats,
            },
        )
    finally:
        conn.close()


# ========== NOTIFICATIONS ==========


@router.get("/notifications")
async def get_notifications(user_id: int, unread_only: bool = False):
    """Get user notifications"""
    notifications = notification_service.get_user_notifications(user_id, unread_only)
    return [dict(n) for n in notifications]


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    notification_service.mark_as_read(notification_id)
    return {"success": True}


@router.get("/notifications/unread-count")
async def get_unread_count(user_id: int):
    """Get unread notification count"""
    count = notification_service.get_unread_count(user_id)
    return {"count": count}
