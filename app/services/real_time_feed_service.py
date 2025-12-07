"""
Real-Time Feed Service - WebSocket Data Streaming
Manages real-time data feeds for dashboard widgets
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Set

from app.services.dashboard_service import dashboard_service
from app.services.websocket_manager import websocket_manager


class RealTimeFeedService:
    """Service for managing real-time dashboard data streams"""

    def __init__(self):
        self.subscriptions: Dict[int, Set[str]] = {}  # user_id -> set of widget_types
        self.update_interval = 5  # seconds
        self.is_running = False

    async def subscribe(self, user_id: int, widget_types: List[str]):
        """Subscribe user to specific widget data feeds"""
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = set()

        self.subscriptions[user_id].update(widget_types)

        # Send initial data
        await self.send_widget_updates(user_id, widget_types)

    async def unsubscribe(self, user_id: int, widget_types: List[str] = None):
        """Unsubscribe user from widget feeds"""
        if user_id in self.subscriptions:
            if widget_types:
                self.subscriptions[user_id] -= set(widget_types)
            else:
                del self.subscriptions[user_id]

    async def send_widget_updates(self, user_id: int, widget_types: List[str]):
        """Send current data for specified widgets"""
        updates = {}

        for widget_type in widget_types:
            try:
                data = dashboard_service.get_widget_data(widget_type, user_id)
                updates[widget_type] = data
            except Exception as e:
                print(f"Error getting data for widget {widget_type}: {e}")
                updates[widget_type] = {"error": str(e)}

        # Send via WebSocket
        message = {
            "type": "widget_update",
            "timestamp": datetime.now().isoformat(),
            "updates": updates,
        }

        await websocket_manager.send_personal_message(json.dumps(message), user_id)

    async def broadcast_update(self, widget_type: str, data: Any = None):
        """Broadcast update to all users subscribed to a widget type"""
        for user_id, subscribed_widgets in self.subscriptions.items():
            if widget_type in subscribed_widgets:
                if data is None:
                    # Fetch fresh data
                    data = dashboard_service.get_widget_data(widget_type, user_id)

                message = {
                    "type": "widget_update",
                    "timestamp": datetime.now().isoformat(),
                    "updates": {widget_type: data},
                }

                await websocket_manager.send_personal_message(
                    json.dumps(message), user_id
                )

    async def start_periodic_updates(self):
        """Start periodic updates for all subscribed users"""
        self.is_running = True

        while self.is_running:
            try:
                # Update all subscribed users
                for user_id, widget_types in list(self.subscriptions.items()):
                    if widget_types:
                        await self.send_widget_updates(user_id, list(widget_types))

                # Wait for next interval
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                print(f"Error in periodic updates: {e}")
                await asyncio.sleep(self.update_interval)

    def stop_periodic_updates(self):
        """Stop periodic updates"""
        self.is_running = False

    async def notify_work_order_update(
        self, work_order_id: int, assigned_to: int = None
    ):
        """Notify users when a work order is updated"""
        # Broadcast to workload widget subscribers
        await self.broadcast_update("workload")

        # If assigned to someone, send them a notification
        if assigned_to:
            message = {
                "type": "notification",
                "notification_type": "work_order_assigned",
                "work_order_id": work_order_id,
                "timestamp": datetime.now().isoformat(),
            }
            await websocket_manager.send_personal_message(
                json.dumps(message), assigned_to
            )

    async def notify_parts_update(self, requester_id: int):
        """Notify user when their parts request is updated"""
        await self.send_widget_updates(requester_id, ["parts_status"])

    async def notify_message_received(self, recipient_id: int):
        """Notify user when they receive a message"""
        await self.send_widget_updates(recipient_id, ["messages"])


# Global instance
real_time_feed = RealTimeFeedService()
