"""
Quota Enforcement Service
=========================

Centralized quota/limit enforcement for multi-tenant SaaS.

Pattern:
1. Organizations have a `counts` field tracking usage
2. Before creating a resource, call `reserve_slot(org_id, resource_type)`
3. Check count against limit, increment atomically
4. If over limit → raises QuotaExceededError

Usage:
    from app.services.quota_service import quota_service, QuotaExceededError

    try:
        await quota_service.reserve_asset_slot(org_id)
        # Create the asset
        await firestore.create_org_document("assets", data, org_id)
    except QuotaExceededError as e:
        raise HTTPException(status_code=403, detail=str(e))
"""

import logging
from typing import Optional

from google.cloud.firestore_v1.transforms import Increment

from app.core.firestore_db import get_firestore_manager
from app.services.org_bootstrap_service import SubscriptionTier, TIER_LIMITS

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when an organization exceeds their tier limit."""

    def __init__(self, resource_type: str, limit: int, current: int, tier: str):
        self.resource_type = resource_type
        self.limit = limit
        self.current = current
        self.tier = tier
        super().__init__(
            f"Quota exceeded: You've reached the {resource_type} limit ({current}/{limit}) "
            f"for the {tier} tier. Please upgrade your plan to add more."
        )


class QuotaService:
    """Service for enforcing resource quotas/limits."""

    # Resource type to limit field mapping
    RESOURCE_LIMITS = {
        "assets": "assets_max",
        "users": "users_max",
        "pm_rules": "pm_rules_max",
        "work_orders": "work_orders_per_month",
    }

    async def get_org_tier(self, org_id: str) -> SubscriptionTier:
        """
        Get the tier for an organization.

        Args:
            org_id: Organization ID

        Returns:
            SubscriptionTier enum
        """
        firestore = get_firestore_manager()
        org = await firestore.get_document("organizations", org_id)

        if not org:
            logger.warning(f"Organization {org_id} not found, defaulting to FREE tier")
            return SubscriptionTier.FREE

        tier_str = org.get("tier", "free")
        try:
            return SubscriptionTier(tier_str)
        except ValueError:
            logger.warning(f"Unknown tier '{tier_str}' for org {org_id}, defaulting to FREE")
            return SubscriptionTier.FREE

    def get_limit(self, tier: SubscriptionTier, resource_type: str) -> int:
        """
        Get the limit for a resource type at a given tier.

        Args:
            tier: Subscription tier
            resource_type: Resource type (assets, users, pm_rules, work_orders)

        Returns:
            Limit value (-1 means unlimited)
        """
        limits = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
        limit_field = self.RESOURCE_LIMITS.get(resource_type)

        if not limit_field:
            logger.warning(f"Unknown resource type: {resource_type}")
            return -1  # Unknown resource = unlimited (fail open)

        return limits.get(limit_field, -1)

    async def get_current_count(self, org_id: str, resource_type: str) -> int:
        """
        Get the current count for a resource type.
        Reads from the counts field in the org document.

        Args:
            org_id: Organization ID
            resource_type: Resource type

        Returns:
            Current count
        """
        firestore = get_firestore_manager()
        org = await firestore.get_document("organizations", org_id)

        if not org:
            return 0

        counts = org.get("counts", {})
        return counts.get(resource_type, 0)

    async def reserve_slot(
        self,
        org_id: str,
        resource_type: str,
        increment: int = 1,
    ) -> bool:
        """
        Reserve a slot for a resource.

        This function:
        1. Reads org doc to get tier and current count
        2. Checks if adding increment would exceed limit
        3. If OK, uses atomic increment to update count
        4. Raises QuotaExceededError if over limit

        Note: There's a small race window between check and increment.
        For SaaS quotas this is acceptable - worst case is one extra
        resource created before the next request fails.

        Args:
            org_id: Organization ID
            resource_type: Resource type (assets, users, pm_rules)
            increment: Number of slots to reserve (default 1)

        Returns:
            True if slot reserved successfully

        Raises:
            QuotaExceededError: If limit exceeded
        """
        firestore = get_firestore_manager()

        if not firestore.db:
            logger.error("Firestore not initialized")
            return True  # Fail open if no DB

        # Get org data
        org = await firestore.get_document("organizations", org_id)

        if not org:
            logger.warning(f"Organization {org_id} not found during quota check")
            return True  # Fail open if org doesn't exist

        # Get tier and limit
        tier_str = org.get("tier", "free")
        try:
            tier = SubscriptionTier(tier_str)
        except ValueError:
            tier = SubscriptionTier.FREE

        limit = self.get_limit(tier, resource_type)

        # Get current count
        counts = org.get("counts", {})
        current = counts.get(resource_type, 0)

        # Unlimited (-1) = no enforcement, just track
        if limit == -1:
            # Use atomic increment for tracking
            org_ref = firestore.db.collection("organizations").document(org_id)
            org_ref.update({f"counts.{resource_type}": Increment(increment)})
            logger.info(
                f"Reserved {increment} {resource_type} slot(s) for org {org_id} (unlimited tier): "
                f"{current} → {current + increment}"
            )
            return True

        # Check if adding increment would exceed limit
        if current + increment > limit:
            raise QuotaExceededError(
                resource_type=resource_type,
                limit=limit,
                current=current,
                tier=tier.value,
            )

        # Atomically increment count
        org_ref = firestore.db.collection("organizations").document(org_id)
        org_ref.update({f"counts.{resource_type}": Increment(increment)})

        logger.info(
            f"Reserved {increment} {resource_type} slot(s) for org {org_id}: "
            f"{current} → {current + increment}/{limit}"
        )
        return True

    async def release_slot(
        self,
        org_id: str,
        resource_type: str,
        decrement: int = 1,
    ) -> bool:
        """
        Release a slot when a resource is deleted.

        Args:
            org_id: Organization ID
            resource_type: Resource type
            decrement: Number of slots to release (default 1)

        Returns:
            True if successful
        """
        firestore = get_firestore_manager()

        if not firestore.db:
            return True

        # Get current count to ensure we don't go below 0
        org = await firestore.get_document("organizations", org_id)
        if not org:
            return True

        counts = org.get("counts", {})
        current = counts.get(resource_type, 0)

        # Calculate actual decrement (don't go below 0)
        actual_decrement = min(decrement, current)

        if actual_decrement > 0:
            org_ref = firestore.db.collection("organizations").document(org_id)
            org_ref.update({f"counts.{resource_type}": Increment(-actual_decrement)})

            logger.info(
                f"Released {actual_decrement} {resource_type} slot(s) for org {org_id}: "
                f"{current} → {current - actual_decrement}"
            )

        return True

    async def check_quota(
        self,
        org_id: str,
        resource_type: str,
        increment: int = 1,
    ) -> dict:
        """
        Check if quota allows adding resources (without reserving).

        Args:
            org_id: Organization ID
            resource_type: Resource type
            increment: Number to add

        Returns:
            {
                "allowed": bool,
                "current": int,
                "limit": int,
                "tier": str,
                "remaining": int
            }
        """
        tier = await self.get_org_tier(org_id)
        limit = self.get_limit(tier, resource_type)
        current = await self.get_current_count(org_id, resource_type)

        if limit == -1:
            return {
                "allowed": True,
                "current": current,
                "limit": -1,
                "tier": tier.value,
                "remaining": -1,  # Unlimited
            }

        allowed = current + increment <= limit
        remaining = max(0, limit - current)

        return {
            "allowed": allowed,
            "current": current,
            "limit": limit,
            "tier": tier.value,
            "remaining": remaining,
        }

    # ==========================================
    # CONVENIENCE METHODS FOR SPECIFIC RESOURCES
    # ==========================================

    async def reserve_asset_slot(self, org_id: str) -> bool:
        """Reserve a slot for creating an asset."""
        return await self.reserve_slot(org_id, "assets")

    async def release_asset_slot(self, org_id: str) -> bool:
        """Release a slot when an asset is deleted."""
        return await self.release_slot(org_id, "assets")

    async def reserve_user_slot(self, org_id: str) -> bool:
        """Reserve a slot for adding a user."""
        return await self.reserve_slot(org_id, "users")

    async def release_user_slot(self, org_id: str) -> bool:
        """Release a slot when a user is removed."""
        return await self.release_slot(org_id, "users")

    async def reserve_pm_rule_slot(self, org_id: str) -> bool:
        """Reserve a slot for creating a PM rule."""
        return await self.reserve_slot(org_id, "pm_rules")

    async def release_pm_rule_slot(self, org_id: str) -> bool:
        """Release a slot when a PM rule is deleted."""
        return await self.release_slot(org_id, "pm_rules")


# Global instance
quota_service = QuotaService()


def get_quota_service() -> QuotaService:
    """Get the global quota service instance."""
    return quota_service
