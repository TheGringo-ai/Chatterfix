"""
Security utilities for AI Team Service
"""

import hashlib
import secrets
import time
from typing import Optional

from app.core.config import settings

def verify_api_key(api_key: str) -> bool:
    """Verify API key authentication"""
    if not api_key:
        return False
    
    # For now, use simple key comparison
    # In production, consider using JWT tokens or more sophisticated auth
    return api_key == settings.INTERNAL_API_KEY

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def create_request_id() -> str:
    """Create unique request ID for tracking"""
    timestamp = str(int(time.time() * 1000))
    random_suffix = secrets.token_hex(8)
    return f"ai-{timestamp}-{random_suffix}"

def hash_content(content: str) -> str:
    """Create hash of content for caching/deduplication"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]