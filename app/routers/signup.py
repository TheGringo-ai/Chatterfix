"""
Signup Routes
User registration and account creation
"""

import os

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services import auth_service
from app.services.firebase_auth import firebase_auth_service
from app.services.mock_data_service import create_demo_data

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
    request: Request = None,
):
    """Create new user account"""

    # Validate password length
    if len(password) < 8:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Password must be at least 8 characters"},
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

            # Get or create user in Firestore
            user_data = await firebase_auth_service.get_or_create_user(user_record)
            user_id = user_data.get("uid")

            # Create demo data for new user
            create_demo_data(user_id)

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
            role="technician",  # Default role for new signups
        )

        if not user_id:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Username or email already exists"},
            )

        # Create demo data for new user
        create_demo_data(user_id)

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
