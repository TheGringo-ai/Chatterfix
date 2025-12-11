import logging
import os

from dotenv import load_dotenv

# Load environment variables (override system defaults)
load_dotenv(override=True)

print("DEBUG: STARTING NEW VERSION WITH FIX - 2025-12-05")

# Define version information immediately to avoid circular import issues
APP_VERSION = "2.1.0-enterprise-planner"
APP_DESCRIPTION = "Enhanced Demo Planner with Advanced Scheduler"

import uvicorn
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.db_adapter import get_db_adapter
from app.middleware import ErrorTrackingMiddleware

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

# GRADUALLY RE-ENABLE ROUTERS - Start with core functionality
try:
    from app.routers import (
        health,
        landing,
        dashboard,
        auth,
        signup,
        settings,
    )
    CORE_ROUTERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import core routers: {e}")
    CORE_ROUTERS_AVAILABLE = False

# Import additional routers
try:
    from app.routers import (
        demo,
        public_demo,
        work_orders,
        assets,
        inventory,
        team,
        planner,
        purchasing,
        ai_team_collaboration,
        fix_it_fred,
        linesmart_integration,
    )
    EXTENDED_ROUTERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import extended routers: {e}")
    EXTENDED_ROUTERS_AVAILABLE = False


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

# Add middleware - DISABLED ProxyHeadersMiddleware for debugging
# app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")  # Trust Cloud Run proxy

# Add error tracking middleware
app.add_middleware(
    ErrorTrackingMiddleware,
    sentry_dsn=os.getenv("SENTRY_DSN"),  # Optional: set SENTRY_DSN env var
    environment=os.getenv("ENVIRONMENT", "development"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production - DISABLED for Cloud Run
# if os.getenv("ENVIRONMENT") == "production":
#     app.add_middleware(
#         TrustedHostMiddleware, allowed_hosts=["*"]  # Allow all hosts for Cloud Run flexibility
#     )

# Add rate limiting - DISABLED for debugging host header issue
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    app.include_router(auth.router)     # Authentication
    app.include_router(signup.router)   # User signup
    app.include_router(settings.router) # Settings

# Include extended functionality
if EXTENDED_ROUTERS_AVAILABLE:
    app.include_router(demo.router)        # Demo routes
    app.include_router(public_demo.router) # Public demo routes (no auth required)
    app.include_router(work_orders.router) # Work orders
    app.include_router(assets.router)      # Assets
    app.include_router(inventory.router)   # Inventory
    app.include_router(team.router)        # Team management
    app.include_router(planner.router)     # Planner functionality
    app.include_router(purchasing.router)  # Purchasing and POS system
    app.include_router(ai_team_collaboration.router)  # AI Team gRPC Collaboration
    app.include_router(fix_it_fred.router)  # Fix it Fred AI-powered autonomous fixing
    app.include_router(linesmart_integration.router)  # LineSmart training service integration


# Root endpoint - redirect to landing page
@app.get("/")
async def root():
    """Root endpoint - redirect to landing page"""
    if CORE_ROUTERS_AVAILABLE:
        return RedirectResponse(url="/landing", status_code=302)
    else:
        # Fallback if routers not available
        return {
            "message": "🚀 ChatterFix CMMS is running!",
            "status": "healthy",
            "version": APP_VERSION,
            "note": "Some routers disabled due to import issues"
        }


# Simple test endpoint to verify deployment
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify deployment works"""
    return {
        "status": "success",
        "message": "ChatterFix is running with CI/CD!",
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "timestamp": "2025-12-10",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
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
            "LineSmart Training Integration"
        ],
        "ai_services": {
            "ai_team": "/ai-team",
            "fix_it_fred": "/fix-it-fred", 
            "linesmart": "/linesmart",
            "unified_integration": "/unified-ai"
        }
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
    port = int(os.getenv("PORT", os.getenv("CMMS_PORT", "8000")))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, log_level="info")
