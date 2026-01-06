"""
Signup Complete Endpoint
========================

Secure endpoint to complete self-service signup after Firebase Auth.

Flow:
1. User creates Firebase Auth account (client-side)
2. Client gets Firebase ID token
3. Client calls POST /api/v1/signup/complete with:
   - Authorization: Bearer <firebase_id_token>
   - Body: { "company": "Acme Corp", "org_slug": "acme-corp" (optional) }
4. Backend:
   - Verifies token
   - Extracts uid + email
   - Checks if user already has org (idempotent)
   - Generates org_id
   - Calls bootstrap_org(tier=STARTER)  <-- SERVER-CONTROLLED
   - Returns org_id + session info

Security:
- Tier is ALWAYS server-set (starter/trial)
- Client cannot request enterprise/professional
- Client cannot call delete
"""

import logging
import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from firebase_admin import auth as firebase_auth

from app.auth import get_current_user
from app.models.user import User
from app.services.org_bootstrap_service import (
    bootstrap_org,
    get_org_status,
    SubscriptionTier,
)
from app.core.firestore_db import get_firestore_manager

router = APIRouter(prefix="/api/v1/signup", tags=["Signup"])
logger = logging.getLogger(__name__)

# Self-service tier: ALWAYS starter (30-day trial with full features)
SELF_SERVICE_TIER = SubscriptionTier.STARTER


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================


class CompleteSignupRequest(BaseModel):
    """Request to complete signup after Firebase Auth."""

    company: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Company/organization name",
    )
    org_slug: Optional[str] = Field(
        None,
        max_length=50,
        description="Desired org slug (optional, auto-generated if not provided)",
    )


class CompleteSignupResponse(BaseModel):
    """Response after successful signup completion."""

    success: bool
    org_id: str
    org_name: str
    tier: str
    trial_ends_at: str
    owner_user_id: str
    next_step: str = "/dashboard"
    message: str


# ==========================================
# HELPER FUNCTIONS
# ==========================================


def sanitize_slug(input_str: str) -> str:
    """
    Sanitize string for use as org_id slug.
    - Lowercase
    - Replace spaces and special chars with hyphens
    - Remove consecutive hyphens
    - Max 30 chars
    """
    # Lowercase and replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", input_str.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    # Truncate to 30 chars
    return slug[:30]


def generate_unique_suffix() -> str:
    """Generate a short random suffix for slug uniqueness."""
    return "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))


async def generate_unique_org_id(base_slug: str) -> str:
    """
    Generate a unique org_id, appending suffix if slug is taken.
    """
    firestore = get_firestore_manager()

    # Try the base slug first
    org_id = base_slug
    existing = await firestore.get_document("organizations", org_id)

    if not existing:
        return org_id

    # Slug taken - append suffix and retry
    for _ in range(10):  # Max 10 attempts
        org_id = f"{base_slug}-{generate_unique_suffix()}"
        existing = await firestore.get_document("organizations", org_id)
        if not existing:
            return org_id

    # Fallback: use full random suffix
    return f"{base_slug}-{generate_unique_suffix()}{generate_unique_suffix()}"


async def get_user_existing_org(uid: str) -> Optional[str]:
    """
    Check if user already belongs to an organization.
    Returns org_id if exists, None otherwise.
    """
    firestore = get_firestore_manager()
    user_doc = await firestore.get_document("users", uid)

    if user_doc and user_doc.get("organization_id"):
        return user_doc.get("organization_id")

    return None


# ==========================================
# ENDPOINTS
# ==========================================


@router.post("/complete", response_model=CompleteSignupResponse)
async def complete_signup(
    request: CompleteSignupRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Complete self-service signup after Firebase Auth.

    Requires: Authorization: Bearer <firebase_id_token>

    This endpoint:
    1. Verifies the Firebase token (via dependency)
    2. Checks if user already has an org (idempotent - returns existing)
    3. Generates unique org_id from company name
    4. Calls bootstrap_org with STARTER tier (server-enforced)
    5. Returns org info and next step

    Security:
    - Tier is ALWAYS starter (30-day trial)
    - Client cannot override tier
    - Idempotent: calling twice returns same org
    """
    logger.info(f"Signup complete request from uid={current_user.uid}, company={request.company}")

    # ========================================
    # 1. Check if user already has an org (idempotent)
    # ========================================
    existing_org_id = await get_user_existing_org(current_user.uid)

    if existing_org_id:
        logger.info(f"User {current_user.uid} already has org {existing_org_id}, returning existing")

        # Get existing org status
        status = await get_org_status(existing_org_id)
        if status:
            # Calculate trial end (30 days from creation)
            try:
                created_at = datetime.fromisoformat(status.created_at.replace("Z", "+00:00"))
                trial_ends = created_at + timedelta(days=30)
            except Exception:
                trial_ends = datetime.now(timezone.utc) + timedelta(days=30)

            return CompleteSignupResponse(
                success=True,
                org_id=existing_org_id,
                org_name=status.name,
                tier=status.tier,
                trial_ends_at=trial_ends.isoformat(),
                owner_user_id=current_user.uid,
                next_step="/dashboard",
                message="Organization already exists. Returning existing.",
            )

        # Org exists but status fetch failed - still return success
        return CompleteSignupResponse(
            success=True,
            org_id=existing_org_id,
            org_name=request.company,
            tier=SELF_SERVICE_TIER.value,
            trial_ends_at=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            owner_user_id=current_user.uid,
            next_step="/dashboard",
            message="Organization already exists.",
        )

    # ========================================
    # 2. Generate unique org_id
    # ========================================
    base_slug = sanitize_slug(request.org_slug or request.company)
    if not base_slug:
        base_slug = "org"  # Fallback if company name is all special chars

    org_id = await generate_unique_org_id(base_slug)
    logger.info(f"Generated org_id={org_id} for company={request.company}")

    # ========================================
    # 3. Bootstrap organization (STARTER tier - server-enforced)
    # ========================================
    now = datetime.now(timezone.utc)
    trial_ends = now + timedelta(days=30)

    result = await bootstrap_org(
        org_id=org_id,
        org_name=request.company,
        owner_user_id=current_user.uid,
        owner_email=current_user.email,
        owner_name=current_user.full_name or current_user.email.split("@")[0],
        tier=SELF_SERVICE_TIER,  # ALWAYS starter - no client override
        timezone_str="America/Chicago",  # Default, can change in settings later
        include_sample_data=False,  # Clean start for real users
        force=False,
    )

    if not result.success:
        logger.error(f"Bootstrap failed for user {current_user.uid}: {result.error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {result.error}",
        )

    logger.info(f"Successfully bootstrapped org {org_id} for user {current_user.uid}")

    return CompleteSignupResponse(
        success=True,
        org_id=result.org_id,
        org_name=result.org_name,
        tier=result.tier,
        trial_ends_at=trial_ends.isoformat(),
        owner_user_id=current_user.uid,
        next_step="/dashboard",
        message=f"Welcome to ChatterFix! Your 30-day trial of {result.tier} tier has started.",
    )


@router.get("/status")
async def get_signup_status(
    current_user: User = Depends(get_current_user),
):
    """
    Check if current user has completed signup (has an organization).

    Returns:
    - has_org: bool
    - org_id: str or null
    - org_name: str or null
    - tier: str or null
    """
    existing_org_id = await get_user_existing_org(current_user.uid)

    if not existing_org_id:
        return {
            "has_org": False,
            "org_id": None,
            "org_name": None,
            "tier": None,
            "message": "User has not completed signup. Call POST /api/v1/signup/complete",
        }

    status = await get_org_status(existing_org_id)

    return {
        "has_org": True,
        "org_id": existing_org_id,
        "org_name": status.name if status else None,
        "tier": status.tier if status else None,
        "message": "User has completed signup",
    }
