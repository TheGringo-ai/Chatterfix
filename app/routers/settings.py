"""
Settings Routes
User settings, API key management, and user administration
"""

from fastapi import APIRouter, Request, Form, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services import auth_service

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection
from typing import Optional

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


def get_current_user_from_session(session_token: Optional[str]):
    """Helper to get current user from session token"""
    if not session_token:
        return None
    return auth_service.validate_session(session_token)


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, session_token: Optional[str] = Cookie(None)):
    """User settings page"""
    user = get_current_user_from_session(session_token)

    if not user:
        return RedirectResponse(url="/auth/login")

    # Get user's API settings
    conn = get_db_connection()
    api_settings = conn.execute(
        """
        SELECT setting_key, setting_value
        FROM user_api_settings
        WHERE user_id = ?
    """,
        (user["id"],),
    ).fetchall()
    conn.close()

    settings_dict = {row["setting_key"]: row["setting_value"] for row in api_settings}

    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "api_settings": settings_dict},
    )


@router.post("/api-keys")
async def save_api_keys(
    gemini_api_key: str = Form(""),
    xai_api_key: str = Form(""),
    openai_api_key: str = Form(""),
    custom_endpoint: str = Form(""),
    session_token: Optional[str] = Cookie(None),
):
    """Save user's API keys"""
    user = get_current_user_from_session(session_token)

    if not user:
        return JSONResponse(
            {"success": False, "message": "Not authenticated"}, status_code=401
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    # Save API keys
    api_keys = {
        "gemini_api_key": gemini_api_key,
        "xai_api_key": xai_api_key,
        "openai_api_key": openai_api_key,
        "custom_endpoint": custom_endpoint,
    }

    for key, value in api_keys.items():
        if value:  # Only save non-empty values
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_api_settings (user_id, setting_key, setting_value, is_encrypted)
                VALUES (?, ?, ?, 1)
            """,
                (user["id"], key, value),
            )

    conn.commit()
    conn.close()

    return JSONResponse({"success": True, "message": "API keys saved successfully"})


@router.get("/users", response_class=HTMLResponse)
async def users_management(
    request: Request, session_token: Optional[str] = Cookie(None)
):
    """User management page (managers only)"""
    user = get_current_user_from_session(session_token)

    if not user or user["role"] != "manager":
        return RedirectResponse(url="/dashboard")

    # Get all users
    conn = get_db_connection()
    users = conn.execute(
        """
        SELECT id, username, email, full_name, role, status, is_active, created_date
        FROM users
        ORDER BY created_date DESC
    """
    ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "users_management.html", {"request": request, "user": user, "users": users}
    )


@router.post("/users/add")
async def add_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    role: str = Form("technician"),
    session_token: Optional[str] = Cookie(None),
):
    """Add a new user (managers only)"""
    user = get_current_user_from_session(session_token)

    if not user or user["role"] != "manager":
        return JSONResponse(
            {"success": False, "message": "Unauthorized"}, status_code=403
        )

    user_id = auth_service.create_user(username, email, password, full_name, role)

    if user_id:
        return JSONResponse(
            {
                "success": True,
                "message": "User created successfully",
                "user_id": user_id,
            }
        )
    else:
        return JSONResponse(
            {"success": False, "message": "Username or email already exists"},
            status_code=400,
        )


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: int, session_token: Optional[str] = Cookie(None)):
    """Toggle user active status (managers only)"""
    user = get_current_user_from_session(session_token)

    if not user or user["role"] != "manager":
        return JSONResponse(
            {"success": False, "message": "Unauthorized"}, status_code=403
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET is_active = NOT is_active
        WHERE id = ?
    """,
        (user_id,),
    )

    conn.commit()
    conn.close()

    return JSONResponse({"success": True, "message": "User status updated"})
