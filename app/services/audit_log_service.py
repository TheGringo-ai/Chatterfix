"""
Audit Log Service for ChatterFix CMMS
Tracks all user actions on work orders, assets, parts, and other entities.
Provides comprehensive activity logging for compliance and troubleshooting.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Enumeration of auditable actions"""
    # Work Order Actions
    WORK_ORDER_CREATED = "work_order_created"
    WORK_ORDER_UPDATED = "work_order_updated"
    WORK_ORDER_COMPLETED = "work_order_completed"
    WORK_ORDER_DELETED = "work_order_deleted"
    WORK_ORDER_ASSIGNED = "work_order_assigned"
    WORK_ORDER_SCHEDULED = "work_order_scheduled"
    WORK_ORDER_STATUS_CHANGED = "work_order_status_changed"

    # Asset Actions
    ASSET_CREATED = "asset_created"
    ASSET_UPDATED = "asset_updated"
    ASSET_DELETED = "asset_deleted"
    ASSET_STATUS_CHANGED = "asset_status_changed"

    # Part/Inventory Actions
    PART_CREATED = "part_created"
    PART_UPDATED = "part_updated"
    PART_CHECKED_OUT = "part_checked_out"
    PART_CHECKED_IN = "part_checked_in"
    PART_STOCK_ADJUSTED = "part_stock_adjusted"

    # User Actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_ROLE_CHANGED = "user_role_changed"

    # PM Actions
    PM_CREATED = "pm_created"
    PM_COMPLETED = "pm_completed"
    PM_SCHEDULED = "pm_scheduled"


class AuditLogService:
    """Service for creating and querying audit logs"""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()
        self.collection_name = "audit_logs"

    async def log_action(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        user_id: str,
        user_name: str,
        organization_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an audit action to Firestore.

        Args:
            action: The type of action being logged
            entity_type: Type of entity (work_order, asset, part, user)
            entity_id: ID of the entity being acted upon
            user_id: ID of the user performing the action
            user_name: Display name of the user
            organization_id: Organization scope for multi-tenant isolation
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            metadata: Additional context information

        Returns:
            The ID of the created audit log entry
        """
        try:
            # Build the audit log entry
            audit_entry = {
                "action": action.value if isinstance(action, AuditAction) else action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "user_name": user_name,
                "organization_id": organization_id,
                "timestamp": datetime.now(timezone.utc),
                "old_values": old_values,
                "new_values": new_values,
                "metadata": metadata or {},
            }

            # Calculate what changed (for updates)
            if old_values and new_values:
                changes = {}
                for key, new_val in new_values.items():
                    old_val = old_values.get(key)
                    if old_val != new_val:
                        changes[key] = {"from": old_val, "to": new_val}
                audit_entry["changes"] = changes

            # Create the audit log entry
            log_id = await self.firestore_manager.create_document(
                self.collection_name, audit_entry
            )

            logger.info(
                f"Audit log created: {action.value if isinstance(action, AuditAction) else action} "
                f"on {entity_type}/{entity_id} by {user_name}"
            )

            return log_id

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit logging should not break main operations
            return ""

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        organization_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get audit history for a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            organization_id: Organization scope
            limit: Maximum number of entries to return
        """
        try:
            filters = [
                {"field": "entity_type", "operator": "==", "value": entity_type},
                {"field": "entity_id", "operator": "==", "value": entity_id},
            ]

            if organization_id:
                filters.append({
                    "field": "organization_id",
                    "operator": "==",
                    "value": organization_id
                })

            logs = await self.firestore_manager.get_collection(
                self.collection_name,
                filters=filters,
                limit=limit,
            )

            # Sort by timestamp descending (most recent first)
            logs = sorted(
                logs,
                key=lambda x: x.get("timestamp", datetime.min),
                reverse=True
            )

            # Convert timestamps to strings for JSON serialization
            for log in logs:
                if "timestamp" in log and hasattr(log["timestamp"], "strftime"):
                    log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

            return logs

        except Exception as e:
            logger.error(f"Failed to get entity history: {e}")
            return []

    async def get_user_activity(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all activity by a specific user.
        """
        try:
            filters = [
                {"field": "user_id", "operator": "==", "value": user_id},
            ]

            if organization_id:
                filters.append({
                    "field": "organization_id",
                    "operator": "==",
                    "value": organization_id
                })

            logs = await self.firestore_manager.get_collection(
                self.collection_name,
                filters=filters,
                limit=limit,
            )

            # Sort by timestamp descending
            logs = sorted(
                logs,
                key=lambda x: x.get("timestamp", datetime.min),
                reverse=True
            )

            # Convert timestamps
            for log in logs:
                if "timestamp" in log and hasattr(log["timestamp"], "strftime"):
                    log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

            return logs

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return []

    async def get_organization_activity(
        self,
        organization_id: str,
        action_filter: Optional[str] = None,
        days: int = 7,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Get all activity for an organization within a time period.
        """
        try:
            from datetime import timedelta

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            filters = [
                {"field": "organization_id", "operator": "==", "value": organization_id},
            ]

            if action_filter:
                filters.append({
                    "field": "action",
                    "operator": "==",
                    "value": action_filter
                })

            logs = await self.firestore_manager.get_collection(
                self.collection_name,
                filters=filters,
                limit=limit,
            )

            # Filter by date and sort
            filtered_logs = []
            for log in logs:
                timestamp = log.get("timestamp")
                if timestamp and timestamp >= cutoff:
                    if hasattr(timestamp, "strftime"):
                        log["timestamp"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    filtered_logs.append(log)

            filtered_logs = sorted(
                filtered_logs,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

            return filtered_logs

        except Exception as e:
            logger.error(f"Failed to get organization activity: {e}")
            return []

    async def get_activity_summary(
        self,
        organization_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get a summary of activity for an organization.
        """
        try:
            logs = await self.get_organization_activity(
                organization_id=organization_id,
                days=days,
                limit=1000,
            )

            # Count by action type
            action_counts = {}
            user_counts = {}
            entity_counts = {}

            for log in logs:
                # Count actions
                action = log.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + 1

                # Count by user
                user = log.get("user_name", "Unknown")
                user_counts[user] = user_counts.get(user, 0) + 1

                # Count by entity type
                entity = log.get("entity_type", "unknown")
                entity_counts[entity] = entity_counts.get(entity, 0) + 1

            return {
                "total_actions": len(logs),
                "period_days": days,
                "action_breakdown": action_counts,
                "user_breakdown": user_counts,
                "entity_breakdown": entity_counts,
                "most_active_user": max(user_counts, key=user_counts.get) if user_counts else None,
                "most_common_action": max(action_counts, key=action_counts.get) if action_counts else None,
            }

        except Exception as e:
            logger.error(f"Failed to get activity summary: {e}")
            return {
                "total_actions": 0,
                "period_days": days,
                "action_breakdown": {},
                "user_breakdown": {},
                "entity_breakdown": {},
            }


# Singleton instance
audit_log_service = AuditLogService()


# Convenience functions for common actions
async def log_work_order_created(
    wo_id: str,
    wo_data: Dict[str, Any],
    user_id: str,
    user_name: str,
    organization_id: Optional[str] = None,
) -> str:
    """Log a work order creation"""
    return await audit_log_service.log_action(
        action=AuditAction.WORK_ORDER_CREATED,
        entity_type="work_order",
        entity_id=wo_id,
        user_id=user_id,
        user_name=user_name,
        organization_id=organization_id,
        new_values=wo_data,
        metadata={"title": wo_data.get("title")},
    )


async def log_work_order_updated(
    wo_id: str,
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    user_id: str,
    user_name: str,
    organization_id: Optional[str] = None,
) -> str:
    """Log a work order update"""
    return await audit_log_service.log_action(
        action=AuditAction.WORK_ORDER_UPDATED,
        entity_type="work_order",
        entity_id=wo_id,
        user_id=user_id,
        user_name=user_name,
        organization_id=organization_id,
        old_values=old_data,
        new_values=new_data,
    )


async def log_work_order_completed(
    wo_id: str,
    wo_data: Dict[str, Any],
    user_id: str,
    user_name: str,
    organization_id: Optional[str] = None,
    completion_notes: Optional[str] = None,
) -> str:
    """Log a work order completion"""
    return await audit_log_service.log_action(
        action=AuditAction.WORK_ORDER_COMPLETED,
        entity_type="work_order",
        entity_id=wo_id,
        user_id=user_id,
        user_name=user_name,
        organization_id=organization_id,
        new_values={"status": "Completed"},
        metadata={
            "title": wo_data.get("title"),
            "completion_notes": completion_notes,
        },
    )


async def log_part_checkout(
    part_id: str,
    part_name: str,
    quantity: int,
    work_order_id: Optional[str],
    user_id: str,
    user_name: str,
    organization_id: Optional[str] = None,
) -> str:
    """Log a part checkout"""
    return await audit_log_service.log_action(
        action=AuditAction.PART_CHECKED_OUT,
        entity_type="part",
        entity_id=part_id,
        user_id=user_id,
        user_name=user_name,
        organization_id=organization_id,
        new_values={"quantity_checked_out": quantity},
        metadata={
            "part_name": part_name,
            "work_order_id": work_order_id,
        },
    )
