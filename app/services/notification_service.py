"""
Intelligent Notification Service
Handles automatic notification generation and delivery
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.core.db_adapter import get_db_adapter
from app.services.email_service import email_service
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    async def _get_user_data(user_id: int) -> Dict[str, Any]:
        """Get user data from Firestore for email notifications"""
        try:
            db_adapter = get_db_adapter()
            if not db_adapter.firestore_manager:
                logger.warning("Firestore not available for user data")
                return {}

            user_data = await db_adapter.firestore_manager.get_document(
                "users", str(user_id)
            )
            return user_data if user_data else {}
        except Exception as e:
            logger.error(f"Failed to get user data for user {user_id}: {e}")
            return {}

    @staticmethod
    async def create_notification(
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        link: str = None,
        priority: str = "normal",
    ) -> str:
        """Create a notification in Firestore"""
        try:
            db_adapter = get_db_adapter()
            if not db_adapter.firestore_manager:
                logger.warning("Firestore not available, notification not stored")
                return f"temp-{datetime.now().timestamp()}"

            notification_data = {
                "user_id": str(user_id),
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "link": link,
                "priority": priority,
                "read": False,
                "created_date": datetime.now().isoformat(),
            }

            notification_id = await db_adapter.firestore_manager.create_document(
                "notifications", notification_data
            )
            logger.info(
                f"Created notification {notification_id} for user {user_id}: {title}"
            )
            return notification_id
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return f"error-{datetime.now().timestamp()}"

    @staticmethod
    async def send_notification(
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        link: str = None,
        priority: str = "normal",
    ):
        """Create and send a real-time notification"""
        notification_id = await NotificationService.create_notification(
            user_id, notification_type, title, message, link, priority
        )

        # Send via WebSocket if user is online
        await websocket_manager.send_personal_message(
            {
                "type": "notification",
                "id": notification_id,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "link": link,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
            },
            user_id,
        )

        return notification_id

    @staticmethod
    async def notify_work_order_assigned(
        work_order_id: int,
        technician_id: int,
        title: str,
        work_order_data: Dict[str, Any] = None,
    ):
        """Notify technician of new work order assignment"""
        # Send in-app notification
        await NotificationService.send_notification(
            user_id=technician_id,
            notification_type="work_order_assigned",
            title="New Work Order Assigned",
            message=f"You have been assigned to: {title}",
            link=f"/work-orders/{work_order_id}",
            priority="high",
        )

        # Send email notification
        try:
            user_data = await NotificationService._get_user_data(technician_id)
            user_email = user_data.get("email")
            user_name = user_data.get("fullName", "Technician")

            if user_email and work_order_data:
                work_order_info = {
                    "id": work_order_id,
                    "title": title,
                    "description": work_order_data.get("description", "No description"),
                    "priority": work_order_data.get("priority", "normal"),
                    "asset_name": work_order_data.get("asset_name", "Unknown Asset"),
                }

                await email_service.send_work_order_notification(
                    to_email=user_email,
                    to_name=user_name,
                    work_order=work_order_info,
                    notification_type="assigned",
                )
                logger.info(f"Sent work order assignment email to {user_email}")
        except Exception as e:
            logger.error(f"Failed to send work order assignment email: {e}")

    @staticmethod
    async def notify_parts_arrived(
        requester_id: int,
        part_name: str,
        work_order_id: int = None,
        parts_data: Dict[str, Any] = None,
    ):
        """Notify technician that requested parts have arrived"""
        link = f"/work-orders/{work_order_id}" if work_order_id else "/inventory"

        # Send in-app notification
        await NotificationService.send_notification(
            user_id=requester_id,
            notification_type="parts_arrived",
            title="Parts Arrived",
            message=f"{part_name} is now available",
            link=link,
            priority="high",
        )

        # Send email notification
        try:
            user_data = await NotificationService._get_user_data(requester_id)
            user_email = user_data.get("email")
            user_name = user_data.get("fullName", "Technician")

            if user_email:
                parts_info = (
                    parts_data
                    if parts_data
                    else {
                        "name": part_name,
                        "part_number": "TBD",
                        "quantity": "Available",
                        "location": "Warehouse",
                    }
                )

                await email_service.send_parts_notification(
                    to_email=user_email,
                    to_name=user_name,
                    parts_info=parts_info,
                    notification_type="arrived",
                )
                logger.info(f"Sent parts arrival email to {user_email}")
        except Exception as e:
            logger.error(f"Failed to send parts arrival email: {e}")

    @staticmethod
    async def notify_training_due(
        user_id: int,
        training_title: str,
        training_id: int,
        notification_type: str = "due",
    ):
        """Notify user of upcoming or overdue training"""
        # Send in-app notification
        await NotificationService.send_notification(
            user_id=user_id,
            notification_type="training_due",
            title="Training Due",
            message=f"Complete: {training_title}",
            link=f"/training/modules/{training_id}",
            priority="normal",
        )

        # Send email notification
        try:
            user_data = await NotificationService._get_user_data(user_id)
            user_email = user_data.get("email")
            user_name = user_data.get("fullName", "Team Member")

            if user_email:
                await email_service.send_training_notification(
                    to_email=user_email,
                    to_name=user_name,
                    training_title=training_title,
                    training_id=str(training_id),
                    notification_type=notification_type,
                )
                logger.info(f"Sent training notification email to {user_email}")
        except Exception as e:
            logger.error(f"Failed to send training notification email: {e}")

    @staticmethod
    async def notify_immediate_failure(
        manager_ids: list, asset_name: str, work_order_id: int, hours_since_pm: float
    ):
        """Alert managers of immediate failure after PM"""
        for manager_id in manager_ids:
            await NotificationService.send_notification(
                user_id=manager_id,
                notification_type="quality_alert",
                title="Immediate Failure Alert",
                message=f"{asset_name} failed {hours_since_pm:.1f}h after PM",
                link=f"/work-orders/{work_order_id}",
                priority="urgent",
            )

    @staticmethod
    async def notify_pm_due(technician_id: int, asset_name: str, asset_id: int):
        """Notify technician of upcoming preventive maintenance"""
        await NotificationService.send_notification(
            user_id=technician_id,
            notification_type="pm_due",
            title="Preventive Maintenance Due",
            message=f"{asset_name} requires scheduled maintenance",
            link=f"/assets/{asset_id}",
            priority="normal",
        )

    @staticmethod
    async def notify_certification_expiring(
        user_id: int, skill_name: str, days_remaining: int
    ):
        """Notify user of expiring certification"""
        priority = "urgent" if days_remaining <= 7 else "high"
        await NotificationService.send_notification(
            user_id=user_id,
            notification_type="certification_expiring",
            title="Certification Expiring",
            message=f"{skill_name} certification expires in {days_remaining} days",
            link="/team/profile",
            priority=priority,
        )

    @staticmethod
    async def get_user_notifications(user_id: int, unread_only: bool = False):
        """Get all notifications for a user from Firestore"""
        try:
            db_adapter = get_db_adapter()
            if not db_adapter.firestore_manager:
                logger.warning("Firestore not available for notifications")
                return []

            filters = [{"field": "user_id", "operator": "==", "value": str(user_id)}]
            if unread_only:
                filters.append({"field": "read", "operator": "==", "value": False})

            notifications = await db_adapter.firestore_manager.get_collection(
                "notifications",
                filters=filters,
                order_by="-created_date",  # Use - prefix for descending order
                limit=50,
            )
            return notifications
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return []

    @staticmethod
    async def mark_as_read(notification_id: str):
        """Mark a notification as read in Firestore"""
        try:
            db_adapter = get_db_adapter()
            if not db_adapter.firestore_manager:
                logger.warning("Firestore not available for notifications")
                return False

            await db_adapter.firestore_manager.update_document(
                "notifications", notification_id, {"read": True}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    @staticmethod
    async def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications from Firestore"""
        try:
            db_adapter = get_db_adapter()
            if not db_adapter.firestore_manager:
                return 0

            filters = [
                {"field": "user_id", "operator": "==", "value": str(user_id)},
                {"field": "read", "operator": "==", "value": False},
            ]

            notifications = await db_adapter.firestore_manager.get_collection(
                "notifications", filters=filters
            )
            return len(notifications)
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0


# Global notification service instance
notification_service = NotificationService()
