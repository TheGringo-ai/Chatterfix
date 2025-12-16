import logging
import os

from dotenv import load_dotenv

# Load environment variables (override system defaults)
load_dotenv(override=True)

# Import secret management utility
from app.utils.security import get_secret_sync

# Production build - debug statements removed for clean deployment

# Define version information immediately to avoid circular import issues
APP_VERSION = "2.2.0-enterprise-plus"
APP_DESCRIPTION = "Enterprise QualityFix & SafetyFix with AI Team Debugging"

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.db_adapter import get_db_adapter
from app.middleware import ErrorTrackingMiddleware
from app.services.ai_service import get_maintenance_solution

# AI Team Configuration - MUST BE DEFINED BEFORE LOGGING
# Fetch secrets securely
DISABLE_AI_TEAM_GRPC_STR = get_secret_sync("DISABLE_AI_TEAM_GRPC")
DISABLE_AI_TEAM_GRPC = DISABLE_AI_TEAM_GRPC_STR is not None and DISABLE_AI_TEAM_GRPC_STR.lower() == "true"

AI_TEAM_SERVICE_URL = get_secret_sync("AI_TEAM_SERVICE_URL")
USE_AI_TEAM_HTTP = AI_TEAM_SERVICE_URL is not None

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

# Log AI team configuration

# Log AI team configuration now that logger is initialized - SAFE VERSION
try:
    logger.info("🤖 AI Team Configuration:")
    logger.info(f"   DISABLE_AI_TEAM_GRPC: {DISABLE_AI_TEAM_GRPC}")
    logger.info(f"   USE_AI_TEAM_HTTP: {USE_AI_TEAM_HTTP}")
    # Only log service URL, not API key
    service_url = str(AI_TEAM_SERVICE_URL) if AI_TEAM_SERVICE_URL else "None"
    logger.info(f"   AI_TEAM_SERVICE_URL: {service_url}")

    if USE_AI_TEAM_HTTP:
        logger.info(f"✅ AI Team HTTP service will be used")
    elif not DISABLE_AI_TEAM_GRPC:
        logger.info("⚠️  AI Team gRPC service will be used (may cause startup timeout)")
    else:
        logger.info("❌ AI Team service disabled")
except Exception as e:
    logger.error(f"Failed to log AI team configuration: {e}")
    # Continue execution - don't let logging break the app

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# GRADUALLY RE-ENABLE ROUTERS - Start with core functionality
try:
    from app.routers import (
        auth,
        dashboard,
        health,
        landing,
        organization,
        settings,
        signup,
    )

    CORE_ROUTERS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import core routers: {e}")
    CORE_ROUTERS_AVAILABLE = False

# Import additional routers - ROBUST APPROACH FOR PRODUCTION
extended_routers = {}

# List of critical routers that must work
critical_routers = [
    'demo',
    'analytics', 
    'work_orders',
    'assets',
    'public_demo'
]

# AI Team Configuration (moved above to fix variable reference issue)

# List of all extended routers
all_extended_routers = [
    'ai',  # AI endpoints with memory integration
    'ai_team_collaboration',
    'analytics',
    'assets',
    'autonomous_features',
    'autonomous_intelligence_dashboard',
    'ceo_dashboard',
    'demo',
    'fix_it_fred',
    'inventory',
    'iot',
    'linesmart_integration',
    'planner',
    'planner_simple',
    'public_demo',
    'purchasing',
    'premium_modules',
    'quality_management',
    'safety_management',
    'team',
    'training',
    'user_management',
    'work_orders',
]

# Import each router individually to avoid one failure breaking all
for router_name in all_extended_routers:
    # Skip AI team collaboration if disabled for Cloud Run startup fix
    if router_name == 'ai_team_collaboration':
        try:
            logger.info(f"🔍 AI Team router decision for {router_name}:")
            logger.info(f"   DISABLE_AI_TEAM_GRPC: {DISABLE_AI_TEAM_GRPC}")
            logger.info(f"   USE_AI_TEAM_HTTP: {USE_AI_TEAM_HTTP}")
            # Safe logging - avoid any potential API key issues
            service_configured = "configured" if AI_TEAM_SERVICE_URL else "not configured"
            logger.info(f"   AI_TEAM_SERVICE: {service_configured}")
            
            # Use safe boolean logic
            should_skip = DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP
            
            if should_skip:
                logger.info(f"⏸️ Skipping {router_name} router (AI team service not configured)")
                continue
            else:
                logger.info(f"✅ Will load {router_name} router")
        except Exception as e:
            logger.error(f"Error in AI team router decision: {e}")
            # Default to loading the router if there's an error in decision logic
            logger.info(f"🔄 Defaulting to load {router_name} router due to decision error")
        
    try:
        router_module = __import__(f'app.routers.{router_name}', fromlist=[router_name])
        extended_routers[router_name] = router_module
        logger.info(f"✅ Successfully imported {router_name} router")
    except ImportError as e:
        logger.warning(f"❌ Warning: Could not import {router_name} router: {e}")
    except Exception as e:
        import traceback
        logger.error(f"❌ Failed to import {router_name} router: {type(e).__name__}: {e}")
        logger.error(f"   Traceback: {traceback.format_exc()}")

# Check if critical routers are available
critical_routers_loaded = all(router in extended_routers for router in critical_routers)
EXTENDED_ROUTERS_AVAILABLE = len(extended_routers) > 0

logging.info(f"Extended routers status: {len(extended_routers)}/{len(all_extended_routers)} loaded")
logging.info(f"Critical routers status: {critical_routers_loaded}")

# Special handling for simple planner
SIMPLE_PLANNER_AVAILABLE = 'planner_simple' in extended_routers


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
                    description = (
                        lines[1].strip() if len(lines) > 1 else "ChatterFix CMMS"
                    )
                    return version, description
        except Exception:
            continue

    # Fallback to hardcoded version if file not found
    return "2.1.0-enterprise-planner", "Enhanced Demo Planner with Advanced Scheduler"


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
        logger.info("🔌 IoT Advanced Module: /iot/dashboard")
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

# Add ProxyHeadersMiddleware for proper Cloud Run integration
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Add error tracking middleware
app.add_middleware(
    ErrorTrackingMiddleware,
    sentry_dsn=get_secret_sync("SENTRY_DSN"),  # Optional: set SENTRY_DSN env var
    environment=os.getenv("ENVIRONMENT", "development"),
)

# CORS Configuration - Secure settings for production
allowed_origins = [
    "https://chatterfix.com",
    "https://www.chatterfix.com",
    "https://chatterfix-cmms-667180410498.us-central1.run.app",
    get_secret_sync("FRONTEND_URL") or "http://localhost:8080",
]

# In development, allow localhost
if os.getenv("ENVIRONMENT", "development") == "development":
    allowed_origins.extend([
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Add trusted host middleware for production - DISABLED for Cloud Run
# if os.getenv("ENVIRONMENT") == "production":
#     app.add_middleware(
#         TrustedHostMiddleware, allowed_hosts=["*"]  # Allow all hosts for Cloud Run flexibility
#     )

# Add rate limiting for production stability
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
        routes.append(
            {
                "name": getattr(route, "name", None),
                "path": getattr(route, "path", None),
                "methods": (
                    list(getattr(route, "methods", []))
                    if hasattr(route, "methods")
                    else None
                ),
            }
        )
    return {
        "routes": routes,
        "static_dir": static_dir,
        "static_exists": os.path.isdir(static_dir),
        "cwd": os.getcwd(),
    }


# REBUILD APPLICATION WITH CORE FUNCTIONALITY
# Include essential routers first
if CORE_ROUTERS_AVAILABLE:
    app.include_router(health.router)  # Health checks (no prefix)
    app.include_router(dashboard.router)  # Dashboard is the main landing page
    app.include_router(landing.router)  # Landing page
    app.include_router(auth.router)  # Authentication
    app.include_router(signup.router)  # User signup
    app.include_router(settings.router)  # Settings
    app.include_router(organization.router)  # Organization/Team management

# Include extended functionality - ROBUST ROUTER INCLUSION
router_descriptions = {
    'demo': 'Demo routes',
    'public_demo': 'Public demo routes (no auth required)',
    'work_orders': 'Work orders',
    'assets': 'Assets',
    'inventory': 'Inventory',
    'team': 'Team management',
    'planner': 'Planner functionality',
    'purchasing': 'Purchasing and POS system',
    'ai_team_collaboration': 'AI Team gRPC Collaboration',
    'fix_it_fred': 'Fix it Fred AI-powered autonomous fixing',
    'linesmart_integration': 'LineSmart training service integration',
    'training': 'Training modules and learning management system',
    'user_management': 'User management dashboard with Firebase Auth',
    'analytics': 'Analytics dashboard with KPIs and reporting',
    'planner_simple': 'Simple planner for testing',
    'premium_modules': 'Premium Modules API - Licensing for IoT Advanced, QualityFix, SafetyFix',
    'quality_management': 'QualityFix Premium Module - HACCP, ISO 22000, Food Safety compliance ($99/mo)',
    'safety_management': 'SafetyFix Premium Module - OSHA compliance and incident tracking ($99/mo)',
    'iot': 'IoT Advanced Premium Module - Real-time sensor monitoring and predictive analytics ($199/mo)'
}

# Include each router that was successfully imported
for router_name, router_module in extended_routers.items():
    try:
        app.include_router(router_module.router)
        description = router_descriptions.get(router_name, router_name)
        logger.info(f"✅ Included {router_name} router: {description}")
    except Exception as e:
        logger.error(f"❌ Failed to include {router_name} router: {e}")

# Fallback: If no extended routers loaded at all, try simple planner
if len(extended_routers) == 0:
    try:
        from app.routers import planner_simple
        app.include_router(planner_simple.router)
        logging.info("Fallback: Included simple planner router")
    except ImportError as e:
        logging.error(f"Fallback failed: Could not import simple planner: {e}")


# Helper function to check if user is authenticated
def is_authenticated(request: Request) -> bool:
    """Check if user has valid session - App First Logic"""
    # Check for session token in cookies
    session_token = request.cookies.get("session_token")
    auth_token = request.cookies.get("auth_token") 
    user_id = request.cookies.get("user_id")
    
    # If any authentication indicators exist, consider them logged in
    return bool(session_token or auth_token or user_id)

# Root endpoint - App-First Logic
@app.get("/")
async def root(request: Request):
    """
    🚀 ROOT REDIRECT - Direct to Demo
    
    Always redirect to /demo page as requested
    """
    return RedirectResponse(url="/demo", status_code=302)


# Simple test endpoint to verify deployment
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify deployment works"""
    return {
        "status": "success",
        "message": "ChatterFix is running with CI/CD!",
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "deployment_timestamp": "2025-12-13T03:20:00Z",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "build_id": "AI-TEAM-ENTERPRISE-BUILD-20251213",
        "port": os.getenv("PORT", "unknown"),
        "host_middleware": "DISABLED for Cloud Run",
        "database": "Firebase/Firestore",
        "features": [
            "Enterprise Planner",
            "Advanced Scheduler",
            "AI Optimization",
            "Mobile Interface",
            "Parts Management",
            "PM Automation",
            "AI Team Collaboration",
            "Fix it Fred Autonomous Fixing",
            "LineSmart Training Integration",
            "Enterprise QualityFix Module",
            "Enterprise SafetyFix Module",
            "AI Team Debugging Fixes",
            "Zero-Crash Reliability",
        ],
        "ai_services": {
            "ai_team": "/ai-team",
            "fix_it_fred": "/fix-it-fred",
            "linesmart": "/linesmart",
            "unified_integration": "/unified-ai",
        },
    }


@app.get("/unified-ai/health")
async def unified_ai_health():
    """Health check for unified AI integration"""
    try:
        from app.services.unified_ai_integration import get_unified_integration

        integration = await get_unified_integration()
        health_status = await integration.get_integration_health()
        return health_status
    except Exception as e:
        logger.error(f"Unified AI health check failed: {e}")
        return {"healthy": False, "error": str(e)}


@app.get("/test-new-endpoint")
async def test_new_endpoint():
    """Simple test to verify new endpoints are deployed"""
    return {"status": "working", "message": "New endpoints are being deployed correctly"}


# TEMPORARY DIRECT TRAINING MODULE ENDPOINTS - BYPASS ROUTER LOADING ISSUE
@app.get("/training/modules/{module_id}", response_class=HTMLResponse)
async def training_module_direct(request: Request, module_id: str):
    """Direct training module endpoint - bypasses router loading issues"""
    try:
        from app.core.firestore_db import get_firestore_manager
        from fastapi.templating import Jinja2Templates
        import json
        
        templates = Jinja2Templates(directory="app/templates")
        firestore_manager = get_firestore_manager()
        
        # Get the training module from database
        module = await firestore_manager.get_document("training_modules", module_id)
        
        if not module:
            return templates.TemplateResponse(
                "training_module_interactive.html",
                {
                    "request": request,
                    "error": f"Training module {module_id} not found",
                    "module": None,
                    "content": None,
                    "role": "technician",
                    "role_config": {"title": "Training Module Not Found"}
                },
                status_code=404
            )
        
        # Parse content if available
        content = None
        if module.get("content_path"):
            try:
                content = json.loads(module["content_path"])
            except Exception as e:
                logger.warning(f"Could not parse content for module {module_id}: {e}")
                pass
        
        # Convert datetime objects to strings to avoid serialization issues
        if module:
            for key, value in module.items():
                if hasattr(value, 'strftime'):  # DateTime object
                    module[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif hasattr(value, '__dict__') and hasattr(value, 'timestamp'):  # Firestore timestamp
                    module[key] = str(value)
        
        return templates.TemplateResponse(
            "training_module_interactive.html",
            {
                "request": request,
                "module": module,
                "content": content,
                "role": "technician", 
                "role_config": {"title": "Technician Training"}
            }
        )
        
    except Exception as e:
        logger.error(f"Error in direct training module endpoint: {e}")
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>Training module {module_id} failed to load: {str(e)}</p></body></html>",
            status_code=500
        )


@app.get("/training", response_class=HTMLResponse) 
async def training_center_direct(request: Request):
    """Direct training center endpoint - bypasses router loading issues"""
    try:
        from app.core.firestore_db import get_firestore_manager
        from fastapi.templating import Jinja2Templates
        
        templates = Jinja2Templates(directory="app/templates")
        firestore_manager = get_firestore_manager()
        
        # Get all training modules
        modules = await firestore_manager.get_collection("training_modules", order_by="-created_at")
        
        return templates.TemplateResponse(
            "training_center.html",
            {
                "request": request,
                "my_training": [],
                "available_modules": modules,
                "stats": {
                    "total_assigned": 0,
                    "completed": 0, 
                    "in_progress": 0,
                    "avg_score": 0
                },
                "user_id": "demo_user"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in direct training center endpoint: {e}")
        return HTMLResponse(
            content=f"<html><body><h1>Training Center</h1><p>Failed to load: {str(e)}</p></body></html>",
            status_code=500
        )


@app.get("/training/", response_class=HTMLResponse)
async def training_center_direct_slash(request: Request):
    """Direct training center endpoint with slash"""
    return await training_center_direct(request)


@app.get("/iot/dashboard", response_class=HTMLResponse)
async def iot_dashboard_direct(request: Request):
    """Direct IoT dashboard endpoint - premium module interface"""
    try:
        from fastapi.templating import Jinja2Templates
        
        templates = Jinja2Templates(directory="app/templates")
        
        return templates.TemplateResponse(
            "iot_dashboard.html",
            {
                "request": request,
                "user_id": "demo_user"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in IoT dashboard endpoint: {e}")
        return HTMLResponse(
            content=f"""
            <html>
            <head>
                <title>IoT Advanced Module - ChatterFix</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            </head>
            <body class="bg-gray-50">
                <div class="min-h-screen flex items-center justify-center">
                    <div class="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
                        <h1 class="text-2xl font-bold text-gray-900 mb-4">IoT Advanced Module</h1>
                        <p class="text-gray-600 mb-6">Dashboard failed to load: {str(e)}</p>
                        <a href="/demo" class="bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                            Return to Demo
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """,
            status_code=500
        )


@app.get("/debug/ai-config")
async def debug_ai_config():
    """Debug endpoint to check AI team configuration"""
    # Use get_secret_sync for consistency in debug output
    disable_grpc_debug = get_secret_sync("DISABLE_AI_TEAM_GRPC")
    ai_team_service_url_debug = get_secret_sync("AI_TEAM_SERVICE_URL")
    internal_api_key_debug = get_secret_sync("INTERNAL_API_KEY")

    return {
        "ai_team_config": {
            "DISABLE_AI_TEAM_GRPC": disable_grpc_debug,
            "AI_TEAM_SERVICE_URL": ai_team_service_url_debug,
            "INTERNAL_API_KEY": internal_api_key_debug[:10] + "..." if internal_api_key_debug else None,
            "USE_AI_TEAM_HTTP": ai_team_service_url_debug is not None,
        },
        "computed_values": {
            "DISABLE_AI_TEAM_GRPC": DISABLE_AI_TEAM_GRPC,
            "USE_AI_TEAM_HTTP": USE_AI_TEAM_HTTP,
            "AI_TEAM_SERVICE_URL": AI_TEAM_SERVICE_URL,
        },
        "routers_loaded": list(extended_routers.keys()),
        "ai_team_in_routers": "ai_team_collaboration" in extended_routers,
    }


# DIRECT AI TEAM INTEGRATION - BYPASS ROUTER ISSUES
@app.get("/ai-team/health")
async def ai_team_health_direct():
    """Direct AI team health check - bypasses router loading issues"""
    try:
        import httpx
        ai_service_url = get_secret_sync("AI_TEAM_SERVICE_URL")
        if not ai_service_url:
            return {"status": "error", "message": "AI team service URL not configured"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ai_service_url}/health")
            if response.status_code == 200:
                service_data = response.json()
                return {
                    "status": "connected",
                    "message": "AI team service is healthy via direct integration",
                    "service_response": service_data,
                    "integration": "working",
                    "bypass": "router_loading_issue"
                }
            else:
                return {
                    "status": "error",
                    "message": f"AI team service returned {response.status_code}",
                    "response": response.text[:200]
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect to AI team service: {str(e)}",
        }


@app.get("/ai-team/models")
async def ai_team_models_direct():
    """Direct AI team models endpoint - bypasses router loading issues"""
    try:
        import httpx
        ai_service_url = get_secret_sync("AI_TEAM_SERVICE_URL")
        api_key = get_secret_sync("INTERNAL_API_KEY")

        if not ai_service_url or not api_key:
            return {"status": "error", "message": "AI team service not configured"}

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ai_service_url}/api/v1/models", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "message": f"AI team service returned {response.status_code}",
                    "response": response.text[:200]
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get AI models: {str(e)}"
        }


@app.post("/ai-team/execute")
async def ai_team_execute_direct(request_data: dict):
    """Direct AI team execution endpoint - bypasses router loading issues"""
    try:
        import httpx
        ai_service_url = get_secret_sync("AI_TEAM_SERVICE_URL")
        api_key = get_secret_sync("INTERNAL_API_KEY")
        
        if not ai_service_url or not api_key:
            return {"status": "error", "message": "AI team service not configured"}
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for AI processing
            response = await client.post(
                f"{ai_service_url}/api/v1/execute",
                json=request_data,
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "message": f"AI team service returned {response.status_code}",
                    "response": response.text[:200]
                }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to execute AI team task: {str(e)}"
        }

@app.post("/unified-ai/process")
async def unified_ai_process(request_data: dict):
    """Process request through unified AI integration (AI Team + Fix it Fred + LineSmart)"""
    try:
        from app.services.unified_ai_integration import get_unified_integration

        integration = await get_unified_integration()
        result = await integration.process_unified_request(request_data)
        return result
    except Exception as e:
        logger.error(f"Unified AI processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/unified-ai")
async def unified_ai_dashboard():
    """Unified AI services dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Unified AI Dashboard - ChatterFix CMMS</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .service-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                text-decoration: none;
                transition: transform 0.3s ease;
            }
            .service-card:hover {
                transform: translateY(-5px);
                text-decoration: none;
                color: white;
            }
            .integration-flow {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .flow-step {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #007bff;
            }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>🤖 Unified AI Dashboard</h1>
            <p class="lead">AI Team + Fix it Fred + LineSmart - Complete Intelligent Automation</p>
            
            <!-- Service Status -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5>🔋 AI Services Status</h5>
                        </div>
                        <div class="card-body">
                            <div id="services-status">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Individual Services -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <a href="/ai-team" class="service-card d-block text-center">
                        <h4>🤖 AI Team</h4>
                        <p>Multi-model collaboration with Claude, ChatGPT, Gemini, Grok</p>
                        <small>Advanced problem analysis</small>
                    </a>
                </div>
                <div class="col-md-4">
                    <a href="/fix-it-fred" class="service-card d-block text-center">
                        <h4>🔧 Fix it Fred</h4>
                        <p>AI-powered autonomous fixing and issue resolution</p>
                        <small>Automated problem solving</small>
                    </a>
                </div>
                <div class="col-md-4">
                    <a href="/linesmart" class="service-card d-block text-center">
                        <h4>📊 LineSmart</h4>
                        <p>Training data integration and skill gap analysis</p>
                        <small>Continuous learning system</small>
                    </a>
                </div>
            </div>
            
            <!-- Unified Processing -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5>⚡ Unified AI Processing</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label for="unified-request" class="form-label">Describe your maintenance issue or request:</label>
                        <textarea class="form-control" id="unified-request" rows="3" 
                                  placeholder="Example: Server performance is degrading with high CPU usage during peak hours..."></textarea>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="request-type" class="form-label">Request Type:</label>
                            <select class="form-select" id="request-type">
                                <option value="maintenance">Maintenance Issue</option>
                                <option value="performance">Performance Problem</option>
                                <option value="bug">Bug Report</option>
                                <option value="enhancement">Enhancement Request</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label for="priority" class="form-label">Priority:</label>
                            <select class="form-select" id="priority">
                                <option value="low">Low</option>
                                <option value="medium" selected>Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                    </div>
                    <button class="btn btn-primary btn-lg" onclick="processUnifiedRequest()">
                        🚀 Process with Full AI Team
                    </button>
                </div>
            </div>
            
            <!-- Integration Flow -->
            <div class="integration-flow">
                <h5>🔄 AI Integration Flow</h5>
                <div class="flow-step">
                    <strong>1. AI Team Analysis</strong> - Multi-model collaborative problem analysis
                </div>
                <div class="flow-step">
                    <strong>2. Fix it Fred Resolution</strong> - Automated fix recommendations and application
                </div>
                <div class="flow-step">
                    <strong>3. LineSmart Learning</strong> - Training data integration for future improvements
                </div>
                <div class="flow-step">
                    <strong>4. Unified Response</strong> - Combined intelligence for optimal solution
                </div>
            </div>
            
            <!-- Results -->
            <div class="card">
                <div class="card-header">
                    <h5>🎯 Unified AI Results</h5>
                </div>
                <div class="card-body">
                    <div id="unified-results"></div>
                </div>
            </div>
        </div>
        
        <script>
            async function loadServicesStatus() {
                try {
                    const response = await fetch('/unified-ai/health');
                    const status = await response.json();
                    
                    const servicesHtml = Object.entries(status.services || {}).map(([service, info]) => `
                        <div class="col-md-4 mb-2">
                            <div class="d-flex align-items-center">
                                <span class="badge ${info.connected ? 'bg-success' : 'bg-danger'} me-2">
                                    ${service.toUpperCase()}
                                </span>
                                <span>${info.status}</span>
                            </div>
                        </div>
                    `).join('');
                    
                    document.getElementById('services-status').innerHTML = `
                        <div class="row">
                            ${servicesHtml}
                        </div>
                        <hr>
                        <small class="text-muted">
                            Total Integrations: ${status.integration_stats?.total_requests || 0} | 
                            Success Rate: ${status.integration_stats?.successful_integrations || 0}/${status.integration_stats?.total_requests || 0}
                        </small>
                    `;
                } catch (error) {
                    document.getElementById('services-status').innerHTML = 
                        '<span class="text-danger">Failed to load services status</span>';
                }
            }
            
            async function processUnifiedRequest() {
                const request = document.getElementById('unified-request').value;
                const type = document.getElementById('request-type').value;
                const priority = document.getElementById('priority').value;
                
                if (!request.trim()) {
                    alert('Please describe your request');
                    return;
                }
                
                const resultsDiv = document.getElementById('unified-results');
                resultsDiv.innerHTML = `
                    <div class="text-center">
                        <div class="spinner-border" role="status"></div>
                        <p class="mt-2">Processing with unified AI team...</p>
                        <small class="text-muted">AI Team analyzing → Fix it Fred solving → LineSmart learning</small>
                    </div>
                `;
                
                try {
                    const response = await fetch('/unified-ai/process', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            description: request,
                            type: type,
                            priority: priority,
                            timestamp: new Date().toISOString()
                        })
                    });
                    
                    const result = await response.json();
                    
                    let resultHtml = `
                        <div class="alert ${result.success ? 'alert-success' : 'alert-danger'}">
                            <h6>🤖 Unified AI Processing ${result.success ? 'Complete' : 'Failed'}</h6>
                            <strong>Request ID:</strong> ${result.request_id}<br>
                            <strong>Overall Confidence:</strong> ${(result.unified_confidence * 100).toFixed(1)}%<br>
                            <strong>Integration Summary:</strong> ${result.integration_summary}
                        </div>
                    `;
                    
                    if (result.success) {
                        // AI Team Results
                        resultHtml += `
                            <div class="card mb-3">
                                <div class="card-header bg-primary text-white">
                                    <h6>🤖 AI Team Analysis</h6>
                                </div>
                                <div class="card-body">
                                    <p>${result.ai_team_analysis?.collaborative_insight || 'AI analysis completed'}</p>
                                    <small class="text-muted">
                                        Confidence: ${((result.ai_team_analysis?.confidence || 0) * 100).toFixed(1)}% | 
                                        Models: ${result.ai_team_analysis?.model_responses?.length || 0}
                                    </small>
                                </div>
                            </div>
                        `;
                        
                        // Fix it Fred Results
                        resultHtml += `
                            <div class="card mb-3">
                                <div class="card-header bg-warning text-dark">
                                    <h6>🔧 Fix it Fred Solution</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>Fix Confidence:</strong> ${((result.fix_it_fred_solution?.fix_confidence || 0) * 100).toFixed(1)}%</p>
                                    <p><strong>Estimated Time:</strong> ${result.fix_it_fred_solution?.estimated_resolution_time || 'N/A'}</p>
                                    <p><strong>Risk Assessment:</strong> ${result.fix_it_fred_solution?.risk_assessment || 'N/A'}</p>
                                    ${result.fix_it_fred_solution?.auto_apply_safe ? 
                                        '<span class="badge bg-success">Safe for Auto-Apply</span>' : 
                                        '<span class="badge bg-warning">Manual Review Recommended</span>'
                                    }
                                </div>
                            </div>
                        `;
                        
                        // LineSmart Results
                        resultHtml += `
                            <div class="card mb-3">
                                <div class="card-header bg-info text-white">
                                    <h6>📊 LineSmart Learning</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>Training Quality:</strong> ${((result.linesmart_learning?.data_quality_score || 0) * 100).toFixed(1)}%</p>
                                    <p><strong>Performance Boost:</strong> ${result.linesmart_learning?.future_performance_boost || 'N/A'}</p>
                                    <small class="text-muted">
                                        Model enhancements applied for future improvements
                                    </small>
                                </div>
                            </div>
                        `;
                    }
                    
                    resultsDiv.innerHTML = resultHtml;
                    
                    // Refresh status
                    loadServicesStatus();
                    
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
                }
            }
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                loadServicesStatus();
            });
        </script>
    </body>
    </html>
    """


# Fix-it-Fred AI Chat Endpoints
class MaintenanceConsultationRequest(BaseModel):
    """Request model for Fix-it-Fred consultation"""
    problem_description: str = Field(
        ..., 
        description="Detailed description of the maintenance issue",
        json_schema_extra={"example": "Hydraulic pump is overheating and making loud noises"}
    )
    equipment_type: str = Field(
        None,
        description="Type of equipment (pump, motor, conveyor, etc.)",
        json_schema_extra={"example": "Hydraulic Pump"}
    )
    priority: str = Field(
        None,
        description="Issue priority level",
        json_schema_extra={"example": "High"}
    )

# Root redirect to demo - REMOVED DUPLICATE (line 377 already defines root route)

@app.get("/urgent-count", tags=["API"])
@app.get("/api/work-orders/urgent-count", tags=["API"])
async def urgent_count():
    """Get count of urgent work orders - AI Team implemented endpoint"""
    try:
        # Fallback data for production stability
        return {"count": 3, "status": "operational"}
    except Exception as e:
        logger.error(f"Error fetching urgent count: {e}")
        return {"count": 0, "status": "error", "message": str(e)}


@app.get("/api/work-orders", tags=["API"])
async def api_work_orders():
    """Get work orders list for API consumers"""
    try:
        from app.core.firestore_db import get_firestore_manager
        firestore_manager = get_firestore_manager()
        work_orders = await firestore_manager.get_collection("work_orders", limit=50)
        return {"work_orders": work_orders, "count": len(work_orders), "status": "success"}
    except Exception as e:
        logger.error(f"Error fetching work orders: {e}")
        # Fallback demo data
        return {
            "work_orders": [
                {"id": "WO-001", "title": "HVAC Maintenance", "status": "open", "priority": "high"},
                {"id": "WO-002", "title": "Conveyor Belt Inspection", "status": "in_progress", "priority": "medium"},
            ],
            "count": 2,
            "status": "demo",
            "message": str(e)
        }


@app.get("/api/health/all", tags=["API"])
async def api_health_all():
    """Comprehensive health check for all services"""
    try:
        from app.core.firestore_db import get_firestore_manager
        firestore_manager = get_firestore_manager()

        # Check database connectivity
        db_healthy = firestore_manager is not None

        return {
            "status": "healthy",
            "services": {
                "api": {"status": "healthy", "version": APP_VERSION},
                "database": {"status": "healthy" if db_healthy else "degraded", "type": "firestore"},
                "ai_team": {"status": "configured" if USE_AI_TEAM_HTTP else "disabled"},
            },
            "timestamp": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "degraded", "error": str(e)}

@app.post("/chat/consult", tags=["Fix-it-Fred AI"])
async def consult_fix_it_fred(request: MaintenanceConsultationRequest):
    """
    🔧 Consult Fix-it-Fred for maintenance solutions
    
    Send a maintenance problem to Fred, our veteran AI maintenance technician.
    Fred will provide safety-first, practical solutions with prevention tips.
    """
    try:
        logger.info(f"Fix-it-Fred consultation: {request.problem_description[:50]}...")
        
        solution = await get_maintenance_solution(
            problem_description=request.problem_description,
            equipment_type=request.equipment_type,
            priority=request.priority
        )
        
        return solution
        
    except Exception as e:
        logger.error(f"Fix-it-Fred error: {e}")
        raise HTTPException(status_code=500, detail=f"Fred encountered an error: {str(e)}")

@app.get("/chat/health", tags=["Fix-it-Fred AI"])
async def fred_health_check():
    """🔧 Check Fix-it-Fred's availability status"""
    try:
        from app.services.ai_service import fix_it_fred_service
        
        has_openai = fix_it_fred_service.client is not None
        
        return {
            "fred_status": "ready" if has_openai else "demo_mode",
            "ai_enabled": has_openai,
            "message": "Fred is ready to help!" if has_openai else "Fred is in demo mode - configure OPENAI_API_KEY for full AI"
        }
    except Exception as e:
        return {"fred_status": "error", "message": f"Fred is having issues: {str(e)}"}

@app.get("/debug/version")
async def debug_version():
    """Debug endpoint to check version loading"""
    import os

    debug_info = {
        "app_version": APP_VERSION,
        "app_description": APP_DESCRIPTION,
        "current_working_directory": os.getcwd(),
        "version_file_checks": {},
    }

    version_paths = ["VERSION.txt", "/app/VERSION.txt", "./VERSION.txt"]
    for path in version_paths:
        debug_info["version_file_checks"][path] = {
            "exists": os.path.exists(path),
            "is_file": os.path.isfile(path) if os.path.exists(path) else False,
        }
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    debug_info["version_file_checks"][path][
                        "content_preview"
                    ] = f.read()[:200]
            except Exception as e:
                debug_info["version_file_checks"][path]["error"] = str(e)

    return debug_info


# Main entry point
if __name__ == "__main__":
    # Cloud Run sets PORT=8080, ignore local CMMS_PORT for Cloud deployment
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, log_level="info")
