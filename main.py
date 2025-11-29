import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.core.database import init_database
from app.core.db_adapter import get_db_adapter

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
    media
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
app.include_router(health.router)     # Health checks (no prefix)
app.include_router(dashboard.router)  # Dashboard is now the main landing page
app.include_router(landing.router)    # Landing page becomes signup page
app.include_router(demo.router)       # Demo routes for app exploration
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
app.include_router(iot.router)        # IoT sensor integration
app.include_router(push.router)       # Push notifications
app.include_router(media.router)      # Media upload and barcode functionality

# Startup event - initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    db_adapter = get_db_adapter()
    print("✅ ChatterFix CMMS started successfully!")
    print(f"📊 Database initialized ({db_adapter.db_type})")
    
    # Auto-populate demo data if database is empty
    try:
        import sqlite3
        conn = sqlite3.connect("./data/cmms.db")
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        
        if user_count == 0:
            print("🔄 Populating demo data...")
            import subprocess
            subprocess.run(["python", "populate_demo_data.py"], check=True)
            print("✨ Demo data populated successfully!")
    except Exception as e:
        print(f"⚠️ Demo data population failed: {e}")
    
    print("🌐 ChatterFix ready for use!")
    print("📊 Analytics dashboard: /analytics/dashboard")
    print("🔌 IoT API: /iot/sensors/")

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
