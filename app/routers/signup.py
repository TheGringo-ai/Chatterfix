"""
Signup Routes
User registration and account creation
"""

from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services import auth_service
from app.services.mock_data_service import create_demo_data
from typing import Optional

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
    request: Request = None
):
    """Create new user account"""
    
    # Validate password length
    if len(password) < 8:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Password must be at least 8 characters"
        })
    
    # Create user
    user_id = auth_service.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name,
        role="technician"  # Default role for new signups
    )
    
    if not user_id:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Username or email already exists"
        })
    
    # Create demo data for new user
    create_demo_data(user_id)
    
    # Auto-login: create session
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    token = auth_service.create_session(user_id, ip_address, user_agent)
    
    # Set cookie and redirect
    response = RedirectResponse(url="/dashboard?welcome=true", status_code=302)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
    )
    
    return response
