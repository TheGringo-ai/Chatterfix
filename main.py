import os
import logging
from dotenv import load_dotenv

# Load environment variables (override system defaults)
load_dotenv(override=True)

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
)

# Initialize FastAPI application
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
        logger.info("🌐 ChatterFix ready for use!")
        logger.info("📊 Analytics dashboard: /analytics/dashboard")
        logger.info("🔌 IoT API: /iot/sensors/")

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
    description="AI-Powered Maintenance Management System",
    version="1.0.0",
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
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include all routers
app.include_router(health.router)  # Health checks (no prefix)
app.include_router(dashboard.router)  # Dashboard is now the main landing page
app.include_router(landing.router)  # Landing page becomes signup page
app.include_router(demo.router)  # Demo routes for app exploration
app.include_router(auth.router)
app.include_router(signup.router)
app.include_router(settings.router)
app.include_router(work_orders.router)
app.include_router(assets.router)
app.include_router(inventory.router)
app.include_router(team.router)
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


# Simple test endpoint to verify deployment
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify deployment works"""
    return {
        "status": "success",
        "message": "ChatterFix is running!",
        "timestamp": "2025-11-30",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "port": os.getenv("PORT", "unknown"),
    }


# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("CMMS_PORT", "8000")))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
