import os
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Read version from VERSION.txt
try:
    with open("VERSION.txt", "r") as f:
        APP_VERSION = f.readline().strip()
except Exception:
    APP_VERSION = "2.2.0-interactive-planner"


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        db_status = "ok"
        try:
            if os.getenv("USE_FIRESTORE", "false").lower() == "true":
                # Firestore health check
                from app.core.db_adapter import get_db_adapter

                get_db_adapter()
                db_status = "firestore_ok"
            else:
                # SQLite health check
                db_status = "sqlite_disabled"
        except Exception:
            db_status = "error"

        return JSONResponse(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_status,
                "version": APP_VERSION,
                "service": "chatterfix-cmms",
            }
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Service unavailable",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
