"""
AI Team Service - Independent FastAPI Application
Provides AI collaboration services via HTTP REST API
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
import uvicorn

from app.core.config import settings
from app.core.security import verify_api_key
from app.api.v1.endpoints import ai_team, analytics, memory
from app.services.ai_orchestrator import AIOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global AI orchestrator instance
ai_orchestrator: Optional[AIOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global ai_orchestrator
    
    logger.info("🚀 Starting AI Team Service...")
    
    # Initialize AI orchestrator
    ai_orchestrator = AIOrchestrator()
    await ai_orchestrator.initialize()
    
    logger.info("✅ AI Team Service ready!")
    yield
    
    logger.info("🛑 Shutting down AI Team Service...")

# Create FastAPI app
app = FastAPI(
    title="ChatterFix AI Team Service",
    description="Independent AI collaboration service for ChatterFix CMMS",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

async def get_current_service(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify API key authentication"""
    if not verify_api_key(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return "authenticated"

async def get_ai_orchestrator() -> AIOrchestrator:
    """Dependency to get AI orchestrator instance"""
    if ai_orchestrator is None:
        raise HTTPException(status_code=503, detail="AI orchestrator not initialized")
    return ai_orchestrator

# Include API routers
app.include_router(
    ai_team.router,
    prefix="/api/v1",
    dependencies=[Depends(get_current_service)]
)
app.include_router(
    analytics.router,
    prefix="/api/v1",
    dependencies=[Depends(get_current_service)]
)
app.include_router(
    memory.router,
    prefix="/api/v1",
    dependencies=[Depends(get_current_service)]
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Get model count without dependency injection
        model_count = 0
        if ai_orchestrator:
            model_count = len(ai_orchestrator.agents)
        
        return {
            "status": "healthy",
            "service": "AI Team Service", 
            "version": "1.0.0",
            "timestamp": time.time(),
            "ai_models_count": model_count,
            "orchestrator_initialized": ai_orchestrator is not None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "service": "AI Team Service",
            "version": "1.0.0", 
            "timestamp": time.time(),
            "error": str(e)
        }

@app.get("/api/v1/models")
async def get_available_models(orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)):
    """Get list of available AI models"""
    try:
        models = []
        for agent_name, agent in orchestrator.agents.items():
            if await agent.is_available():
                models.append({
                    "name": agent_name,
                    "model_type": agent.config.model_type.value,
                    "role": agent.config.role,
                    "capabilities": agent.config.capabilities,
                    "status": "available"
                })
        return {"models": models, "total": len(models)}
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ChatterFix AI Team Service",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "execute": "/api/v1/execute",
            "stream": "/api/v1/stream", 
            "models": "/api/v1/models",
            "analytics": "/api/v1/analytics",
            "memory": "/api/v1/memory"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=False,
        log_level="info"
    )