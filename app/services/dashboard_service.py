"""
Dashboard Service - Widget Data Aggregation
Provides data for all dashboard widgets based on user role and configuration
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.core.database import get_db_connection
from app.core.db_adapter import get_db_adapter


class DashboardService:
    """Service for managing dashboard widgets and data"""

    def __init__(self):
        self.conn = None

    def get_user_dashboard_config(self, user_id: int) -> Dict[str, Any]:
        """Get user's dashboard configuration including widgets and layout"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get user info and preferences
        user = cur.execute(
            """
            SELECT id, role, dashboard_layout, theme, refresh_interval
            FROM users WHERE id = ?
        """,
            (user_id,),
        ).fetchone()

        if not user:
            conn.close()
            return {"error": "User not found"}

        user_dict = dict(user)

        # Get user's configured widgets
        widgets = cur.execute(
            """
            SELECT
                udc.id as config_id,
                udc.position,
                udc.size,
                udc.config,
                udc.is_visible,
                dw.widget_type,
                dw.title,
                dw.description
            FROM user_dashboard_config udc
            JOIN dashboard_widgets dw ON udc.widget_id = dw.id
            WHERE udc.user_id = ? AND udc.is_visible = 1
            ORDER BY udc.position
        """,
            (user_id,),
        ).fetchall()

        # If no widgets configured, get defaults for role
        if not widgets:
            widgets = self._get_default_widgets_for_role(user_dict["role"])

        conn.close()

        return {
            "user": user_dict,
            "widgets": [dict(w) for w in widgets],
            "layout": user_dict.get("dashboard_layout", "grid"),
            "theme": user_dict.get("theme", "dark"),
            "refresh_interval": user_dict.get("refresh_interval", 30),
        }

    def _get_default_widgets_for_role(self, role: str) -> List[Any]:
        """Get default widgets for a specific role"""
        conn = get_db_connection()
        cur = conn.cursor()

        widgets = cur.execute(
            """
            SELECT
                id,
                widget_type,
                title,
                description,
                'medium' as size,
                1 as is_visible
            FROM dashboard_widgets
            WHERE default_roles LIKE ?
            ORDER BY id
        """,
            (f'%"{role}"%',),
        ).fetchall()

        conn.close()
        return widgets

    def get_widget_data(
        self, widget_type: str, user_id: int, config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get data for a specific widget type"""

        widget_methods = {
            "workload": self.get_workload_data,
            "parts_status": self.get_parts_data,
            "messages": self.get_messages_data,
            "performance": self.get_performance_data,
            "equipment": self.get_equipment_data,
            "notifications": self.get_notifications_data,
            "team_status": self.get_team_data,
            "training": self.get_training_data,
            "quick_actions": self.get_quick_actions_data,
            "ai_insights": self.get_ai_insights_data,
            "quality_alerts": self.get_quality_alerts_data,
            "inventory_overview": self.get_inventory_data,
            "approval_queue": self.get_approval_queue_data,
            "analytics": self.get_analytics_data,
        }

        method = widget_methods.get(widget_type)
        if method:
            return method(user_id, config or {})
        else:
            return {"error": f"Unknown widget type: {widget_type}"}

    def get_workload_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get today's work orders for the user"""
        conn = get_db_connection()
        cur = conn.cursor()

        today = datetime.now().date()

        # Get assigned work orders
        work_orders = cur.execute(
            """
            SELECT
                id,
                title,
                description,
                priority,
                status,
                due_date,
                estimated_duration,
                actual_start_time,
                blocked_reason,
                location,
                asset_id
            FROM work_orders
            WHERE assigned_to = ?
            AND status NOT IN ('completed', 'cancelled')
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                due_date
        """,
            (user_id,),
        ).fetchall()

        # Get stats
        stats = {
            "total": len(work_orders),
            "overdue": 0,
            "due_today": 0,
            "blocked": 0,
            "in_progress": 0,
        }

        wo_list = []
        for wo in work_orders:
            wo_dict = dict(wo)

            # Calculate status
            if wo_dict["blocked_reason"]:
                stats["blocked"] += 1
                wo_dict["status_label"] = "blocked"
            elif wo_dict["actual_start_time"]:
                stats["in_progress"] += 1
                wo_dict["status_label"] = "in_progress"
            else:
                wo_dict["status_label"] = "pending"

            # Check if overdue or due today
            if wo_dict["due_date"]:
                due_date = datetime.strptime(wo_dict["due_date"], "%Y-%m-%d").date()
                if due_date < today:
                    stats["overdue"] += 1
                    wo_dict["urgency"] = "overdue"
                elif due_date == today:
                    stats["due_today"] += 1
                    wo_dict["urgency"] = "today"
                else:
                    wo_dict["urgency"] = "upcoming"

            wo_list.append(wo_dict)

        conn.close()

        return {"work_orders": wo_list, "stats": stats}

    def get_parts_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get parts status for the user"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get user's parts requests
        requests = cur.execute(
            """
            SELECT
                pr.id,
                pr.quantity,
                pr.priority,
                pr.status,
                pr.requested_date,
                pr.fulfilled_date,
                p.name as part_name,
                p.part_number,
                wo.title as work_order_title
            FROM parts_requests pr
            JOIN parts p ON pr.part_id = p.id
            LEFT JOIN work_orders wo ON pr.work_order_id = wo.id
            WHERE pr.requester_id = ?
            AND pr.status != 'delivered'
            ORDER BY pr.requested_date DESC
            LIMIT 10
        """,
            (user_id,),
        ).fetchall()

        # Get arriving today (status = 'arrived')
        arriving_today = cur.execute(
            """
            SELECT COUNT(*) as count
            FROM parts_requests
            WHERE requester_id = ? AND status = 'arrived'
        """,
            (user_id,),
        ).fetchone()

        # Get pending count
        pending = cur.execute(
            """
            SELECT COUNT(*) as count
            FROM parts_requests
            WHERE requester_id = ? AND status = 'pending'
        """,
            (user_id,),
        ).fetchone()

        conn.close()

        return {
            "requests": [dict(r) for r in requests],
            "arriving_today": arriving_today["count"] if arriving_today else 0,
            "pending": pending["count"] if pending else 0,
        }

    def get_messages_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get recent messages for the user"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get unread messages
        messages = cur.execute(
            """
            SELECT
                tm.id,
                tm.message,
                tm.priority,
                tm.created_date,
                tm.read,
                u.full_name as sender_name,
                u.username as sender_username
            FROM team_messages tm
            JOIN users u ON tm.sender_id = u.id
            WHERE (tm.recipient_id = ? OR tm.recipient_id IS NULL)
            AND tm.sender_id != ?
            ORDER BY tm.created_date DESC
            LIMIT 20
        """,
            (user_id, user_id),
        ).fetchall()

        # Get unread count
        unread_count = cur.execute(
            """
            SELECT COUNT(*) as count
            FROM team_messages
            WHERE (recipient_id = ? OR recipient_id IS NULL)
            AND sender_id != ?
            AND read = 0
        """,
            (user_id, user_id),
        ).fetchone()

        conn.close()

        return {
            "messages": [dict(m) for m in messages],
            "unread_count": unread_count["count"] if unread_count else 0,
        }

    def get_performance_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get performance metrics for the user"""
        conn = get_db_connection()
        cur = conn.cursor()

        datetime.now().date()

        # Today's completions
        today_stats = cur.execute(
            """
            SELECT
                COUNT(*) as completed,
                AVG(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as avg_hours
            FROM work_orders
            WHERE assigned_to = ?
            AND status = 'completed'
            AND DATE(actual_end) = DATE('now')
        """,
            (user_id,),
        ).fetchone()

        # This week's stats
        week_stats = cur.execute(
            """
            SELECT
                COUNT(*) as completed,
                AVG(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as avg_hours
            FROM work_orders
            WHERE assigned_to = ?
            AND status = 'completed'
            AND DATE(actual_end) >= DATE('now', '-7 days')
        """,
            (user_id,),
        ).fetchone()

        # Get latest performance record
        performance = cur.execute(
            """
            SELECT quality_score, safety_incidents, training_hours
            FROM user_performance
            WHERE user_id = ?
            ORDER BY period_end DESC
            LIMIT 1
        """,
            (user_id,),
        ).fetchone()

        conn.close()

        return {
            "today": {
                "completed": today_stats["completed"] if today_stats else 0,
                "avg_hours": (
                    round(today_stats["avg_hours"], 1)
                    if today_stats and today_stats["avg_hours"]
                    else 0
                ),
            },
            "this_week": {
                "completed": week_stats["completed"] if week_stats else 0,
                "avg_hours": (
                    round(week_stats["avg_hours"], 1)
                    if week_stats and week_stats["avg_hours"]
                    else 0
                ),
            },
            "quality_score": performance["quality_score"] if performance else 0,
            "safety_incidents": performance["safety_incidents"] if performance else 0,
            "training_hours": performance["training_hours"] if performance else 0,
        }

    def get_equipment_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get assigned equipment status"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get assets assigned to user (via active work orders)
        assets = cur.execute(
            """
            SELECT DISTINCT
                a.id,
                a.name,
                a.asset_id,
                a.status,
                a.condition,
                a.criticality,
                a.next_maintenance_date
            FROM assets a
            JOIN work_orders wo ON a.id = wo.asset_id
            WHERE wo.assigned_to = ?
            AND wo.status NOT IN ('completed', 'cancelled')
            ORDER BY a.criticality DESC, a.next_maintenance_date
            LIMIT 10
        """,
            (user_id,),
        ).fetchall()

        # Count by health status
        health_counts = {"good": 0, "fair": 0, "poor": 0, "critical": 0}
        asset_list = []

        for asset in assets:
            asset_dict = dict(asset)
            condition = asset_dict.get("condition", "").lower()

            if condition == "excellent" or condition == "good":
                health_counts["good"] += 1
                asset_dict["health"] = "good"
            elif condition == "fair":
                health_counts["fair"] += 1
                asset_dict["health"] = "fair"
            elif condition == "poor":
                health_counts["poor"] += 1
                asset_dict["health"] = "poor"
            else:
                health_counts["critical"] += 1
                asset_dict["health"] = "critical"

            asset_list.append(asset_dict)

        conn.close()

        return {
            "assets": asset_list,
            "health_counts": health_counts,
            "total": len(asset_list),
        }

    def get_notifications_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get recent notifications"""
        conn = get_db_connection()
        cur = conn.cursor()

        notifications = cur.execute(
            """
            SELECT
                id,
                notification_type,
                title,
                message,
                link,
                priority,
                read,
                created_date
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_date DESC
            LIMIT 10
        """,
            (user_id,),
        ).fetchall()

        unread_count = cur.execute(
            """
            SELECT COUNT(*) as count
            FROM notifications
            WHERE user_id = ? AND read = 0
        """,
            (user_id,),
        ).fetchone()

        conn.close()

        return {
            "notifications": [dict(n) for n in notifications],
            "unread_count": unread_count["count"] if unread_count else 0,
        }

    def get_team_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get team status and availability"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all team members
        team_members = cur.execute(
            """
            SELECT
                id,
                username,
                full_name,
                role,
                status,
                last_seen
            FROM users
            WHERE id != ?
            ORDER BY status DESC, full_name
        """,
            (user_id,),
        ).fetchall()

        # Count by status
        status_counts = {"available": 0, "busy": 0, "offline": 0}
        members_list = []

        for member in team_members:
            member_dict = dict(member)
            status = member_dict.get("status", "offline")
            status_counts[status] = status_counts.get(status, 0) + 1
            members_list.append(member_dict)

        conn.close()

        return {
            "team_members": members_list,
            "status_counts": status_counts,
            "total": len(members_list),
        }

    def get_training_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get training status"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get assigned training
        training = cur.execute(
            """
            SELECT
                ut.id,
                ut.status,
                ut.score,
                tm.title,
                tm.description,
                tm.estimated_duration_minutes,
                tm.difficulty_level
            FROM user_training ut
            JOIN training_modules tm ON ut.training_module_id = tm.id
            WHERE ut.user_id = ?
            AND ut.status != 'completed'
            ORDER BY ut.id DESC
            LIMIT 5
        """,
            (user_id,),
        ).fetchall()

        conn.close()

        return {"training": [dict(t) for t in training], "due_count": len(training)}

    def get_quick_actions_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get quick action buttons"""
        return {
            "actions": [
                {
                    "id": "report_emergency",
                    "label": "Report Emergency",
                    "icon": "🚨",
                    "color": "danger",
                },
                {
                    "id": "request_parts",
                    "label": "Request Parts",
                    "icon": "📦",
                    "color": "primary",
                },
                {
                    "id": "clock_in",
                    "label": "Clock In/Out",
                    "icon": "🕐",
                    "color": "info",
                },
                {
                    "id": "start_break",
                    "label": "Start Break",
                    "icon": "☕",
                    "color": "warning",
                },
                {"id": "ar_mode", "label": "AR Mode", "icon": "🥽", "color": "success"},
                {
                    "id": "submit_feedback",
                    "label": "Submit Feedback",
                    "icon": "💬",
                    "color": "secondary",
                },
            ]
        }

    def get_ai_insights_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get AI-powered insights and predictions"""
        # Placeholder - would integrate with predictive engine
        return {
            "insights": [
                {
                    "type": "prediction",
                    "message": "Pump #5 may fail within 7 days",
                    "confidence": 0.85,
                    "priority": "high",
                },
                {
                    "type": "recommendation",
                    "message": "Schedule PM for HVAC Unit 3 this week",
                    "confidence": 0.92,
                    "priority": "medium",
                },
            ]
        }

    def get_quality_alerts_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get quality alerts and recurring issues"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get recent feedback with issues
        alerts = cur.execute(
            """
            SELECT
                wf.id,
                wf.feedback_type,
                wf.description,
                wf.time_to_failure_hours,
                wf.created_date,
                a.name as asset_name,
                u.full_name as technician_name
            FROM work_order_feedback wf
            JOIN assets a ON wf.asset_id = a.id
            JOIN users u ON wf.technician_id = u.id
            WHERE wf.feedback_type IN ('immediate_failure', 'quality_concern')
            ORDER BY wf.created_date DESC
            LIMIT 10
        """
        ).fetchall()

        conn.close()

        return {"alerts": [dict(a) for a in alerts], "count": len(alerts)}

    def get_inventory_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get inventory overview for parts manager"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get low stock items
        low_stock = cur.execute(
            """
            SELECT
                id,
                name,
                part_number,
                quantity,
                min_quantity,
                location
            FROM parts
            WHERE quantity <= min_quantity
            ORDER BY (quantity - min_quantity)
            LIMIT 10
        """
        ).fetchall()

        # Get pending requests
        pending_requests = cur.execute(
            """
            SELECT COUNT(*) as count
            FROM parts_requests
            WHERE status = 'pending'
        """
        ).fetchone()

        conn.close()

        return {
            "low_stock": [dict(p) for p in low_stock],
            "pending_requests": pending_requests["count"] if pending_requests else 0,
        }

    def get_approval_queue_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get items needing approval"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get pending parts requests
        requests = cur.execute(
            """
            SELECT
                pr.id,
                pr.quantity,
                pr.priority,
                pr.requested_date,
                p.name as part_name,
                u.full_name as requester_name
            FROM parts_requests pr
            JOIN parts p ON pr.part_id = p.id
            JOIN users u ON pr.requester_id = u.id
            WHERE pr.status = 'pending'
            ORDER BY pr.priority DESC, pr.requested_date
            LIMIT 10
        """
        ).fetchall()

        conn.close()

        return {
            "pending_approvals": [dict(r) for r in requests],
            "count": len(requests),
        }

    def get_analytics_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get analytics and metrics for managers"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get overall stats
        stats = cur.execute(
            """
            SELECT
                COUNT(*) as total_work_orders,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM work_orders
            WHERE DATE(created_date) >= DATE('now', '-30 days')
        """
        ).fetchone()

        conn.close()

        return {"stats": dict(stats) if stats else {}, "period": "Last 30 days"}

    def update_widget_config(self, user_id: int, widget_id: int, config: Dict) -> bool:
        """Update widget configuration for a user"""
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                UPDATE user_dashboard_config
                SET config = ?, size = ?, position = ?
                WHERE user_id = ? AND widget_id = ?
            """,
                (
                    json.dumps(config.get("config", {})),
                    config.get("size", "medium"),
                    config.get("position", 0),
                    user_id,
                    widget_id,
                ),
            )
            conn.commit()
            success = cur.rowcount > 0
        except Exception as e:
            print(f"Error updating widget config: {e}")
            success = False
        finally:
            conn.close()

        return success

    def save_dashboard_layout(self, user_id: int, widgets: List[Dict]) -> bool:
        """Save user's dashboard layout"""
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Delete existing config
            cur.execute(
                "DELETE FROM user_dashboard_config WHERE user_id = ?", (user_id,)
            )

            # Insert new config
            for widget in widgets:
                cur.execute(
                    """
                    INSERT INTO user_dashboard_config (user_id, widget_id, position, size, config, is_visible)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        widget["widget_id"],
                        widget.get("position", 0),
                        widget.get("size", "medium"),
                        json.dumps(widget.get("config", {})),
                        widget.get("is_visible", 1),
                    ),
                )

            conn.commit()
            success = True
        except Exception as e:
            print(f"Error saving dashboard layout: {e}")
            conn.rollback()
            success = False
        finally:
            conn.close()

        return success

    async def get_dashboard_data_async(self, user_id: str = None) -> Dict[str, Any]:
        """Get dashboard data using the database adapter (async)"""
        db = get_db_adapter()
        return await db.get_dashboard_data(user_id)

    async def create_work_order_async(self, work_order_data: Dict[str, Any]) -> str:
        """Create work order using the database adapter (async)"""
        db = get_db_adapter()
        return await db.create_work_order(work_order_data)

    async def get_work_orders_async(
        self, status: str = None, assigned_to: str = None
    ) -> List[Dict[str, Any]]:
        """Get work orders using the database adapter (async)"""
        db = get_db_adapter()
        return await db.get_work_orders(status, assigned_to)

    async def create_asset_async(self, asset_data: Dict[str, Any]) -> str:
        """Create asset using the database adapter (async)"""
        db = get_db_adapter()
        return await db.create_asset(asset_data)

    async def get_assets_async(
        self, status: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        """Get assets using the database adapter (async)"""
        db = get_db_adapter()
        return await db.get_assets(status, location)


# Global instance
dashboard_service = DashboardService()
