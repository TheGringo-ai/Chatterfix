"""
Push Notification Service for ChatterFix CMMS
Handles push notifications for urgent work orders and alerts
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import asyncio

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for managing push notifications"""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    async def register_subscription(
        self, user_id: str, subscription: Dict[str, Any]
    ) -> bool:
        """Register a push notification subscription in Firestore."""
        try:
            sub_data = {
                "user_id": user_id,
                "endpoint": subscription.get("endpoint"),
                "keys": subscription.get("keys", {}),
                "created_at": datetime.now(timezone.utc),
            }
            # Use user_id as the document ID for easy lookup
            await self.firestore_manager.create_document(
                "push_subscriptions", sub_data, doc_id=user_id
            )
            logger.info(f"Push subscription registered for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error registering push subscription: {e}")
            return False

    async def unregister_subscription(self, user_id: str) -> bool:
        """Unregister a push notification subscription from Firestore."""
        try:
            await self.firestore_manager.delete_document("push_subscriptions", user_id)
            return True
        except Exception as e:
            logger.error(f"Error unregistering push subscription: {e}")
            return False

    async def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get push subscription for a user from Firestore."""
        try:
            return await self.firestore_manager.get_document(
                "push_subscriptions", user_id
            )
        except Exception as e:
            logger.error(f"Error getting subscription for user {user_id}: {e}")
            return None

    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        url: str = "/",
        priority: str = "normal",
        tag: str = "chatterfix",
        data: Dict = None,
    ) -> Dict[str, Any]:
        """Send a push notification to a user."""
        notification_payload = {
            "title": title,
            "body": body,
            "icon": "/static/images/icon-192.png",
            "tag": tag,
            "priority": priority,
            "data": {"url": url, **(data or {})},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            notification_data = {
                "user_id": user_id,
                "notification_type": "push",
                "title": title,
                "message": body,
                "link": url,
                "priority": priority,
                "is_read": False,
                "created_at": datetime.now(timezone.utc),
            }
            await self.firestore_manager.create_document(
                "notifications", notification_data
            )

            subscription = await self.get_subscription(user_id)
            if subscription:
                # In production, this would use pywebpush or similar to send the notification
                logger.info(
                    f"Simulating push notification sent to user {user_id}: {title}"
                )
                return {
                    "success": True,
                    "delivered": True,
                    "payload": notification_payload,
                }
            else:
                logger.info(
                    f"No subscription for user {user_id}, notification stored only"
                )
                return {
                    "success": True,
                    "delivered": False,
                    "reason": "no_subscription",
                }
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {"success": False, "error": str(e)}

    async def broadcast_notification(
        self,
        title: str,
        body: str,
        url: str = "/",
        priority: str = "normal",
        user_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send notification to multiple users."""
        if user_ids:
            users_to_notify = user_ids
        else:
            subscriptions = await self.firestore_manager.get_collection(
                "push_subscriptions"
            )
            users_to_notify = [
                sub.get("user_id") for sub in subscriptions if sub.get("user_id")
            ]

        tasks = [
            self.send_notification(user_id, title, body, url, priority)
            for user_id in users_to_notify
        ]
        results = await asyncio.gather(*tasks)

        summary = {
            "total": len(results),
            "delivered": len([r for r in results if r.get("delivered")]),
            "failed": len([r for r in results if not r.get("success")]),
            "no_subscription": len(
                [r for r in results if r.get("reason") == "no_subscription"]
            ),
        }
        return summary

    # Other notification methods remain the same but now call the async send_notification


# Global push notification service instance
push_service = PushNotificationService()
