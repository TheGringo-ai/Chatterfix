"""
Push Notification Service for ChatterFix CMMS
Handles push notifications for urgent work orders and alerts
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.core.database import get_db_connection

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for managing push notifications"""
    
    def __init__(self):
        self.subscriptions = {}  # In-memory store for demo; production would use database
    
    def register_subscription(self, user_id: int, subscription: Dict[str, Any]) -> bool:
        """
        Register a push notification subscription
        
        subscription format:
        {
            "endpoint": "https://fcm.googleapis.com/fcm/send/...",
            "keys": {
                "p256dh": "...",
                "auth": "..."
            }
        }
        """
        conn = get_db_connection()
        try:
            # Ensure table exists
            self._ensure_subscriptions_table(conn)
            
            # Store subscription
            conn.execute("""
                INSERT OR REPLACE INTO push_subscriptions 
                (user_id, endpoint, p256dh_key, auth_key, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                subscription.get('endpoint'),
                subscription.get('keys', {}).get('p256dh'),
                subscription.get('keys', {}).get('auth'),
                datetime.now().isoformat()
            ))
            conn.commit()
            
            # Also store in memory for quick access
            self.subscriptions[user_id] = subscription
            
            logger.info(f"Push subscription registered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering push subscription: {e}")
            return False
        finally:
            conn.close()
    
    def unregister_subscription(self, user_id: int) -> bool:
        """Unregister a push notification subscription"""
        conn = get_db_connection()
        try:
            conn.execute(
                "DELETE FROM push_subscriptions WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            
            if user_id in self.subscriptions:
                del self.subscriptions[user_id]
            
            return True
        except Exception as e:
            logger.error(f"Error unregistering push subscription: {e}")
            return False
        finally:
            conn.close()
    
    def get_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get push subscription for a user"""
        # Check memory cache first
        if user_id in self.subscriptions:
            return self.subscriptions[user_id]
        
        conn = get_db_connection()
        try:
            self._ensure_subscriptions_table(conn)
            
            result = conn.execute(
                "SELECT endpoint, p256dh_key, auth_key FROM push_subscriptions WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            if result:
                subscription = {
                    "endpoint": result['endpoint'],
                    "keys": {
                        "p256dh": result['p256dh_key'],
                        "auth": result['auth_key']
                    }
                }
                self.subscriptions[user_id] = subscription
                return subscription
            
            return None
        finally:
            conn.close()
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        url: str = "/",
        priority: str = "normal",
        tag: str = "chatterfix",
        data: Dict = None
    ) -> Dict[str, Any]:
        """
        Send a push notification to a user
        
        In production, this would use a push service like:
        - Firebase Cloud Messaging (FCM)
        - Web Push Protocol with VAPID
        - OneSignal
        
        For this demo, we simulate the notification and store it
        """
        notification_payload = {
            "title": title,
            "body": body,
            "icon": "/static/images/icon-192.png",
            "badge": "/static/images/icon-192.png",
            "tag": tag,
            "priority": priority,
            "data": {
                "url": url,
                **(data or {})
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Store notification in database
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO notifications 
                (user_id, notification_type, title, message, link, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "push",
                title,
                body,
                url,
                priority
            ))
            conn.commit()
            
            # In production, this would actually send the push notification
            # using the Web Push protocol or FCM
            subscription = self.get_subscription(user_id)
            
            if subscription:
                # Simulated push - in production, use pywebpush or similar
                logger.info(f"Push notification sent to user {user_id}: {title}")
                return {
                    "success": True,
                    "delivered": True,
                    "payload": notification_payload
                }
            else:
                logger.info(f"No subscription for user {user_id}, notification stored only")
                return {
                    "success": True,
                    "delivered": False,
                    "reason": "no_subscription",
                    "payload": notification_payload
                }
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            conn.close()
    
    async def send_urgent_work_order_notification(
        self,
        user_id: int,
        work_order_id: int,
        work_order_title: str,
        asset_name: str = None
    ) -> Dict[str, Any]:
        """Send notification for urgent work order"""
        title = "🚨 Urgent Work Order"
        body = f"New urgent task: {work_order_title}"
        if asset_name:
            body += f" ({asset_name})"
        
        return await self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            url=f"/work-orders/{work_order_id}",
            priority="urgent",
            tag=f"wo-{work_order_id}",
            data={
                "type": "work_order",
                "work_order_id": work_order_id
            }
        )
    
    async def send_sensor_alert_notification(
        self,
        user_id: int,
        asset_id: int,
        asset_name: str,
        sensor_type: str,
        value: float,
        severity: str
    ) -> Dict[str, Any]:
        """Send notification for sensor threshold alert"""
        emoji = "🔴" if severity == "critical" else "🟡"
        title = f"{emoji} Sensor Alert - {asset_name}"
        body = f"{sensor_type.title()} reading: {value} ({severity})"
        
        return await self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            url=f"/assets/{asset_id}",
            priority="high" if severity == "critical" else "normal",
            tag=f"sensor-{asset_id}-{sensor_type}",
            data={
                "type": "sensor_alert",
                "asset_id": asset_id,
                "sensor_type": sensor_type,
                "severity": severity
            }
        )
    
    async def send_pm_due_notification(
        self,
        user_id: int,
        asset_id: int,
        asset_name: str,
        due_date: str
    ) -> Dict[str, Any]:
        """Send notification for PM due"""
        title = "📅 Preventive Maintenance Due"
        body = f"{asset_name} - maintenance due {due_date}"
        
        return await self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            url=f"/assets/{asset_id}",
            priority="normal",
            tag=f"pm-{asset_id}",
            data={
                "type": "pm_due",
                "asset_id": asset_id
            }
        )
    
    async def broadcast_notification(
        self,
        title: str,
        body: str,
        url: str = "/",
        priority: str = "normal",
        user_ids: List[int] = None
    ) -> Dict[str, Any]:
        """Send notification to multiple users"""
        conn = get_db_connection()
        try:
            if user_ids:
                # Send to specific users
                users = user_ids
            else:
                # Send to all users with active subscriptions
                self._ensure_subscriptions_table(conn)
                result = conn.execute("SELECT DISTINCT user_id FROM push_subscriptions").fetchall()
                users = [r['user_id'] for r in result]
            
            results = {
                "total": len(users),
                "delivered": 0,
                "failed": 0,
                "no_subscription": 0
            }
            
            for user_id in users:
                result = await self.send_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    url=url,
                    priority=priority
                )
                
                if result.get("delivered"):
                    results["delivered"] += 1
                elif result.get("reason") == "no_subscription":
                    results["no_subscription"] += 1
                else:
                    results["failed"] += 1
            
            return results
            
        finally:
            conn.close()
    
    def _ensure_subscriptions_table(self, conn):
        """Ensure push_subscriptions table exists"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                endpoint TEXT NOT NULL,
                p256dh_key TEXT,
                auth_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.commit()


# Global push notification service instance
push_service = PushNotificationService()
