import os
import logging
from dotenv import load_dotenv

# Load environment variables (override system defaults)
load_dotenv(override=True)

print("DEBUG: STARTING NEW VERSION WITH FIX - 2025-12-05")

# Define version information immediately to avoid circular import issues
APP_VERSION = "2.1.0-enterprise-planner"
APP_DESCRIPTION = "Enhanced Demo Planner with Advanced Scheduler"

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.db_adapter import get_db_adapter

# Configure logging (Cloud Run friendly)
try:
    os.makedirs("logs", exist_ok=True)
    handlers = [logging.FileHandler("logs/chatterfix.log"), logging.StreamHandler()]
except (OSError, PermissionError):
    # Fallback for Cloud Run where we can't write files
    handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers,
)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Import all routers
from app.routers import (
    ai,
    ar,
    assets,
    auth,
    dashboard,
    demo,
    feedback,
    geolocation,
    health,
    inventory,
    landing,
    manager,
    onboarding,
    planner,
    purchasing,
    settings,
    signup,
    team,
    training,
    work_orders,
    analytics,
    iot,
    push,
    media,
    public_demo,
)

# Initialize FastAPI application
# Load version information first
def load_version():
    """Load version from VERSION.txt file"""
    import os
    version_paths = ["VERSION.txt", "/app/VERSION.txt", "./VERSION.txt"]
    
    for path in version_paths:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    lines = f.readlines()
                    version = lines[0].strip()
                    description = lines[1].strip() if len(lines) > 1 else "ChatterFix CMMS"
                    return version, description
        except Exception as e:
            continue
    
    # Fallback to hardcoded version if file not found
    return "2.1.0-enterprise-planner", "Enhanced Demo Planner with Advanced Scheduler"

print(f"DEBUG: main.py loaded. Version: {APP_VERSION}")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown"""
    # Startup
    try:
        logger.info("🚀 Starting ChatterFix CMMS...")

        # Initialize database adapter
        db_adapter = get_db_adapter()
        logger.info(f"📊 Database initialized ({db_adapter.db_type})")

        if db_adapter.db_type == "firestore":
            logger.info("🔥 Firebase/Firestore configured and ready")
            logger.info("✅ No SQLite dependencies - running on GCP")
        else:
            logger.warning("📁 Running in fallback SQLite mode")
            logger.warning("   For production, configure Firebase credentials")

        logger.info("✅ ChatterFix CMMS started successfully!")
        
        # Load version info for logging
        app_version, app_description = load_version()
        logger.info(f"📦 Version: {app_version}")
        logger.info(f"📋 Features: {app_description}")
        logger.info("🌐 ChatterFix ready for use!")
        logger.info("📊 Analytics dashboard: /analytics/dashboard")
        logger.info("🔌 IoT API: /iot/sensors/")
        logger.info("🎯 Enterprise Planner: /demo/planner")
        logger.info("⚙️ Advanced Scheduler: /planner/advanced")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start ChatterFix CMMS: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down ChatterFix CMMS...")
        logger.info("✅ ChatterFix CMMS shutdown complete")

app = FastAPI(
    title="ChatterFix CMMS API",
    description=f"AI-Powered Maintenance Management System - {APP_DESCRIPTION}",
    version=APP_VERSION,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["chatterfix.com", "*.chatterfix.com"]
    )

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files
app_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(app_dir, "app", "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"✅ Static files mounted from {static_dir}")
else:
    logger.error(f"❌ Static directory not found at {static_dir}")

@app.get("/debug/routes")
async def debug_routes():
    """List all registered routes for debugging"""
    routes = []
    for route in app.routes:
        routes.append({
            "name": getattr(route, "name", None),
            "path": getattr(route, "path", None),
            "methods": list(getattr(route, "methods", [])) if hasattr(route, "methods") else None
        })
    return {
        "routes": routes,
        "static_dir": static_dir,
        "static_exists": os.path.isdir(static_dir),
        "cwd": os.getcwd()
    }

# Include all routers
app.include_router(health.router)  # Health checks (no prefix)
app.include_router(dashboard.router)  # Dashboard is now the main landing page
app.include_router(landing.router)  # Landing page becomes signup page
app.include_router(public_demo.router)  # Public demo routes (no auth required)
app.include_router(demo.router)  # Demo routes for app exploration
app.include_router(auth.router)
app.include_router(signup.router)
app.include_router(settings.router)
app.include_router(work_orders.router)
app.include_router(assets.router)
app.include_router(inventory.router)
app.include_router(team.router)
app.include_router(manager.router)  # Manager Dashboard - Complete Control Center
app.include_router(training.router)
app.include_router(purchasing.router)
app.include_router(planner.router)
app.include_router(feedback.router)
app.include_router(ai.router)
app.include_router(ar.router)
app.include_router(geolocation.router)
app.include_router(onboarding.router)
app.include_router(analytics.router)  # Advanced analytics dashboard
app.include_router(iot.router)  # IoT sensor integration
app.include_router(push.router)  # Push notifications
app.include_router(media.router)  # Media upload and barcode functionality


# Root endpoint - redirect to landing page
@app.get("/")
async def root():
    """Root endpoint - redirect to landing page"""
    return RedirectResponse(url="/landing", status_code=302)


# Simple test endpoint to verify deployment
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify deployment works"""
    return {
        "status": "success",
        "message": "ChatterFix is running!",
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "timestamp": "2025-12-04",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "port": os.getenv("PORT", "unknown"),
        "database": "Firebase/Firestore",
        "features": [
            "Enterprise Planner",
            "Advanced Scheduler", 
            "AI Optimization",
            "Mobile Interface",
            "Parts Management",
            "PM Automation"
        ]
    }


@app.get("/debug/version")
async def debug_version():
    """Debug endpoint to check version loading"""
    import os
    debug_info = {
        "app_version": APP_VERSION,
        "app_description": APP_DESCRIPTION,
        "current_working_directory": os.getcwd(),
        "version_file_checks": {}
    }
    
    version_paths = ["VERSION.txt", "/app/VERSION.txt", "./VERSION.txt"]
    for path in version_paths:
        debug_info["version_file_checks"][path] = {
            "exists": os.path.exists(path),
            "is_file": os.path.isfile(path) if os.path.exists(path) else False
        }
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    debug_info["version_file_checks"][path]["content_preview"] = f.read()[:200]
            except Exception as e:
                debug_info["version_file_checks"][path]["error"] = str(e)
    
    return debug_info


# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("CMMS_PORT", "8000")))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, log_level="info")
