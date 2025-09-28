#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Security and Rate Limiting Middleware
Enhanced security measures recommended by AI analysis
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import time
import asyncio
import logging
from collections import defaultdict, deque
import hashlib
import jwt
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation with sliding window"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = {}
        
    def is_allowed(self, identifier: str, limit: int = 100, window: int = 60) -> bool:
        """Check if request is allowed based on rate limit"""
        now = time.time()
        
        # Check if IP is temporarily blocked
        if identifier in self.blocked_ips:
            if now < self.blocked_ips[identifier]:
                return False
            else:
                del self.blocked_ips[identifier]
        
        # Clean old requests outside the window
        request_times = self.requests[identifier]
        while request_times and request_times[0] < now - window:
            request_times.popleft()
        
        # Check rate limit
        if len(request_times) >= limit:
            # Block IP for 5 minutes on rate limit exceeded
            self.blocked_ips[identifier] = now + 300
            logger.warning(f"Rate limit exceeded for {identifier}, blocked for 5 minutes")
            return False
        
        # Add current request
        request_times.append(now)
        return True

class SecurityValidator:
    """Enhanced security validation"""
    
    @staticmethod
    def validate_file_content(file_data: bytes, allowed_types: list) -> tuple[bool, str]:
        """Validate file content for security issues"""
        
        # Check for suspicious patterns in file content
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'data:text/html',
            b'<?php',
            b'<%',
            b'eval(',
            b'exec(',
            b'system(',
            b'passthru(',
            b'shell_exec(',
        ]
        
        file_lower = file_data.lower()
        for pattern in suspicious_patterns:
            if pattern in file_lower:
                return False, f"Suspicious content detected: {pattern.decode('utf-8', errors='ignore')}"
        
        # Check file size limits based on type
        max_sizes = {
            'image': 10 * 1024 * 1024,  # 10MB
            'audio': 50 * 1024 * 1024,  # 50MB
            'document': 5 * 1024 * 1024,  # 5MB
        }
        
        for file_type, max_size in max_sizes.items():
            if file_type in allowed_types and len(file_data) > max_size:
                return False, f"File too large for {file_type} type. Max: {max_size // (1024*1024)}MB"
        
        return True, "File content validated"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        import re
        
        # Remove path separators and special characters
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_filename = re.sub(r'\.\.+', '.', safe_filename)
        safe_filename = safe_filename.strip('. ')
        
        # Ensure filename is not empty
        if not safe_filename:
            safe_filename = f"file_{int(time.time())}"
        
        return safe_filename
    
    @staticmethod
    def validate_request_headers(request: Request) -> tuple[bool, str]:
        """Validate request headers for security"""
        
        # Check for common attack headers
        dangerous_headers = [
            'x-forwarded-host',
            'x-original-url',
            'x-rewrite-url',
        ]
        
        for header in dangerous_headers:
            if header in request.headers:
                logger.warning(f"Suspicious header detected: {header}")
        
        # Validate User-Agent
        user_agent = request.headers.get('user-agent', '')
        if not user_agent or len(user_agent) > 500:
            return False, "Invalid or missing User-Agent"
        
        # Check for suspicious User-Agent patterns
        suspicious_ua_patterns = [
            'sqlmap',
            'nikto',
            'nessus',
            'burp',
            'dirbuster',
            'gobuster',
        ]
        
        ua_lower = user_agent.lower()
        for pattern in suspicious_ua_patterns:
            if pattern in ua_lower:
                return False, f"Suspicious User-Agent: {pattern}"
        
        return True, "Headers validated"

class AuthenticationValidator:
    """Enhanced authentication validation"""
    
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "enterprise-cloudrun-secret-2024")
        self.security = HTTPBearer(auto_error=False)
    
    async def verify_token(self, credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[dict]:
        """Verify JWT token"""
        if not credentials:
            return None
        
        try:
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret,
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Global instances
rate_limiter = RateLimiter()
security_validator = SecurityValidator()
auth_validator = AuthenticationValidator()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    
    # Get client IP
    client_ip = request.client.host
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    # Define rate limits per endpoint type
    endpoint_limits = {
        '/api/media/upload/': (10, 60),  # 10 uploads per minute
        '/api/speech/': (20, 60),        # 20 speech requests per minute
        '/api/ocr/': (15, 60),           # 15 OCR requests per minute
        '/global-ai/': (30, 60),         # 30 AI requests per minute
        'default': (100, 60)             # 100 general requests per minute
    }
    
    # Find matching rate limit
    limit, window = endpoint_limits['default']
    for path_prefix, (path_limit, path_window) in endpoint_limits.items():
        if request.url.path.startswith(path_prefix):
            limit, window = path_limit, path_window
            break
    
    # Check rate limit
    identifier = f"{client_ip}:{request.url.path}"
    if not rate_limiter.is_allowed(identifier, limit, window):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {limit} requests per {window} seconds."
        )
    
    response = await call_next(request)
    return response

async def security_middleware(request: Request, call_next):
    """Security validation middleware"""
    
    # Validate request headers
    headers_valid, headers_message = security_validator.validate_request_headers(request)
    if not headers_valid:
        logger.warning(f"Security violation from {request.client.host}: {headers_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request headers"
        )
    
    # Add security headers to response
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response

def setup_security_middleware(app):
    """Setup security middleware on FastAPI app"""
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(security_middleware)
    logger.info("✅ Security middleware enabled")