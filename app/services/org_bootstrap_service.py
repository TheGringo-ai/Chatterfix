"""
Organization Bootstrap Service
==============================

Single source of truth for organization provisioning.
Both admin API and self-service signup call these functions.

Functions:
- bootstrap_org(): Create org + rate limits + user
- delete_org(): Remove org and all data
- get_org_status(): Get org state and counts
- create_rate_limits(): Create/update rate limits for an org
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


# ==========================================
# CONFIGURATION
# ==========================================


class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Rate limits by tier
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "ai_requests_per_day": 25,
        "work_orders_per_month": 50,
        "assets_max": 10,
        "users_max": 3,
        "pm_rules_max": 5,
        "storage_mb": 100,
    },
    SubscriptionTier.STARTER: {
        "ai_requests_per_day": 100,
        "work_orders_per_month": 200,
        "assets_max": 50,
        "users_max": 10,
        "pm_rules_max": 25,
        "storage_mb": 500,
    },
    SubscriptionTier.PROFESSIONAL: {
        "ai_requests_per_day": 500,
        "work_orders_per_month": 1000,
        "assets_max": 250,
        "users_max": 50,
        "pm_rules_max": 100,
        "storage_mb": 2000,
    },
    SubscriptionTier.ENTERPRISE: {
        "ai_requests_per_day": -1,  # Unlimited
        "work_orders_per_month": -1,
        "assets_max": -1,
        "users_max": -1,
        "pm_rules_max": -1,
        "storage_mb": -1,
    },
}

# Default organization settings
DEFAULT_SETTINGS = {
    "timezone": "America/Chicago",
    "work_order_prefix": "WO",
    "asset_tag_prefix": "ASSET",
    "date_format": "MM/DD/YYYY",
    "time_format": "12h",
    "notifications": {
        "email_on_wo_assigned": True,
        "email_on_wo_completed": True,
        "email_on_pm_due": True,
    },
    "features": {
        "voice_commands": True,
        "ocr_scanning": True,
        "ai_assistant": True,
        "safety_inspections": False,  # Enterprise only
        "ar_training": False,  # Enterprise only
    },
}


# ==========================================
# RESULT TYPES
# ==========================================


class BootstrapResult:
    """Result of bootstrap operation."""

    def __init__(
        self,
        success: bool,
        org_id: str,
        org_name: str = "",
        tier: str = "free",
        documents_created: List[str] = None,
        sample_data_created: Dict[str, int] = None,
        message: str = "",
        error: str = None,
    ):
        self.success = success
        self.org_id = org_id
        self.org_name = org_name
        self.tier = tier
        self.documents_created = documents_created or []
        self.sample_data_created = sample_data_created
        self.message = message
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "org_id": self.org_id,
            "org_name": self.org_name,
            "tier": self.tier,
            "documents_created": self.documents_created,
            "sample_data_created": self.sample_data_created,
            "message": self.message,
            "error": self.error,
        }


class DeleteResult:
    """Result of delete operation."""

    def __init__(
        self,
        success: bool,
        org_id: str,
        deleted_counts: Dict[str, int] = None,
        message: str = "",
        error: str = None,
    ):
        self.success = success
        self.org_id = org_id
        self.deleted_counts = deleted_counts or {}
        self.message = message
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "org_id": self.org_id,
            "deleted": self.deleted_counts,
            "message": self.message,
            "error": self.error,
        }


class OrgStatus:
    """Organization status and counts."""

    def __init__(
        self,
        org_id: str,
        name: str,
        tier: str,
        is_demo: bool,
        owner_email: str,
        member_count: int,
        created_at: str,
        rate_limits: Dict[str, Any],
        usage: Dict[str, Any],
        counts: Dict[str, int],
        status: str = "ready",
    ):
        self.org_id = org_id
        self.name = name
        self.tier = tier
        self.is_demo = is_demo
        self.owner_email = owner_email
        self.member_count = member_count
        self.created_at = created_at
        self.rate_limits = rate_limits
        self.usage = usage
        self.counts = counts
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "org_id": self.org_id,
            "name": self.name,
            "tier": self.tier,
            "is_demo": self.is_demo,
            "owner_email": self.owner_email,
            "member_count": self.member_count,
            "created_at": self.created_at,
            "rate_limits": self.rate_limits,
            "usage": self.usage,
            "counts": self.counts,
            "status": self.status,
        }


# ==========================================
# CORE SERVICE FUNCTIONS
# ==========================================


async def create_rate_limits(
    org_id: str,
    tier: SubscriptionTier = SubscriptionTier.FREE,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Create rate limits document for an organization.

    Args:
        org_id: Organization ID
        tier: Subscription tier
        force: If True, overwrite existing rate limits

    Returns:
        Rate limits document data
    """
    firestore = get_firestore_manager()
    now = datetime.now(timezone.utc)

    # Check if already exists
    if not force:
        existing = await firestore.get_document("rate_limits", org_id)
        if existing:
            logger.info(f"Rate limits already exist for org {org_id}")
            return existing

    # Delete existing if force
    if force and firestore.db:
        try:
            firestore.db.collection("rate_limits").document(org_id).delete()
        except Exception:
            pass

    tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])

    rate_limit_data = {
        "organization_id": org_id,
        "tier": tier.value,
        "limits": tier_limits,
        "usage": {
            "ai_requests_today": 0,
            "work_orders_this_month": 0,
            "assets_count": 0,
            "users_count": 1,
            "pm_rules_count": 0,
            "storage_used_mb": 0,
        },
        "billing_cycle_start": now.isoformat(),
        "next_reset": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    await firestore.create_document("rate_limits", rate_limit_data, doc_id=org_id)
    logger.info(f"Created rate limits for org {org_id} with tier {tier.value}")

    return rate_limit_data


async def bootstrap_org(
    org_id: str,
    org_name: str,
    owner_user_id: str,
    owner_email: str,
    owner_name: str = "",
    tier: SubscriptionTier = SubscriptionTier.FREE,
    timezone_str: str = None,
    include_sample_data: bool = False,
    force: bool = False,
) -> BootstrapResult:
    """
    Bootstrap a new organization with all required data.

    This is the SINGLE SOURCE OF TRUTH for org creation.
    Both admin API and self-service signup call this function.

    Args:
        org_id: Unique organization identifier
        org_name: Display name for organization
        owner_user_id: Firebase UID of owner
        owner_email: Owner's email address
        owner_name: Owner's display name (optional)
        tier: Subscription tier (default: FREE)
        timezone_str: Organization timezone (optional)
        include_sample_data: Seed sample assets and PM rules
        force: Overwrite if org exists

    Returns:
        BootstrapResult with status and created documents
    """
    logger.info(f"Bootstrap request for org_id={org_id}, tier={tier.value}")

    try:
        firestore = get_firestore_manager()
        now = datetime.now(timezone.utc)
        documents_created = []
        sample_data_counts = None

        # ========================================
        # 1. Check if org already exists
        # ========================================
        existing_org = await firestore.get_document("organizations", org_id)

        if existing_org and not force:
            logger.info(f"Organization {org_id} already exists, returning existing info")
            return BootstrapResult(
                success=True,
                org_id=org_id,
                org_name=existing_org.get("name", org_name),
                tier=existing_org.get("tier", tier.value),
                documents_created=[],
                message="Organization already exists. Use force=true to overwrite.",
            )

        # ========================================
        # 2. Create organization document
        # ========================================
        settings = {**DEFAULT_SETTINGS}
        if timezone_str:
            settings["timezone"] = timezone_str

        org_data = {
            "org_id": org_id,
            "name": org_name,
            "owner_id": owner_user_id,
            "owner_email": owner_email,
            "tier": tier.value,
            "is_demo": False,
            "members": [
                {
                    "user_id": owner_user_id,
                    "email": owner_email,
                    "name": owner_name or owner_email.split("@")[0],
                    "role": "owner",
                    "joined_at": now.isoformat(),
                }
            ],
            # Resource counts for quota enforcement
            "counts": {
                "assets": 0,
                "users": 1,  # Owner counts as 1
                "pm_rules": 0,
                "work_orders": 0,
            },
            "settings": settings,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        await firestore.create_document("organizations", org_data, doc_id=org_id)
        documents_created.append(f"organizations/{org_id}")
        logger.info(f"Created organization document: {org_id}")

        # ========================================
        # 3. Create rate limits document
        # ========================================
        await create_rate_limits(org_id, tier, force=force)
        documents_created.append(f"rate_limits/{org_id}")

        # ========================================
        # 4. Create/update user document
        # ========================================
        user_data = {
            "uid": owner_user_id,
            "email": owner_email,
            "full_name": owner_name or owner_email.split("@")[0],
            "organization_id": org_id,
            "organization_name": org_name,
            "role": "owner",
            "permissions": [
                "manage_organization",
                "manage_users",
                "manage_assets",
                "manage_work_orders",
                "manage_inventory",
                "manage_pm_rules",
                "view_reports",
                "use_ai",
            ],
            "is_active": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        if firestore.db:
            firestore.db.collection("users").document(owner_user_id).set(
                user_data, merge=True
            )
        documents_created.append(f"users/{owner_user_id}")
        logger.info(f"Created/updated user document: {owner_user_id}")

        # ========================================
        # 5. (Optional) Create sample data
        # ========================================
        if include_sample_data:
            sample_data_counts = await _create_sample_data(org_id, firestore, documents_created)

        # ========================================
        # 6. Return success result
        # ========================================
        return BootstrapResult(
            success=True,
            org_id=org_id,
            org_name=org_name,
            tier=tier.value,
            documents_created=documents_created,
            sample_data_created=sample_data_counts,
            message=f"Organization '{org_name}' bootstrapped successfully",
        )

    except Exception as e:
        logger.error(f"Bootstrap failed for org {org_id}: {e}")
        return BootstrapResult(
            success=False,
            org_id=org_id,
            error=str(e),
            message=f"Bootstrap failed: {str(e)}",
        )


async def delete_org(org_id: str) -> DeleteResult:
    """
    Delete an organization and ALL its data.

    WARNING: This is destructive and cannot be undone.

    Args:
        org_id: Organization ID to delete

    Returns:
        DeleteResult with deleted counts
    """
    logger.info(f"Delete request for org_id={org_id}")

    try:
        firestore = get_firestore_manager()

        if not firestore.db:
            return DeleteResult(
                success=False,
                org_id=org_id,
                error="Firestore not initialized",
                message="Database connection failed",
            )

        deleted_counts = {}

        # Delete collections in order
        collections_to_delete = [
            "work_orders",
            "pm_schedule_rules",
            "pm_evaluations",
            "assets",
            "parts",
            "vendors",
            "asset_meters",
            "asset_categories",
            "locations",
        ]

        for collection in collections_to_delete:
            docs = list(
                firestore.db.collection(collection)
                .where("organization_id", "==", org_id)
                .stream()
            )
            for doc in docs:
                doc.reference.delete()
            deleted_counts[collection] = len(docs)
            if len(docs) > 0:
                logger.info(f"Deleted {len(docs)} {collection} for org {org_id}")

        # Delete rate limits
        try:
            firestore.db.collection("rate_limits").document(org_id).delete()
            deleted_counts["rate_limits"] = 1
        except Exception:
            deleted_counts["rate_limits"] = 0

        # Delete organization document
        try:
            firestore.db.collection("organizations").document(org_id).delete()
            deleted_counts["organizations"] = 1
        except Exception:
            deleted_counts["organizations"] = 0

        logger.info(f"Deleted organization {org_id}")

        return DeleteResult(
            success=True,
            org_id=org_id,
            deleted_counts=deleted_counts,
            message=f"Organization {org_id} and all data deleted",
        )

    except Exception as e:
        logger.error(f"Delete failed for org {org_id}: {e}")
        return DeleteResult(
            success=False,
            org_id=org_id,
            error=str(e),
            message=f"Delete failed: {str(e)}",
        )


async def get_org_status(org_id: str) -> Optional[OrgStatus]:
    """
    Get organization status, limits, and counts.

    Args:
        org_id: Organization ID

    Returns:
        OrgStatus or None if org not found
    """
    try:
        firestore = get_firestore_manager()

        # Get organization
        org = await firestore.get_document("organizations", org_id)
        if not org:
            return None

        # Get rate limits
        rate_limits = await firestore.get_document("rate_limits", org_id)

        # Count documents
        assets = await firestore.get_org_collection("assets", org_id, limit=1000)
        work_orders = await firestore.get_org_collection("work_orders", org_id, limit=1000)
        pm_rules = await firestore.get_org_collection("pm_schedule_rules", org_id, limit=100)

        return OrgStatus(
            org_id=org_id,
            name=org.get("name", ""),
            tier=org.get("tier", "free"),
            is_demo=org.get("is_demo", False),
            owner_email=org.get("owner_email", ""),
            member_count=len(org.get("members", [])),
            created_at=org.get("created_at", ""),
            rate_limits=rate_limits.get("limits") if rate_limits else None,
            usage=rate_limits.get("usage") if rate_limits else None,
            counts={
                "assets": len(assets),
                "work_orders": len(work_orders),
                "pm_rules": len(pm_rules),
            },
            status="ready",
        )

    except Exception as e:
        logger.error(f"Failed to get org status for {org_id}: {e}")
        return None


def get_tier_limits(tier: SubscriptionTier) -> Dict[str, int]:
    """Get rate limits for a tier."""
    return TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])


# ==========================================
# SAMPLE DATA (internal helper)
# ==========================================


async def _create_sample_data(
    org_id: str,
    firestore,
    documents_created: List[str],
) -> Dict[str, int]:
    """Create sample assets and PM rules for demo purposes."""
    now = datetime.now(timezone.utc)
    counts = {"assets": 0, "pm_rules": 0}

    # Sample assets
    sample_assets = [
        {
            "organization_id": org_id,
            "name": "HVAC Unit - Main Building",
            "asset_tag": "HVAC-001",
            "asset_type": "HVAC",
            "location": "Rooftop - Building A",
            "status": "operational",
            "criticality": 4,
            "manufacturer": "Carrier",
            "model": "50XC",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "organization_id": org_id,
            "name": "Air Compressor #1",
            "asset_tag": "COMP-001",
            "asset_type": "Compressor",
            "location": "Utility Room",
            "status": "operational",
            "criticality": 3,
            "manufacturer": "Ingersoll Rand",
            "model": "R-Series 30",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "organization_id": org_id,
            "name": "Forklift - Warehouse",
            "asset_tag": "FORK-001",
            "asset_type": "Material Handling",
            "location": "Warehouse Floor",
            "status": "operational",
            "criticality": 3,
            "manufacturer": "Toyota",
            "model": "8FGCU25",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
    ]

    created_assets = []
    for asset in sample_assets:
        asset_id = await firestore.create_org_document("assets", asset, org_id)
        asset["id"] = asset_id
        created_assets.append(asset)
        documents_created.append(f"assets/{asset_id}")
        counts["assets"] += 1

    # PM rule templates by asset type
    pm_templates = {
        "HVAC": {"name": "Quarterly HVAC Filter Change", "interval_days": 90},
        "Compressor": {"name": "Monthly Compressor Oil Check", "interval_days": 30},
        "Material Handling": {"name": "Weekly Forklift Safety Inspection", "interval_days": 7},
    }

    for i, asset in enumerate(created_assets):
        asset_type = asset.get("asset_type", "")
        template = pm_templates.get(asset_type)

        if template:
            next_due = now + timedelta(days=7 + i * 3)
            rule = {
                "organization_id": org_id,
                "asset_id": asset.get("id"),
                "name": template["name"],
                "title": f"{template['name']} - {asset.get('name')}",
                "description": f"Scheduled maintenance for {asset.get('name')}",
                "schedule_type": "time",
                "interval_days": template["interval_days"],
                "tolerance_days": 3,
                "is_active": True,
                "next_due": next_due.isoformat(),
                "cooldown_hours": 24,
                "priority": "Medium",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
            rule_id = await firestore.create_org_document("pm_schedule_rules", rule, org_id)
            documents_created.append(f"pm_schedule_rules/{rule_id}")
            counts["pm_rules"] += 1

    logger.info(f"Created sample data for org {org_id}: {counts}")
    return counts
