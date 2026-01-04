"""
Settings Routes
User settings, organization settings, security, and administration
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_active_user, get_optional_current_user, require_permission, require_permission_cookie, get_current_user_from_cookie
from app.models.user import User
from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


# ============ Pydantic Models ============

class OrganizationSettings(BaseModel):
    """Organization-level settings"""
    name: Optional[str] = None
    industry: Optional[str] = None
    timezone: Optional[str] = "America/New_York"
    date_format: Optional[str] = "MM/DD/YYYY"


class SecuritySettings(BaseModel):
    """Security and access control settings"""
    protect_manager_dashboard: bool = False  # Default: open access
    require_login_all: bool = False
    session_timeout: int = 60  # minutes
    require_2fa: bool = False


# ============ Helper Functions ============

async def get_org_settings(org_id: str = "default") -> dict:
    """Get organization settings from Firestore"""
    try:
        firestore = get_firestore_manager()
        settings = await firestore.get_document("organization_settings", org_id)
        # Return empty dict if document doesn't exist
        return settings if settings else {}
    except Exception as e:
        logger.warning(f"Could not fetch org settings: {e}")
        return {}


async def get_security_settings(org_id: str = "default") -> dict:
    """Get security settings - used by other routers to check access"""
    try:
        firestore = get_firestore_manager()
        settings = await firestore.get_document("organization_settings", org_id)
        # Handle None case when document doesn't exist
        if not settings:
            settings = {}
        return {
            "protect_manager_dashboard": settings.get("protect_manager_dashboard", False),
            "require_login_all": settings.get("require_login_all", False),
            "session_timeout": settings.get("session_timeout", 60),
            "require_2fa": settings.get("require_2fa", False),
        }
    except Exception as e:
        logger.warning(f"Could not fetch security settings: {e}")
        return {"protect_manager_dashboard": False, "require_login_all": False}


def mask_api_key(key: str) -> str:
    """Mask API key for display, showing only last 4 chars"""
    if not key or len(key) < 8:
        return "********"
    return "********" + key[-4:]


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request):
    """User settings page - accessible to anyone, some features require auth"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)

    # Fetch organization settings
    org_id = current_user.organization_id if current_user else "default"
    org_settings = await get_org_settings(org_id)

    # Fetch user API settings if logged in
    api_settings = {
        "gemini_api_key": "",
        "xai_api_key": "",
        "openai_api_key": "",
        "custom_endpoint": "",
    }

    if current_user:
        try:
            firestore = get_firestore_manager()
            user_settings = await firestore.get_document("user_settings", current_user.uid)
            if user_settings:
                api_settings = {
                    "gemini_api_key": mask_api_key(user_settings.get("gemini_api_key", "")),
                    "xai_api_key": mask_api_key(user_settings.get("xai_api_key", "")),
                    "openai_api_key": mask_api_key(user_settings.get("openai_api_key", "")),
                    "custom_endpoint": user_settings.get("custom_endpoint", ""),
                }
        except Exception as e:
            logger.warning(f"Could not fetch user settings: {e}")

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": current_user,
            "api_settings": api_settings,
            "org_settings": org_settings,
        },
    )


@router.post("/organization")
async def save_organization_settings(
    settings: OrganizationSettings,
    current_user: User = Depends(get_optional_current_user),
):
    """Save organization settings"""
    try:
        firestore = get_firestore_manager()
        org_id = current_user.organization_id if current_user else "default"

        settings_data = {
            "name": settings.name,
            "industry": settings.industry,
            "timezone": settings.timezone,
            "date_format": settings.date_format,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.uid if current_user else "anonymous",
        }

        # Merge with existing settings
        existing = await firestore.get_document("organization_settings", org_id) or {}
        existing.update(settings_data)

        await firestore.set_document("organization_settings", org_id, existing)
        logger.info(f"Organization settings saved for {org_id}")

        return JSONResponse({"success": True, "message": "Organization settings saved!"})

    except Exception as e:
        logger.error(f"Failed to save organization settings: {e}")
        return JSONResponse(
            {"success": False, "message": f"Failed to save: {str(e)}"}, status_code=500
        )


@router.post("/security")
async def save_security_settings(
    settings: SecuritySettings,
    current_user: User = Depends(get_optional_current_user),
):
    """Save security settings"""
    try:
        firestore = get_firestore_manager()
        org_id = current_user.organization_id if current_user else "default"

        settings_data = {
            "protect_manager_dashboard": settings.protect_manager_dashboard,
            "require_login_all": settings.require_login_all,
            "session_timeout": settings.session_timeout,
            "require_2fa": settings.require_2fa,
            "security_updated_at": datetime.now(timezone.utc).isoformat(),
            "security_updated_by": current_user.uid if current_user else "anonymous",
        }

        # Merge with existing settings
        existing = await firestore.get_document("organization_settings", org_id) or {}
        existing.update(settings_data)

        await firestore.set_document("organization_settings", org_id, existing)
        logger.info(f"Security settings saved for {org_id}")

        return JSONResponse({"success": True, "message": "Security settings saved!"})

    except Exception as e:
        logger.error(f"Failed to save security settings: {e}")
        return JSONResponse(
            {"success": False, "message": f"Failed to save: {str(e)}"}, status_code=500
        )


@router.get("/security/check")
async def check_security_settings(org_id: str = "default"):
    """Public endpoint to check security settings - used by other routers"""
    settings = await get_security_settings(org_id)
    return JSONResponse(settings)


@router.post("/api-keys")
async def save_api_keys(
    gemini_api_key: str = Form(""),
    xai_api_key: str = Form(""),
    openai_api_key: str = Form(""),
    custom_endpoint: str = Form(""),
    current_user: User = Depends(get_current_active_user),
):
    """Save user's API keys to Firestore"""
    try:
        firestore = get_firestore_manager()

        # Get existing settings to preserve keys that weren't changed
        existing_settings = (
            await firestore.get_document("user_settings", current_user.uid) or {}
        )

        # Only update keys that were actually provided (not masked placeholders)
        settings_data = {
            "user_id": current_user.uid,
            "custom_endpoint": custom_endpoint,
            "updated_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        }

        # Only update API keys if new values provided (not masked)
        if gemini_api_key and not gemini_api_key.startswith("********"):
            settings_data["gemini_api_key"] = gemini_api_key
        elif existing_settings.get("gemini_api_key"):
            settings_data["gemini_api_key"] = existing_settings["gemini_api_key"]

        if xai_api_key and not xai_api_key.startswith("********"):
            settings_data["xai_api_key"] = xai_api_key
        elif existing_settings.get("xai_api_key"):
            settings_data["xai_api_key"] = existing_settings["xai_api_key"]

        if openai_api_key and not openai_api_key.startswith("********"):
            settings_data["openai_api_key"] = openai_api_key
        elif existing_settings.get("openai_api_key"):
            settings_data["openai_api_key"] = existing_settings["openai_api_key"]

        # Save to Firestore
        await firestore.set_document("user_settings", current_user.uid, settings_data)
        logger.info(f"API keys saved for user {current_user.uid}")

        return JSONResponse({"success": True, "message": "API keys saved successfully"})

    except Exception as e:
        logger.error(f"Failed to save API keys: {e}")
        return JSONResponse(
            {"success": False, "message": f"Failed to save: {str(e)}"}, status_code=500
        )


@router.get("/users", response_class=HTMLResponse)
async def users_management(
    request: Request, current_user: User = Depends(require_permission_cookie("manager"))
):
    """User management page (managers only) - uses cookie auth for HTML pages"""
    users = []

    try:
        firestore = get_firestore_manager()
        # Fetch users from Firestore 'users' collection
        users_data = await firestore.get_collection("users", order_by="created_at")

        for user in users_data:
            # Handle datetime serialization
            created_at = user.get("created_at", "")
            if hasattr(created_at, "strftime"):
                created_at = created_at.strftime("%Y-%m-%d")

            users.append(
                {
                    "id": user.get("uid", user.get("id", "")),
                    "username": user.get("username", user.get("email", "")),
                    "email": user.get("email", ""),
                    "full_name": user.get("full_name", user.get("display_name", "")),
                    "role": user.get("role", "technician"),
                    "status": "active" if user.get("is_active", True) else "disabled",
                    "is_active": user.get("is_active", True),
                    "created_date": created_at,
                }
            )
    except Exception as e:
        logger.warning(f"Could not fetch users from Firestore: {e}")
        # Fallback to demo data if Firestore fails
        users = [
            {
                "id": "demo-1",
                "username": "demo_user",
                "email": "user@demo.com",
                "full_name": "Demo User",
                "role": "technician",
                "status": "active",
                "is_active": True,
                "created_date": "2024-01-01",
            },
        ]

    return templates.TemplateResponse(
        "users_management.html",
        {"request": request, "user": current_user, "users": users},
    )


@router.post("/users/add")
async def add_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    role: str = Form("technician"),
    current_user: User = Depends(require_permission("manager")),
):
    """Add a new user (managers only)"""
    # This functionality should be handled via the Firebase Console or a dedicated admin SDK script.
    # Creating users with passwords from the backend is insecure and not the standard Firebase flow.
    # The client (e.g., a frontend admin panel) should use the Firebase JS SDK to create users.
    # A profile document can then be created in Firestore.
    return JSONResponse(
        {
            "success": False,
            "message": "User creation from here is disabled for security. Please use the Firebase Console.",
        },
        status_code=403,
    )


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str, current_user: User = Depends(require_permission("manager"))
):
    """Toggle user active status (managers only)"""
    try:
        firestore = get_firestore_manager()

        # Get current user status
        user_doc = await firestore.get_document("users", user_id)
        if not user_doc:
            return JSONResponse(
                {"success": False, "message": "User not found"}, status_code=404
            )

        # Toggle the is_active status
        new_status = not user_doc.get("is_active", True)

        # Update in Firestore
        await firestore.update_document(
            "users",
            user_id,
            {
                "is_active": new_status,
                "updated_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
                "updated_by": current_user.uid,
            },
        )

        logger.info(
            f"User {user_id} status toggled to {new_status} by manager {current_user.uid}"
        )

        return JSONResponse(
            {
                "success": True,
                "message": f"User {'activated' if new_status else 'deactivated'} successfully",
                "is_active": new_status,
            }
        )

    except Exception as e:
        logger.error(f"Failed to toggle user status: {e}")
        return JSONResponse(
            {"success": False, "message": f"Failed to update: {str(e)}"},
            status_code=500,
        )
