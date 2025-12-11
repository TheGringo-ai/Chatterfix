#!/usr/bin/env python3
"""
🤖 AI Services Microservice
Independent AI platform providing:
- AI Team (Multi-model collaboration)  
- Fix it Fred (Autonomous repair)
- LineSmart (Training & analytics)
- Unified AI integration

Designed with AI Team collaboration for optimal architecture
"""
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

# Add project paths for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
load_dotenv(override=True)

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# AI Services logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - 🤖 AI-SERVICES - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

@asynccontextmanager
async def ai_services_lifespan(app: FastAPI):
    """AI Services microservice lifecycle with AI Team guidance"""
    logger.info("🤖 Starting AI Services Microservice...")
    logger.info("🎯 Designed with AI Team collaboration")
    
    # Start gRPC AI Team server
    grpc_task = None
    try:
        from ai_team.grpc_server import serve
        grpc_task = asyncio.create_task(serve(port=50051))
        logger.info("✅ AI Team gRPC server: localhost:50051")
    except Exception as e:
        logger.error(f"❌ gRPC server failed: {e}")
    
    logger.info("✅ AI Services ready!")
    logger.info("🌐 HTTP API: localhost:8001")
    logger.info("🤖 AI Team: /ai-team") 
    logger.info("🔧 Fix it Fred: /fix-it-fred")
    logger.info("📊 LineSmart: /linesmart")
    logger.info("⚡ Unified AI: /unified-ai")
    logger.info("📋 Service Info: /ai-services-info")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Services...")
    if grpc_task:
        grpc_task.cancel()
        try:
            await grpc_task
        except asyncio.CancelledError:
            pass
    logger.info("✅ AI Services shutdown complete")

# Create AI Services app
app = FastAPI(
    title="AI Services Microservice",
    description="Independent AI Platform - Designed with AI Team collaboration",
    version="1.0.0",
    lifespan=ai_services_lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for microservice communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Import AI service routers
try:
    from app.routers.ai_team_collaboration import router as ai_team_router
    from app.routers.fix_it_fred import router as fix_it_fred_router
    from app.routers.linesmart_integration import router as linesmart_router
    from app.routers.ai_memory import router as ai_memory_router
    
    app.include_router(ai_team_router)
    app.include_router(fix_it_fred_router)
    app.include_router(linesmart_router)
    app.include_router(ai_memory_router)
    
    logger.info("✅ AI service routers loaded")
    AI_SERVICES_LOADED = True
    
except ImportError as e:
    logger.error(f"❌ Failed to load AI routers: {e}")
    AI_SERVICES_LOADED = False

# Unified AI endpoints
if AI_SERVICES_LOADED:
    @app.get("/unified-ai/health")
    async def unified_ai_health():
        """Unified AI health check"""
        try:
            from app.services.unified_ai_integration import get_unified_integration
            integration = await get_unified_integration()
            return await integration.get_integration_health()
        except Exception as e:
            logger.error(f"Unified AI health failed: {e}")
            return {"healthy": False, "error": str(e)}

    @app.post("/unified-ai/process")
    async def unified_ai_process(request_data: dict):
        """Process request through unified AI system"""
        try:
            from app.services.unified_ai_integration import get_unified_integration
            integration = await get_unified_integration()
            return await integration.process_unified_request(request_data)
        except Exception as e:
            logger.error(f"Unified AI processing failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# AI Services microservice endpoints
@app.get("/")
async def ai_services_root():
    """AI Services microservice root"""
    return {
        "service": "AI Services Microservice", 
        "status": "operational",
        "version": "1.0.0",
        "architecture": "microservice",
        "port": 8001,
        "designed_by": "AI Team Collaboration",
        "services": {
            "ai_team": {
                "description": "Multi-model AI collaboration (Claude, ChatGPT, Gemini, Grok)",
                "endpoint": "/ai-team",
                "grpc": "localhost:50051"
            },
            "fix_it_fred": {
                "description": "AI autonomous repair system",
                "endpoint": "/fix-it-fred"
            },
            "linesmart": {
                "description": "Training data & skill gap analysis", 
                "endpoint": "/linesmart"
            },
            "ai_memory": {
                "description": "AI learning system to prevent repeat coding mistakes",
                "endpoint": "/ai-memory"
            },
            "unified_ai": {
                "description": "Complete AI workflow orchestration",
                "endpoint": "/unified-ai"
            }
        },
        "capabilities": [
            "multi_model_collaboration",
            "autonomous_problem_solving", 
            "intelligent_training",
            "unified_ai_processing",
            "learning_memory_system"
        ],
        "communication": {
            "external_api": "REST",
            "ai_team_internal": "gRPC",
            "cmms_integration": "/ai-services-info"
        }
    }

@app.get("/health")
async def ai_services_health():
    """AI Services health check"""
    try:
        components = {
            "ai_services_loaded": AI_SERVICES_LOADED,
            "ai_team_grpc": False,
            "unified_integration": False
        }
        
        # Check AI Team gRPC
        try:
            from ai_team.grpc_client import get_ai_team_client
            client = get_ai_team_client()
            ai_health = await client.health_check()
            components["ai_team_grpc"] = ai_health.get("healthy", False)
        except:
            pass
        
        # Check unified integration
        try:
            from app.services.unified_ai_integration import get_unified_integration
            integration = await get_unified_integration()
            integration_status = await integration.get_integration_health()
            components["unified_integration"] = integration_status.get("unified_integration_healthy", False)
        except:
            pass
        
        all_healthy = all(components.values())
        
        return {
            "healthy": all_healthy,
            "service": "ai-services",
            "version": "1.0.0", 
            "port": 8001,
            "components": components,
            "endpoints": ["/ai-team", "/fix-it-fred", "/linesmart", "/ai-memory", "/unified-ai"],
            "microservice_ready": True
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"healthy": False, "service": "ai-services", "error": str(e)}

@app.get("/ai-services-info")
async def ai_services_info():
    """Service discovery info for CMMS integration"""
    return {
        "service_name": "ai-services",
        "service_type": "microservice", 
        "version": "1.0.0",
        "communication": {
            "http_port": 8001,
            "grpc_port": 50051,
            "protocols": ["REST", "gRPC"]
        },
        "endpoints": {
            "health_check": "/health",
            "service_info": "/ai-services-info",
            "unified_processing": "/unified-ai/process",
            "ai_analysis": "/ai-team/execute",
            "autonomous_repair": "/fix-it-fred/analyze", 
            "training_integration": "/linesmart/submit-training-data",
            "memory_system": "/ai-memory/health"
        },
        "integration_patterns": {
            "cmms_integration": {
                "health_check": "GET /health",
                "process_request": "POST /unified-ai/process", 
                "analyze_issue": "POST /fix-it-fred/analyze",
                "ai_collaboration": "POST /ai-team/execute"
            }
        },
        "designed_with": "AI Team multi-model collaboration"
    }

# Service discovery for other microservices
@app.get("/discover")
async def service_discovery():
    """Service discovery endpoint"""
    return {
        "service": "ai-services",
        "healthy": True,
        "endpoints": {
            "base_url": "http://localhost:8001",
            "health": "/health",
            "info": "/ai-services-info", 
            "unified_ai": "/unified-ai/process"
        },
        "capabilities": [
            "ai_analysis", "autonomous_repair", "training_analytics", "unified_intelligence", "memory_learning"
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("AI_SERVICES_PORT", "8001"))
    logger.info(f"🚀 Starting AI Services on port {port}")
    logger.info("🤖 Designed with AI Team collaboration")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port, 
        reload=False,
        log_level="info"
    )