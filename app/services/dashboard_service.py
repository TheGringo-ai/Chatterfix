from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import logging

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for managing dashboard widgets and data"""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    # Standardized status values for consistency
    WORK_ORDER_STATUSES = ["Open", "In Progress", "Completed", "On Hold", "Cancelled"]
    ASSET_STATUSES = ["Operational", "Warning", "Critical", "Maintenance", "Offline"]

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
            filters=[{"field": "assigned_to_uid", "operator": "==", "value": user_id}],
        )

        stats = {
            "total": len(work_orders),
            "overdue": len(
                [
                    wo
                    for wo in work_orders
                    if wo.get("due_date")
                    and datetime.fromisoformat(wo["due_date"]) < datetime.now()
                ]
            ),
            "due_today": len(
                [
                    wo
                    for wo in work_orders
                    if wo.get("due_date")
                    and wo["due_date"] == datetime.now().date().isoformat()
                ]
            ),
            "in_progress": len(
                [wo for wo in work_orders if wo.get("status") == "In Progress"]
            ),
        }
        return {"work_orders": work_orders, "stats": stats}

    async def get_performance_data(self, user_id: str, config: Dict, organization_id: str = None) -> Dict[str, Any]:
        """Get performance metrics for the user from Firestore"""
        try:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())

            filters = [{"field": "assigned_to_uid", "operator": "==", "value": user_id}]
            if organization_id:
                filters.append({"field": "organization_id", "operator": "==", "value": organization_id})

            work_orders = await self.firestore_manager.get_collection("work_orders", filters=filters)

            # Calculate today's stats
            today_completed = 0
            today_hours = 0
            week_completed = 0
            week_hours = 0

            for wo in work_orders:
                if wo.get("status") == "Completed":
                    completed_at = wo.get("completed_at")
                    if completed_at:
                        try:
                            if isinstance(completed_at, str):
                                completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                            else:
                                completed_dt = completed_at

                            hours = wo.get("labor_hours", 0) or wo.get("estimated_hours", 2)

                            if completed_dt >= today_start:
                                today_completed += 1
                                today_hours += hours
                            if completed_dt >= week_start:
                                week_completed += 1
                                week_hours += hours
                        except (ValueError, TypeError, AttributeError):
                            # ValueError: invalid datetime format
                            # TypeError: non-string/datetime value
                            # AttributeError: missing expected attributes
                            pass

            return {
                "today": {
                    "completed": today_completed,
                    "avg_hours": round(today_hours / today_completed, 1) if today_completed > 0 else 0
                },
                "this_week": {
                    "completed": week_completed,
                    "avg_hours": round(week_hours / week_completed, 1) if week_completed > 0 else 0
                },
                "quality_score": 98,  # Would need quality tracking system
                "safety_incidents": 0,  # Would need safety incident tracking
                "training_hours": 4,  # Would need training time tracking
            }
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return {
                "today": {"completed": 0, "avg_hours": 0},
                "this_week": {"completed": 0, "avg_hours": 0},
                "quality_score": 0,
                "safety_incidents": 0,
                "training_hours": 0,
            }

    async def get_notifications_data(
        self, user_id: str, config: Dict
    ) -> Dict[str, Any]:
        """Get recent notifications"""
        notifications = await self.firestore_manager.get_collection(
            "notifications",
            filters=[{"field": "user_id", "operator": "==", "value": user_id}],
            order_by="-timestamp",
            limit=10,
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
            filters=[
                {"field": "user_id", "operator": "==", "value": user_id},
                {"field": "status", "operator": "!=", "value": "completed"},
            ],
            limit=5,
        )
        return {"training": training, "due_count": len(training)}

    # Org-scoped methods for real data
    async def get_parts_data(self, user_id: str, config: Dict, organization_id: str = None) -> Dict[str, Any]:
        """Get parts/inventory status from Firestore"""
        try:
            filters = []
            if organization_id:
                filters.append({"field": "organization_id", "operator": "==", "value": organization_id})

            parts = await self.firestore_manager.get_collection("parts", filters=filters if filters else None)

            low_stock = []
            for part in parts:
                current = part.get("current_stock", 0)
                minimum = part.get("minimum_stock", 5)
                if current <= minimum:
                    low_stock.append({
                        "id": part.get("id"),
                        "name": part.get("name"),
                        "current_stock": current,
                        "minimum_stock": minimum,
                        "status": "critical" if current == 0 else "low"
                    })

            return {
                "total_parts": len(parts),
                "low_stock": low_stock[:10],
                "low_stock_count": len(low_stock),
                "arriving_today": 0,  # Would need purchase order tracking
                "pending_requests": 0,
            }
        except Exception as e:
            logger.error(f"Error getting parts data: {e}")
            return {"total_parts": 0, "low_stock": [], "low_stock_count": 0, "arriving_today": 0, "pending_requests": 0}

    async def get_team_data(self, user_id: str, config: Dict, organization_id: str = None) -> Dict[str, Any]:
        """Get team status from Firestore"""
        try:
            filters = []
            if organization_id:
                filters.append({"field": "organization_id", "operator": "==", "value": organization_id})

            users = await self.firestore_manager.get_collection("users", filters=filters if filters else None)

            # Filter to technicians and managers
            team_members = []
            status_counts = {"available": 0, "busy": 0, "offline": 0}

            for user in users:
                role = user.get("role", "").lower()
                if role in ["technician", "tech", "manager", "owner", "admin"]:
                    status = user.get("status", "available")
                    team_members.append({
                        "id": user.get("id") or user.get("uid"),
                        "name": user.get("full_name") or user.get("email", "Unknown"),
                        "role": role.title(),
                        "status": status,
                    })
                    if status in status_counts:
                        status_counts[status] += 1
                    else:
                        status_counts["available"] += 1

            return {
                "team_members": team_members[:20],
                "status_counts": status_counts,
                "total": len(team_members),
            }
        except Exception as e:
            logger.error(f"Error getting team data: {e}")
            return {"team_members": [], "status_counts": {"available": 0, "busy": 0, "offline": 0}, "total": 0}

    async def get_inventory_data(self, user_id: str, config: Dict, organization_id: str = None) -> Dict[str, Any]:
        """Get inventory analytics from Firestore"""
        try:
            filters = []
            if organization_id:
                filters.append({"field": "organization_id", "operator": "==", "value": organization_id})

            parts = await self.firestore_manager.get_collection("parts", filters=filters if filters else None)

            total_value = 0
            low_stock = []
            by_category = {}

            for part in parts:
                current = part.get("current_stock", 0)
                unit_cost = part.get("unit_cost", 0)
                minimum = part.get("minimum_stock", 5)
                category = part.get("category", "General")

                total_value += current * unit_cost

                if current <= minimum:
                    low_stock.append({
                        "id": part.get("id"),
                        "name": part.get("name"),
                        "part_number": part.get("part_number", "N/A"),
                        "current_stock": current,
                        "minimum_stock": minimum,
                    })

                by_category[category] = by_category.get(category, 0) + 1

            return {
                "total_parts": len(parts),
                "total_value": round(total_value, 2),
                "low_stock": low_stock[:10],
                "low_stock_count": len(low_stock),
                "by_category": by_category,
                "pending_requests": 0,
            }
        except Exception as e:
            logger.error(f"Error getting inventory data: {e}")
            return {"total_parts": 0, "total_value": 0, "low_stock": [], "low_stock_count": 0, "by_category": {}, "pending_requests": 0}

    async def get_analytics_data(self, user_id: str, config: Dict, organization_id: str = None) -> Dict[str, Any]:
        """Get analytics summary from Firestore"""
        try:
            filters = []
            if organization_id:
                filters.append({"field": "organization_id", "operator": "==", "value": organization_id})

            work_orders = await self.firestore_manager.get_collection("work_orders", filters=filters if filters else None)
            assets = await self.firestore_manager.get_collection("assets", filters=filters if filters else None)

            # Calculate stats
            total_wo = len(work_orders)
            completed = len([wo for wo in work_orders if wo.get("status") == "Completed"])
            open_wo = len([wo for wo in work_orders if wo.get("status") == "Open"])
            in_progress = len([wo for wo in work_orders if wo.get("status") == "In Progress"])

            completion_rate = round((completed / total_wo) * 100, 1) if total_wo > 0 else 0

            # Asset health
            operational = len([a for a in assets if a.get("status") in ["Operational", "operational", "Active"]])
            warning = len([a for a in assets if a.get("status") in ["Warning", "warning", "Maintenance"]])
            critical = len([a for a in assets if a.get("status") in ["Critical", "critical", "Down"]])

            return {
                "period": "Last 30 days",
                "stats": {
                    "work_orders": {
                        "total": total_wo,
                        "completed": completed,
                        "open": open_wo,
                        "in_progress": in_progress,
                        "completion_rate": completion_rate,
                    },
                    "assets": {
                        "total": len(assets),
                        "operational": operational,
                        "warning": warning,
                        "critical": critical,
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {"period": "Last 30 days", "stats": {}}

    def get_messages_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get messages - placeholder for future messaging system"""
        return {"messages": [], "unread_count": 0}

    def get_quick_actions_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get quick actions based on user role"""
        return {
            "actions": [
                {"id": "create_wo", "label": "Create Work Order", "icon": "plus"},
                {"id": "scan_part", "label": "Scan Part", "icon": "barcode"},
                {"id": "voice_command", "label": "Voice Command", "icon": "microphone"},
            ]
        }

    def get_ai_insights_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get AI insights - placeholder for AI recommendations"""
        return {
            "insights": [
                {"type": "pm_due", "message": "3 preventive maintenance tasks due this week", "priority": "medium"},
                {"type": "low_stock", "message": "2 critical parts running low", "priority": "high"},
            ]
        }

    def get_quality_alerts_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get quality alerts - placeholder for quality system"""
        return {"alerts": [], "count": 0}

    def get_approval_queue_data(self, user_id: str, config: Dict) -> Dict[str, Any]:
        """Get approval queue - placeholder for approval workflow"""
        return {"pending_approvals": [], "count": 0}

    async def update_widget_config(self, user_id: str, widget_id: str, config: Dict, organization_id: str = None) -> bool:
        """Update widget configuration in Firestore"""
        try:
            await self.firestore_manager.set_document(
                "dashboard_configs",
                f"{user_id}_{widget_id}",
                {"user_id": user_id, "widget_id": widget_id, "config": config, "updated_at": datetime.now(timezone.utc).isoformat()}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating widget config: {e}")
            return False

    async def save_dashboard_layout(self, user_id: str, widgets: List[Dict], organization_id: str = None) -> bool:
        """Save dashboard layout to Firestore"""
        try:
            await self.firestore_manager.set_document(
                "dashboard_layouts",
                user_id,
                {"user_id": user_id, "widgets": widgets, "updated_at": datetime.now(timezone.utc).isoformat()}
            )
            return True
        except Exception as e:
            logger.error(f"Error saving dashboard layout: {e}")
            return False


# Global instance
dashboard_service = DashboardService()
