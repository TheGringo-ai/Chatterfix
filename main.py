import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.core.database import init_database

# Import all routers
from app.routers import (
    ai,
    ar,
    assets,
    dashboard,
    feedback,
    geolocation,
    inventory,
    onboarding,
    planner,
    purchasing,
    team,
    training,
    work_orders
)

# Initialize FastAPI application
app = FastAPI(
    title="ChatterFix CMMS",
    description="Comprehensive Maintenance Management System with AI Integration",
    version="2.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include all routers
app.include_router(dashboard.router)
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

# Root route - redirect to dashboard
@app.get("/")
async def root():
    """Redirect to dashboard"""
    return RedirectResponse(url="/dashboard")

# Startup event - initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    print("✅ ChatterFix CMMS started successfully!")
    print("📊 Database initialized")
    print("🌐 Access the application at: http://localhost:8000")

# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("CMMS_PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
