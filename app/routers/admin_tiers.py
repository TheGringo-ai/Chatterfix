"""
Admin Tier Management API
=========================

Admin-only endpoints for managing organization tiers.

SECURITY: These endpoints should be protected by admin auth.
For now, they use a simple admin secret header.

Endpoints:
- GET  /api/v1/admin/orgs - List all organizations
- GET  /api/v1/admin/orgs/{org_id} - Get org tier info
- POST /api/v1/admin/orgs/{org_id}/tier - Change tier
- POST /api/v1/admin/orgs/{org_id}/extend - Extend trial
- POST /api/v1/admin/process-expired - Process expired trials
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field

from app.services.tier_management_service import get_tier_manager

router = APIRouter(prefix="/api/v1/admin", tags=["Admin - Tier Management"])
logger = logging.getLogger(__name__)

# Admin secret MUST be set via environment variable - no default allowed
# SECURITY: Never commit secrets or use hardcoded fallbacks
ADMIN_SECRET = os.getenv("ADMIN_SECRET")


def verify_admin(x_admin_secret: str = Header(None)):
    """Verify admin secret header."""
    # Fail if admin secret is not configured in environment
    if not ADMIN_SECRET:
        logger.error("ADMIN_SECRET environment variable is not configured")
        raise HTTPException(
            status_code=500,
            detail="Admin authentication not configured. Contact system administrator.",
        )

    if not x_admin_secret or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Provide X-Admin-Secret header.",
        )
    return True


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================


class SetTierRequest(BaseModel):
    """Request to change organization tier."""

    tier: str = Field(..., description="Target tier: free, starter, professional, enterprise")
    trial_days: Optional[int] = Field(None, description="If set, tier expires after this many days")
    reason: Optional[str] = Field("admin_change", description="Reason for change")


class ExtendTrialRequest(BaseModel):
    """Request to extend trial period."""

    additional_days: int = Field(..., gt=0, description="Days to add to trial")


# ==========================================
# ENDPOINTS
# ==========================================


@router.get("/orgs")
async def list_organizations(
    tier: Optional[str] = Query(None, description="Filter by tier"),
    include_expired: bool = Query(True, description="Include expired trials"),
    limit: int = Query(100, ge=1, le=500),
    x_admin_secret: str = Header(None),
):
    """
    List all organizations with tier info.

    Headers:
        X-Admin-Secret: <admin_secret>

    Query params:
        tier: Filter by tier (free, starter, professional, enterprise)
        include_expired: Include orgs with expired trials
        limit: Max orgs to return (default 100)
    """
    verify_admin(x_admin_secret)

    manager = get_tier_manager()
    orgs = await manager.list_orgs(
        tier_filter=tier,
        include_expired=include_expired,
        limit=limit,
    )

    return {
        "count": len(orgs),
        "organizations": orgs,
    }


@router.get("/orgs/{org_id}")
async def get_organization_tier(
    org_id: str,
    x_admin_secret: str = Header(None),
):
    """
    Get detailed tier info for an organization.

    Headers:
        X-Admin-Secret: <admin_secret>
    """
    verify_admin(x_admin_secret)

    manager = get_tier_manager()
    info = await manager.get_org_tier_info(org_id)

    if not info:
        raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")

    return info


@router.post("/orgs/{org_id}/tier")
async def set_organization_tier(
    org_id: str,
    request: SetTierRequest,
    x_admin_secret: str = Header(None),
):
    """
    Change an organization's tier.

    Headers:
        X-Admin-Secret: <admin_secret>

    Examples:
        # Give enterprise for 30 days
        {"tier": "enterprise", "trial_days": 30}

        # Permanent professional upgrade
        {"tier": "professional"}

        # Downgrade to free
        {"tier": "free"}
    """
    verify_admin(x_admin_secret)

    manager = get_tier_manager()
    result = await manager.set_tier(
        org_id=org_id,
        tier=request.tier,
        trial_days=request.trial_days,
        reason=request.reason or "admin_change",
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/orgs/{org_id}/extend")
async def extend_organization_trial(
    org_id: str,
    request: ExtendTrialRequest,
    x_admin_secret: str = Header(None),
):
    """
    Extend an organization's trial period.

    Headers:
        X-Admin-Secret: <admin_secret>

    Example:
        {"additional_days": 14}
    """
    verify_admin(x_admin_secret)

    manager = get_tier_manager()
    result = await manager.extend_trial(
        org_id=org_id,
        additional_days=request.additional_days,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/process-expired")
async def process_expired_trials(
    x_admin_secret: str = Header(None),
):
    """
    Process expired trials - downgrade to FREE tier.

    Call this periodically (e.g., daily cron job) or manually.

    Headers:
        X-Admin-Secret: <admin_secret>
    """
    verify_admin(x_admin_secret)

    manager = get_tier_manager()
    result = await manager.process_expired_trials()

    return result
