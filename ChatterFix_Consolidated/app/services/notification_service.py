"""
Intelligent Notification Service
Handles automatic notification generation and delivery
"""
from app.core.database import get_db_connection
from app.services.websocket_manager import websocket_manager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    
    @staticmethod
    def create_notification(user_id: int, notification_type: str, title: str, 
                          message: str, link: str = None, priority: str = 'normal'):
        """Create a notification in the database"""
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO notifications (user_id, notification_type, title, message, link, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, notification_type, title, message, link, priority))
            conn.commit()
            notification_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            logger.info(f"Created notification {notification_id} for user {user_id}: {title}")
            return notification_id
        finally:
            conn.close()
    
    @staticmethod
    async def send_notification(user_id: int, notification_type: str, title: str,
                               message: str, link: str = None, priority: str = 'normal'):
        """Create and send a real-time notification"""
        notification_id = NotificationService.create_notification(
            user_id, notification_type, title, message, link, priority
        )
        
        # Send via WebSocket if user is online
        await websocket_manager.send_personal_message({
            'type': 'notification',
            'id': notification_id,
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'link': link,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }, user_id)
        
        return notification_id
    
    @staticmethod
    async def notify_work_order_assigned(work_order_id: int, technician_id: int, title: str):
        """Notify technician of new work order assignment"""
        await NotificationService.send_notification(
            user_id=technician_id,
            notification_type='work_order_assigned',
            title='New Work Order Assigned',
            message=f'You have been assigned to: {title}',
            link=f'/work-orders/{work_order_id}',
            priority='high'
        )
    
    @staticmethod
    async def notify_parts_arrived(requester_id: int, part_name: str, work_order_id: int = None):
        """Notify technician that requested parts have arrived"""
        link = f'/work-orders/{work_order_id}' if work_order_id else '/inventory'
        await NotificationService.send_notification(
            user_id=requester_id,
            notification_type='parts_arrived',
            title='Parts Arrived',
            message=f'{part_name} is now available',
            link=link,
            priority='high'
        )
    
    @staticmethod
    async def notify_training_due(user_id: int, training_title: str, training_id: int):
        """Notify user of upcoming or overdue training"""
        await NotificationService.send_notification(
            user_id=user_id,
            notification_type='training_due',
            title='Training Due',
            message=f'Complete: {training_title}',
            link=f'/training/modules/{training_id}',
            priority='normal'
        )
    
    @staticmethod
    async def notify_immediate_failure(manager_ids: list, asset_name: str, 
                                      work_order_id: int, hours_since_pm: float):
        """Alert managers of immediate failure after PM"""
        for manager_id in manager_ids:
            await NotificationService.send_notification(
                user_id=manager_id,
                notification_type='quality_alert',
                title='Immediate Failure Alert',
                message=f'{asset_name} failed {hours_since_pm:.1f}h after PM',
                link=f'/work-orders/{work_order_id}',
                priority='urgent'
            )
    
    @staticmethod
    async def notify_pm_due(technician_id: int, asset_name: str, asset_id: int):
        """Notify technician of upcoming preventive maintenance"""
        await NotificationService.send_notification(
            user_id=technician_id,
            notification_type='pm_due',
            title='Preventive Maintenance Due',
            message=f'{asset_name} requires scheduled maintenance',
            link=f'/assets/{asset_id}',
            priority='normal'
        )
    
    @staticmethod
    async def notify_certification_expiring(user_id: int, skill_name: str, days_remaining: int):
        """Notify user of expiring certification"""
        priority = 'urgent' if days_remaining <= 7 else 'high'
        await NotificationService.send_notification(
            user_id=user_id,
            notification_type='certification_expiring',
            title='Certification Expiring',
            message=f'{skill_name} certification expires in {days_remaining} days',
            link='/team/profile',
            priority=priority
        )
    
    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False):
        """Get all notifications for a user"""
        conn = get_db_connection()
        try:
            query = "SELECT * FROM notifications WHERE user_id = ?"
            params = [user_id]
            
            if unread_only:
                query += " AND read = 0"
            
            query += " ORDER BY created_date DESC LIMIT 50"
            
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()
    
    @staticmethod
    def mark_as_read(notification_id: int):
        """Mark a notification as read"""
        conn = get_db_connection()
        try:
            conn.execute("UPDATE notifications SET read = 1 WHERE id = ?", (notification_id,))
            conn.commit()
        finally:
            conn.close()
    
    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications"""
        conn = get_db_connection()
        try:
            result = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = 0",
                (user_id,)
            ).fetchone()
            return result[0] if result else 0
        finally:
            conn.close()

# Global notification service instance
notification_service = NotificationService()
