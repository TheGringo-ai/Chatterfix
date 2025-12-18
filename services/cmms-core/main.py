#!/usr/bin/env python3
"""
🏭 ChatterFix CMMS Core Microservice
Business application for Computerized Maintenance Management System
Integrates with AI Services microservice for intelligent features

Designed with AI Team collaboration for optimal separation of concerns
"""
import logging
import os
import sys
from contextlib import asynccontextmanager

import httpx

# Add project paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv

load_dotenv(override=True)

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Import CMMS core modules
from app.core.db_adapter import get_db_adapter
from app.middleware import ErrorTrackingMiddleware

logger = logging.getLogger(__name__)

# CMMS Core logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - 🏭 CMMS-CORE - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


# AI Services Integration Client
class AIServicesClient:
    """HTTP client for communicating with AI Services microservice"""

    def __init__(self, ai_services_url: str):
        self.ai_services_url = ai_services_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.connected = False

    async def health_check(self):
        """Check AI Services availability"""
        try:
            response = await self.client.get(f"{self.ai_services_url}/health")
            if response.status_code == 200:
                self.connected = True
                return response.json()
            return None
        except Exception as e:
            logger.warning(f"AI Services health check failed: {e}")
            self.connected = False
            return None

    async def get_service_info(self):
        """Get AI Services information"""
        try:
            response = await self.client.get(f"{self.ai_services_url}/ai-services-info")
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    async def process_unified_request(self, request_data: dict):
        """Send request to unified AI processing"""
        try:
            response = await self.client.post(
                f"{self.ai_services_url}/unified-ai/process", json=request_data
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Unified AI request failed: {e}")
            return None

    async def analyze_maintenance_issue(self, issue_data: dict):
        """Analyze maintenance issue with Fix it Fred"""
        try:
            # Transform CMMS format to Fix it Fred format
            fix_it_fred_request = {
                "issue_description": issue_data.get("description", ""),
                "severity": issue_data.get("priority", "medium"),
                "category": issue_data.get("category", "maintenance"),
                "system_context": f"Asset ID: {issue_data.get('asset_id', 'N/A')}, Work Order: {issue_data.get('work_order_id', 'N/A')}",
                "auto_apply": False,  # Always require manual review from CMMS
            }

            response = await self.client.post(
                f"{self.ai_services_url}/fix-it-fred/analyze", json=fix_it_fred_request
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Fix it Fred analysis failed: {e}")
            return None

    async def collaborate_with_ai_team(self, prompt: str, context: str = ""):
        """Get AI Team collaboration"""
        try:
            response = await self.client.post(
                f"{self.ai_services_url}/ai-team/execute",
                json={"prompt": prompt, "context": context},
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"AI Team collaboration failed: {e}")
            return None

    async def submit_training_data(self, training_data: dict):
        """Submit data to LineSmart for training"""
        try:
            response = await self.client.post(
                f"{self.ai_services_url}/linesmart/submit-training-data",
                json=training_data,
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"LineSmart training submission failed: {e}")
            return None


# Global AI Services client
ai_services_client = None


def get_ai_services_client() -> AIServicesClient:
    """Dependency to get AI Services client"""
    return ai_services_client


@asynccontextmanager
async def cmms_lifespan(app: FastAPI):
    """CMMS Core microservice lifecycle"""
    global ai_services_client

    logger.info("🏭 Starting ChatterFix CMMS Core Microservice...")
    logger.info("🎯 Designed with AI Team collaboration")

    # Initialize database
    try:
        db_adapter = get_db_adapter()
        logger.info(f"✅ Database initialized ({db_adapter.db_type})")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    # Initialize AI Services client
    ai_services_url = os.getenv("AI_SERVICES_URL", "http://localhost:8002")
    ai_services_client = AIServicesClient(ai_services_url)

    # Test AI Services connection
    ai_health = await ai_services_client.health_check()
    if ai_health and ai_health.get("healthy"):
        logger.info("✅ AI Services connected successfully")
        logger.info(f"🤖 AI Services: {ai_services_url}")

        # Get AI Services info
        ai_info = await ai_services_client.get_service_info()
        if ai_info:
            logger.info(f"🤖 AI Services version: {ai_info.get('version')}")
    else:
        logger.warning("⚠️  AI Services not available - running without AI features")
        logger.warning(f"   Attempted connection to: {ai_services_url}")

    logger.info("✅ ChatterFix CMMS Core ready!")
    logger.info("🌐 CMMS Application: localhost:8000")
    logger.info("📊 Dashboard: /dashboard")
    logger.info("🔧 Work Orders: /work-orders")
    logger.info("📦 Assets: /assets")
    logger.info("👥 Team: /team")
    logger.info("🤖 AI Integration: /ai/* endpoints")

    yield

    # Shutdown
    logger.info("🛑 Shutting down CMMS Core...")
    if ai_services_client:
        await ai_services_client.client.aclose()
    logger.info("✅ CMMS Core shutdown complete")


# Create CMMS Core app
app = FastAPI(
    title="ChatterFix CMMS Core",
    description="Computerized Maintenance Management System - Business Logic Service",
    version="2.0.0",
    lifespan=cmms_lifespan,
)

# Middleware
app.add_middleware(
    ErrorTrackingMiddleware,
    sentry_dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "development"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
static_dir = os.path.join(app_dir, "app", "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Import CMMS business routers only
try:
    from app.routers import (
        assets,
        auth,
        dashboard,
        demo,
        health,
        inventory,
        landing,
        planner,
        settings,
        signup,
        team,
        work_orders,
    )

    # Include business routers
    app.include_router(health.router)
    app.include_router(landing.router)
    app.include_router(dashboard.router)
    app.include_router(auth.router)
    app.include_router(signup.router)
    app.include_router(settings.router)
    app.include_router(demo.router)
    app.include_router(work_orders.router)
    app.include_router(assets.router)
    app.include_router(inventory.router)
    app.include_router(team.router)
    app.include_router(planner.router)

    logger.info("✅ CMMS business routers loaded")
    BUSINESS_ROUTERS_LOADED = True

except ImportError as e:
    logger.error(f"❌ Failed to load CMMS routers: {e}")
    BUSINESS_ROUTERS_LOADED = False


# CMMS Core endpoints
@app.get("/")
async def cmms_root():
    """CMMS root - redirect to dashboard"""
    if BUSINESS_ROUTERS_LOADED:
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        return {
            "service": "ChatterFix CMMS Core",
            "status": "operational",
            "message": "Business application for maintenance management",
        }


@app.get("/health")
async def cmms_health():
    """CMMS Core health check"""
    try:
        # Check database
        db_healthy = False
        try:
            db_adapter = get_db_adapter()
            db_healthy = True
        except Exception:
            pass

        # Check AI Services
        ai_health = (
            await ai_services_client.health_check() if ai_services_client else None
        )
        ai_connected = bool(ai_health and ai_health.get("healthy"))

        return {
            "healthy": db_healthy and BUSINESS_ROUTERS_LOADED,
            "service": "cmms-core",
            "version": "2.0.0",
            "port": 8000,
            "components": {
                "database": db_healthy,
                "business_routers": BUSINESS_ROUTERS_LOADED,
                "ai_services_integration": ai_connected,
                "static_files": os.path.isdir(static_dir),
            },
            "ai_services": {
                "connected": ai_connected,
                "url": os.getenv("AI_SERVICES_URL", "http://localhost:8002"),
                "status": (
                    ai_health.get("service", "unknown") if ai_health else "disconnected"
                ),
            },
            "business_features": [
                "work_orders",
                "assets",
                "inventory",
                "team_management",
                "preventive_maintenance",
                "dashboard",
                "analytics",
                "ai_integration",
            ],
        }

    except Exception as e:
        logger.error(f"CMMS health check failed: {e}")
        return {"healthy": False, "service": "cmms-core", "error": str(e)}


@app.get("/cmms-info")
async def cmms_service_info():
    """CMMS service information"""
    ai_health = await ai_services_client.health_check() if ai_services_client else None

    return {
        "service": "ChatterFix CMMS Core",
        "version": "2.0.0",
        "architecture": "microservice",
        "port": 8000,
        "description": "Business logic for maintenance management",
        "designed_with": "AI Team collaboration",
        "business_domains": {
            "maintenance": {
                "work_orders": "/work-orders",
                "assets": "/assets",
                "inventory": "/inventory",
                "preventive_maintenance": "/planner",
            },
            "operations": {
                "dashboard": "/dashboard",
                "analytics": "/analytics",
                "team": "/team",
            },
            "administration": {
                "auth": "/auth",
                "settings": "/settings",
                "users": "/signup",
            },
        },
        "ai_integration": {
            "status": (
                "connected"
                if ai_health and ai_health.get("healthy")
                else "disconnected"
            ),
            "ai_services_url": os.getenv("AI_SERVICES_URL", "http://localhost:8002"),
            "endpoints": ["/ai/*"],
            "capabilities": [
                "intelligent_analysis",
                "autonomous_repair",
                "predictive_maintenance",
            ],
        },
    }


# AI Integration endpoints (proxy to AI Services)
@app.post("/ai/analyze-issue")
async def analyze_maintenance_issue(
    issue_data: dict, ai_client: AIServicesClient = Depends(get_ai_services_client)
):
    """Analyze maintenance issue using AI Services"""
    if not ai_client or not ai_client.connected:
        raise HTTPException(status_code=503, detail="AI Services not available")

    # Add CMMS context
    enhanced_request = {
        "source": "cmms",
        "type": "maintenance_issue",
        "description": issue_data.get("description", ""),
        "priority": issue_data.get("priority", "medium"),
        "asset_id": issue_data.get("asset_id"),
        "work_order_id": issue_data.get("work_order_id"),
        "cmms_context": issue_data,
    }

    result = await ai_client.analyze_maintenance_issue(enhanced_request)

    if not result:
        raise HTTPException(status_code=503, detail="AI analysis failed")

    return {
        "source": "cmms_ai_integration",
        "analysis": result,
        "ai_recommendations": result.get("recommended_actions", []),
        "confidence": result.get("fix_confidence", 0),
        "estimated_time": result.get("estimated_time", "unknown"),
    }


@app.post("/ai/unified-process")
async def unified_ai_processing(
    request_data: dict, ai_client: AIServicesClient = Depends(get_ai_services_client)
):
    """Process request through unified AI system"""
    if not ai_client or not ai_client.connected:
        raise HTTPException(status_code=503, detail="AI Services not available")

    # Add CMMS context
    cmms_request = {"source": "cmms", "cmms_data": request_data, **request_data}

    result = await ai_client.process_unified_request(cmms_request)

    if not result:
        raise HTTPException(status_code=503, detail="Unified AI processing failed")

    return {
        "cmms_integration": True,
        "unified_result": result,
        "ai_team_analysis": result.get("ai_team_analysis"),
        "fix_recommendations": result.get("fix_it_fred_solution"),
        "training_feedback": result.get("linesmart_learning"),
    }


@app.get("/ai/status")
async def ai_integration_status(
    ai_client: AIServicesClient = Depends(get_ai_services_client),
):
    """Check AI Services integration status from CMMS perspective"""
    if not ai_client:
        return {"ai_available": False, "message": "AI client not initialized"}

    ai_health = await ai_client.health_check()
    ai_info = await ai_client.get_service_info()

    return {
        "ai_integration_status": "active" if ai_health else "disconnected",
        "ai_services_info": ai_info,
        "ai_health": ai_health,
        "cmms_ai_features": {
            "intelligent_work_orders": bool(ai_health),
            "predictive_maintenance": bool(ai_health),
            "automated_diagnostics": bool(ai_health),
            "training_optimization": bool(ai_health),
        },
        "integration_endpoints": [
            "/ai/analyze-issue",
            "/ai/unified-process",
            "/ai/status",
        ],
    }


if __name__ == "__main__":
    port = int(os.getenv("CMMS_PORT", "8000"))
    logger.info(f"🚀 Starting CMMS Core on port {port}")
    logger.info("🏭 Designed with AI Team collaboration")

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, log_level="info")
