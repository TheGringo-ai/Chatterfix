"""
Authentication Routes
Login, logout, and user authentication endpoints
"""

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services import auth_service
from app.services.firebase_auth import (
    firebase_auth_service,
)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    request: Request = None,
):
    """User login endpoint"""
    # Try Firebase authentication first
    if firebase_auth_service.is_available:
        try:
            # Sign in with Firebase
            auth_result = await firebase_auth_service.sign_in_with_email_password(
                username, password
            )
            token = auth_result["idToken"]

            # Set cookie
            response = RedirectResponse(url="/dashboard", status_code=302)
            response.set_cookie(
                key="session_token",
                value=token,
                httponly=True,
                max_age=86400,  # 24 hours
                samesite="lax",
            )
            return response
        except Exception:
            # If Firebase login fails, fall through to try local DB (legacy/backup)
            pass

    # Authenticate user (Local SQL fallback)
    user = auth_service.authenticate_user(username, password)

    if not user:
        return JSONResponse(
            {"success": False, "message": "Invalid username or password"},
            status_code=401,
        )

    # Create session
    ip_address = request.client.host if (request and request.client) else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    token = auth_service.create_session(user["id"], ip_address, user_agent)

    # Set cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax",
    )

    return response


@router.post("/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    """User logout endpoint"""
    if session_token:
        auth_service.invalidate_session(session_token)

    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("session_token")
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/me")
async def get_current_user(session_token: Optional[str] = Cookie(None)):
    """Get current logged-in user"""
    if not session_token:
        return JSONResponse({"authenticated": False}, status_code=401)

    # Try validating as Firebase token first
    try:
        user_data = await firebase_auth_service.verify_token(session_token)
        return JSONResponse(
            {
                "authenticated": True,
                "user": {
                    "id": user_data["uid"],
                    "username": user_data["email"],
                    "email": user_data["email"],
                    "full_name": user_data["name"] or user_data["email"],
                    "role": user_data["user_data"].get(
                        "role", "technician"
                    ),  # Get role from Firestore
                },
            }
        )
    except Exception:
        # Fallback to local SQL session validation
        pass

    user = auth_service.validate_session(session_token)

    if not user:
        return JSONResponse({"authenticated": False}, status_code=401)

    return JSONResponse(
        {
            "authenticated": True,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
            },
        }
    )


@router.post("/change-password")
async def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    session_token: Optional[str] = Cookie(None),
):
    """Change user password"""
    if not session_token:
        return JSONResponse(
            {"success": False, "message": "Not authenticated"}, status_code=401
        )

    user = auth_service.validate_session(session_token)
    if not user:
        return JSONResponse(
            {"success": False, "message": "Invalid session"}, status_code=401
        )

    success = auth_service.change_password(user["id"], old_password, new_password)

    if success:
        return JSONResponse(
            {"success": True, "message": "Password changed successfully"}
        )
    else:
        return JSONResponse(
            {"success": False, "message": "Invalid old password"}, status_code=400
        )


# ===== FIREBASE AUTHENTICATION ENDPOINTS =====


@router.post("/firebase/verify")
async def verify_firebase_token(token: str = Form(...), request: Request = None):
    """Verify Firebase ID token and create session"""
    try:
        # Verify the Firebase token
        user_data = await firebase_auth_service.verify_token(token)

        return JSONResponse(
            {
                "success": True,
                "user": {
                    "uid": user_data["uid"],
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "verified": user_data["verified"],
                    "role": user_data["user_data"].get("role", "technician"),
                },
            }
        )

    except HTTPException as e:
        return JSONResponse(
            {"success": False, "message": str(e.detail)}, status_code=e.status_code
        )
    except Exception:
        return JSONResponse(
            {"success": False, "message": "Authentication failed"}, status_code=401
        )


@router.get("/firebase/user")
async def get_firebase_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current Firebase user data"""
    return JSONResponse(
        {
            "success": True,
            "user": {
                "uid": current_user["uid"],
                "email": current_user["email"],
                "name": current_user["name"],
                "verified": current_user["verified"],
                "user_data": current_user["user_data"],
            },
        }
    )


@router.put("/firebase/profile")
async def update_firebase_profile(
    display_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update Firebase user profile"""
    try:
        profile_data = {}
        if display_name:
            profile_data["display_name"] = display_name
        if phone:
            profile_data["profile.phone"] = phone
        if role and current_user["user_data"].get("role") in ["manager", "supervisor"]:
            profile_data["role"] = role

        success = await firebase_auth_service.update_user_profile(
            current_user["uid"], profile_data
        )

        if success:
            return JSONResponse(
                {"success": True, "message": "Profile updated successfully"}
            )
        else:
            return JSONResponse(
                {"success": False, "message": "Profile update failed"}, status_code=400
            )

    except Exception:
        return JSONResponse(
            {"success": False, "message": "Profile update failed"}, status_code=500
        )


@router.get("/config")
async def get_auth_config():
    """Get authentication configuration for frontend"""
    use_firebase = os.getenv("USE_FIRESTORE", "false").lower() == "true"

    config = {"use_firebase": use_firebase, "firebase_config": None}

    if use_firebase:
        config["firebase_config"] = {
            "apiKey": os.getenv("FIREBASE_API_KEY", ""),
            "authDomain": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'chatterfix-cmms')}.firebaseapp.com",
            "projectId": os.getenv("GOOGLE_CLOUD_PROJECT", "chatterfix-cmms"),
            "storageBucket": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'chatterfix-cmms')}.appspot.com",
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
            "appId": os.getenv("FIREBASE_APP_ID", ""),
        }

    return JSONResponse(config)
