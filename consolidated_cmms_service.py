#!/usr/bin/env python3
"""
ChatterFix Consolidated CMMS Service
Combines work orders, assets, and parts into one deployment with modular architecture
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import modular routers
from modules.work_orders import router as work_orders_router
from modules.assets import router as assets_router  
from modules.parts import router as parts_router
from modules.shared import get_health_status

app = FastAPI(
    title="ChatterFix Consolidated CMMS Service",
    description="Unified work orders, assets, and parts management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include module routers
app.include_router(work_orders_router, prefix="/work_orders", tags=["Work Orders"])
app.include_router(assets_router, prefix="/assets", tags=["Assets"])
app.include_router(parts_router, prefix="/parts", tags=["Parts"])

@app.get("/health")
async def health_check():
    """Consolidated health check"""
    return {
        "status": "healthy",
        "service": "consolidated_cmms",
        "version": "1.0.0",
        "modules": ["work_orders", "assets", "parts"],
        **get_health_status()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ChatterFix Consolidated CMMS",
        "version": "1.0.0",
        "endpoints": {
            "work_orders": "/work_orders",
            "assets": "/assets", 
            "parts": "/parts",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)