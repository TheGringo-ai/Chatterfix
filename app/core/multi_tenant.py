"""
Multi-Tenant Security Module

Provides centralized organization_id handling and validation for
multi-tenant data isolation. All Firestore operations MUST use
organization_id from this module to ensure proper data scoping.

Usage:
    from app.core.multi_tenant import get_organization_id, require_organization_id

    # In router endpoints:
    org_id = get_organization_id(current_user, request_org_id)  # May return None
    org_id = require_organization_id(current_user, request_org_id)  # Raises if missing
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status

from app.models.user import User

logger = logging.getLogger(__name__)


class OrganizationContextError(Exception):
    """Raised when organization context is missing or invalid."""

    pass


def get_organization_id(
    current_user: Optional[User],
    explicit_org_id: Optional[str] = None,
    allow_explicit: bool = True,
) -> Optional[str]:
    """
    Get organization_id from authenticated user or explicit parameter.

    Priority:
    1. Authenticated user's organization_id (from auth token claims)
    2. Explicit organization_id parameter (if allow_explicit=True)

    Args:
        current_user: Authenticated user from auth dependency (may be None)
        explicit_org_id: Explicitly provided organization_id (from request body/query)
        allow_explicit: If False, reject explicit org_id when user is authenticated

    Returns:
        organization_id string or None if not available

    Note:
        This function does NOT raise exceptions. Use require_organization_id()
        for endpoints that must have org context.
    """
    # Priority 1: Use authenticated user's organization
    if current_user and current_user.organization_id:
        # If explicit org_id provided, validate it matches user's org
        if explicit_org_id and explicit_org_id != current_user.organization_id:
            logger.warning(
                f"User {current_user.uid} attempted cross-org access: "
                f"user_org={current_user.organization_id}, requested={explicit_org_id}"
            )
            return None  # Don't return mismatched org
        return current_user.organization_id

    # Priority 2: Use explicit org_id (for unauthenticated or legacy requests)
    if allow_explicit and explicit_org_id:
        logger.debug(
            f"Using explicit organization_id={explicit_org_id} "
            "(TODO: require auth token in production)"
        )
        return explicit_org_id

    return None


def require_organization_id(
    current_user: Optional[User],
    explicit_org_id: Optional[str] = None,
    allow_explicit: bool = True,
) -> str:
    """
    Require organization_id - raises HTTPException if not available.

    Use this in endpoints that MUST have organization context.

    Args:
        current_user: Authenticated user from auth dependency
        explicit_org_id: Explicitly provided organization_id
        allow_explicit: If False, only accept org from auth token

    Returns:
        organization_id string (never None)

    Raises:
        HTTPException 401: If not authenticated and no explicit org provided
        HTTPException 403: If user tries to access different organization
        HTTPException 400: If organization context is missing

    Example:
        @router.get("/items")
        async def get_items(
            current_user: Optional[User] = Depends(get_optional_current_user),
            org_id: Optional[str] = Query(None),
        ):
            organization_id = require_organization_id(current_user, org_id)
            return await service.get_items(organization_id)
    """
    # Check for cross-org access attempt first
    if current_user and current_user.organization_id:
        if explicit_org_id and explicit_org_id != current_user.organization_id:
            logger.warning(
                f"SECURITY: User {current_user.uid} ({current_user.email}) "
                f"attempted to access org {explicit_org_id} but belongs to "
                f"{current_user.organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access resources from another organization",
            )
        return current_user.organization_id

    # No authenticated user with org - check explicit
    if allow_explicit and explicit_org_id:
        # Log warning for production TODO
        logger.warning(
            f"Using explicit organization_id={explicit_org_id} without auth. "
            "TODO: Require authenticated user with org claim in production."
        )
        return explicit_org_id

    # No org context available
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide valid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # User is authenticated but has no org
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Organization context required. User is not associated with an organization.",
    )


def validate_organization_access(
    current_user: User,
    resource_org_id: str,
) -> bool:
    """
    Validate that user has access to a specific organization's resource.

    Args:
        current_user: Authenticated user
        resource_org_id: Organization ID of the resource being accessed

    Returns:
        True if access is allowed

    Raises:
        HTTPException 403: If user doesn't have access
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any organization",
        )

    if current_user.organization_id != resource_org_id:
        logger.warning(
            f"SECURITY: User {current_user.uid} tried to access resource "
            f"from org {resource_org_id} but belongs to {current_user.organization_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Resource belongs to another organization",
        )

    return True


def get_org_id_from_request(request: Request) -> Optional[str]:
    """
    Extract organization_id from various request sources.

    Checks (in order):
    1. Request state (set by middleware)
    2. Query parameter 'organization_id' or 'org_id'
    3. Header 'X-Organization-ID'

    Args:
        request: FastAPI Request object

    Returns:
        organization_id or None
    """
    # Check request state (middleware may have set this)
    if hasattr(request.state, "organization_id"):
        return request.state.organization_id

    # Check query parameters
    org_id = request.query_params.get("organization_id") or request.query_params.get(
        "org_id"
    )
    if org_id:
        return org_id

    # Check headers
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        return org_id

    return None


# ==========================================
# DECORATORS FOR ROUTE PROTECTION
# ==========================================


def org_scoped(func):
    """
    Decorator to mark a function as organization-scoped.

    This is primarily for documentation/tooling purposes.
    Actual enforcement should use require_organization_id().

    Usage:
        @org_scoped
        async def get_work_orders(organization_id: str):
            ...
    """
    func._org_scoped = True
    return func


# ==========================================
# CONSTANTS
# ==========================================

# Demo organization ID for unauthenticated demo access
DEMO_ORGANIZATION_ID = "demo_org"

# System organization ID for global/system resources
SYSTEM_ORGANIZATION_ID = "__system__"


def is_demo_organization(org_id: str) -> bool:
    """Check if organization is the demo organization."""
    return org_id == DEMO_ORGANIZATION_ID or org_id.startswith("demo_")


def is_system_organization(org_id: str) -> bool:
    """Check if organization is the system organization."""
    return org_id == SYSTEM_ORGANIZATION_ID
