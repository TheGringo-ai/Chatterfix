import os
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Read version from VERSION.txt
APP_VERSION = "unknown"
try:
    version_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "VERSION.txt"
    )
    with open(version_file, "r") as f:
        APP_VERSION = f.readline().strip()
except Exception as e:
    # Log warning if VERSION.txt is missing (indicates deployment issue)
    import logging

    logging.warning(f"Could not read VERSION.txt: {e}. Using 'unknown' as version.")
    APP_VERSION = "unknown"


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
                "ai_team_config": {
                    "DISABLE_AI_TEAM_GRPC": os.getenv("DISABLE_AI_TEAM_GRPC"),
                    "AI_TEAM_SERVICE_URL": os.getenv("AI_TEAM_SERVICE_URL"),
                    "INTERNAL_API_KEY": os.getenv("INTERNAL_API_KEY", "not_set")[:10] + "..." if os.getenv("INTERNAL_API_KEY") else None,
                    "USE_AI_TEAM_HTTP": os.getenv("AI_TEAM_SERVICE_URL") is not None,
                }
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
