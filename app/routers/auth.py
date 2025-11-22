"""
Authentication Routes
Login, logout, and user authentication endpoints
"""

from fastapi import APIRouter, Request, Form, Cookie, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services import auth_service
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    request: Request = None
):
    """User login endpoint"""
    # Authenticate user
    user = auth_service.authenticate_user(username, password)
    
    if not user:
        return JSONResponse(
            {"success": False, "message": "Invalid username or password"},
            status_code=401
        )
    
    # Create session
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    token = auth_service.create_session(user['id'], ip_address, user_agent)
    
    # Set cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
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
    
    user = auth_service.validate_session(session_token)
    
    if not user:
        return JSONResponse({"authenticated": False}, status_code=401)
    
    return JSONResponse({
        "authenticated": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role']
        }
    })


@router.post("/change-password")
async def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    session_token: Optional[str] = Cookie(None)
):
    """Change user password"""
    if not session_token:
        return JSONResponse({"success": False, "message": "Not authenticated"}, status_code=401)
    
    user = auth_service.validate_session(session_token)
    if not user:
        return JSONResponse({"success": False, "message": "Invalid session"}, status_code=401)
    
    success = auth_service.change_password(user['id'], old_password, new_password)
    
    if success:
        return JSONResponse({"success": True, "message": "Password changed successfully"})
    else:
        return JSONResponse({"success": False, "message": "Invalid old password"}, status_code=400)
