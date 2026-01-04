"""
Organization Management Routes
Handles team management, invites, and organization settings
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr

from app.auth import get_current_active_user, require_permission, require_permission_cookie, get_current_user_from_cookie, require_auth_cookie
from app.models.user import User
from app.services.auth_service import check_permission
from app.services.organization_service import get_organization_service
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organization", tags=["organization"])
templates = Jinja2Templates(directory="app/templates")


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "technician"


class UpdateMemberRoleRequest(BaseModel):
    role: str


class UpdateOrganizationRequest(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    phone: Optional[str] = None


# ==========================================
# ORGANIZATION INFO
# ==========================================


@router.get("", response_class=JSONResponse)
async def get_organization(current_user: User = Depends(require_auth_cookie)):
    """Get current user's organization details"""
    org_service = get_organization_service()

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    org = await org_service.get_organization(current_user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "success": True,
        "organization": {
            "id": org.get("id"),
            "name": org.get("name"),
            "industry": org.get("industry"),
            "size": org.get("size"),
            "status": org.get("status"),
            "member_count": org.get("member_count", 1),
            "subscription": org.get("subscription", {}),
            "settings": org.get("settings", {}),
        },
    }


@router.put("", response_class=JSONResponse)
async def update_organization(
    update_data: UpdateOrganizationRequest,
    current_user: User = Depends(require_permission_cookie("manage_organization")),
):
    """Update organization settings (owner/admin only)"""
    org_service = get_organization_service()

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    update_dict = update_data.dict(exclude_none=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")

    success = await org_service.update_organization(
        current_user.organization_id, update_dict
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update organization")

    return {"success": True, "message": "Organization updated successfully"}


# ==========================================
# SUBSCRIPTION STATUS
# ==========================================


@router.get("/subscription", response_class=JSONResponse)
async def get_subscription_status(current_user: User = Depends(require_auth_cookie)):
    """Get organization's subscription/trial status"""
    from app.services.subscription_service import get_subscription_service

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    subscription_service = get_subscription_service()
    status = await subscription_service.get_subscription_status(current_user.organization_id)

    return {
        "success": True,
        "subscription": status,
    }


# ==========================================
# TEAM MANAGEMENT
# ==========================================


@router.get("/team", response_class=JSONResponse)
async def get_team_members(current_user: User = Depends(require_auth_cookie)):
    """Get all team members in the organization"""
    org_service = get_organization_service()

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    members = await org_service.get_organization_members(current_user.organization_id)

    return {"success": True, "members": members, "total": len(members)}


@router.post("/team/invite", response_class=JSONResponse)
async def invite_team_member(
    invite_data: InviteMemberRequest,
    current_user: User = Depends(require_permission_cookie("manage_team")),
):
    """Invite a new team member to the organization"""
    org_service = get_organization_service()

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    # Validate role
    valid_roles = ["owner", "manager", "supervisor", "technician", "requestor"]
    if invite_data.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )

    try:
        # Create invite
        invite_code = await org_service.create_invite(
            org_id=current_user.organization_id,
            email=invite_data.email,
            role=invite_data.role,
            invited_by=current_user.uid,
        )

        # Get organization name for email
        org = await org_service.get_organization(current_user.organization_id)
        org_name = (
            org.get("name", "ChatterFix Organization")
            if org
            else "ChatterFix Organization"
        )

        # Send invite email
        try:
            await email_service.send_team_invite_email(
                to_email=invite_data.email,
                organization_name=org_name,
                inviter_name=current_user.full_name or current_user.email,
                role=invite_data.role,
                invite_code=invite_code,
            )
        except Exception as email_error:
            logger.warning(f"Failed to send invite email: {email_error}")
            # Don't fail the invite if email fails

        logger.info(
            f"Invited {invite_data.email} to org {current_user.organization_id} as {invite_data.role}"
        )

        return {
            "success": True,
            "message": f"Invitation sent to {invite_data.email}",
            "invite_code": invite_code,
        }

    except Exception as e:
        logger.error(f"Error creating invite: {e}")
        raise HTTPException(status_code=500, detail="Failed to create invitation")


@router.get("/team/invites", response_class=JSONResponse)
async def get_pending_invites(
    current_user: User = Depends(require_permission_cookie("manage_team")),
):
    """Get all pending invitations for the organization"""
    org_service = get_organization_service()

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    invites = await org_service.get_pending_invites(current_user.organization_id)

    return {"success": True, "invites": invites, "total": len(invites)}


class UpdateTeamMemberRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    skills: Optional[list] = None
    certifications: Optional[list] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.put("/team/{user_id}", response_class=JSONResponse)
async def update_team_member(
    request: Request,
    user_id: str,
    update_data: UpdateTeamMemberRequest,
):
    """Update a team member's information"""
    # Use cookie-based auth for browser JavaScript calls (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not check_permission(current_user, "manage_team"):
        raise HTTPException(status_code=403, detail="Permission denied: 'manage_team' required")

    org_service = get_organization_service()

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    # Verify user belongs to same organization
    from app.core.firestore_db import get_firestore_manager
    firestore_manager = get_firestore_manager()

    try:
        user_doc = await firestore_manager.get_document("users", user_id)
        if not user_doc or user_doc.get("organization_id") != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Team member not found")

        # Update user document
        update_dict = update_data.dict(exclude_none=True)
        if update_dict:
            await firestore_manager.update_document("users", user_id, update_dict)

        return {"success": True, "message": "Team member updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team member: {e}")
        raise HTTPException(status_code=500, detail="Failed to update team member")


@router.delete("/team/{user_id}", response_class=JSONResponse)
async def remove_team_member(
    request: Request,
    user_id: str,
):
    """Remove a team member from the organization"""
    # Use cookie-based auth for browser JavaScript calls (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not check_permission(current_user, "manage_team"):
        raise HTTPException(status_code=403, detail="Permission denied: 'manage_team' required")

    org_service = get_organization_service()

    if not current_user.organization_id:
        raise HTTPException(
            status_code=404, detail="No organization associated with this account"
        )

    # Can't remove yourself
    if user_id == current_user.uid:
        raise HTTPException(
            status_code=400, detail="You cannot remove yourself from the organization"
        )

    success = await org_service.remove_member(current_user.organization_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove team member")

    return {"success": True, "message": "Team member removed successfully"}


# ==========================================
# INVITE ACCEPTANCE (Public endpoint)
# ==========================================


@router.get("/invite/{invite_code}", response_class=HTMLResponse)
async def view_invite(request: Request, invite_code: str):
    """View an organization invite (public page)"""
    org_service = get_organization_service()

    # Get invite details
    if org_service.db:
        invite_ref = org_service.db.collection("organization_invites").document(
            invite_code
        )
        invite_doc = invite_ref.get()

        if invite_doc.exists:
            invite = invite_doc.to_dict()
            if invite.get("status") == "pending":
                return templates.TemplateResponse(
                    "organization/accept_invite.html",
                    {
                        "request": request,
                        "invite": invite,
                        "invite_code": invite_code,
                        "organization_name": invite.get(
                            "organization_name", "An organization"
                        ),
                    },
                )

    # Invalid or expired invite
    return templates.TemplateResponse(
        "organization/invalid_invite.html", {"request": request}
    )


@router.post("/invite/{invite_code}/accept", response_class=JSONResponse)
async def accept_invite(
    invite_code: str, current_user: User = Depends(get_current_active_user)
):
    """Accept an organization invitation"""
    org_service = get_organization_service()

    # Check if user already has an organization
    if current_user.organization_id:
        raise HTTPException(
            status_code=400,
            detail="You are already a member of an organization. Leave your current organization first.",
        )

    org_id = await org_service.accept_invite(invite_code, current_user.uid)
    if not org_id:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")

    return {
        "success": True,
        "message": "You have joined the organization!",
        "organization_id": org_id,
    }


# ==========================================
# API ENDPOINTS FOR FRONTEND
# ==========================================


@router.get("/api/info", response_class=JSONResponse)
async def api_get_organization_info(
    current_user: User = Depends(get_current_active_user),
):
    """API endpoint to get organization info for frontend"""
    org_service = get_organization_service()

    if not current_user.organization_id:
        return {"has_organization": False, "organization": None}

    org = await org_service.get_organization(current_user.organization_id)

    return {
        "has_organization": True,
        "organization": (
            {
                "id": org.get("id") if org else None,
                "name": org.get("name") if org else None,
                "role": current_user.role,
            }
            if org
            else None
        ),
    }
