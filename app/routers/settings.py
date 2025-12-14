"""
Settings Routes
User settings, API key management, and user administration
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_active_user, require_permission
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """User settings page"""
    if not current_user:
        return RedirectResponse(url="/auth/login")

    # TODO: Migrate user_api_settings to Firestore, keyed by user.uid
    # For now, returning mock data.
    settings_dict = {
        "gemini_api_key": "********",
        "xai_api_key": "********",
        "openai_api_key": "********",
        "custom_endpoint": "",
    }

    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": current_user, "api_settings": settings_dict},
    )


@router.post("/api-keys")
async def save_api_keys(
    gemini_api_key: str = Form(""),
    xai_api_key: str = Form(""),
    openai_api_key: str = Form(""),
    custom_endpoint: str = Form(""),
    current_user: User = Depends(get_current_active_user),
):
    """Save user's API keys"""
    # TODO: Migrate this to save settings in a 'user_settings' collection in Firestore
    # keyed by current_user.uid.
    
    print(f"Saving API keys for user {current_user.uid}")
    print(f"GEMINI Key length: {len(gemini_api_key)}")

    return JSONResponse({"success": True, "message": "API keys saved successfully (MOCK)"})


@router.get("/users", response_class=HTMLResponse)
async def users_management(
    request: Request, current_user: User = Depends(require_permission("manager"))
):
    """User management page (managers only)"""
    # TODO: Migrate this to fetch all users from a 'users' collection in Firestore.
    users = [
        {"id": "uid-1", "username": "demo_user", "email": "user@demo.com", "full_name": "Demo User", "role": "technician", "status": "active", "is_active": True, "created_date": "2024-01-01"},
        {"id": "uid-2", "username": "manager_user", "email": "manager@demo.com", "full_name": "Manager User", "role": "manager", "status": "active", "is_active": True, "created_date": "2024-01-01"},
    ]
    
    return templates.TemplateResponse(
        "users_management.html", {"request": request, "user": current_user, "users": users}
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
            {"success": False, "message": "User creation from here is disabled for security. Please use the Firebase Console."},
            status_code=403,
        )


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: str, current_user: User = Depends(require_permission("manager"))):
    """Toggle user active status (managers only)"""
    # TODO: Migrate this to update the 'disabled' field on a user document in Firestore.
    # You would also use the Firebase Admin SDK to disable the user in Firebase Auth itself.
    # auth.update_user(user_id, disabled=True/False)
    
    print(f"Toggling active status for user {user_id} by manager {current_user.uid}")

    return JSONResponse({"success": True, "message": "User status updated (MOCK)"})
