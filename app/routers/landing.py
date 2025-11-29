from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime
import smtplib

# Email functionality - temporarily simplified
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart
import os
import logging
import secrets
import string
from app.core.database import get_db_connection

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LandingSignupRequest(BaseModel):
    fullName: str
    email: EmailStr
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
        # TODO: Implement actual email sending

    except Exception as e:
        logger.error(f"Failed to log notification: {str(e)}")


async def send_welcome_email(user_data: dict, password: str):
    """Send welcome email to the new user"""
    try:
        # Simplified logging for now - email functionality can be added later
        logger.info(
            f"Welcome email logged for {user_data['fullName']} ({user_data['email']})"
        )
        # TODO: Implement actual welcome email sending

    except Exception as e:
        logger.error(f"Failed to log welcome email: {str(e)}")


@router.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the landing page (now signup page)"""
    return templates.TemplateResponse("landing.html", {"request": request})


@router.post("/api/landing/signup")
async def handle_landing_signup(
    signup_data: LandingSignupRequest, background_tasks: BackgroundTasks
):
    """Handle landing page signup form submission"""
    try:
        # Generate secure password
        password = generate_password()

        # Create user in database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (signup_data.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please use the login page.",
            )

        # Insert new user (working with existing schema)
        cursor.execute(
            """
            INSERT INTO users (
                username, email, password_hash, full_name, phone, role, 
                is_active, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                signup_data.email,  # Use email as username
                signup_data.email,
                password,  # In production, you should hash this password
                signup_data.fullName,
                signup_data.phone,
                "manager",  # First user becomes manager
                True,
                datetime.now().isoformat(),
            ),
        )

        user_id = cursor.lastrowid

        # Insert company information
        cursor.execute(
            """
            INSERT INTO companies (
                user_id, name, industry, company_size, created_date
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (
                user_id,
                signup_data.company,
                signup_data.industry,
                signup_data.company_size,
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        # Prepare user data for emails
        user_data = {
            "fullName": signup_data.fullName,
            "email": signup_data.email,
            "company": signup_data.company,
            "phone": signup_data.phone,
            "industry": signup_data.industry,
            "company_size": signup_data.company_size,
        }

        # Schedule background email tasks
        background_tasks.add_task(send_notification_email, user_data, password)
        background_tasks.add_task(send_welcome_email, user_data, password)

        logger.info(
            f"New user created: {signup_data.email} for company {signup_data.company}"
        )

        return {
            "success": True,
            "message": "Account created successfully! Check your email for login credentials.",
            "user_id": user_id,
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
