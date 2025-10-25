"""
Shared utilities and configurations for all CMMS modules
"""

import os
import logging
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Header, Depends
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
GCS_BUCKET = os.getenv("GCS_BUCKET", "chatterfix-attachments")
GCS_SIGNED_URL_TTL = int(os.getenv("GCS_SIGNED_URL_TTL", "900"))
CHATTERFIX_API_KEY = os.getenv("CHATTERFIX_API_KEY")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# GCS client (shared across modules)
try:
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(GCS_BUCKET)
except Exception as e:
    logger.warning(f"GCS not configured: {e}")
    gcs_client = None
    bucket = None

# Security Functions
async def verify_api_key(x_api_key: str = Header(..., description="ChatterFix API Key")):
    """
    Verify the API key from the x-api-key header
    Raises 401 if key is missing or invalid
    """
    if not CHATTERFIX_API_KEY:
        logger.warning("CHATTERFIX_API_KEY not configured - allowing unauthenticated access")
        return True
    
    if not x_api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include 'x-api-key' header.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if x_api_key != CHATTERFIX_API_KEY:
        logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return True

def get_health_status():
    """Get shared health status"""
    db_status = "configured" if DATABASE_URL else "not_configured"
    gcs_status = "connected" if gcs_client else "disconnected"
    api_key_status = "configured" if CHATTERFIX_API_KEY else "not_configured"
    
    return {
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "storage": gcs_status,
        "api_key": api_key_status,
        "security": "enabled" if CHATTERFIX_API_KEY else "disabled"
    }

# Common response patterns
def success_response(message: str, data: dict = None):
    """Standard success response"""
    response = {"success": True, "message": message}
    if data:
        response.update(data)
    return response

def error_response(message: str, details: str = None):
    """Standard error response"""
    response = {"success": False, "error": message}
    if details:
        response["details"] = details
    return response