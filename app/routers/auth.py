"""
Authentication Routes
Login, logout, and user authentication endpoints
Firebase Authentication Only - No SQLite fallback
"""

import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.firebase_auth import firebase_auth_service

logger = logging.getLogger(__name__)

# Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/login")
@limiter.limit("5/minute")  # Rate limit: 5 login attempts per minute per IP
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """User login endpoint with Firebase Authentication"""
    if not firebase_auth_service.is_available:
        logger.error("Firebase authentication is not available")
        return JSONResponse(
            {"success": False, "message": "Authentication service unavailable. Please contact support."},
            status_code=503,
        )

    try:
        # Sign in with Firebase
        auth_result = await firebase_auth_service.sign_in_with_email_password(
            username, password
        )
        token = auth_result["idToken"]

        # Create redirect response and set cookie directly on it
        redirect_response = RedirectResponse(url="/dashboard", status_code=302)
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        redirect_response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=is_production,  # HTTPS only in production
            max_age=3600,  # 1 hour
            samesite="lax",  # Lax allows cookie on same-site navigations
            path="/",  # Cookie available for all paths
        )
        return redirect_response

    except Exception as e:
        logger.warning(f"Login failed for {username}: {e}")
        return JSONResponse(
            {"success": False, "message": "Invalid email or password"},
            status_code=401,
        )


@router.post("/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    """User logout endpoint - clears session cookie"""
    # Firebase tokens are stateless, so we just clear the cookie
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("session_token")
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/me")
async def get_current_user_info(session_token: Optional[str] = Cookie(None)):
    """Get current logged-in user from Firebase"""
    if not session_token:
        return JSONResponse({"authenticated": False}, status_code=401)

    try:
        user_data = await firebase_auth_service.verify_token(session_token)
        return JSONResponse(
            {
                "authenticated": True,
                "user": {
                    "id": user_data["uid"],
                    "uid": user_data["uid"],
                    "username": user_data["email"],
                    "email": user_data["email"],
                    "full_name": user_data["name"] or user_data["email"],
                    "role": user_data["user_data"].get("role", "technician"),
                    "permissions": user_data["user_data"].get("permissions", []),
                },
            }
        )
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return JSONResponse({"authenticated": False}, status_code=401)


@router.post("/reset-password")
@limiter.limit("3/minute")  # Rate limit password reset requests
async def request_password_reset(
    request: Request,
    email: str = Form(...),
):
    """Request password reset via Firebase"""
    if not firebase_auth_service.is_available:
        return JSONResponse(
            {"success": False, "message": "Service unavailable"},
            status_code=503,
        )

    try:
        # Firebase handles sending the password reset email
        await firebase_auth_service.send_password_reset_email(email)
        return JSONResponse(
            {"success": True, "message": "If an account exists with this email, a password reset link has been sent."}
        )
    except Exception as e:
        logger.warning(f"Password reset request failed for {email}: {e}")
        # Don't reveal if email exists or not
        return JSONResponse(
            {"success": True, "message": "If an account exists with this email, a password reset link has been sent."}
        )


# ===== FIREBASE AUTHENTICATION ENDPOINTS =====


@router.post("/firebase/verify")
@limiter.limit("10/minute")  # Rate limit token verification
async def verify_firebase_token(request: Request, token: str = Form(...)):
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
async def get_firebase_user(session_token: Optional[str] = Cookie(None)):
    """Get current Firebase user data"""
    if not session_token:
        return JSONResponse({"success": False, "message": "Not authenticated"}, status_code=401)

    try:
        user_data = await firebase_auth_service.verify_token(session_token)
        return JSONResponse(
            {
                "success": True,
                "user": {
                    "uid": user_data["uid"],
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "verified": user_data["verified"],
                    "user_data": user_data["user_data"],
                },
            }
        )
    except Exception:
        return JSONResponse(
            {"success": False, "message": "Authentication failed"}, status_code=401
        )


@router.put("/firebase/profile")
async def update_firebase_profile(
    request: Request,
    display_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    session_token: Optional[str] = Cookie(None),
):
    """Update Firebase user profile"""
    if not session_token:
        return JSONResponse({"success": False, "message": "Not authenticated"}, status_code=401)

    try:
        current_user = await firebase_auth_service.verify_token(session_token)

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


@router.post("/firebase-signin")
async def firebase_signin(request: Request):
    """Handle Firebase authentication tokens from client-side signup/login"""
    try:
        body = await request.json()
        id_token = body.get("idToken")

        if not id_token:
            raise HTTPException(status_code=400, detail="ID token required")

        # Verify Firebase token and get user data
        user_data = await firebase_auth_service.verify_token(id_token)

        # Use the ID token as session token (Firebase ID tokens are self-validating)
        session_token = id_token

        # Create response with user data
        json_response = JSONResponse(
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

        # Set session cookie directly on the response being returned
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        json_response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=is_production,  # HTTPS only in production
            max_age=3600,  # 1 hour
            samesite="lax",  # Lax allows cookie on same-site navigations
            path="/",  # Cookie available for all paths
        )

        return json_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.get("/config")
async def get_auth_config():
    """Get authentication configuration for frontend

    Note: Firebase API keys are designed to be public - they are protected
    by Firebase Security Rules, not by keeping them secret. This is how
    Firebase web authentication is designed to work.
    """
    # Always use Firebase
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "fredfix")
    api_key = os.getenv("FIREBASE_API_KEY", "")

    config = {
        "use_firebase": True,
        "firebase_config": {
            "apiKey": api_key,
            "authDomain": f"{project_id}.firebaseapp.com",
            "projectId": project_id,
            "storageBucket": f"{project_id}.appspot.com",
        }
    }

    return JSONResponse(config)
