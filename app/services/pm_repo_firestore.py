"""
PM Repository - Firestore Persistence Layer

Clean interfaces for PM automation data access.
All methods use organization_id for multi-tenant isolation.
All timestamps are UTC timezone-aware.
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.core.firestore_db import FirestoreManager, get_firestore_manager

logger = logging.getLogger(__name__)


class PMRepositoryProtocol(Protocol):
    """Protocol defining the PM repository interface."""

    async def load_templates(
        self,
        organization_id: str,
        maintenance_type: Optional[str] = None,
        include_global: bool = True,
    ) -> List[Dict[str, Any]]:
        """Load PM templates for an organization."""
        ...

    async def load_rules(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Load PM schedule rules for an organization."""
        ...

    async def load_due_rules(
        self, organization_id: str, due_before: datetime
    ) -> List[Dict[str, Any]]:
        """Load rules that are due before a given date."""
        ...

    async def load_meters(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        meter_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load asset meters for an organization."""
        ...

    async def load_meters_exceeding_threshold(
        self, organization_id: str, threshold_type: str = "warning"
    ) -> List[Dict[str, Any]]:
        """Load meters exceeding the specified threshold."""
        ...

    async def save_generated_order(
        self, order_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Save a PM generated order tracking record."""
        ...

    async def save_work_order(
        self, work_order_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Save a work order to Firestore."""
        ...

    async def update_rule_next_due(
        self,
        rule_id: str,
        next_due: datetime,
        organization_id: str,
        last_generated: Optional[datetime] = None,
    ) -> bool:
        """Update a rule's next_due date after successful generation."""
        ...

    async def batch_update_rules_next_due(
        self,
        updates: List[Dict[str, Any]],
        organization_id: str,
    ) -> int:
        """Batch update multiple rules' next_due dates."""
        ...

    async def get_pm_order_by_idempotency_key(
        self, idempotency_key: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check if a PM order exists with the given idempotency key."""
        ...

    async def update_meter_reading(
        self,
        meter_id: str,
        new_value: float,
        organization_id: str,
        reading_source: str = "manual",
    ) -> Dict[str, Any]:
        """Update a meter reading and return threshold status."""
        ...

    async def get_pm_overview(
        self, organization_id: str, days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive PM overview for dashboard."""
        ...

    async def save_template(
        self, template_data: Dict[str, Any], organization_id: Optional[str] = None
    ) -> str:
        """Save a PM template."""
        ...

    async def save_rule(
        self, rule_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Save a PM schedule rule."""
        ...

    async def save_meter(
        self, meter_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Save an asset meter."""
        ...


class FirestorePMRepository:
    """
    Firestore implementation of PM repository.

    Provides clean data access layer for PM automation.
    All timestamps are converted to UTC timezone-aware datetimes.
    """

    def __init__(self, firestore_manager: Optional[FirestoreManager] = None):
        """
        Initialize repository with optional FirestoreManager.

        Args:
            firestore_manager: Optional FirestoreManager instance.
                              If None, uses the global singleton.
        """
        self._firestore = firestore_manager or get_firestore_manager()

    @staticmethod
    def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is UTC timezone-aware."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _utc_now() -> datetime:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc)

    # ==========================================
    # LOAD METHODS
    # ==========================================

    async def load_templates(
        self,
        organization_id: str,
        maintenance_type: Optional[str] = None,
        include_global: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Load PM templates for an organization.

        Args:
            organization_id: Organization to load templates for
            maintenance_type: Optional filter by maintenance type
            include_global: Include global templates (org_id is None)

        Returns:
            List of template documents
        """
        return await self._firestore.get_pm_templates(
            organization_id,
            maintenance_type=maintenance_type,
            include_global=include_global,
        )

    async def load_rules(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Load PM schedule rules for an organization.

        Args:
            organization_id: Organization to load rules for
            asset_id: Optional filter by asset
            is_active: Optional filter by active status

        Returns:
            List of rule documents
        """
        return await self._firestore.get_pm_schedule_rules(
            organization_id, asset_id=asset_id, is_active=is_active
        )

    async def load_due_rules(
        self, organization_id: str, due_before: datetime
    ) -> List[Dict[str, Any]]:
        """
        Load rules that are due before a given date.

        Args:
            organization_id: Organization to load rules for
            due_before: Load rules due before this date (UTC)

        Returns:
            List of due rule documents
        """
        due_before = self._ensure_utc(due_before)
        return await self._firestore.get_due_pm_rules(organization_id, due_before)

    async def load_meters(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        meter_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Load asset meters for an organization.

        Args:
            organization_id: Organization to load meters for
            asset_id: Optional filter by asset
            meter_type: Optional filter by meter type

        Returns:
            List of meter documents
        """
        return await self._firestore.get_asset_meters(
            organization_id, asset_id=asset_id, meter_type=meter_type
        )

    async def load_meters_exceeding_threshold(
        self, organization_id: str, threshold_type: str = "warning"
    ) -> List[Dict[str, Any]]:
        """
        Load meters exceeding the specified threshold.

        Args:
            organization_id: Organization to check
            threshold_type: "warning" or "critical"

        Returns:
            List of meters exceeding threshold
        """
        return await self._firestore.get_meters_exceeding_threshold(
            organization_id, threshold_type
        )

    # ==========================================
    # SAVE METHODS
    # ==========================================

    async def save_generated_order(
        self, order_data: Dict[str, Any], organization_id: str
    ) -> str:
        """
        Save a PM generated order tracking record.

        Automatically adds created_at timestamp.

        Args:
            order_data: PM order data
            organization_id: Organization ID

        Returns:
            Created document ID
        """
        # Ensure timestamps are UTC
        if "generated_date" in order_data:
            if isinstance(order_data["generated_date"], datetime):
                order_data["generated_date"] = self._ensure_utc(
                    order_data["generated_date"]
                )

        order_data["created_at"] = self._utc_now()
        order_data["updated_at"] = self._utc_now()

        return await self._firestore.create_pm_generated_order(
            order_data, organization_id
        )

    async def save_work_order(
        self, work_order_data: Dict[str, Any], organization_id: str
    ) -> str:
        """
        Save a work order to Firestore.

        Args:
            work_order_data: Work order data
            organization_id: Organization ID

        Returns:
            Created work order ID
        """
        return await self._firestore.create_org_work_order(
            work_order_data, organization_id
        )

    async def save_template(
        self, template_data: Dict[str, Any], organization_id: Optional[str] = None
    ) -> str:
        """
        Save a PM template.

        Args:
            template_data: Template data
            organization_id: Organization ID (None for global templates)

        Returns:
            Created template ID
        """
        template_data["created_at"] = self._utc_now()
        template_data["updated_at"] = self._utc_now()
        return await self._firestore.create_pm_template(template_data, organization_id)

    async def save_rule(
        self, rule_data: Dict[str, Any], organization_id: str
    ) -> str:
        """
        Save a PM schedule rule.

        Args:
            rule_data: Rule data
            organization_id: Organization ID

        Returns:
            Created rule ID
        """
        # Ensure dates are UTC
        if "next_due" in rule_data and isinstance(rule_data["next_due"], datetime):
            rule_data["next_due"] = self._ensure_utc(rule_data["next_due"])
        if "start_date" in rule_data and isinstance(rule_data["start_date"], datetime):
            rule_data["start_date"] = self._ensure_utc(rule_data["start_date"])

        rule_data["created_at"] = self._utc_now()
        rule_data["updated_at"] = self._utc_now()

        return await self._firestore.create_pm_schedule_rule(rule_data, organization_id)

    async def save_meter(
        self, meter_data: Dict[str, Any], organization_id: str
    ) -> str:
        """
        Save an asset meter.

        Args:
            meter_data: Meter data
            organization_id: Organization ID

        Returns:
            Created meter ID
        """
        meter_data["created_at"] = self._utc_now()
        meter_data["updated_at"] = self._utc_now()
        return await self._firestore.create_asset_meter(meter_data, organization_id)

    # ==========================================
    # UPDATE METHODS
    # ==========================================

    async def update_rule_next_due(
        self,
        rule_id: str,
        next_due: datetime,
        organization_id: str,
        last_generated: Optional[datetime] = None,
    ) -> bool:
        """
        Update a rule's next_due date after successful generation.

        Args:
            rule_id: Rule document ID
            next_due: New next_due date (UTC)
            organization_id: Organization ID
            last_generated: Optional last generation timestamp (UTC)

        Returns:
            True if update successful
        """
        update_data = {
            "next_due": self._ensure_utc(next_due),
            "updated_at": self._utc_now(),
        }

        if last_generated:
            update_data["last_generated"] = self._ensure_utc(last_generated)

        return await self._firestore.update_pm_schedule_rule(
            rule_id, update_data, organization_id
        )

    async def batch_update_rules_next_due(
        self,
        updates: List[Dict[str, Any]],
        organization_id: str,
    ) -> int:
        """
        Batch update multiple rules' next_due dates.

        This should be called AFTER successful generation to avoid
        partial updates on failure.

        Args:
            updates: List of dicts with 'rule_id', 'next_due', and optional 'last_generated'
            organization_id: Organization ID

        Returns:
            Number of successfully updated rules
        """
        success_count = 0
        now = self._utc_now()

        for update in updates:
            try:
                rule_id = update.get("rule_id")
                next_due = update.get("next_due")

                if not rule_id or not next_due:
                    continue

                update_data = {
                    "next_due": self._ensure_utc(next_due),
                    "updated_at": now,
                }

                if "last_generated" in update:
                    update_data["last_generated"] = self._ensure_utc(
                        update["last_generated"]
                    )

                result = await self._firestore.update_pm_schedule_rule(
                    rule_id, update_data, organization_id
                )

                if result:
                    success_count += 1

            except Exception as e:
                logger.error(f"Failed to update rule {update.get('rule_id')}: {e}")

        return success_count

    async def update_meter_reading(
        self,
        meter_id: str,
        new_value: float,
        organization_id: str,
        reading_source: str = "manual",
    ) -> Dict[str, Any]:
        """
        Update a meter reading and return threshold status.

        Args:
            meter_id: Meter document ID
            new_value: New reading value
            organization_id: Organization ID
            reading_source: Source of reading ('manual', 'iot', 'api')

        Returns:
            Dict with meter info and threshold status
        """
        return await self._firestore.update_meter_reading(
            meter_id, new_value, organization_id, reading_source
        )

    # ==========================================
    # QUERY METHODS
    # ==========================================

    async def get_pm_order_by_idempotency_key(
        self, idempotency_key: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a PM order exists with the given idempotency key.

        Used to prevent duplicate work order creation.

        Args:
            idempotency_key: The idempotency key to check
            organization_id: Organization ID

        Returns:
            Existing PM order if found, None otherwise
        """
        return await self._firestore.get_pm_order_by_idempotency_key(
            idempotency_key, organization_id
        )

    async def get_pm_overview(
        self, organization_id: str, days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive PM overview for dashboard.

        Args:
            organization_id: Organization to get overview for
            days_ahead: Number of days to look ahead

        Returns:
            Dict with PM statistics and upcoming maintenance
        """
        return await self._firestore.get_pm_overview(organization_id, days_ahead)


# ==========================================
# FACTORY FUNCTIONS
# ==========================================

# Cached repository instance (lazy initialization)
_pm_repository: Optional[FirestorePMRepository] = None


def get_pm_repository() -> FirestorePMRepository:
    """
    Get PM repository instance.

    Uses lazy initialization - repository is created on first call.
    Thread-safe for typical async usage patterns.

    Returns:
        FirestorePMRepository instance
    """
    global _pm_repository
    if _pm_repository is None:
        _pm_repository = FirestorePMRepository()
    return _pm_repository


def create_pm_repository(
    firestore_manager: Optional[FirestoreManager] = None,
) -> FirestorePMRepository:
    """
    Create a new PM repository instance.

    Use this for dependency injection in tests or when
    a specific FirestoreManager instance is needed.

    Args:
        firestore_manager: Optional FirestoreManager instance

    Returns:
        New FirestorePMRepository instance
    """
    return FirestorePMRepository(firestore_manager)


def is_demo_mode() -> bool:
    """
    Check if running in demo mode.

    Demo mode enables seed data and mock features.
    Controlled by DEMO_MODE or ENVIRONMENT environment variables.

    Returns:
        True if in demo mode
    """
    if os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes"):
        return True

    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ("development", "dev", "local", "demo")
