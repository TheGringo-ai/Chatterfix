import os
import psutil
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
import httpx

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
    """Basic health check endpoint for load balancers"""
    return JSONResponse({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check endpoint for monitoring and diagnostics"""
    start_time = time.time()
    health_data: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chatterfix-cmms",
        "version": APP_VERSION,
    }
    
    try:
        # System metrics
        health_data["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
        }
        
        # Database connectivity
        health_data["database"] = await check_database_health()
        
        # AI Team service connectivity
        health_data["ai_team"] = await check_ai_team_health()
        
        # Application health
        health_data["application"] = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "port": os.getenv("PORT", "8080"),
            "workers": os.getenv("WEB_CONCURRENCY", "1"),
        }
        
        # Response time
        health_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        # Determine overall status
        issues = []
        if health_data["system"]["memory_percent"] > 90:
            issues.append("high_memory_usage")
        if health_data["system"]["cpu_percent"] > 95:
            issues.append("high_cpu_usage")
        if health_data["database"]["status"] == "error":
            issues.append("database_connection_failed")
        if health_data["ai_team"]["status"] == "error":
            issues.append("ai_team_connection_failed")
            
        if issues:
            health_data["status"] = "degraded"
            health_data["issues"] = issues
            return JSONResponse(status_code=207, content=health_data)  # 207 Multi-Status
            
        return JSONResponse(content=health_data)
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
            }
        )


@router.get("/health/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    try:
        # Check critical dependencies
        db_health = await check_database_health()
        
        if db_health["status"] == "error":
            return JSONResponse(
                status_code=503,
                content={
                    "ready": False,
                    "reason": "database_unavailable",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        
        return JSONResponse({"ready": True, "timestamp": datetime.utcnow().isoformat()})
        
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "reason": "service_error",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return JSONResponse({"alive": True, "timestamp": datetime.utcnow().isoformat()})


@router.get("/health/environment")
async def environment_info():
    """
    Get current environment information

    Clearly shows if you're on DEV or PROD
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    # Determine environment type
    is_production = env == "production"
    is_dev = env in ["development", "dev", "staging"]

    # Get service info
    service_url = os.getenv("K_SERVICE", "unknown")
    revision = os.getenv("K_REVISION", "unknown")

    env_info = {
        "environment": env,
        "is_production": is_production,
        "is_development": is_dev,
        "service": service_url,
        "revision": revision,
        "version": APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if is_production:
        env_info["banner"] = "🚀 PRODUCTION - chatterfix.com"
        env_info["warning"] = "Changes here affect real users!"
        env_info["urls"] = {
            "main": "https://chatterfix.com",
            "demo": "https://chatterfix.com/demo"
        }
    else:
        env_info["banner"] = "🧪 DEVELOPMENT - Testing Environment"
        env_info["info"] = "Safe to test - does not affect production"
        env_info["urls"] = {
            "main": "https://gringo-core-650169261019.us-central1.run.app",
            "demo": "https://gringo-core-650169261019.us-central1.run.app/demo"
        }
        env_info["promote_command"] = "./scripts/deploy-prod.sh"

    return JSONResponse(env_info)


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity"""
    db_info = {
        "status": "unknown",
        "type": "none",
        "response_time_ms": None,
    }
    
    start_time = time.time()
    try:
        if os.getenv("USE_FIRESTORE", "false").lower() == "true":
            # Firestore health check
            from app.core.db_adapter import get_db_adapter
            
            db_adapter = get_db_adapter()
            # Simple test to verify connection
            await db_adapter.get_all_work_orders()  # This will test the connection
            
            db_info["status"] = "ok"
            db_info["type"] = "firestore"
        else:
            # SQLite health check
            db_info["status"] = "ok" 
            db_info["type"] = "sqlite_disabled"
            
        db_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
    except Exception as e:
        db_info["status"] = "error"
        db_info["error"] = str(e)
        db_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return db_info


async def check_ai_team_health() -> Dict[str, Any]:
    """Check AI Team service connectivity"""
    ai_info = {
        "status": "unknown", 
        "service_url": None,
        "response_time_ms": None,
        "grpc_disabled": os.getenv("DISABLE_AI_TEAM_GRPC", "true").lower() == "true",
    }
    
    ai_service_url = os.getenv("AI_TEAM_SERVICE_URL")
    
    if not ai_service_url:
        ai_info["status"] = "disabled"
        ai_info["reason"] = "no_service_url_configured"
        return ai_info
    
    ai_info["service_url"] = ai_service_url
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ai_service_url}/health")
            ai_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                ai_info["status"] = "ok"
                ai_info["service_response"] = response.json()
            else:
                ai_info["status"] = "error"
                ai_info["error"] = f"HTTP {response.status_code}"
                
    except Exception as e:
        ai_info["status"] = "error"
        ai_info["error"] = str(e)
        ai_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return ai_info
