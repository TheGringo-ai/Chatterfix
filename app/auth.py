"""
Authentication module for FastAPI dependencies using Firebase.
Provides dependencies to protect endpoints and get the current authenticated user.
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User
from app.services.auth_service import verify_id_token_and_get_user, check_permission

# This tells FastAPI where the client can go to get a token.
# Since Firebase handles this on the client-side, this is mainly for documentation purposes.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

async def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme_optional)) -> Optional[User]:
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
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    FastAPI dependency that builds on `get_current_user` to also check
    if the user is active.

    Use this for endpoints that require an active, non-disabled user.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# You can also create dependencies for specific roles
async def get_current_manager_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    FastAPI dependency to ensure the user has the 'manager' role.
    """
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have the required 'manager' role.",
        )
    return current_user

def require_permission(permission: str):
    """
    Dependency factory for requiring specific permissions.
    This creates a dependency that can be used in endpoint definitions.
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission}' required."
            )
        return current_user
    return permission_checker