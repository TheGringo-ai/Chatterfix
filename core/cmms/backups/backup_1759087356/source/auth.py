#!/usr/bin/env python3
"""
Enterprise Authentication and RBAC System for ChatterFix CMMS
JWT-based authentication with role-based access control
"""

import jwt
import bcrypt
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

# User roles and permissions
ROLES = {
    "admin": {
        "permissions": ["all"],
        "description": "Full system access"
    },
    "manager": {
        "permissions": [
            "work_orders:read", "work_orders:write", "work_orders:delete",
            "assets:read", "assets:write", "assets:delete",
            "parts:read", "parts:write", "parts:delete",
            "reports:read", "users:read"
        ],
        "description": "Manager access with reporting"
    },
    "technician": {
        "permissions": [
            "work_orders:read", "work_orders:write",
            "assets:read", "assets:write",
            "parts:read", "parts:write"
        ],
        "description": "Field technician access"
    },
    "viewer": {
        "permissions": [
            "work_orders:read", "assets:read", "parts:read"
        ],
        "description": "Read-only access"
    }
}

class AuthManager:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialize authentication tables"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT TRUE,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                department TEXT,
                full_name TEXT
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token_hash TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create default admin user if none exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        if cursor.fetchone()[0] == 0:
            admin_password = self.hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name, department)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("admin", "admin@chatterfix.com", admin_password, "admin", "System Administrator", "IT"))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, email: str, password: str, role: str = "viewer", 
                   full_name: str = "", department: str = "") -> Dict:
        """Create a new user"""
        if role not in ROLES:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name, department)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, email, password_hash, role, full_name, department))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {
                "id": user_id,
                "username": username,
                "email": email,
                "role": role,
                "full_name": full_name,
                "department": department
            }
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, full_name, department, is_active
            FROM users WHERE username = ? OR email = ?
        """, (username, username))
        
        user = cursor.fetchone()
        
        if user and user[7] and self.verify_password(password, user[3]):  # is_active and password check
            # Update last login
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                         (datetime.now(), user[0]))
            conn.commit()
            
            conn.close()
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "role": user[4],
                "full_name": user[5],
                "department": user[6]
            }
        
        conn.close()
        return None
    
    def create_access_token(self, user_data: Dict) -> str:
        """Create a JWT access token"""
        expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        token_data = {
            "user_id": user_data["id"],
            "username": user_data["username"],
            "role": user_data["role"],
            "exp": expiration
        }
        
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # Store session in database
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO user_sessions (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
        """, (user_data["id"], token_hash, expiration))
        
        conn.commit()
        conn.close()
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def has_permission(self, user_role: str, permission: str) -> bool:
        """Check if a user role has a specific permission"""
        if user_role not in ROLES:
            return False
        
        role_permissions = ROLES[user_role]["permissions"]
        
        # Admin has all permissions
        if "all" in role_permissions:
            return True
        
        return permission in role_permissions
    
    def log_action(self, user_id: int, action: str, resource: str, 
                  resource_id: str = None, details: str = None, ip_address: str = None):
        """Log user action for audit trail"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, resource, resource_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, resource, resource_id, details, ip_address))
        
        conn.commit()
        conn.close()

# Dependency functions for FastAPI
def get_auth_manager() -> AuthManager:
    """Dependency to get auth manager instance"""
    database_path = os.getenv("DATABASE_PATH", "/tmp/cmms.db")
    return AuthManager(database_path)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: AuthManager = Depends(get_auth_manager)
) -> Dict:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    # Get full user data
    conn = sqlite3.connect(auth_manager.database_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, role, full_name, department, is_active
        FROM users WHERE id = ?
    """, (payload["user_id"],))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user or not user[6]:  # User not found or inactive
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "role": user[3],
        "full_name": user[4],
        "department": user[5]
    }

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_dependency(
        current_user: Dict = Depends(get_current_user),
        auth_manager: AuthManager = Depends(get_auth_manager)
    ):
        if not auth_manager.has_permission(current_user["role"], permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    
    return permission_dependency

def require_role(required_role: str):
    """Decorator to require specific role"""
    def role_dependency(current_user: Dict = Depends(get_current_user)):
        if current_user["role"] != required_role and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required role: {required_role}"
            )
        return current_user
    
    return role_dependency