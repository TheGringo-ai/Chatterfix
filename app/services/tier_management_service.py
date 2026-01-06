"""
Tier Management Service
=======================

Admin service for managing organization subscription tiers.

Features:
- Change org tier (upgrade/downgrade)
- Time-limited upgrades (e.g., "enterprise for 30 days")
- Auto-downgrade when trial expires
- List all orgs with tier info

Usage:
    from app.services.tier_management_service import tier_manager

    # Upgrade to enterprise for 30 days
    await tier_manager.set_tier("acme-corp", "enterprise", trial_days=30)

    # Permanent upgrade (no expiration)
    await tier_manager.set_tier("acme-corp", "professional")

    # Downgrade to free
    await tier_manager.set_tier("acme-corp", "free")

    # List all orgs
    orgs = await tier_manager.list_orgs()
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core.firestore_db import get_firestore_manager
from app.services.org_bootstrap_service import (
    SubscriptionTier,
    TIER_LIMITS,
    create_rate_limits,
)

logger = logging.getLogger(__name__)


class TierManagementService:
    """Service for managing organization tiers."""

    async def get_org_tier_info(self, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed tier info for an organization.

        Returns:
            {
                "org_id": "acme-corp",
                "org_name": "Acme Corporation",
                "tier": "starter",
                "tier_expires_at": "2026-02-05T...",  # null if permanent
                "is_trial": true,
                "days_remaining": 25,
                "limits": {...}
            }
        """
        firestore = get_firestore_manager()

        org = await firestore.get_document("organizations", org_id)
        if not org:
            return None

        rate_limits = await firestore.get_document("rate_limits", org_id)

        tier = org.get("tier", "free")
        tier_expires_at = org.get("tier_expires_at")

        # Calculate days remaining
        days_remaining = None
        is_trial = False
        if tier_expires_at:
            try:
                expires = datetime.fromisoformat(tier_expires_at.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                remaining = expires - now
                days_remaining = max(0, remaining.days)
                is_trial = True
            except Exception:
                pass

        return {
            "org_id": org_id,
            "org_name": org.get("name", ""),
            "owner_email": org.get("owner_email", ""),
            "tier": tier,
            "tier_expires_at": tier_expires_at,
            "is_trial": is_trial,
            "days_remaining": days_remaining,
            "limits": rate_limits.get("limits") if rate_limits else TIER_LIMITS.get(SubscriptionTier(tier)),
            "usage": rate_limits.get("usage") if rate_limits else None,
            "created_at": org.get("created_at"),
        }

    async def set_tier(
        self,
        org_id: str,
        tier: str,
        trial_days: Optional[int] = None,
        reason: str = "admin_change",
    ) -> Dict[str, Any]:
        """
        Change an organization's tier.

        Args:
            org_id: Organization ID
            tier: Target tier (free, starter, professional, enterprise)
            trial_days: If set, tier expires after this many days (time-limited upgrade)
            reason: Reason for change (for audit log)

        Returns:
            Result dict with success status and new tier info

        Examples:
            # Give enterprise for 30 days
            await set_tier("acme", "enterprise", trial_days=30)

            # Permanent professional upgrade
            await set_tier("acme", "professional")

            # Downgrade to free (immediate)
            await set_tier("acme", "free")
        """
        firestore = get_firestore_manager()

        # Validate tier
        try:
            tier_enum = SubscriptionTier(tier.lower())
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid tier: {tier}. Valid: free, starter, professional, enterprise",
            }

        # Check org exists
        org = await firestore.get_document("organizations", org_id)
        if not org:
            return {
                "success": False,
                "error": f"Organization {org_id} not found",
            }

        now = datetime.now(timezone.utc)

        # Calculate expiration
        tier_expires_at = None
        if trial_days:
            tier_expires_at = (now + timedelta(days=trial_days)).isoformat()

        # Update organization document
        update_data = {
            "tier": tier_enum.value,
            "tier_expires_at": tier_expires_at,
            "tier_changed_at": now.isoformat(),
            "tier_change_reason": reason,
            "updated_at": now.isoformat(),
        }

        if firestore.db:
            firestore.db.collection("organizations").document(org_id).update(update_data)

        # Update rate limits to match new tier
        await create_rate_limits(org_id, tier_enum, force=True)

        logger.info(f"Changed org {org_id} to tier {tier_enum.value} (expires: {tier_expires_at}, reason: {reason})")

        return {
            "success": True,
            "org_id": org_id,
            "tier": tier_enum.value,
            "tier_expires_at": tier_expires_at,
            "trial_days": trial_days,
            "limits": TIER_LIMITS.get(tier_enum),
            "message": f"Tier changed to {tier_enum.value}" + (f" for {trial_days} days" if trial_days else " (permanent)"),
        }

    async def extend_trial(self, org_id: str, additional_days: int) -> Dict[str, Any]:
        """
        Extend an organization's trial period.

        Args:
            org_id: Organization ID
            additional_days: Days to add to current expiration
        """
        firestore = get_firestore_manager()

        org = await firestore.get_document("organizations", org_id)
        if not org:
            return {"success": False, "error": f"Organization {org_id} not found"}

        now = datetime.now(timezone.utc)
        current_expires = org.get("tier_expires_at")

        # Start from current expiration or now
        if current_expires:
            try:
                base = datetime.fromisoformat(current_expires.replace("Z", "+00:00"))
                if base < now:
                    base = now
            except Exception:
                base = now
        else:
            base = now

        new_expires = (base + timedelta(days=additional_days)).isoformat()

        if firestore.db:
            firestore.db.collection("organizations").document(org_id).update({
                "tier_expires_at": new_expires,
                "updated_at": now.isoformat(),
            })

        logger.info(f"Extended org {org_id} trial by {additional_days} days to {new_expires}")

        return {
            "success": True,
            "org_id": org_id,
            "tier": org.get("tier"),
            "new_expires_at": new_expires,
            "message": f"Trial extended by {additional_days} days",
        }

    async def list_orgs(
        self,
        tier_filter: Optional[str] = None,
        include_expired: bool = True,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List all organizations with tier info.

        Args:
            tier_filter: Only show orgs with this tier
            include_expired: Include orgs with expired trials
            limit: Max orgs to return
        """
        firestore = get_firestore_manager()

        if not firestore.db:
            return []

        query = firestore.db.collection("organizations")

        if tier_filter:
            query = query.where("tier", "==", tier_filter.lower())

        query = query.limit(limit)

        orgs = []
        now = datetime.now(timezone.utc)

        for doc in query.stream():
            data = doc.to_dict()
            org_id = doc.id

            tier_expires_at = data.get("tier_expires_at")
            is_expired = False
            days_remaining = None

            if tier_expires_at:
                try:
                    expires = datetime.fromisoformat(tier_expires_at.replace("Z", "+00:00"))
                    remaining = expires - now
                    days_remaining = remaining.days
                    is_expired = days_remaining < 0
                except Exception:
                    pass

            if not include_expired and is_expired:
                continue

            orgs.append({
                "org_id": org_id,
                "name": data.get("name", ""),
                "owner_email": data.get("owner_email", ""),
                "tier": data.get("tier", "free"),
                "tier_expires_at": tier_expires_at,
                "is_expired": is_expired,
                "days_remaining": days_remaining,
                "created_at": data.get("created_at"),
                "is_demo": data.get("is_demo", False),
            })

        # Sort by creation date (newest first)
        def sort_key(x):
            created = x.get("created_at", "")
            if hasattr(created, "isoformat"):
                return created.isoformat()
            return str(created) if created else ""

        orgs.sort(key=sort_key, reverse=True)

        return orgs

    async def process_expired_trials(self) -> Dict[str, Any]:
        """
        Process expired trials - downgrade to FREE tier.
        Call this periodically (e.g., daily cron job).

        Returns:
            List of orgs that were downgraded
        """
        firestore = get_firestore_manager()

        if not firestore.db:
            return {"success": False, "error": "Firestore not initialized"}

        now = datetime.now(timezone.utc)
        downgraded = []

        # Find orgs with expired tier_expires_at
        query = firestore.db.collection("organizations").where(
            "tier_expires_at", "<=", now.isoformat()
        )

        for doc in query.stream():
            org_id = doc.id
            data = doc.to_dict()
            current_tier = data.get("tier", "free")

            # Only downgrade if not already free
            if current_tier != "free":
                result = await self.set_tier(
                    org_id,
                    "free",
                    reason="trial_expired",
                )
                if result.get("success"):
                    downgraded.append({
                        "org_id": org_id,
                        "previous_tier": current_tier,
                        "new_tier": "free",
                    })
                    logger.info(f"Downgraded expired org {org_id} from {current_tier} to free")

        return {
            "success": True,
            "processed_at": now.isoformat(),
            "downgraded_count": len(downgraded),
            "downgraded": downgraded,
        }


# Global instance
tier_manager = TierManagementService()


def get_tier_manager() -> TierManagementService:
    """Get the global tier manager instance."""
    return tier_manager
