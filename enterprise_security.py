#!/usr/bin/env python3
"""
ChatterFix CMMS - Enterprise Security Module
OAuth2 + JWT + RBAC + Anomaly Detection
"""

import jwt
import bcrypt
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import secrets
import os
import hashlib
from collections import defaultdict, deque
import asyncio
import json

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# RBAC Role definitions
ROLES = {
    "technician": {
        "permissions": [
            "view_work_orders", "update_work_status", "view_assets", 
            "add_notes", "view_parts", "request_parts"
        ],
        "description": "Field technician with basic operational access"
    },
    "supervisor": {
        "permissions": [
            "view_work_orders", "create_work_orders", "assign_work_orders",
            "update_work_status", "view_assets", "update_assets", 
            "view_parts", "manage_parts", "view_reports"
        ],
        "description": "Supervisor with team management capabilities"
    },
    "manager": {
        "permissions": [
            "view_work_orders", "create_work_orders", "assign_work_orders",
            "delete_work_orders", "view_assets", "create_assets", "update_assets",
            "view_parts", "manage_parts", "view_reports", "create_reports",
            "manage_users", "view_analytics"
        ],
        "description": "Manager with full operational control"
    },
    "admin": {
        "permissions": [
            "*"  # All permissions
        ],
        "description": "System administrator with full access"
    }
}

class SecurityModels:
    class User(BaseModel):
        username: str
        email: EmailStr
        role: str
        full_name: Optional[str] = None
        is_active: bool = True
        created_at: datetime = datetime.now()
    
    class UserCreate(BaseModel):
        username: str
        email: EmailStr
        password: str
        role: str
        full_name: Optional[str] = None
    
    class UserLogin(BaseModel):
        username: str
        password: str
        remember_me: bool = False
    
    class Token(BaseModel):
        access_token: str
        refresh_token: str
        token_type: str = "bearer"
        expires_in: int
    
    class TokenData(BaseModel):
        username: Optional[str] = None
        role: Optional[str] = None
        permissions: List[str] = []

class SecurityManager:
    """Enterprise security and anomaly detection system"""
    
    def __init__(self):
        self.redis_client = None
        self.failed_attempts = defaultdict(deque)
        self.suspicious_activity = defaultdict(list)
        self.security_events = []
    
    async def initialize(self):
        """Initialize Redis connection for session management"""
        self.redis_client = await redis.from_url(
            REDIS_URL,
            encoding="utf-8", 
            decode_responses=True
        )
        print("🔐 Security manager initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))\n    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        \"\"\"Create JWT access token\"\"\"
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({\"exp\": expire, \"type\": \"access\"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        \"\"\"Create JWT refresh token\"\"\"
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({\"exp\": expire, \"type\": \"refresh\"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        \"\"\"Verify and decode JWT token\"\"\"
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=\"Token has expired\"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=\"Could not validate credentials\"
            )
    
    def get_user_permissions(self, role: str) -> List[str]:
        \"\"\"Get permissions for a role\"\"\"
        if role in ROLES:
            return ROLES[role][\"permissions\"]
        return []
    
    def check_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        \"\"\"Check if user has required permission\"\"\"
        return \"*\" in user_permissions or required_permission in user_permissions
    
    async def log_security_event(self, event_type: str, user: str, ip_address: str, details: dict):
        \"\"\"Log security event for monitoring\"\"\"
        event = {
            \"timestamp\": datetime.now().isoformat(),
            \"type\": event_type,
            \"user\": user,
            \"ip_address\": ip_address,
            \"details\": details
        }
        
        self.security_events.append(event)
        
        # Store in Redis for persistence
        if self.redis_client:
            await self.redis_client.lpush(
                \"security_events\",
                json.dumps(event)
            )
            # Keep only last 1000 events
            await self.redis_client.ltrim(\"security_events\", 0, 999)
    
    async def detect_brute_force(self, username: str, ip_address: str) -> bool:
        \"\"\"Detect brute force attempts\"\"\"
        key = f\"{username}:{ip_address}\"
        now = datetime.now()
        
        # Clean old attempts (older than 15 minutes)
        cutoff = now - timedelta(minutes=15)
        self.failed_attempts[key] = deque([
            attempt for attempt in self.failed_attempts[key] 
            if attempt > cutoff
        ])
        
        # Add current attempt
        self.failed_attempts[key].append(now)
        
        # Check if too many attempts
        if len(self.failed_attempts[key]) >= 5:
            await self.log_security_event(
                \"brute_force_detected\",
                username,
                ip_address,
                {\"attempts_count\": len(self.failed_attempts[key])}
            )
            return True
        
        return False
    
    async def is_account_locked(self, username: str) -> bool:
        \"\"\"Check if account is locked\"\"\"
        if self.redis_client:
            locked_until = await self.redis_client.get(f\"locked:{username}\")
            if locked_until:
                unlock_time = datetime.fromisoformat(locked_until)
                if datetime.now() < unlock_time:
                    return True
                else:
                    # Lock expired, remove it
                    await self.redis_client.delete(f\"locked:{username}\")
        return False
    
    async def lock_account(self, username: str, duration_minutes: int = 30):
        \"\"\"Lock account for specified duration\"\"\"
        if self.redis_client:
            unlock_time = datetime.now() + timedelta(minutes=duration_minutes)
            await self.redis_client.setex(
                f\"locked:{username}\",
                duration_minutes * 60,
                unlock_time.isoformat()
            )
    
    async def invalidate_user_sessions(self, username: str):
        \"\"\"Invalidate all sessions for a user\"\"\"
        if self.redis_client:
            pattern = f\"session:{username}:*\"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)

# Initialize security manager
security_manager = SecurityManager()
security = HTTPBearer()

# FastAPI app
app = FastAPI(
    title=\"ChatterFix CMMS - Enterprise Security\",
    description=\"OAuth2 + JWT + RBAC + Anomaly Detection\",
    version=\"1.0.0\"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[\"*\"],
    allow_credentials=True,
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> SecurityModels.TokenData:
    \"\"\"Get current authenticated user\"\"\"
    token = credentials.credentials
    payload = security_manager.verify_token(token)
    
    username = payload.get(\"sub\")
    role = payload.get(\"role\")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=\"Could not validate credentials\"
        )
    
    permissions = security_manager.get_user_permissions(role)
    
    return SecurityModels.TokenData(
        username=username,
        role=role,
        permissions=permissions
    )

def require_permission(permission: str):
    \"\"\"Decorator to require specific permission\"\"\"
    def permission_checker(current_user: SecurityModels.TokenData = Depends(get_current_user)):
        if not security_manager.check_permission(current_user.permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f\"Insufficient permissions. Required: {permission}\"
            )
        return current_user
    return permission_checker

@app.on_event(\"startup\")
async def startup_event():
    await security_manager.initialize()

@app.post(\"/auth/login\", response_model=SecurityModels.Token)
async def login(user_login: SecurityModels.UserLogin, request_ip: str = \"127.0.0.1\"):
    \"\"\"Authenticate user and return tokens\"\"\"
    
    # Check if account is locked
    if await security_manager.is_account_locked(user_login.username):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=\"Account is temporarily locked due to too many failed attempts\"
        )
    
    # Check for brute force attempts
    if await security_manager.detect_brute_force(user_login.username, request_ip):
        await security_manager.lock_account(user_login.username, 30)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=\"Too many failed attempts. Account locked for 30 minutes.\"
        )
    
    # TODO: Verify credentials against database
    # For demo, using hardcoded admin user
    if user_login.username == \"admin\" and user_login.password == \"admin123\":
        user_role = \"admin\"
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security_manager.create_access_token(
            data={\"sub\": user_login.username, \"role\": user_role},
            expires_delta=access_token_expires
        )
        refresh_token = security_manager.create_refresh_token(
            data={\"sub\": user_login.username, \"role\": user_role}
        )
        
        await security_manager.log_security_event(
            \"successful_login\",
            user_login.username,
            request_ip,
            {\"role\": user_role}
        )
        
        return SecurityModels.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    else:
        await security_manager.log_security_event(
            \"failed_login\",
            user_login.username,
            request_ip,
            {\"reason\": \"invalid_credentials\"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=\"Invalid credentials\"
        )

@app.post(\"/auth/refresh\")
async def refresh_token(refresh_token: str):
    \"\"\"Refresh access token\"\"\"
    payload = security_manager.verify_token(refresh_token)
    
    if payload.get(\"type\") != \"refresh\":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=\"Invalid token type\"
        )
    
    username = payload.get(\"sub\")
    role = payload.get(\"role\")
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security_manager.create_access_token(
        data={\"sub\": username, \"role\": role},
        expires_delta=access_token_expires
    )
    
    return {
        \"access_token\": access_token,
        \"token_type\": \"bearer\",
        \"expires_in\": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.get(\"/auth/me\")
async def get_current_user_info(current_user: SecurityModels.TokenData = Depends(get_current_user)):
    \"\"\"Get current user information\"\"\"
    return {
        \"username\": current_user.username,
        \"role\": current_user.role,
        \"permissions\": current_user.permissions
    }

@app.get(\"/auth/roles\")
async def get_available_roles(current_user: SecurityModels.TokenData = Depends(require_permission(\"manage_users\"))):
    \"\"\"Get all available roles (admin only)\"\"\"
    return ROLES

@app.get(\"/security/events\")
async def get_security_events(current_user: SecurityModels.TokenData = Depends(require_permission(\"view_security_logs\"))):
    \"\"\"Get recent security events\"\"\"
    return {
        \"events\": security_manager.security_events[-50:],  # Last 50 events
        \"total_events\": len(security_manager.security_events)
    }

@app.get(\"/health\")
async def health_check():
    \"\"\"Security service health check\"\"\"
    return {
        \"status\": \"healthy\",
        \"service\": \"enterprise-security\",
        \"features\": [
            \"OAuth2 JWT Authentication\",
            \"Role-Based Access Control (RBAC)\",
            \"Brute Force Protection\", 
            \"Account Locking\",
            \"Security Event Logging\",
            \"Anomaly Detection\"
        ],
        \"roles_configured\": list(ROLES.keys())
    }

if __name__ == \"__main__\":
    import uvicorn
    uvicorn.run(app, host=\"0.0.0.0\", port=8007)