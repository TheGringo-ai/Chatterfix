"""
Authentication module - wrapper for utils.auth
Provides authentication utilities for the ChatterFix CMMS application
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie

from app.services.auth_service import validate_session

# Authentication function for FastAPI dependencies
def get_current_user(session_token: Optional[str] = Cookie(None)):
    """
    Get current user from session token
    
    Args:
        session_token: Session token from cookie
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: If not authenticated
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = validate_session(session_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error and return proper authentication failure
        import logging
        logging.getLogger(__name__).error(f"Session validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Export the main functions that other modules expect
__all__ = ['get_current_user']