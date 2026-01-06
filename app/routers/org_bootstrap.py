"""
Organization Bootstrap Endpoint
================================

Provides a single endpoint to bootstrap a new organization with all required data:
- Organization document
- Rate limits configuration
- Default settings
- Owner user document
- (Optional) Sample assets and PM templates

This makes onboarding repeatable, fast, and idempotent.

Endpoint: POST /api/v1/orgs/{org_id}/bootstrap
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from app.core.firestore_db import get_firestore_manager

router = APIRouter(prefix="/api/v1/orgs", tags=["Organization Bootstrap"])
logger = logging.getLogger(__name__)


# ==========================================
# CONFIGURATION
# ==========================================


class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Default rate limits by tier
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
# REQUEST/RESPONSE MODELS
# ==========================================


class BootstrapRequest(BaseModel):
    """Request to bootstrap a new organization."""

    org_name: str = Field(..., min_length=2, max_length=100, description="Organization name")
    owner_email: EmailStr = Field(..., description="Owner's email address")
    owner_user_id: str = Field(..., min_length=1, description="Owner's Firebase UID")
    owner_name: Optional[str] = Field(None, description="Owner's display name")
    tier: SubscriptionTier = Field(SubscriptionTier.FREE, description="Subscription tier")
    timezone: Optional[str] = Field(None, description="Organization timezone")
    include_sample_data: bool = Field(False, description="Seed sample assets and PM rules")


class BootstrapResult(BaseModel):
    """Result of bootstrapping an organization."""

    success: bool
    org_id: str
    org_name: str
    tier: str
    documents_created: List[str]
    sample_data_created: Optional[Dict[str, int]] = None
    message: str


# ==========================================
# SAMPLE DATA TEMPLATES
# ==========================================


def _get_sample_assets(org_id: str) -> List[Dict[str, Any]]:
    """Generate sample assets for demo purposes."""
    now = datetime.now(timezone.utc).isoformat()
    return [
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
            "serial_number": "CAR-2023-001",
            "install_date": "2023-01-15",
            "created_at": now,
            "updated_at": now,
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
            "serial_number": "IR-2022-456",
            "install_date": "2022-06-10",
            "created_at": now,
            "updated_at": now,
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
            "serial_number": "TOY-2021-789",
            "install_date": "2021-03-20",
            "created_at": now,
            "updated_at": now,
        },
    ]


def _get_sample_pm_rules(org_id: str, assets: List[Dict]) -> List[Dict[str, Any]]:
    """Generate sample PM rules for demo purposes."""
    now = datetime.now(timezone.utc)
    rules = []

    # Map asset types to PM templates
    pm_templates = {
        "HVAC": {
            "name": "Quarterly HVAC Filter Change",
            "interval_days": 90,
            "description": "Replace air filters and check refrigerant levels",
        },
        "Compressor": {
            "name": "Monthly Compressor Oil Check",
            "interval_days": 30,
            "description": "Check oil level, drain moisture, inspect belts",
        },
        "Material Handling": {
            "name": "Weekly Forklift Safety Inspection",
            "interval_days": 7,
            "description": "Pre-shift safety checklist, fluid levels, brake test",
        },
    }

    for i, asset in enumerate(assets):
        asset_type = asset.get("asset_type", "")
        template = pm_templates.get(asset_type)

        if template:
            # Set next_due to a week from now (staggered)
            next_due = now + timedelta(days=7 + i * 3)

            rules.append({
                "organization_id": org_id,
                "asset_id": asset.get("id"),
                "name": template["name"],
                "title": f"{template['name']} - {asset.get('name')}",
                "description": template["description"],
                "schedule_type": "time",
                "interval_days": template["interval_days"],
                "tolerance_days": 3,
                "is_active": True,
                "next_due": next_due.isoformat(),
                "cooldown_hours": 24,
                "priority": "Medium",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            })

    return rules


# ==========================================
# BOOTSTRAP ENDPOINT
# ==========================================


# ==========================================
# HELPER FUNCTIONS (can be imported)
# ==========================================


async def create_rate_limits_for_org(
    org_id: str,
    tier: SubscriptionTier = SubscriptionTier.FREE,
) -> Dict[str, Any]:
    """
    Create rate limits document for an organization.

    This can be called from signup flow or bootstrap endpoint.
    Safe to call multiple times - will only create if not exists.

    Args:
        org_id: Organization ID
        tier: Subscription tier (default: FREE for self-service signups)

    Returns:
        Rate limits document data
    """
    firestore = get_firestore_manager()
    now = datetime.now(timezone.utc)

    # Check if already exists
    existing = await firestore.get_document("rate_limits", org_id)
    if existing:
        logger.info(f"Rate limits already exist for org {org_id}")
        return existing

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


@router.post("/{org_id}/bootstrap", response_model=BootstrapResult)
async def bootstrap_organization(
    org_id: str,
    request: BootstrapRequest,
    force: bool = Query(False, description="Force overwrite if org exists"),
):
    """
    Bootstrap a new organization with all required data.

    This endpoint is idempotent:
    - If org doesn't exist: creates everything
    - If org exists and force=False: returns existing org info
    - If org exists and force=True: overwrites everything

    Creates:
    1. Organization document
    2. Rate limits configuration
    3. User document for owner
    4. (Optional) Sample assets and PM rules

    Returns:
        BootstrapResult with created documents and status
    """
    logger.info(f"Bootstrap request for org_id={org_id}, tier={request.tier}")

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
                org_name=existing_org.get("name", request.org_name),
                tier=existing_org.get("tier", request.tier.value),
                documents_created=[],
                message="Organization already exists. Use force=true to overwrite.",
            )

        # ========================================
        # 2. Create organization document
        # ========================================
        settings = {**DEFAULT_SETTINGS}
        if request.timezone:
            settings["timezone"] = request.timezone

        org_data = {
            "org_id": org_id,
            "name": request.org_name,
            "owner_id": request.owner_user_id,
            "owner_email": request.owner_email,
            "tier": request.tier.value,
            "is_demo": False,
            "members": [
                {
                    "user_id": request.owner_user_id,
                    "email": request.owner_email,
                    "name": request.owner_name or request.owner_email.split("@")[0],
                    "role": "owner",
                    "joined_at": now.isoformat(),
                }
            ],
            "settings": settings,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        await firestore.create_document("organizations", org_data, doc_id=org_id)
        documents_created.append(f"organizations/{org_id}")
        logger.info(f"Created organization document: {org_id}")

        # ========================================
        # 3. Create rate limits document (using helper)
        # ========================================
        # Delete existing rate limits if force=True
        if force:
            try:
                if firestore.db:
                    firestore.db.collection("rate_limits").document(org_id).delete()
            except Exception:
                pass

        await create_rate_limits_for_org(org_id, request.tier)
        documents_created.append(f"rate_limits/{org_id}")
        logger.info(f"Created rate limits document for org: {org_id}")

        # ========================================
        # 4. Create/update user document
        # ========================================
        user_data = {
            "uid": request.owner_user_id,
            "email": request.owner_email,
            "full_name": request.owner_name or request.owner_email.split("@")[0],
            "organization_id": org_id,
            "organization_name": request.org_name,
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

        # Use set with merge to update if exists
        if firestore.db:
            firestore.db.collection("users").document(request.owner_user_id).set(
                user_data, merge=True
            )
        documents_created.append(f"users/{request.owner_user_id}")
        logger.info(f"Created/updated user document: {request.owner_user_id}")

        # ========================================
        # 5. (Optional) Create sample data
        # ========================================
        if request.include_sample_data:
            sample_data_counts = {"assets": 0, "pm_rules": 0}

            # Create sample assets
            sample_assets = _get_sample_assets(org_id)
            created_assets = []

            for asset in sample_assets:
                asset_id = await firestore.create_org_document("assets", asset, org_id)
                asset["id"] = asset_id
                created_assets.append(asset)
                documents_created.append(f"assets/{asset_id}")
                sample_data_counts["assets"] += 1

            logger.info(f"Created {len(created_assets)} sample assets")

            # Create sample PM rules
            sample_rules = _get_sample_pm_rules(org_id, created_assets)

            for rule in sample_rules:
                rule_id = await firestore.create_org_document("pm_schedule_rules", rule, org_id)
                documents_created.append(f"pm_schedule_rules/{rule_id}")
                sample_data_counts["pm_rules"] += 1

            logger.info(f"Created {sample_data_counts['pm_rules']} sample PM rules")

        # ========================================
        # 6. Return success result
        # ========================================
        return BootstrapResult(
            success=True,
            org_id=org_id,
            org_name=request.org_name,
            tier=request.tier.value,
            documents_created=documents_created,
            sample_data_created=sample_data_counts,
            message=f"Organization '{request.org_name}' bootstrapped successfully",
        )

    except Exception as e:
        logger.error(f"Bootstrap failed for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bootstrap failed: {str(e)}",
        )


@router.get("/{org_id}/status")
async def get_org_status(org_id: str):
    """
    Get organization bootstrap status and summary.

    Returns current state of organization including:
    - Organization details
    - Rate limits and usage
    - Document counts
    """
    try:
        firestore = get_firestore_manager()

        # Get organization
        org = await firestore.get_document("organizations", org_id)
        if not org:
            raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")

        # Get rate limits
        rate_limits = await firestore.get_document("rate_limits", org_id)

        # Count documents
        assets = await firestore.get_org_collection("assets", org_id, limit=1000)
        work_orders = await firestore.get_org_collection("work_orders", org_id, limit=1000)
        pm_rules = await firestore.get_org_collection("pm_schedule_rules", org_id, limit=100)

        return JSONResponse(content={
            "org_id": org_id,
            "name": org.get("name"),
            "tier": org.get("tier", "free"),
            "is_demo": org.get("is_demo", False),
            "owner_email": org.get("owner_email"),
            "member_count": len(org.get("members", [])),
            "created_at": org.get("created_at"),
            "rate_limits": rate_limits.get("limits") if rate_limits else None,
            "usage": rate_limits.get("usage") if rate_limits else None,
            "counts": {
                "assets": len(assets),
                "work_orders": len(work_orders),
                "pm_rules": len(pm_rules),
            },
            "status": "ready",
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get org status for {org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    confirm: bool = Query(False, description="Confirm deletion"),
):
    """
    Delete an organization and all its data.

    WARNING: This is destructive and cannot be undone.
    Requires confirm=true to execute.

    Deletes:
    - Organization document
    - Rate limits
    - All assets
    - All work orders
    - All PM rules
    - All parts and vendors
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Deletion requires confirm=true. This action cannot be undone.",
        )

    try:
        firestore = get_firestore_manager()

        if not firestore.db:
            raise Exception("Firestore not initialized")

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
            logger.info(f"Deleted {len(docs)} {collection} for org {org_id}")

        # Delete rate limits
        try:
            firestore.db.collection("rate_limits").document(org_id).delete()
            deleted_counts["rate_limits"] = 1
        except Exception:
            pass

        # Delete organization document
        try:
            firestore.db.collection("organizations").document(org_id).delete()
            deleted_counts["organizations"] = 1
        except Exception:
            pass

        logger.info(f"Deleted organization {org_id}")

        return JSONResponse(content={
            "success": True,
            "org_id": org_id,
            "deleted": deleted_counts,
            "message": f"Organization {org_id} and all data deleted",
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
