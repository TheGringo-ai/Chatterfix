"""
Team Collaboration Router
Shows demo data for guests, real Firestore data for authenticated users
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_optional_current_user, get_current_user_from_cookie
from app.models.user import User
from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team", tags=["team"])
templates = Jinja2Templates(directory="app/templates")

# Demo data for unauthenticated users
DEMO_TEAM = [
    {
        "id": "demo_1",
        "full_name": "Mike Johnson",
        "username": "mike.johnson@demo.com",
        "role": "Senior Technician",
        "department": "Maintenance",
        "skills": ["HVAC", "Electrical", "Plumbing"],
        "certifications": ["EPA 608", "OSHA 30", "First Aid/CPR"],
        "active_work_orders": 3,
        "completed_orders": 47,
        "status": "Available",
        "contact": "mike.johnson@demo.com",
        "phone": "(555) 123-4567",
        "start_date": "2021-03-15",
        "employee_id": "EMP-001",
        "shift": "Day Shift (7am-3pm)",
        "supervisor": "Sarah Chen",
        "notes": "Excellent troubleshooting skills. Lead tech for HVAC systems.",
    },
    {
        "id": "demo_2",
        "full_name": "Sarah Chen",
        "username": "sarah.chen@demo.com",
        "role": "Maintenance Manager",
        "department": "Operations",
        "skills": ["Project Management", "Mechanical", "Safety", "Team Leadership"],
        "certifications": ["PMP", "CMRP", "OSHA 30", "Six Sigma Green Belt"],
        "active_work_orders": 5,
        "completed_orders": 128,
        "status": "Busy",
        "contact": "sarah.chen@demo.com",
        "phone": "(555) 234-5678",
        "start_date": "2018-06-01",
        "employee_id": "EMP-002",
        "shift": "Day Shift (7am-3pm)",
        "supervisor": "Director of Operations",
        "notes": "Department head. Responsible for all maintenance operations.",
    },
    {
        "id": "demo_3",
        "full_name": "Alex Rodriguez",
        "username": "alex.rodriguez@demo.com",
        "role": "Maintenance Technician",
        "department": "Maintenance",
        "skills": ["Mechanical", "Pneumatics", "Preventive Maintenance"],
        "certifications": ["OSHA 10", "Forklift Operator"],
        "active_work_orders": 2,
        "completed_orders": 23,
        "status": "Available",
        "contact": "alex.rodriguez@demo.com",
        "phone": "(555) 345-6789",
        "start_date": "2023-01-10",
        "employee_id": "EMP-003",
        "shift": "Swing Shift (3pm-11pm)",
        "supervisor": "Mike Johnson",
        "notes": "New hire showing great progress. Strong mechanical aptitude.",
    },
]


# ========== TEAM ROUTES ==========


@router.get("/", response_class=HTMLResponse)
async def team_dashboard(request: Request):
    """Team dashboard - shows real data for authenticated, demo data for guests"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    is_demo = False
    team_members = []

    logger.info(f"Team dashboard: current_user={current_user is not None}, org_id={current_user.organization_id if current_user else None}")

    if current_user:
        # User is authenticated - NOT demo mode
        is_demo = False
        firestore_manager = get_firestore_manager()

        if current_user.organization_id:
            # Has organization - show team from that org
            try:
                team_members = await firestore_manager.get_collection(
                    "users",
                    filters=[
                        {
                            "field": "organization_id",
                            "operator": "==",
                            "value": current_user.organization_id,
                        }
                    ],
                )
                logger.info(f"Loaded {len(team_members)} team members for org {current_user.organization_id}")
            except Exception as e:
                logger.error(f"Error loading team: {e}")
                # Show user's own profile as fallback
                team_members = [{
                    "id": current_user.uid,
                    "full_name": current_user.full_name or current_user.email,
                    "username": current_user.email,
                    "role": current_user.role,
                    "status": "Available",
                    "skills": [],
                    "certifications": [],
                }]
        else:
            # Authenticated but no org - show user's own profile
            logger.info(f"User {current_user.uid} has no organization_id - showing own profile")
            team_members = [{
                "id": current_user.uid,
                "full_name": current_user.full_name or current_user.email,
                "username": current_user.email,
                "role": current_user.role,
                "status": "Available",
                "skills": [],
                "certifications": [],
            }]
    else:
        # Not authenticated - show demo data
        logger.info("No authenticated user - showing demo data")
        team_members = DEMO_TEAM
        is_demo = True

    response = templates.TemplateResponse(
        "team_dashboard.html",
        {
            "request": request,
            "users": team_members,
            "team_members": team_members,
            "messages": [],
            "online_users": [],
            "current_user": current_user,
            "user": current_user,
            "is_demo": is_demo,
        },
    )
    # Force no caching to ensure users see latest version
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/users", response_class=JSONResponse)
async def get_users(current_user: Optional[User] = Depends(get_optional_current_user)):
    """Get users - org-scoped for authenticated, demo data for guests"""
    if not current_user or not current_user.organization_id:
        # Return demo data for unauthenticated users
        return JSONResponse({"users": DEMO_TEAM, "is_demo": True})

    firestore_manager = get_firestore_manager()
    users = []
    try:
        users = await firestore_manager.get_collection(
            "users",
            filters=[
                {
                    "field": "organization_id",
                    "operator": "==",
                    "value": current_user.organization_id,
                }
            ],
        )
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        # Fall back to demo data on error
        return JSONResponse({"users": DEMO_TEAM, "is_demo": True})

    return JSONResponse({"users": users, "is_demo": False})


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_profile(request: Request, user_id: str):
    """User profile - redirect back to team page"""
    # Always redirect to team page for now (profile details shown in modal)
    return RedirectResponse(url="/team", status_code=302)


@router.get("/messages", response_class=JSONResponse)
async def get_messages(
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get messages - empty for guests, real data for authenticated"""
    if not current_user:
        return JSONResponse({"messages": [], "is_demo": True})
    return JSONResponse({"messages": [], "is_demo": False})


@router.get("/notifications", response_class=JSONResponse)
async def get_notifications(
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get notifications - empty for guests, real data for authenticated"""
    if not current_user:
        return JSONResponse({"notifications": [], "is_demo": True})
    return JSONResponse({"notifications": [], "is_demo": False})


# ========== FIRESTORE-BASED MESSAGING ==========

from pydantic import BaseModel
from datetime import datetime, timezone


class SendMessageRequest(BaseModel):
    """Request model for sending a message"""
    message: str
    recipient_id: Optional[str] = None  # None = broadcast to team
    priority: str = "normal"  # normal, high, urgent


@router.post("/messages", response_class=JSONResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Send a message to team or specific user"""
    if not current_user:
        return JSONResponse({"success": False, "error": "Not authenticated"}, status_code=401)

    firestore_manager = get_firestore_manager()

    try:
        # Create message document
        message_data = {
            "sender_id": current_user.id,
            "sender_name": current_user.full_name or current_user.email,
            "recipient_id": request.recipient_id,
            "recipient_name": None,  # Will be populated if specific recipient
            "message": request.message,
            "priority": request.priority,
            "organization_id": current_user.organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
        }

        # Get recipient name if specified
        if request.recipient_id:
            try:
                recipient = await firestore_manager.get_document("users", request.recipient_id)
                if recipient:
                    message_data["recipient_name"] = recipient.get("full_name") or recipient.get("email")
            except Exception:
                pass

        # Save to Firestore
        doc_id = await firestore_manager.create_document("team_messages", message_data)

        return JSONResponse({
            "success": True,
            "message_id": doc_id,
            "message": "Message sent successfully"
        })

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/messages/recent", response_class=JSONResponse)
async def get_recent_messages(
    limit: int = 50,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get recent messages for the team"""
    if not current_user:
        return JSONResponse({"success": False, "error": "Not authenticated"}, status_code=401)

    firestore_manager = get_firestore_manager()

    try:
        # Get messages for this organization
        messages = await firestore_manager.get_collection(
            "team_messages",
            filters=[
                {
                    "field": "organization_id",
                    "operator": "==",
                    "value": current_user.organization_id,
                }
            ],
            order_by="created_at",
            order_direction="desc",
            limit=limit,
        )

        return JSONResponse({
            "success": True,
            "messages": messages,
            "count": len(messages)
        })

    except Exception as e:
        logger.error(f"Error loading messages: {e}")
        return JSONResponse({"success": False, "error": str(e), "messages": []}, status_code=500)


@router.post("/messages/{message_id}/read", response_class=JSONResponse)
async def mark_message_read(
    message_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Mark a message as read"""
    if not current_user:
        return JSONResponse({"success": False, "error": "Not authenticated"}, status_code=401)

    firestore_manager = get_firestore_manager()

    try:
        await firestore_manager.update_document(
            "team_messages",
            message_id,
            {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}
        )
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error marking message read: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
