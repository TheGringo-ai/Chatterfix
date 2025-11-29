from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import sqlite3
from datetime import datetime

router = APIRouter()

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
                db_adapter = get_db_adapter()
                db_status = "firestore_ok"
            else:
                # SQLite health check
                conn = sqlite3.connect("./data/cmms.db")
                conn.execute("SELECT 1")
                conn.close()
                db_status = "sqlite_ok"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "2.0.0",
            "service": "chatterfix-cmms"
        })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
