
#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
from typing import Optional, List
import logging
from datetime import datetime

app = FastAPI(title="ChatterFix Secure Work Orders Service", version="1.0.0")
security = HTTPBearer()

class SecurityContext:
    def __init__(self, user_id: str, tenant_id: str, roles: List[str]):
        self.user_id = user_id
        self.tenant_id = tenant_id  
        self.roles = roles
        
    def has_permission(self, permission: str) -> bool:
        # Enterprise RBAC permission checking
        permission_map = {
            "work_orders:read": ["technician", "supervisor", "admin"],
            "work_orders:write": ["technician", "supervisor", "admin"], 
            "work_orders:delete": ["supervisor", "admin"],
            "work_orders:admin": ["admin"]
        }
        
        required_roles = permission_map.get(permission, [])
        return any(role in self.roles for role in required_roles)

async def get_security_context(credentials: HTTPAuthorizationCredentials = Security(security)) -> SecurityContext:
    # Verify token with auth service
    auth_response = await verify_with_auth_service(credentials.credentials)
    if not auth_response:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    return SecurityContext(
        user_id=auth_response["user_id"],
        tenant_id=auth_response["tenant_id"],
        roles=auth_response["roles"]
    )

@app.get("/api/work_orders")
async def get_work_orders(
    status: Optional[str] = None,
    security_ctx: SecurityContext = Depends(get_security_context)
):
    if not security_ctx.has_permission("work_orders:read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Tenant-isolated query with row-level security
    async with asyncpg.connect(DATABASE_URL) as conn:
        query = '''
            SELECT * FROM work_orders 
            WHERE tenant_id = $1
            AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
        '''
        
        results = await conn.fetch(query, security_ctx.tenant_id, status)
        
        # Audit logging
        await log_data_access(
            user_id=security_ctx.user_id,
            tenant_id=security_ctx.tenant_id,
            action="work_orders:read",
            resource_count=len(results)
        )
        
        return {"success": True, "work_orders": results}

async def log_data_access(user_id: str, tenant_id: str, action: str, resource_count: int):
    # Enterprise audit logging
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "tenant_id": tenant_id, 
        "action": action,
        "resource_count": resource_count,
        "ip_address": "request.client.host"  # Get from request context
    }
    
    # Log to audit system (e.g., ELK stack)
    logging.info(f"AUDIT: {json.dumps(audit_entry)}")
