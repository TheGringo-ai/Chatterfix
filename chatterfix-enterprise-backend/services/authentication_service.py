
#!/usr/bin/env python3
import os
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
import redis
import asyncpg
from pydantic import BaseModel

app = FastAPI(title="ChatterFix Authentication Service", version="1.0.0")
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enterprise security configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-super-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class UserAuth(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class EnterpriseAuthManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
    async def authenticate_user(self, username: str, password: str, tenant_id: str):
        # Enterprise authentication logic with tenant isolation
        async with asyncpg.connect(DATABASE_URL) as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE username = $1 AND tenant_id = $2 AND active = true",
                username, tenant_id
            )
            
            if user and pwd_context.verify(password, user['password_hash']):
                return user
            return None
    
    def create_access_token(self, user_data: dict):
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_data["username"],
            "tenant_id": user_data["tenant_id"],
            "roles": user_data["roles"],
            "exp": expire
        }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

auth_manager = EnterpriseAuthManager()

@app.post("/auth/login", response_model=TokenResponse)
async def login(auth_data: UserAuth, tenant_id: str):
    user = await auth_manager.authenticate_user(
        auth_data.username, auth_data.password, tenant_id
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth_manager.create_access_token(user)
    refresh_token = auth_manager.create_refresh_token(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/auth/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    payload = auth_manager.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True, "user": payload}
