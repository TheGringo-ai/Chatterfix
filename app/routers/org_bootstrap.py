"""
Organization Bootstrap API Router
=================================

Admin API endpoints for organization provisioning.
All logic lives in org_bootstrap_service.py - this is just the HTTP layer.

Endpoints:
- POST /api/v1/orgs/{org_id}/bootstrap - Create org
- GET /api/v1/orgs/{org_id}/status - Get org status
- DELETE /api/v1/orgs/{org_id} - Delete org (requires confirm=true)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from app.services.org_bootstrap_service import (
    SubscriptionTier,
    bootstrap_org,
    delete_org,
    get_org_status,
    create_rate_limits,
    TIER_LIMITS,
)

router = APIRouter(prefix="/api/v1/orgs", tags=["Organization Bootstrap"])
logger = logging.getLogger(__name__)


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


class BootstrapResponse(BaseModel):
    """Response from bootstrap endpoint."""

    success: bool
    org_id: str
    org_name: str
    tier: str
    documents_created: list
    sample_data_created: Optional[dict] = None
    message: str
    error: Optional[str] = None


# ==========================================
# ENDPOINTS
# ==========================================


@router.post("/{org_id}/bootstrap", response_model=BootstrapResponse)
async def bootstrap_organization_endpoint(
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
    """
    result = await bootstrap_org(
        org_id=org_id,
        org_name=request.org_name,
        owner_user_id=request.owner_user_id,
        owner_email=request.owner_email,
        owner_name=request.owner_name or "",
        tier=request.tier,
        timezone_str=request.timezone,
        include_sample_data=request.include_sample_data,
        force=force,
    )

    if not result.success and result.error:
        raise HTTPException(status_code=500, detail=result.error)

    return BootstrapResponse(
        success=result.success,
        org_id=result.org_id,
        org_name=result.org_name,
        tier=result.tier,
        documents_created=result.documents_created,
        sample_data_created=result.sample_data_created,
        message=result.message,
        error=result.error,
    )


@router.get("/{org_id}/status")
async def get_organization_status_endpoint(org_id: str):
    """
    Get organization bootstrap status and summary.

    Returns current state of organization including:
    - Organization details
    - Rate limits and usage
    - Document counts
    """
    status = await get_org_status(org_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")

    return JSONResponse(content=status.to_dict())


@router.delete("/{org_id}")
async def delete_organization_endpoint(
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

    result = await delete_org(org_id)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Delete failed")

    return JSONResponse(content=result.to_dict())


# ==========================================
# EXPORTS FOR OTHER MODULES
# ==========================================

# Re-export for backward compatibility with signup.py imports
__all__ = [
    "SubscriptionTier",
    "create_rate_limits",
    "bootstrap_org",
    "delete_org",
    "get_org_status",
    "TIER_LIMITS",
]
