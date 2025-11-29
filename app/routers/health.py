"""
Health Check Endpoints
Provides health and readiness checks for the application
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.db_adapter import get_db_adapter
from app.services.firebase_auth import firebase_auth_service
import os

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "ChatterFix CMMS",
        "version": "2.0.0",
        "database": get_db_adapter().db_type,
        "environment": "production" if os.getenv("USE_FIRESTORE") == "true" else "development"
    })

@router.get("/readiness")
async def readiness_check():
    """Readiness check that validates dependencies"""
    health_status = {
        "status": "ready",
        "checks": {}
    }
    
    try:
        # Check database adapter
        db = get_db_adapter()
        health_status["checks"]["database"] = {
            "status": "ok",
            "type": db.db_type
        }
    except Exception as e:
        health_status["status"] = "not_ready"
        health_status["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        # Check Firebase if enabled
        if os.getenv("USE_FIRESTORE") == "true":
            if firebase_auth_service.app:
                health_status["checks"]["firebase"] = {"status": "ok"}
            else:
                health_status["checks"]["firebase"] = {"status": "not_initialized"}
        else:
            health_status["checks"]["firebase"] = {"status": "disabled"}
    except Exception as e:
        health_status["status"] = "not_ready"
        health_status["checks"]["firebase"] = {
            "status": "error",
            "error": str(e)
        }
    
    status_code = 200 if health_status["status"] == "ready" else 503
    return JSONResponse(health_status, status_code=status_code)

@router.get("/liveness")
async def liveness_check():
    """Liveness check - simple response to show app is running"""
    return JSONResponse({"status": "alive", "timestamp": "2024-11-28T16:00:00Z"})