"""
Signup Routes
User registration and account creation
Creates user + organization for multi-tenant support
"""

import os
from datetime import datetime

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services import auth_service
from app.services.firebase_auth import firebase_auth_service
from app.services.organization_service import get_organization_service
from app.routers.org_bootstrap import create_rate_limits_for_org, SubscriptionTier

router = APIRouter(prefix="/signup", tags=["signup"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Redirect to main signup page (landing)"""
    return RedirectResponse(url="/landing", status_code=302)


@router.post("")
async def signup(
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    company_name: str = Form(""),  # Optional company name
    request: Request = None,
):
    """
    Create new user account with organization.
    Creates both the user and their personal/company organization.
    """

    # Validate password length
    if len(password) < 8:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Password must be at least 8 characters"},
        )

    org_service = get_organization_service()

    # Use company name or generate from username/email
    org_name = (
        company_name.strip() if company_name else f"{full_name or username}'s Workspace"
    )

    # Check if we're using Firebase (production) or SQLite (local)
    use_firebase = os.getenv("USE_FIRESTORE", "false").lower() == "true"

    if use_firebase and firebase_auth_service.is_available:
        # Firebase/Firestore signup flow
        try:
            # Create Firebase user
            user_record = await firebase_auth_service.create_user_with_email_password(
                email=email, password=password, display_name=full_name or username
            )

            user_id = user_record.uid

            # Create organization for this user
            org_data = await org_service.create_organization(
                name=org_name,
                owner_user_id=user_id,
                owner_email=email,
            )
            org_id = org_data.get("id")

            # Create rate limits for the organization (FREE tier for self-service)
            try:
                await create_rate_limits_for_org(org_id, SubscriptionTier.FREE)
            except Exception as rate_limit_error:
                print(f"Rate limits creation failed (non-critical): {rate_limit_error}")

            # Update user profile with organization info
            if firebase_auth_service.db:
                user_ref = firebase_auth_service.db.collection("users").document(
                    user_id
                )
                user_ref.set(
                    {
                        "uid": user_id,
                        "email": email,
                        "username": username,
                        "full_name": full_name or username,
                        "display_name": full_name or username,
                        "role": "owner",
                        "status": "active",
                        "organization_id": org_id,
                        "organization_name": org_name,
                        "organization_role": "owner",
                        "created_at": datetime.now().isoformat(),
                    },
                    merge=True,
                )

            # Create Firebase session token
            token = await firebase_auth_service.create_custom_token(user_record.uid)

        except Exception as e:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": f"Signup failed: {str(e)}"},
            )
    else:
        # SQLite signup flow (local development)
        user_id = auth_service.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role="owner",  # Owner of their own workspace
        )

        if not user_id:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Username or email already exists"},
            )

        # Create organization for local user too
        try:
            org_data = await org_service.create_organization(
                name=org_name,
                owner_user_id=str(user_id),
                owner_email=email,
            )
            # Create rate limits for local development too
            org_id = org_data.get("id")
            if org_id:
                await create_rate_limits_for_org(org_id, SubscriptionTier.FREE)
        except Exception as org_error:
            # Log but don't fail - org creation is enhancement
            print(f"Organization creation failed (non-critical): {org_error}")

        # Auto-login: create session
        ip_address = request.client.host if (request and request.client) else "unknown"
        user_agent = (
            request.headers.get("user-agent", "unknown") if request else "unknown"
        )
        token = auth_service.create_session(user_id, ip_address, user_agent)

    # Set cookie and redirect to dashboard with welcome message
    response = RedirectResponse(url="/dashboard?welcome=true", status_code=302)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax",
    )

    return response
