"""
Authentication module for FastAPI dependencies using Firebase.
Provides dependencies to protect endpoints and get the current authenticated user.

Two authentication methods supported:
1. OAuth2 Bearer token (Authorization header) - for API calls
2. Cookie-based session (session_token cookie) - for web pages

Trial access checking:
- All new users get 30-day free trial
- Access is blocked when trial expires (unless paid subscription)
"""

import asyncio
import logging
from typing import Annotated, Optional, Dict, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth

from app.models.user import User
from app.services.auth_service import verify_id_token_and_get_user, check_permission
from app.services.subscription_service import get_subscription_service, SubscriptionStatus

logger = logging.getLogger(__name__)

# Configurable roles for role-based access control
ADMIN_ROLES = {"owner", "admin", "manager", "supervisor"}

# This tells FastAPI where the client can go to get a token.
# Since Firebase handles this on the client-side, this is mainly for documentation purposes.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token", auto_error=False
)


# ==========================================
# COOKIE-BASED AUTH (for web pages)
# ==========================================


async def get_current_user_from_cookie(request: Request) -> Optional[User]:
    """
    Get user from session cookie - used for HTML page routes.
    Returns None if not authenticated (does not raise exception).

    Includes:
    - 5-second timeout for Firebase verification
    - Specific exception handling for Firebase auth errors
    - Logging for failed authentication attempts
    """
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None

    try:
        # Add 5-second timeout for Firebase verification call
        user = await asyncio.wait_for(
            verify_id_token_and_get_user(session_token),
            timeout=5.0
        )
        return user
    except asyncio.TimeoutError:
        logger.warning(
            "Token verification timed out",
            extra={"client": request.client.host if request.client else "unknown"}
        )
    except auth.InvalidIdTokenError:
        logger.warning(
            "Invalid token provided",
            extra={"client": request.client.host if request.client else "unknown"}
        )
    except auth.ExpiredIdTokenError:
        logger.info(
            "Expired token - user needs to re-authenticate",
            extra={"client": request.client.host if request.client else "unknown"}
        )
    except auth.RevokedIdTokenError:
        logger.warning(
            "Revoked token detected",
            extra={"client": request.client.host if request.client else "unknown"}
        )
    except Exception as e:
        logger.error(
            f"Unexpected auth error: {type(e).__name__}",
            extra={
                "client": request.client.host if request.client else "unknown",
                "path": request.url.path,
            }
        )
    return None


async def require_auth_cookie(request: Request) -> User:
    """
    Require authentication via cookie - raises 401 if not authenticated.
    Use this for page routes that require login.
    """
    user = await get_current_user_from_cookie(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


# ==========================================
# OAUTH2 BEARER TOKEN AUTH (for API calls)
# ==========================================


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
) -> Optional[User]:
    """
    FastAPI dependency that tries to get a user but does not fail if not present.
    """
    if not token:
        return None
    user = await verify_id_token_and_get_user(token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    FastAPI dependency to verify the Firebase ID token and get the user.

    This function is used in endpoint definitions to protect them.

    Args:
        token: The bearer token from the 'Authorization' header.

    Returns:
        The authenticated User object with data from Firestore.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    user = await verify_id_token_and_get_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    FastAPI dependency that builds on `get_current_user` to also check
    if the user is active.

    Use this for endpoints that require an active, non-disabled user.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Role-based access control dependencies
async def get_current_manager_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    FastAPI dependency to ensure the user has manager-level access.
    Uses configurable ADMIN_ROLES set for flexibility.
    """
    if current_user.role not in ADMIN_ROLES:
        logger.warning(
            f"Access denied: user {current_user.uid} with role '{current_user.role}' "
            f"attempted to access manager-only resource"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {', '.join(sorted(ADMIN_ROLES))}",
        )
    return current_user


def require_role(allowed_roles: set[str]):
    """
    Dependency factory for requiring specific roles (configurable).

    Usage:
        @router.get("/admin")
        async def admin_page(user: User = Depends(require_role({"admin", "owner"}))):
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Role check failed: user {current_user.uid} role '{current_user.role}' "
                f"not in {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(sorted(allowed_roles))}",
            )
        return current_user
    return role_checker


def require_permission(permission: str):
    """
    Dependency factory for requiring specific permissions (OAuth2 Bearer token).
    This creates a dependency that can be used in API endpoint definitions.
    """

    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission}' required.",
            )
        return current_user

    return permission_checker


def require_permission_cookie(permission: str):
    """
    Dependency factory for requiring specific permissions (cookie-based).
    Use this for HTML page routes that require specific permissions.
    (Lesson #8: HTML pages must use cookie auth, not OAuth2 Bearer)
    """

    async def permission_checker(request: Request):
        user = await get_current_user_from_cookie(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        if user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        if not check_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission}' required.",
            )
        return user

    return permission_checker


# ==========================================
# TRIAL / SUBSCRIPTION ACCESS CHECKING
# ==========================================


async def get_subscription_status_for_user(user: User) -> Dict[str, Any]:
    """
    Get subscription/trial status for a user's organization.
    Returns status info including days remaining and access permissions.
    """
    if not user or not user.organization_id:
        # No organization - default to trial status
        return {
            "status": SubscriptionStatus.TRIAL,
            "has_access": True,
            "days_remaining": 30,
            "message": "Free trial",
        }

    subscription_service = get_subscription_service()
    return await subscription_service.get_subscription_status(user.organization_id)


async def check_trial_access(request: Request) -> Dict[str, Any]:
    """
    Check if the current user has access (trial or paid subscription).
    Returns subscription status dict - does NOT block access.
    Use require_active_subscription to block expired users.
    """
    user = await get_current_user_from_cookie(request)
    if not user:
        return {
            "status": SubscriptionStatus.TRIAL,
            "has_access": True,
            "days_remaining": 30,
            "message": "Free trial",
            "is_demo": True,
        }

    status_info = await get_subscription_status_for_user(user)
    status_info["is_demo"] = False
    return status_info


async def require_active_subscription(request: Request) -> User:
    """
    Dependency that requires both authentication AND active subscription/trial.
    Raises 403 if trial expired and no paid subscription.
    Use this for protected routes that should block expired users.
    """
    user = await get_current_user_from_cookie(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    status_info = await get_subscription_status_for_user(user)

    if not status_info.get("has_access", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your free trial has expired. Please upgrade to continue using ChatterFix.",
        )

    return user


def require_active_subscription_with_status():
    """
    Dependency factory that returns both user and subscription status.
    Use this when you need to show trial info on the page.
    """
    async def checker(request: Request) -> tuple[User, Dict[str, Any]]:
        user = await get_current_user_from_cookie(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        if user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")

        status_info = await get_subscription_status_for_user(user)

        if not status_info.get("has_access", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your free trial has expired. Please upgrade to continue using ChatterFix.",
            )

        return user, status_info

    return checker
