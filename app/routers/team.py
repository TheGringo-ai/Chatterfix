"""
Team Collaboration Router
Routes authenticated users to org-scoped team data, demo users to demo team
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_optional_current_user
from app.models.user import User
from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team", tags=["team"])
templates = Jinja2Templates(directory="app/templates")

# ========== TEAM ROUTES ==========


@router.get("/", response_class=HTMLResponse)
async def team_dashboard(request: Request, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Team dashboard - shows org team data for authenticated users, demo for others"""
    if not current_user:
        # Redirect unauthenticated users to demo
        return RedirectResponse(url="/demo/team", status_code=302)

    # Authenticated user - show their org's team data
    firestore_manager = get_firestore_manager()
    team_members = []

    if current_user.organization_id:
        try:
            # Get team members from organization
            team_members = await firestore_manager.get_collection(
                "users",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}]
            )
        except Exception as e:
            logger.error(f"Error loading team: {e}")

    return templates.TemplateResponse(
        "team_dashboard.html",
        {"request": request, "team_members": team_members, "current_user": current_user, "is_demo": False}
    )


@router.get("/users", response_class=JSONResponse)
async def get_users(current_user: Optional[User] = Depends(get_optional_current_user)):
    """Get users - org-scoped for authenticated, redirect demo"""
    if not current_user:
        return RedirectResponse(url="/demo/team", status_code=302)

    firestore_manager = get_firestore_manager()
    users = []
    if current_user.organization_id:
        try:
            users = await firestore_manager.get_collection(
                "users",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}]
            )
        except Exception as e:
            logger.error(f"Error loading users: {e}")

    return JSONResponse({"users": users})


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_profile(request: Request, user_id: str, current_user: Optional[User] = Depends(get_optional_current_user)):
    """User profile - redirect to demo team for now"""
    if not current_user:
        return RedirectResponse(url="/demo/team", status_code=302)
    return RedirectResponse(url="/team", status_code=302)


@router.get("/messages", response_class=JSONResponse)
async def get_messages(current_user: Optional[User] = Depends(get_optional_current_user)):
    """Get messages - redirect to demo team for unauthenticated"""
    if not current_user:
        return RedirectResponse(url="/demo/team", status_code=302)
    return JSONResponse({"messages": []})


@router.get("/notifications", response_class=JSONResponse)
async def get_notifications(current_user: Optional[User] = Depends(get_optional_current_user)):
    """Get notifications - redirect to demo team for unauthenticated"""
    if not current_user:
        return RedirectResponse(url="/demo/team", status_code=302)
    return JSONResponse({"notifications": []})


# Note: WebSocket and POST endpoints removed since they require SQL database
# For full functionality, implement Firestore-compatible versions
