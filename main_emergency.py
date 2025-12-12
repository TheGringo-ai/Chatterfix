"""
EMERGENCY DEPLOYMENT VERSION - Minimal ChatterFix for Cloud Run
Stripped down version to get dashboards working ASAP
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Minimal FastAPI app for emergency deployment
app = FastAPI(
    title="ChatterFix CMMS - Emergency",
    description="Emergency deployment to restore dashboard functionality",
    version="emergency-1.0.0"
)

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(app_dir, "app", "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Import only essential routers that work
try:
    from app.routers import health, dashboard
    app.include_router(health.router)
    app.include_router(dashboard.router)
    print("✅ Core routers loaded")
except ImportError:
    print("❌ Core routers failed")

# Import critical dashboard routers individually with better error handling
critical_routers = ["demo", "analytics", "work_orders", "assets", "user_management"]
loaded_routers = []

for router_name in critical_routers:
    try:
        router_module = __import__(f'app.routers.{router_name}', fromlist=[router_name])
        app.include_router(router_module.router)
        loaded_routers.append(router_name)
        print(f"✅ {router_name} router loaded")
    except Exception as e:
        print(f"❌ {router_name} router failed: {e}")
        # Try to continue anyway for critical functionality
        continue

# Specifically try analytics again with more specific imports
if "analytics" not in loaded_routers:
    try:
        from app.routers.analytics import router as analytics_router
        app.include_router(analytics_router)
        loaded_routers.append("analytics")
        print("✅ analytics router loaded (retry)")
    except Exception as e:
        print(f"❌ analytics router retry failed: {e}")
        # Try minimal analytics if full fails
        try:
            from app.routers import analytics
            app.include_router(analytics.router)
            loaded_routers.append("analytics")
            print("✅ analytics router loaded (minimal)")
        except Exception as e2:
            print(f"❌ analytics minimal also failed: {e2}")

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/emergency/status")
async def emergency_status():
    return {
        "status": "emergency_deployment_active",
        "loaded_routers": loaded_routers,
        "critical_dashboards": [
            "/demo/work-orders",
            "/analytics/dashboard", 
            "/analytics/roi-dashboard",
            "/demo/planner"
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main_emergency:app", host="0.0.0.0", port=port)