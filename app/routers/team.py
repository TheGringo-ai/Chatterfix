"""
Team Collaboration Router
Redirects to demo team routes since app uses Firestore-only architecture
"""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team", tags=["team"])

# ========== TEAM REDIRECTS ==========


@router.get("/", response_class=HTMLResponse)
async def team_dashboard(request: Request):
    """Team dashboard - redirect to demo team which works with Firestore"""
    return RedirectResponse(url="/demo/team", status_code=302)


@router.get("/users", response_class=JSONResponse)
async def get_users():
    """Get users - redirect to demo implementation"""
    return RedirectResponse(url="/demo/team", status_code=302)


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_profile(request: Request, user_id: int):
    """User profile - redirect to demo team"""
    return RedirectResponse(url="/demo/team", status_code=302)


@router.get("/messages", response_class=JSONResponse)
async def get_messages():
    """Get messages - redirect to demo team"""
    return RedirectResponse(url="/demo/team", status_code=302)


@router.get("/notifications", response_class=JSONResponse)
async def get_notifications():
    """Get notifications - redirect to demo team"""
    return RedirectResponse(url="/demo/team", status_code=302)


# Note: WebSocket and POST endpoints removed since they require SQL database
# For full functionality, implement Firestore-compatible versions
