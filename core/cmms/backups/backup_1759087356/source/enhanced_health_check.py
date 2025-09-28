# Enhanced Health Check for ChatterFix CMMS
# Drop this into your app.py to replace the basic /health endpoint

import sqlite3
import requests
from datetime import datetime
from fastapi import HTTPException
import os

# Health check configuration
DATABASE_PATH = "cmms.db"  # Adjust to your actual DB path
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"  # Adjust to your model

@app.get("/health")
def enhanced_health_check():
    """
    Comprehensive health check for deployment readiness validation.
    Returns 200 only when all critical components are operational.
    """
    health_status = {
        "status": "unknown",
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "deploy_id": os.environ.get("DEPLOY_ID", "unknown")
    }
    
    all_healthy = True
    
    # 1. Database connectivity check
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=2)
        cursor = conn.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        all_healthy = False
    
    # 2. Ollama service check
    try:
        # Check Ollama API is responding
        version_response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=3)
        version_ok = version_response.status_code == 200
        
        # Check required model is available
        tags_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if tags_response.status_code == 200:
            tags_data = tags_response.json()
            models = tags_data.get("models", [])
            has_model = any(
                model.get("name", "").startswith(OLLAMA_MODEL.split(":")[0]) 
                for model in models
            )
        else:
            has_model = False
        
        if version_ok and has_model:
            health_status["components"]["ollama"] = {
                "status": "healthy",
                "message": f"Ollama running with {OLLAMA_MODEL} model"
            }
        else:
            health_status["components"]["ollama"] = {
                "status": "degraded",
                "message": f"Ollama API: {version_ok}, Model {OLLAMA_MODEL}: {has_model}"
            }
            all_healthy = False
            
    except requests.exceptions.RequestException as e:
        health_status["components"]["ollama"] = {
            "status": "unhealthy",
            "error": f"Ollama connection failed: {str(e)}"
        }
        all_healthy = False
    
    # 3. Universal AI endpoints check
    try:
        # Quick self-test of AI injection endpoint
        ai_inject_response = requests.get("http://localhost:8000/ai-inject.js", timeout=2)
        ai_inject_ok = ai_inject_response.status_code == 200
        
        health_status["components"]["universal_ai"] = {
            "status": "healthy" if ai_inject_ok else "degraded",
            "ai_injection": ai_inject_ok
        }
        
        if not ai_inject_ok:
            all_healthy = False
            
    except Exception as e:
        health_status["components"]["universal_ai"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        all_healthy = False
    
    # 4. Memory and disk space checks
    try:
        import psutil
        
        # Memory check (warn if > 80% used)
        memory = psutil.virtual_memory()
        memory_ok = memory.percent < 80
        
        # Disk space check (warn if > 85% used)
        disk = psutil.disk_usage('/')
        disk_ok = (disk.used / disk.total) < 0.85
        
        health_status["components"]["resources"] = {
            "status": "healthy" if (memory_ok and disk_ok) else "warning",
            "memory_percent": memory.percent,
            "disk_percent": round((disk.used / disk.total) * 100, 1)
        }
        
    except ImportError:
        # psutil not available, skip resource checks
        health_status["components"]["resources"] = {
            "status": "unknown",
            "message": "Resource monitoring not available"
        }
    
    # Overall status
    health_status["status"] = "healthy" if all_healthy else "unhealthy"
    
    # Return appropriate HTTP status
    if all_healthy:
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)


# Readiness check - separate endpoint for Kubernetes-style readiness
@app.get("/ready")
def readiness_check():
    """
    Readiness probe - returns 200 when service is ready to accept traffic.
    More strict than health check.
    """
    try:
        # Test actual AI processing capability
        test_response = requests.post(
            "http://localhost:8000/global-ai/process-message",
            json={
                "message": "health check ping", 
                "page": "/health",
                "context": "readiness_probe"
            },
            timeout=5
        )
        
        if test_response.status_code == 200:
            return {"status": "ready", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(
                status_code=503, 
                detail={"status": "not_ready", "reason": "AI processing test failed"}
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "error": str(e)}
        )