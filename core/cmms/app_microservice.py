#!/usr/bin/env python3
"""
ChatterFix CMMS - Main Application Microservice
Streamlined FastAPI application that communicates with the database microservice.

This service handles:
- UI and business logic
- Authentication and authorization
- API endpoints for frontend
- Integration with external services
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
import json

# Import database client
from database_client import db_client, DatabaseClientError, check_database_health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("Starting ChatterFix CMMS Main Application...")
    
    # Check database service health
    try:
        health = check_database_health()
        logger.info(f"Database service health: {health['status']}")
    except Exception as e:
        logger.warning(f"Database service health check failed: {e}")
    
    yield
    
    logger.info("ChatterFix CMMS Main Application shutting down...")

app = FastAPI(
    title="ChatterFix CMMS",
    description="Comprehensive Maintenance Management System",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted successfully")
except Exception as e:
    logger.warning(f"Failed to mount static files: {e}")

# Security
security = HTTPBearer(auto_error=False)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def create_access_token(user_data: dict) -> str:
    """Create JWT access token"""
    to_encode = user_data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Verify JWT token"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# Basic HTML templates
HTML_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS Enterprise</title>
    <style>
        :root {{
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3d3d3d;
            --bg-card: rgba(45,45,45,0.8);
            --bg-header: rgba(26,26,26,0.95);
            --bg-nav: rgba(35,35,35,0.9);
            --accent-primary: #8B9467;
            --accent-secondary: #2E4053;
            --text-primary: #ffffff;
            --text-secondary: rgba(255,255,255,0.8);
            --text-muted: rgba(255,255,255,0.6);
            --border-color: rgba(255,255,255,0.1);
            --shadow-light: 0 4px 16px rgba(0,0,0,0.3);
            --shadow-heavy: 0 8px 32px rgba(0,0,0,0.5);
        }}
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 50%, var(--bg-tertiary) 100%);
            min-height: 100vh;
            color: var(--text-primary);
        }}
        .header {{
            background: var(--bg-header);
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-primary);
            border-bottom: 1px solid var(--border-color);
            box-shadow: var(--shadow-light);
        }}
        .logo {{
            font-size: 1.5em;
            font-weight: 700;
        }}
        .enterprise-badge {{
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: 10px;
        }}
        .cloud-badge {{
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }}
        .nav {{
            background: var(--bg-nav);
            padding: 15px 20px;
            display: flex;
            gap: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        .nav a {{
            color: var(--text-primary);
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }}
        .nav a:hover, .nav a.active {{
            background: var(--bg-card);
            border-color: var(--accent-primary);
            color: var(--accent-primary);
        }}
        .dashboard {{
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{
            background: var(--bg-card);
            padding: 25px;
            border-radius: 16px;
            backdrop-filter: blur(20px);
            color: var(--text-primary);
            box-shadow: var(--shadow-light);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        .card:hover {{
            box-shadow: var(--shadow-heavy);
            border-color: var(--accent-primary);
            transform: translateY(-2px);
        }}
        .card h3 {{
            margin: 0 0 15px 0;
            color: var(--text-primary);
            font-size: 1.2em;
        }}
        .card .count {{
            font-size: 2.5em;
            font-weight: 700;
            margin: 10px 0;
            background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .btn {{
            background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(139,148,103,0.4);
            color: white;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            🔧 ChatterFix CMMS 
            <span class="enterprise-badge">ENTERPRISE</span>
            <span class="cloud-badge">CLOUD</span>
        </div>
    </div>
    <div class="nav">
        <a href="/" class="active">Dashboard</a>
        <a href="/workorders">Work Orders</a>
        <a href="/assets">Assets</a>
        <a href="/parts">Parts</a>
        <a href="/health">Health</a>
    </div>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check"""
    try:
        # Check database service
        db_health = check_database_health()
        
        app_health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "main_application",
            "database_service": db_health
        }
        
        if db_health.get("status") != "healthy":
            app_health["status"] = "degraded"
        
        return app_health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "service": "main_application",
            "error": str(e)
        }

# Home page
@app.get("/", response_class=HTMLResponse)
async def home():
    """Main dashboard"""
    try:
        # Get overview statistics from database service
        stats = await db_client.async_client.get_overview_stats()
        
        content = f"""
        <div class="dashboard">
            <div class="card">
                <h3>🔧 Work Orders</h3>
                <div class="count">{stats.get('work_orders_count', 0)}</div>
                <p>Active maintenance requests and scheduled tasks</p>
                <a href="/workorders" class="btn">View All Work Orders</a>
            </div>
            <div class="card">
                <h3>🏭 Assets</h3>
                <div class="count">{stats.get('assets_count', 0)}</div>
                <p>Equipment and infrastructure under management</p>
                <a href="/assets" class="btn">View All Assets</a>
            </div>
            <div class="card">
                <h3>📦 Parts</h3>
                <div class="count">{stats.get('parts_count', 0)}</div>
                <p>Inventory and spare parts management</p>
                <a href="/parts" class="btn">View All Parts</a>
            </div>
            <div class="card">
                <h3>👥 Users</h3>
                <div class="count">{stats.get('users_count', 4)}</div>
                <p>System users and technicians</p>
                <a href="/health" class="btn">System Health</a>
            </div>
        </div>
        """
        
        return HTML_BASE.format(content=content)
        
    except Exception as e:
        logger.error(f"Dashboard failed: {e}")
        content = f"""
        <div class="alert alert-danger">
            <h4>Service Error</h4>
            <p>Unable to load dashboard data: {str(e)}</p>
            <p>Please check if the database service is running.</p>
        </div>
        """
        return HTML_BASE.format(content=content)

# Work Orders page
@app.get("/workorders", response_class=HTMLResponse)
async def work_orders_page():
    """Work orders listing page"""
    try:
        work_orders = db_client.get_work_orders()
        
        rows = ""
        for wo in work_orders:
            rows += f"""
            <tr>
                <td>{wo.get('id', '')}</td>
                <td>{wo.get('title', '')}</td>
                <td><span class="badge bg-{'success' if wo.get('status') == 'completed' else 'warning'}">{wo.get('status', '')}</span></td>
                <td><span class="badge bg-{'danger' if wo.get('priority') == 'high' else 'info'}">{wo.get('priority', '')}</span></td>
                <td>{wo.get('assigned_username', 'Unassigned')}</td>
                <td>{wo.get('created_at', '')[:10] if wo.get('created_at') else ''}</td>
            </tr>
            """
        
        content = f"""
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Work Orders</h1>
            <button class="btn btn-primary" onclick="createWorkOrder()">Create Work Order</button>
        </div>
        <div class="card">
            <div class="card-body">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Status</th>
                            <th>Priority</th>
                            <th>Assigned To</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
        function createWorkOrder() {{
            const title = prompt("Work Order Title:");
            const description = prompt("Description:");
            
            if (title && description) {{
                fetch('/api/work-orders', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{'title': title, 'description': description}})
                }})
                .then(response => response.json())
                .then(data => {{
                    alert('Work order created successfully!');
                    location.reload();
                }})
                .catch(error => alert('Error creating work order: ' + error));
            }}
        }}
        </script>
        """
        
        return HTML_BASE.format(content=content)
        
    except Exception as e:
        logger.error(f"Work orders page failed: {e}")
        content = f"""
        <div class="alert alert-danger">
            <h4>Service Error</h4>
            <p>Unable to load work orders: {str(e)}</p>
        </div>
        """
        return HTML_BASE.format(content=content)

# Assets page
@app.get("/assets", response_class=HTMLResponse)
async def assets_page():
    """Assets listing page"""
    try:
        assets = db_client.get_assets()
        
        rows = ""
        for asset in assets:
            rows += f"""
            <tr>
                <td>{asset.get('id', '')}</td>
                <td>{asset.get('name', '')}</td>
                <td>{asset.get('asset_type', '')}</td>
                <td>{asset.get('location', '')}</td>
                <td><span class="badge bg-{'success' if asset.get('status') == 'active' else 'secondary'}">{asset.get('status', '')}</span></td>
                <td>{asset.get('created_at', '')[:10] if asset.get('created_at') else ''}</td>
            </tr>
            """
        
        content = f"""
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Assets</h1>
            <button class="btn btn-primary" onclick="createAsset()">Add Asset</button>
        </div>
        <div class="card">
            <div class="card-body">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Location</th>
                            <th>Status</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
        function createAsset() {{
            const name = prompt("Asset Name:");
            const assetType = prompt("Asset Type:");
            const location = prompt("Location:");
            
            if (name && assetType && location) {{
                fetch('/api/assets', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{'name': name, 'asset_type': assetType, 'location': location, 'description': ''}})
                }})
                .then(response => response.json())
                .then(data => {{
                    alert('Asset created successfully!');
                    location.reload();
                }})
                .catch(error => alert('Error creating asset: ' + error));
            }}
        }}
        </script>
        """
        
        return HTML_BASE.format(content=content)
        
    except Exception as e:
        logger.error(f"Assets page failed: {e}")
        content = f"""
        <div class="alert alert-danger">
            <h4>Service Error</h4>
            <p>Unable to load assets: {str(e)}</p>
        </div>
        """
        return HTML_BASE.format(content=content)

# Parts page
@app.get("/parts", response_class=HTMLResponse)
async def parts_page():
    """Parts listing page"""
    try:
        parts = db_client.get_parts()
        
        rows = ""
        for part in parts:
            rows += f"""
            <tr>
                <td>{part.get('id', '')}</td>
                <td>{part.get('name', '')}</td>
                <td>{part.get('part_number', '')}</td>
                <td>{part.get('quantity', 0)}</td>
                <td>{part.get('location', '')}</td>
                <td>{part.get('supplier', '')}</td>
            </tr>
            """
        
        content = f"""
        <h1>Parts Inventory</h1>
        <div class="card">
            <div class="card-body">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Part Number</th>
                            <th>Quantity</th>
                            <th>Location</th>
                            <th>Supplier</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return HTML_BASE.format(content=content)
        
    except Exception as e:
        logger.error(f"Parts page failed: {e}")
        content = f"""
        <div class="alert alert-danger">
            <h4>Service Error</h4>
            <p>Unable to load parts: {str(e)}</p>
        </div>
        """
        return HTML_BASE.format(content=content)

# API Endpoints that proxy to database service
@app.get("/api/work-orders")
async def api_get_work_orders(limit: int = 100, offset: int = 0):
    """Get work orders via database service"""
    try:
        return db_client.get_work_orders(limit, offset)
    except DatabaseClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders")
async def api_create_work_order(work_order: dict):
    """Create work order via database service"""
    try:
        return db_client.create_work_order(work_order)
    except DatabaseClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets")
async def api_get_assets(limit: int = 100, offset: int = 0):
    """Get assets via database service"""
    try:
        return db_client.get_assets(limit, offset)
    except DatabaseClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets")
async def api_create_asset(asset: dict):
    """Create asset via database service"""
    try:
        return db_client.create_asset(asset)
    except DatabaseClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts")
async def api_get_parts(limit: int = 100, offset: int = 0):
    """Get parts via database service"""
    try:
        return db_client.get_parts(limit, offset)
    except DatabaseClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/overview")
async def api_get_stats():
    """Get overview statistics via database service"""
    try:
        return db_client.get_overview_stats()
    except DatabaseClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)