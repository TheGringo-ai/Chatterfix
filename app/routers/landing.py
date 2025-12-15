# Email functionality - temporarily simplified
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart
import logging
import os
import secrets
import string
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.core.db_adapter import get_db_adapter
from app.services.organization_service import get_organization_service
from app.services.firebase_auth import firebase_auth_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LandingSignupRequest(BaseModel):
    fullName: str
    email: str
    company: str
    phone: str = None
    industry: str
    company_size: str


def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for i in range(length))
    return password


async def send_notification_email(user_data: dict, password: str):
    """Send notification email to yoyofred@gringosgambit.com"""
    try:
        # Simplified logging for now - email functionality can be added later
        logger.info(
            f"""
🚀 NEW CHATTERFIX SIGNUP:
Company: {user_data['company']}
Industry: {user_data['industry']}
Size: {user_data['company_size']}
Contact: {user_data['fullName']} ({user_data['email']})
Password: {password}
"""
        )
        # Send actual email using email service
        from app.services.email_service import email_service

        await email_service.send_password_reset_email(user_data, password)

    except Exception as e:
        logger.error(f"Failed to log notification: {str(e)}")


async def send_welcome_email(user_data: dict, password: str):
    """Send welcome email to the new user"""
    try:
        # Simplified logging for now - email functionality can be added later
        logger.info(
            f"Welcome email logged for {user_data['fullName']} ({user_data['email']})"
        )
        # Send actual welcome email using email service
        from app.services.email_service import email_service

        await email_service.send_welcome_email(user_data, password)

    except Exception as e:
        logger.error(f"Failed to log welcome email: {str(e)}")


@router.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the comprehensive public landing page with demo access"""
    return templates.TemplateResponse("public_landing.html", {"request": request})


@router.get("/public", response_class=HTMLResponse)
async def public_landing(request: Request):
    """Public landing page (same as /landing for compatibility)"""
    return templates.TemplateResponse("public_landing.html", {"request": request})


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serve the signup page for actual registration"""
    # Firebase configuration for client-side auth
    firebase_config = (
        {
            "api_key": os.getenv("FIREBASE_API_KEY", ""),
            "auth_domain": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'chatterfix-cmms')}.firebaseapp.com",
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "chatterfix-cmms"),
            "storage_bucket": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'chatterfix-cmms')}.appspot.com",
            "messaging_sender_id": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
            "app_id": os.getenv("FIREBASE_APP_ID", ""),
        }
        if os.getenv("FIREBASE_API_KEY")
        else None
    )

    return templates.TemplateResponse(
        "signup.html", {"request": request, "firebase_config": firebase_config}
    )


@router.post("/api/landing/signup")
async def handle_landing_signup(
    signup_data: LandingSignupRequest, background_tasks: BackgroundTasks
):
    """
    Handle landing page signup form submission.
    Creates:
    1. Firebase Auth user
    2. Firestore user profile
    3. Organization for the company
    """
    try:
        # Generate secure password
        password = generate_password()

        db = get_db_adapter()
        org_service = get_organization_service()

        # Check if user already exists
        existing_user = await db.get_user_by_email(signup_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please use the login page.",
            )

        user_id = None
        org_id = None

        # Try Firebase Authentication first (production)
        if firebase_auth_service.is_available:
            try:
                # Create Firebase Auth user
                user_record = await firebase_auth_service.create_user_with_email_password(
                    email=signup_data.email,
                    password=password,
                    display_name=signup_data.fullName
                )
                user_id = user_record.uid

                # Create organization for this company
                org_data = await org_service.create_organization(
                    name=signup_data.company,
                    owner_user_id=user_id,
                    owner_email=signup_data.email,
                    industry=signup_data.industry,
                    size=signup_data.company_size,
                    phone=signup_data.phone,
                )
                org_id = org_data.get("id")

                # Update user profile in Firestore with full details
                if firebase_auth_service.db:
                    user_ref = firebase_auth_service.db.collection("users").document(user_id)
                    user_ref.set({
                        "uid": user_id,
                        "email": signup_data.email,
                        "full_name": signup_data.fullName,
                        "display_name": signup_data.fullName,
                        "phone": signup_data.phone,
                        "role": "owner",  # Owner of the organization
                        "status": "active",
                        "organization_id": org_id,
                        "organization_name": signup_data.company,
                        "organization_role": "owner",
                        "company": {
                            "name": signup_data.company,
                            "industry": signup_data.industry,
                            "size": signup_data.company_size,
                        },
                        "created_at": datetime.now().isoformat(),
                    }, merge=True)

                logger.info(f"Created Firebase user {user_id} with organization {org_id}")

            except Exception as firebase_error:
                logger.error(f"Firebase signup failed: {firebase_error}")
                # Fall back to basic Firestore storage
                raise HTTPException(
                    status_code=500,
                    detail=f"Account creation failed: {str(firebase_error)}"
                )
        else:
            # Fallback: Create user in Firestore only (no Firebase Auth)
            user_data = {
                "email": signup_data.email,
                "full_name": signup_data.fullName,
                "phone": signup_data.phone,
                "role": "owner",
                "status": "active",
                "company": {
                    "name": signup_data.company,
                    "industry": signup_data.industry,
                    "size": signup_data.company_size,
                },
                "created_at": datetime.now().isoformat(),
            }
            user_id = await db.create_user(user_data)

            # Create organization
            org_data = await org_service.create_organization(
                name=signup_data.company,
                owner_user_id=user_id,
                owner_email=signup_data.email,
                industry=signup_data.industry,
                size=signup_data.company_size,
                phone=signup_data.phone,
            )
            org_id = org_data.get("id")

        # Prepare user data for emails
        email_data = {
            "fullName": signup_data.fullName,
            "email": signup_data.email,
            "company": signup_data.company,
            "phone": signup_data.phone,
            "industry": signup_data.industry,
            "company_size": signup_data.company_size,
        }

        # Schedule background email tasks
        background_tasks.add_task(send_notification_email, email_data, password)
        background_tasks.add_task(send_welcome_email, email_data, password)

        logger.info(
            f"New user created: {signup_data.email} for company {signup_data.company} (org: {org_id})"
        )

        return {
            "success": True,
            "message": "Account created successfully! Check your email for login credentials.",
            "user_id": user_id,
            "organization_id": org_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create account. Please try again later."
        )


@router.get("/api/landing/health")
async def landing_health():
    """Health check endpoint for landing page"""
    return {"status": "healthy", "service": "landing_page"}
