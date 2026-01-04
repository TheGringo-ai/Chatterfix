"""
Authentication Routes
Login, logout, and user authentication endpoints
Firebase Authentication Only - No SQLite fallback
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Cookie, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.firebase_auth import firebase_auth_service
from app.services.organization_service import OrganizationService

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
            {
                "success": False,
                "message": "Authentication service unavailable. Please contact support.",
            },
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
            {
                "success": True,
                "message": "If an account exists with this email, a password reset link has been sent.",
            }
        )
    except Exception as e:
        logger.warning(f"Password reset request failed for {email}: {e}")
        # Don't reveal if email exists or not
        return JSONResponse(
            {
                "success": True,
                "message": "If an account exists with this email, a password reset link has been sent.",
            }
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
        return JSONResponse(
            {"success": False, "message": "Not authenticated"}, status_code=401
        )

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
        return JSONResponse(
            {"success": False, "message": "Not authenticated"}, status_code=401
        )

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

        uid = user_data["uid"]
        email = user_data["email"]
        name = user_data["name"]
        stored_user_data = user_data.get("user_data", {})

        # Check if user has an organization - if not, create one
        org_id = stored_user_data.get("organization_id")
        org_name = stored_user_data.get("organization_name")

        if not org_id:
            # User doesn't have an organization - create one for them
            logger.info(f"User {uid} has no organization - creating one")
            org_service = OrganizationService()
            try:
                org_data = await org_service.create_organization(
                    name=f"{name or email.split('@')[0]}'s Workspace",
                    owner_user_id=uid,
                    owner_email=email,
                    is_demo=False,
                )
                org_id = org_data.get("id")
                org_name = org_data.get("name")
                logger.info(f"Created organization {org_id} for user {uid}")

                # Update user document with organization info
                if firebase_auth_service.db:
                    user_ref = firebase_auth_service.db.collection("users").document(uid)
                    user_ref.set(
                        {
                            "organization_id": org_id,
                            "organization_name": org_name,
                            "organization_role": "owner",
                            "role": "owner",
                        },
                        merge=True,
                    )
            except Exception as org_error:
                logger.error(f"Failed to create organization for user {uid}: {org_error}")
                # Don't fail login - just log the error

        # Use the ID token as session token (Firebase ID tokens are self-validating)
        session_token = id_token

        # Create response with user data
        json_response = JSONResponse(
            {
                "success": True,
                "user": {
                    "uid": uid,
                    "email": email,
                    "name": name,
                    "verified": user_data["verified"],
                    "role": stored_user_data.get("role", "owner"),
                    "organization_id": org_id,
                    "organization_name": org_name,
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
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", f"{project_id}.firebasestorage.app")
    messaging_sender_id = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "")
    app_id = os.getenv("FIREBASE_APP_ID", "")
    measurement_id = os.getenv("FIREBASE_MEASUREMENT_ID", "")

    config = {
        "use_firebase": True,
        "firebase_config": {
            "apiKey": api_key,
            "authDomain": f"{project_id}.firebaseapp.com",
            "projectId": project_id,
            "storageBucket": storage_bucket,
            "messagingSenderId": messaging_sender_id,
            "appId": app_id,
            "measurementId": measurement_id,
        },
    }

    return JSONResponse(config)


# ===== DEMO ORGANIZATION ENDPOINTS =====


@router.post("/try-demo")
@limiter.limit("10/minute")  # Rate limit demo creation
async def try_demo(request: Request):
    """Create a demo account with Firebase Anonymous Auth

    This endpoint:
    1. Accepts an anonymous Firebase ID token from the client
    2. Creates a demo organization (expires in 48 hours)
    3. Creates a user record linked to the demo org
    4. Sets the session cookie
    5. Returns success for client redirect
    """
    try:
        body = await request.json()
        id_token = body.get("idToken")

        if not id_token:
            raise HTTPException(status_code=400, detail="ID token required")

        # Verify the anonymous Firebase token
        from firebase_admin import auth

        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as verify_error:
            logger.error(f"Demo token verification failed: {verify_error}")
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        anonymous_uid = decoded_token["uid"]
        is_anonymous = (
            decoded_token.get("firebase", {}).get("sign_in_provider") == "anonymous"
        )

        if not is_anonymous:
            raise HTTPException(
                status_code=400,
                detail="This endpoint is for anonymous demo users only. Please use /signup for regular accounts.",
            )

        # Create demo organization using the organization service
        org_service = OrganizationService()

        try:
            demo_org = await org_service.create_demo_organization(anonymous_uid)
        except Exception as org_error:
            logger.error(f"Demo organization creation failed: {org_error}")
            raise HTTPException(
                status_code=500, detail="Failed to create demo organization"
            )

        # Create/update user record in Firestore for the anonymous user
        if firebase_auth_service.db:
            user_ref = firebase_auth_service.db.collection("users").document(
                anonymous_uid
            )
            from firebase_admin import firestore

            user_data = {
                "uid": anonymous_uid,
                "email": f"demo-{anonymous_uid[:8]}@demo.chatterfix.com",
                "display_name": f"Demo User",
                "is_anonymous": True,
                "is_demo": True,
                "organization_id": demo_org["id"],
                "organization_name": demo_org["name"],
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": firestore.SERVER_TIMESTAMP,
                "role": "manager",  # Give demo users manager access to see all features
                "status": "active",
                "demo_expires_at": demo_org["expires_at"],
            }
            user_ref.set(user_data)

        # Calculate time remaining for display
        time_remaining = await org_service.get_demo_time_remaining(demo_org["id"])
        hours_remaining = time_remaining // 60 if time_remaining else 48

        # Create response with demo info
        json_response = JSONResponse(
            {
                "success": True,
                "demo": True,
                "organization": {
                    "id": demo_org["id"],
                    "name": demo_org["name"],
                    "expires_at": (
                        demo_org["expires_at"].isoformat()
                        if demo_org.get("expires_at")
                        else None
                    ),
                    "hours_remaining": hours_remaining,
                },
                "user": {
                    "uid": anonymous_uid,
                    "role": "manager",
                    "is_demo": True,
                },
                "message": f"Welcome to your 48-hour demo! Your workspace '{demo_org['name']}' is ready.",
            }
        )

        # Set session cookie
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        json_response.set_cookie(
            key="session_token",
            value=id_token,
            httponly=True,
            secure=is_production,
            max_age=3600 * 48,  # 48 hours for demo
            samesite="lax",
            path="/",
        )

        logger.info(
            f"Demo organization created: {demo_org['id']} for user {anonymous_uid}"
        )
        return json_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Try demo error: {e}")
        raise HTTPException(status_code=500, detail=f"Demo creation failed: {str(e)}")


@router.get("/demo-status")
async def get_demo_status(session_token: Optional[str] = Cookie(None)):
    """Check the status of a demo account (time remaining, etc.)"""
    if not session_token:
        return JSONResponse({"is_demo": False}, status_code=200)

    try:
        user_data = await firebase_auth_service.verify_token(session_token)

        # Check if user is a demo user
        is_demo = user_data.get("user_data", {}).get("is_demo", False)

        if not is_demo:
            return JSONResponse({"is_demo": False}, status_code=200)

        org_id = user_data.get("organization_id") or user_data.get("user_data", {}).get(
            "organization_id"
        )

        if not org_id:
            return JSONResponse(
                {"is_demo": True, "error": "No organization found"}, status_code=200
            )

        # Get time remaining
        org_service = OrganizationService()
        time_remaining = await org_service.get_demo_time_remaining(org_id)

        if time_remaining is None:
            return JSONResponse(
                {
                    "is_demo": True,
                    "expired": True,
                    "message": "Your demo has expired. Sign up for a free account to keep your data!",
                },
                status_code=200,
            )

        hours = time_remaining // 60
        minutes = time_remaining % 60

        return JSONResponse(
            {
                "is_demo": True,
                "expired": False,
                "minutes_remaining": time_remaining,
                "hours_remaining": hours,
                "display_time": f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
                "organization_id": org_id,
                "message": f"Demo time remaining: {hours}h {minutes}m",
            },
            status_code=200,
        )

    except Exception as e:
        logger.warning(f"Demo status check failed: {e}")
        return JSONResponse({"is_demo": False, "error": str(e)}, status_code=200)


@router.post("/upgrade-demo")
@limiter.limit("5/minute")
async def upgrade_demo_account(
    request: Request, session_token: Optional[str] = Cookie(None)
):
    """Upgrade a demo account to a real account

    This endpoint:
    1. Links the anonymous Firebase user to an email/password
    2. Converts the demo organization to a permanent one
    3. Updates user records
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        full_name = body.get("full_name", "")
        organization_name = body.get("organization_name")  # Optional new name

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        if len(password) < 8:
            raise HTTPException(
                status_code=400, detail="Password must be at least 8 characters"
            )

        # Verify current session and get user data
        user_data = await firebase_auth_service.verify_token(session_token)

        # Check if user is a demo user
        is_demo = user_data.get("user_data", {}).get("is_demo", False)
        if not is_demo:
            raise HTTPException(
                status_code=400,
                detail="This endpoint is only for demo accounts. You already have a full account.",
            )

        org_id = user_data.get("organization_id") or user_data.get("user_data", {}).get(
            "organization_id"
        )
        old_uid = user_data["uid"]

        if not org_id:
            raise HTTPException(
                status_code=400, detail="No organization found for this demo account"
            )

        # Create a new Firebase user with email/password
        from firebase_admin import auth

        try:
            # Create new user with email/password
            new_user = auth.create_user(
                email=email,
                password=password,
                display_name=full_name or email.split("@")[0],
                email_verified=False,
            )
            new_uid = new_user.uid

            # Send email verification
            try:
                link = auth.generate_email_verification_link(email)
                logger.info(f"Email verification link generated for {email}")
            except Exception as verify_error:
                logger.warning(f"Could not generate verification link: {verify_error}")

        except auth.EmailAlreadyExistsError:
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please use a different email or login to your existing account.",
            )
        except Exception as create_error:
            logger.error(f"Failed to create user: {create_error}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create account: {str(create_error)}"
            )

        # Convert the demo organization to a real one
        org_service = OrganizationService()

        try:
            success = await org_service.convert_demo_to_real(
                org_id=org_id,
                new_owner_uid=new_uid,
                new_owner_email=email,
                new_name=organization_name,
            )

            if not success:
                # Rollback: delete the created user
                auth.delete_user(new_uid)
                raise HTTPException(
                    status_code=500, detail="Failed to upgrade organization"
                )

        except HTTPException:
            raise
        except Exception as org_error:
            # Rollback: delete the created user
            try:
                auth.delete_user(new_uid)
            except Exception:
                pass
            logger.error(f"Organization conversion failed: {org_error}")
            raise HTTPException(
                status_code=500, detail="Failed to upgrade organization"
            )

        # Update user record in Firestore
        if firebase_auth_service.db:
            from firebase_admin import firestore

            # Create new user document
            new_user_ref = firebase_auth_service.db.collection("users").document(
                new_uid
            )
            new_user_data = {
                "uid": new_uid,
                "email": email,
                "display_name": full_name or email.split("@")[0],
                "full_name": full_name,
                "is_anonymous": False,
                "is_demo": False,
                "organization_id": org_id,
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": firestore.SERVER_TIMESTAMP,
                "role": "manager",  # Keep manager role from demo
                "status": "active",
                "upgraded_from_demo": True,
                "previous_anonymous_uid": old_uid,
            }
            new_user_ref.set(new_user_data)

            # Mark old anonymous user as upgraded (don't delete for audit trail)
            old_user_ref = firebase_auth_service.db.collection("users").document(
                old_uid
            )
            old_user_ref.update(
                {
                    "status": "upgraded",
                    "upgraded_to": new_uid,
                    "upgraded_at": firestore.SERVER_TIMESTAMP,
                }
            )

        # Delete the anonymous Firebase user (optional - keeps things clean)
        try:
            auth.delete_user(old_uid)
            logger.info(f"Deleted anonymous user {old_uid} after upgrade")
        except Exception as delete_error:
            logger.warning(f"Could not delete anonymous user {old_uid}: {delete_error}")

        # Create a custom token for the new user to sign them in
        custom_token = auth.create_custom_token(new_uid)
        if isinstance(custom_token, bytes):
            custom_token = custom_token.decode("utf-8")

        # Get updated org info
        org_data = await org_service.get_organization(org_id)

        return JSONResponse(
            {
                "success": True,
                "message": "Account upgraded successfully! Please verify your email.",
                "user": {
                    "uid": new_uid,
                    "email": email,
                    "display_name": full_name or email.split("@")[0],
                    "is_demo": False,
                },
                "organization": {
                    "id": org_id,
                    "name": org_data.get("name") if org_data else organization_name,
                },
                "custom_token": custom_token,  # Client uses this to sign in as the new user
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo upgrade error: {e}")
        raise HTTPException(status_code=500, detail=f"Upgrade failed: {str(e)}")


@router.get("/upgrade", response_class=HTMLResponse)
async def upgrade_page(request: Request, session_token: Optional[str] = Cookie(None)):
    """Render the demo upgrade page"""
    # Check if user is logged in and is a demo user
    is_demo = False
    demo_status = None

    if session_token:
        try:
            user_data = await firebase_auth_service.verify_token(session_token)
            is_demo = user_data.get("user_data", {}).get("is_demo", False)

            if is_demo:
                org_id = user_data.get("organization_id") or user_data.get(
                    "user_data", {}
                ).get("organization_id")
                if org_id:
                    org_service = OrganizationService()
                    time_remaining = await org_service.get_demo_time_remaining(org_id)
                    if time_remaining:
                        hours = time_remaining // 60
                        minutes = time_remaining % 60
                        demo_status = {
                            "hours": hours,
                            "minutes": minutes,
                            "org_id": org_id,
                            "org_name": user_data.get("user_data", {}).get(
                                "organization_name", "Demo Workspace"
                            ),
                        }
        except Exception:
            pass

    if not is_demo:
        # Not a demo user, redirect to signup
        return RedirectResponse(url="/signup", status_code=302)

    return templates.TemplateResponse(
        "upgrade.html",
        {
            "request": request,
            "demo_status": demo_status,
        },
    )
