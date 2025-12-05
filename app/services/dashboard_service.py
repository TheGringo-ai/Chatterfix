"""
Dashboard Service - Widget Data Aggregation
Provides data for all dashboard widgets based on user role and configuration
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
# # from app.core.database import get_db_connection
from app.core.db_adapter import get_db_adapter


class DashboardService:
    """Service for managing dashboard widgets and data"""

    def __init__(self):
        self.conn = None

    def get_user_dashboard_config(self, user_id: int) -> Dict[str, Any]:
        """Get user's dashboard configuration including widgets and layout"""
        # Mock configuration for now to avoid DB errors
        return {
            "user": {"id": user_id, "role": "technician", "theme": "dark"},
            "widgets": [
                {"widget_type": "workload", "title": "My Workload", "size": "medium"},
                {"widget_type": "performance", "title": "Performance", "size": "small"},
                {"widget_type": "notifications", "title": "Notifications", "size": "small"}
            ],
            "layout": "grid",
            "theme": "dark",
            "refresh_interval": 30,
        }

    def _get_default_widgets_for_role(self, role: str) -> List[Any]:
        """Get default widgets for a specific role"""
        return []

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
        # Mock data for now
        today = datetime.now().date()
        
        stats = {
            "total": 3,
            "overdue": 1,
            "due_today": 1,
            "blocked": 0,
            "in_progress": 1,
        }
        
        wo_list = [
            {
                "id": 101,
                "title": "Inspect HVAC Unit 3",
                "description": "Routine inspection",
                "priority": "high",
                "status": "in_progress",
                "due_date": str(today),
                "estimated_duration": 60,
                "actual_start_time": "2023-10-27 09:00:00",
                "blocked_reason": None,
                "location": "Building A, Roof",
                "asset_id": "HVAC-003",
                "status_label": "in_progress",
                "urgency": "today"
            },
            {
                "id": 102,
                "title": "Replace Filter on AHU-1",
                "description": "Filter is clogged",
                "priority": "medium",
                "status": "pending",
                "due_date": str(today - timedelta(days=1)),
                "estimated_duration": 30,
                "actual_start_time": None,
                "blocked_reason": None,
                "location": "Building B, Basement",
                "asset_id": "AHU-001",
                "status_label": "pending",
                "urgency": "overdue"
            },
            {
                "id": 103,
                "title": "Check Generator Fuel",
                "description": "Monthly check",
                "priority": "low",
                "status": "pending",
                "due_date": str(today + timedelta(days=1)),
                "estimated_duration": 15,
                "actual_start_time": None,
                "blocked_reason": None,
                "location": "Building C, Exterior",
                "asset_id": "GEN-001",
                "status_label": "pending",
                "urgency": "upcoming"
            }
        ]

        return {"work_orders": wo_list, "stats": stats}

    def get_parts_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get parts status for the user"""
        # Mock data
        return {
            "requests": [],
            "arriving_today": 0,
            "pending": 0,
        }

    def get_messages_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get recent messages for the user"""
        # Mock data
        return {
            "messages": [],
            "unread_count": 0,
        }

    def get_performance_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get performance metrics for the user"""
        # Mock data
        return {
            "today": {
                "completed": 2,
                "avg_hours": 1.5,
            },
            "this_week": {
                "completed": 12,
                "avg_hours": 1.8,
            },
            "quality_score": 98,
            "safety_incidents": 0,
            "training_hours": 4,
        }

    def get_equipment_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get assigned equipment status"""
        # Mock data
        return {
            "assets": [],
            "health_counts": {"good": 0, "fair": 0, "poor": 0, "critical": 0},
            "total": 0,
        }

    def get_notifications_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get recent notifications"""
        # Mock data
        return {
            "notifications": [],
            "unread_count": 0,
        }

    def get_team_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get team status and availability"""
        # Mock data
        return {
            "team_members": [],
            "status_counts": {"available": 0, "busy": 0, "offline": 0},
            "total": 0,
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
        # Mock data
        return {"alerts": [], "count": 0}

    def get_inventory_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get inventory overview for parts manager"""
        # Mock data
        return {
            "low_stock": [],
            "pending_requests": 0,
        }

    def get_approval_queue_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get items needing approval"""
        # Mock data
        return {
            "pending_approvals": [],
            "count": 0,
        }

    def get_analytics_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        """Get analytics and metrics for managers"""
        # Mock data
        return {"stats": {}, "period": "Last 30 days"}

    def update_widget_config(self, user_id: int, widget_id: int, config: Dict) -> bool:
        """Update widget configuration for a user"""
        # Mock success
        return True

    def save_dashboard_layout(self, user_id: int, widgets: List[Dict]) -> bool:
        """Save user's dashboard layout"""
        # Mock success
        return True

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
