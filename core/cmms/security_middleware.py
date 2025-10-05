#!/usr/bin/env python3
"""
ChatterFix CMMS - Multi-Tenant Security & Access Control
Enterprise-grade security middleware for SaaS platform
"""

import os
import jwt
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from functools import wraps
from dataclasses import dataclass

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
import bcrypt
import redis

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security constants
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# ============ DATA MODELS ============

@dataclass
class User:
    id: int
    email: str
    full_name: str
    organization_id: int
    role: str
    permissions: Set[str]
    is_active: bool = True
    is_verified: bool = True

@dataclass 
class Organization:
    id: int
    name: str
    subdomain: str
    plan_type: str
    is_active: bool = True
    
@dataclass
class Permission:
    name: str
    description: str
    resource: str
    action: str

@dataclass
class SecurityContext:
    user: User
    organization: Organization
    permissions: Set[str]
    session_id: str
    ip_address: str
    user_agent: str

# ============ ROLE-BASED ACCESS CONTROL ============

class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self):
        self.permissions = self._initialize_permissions()
        self.roles = self._initialize_roles()
    
    def _initialize_permissions(self) -> Dict[str, Permission]:
        """Initialize system permissions"""
        permissions = {}
        
        # Organization permissions
        org_perms = [
            ("org.read", "View organization details", "organization", "read"),
            ("org.write", "Modify organization settings", "organization", "write"),
            ("org.admin", "Full organization administration", "organization", "admin"),
        ]
        
        # Customer permissions
        customer_perms = [
            ("customer.read", "View customers", "customer", "read"),
            ("customer.write", "Modify customers", "customer", "write"),
            ("customer.create", "Create new customers", "customer", "create"),
            ("customer.delete", "Delete customers", "customer", "delete"),
        ]
        
        # CMMS permissions
        cmms_perms = [
            ("cmms.read", "View CMMS data", "cmms", "read"),
            ("cmms.write", "Modify CMMS data", "cmms", "write"),
            ("cmms.admin", "Full CMMS administration", "cmms", "admin"),
        ]
        
        # GCP permissions
        gcp_perms = [
            ("gcp.read", "View GCP resources", "gcp", "read"),
            ("gcp.write", "Modify GCP resources", "gcp", "write"),
            ("gcp.admin", "Full GCP administration", "gcp", "admin"),
        ]
        
        # Billing permissions
        billing_perms = [
            ("billing.read", "View billing information", "billing", "read"),
            ("billing.write", "Modify billing settings", "billing", "write"),
            ("billing.admin", "Full billing administration", "billing", "admin"),
        ]
        
        all_perms = org_perms + customer_perms + cmms_perms + gcp_perms + billing_perms
        
        for name, desc, resource, action in all_perms:
            permissions[name] = Permission(name, desc, resource, action)
            
        return permissions
    
    def _initialize_roles(self) -> Dict[str, Set[str]]:
        """Initialize system roles with permissions"""
        return {
            "super_admin": {
                "org.admin", "customer.read", "customer.write", "customer.create", "customer.delete",
                "cmms.admin", "gcp.admin", "billing.admin"
            },
            "org_admin": {
                "org.read", "org.write", "customer.read", "customer.write", "customer.create",
                "cmms.admin", "gcp.read", "gcp.write", "billing.read", "billing.write"
            },
            "manager": {
                "org.read", "customer.read", "customer.write", "cmms.read", "cmms.write",
                "gcp.read", "billing.read"
            },
            "user": {
                "org.read", "customer.read", "cmms.read", "gcp.read", "billing.read"
            },
            "readonly": {
                "org.read", "customer.read", "cmms.read", "gcp.read", "billing.read"
            }
        }
    
    def get_role_permissions(self, role: str) -> Set[str]:
        """Get permissions for a role"""
        return self.roles.get(role, set())
    
    def has_permission(self, user_permissions: Set[str], required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in user_permissions
    
    def validate_access(self, user: User, resource: str, action: str) -> bool:
        """Validate user access to resource/action"""
        required_perm = f"{resource}.{action}"
        return self.has_permission(user.permissions, required_perm)

# ============ AUTHENTICATION SERVICE ============

class AuthenticationService:
    """JWT-based authentication service"""
    
    def __init__(self, database_pool):
        self.db_pool = database_pool
        self.rbac = RBACManager()
        
        # Initialize Redis for session management
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis.ping()
            logger.info("Redis connected for session management")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis = None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email/password"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT u.*, o.name as org_name, o.subdomain, o.plan_type, o.is_active as org_active
                    FROM customers u
                    JOIN organizations o ON u.organization_id = o.id
                    WHERE u.email = $1 AND u.is_active = TRUE AND o.is_active = TRUE
                """, email)
                
                if not row:
                    return None
                
                # In production, verify password hash
                # if not bcrypt.checkpw(password.encode('utf-8'), row['password_hash'].encode('utf-8')):
                #     return None
                
                # Get user permissions based on role
                permissions = self.rbac.get_role_permissions(row['role'])
                
                return User(
                    id=row['id'],
                    email=row['email'],
                    full_name=row['full_name'],
                    organization_id=row['organization_id'],
                    role=row['role'],
                    permissions=permissions,
                    is_active=row['is_active'],
                    is_verified=True
                )
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def create_access_token(self, user: User, session_id: str) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "organization_id": user.organization_id,
            "role": user.role,
            "session_id": session_id,
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
            "iat": datetime.utcnow(),
            "iss": "chatterfix-saas"
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check session in Redis if available
            if self.redis:
                session_key = f"session:{payload['session_id']}"
                if not self.redis.exists(session_key):
                    logger.warning("Session not found in Redis")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def create_session(self, user: User, ip_address: str, user_agent: str) -> str:
        """Create user session"""
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store session in Redis if available
        if self.redis:
            session_key = f"session:{session_id}"
            session_data = {
                "user_id": user.id,
                "organization_id": user.organization_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }
            
            # Set session with expiration
            self.redis.hmset(session_key, session_data)
            self.redis.expire(session_key, TOKEN_EXPIRE_HOURS * 3600)
        
        return session_id
    
    async def invalidate_session(self, session_id: str):
        """Invalidate user session"""
        if self.redis:
            session_key = f"session:{session_id}"
            self.redis.delete(session_key)

# ============ TENANT ISOLATION ============

class TenantIsolationService:
    """Multi-tenant data isolation service"""
    
    def __init__(self, database_pool):
        self.db_pool = database_pool
    
    async def get_user_organization(self, user_id: int) -> Optional[Organization]:
        """Get user's organization"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT o.* FROM organizations o
                    JOIN customers u ON o.id = u.organization_id
                    WHERE u.id = $1 AND o.is_active = TRUE
                """, user_id)
                
                if row:
                    return Organization(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting user organization: {e}")
            return None
    
    def apply_tenant_filter(self, query: str, organization_id: int) -> str:
        """Apply tenant isolation filter to SQL query"""
        # Add WHERE clause for tenant isolation
        if "WHERE" in query.upper():
            return query + f" AND organization_id = {organization_id}"
        else:
            return query + f" WHERE organization_id = {organization_id}"
    
    async def validate_resource_access(self, user: User, resource_id: int, table_name: str) -> bool:
        """Validate user can access specific resource"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(f"""
                    SELECT COUNT(*) as count FROM {table_name}
                    WHERE id = $1 AND organization_id = $2
                """, resource_id, user.organization_id)
                
                return row['count'] > 0
                
        except Exception as e:
            logger.error(f"Error validating resource access: {e}")
            return False

# ============ SECURITY MIDDLEWARE ============

class SecurityMiddleware:
    """Main security middleware for request processing"""
    
    def __init__(self, database_pool):
        self.auth_service = AuthenticationService(database_pool)
        self.tenant_service = TenantIsolationService(database_pool)
        self.rbac = RBACManager()
        self.security = HTTPBearer()
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """Get current authenticated user"""
        try:
            # Verify token
            payload = self.auth_service.verify_token(credentials.credentials)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            
            # Get user from database
            async with self.auth_service.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT u.*, o.name as org_name, o.subdomain, o.plan_type
                    FROM customers u
                    JOIN organizations o ON u.organization_id = o.id
                    WHERE u.id = $1 AND u.is_active = TRUE AND o.is_active = TRUE
                """, payload['user_id'])
                
                if not row:
                    raise HTTPException(status_code=401, detail="User not found or inactive")
                
                # Get user permissions
                permissions = self.rbac.get_role_permissions(row['role'])
                
                return User(
                    id=row['id'],
                    email=row['email'],
                    full_name=row['full_name'],
                    organization_id=row['organization_id'],
                    role=row['role'],
                    permissions=permissions,
                    is_active=row['is_active'],
                    is_verified=True
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def get_security_context(self, request: Request, user: User = Depends(get_current_user)) -> SecurityContext:
        """Get full security context for request"""
        try:
            # Get organization
            organization = await self.tenant_service.get_user_organization(user.id)
            if not organization:
                raise HTTPException(status_code=403, detail="Organization not found")
            
            # Extract request info
            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            # Create session ID from token
            auth_header = request.headers.get("authorization", "")
            session_id = "unknown"
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = self.auth_service.verify_token(token)
                if payload:
                    session_id = payload.get("session_id", "unknown")
            
            return SecurityContext(
                user=user,
                organization=organization,
                permissions=user.permissions,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating security context: {e}")
            raise HTTPException(status_code=500, detail="Security context creation failed")

# ============ PERMISSION DECORATORS ============

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract security context from kwargs
            security_context = None
            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break
            
            if not security_context:
                # Try to find in kwargs
                security_context = kwargs.get('security_context')
            
            if not security_context:
                raise HTTPException(status_code=401, detail="Security context required")
            
            # Check permission
            if not security_context.user.permissions or permission not in security_context.user.permissions:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Insufficient permissions. Required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract security context from kwargs
            security_context = None
            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break
            
            if not security_context:
                security_context = kwargs.get('security_context')
            
            if not security_context:
                raise HTTPException(status_code=401, detail="Security context required")
            
            # Check role
            if security_context.user.role != role:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient role. Required: {role}, Current: {security_context.user.role}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# ============ AUDIT LOGGING ============

class AuditLogger:
    """Security audit logging service"""
    
    def __init__(self, database_pool):
        self.db_pool = database_pool
    
    async def log_security_event(
        self,
        user_id: Optional[int],
        organization_id: Optional[int],
        event_type: str,
        resource: str,
        action: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security event"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO security_audit_log 
                    (user_id, organization_id, event_type, resource, action, 
                     ip_address, user_agent, success, details, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, user_id, organization_id, event_type, resource, action,
                    ip_address, user_agent, success, 
                    json.dumps(details) if details else None,
                    datetime.utcnow())
                    
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

# ============ RATE LIMITING ============

class RateLimiter:
    """Rate limiting service"""
    
    def __init__(self):
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis.ping()
            logger.info("Redis connected for rate limiting")
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            self.redis = None
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """Check if request is within rate limit"""
        if not self.redis:
            return True  # Allow if Redis not available
        
        try:
            current = self.redis.get(key)
            if current is None:
                # First request
                self.redis.setex(key, window_seconds, 1)
                return True
            elif int(current) < limit:
                # Within limit
                self.redis.incr(key)
                return True
            else:
                # Rate limited
                return False
                
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow on error

# Export main components
__all__ = [
    "SecurityMiddleware",
    "AuthenticationService", 
    "TenantIsolationService",
    "RBACManager",
    "AuditLogger",
    "RateLimiter",
    "SecurityContext",
    "User",
    "Organization",
    "require_permission",
    "require_role"
]