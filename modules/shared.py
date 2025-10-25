"""
Shared utilities and configurations for all CMMS modules
"""

import os
import logging
from datetime import datetime
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
GCS_BUCKET = os.getenv("GCS_BUCKET", "chatterfix-attachments")
GCS_SIGNED_URL_TTL = int(os.getenv("GCS_SIGNED_URL_TTL", "900"))

# GCS client (shared across modules)
try:
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(GCS_BUCKET)
except Exception as e:
    logger.warning(f"GCS not configured: {e}")
    gcs_client = None
    bucket = None

def get_health_status():
    """Get shared health status"""
    db_status = "configured" if DATABASE_URL else "not_configured"
    gcs_status = "connected" if gcs_client else "disconnected"
    
    return {
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "storage": gcs_status
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