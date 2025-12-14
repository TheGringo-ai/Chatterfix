import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.db_adapter import get_db_adapter
from app.core.firestore_db import get_firestore_manager


class DashboardService:
    """Service for managing dashboard widgets and data"""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    def get_user_dashboard_config(self, user_id: str) -> Dict[str, Any]:
        """Get user's dashboard configuration including widgets and layout"""
        # In a real app, this would be fetched from Firestore
        return {
            "user": {"id": user_id, "role": "technician", "theme": "dark"},
            "widgets": [
                {"widget_type": "workload", "title": "My Workload", "size": "medium"},
                {"widget_type": "performance", "title": "Performance", "size": "small"},
                {
                    "widget_type": "notifications",
                    "title": "Notifications",
                    "size": "small",
                },
            ],
        }

    async def get_widget_data(
        self, widget_type: str, user_id: str, config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get data for a specific widget type"""
        widget_methods = {
            "workload": self.get_workload_data,
            "performance": self.get_performance_data,
            "notifications": self.get_notifications_data,
            "equipment": self.get_equipment_data,
            "training": self.get_training_data,
        }

        method = widget_methods.get(widget_type)
        if method:
            return await method(user_id, config or {})
        else:
            return {"error": f"Unknown widget type: {widget_type}"}

    async def get_workload_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get today's work orders for the user"""
        work_orders = await self.firestore_manager.get_collection(
            "work_orders",
            filters=[{"field": "assigned_to_uid", "operator": "==", "value": user_id}]
        )
        
        stats = {
            "total": len(work_orders),
            "overdue": len([wo for wo in work_orders if wo.get("due_date") and datetime.fromisoformat(wo["due_date"]) < datetime.now()]),
            "due_today": len([wo for wo in work_orders if wo.get("due_date") and wo["due_date"] == datetime.now().date().isoformat()]),
            "in_progress": len([wo for wo in work_orders if wo.get("status") == "In Progress"]),
        }
        return {"work_orders": work_orders, "stats": stats}

    async def get_performance_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get performance metrics for the user"""
        # TODO: Refactor to calculate real performance data from Firestore
        return {
            "today": {"completed": 2, "avg_hours": 1.5},
            "this_week": {"completed": 12, "avg_hours": 1.8},
            "quality_score": 98, "safety_incidents": 0, "training_hours": 4,
        }

    async def get_notifications_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get recent notifications"""
        notifications = await self.firestore_manager.get_collection(
            "notifications",
            filters=[{"field": "user_id", "operator": "==", "value": user_id}],
            order_by="-timestamp", limit=10
        )
        unread_count = len([n for n in notifications if not n.get("is_read")])
        return {"notifications": notifications, "unread_count": unread_count}

    async def get_equipment_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get assigned equipment status"""
        # This logic is simplified. A real implementation would need a way to link users to assets.
        assets = await self.firestore_manager.get_collection("assets", limit=10)
        health_counts = {"good": 0, "fair": 0, "poor": 0, "critical": 0}
        for asset in assets:
            # A real health score would be more complex
            if asset.get("status") == "Active":
                health_counts["good"] += 1
            elif asset.get("status") == "Maintenance":
                health_counts["fair"] += 1
            else:
                health_counts["poor"] += 1
                
        return {"assets": assets, "health_counts": health_counts, "total": len(assets)}

    async def get_training_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get training status"""
        training = await self.firestore_manager.get_collection(
            "user_training",
            filters=[{"field": "user_id", "operator": "==", "value": user_id}, {"field": "status", "operator": "!=", "value": "completed"}],
            limit=5
        )
        return {"training": training, "due_count": len(training)}

    # Other methods remain for future refactoring
    def get_parts_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"requests": [], "arriving_today": 0, "pending": 0}
    def get_messages_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"messages": [], "unread_count": 0}
    def get_team_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"team_members": [], "status_counts": {"available": 0, "busy": 0, "offline": 0}, "total": 0}
    def get_quick_actions_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"actions": []}
    def get_ai_insights_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"insights": []}
    def get_quality_alerts_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"alerts": [], "count": 0}
    def get_inventory_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"low_stock": [], "pending_requests": 0}
    def get_approval_queue_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"pending_approvals": [], "count": 0}
    def get_analytics_data(self, user_id: int, config: Dict) -> Dict[str, Any]:
        return {"stats": {}, "period": "Last 30 days"}
    def update_widget_config(self, user_id: int, widget_id: int, config: Dict) -> bool:
        return True
    def save_dashboard_layout(self, user_id: int, widgets: List[Dict]) -> bool:
        return True

# Global instance
dashboard_service = DashboardService()
