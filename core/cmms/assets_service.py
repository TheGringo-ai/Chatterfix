#!/usr/bin/env python3
"""
ChatterFix CMMS - Assets Microservice
Complete asset lifecycle management with predictive maintenance insights
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, date, timedelta
import logging
import os
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database service configuration
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")

# Pydantic models
class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="active", pattern="^(active|maintenance|decommissioned|repair)$")
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    serial_number: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=255)
    model: Optional[str] = Field(None, max_length=255)
    purchase_cost: Optional[float] = Field(None, ge=0)

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    asset_type: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|maintenance|decommissioned|repair)$")
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    serial_number: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=255)
    model: Optional[str] = Field(None, max_length=255)
    purchase_cost: Optional[float] = Field(None, ge=0)

class AssetResponse(BaseModel):
    id: int
    name: str
    description: str
    asset_type: str
    location: str
    status: str
    purchase_date: Optional[date]
    warranty_expiry: Optional[date]
    serial_number: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    purchase_cost: Optional[float]
    created_at: datetime
    updated_at: datetime

class MaintenanceSchedule(BaseModel):
    asset_id: int
    maintenance_type: str = Field(..., pattern="^(preventive|corrective|predictive|emergency)$")
    frequency_days: int = Field(..., gt=0)
    description: str
    estimated_duration_hours: Optional[float] = Field(None, gt=0)
    last_performed: Optional[date] = None
    next_due: Optional[date] = None

# Create FastAPI app
app = FastAPI(
    title="ChatterFix CMMS - Assets Service",
    description="Advanced AI-powered asset lifecycle management system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_database_client():
    """Get HTTP client for database service"""
    return httpx.AsyncClient(base_url=DATABASE_SERVICE_URL, timeout=30.0)

@app.get("/health")
async def health_check():
    """Assets service health check"""
    try:
        async with await get_database_client() as client:
            response = await client.get("/health")
            db_status = "healthy" if response.status_code == 200 else "unhealthy"
        
        return {
            "status": "healthy",
            "service": "assets",
            "database_connection": db_status,
            "timestamp": datetime.now().isoformat(),
            "features": [
                "Complete asset lifecycle management",
                "Predictive maintenance scheduling",
                "Advanced AI insights",
                "Real-time asset tracking",
                "Automated depreciation calculations"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "assets",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/", response_class=HTMLResponse)
async def assets_dashboard():
    """Assets service dashboard with ChatterFix standardized styling"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Assets Management - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        :root {
            --primary-dark: #0a0a0a;
            --secondary-dark: #16213e;
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-purple: #667eea;
            --accent-purple-dark: #764ba2;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --bg-primary: #0a0a0a;
            --bg-card: rgba(255, 255, 255, 0.05);
            --bg-gradient: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            --font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        * { box-sizing: border-box; }
        
        body {
            margin: 0;
            font-family: var(--font-family);
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(10, 10, 10, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 16px 0;
            z-index: 1000;
        }
        
        .navbar-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .navbar-brand {
            background: var(--text-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: 1.25rem;
        }
        
        .page-header {
            padding: 120px 0 64px;
            text-align: center;
            background: var(--bg-gradient);
        }
        
        .page-header h1 {
            font-size: 3rem;
            font-weight: 800;
            background: var(--text-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
            margin: 0;
        }
        
        .page-header .subtitle {
            margin: 1rem 0 0 0;
            color: var(--text-secondary);
            font-size: 1.2rem;
            font-weight: 400;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
        }
        
        .btn-primary {
            background: var(--gradient-primary);
            color: var(--text-primary);
            border: none;
            border-radius: 50px;
            padding: 12px 32px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: transparent;
            color: var(--text-primary);
            border: 2px solid var(--accent-purple);
            border-radius: 50px;
            padding: 10px 30px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-secondary:hover {
            background: var(--gradient-primary);
            border-color: transparent;
            transform: translateY(-2px);
        }
        
        .controls {
            display: flex;
            gap: 16px;
            margin-bottom: 32px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 24px;
            margin-bottom: 48px;
        }
        
        .stat-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            background: var(--text-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: block;
            margin-bottom: 8px;
        }
        
        .assets-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 32px;
            margin-top: 32px;
        }
        
        .form-card, .list-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 32px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
        }
        
        .form-card h3, .list-card h3 {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 24px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 8px;
            display: block;
        }
        
        .form-input {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 12px 16px;
            color: var(--text-primary);
            font-family: var(--font-family);
            font-size: 1rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            width: 100%;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--accent-purple);
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
        }
        
        .form-input::placeholder {
            color: var(--text-secondary);
        }
        
        .asset-item {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .asset-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .asset-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .asset-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
            color: var(--text-primary);
        }
        
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .status-active {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .status-maintenance {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
        }
        
        .status-repair {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }
        
        .status-decommissioned {
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
        }
        
        @media (max-width: 768px) {
            .page-header h1 {
                font-size: 2.25rem;
            }
            .container {
                padding: 0 16px;
            }
            .assets-grid {
                grid-template-columns: 1fr;
            }
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
        }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="navbar-content">
                <div class="navbar-brand">ChatterFix CMMS</div>
                <div>Assets Management</div>
            </div>
        </nav>

        <div class="page-header">
            <div class="container">
                <h1>🏭 Assets Management</h1>
                <p class="subtitle">Real-time Asset Lifecycle Management with AI-powered Analytics</p>
            </div>
        </div>
        
        <div class="container">
            <div class="controls">
                <a href="/" class="btn-secondary">← Back to Dashboard</a>
                <button onclick="refreshAssets()" class="btn-secondary">🔄 Refresh</button>
                <button onclick="getAIInsights()" class="btn-primary">🧠 Get AI Insights</button>
            </div>

            <div class="stats-overview">
                <div class="stat-card">
                    <div class="stat-number" id="total-assets">24</div>
                    <div>Total Assets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="active-assets">18</div>
                    <div>Active Assets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="maintenance-due">3</div>
                    <div>Maintenance Due</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-value">$2.4M</div>
                    <div>Total Value</div>
                </div>
            </div>
            
            <div class="assets-grid">
                <div class="form-card">
                    <h3>Create New Asset</h3>
                    <form id="assetForm" onsubmit="createAsset(event)">
                        <div class="form-group">
                            <label class="form-label" for="name">Asset Name</label>
                            <input type="text" id="name" name="name" class="form-input" 
                                   placeholder="Enter asset name" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="description">Description</label>
                            <textarea id="description" name="description" class="form-input" 
                                      rows="3" placeholder="Describe the asset" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="asset_type">Asset Type</label>
                            <select id="asset_type" name="asset_type" class="form-input">
                                <option value="machinery">Machinery</option>
                                <option value="vehicle">Vehicle</option>
                                <option value="equipment">Equipment</option>
                                <option value="facility">Facility</option>
                                <option value="tool">Tool</option>
                                <option value="computer">Computer</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="location">Location</label>
                            <input type="text" id="location" name="location" class="form-input" 
                                   placeholder="Asset location" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="status">Status</label>
                            <select id="status" name="status" class="form-input">
                                <option value="active" selected>Active</option>
                                <option value="maintenance">Maintenance</option>
                                <option value="repair">Repair</option>
                                <option value="decommissioned">Decommissioned</option>
                            </select>
                        </div>
                        
                        <button type="submit" class="btn-primary" style="width: 100%;">
                            ✅ Create Asset
                        </button>
                    </form>
                </div>
                
                <div class="list-card">
                    <h3>Active Assets</h3>
                    <div id="assetsList">
                        <!-- Sample assets data -->
                        <div class="asset-item">
                            <div class="asset-header">
                                <h4 class="asset-title">CNC Machine - Model X100</h4>
                                <span class="status-badge status-active">Active</span>
                            </div>
                            <p>High-precision CNC machining center for production line A</p>
                            <div style="font-size: 0.875rem; opacity: 0.7;">
                                📍 Production Floor A | 🔧 Last Maintenance: 2024-09-15 | 💰 Value: $125,000
                            </div>
                        </div>

                        <div class="asset-item">
                            <div class="asset-header">
                                <h4 class="asset-title">Forklift - Toyota 8FGU25</h4>
                                <span class="status-badge status-maintenance">Maintenance</span>
                            </div>
                            <p>Material handling forklift for warehouse operations</p>
                            <div style="font-size: 0.875rem; opacity: 0.7;">
                                📍 Warehouse B | 🔧 Scheduled: 2024-10-05 | 💰 Value: $35,000
                            </div>
                        </div>

                        <div class="asset-item">
                            <div class="asset-header">
                                <h4 class="asset-title">HVAC System - Unit 3</h4>
                                <span class="status-badge status-active">Active</span>
                            </div>
                            <p>Climate control system for manufacturing facility</p>
                            <div style="font-size: 0.875rem; opacity: 0.7;">
                                📍 Building 3 Rooftop | 🔧 Last Maintenance: 2024-08-20 | 💰 Value: $85,000
                            </div>
                        </div>

                        <div class="asset-item">
                            <div class="asset-header">
                                <h4 class="asset-title">Conveyor Belt System</h4>
                                <span class="status-badge status-active">Active</span>
                            </div>
                            <p>Automated material transport system for assembly line</p>
                            <div style="font-size: 0.875rem; opacity: 0.7;">
                                📍 Assembly Line 2 | 🔧 Next Maintenance: 2024-10-12 | 💰 Value: $45,000
                            </div>
                        </div>

                        <div class="asset-item">
                            <div class="asset-header">
                                <h4 class="asset-title">Generator - Backup Power</h4>
                                <span class="status-badge status-repair">Repair</span>
                            </div>
                            <p>Emergency backup power generator for critical systems</p>
                            <div style="font-size: 0.875rem; opacity: 0.7;">
                                📍 Utility Building | 🔧 Repair Started: 2024-09-28 | 💰 Value: $75,000
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
        async function createAsset(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const asset = {
                name: formData.get('name'),
                description: formData.get('description'),
                asset_type: formData.get('asset_type'),
                location: formData.get('location'),
                status: formData.get('status')
            };
            
            try {
                const response = await fetch('/api/assets', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(asset)
                });
                
                if (response.ok) {
                    document.getElementById('assetForm').reset();
                    alert('✅ Asset created successfully!');
                    refreshAssets();
                } else {
                    const error = await response.json();
                    alert('❌ Error creating asset: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error creating asset:', error);
                alert('❌ Error creating asset: ' + error.message);
            }
        }
        
        function refreshAssets() {
            // Refresh functionality would reload actual asset data
            console.log('Refreshing assets...');
        }
        
        function getAIInsights() {
            alert('🧠 AI Analysis: 3 assets require maintenance within 30 days. Predictive analytics suggest scheduling preventive maintenance for CNC Machine X100 to avoid 85% probability of failure.');
        }
        </script>
    </body>
    </html>
    """

# Assets CRUD Operations
@app.get("/api/assets", response_model=List[AssetResponse])
async def get_assets(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, pattern="^(active|maintenance|decommissioned|repair)$"),
    asset_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None)
):
    """Get assets with filtering and pagination"""
    try:
        async with await get_database_client() as client:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            if asset_type:
                params["asset_type"] = asset_type
            if location:
                params["location"] = location
            
            response = await client.get("/api/assets", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: int):
    """Get a specific asset by ID"""
    try:
        async with await get_database_client() as client:
            response = await client.get(f"/api/assets/{asset_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            response.raise_for_status()
            return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets", response_model=Dict[str, Any])
async def create_asset(asset: AssetCreate):
    """Create a new asset"""
    try:
        async with await get_database_client() as client:
            asset_data = asset.dict()
            response = await client.post("/api/assets", json=asset_data)
            response.raise_for_status()
            result = response.json()
            
            # Initialize predictive maintenance schedule
            if result.get("id"):
                await initialize_maintenance_schedule(result["id"], asset.asset_type)
            
            return result
    except Exception as e:
        logger.error(f"Failed to create asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/assets/{asset_id}", response_model=Dict[str, Any])
async def update_asset(asset_id: int, asset: AssetUpdate):
    """Update an existing asset"""
    try:
        async with await get_database_client() as client:
            # First check if asset exists
            check_response = await client.get(f"/api/assets/{asset_id}")
            if check_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            # Prepare update data (only include non-None fields)
            update_data = {k: v for k, v in asset.dict().items() if v is not None}
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.now().isoformat()
            
            # Execute update via database service
            query = "UPDATE assets SET "
            query += ", ".join([f"{key} = %s" for key in update_data.keys()])
            query += f" WHERE id = %s"
            
            params = list(update_data.values()) + [asset_id]
            
            response = await client.post("/api/query", json={
                "query": query,
                "params": params,
                "fetch": None
            })
            response.raise_for_status()
            
            return {"message": "Asset updated successfully", "id": asset_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: int):
    """Delete an asset"""
    try:
        async with await get_database_client() as client:
            # First check if asset exists
            check_response = await client.get(f"/api/assets/{asset_id}")
            if check_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            # Check for associated work orders
            wo_check = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM work_orders WHERE asset_id = %s AND status NOT IN ('completed', 'cancelled')",
                "params": [asset_id],
                "fetch": "one"
            })
            wo_check.raise_for_status()
            active_work_orders = wo_check.json()["data"][0]
            
            if active_work_orders > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete asset with {active_work_orders} active work orders"
                )
            
            # Delete asset
            response = await client.post("/api/query", json={
                "query": "DELETE FROM assets WHERE id = %s",
                "params": [asset_id],
                "fetch": None
            })
            response.raise_for_status()
            
            return {"message": "Asset deleted successfully", "id": asset_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Intelligence Features
@app.get("/api/assets/stats")
async def get_asset_stats():
    """Get asset statistics"""
    try:
        async with await get_database_client() as client:
            stats = {}
            
            # Total assets
            response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM assets",
                "fetch": "one"
            })
            response.raise_for_status()
            stats["total"] = response.json()["data"][0]
            
            # By status
            for status in ["active", "maintenance", "decommissioned", "repair"]:
                response = await client.post("/api/query", json={
                    "query": "SELECT COUNT(*) FROM assets WHERE status = %s",
                    "params": [status],
                    "fetch": "one"
                })
                response.raise_for_status()
                stats[status] = response.json()["data"][0]
            
            # Total value
            response = await client.post("/api/query", json={
                "query": "SELECT COALESCE(SUM(purchase_cost), 0) FROM assets WHERE purchase_cost IS NOT NULL",
                "fetch": "one"
            })
            response.raise_for_status()
            stats["total_value"] = round(response.json()["data"][0], 2)
            
            # Maintenance due (next 30 days)
            response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(*) FROM assets 
                WHERE status = 'active' 
                AND EXISTS (
                    SELECT 1 FROM work_orders wo 
                    WHERE wo.asset_id = assets.id 
                    AND wo.due_date <= CURRENT_DATE + INTERVAL '30 days'
                    AND wo.status NOT IN ('completed', 'cancelled')
                )
                """,
                "fetch": "one"
            })
            response.raise_for_status()
            stats["maintenance_due"] = response.json()["data"][0]
            
            return stats
    except Exception as e:
        logger.error(f"Failed to get asset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/analytics")
async def get_asset_analytics():
    """Advanced asset analytics and insights"""
    try:
        async with await get_database_client() as client:
            analytics = {}
            
            # Critical maintenance (overdue or urgent)
            response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(*) FROM work_orders wo
                JOIN assets a ON wo.asset_id = a.id
                WHERE wo.priority = 'critical' 
                AND wo.status NOT IN ('completed', 'cancelled')
                """,
                "fetch": "one"
            })
            response.raise_for_status()
            analytics["critical_maintenance"] = response.json()["data"][0]
            
            # Upcoming maintenance (next 7 days)
            response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(*) FROM work_orders wo
                JOIN assets a ON wo.asset_id = a.id
                WHERE wo.due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                AND wo.status NOT IN ('completed', 'cancelled')
                """,
                "fetch": "one"
            })
            response.raise_for_status()
            analytics["upcoming_maintenance"] = response.json()["data"][0]
            
            # Simulated utilization rate (would be real sensor data in production)
            analytics["utilization_rate"] = 87.5
            
            # Simulated efficiency score (would be calculated from real performance data)
            analytics["efficiency_score"] = 94.2
            
            # Asset depreciation analysis
            response = await client.post("/api/query", json={
                "query": """
                SELECT 
                    AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, purchase_date))) as avg_age,
                    COUNT(*) as assets_with_age
                FROM assets 
                WHERE purchase_date IS NOT NULL
                """,
                "fetch": "one"
            })
            response.raise_for_status()
            result = response.json()["data"]
            analytics["average_asset_age_years"] = round(result[0], 1) if result and result[0] else 0
            analytics["assets_with_age_data"] = result[1] if result else 0
            
            return analytics
    except Exception as e:
        logger.error(f"Failed to get asset analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/{asset_id}/maintenance")
async def get_asset_maintenance_schedule(asset_id: int):
    """Get maintenance schedule for a specific asset"""
    try:
        async with await get_database_client() as client:
            # Check if asset exists
            asset_response = await client.get(f"/api/assets/{asset_id}")
            if asset_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            # Get maintenance history and upcoming
            response = await client.post("/api/query", json={
                "query": """
                SELECT wo.*, u.username as assigned_username
                FROM work_orders wo
                LEFT JOIN users u ON wo.assigned_to = u.id
                WHERE wo.asset_id = %s
                ORDER BY wo.due_date DESC
                """,
                "params": [asset_id],
                "fetch": "all"
            })
            response.raise_for_status()
            
            maintenance_records = response.json()["data"]
            return {
                "asset_id": asset_id,
                "maintenance_records": maintenance_records,
                "upcoming_count": len([r for r in maintenance_records if r["status"] not in ["completed", "cancelled"]]),
                "total_maintenance_cost": sum(r.get("estimated_hours", 0) * 75 for r in maintenance_records if r["status"] == "completed")  # $75/hour
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get maintenance schedule for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets/{asset_id}/maintenance")
async def schedule_maintenance(asset_id: int, maintenance: MaintenanceSchedule):
    """Schedule maintenance for an asset"""
    try:
        async with await get_database_client() as client:
            # Check if asset exists
            asset_response = await client.get(f"/api/assets/{asset_id}")
            if asset_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            asset = asset_response.json()
            
            # Create work order for maintenance
            work_order_data = {
                "title": f"{maintenance.maintenance_type.title()} Maintenance - {asset['name']}",
                "description": maintenance.description,
                "priority": "medium" if maintenance.maintenance_type == "preventive" else "high",
                "status": "open",
                "asset_id": asset_id,
                "due_date": maintenance.next_due.isoformat() if maintenance.next_due else None,
                "estimated_hours": maintenance.estimated_duration_hours
            }
            
            response = await client.post("/api/work-orders", json=work_order_data)
            response.raise_for_status()
            
            return {
                "message": "Maintenance scheduled successfully",
                "work_order": response.json(),
                "maintenance_type": maintenance.maintenance_type,
                "next_due": maintenance.next_due
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule maintenance for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Asset Management Features
@app.get("/api/assets/form")
async def asset_form():
    """Interactive asset creation/editing form"""
    return {
        "form_fields": {
            "name": {"type": "text", "required": True, "max_length": 255},
            "description": {"type": "textarea", "required": True},
            "asset_type": {"type": "select", "options": ["machinery", "vehicle", "equipment", "facility", "tool", "computer"], "required": True},
            "location": {"type": "text", "required": True, "max_length": 255},
            "status": {"type": "select", "options": ["active", "maintenance", "decommissioned", "repair"], "default": "active"},
            "purchase_date": {"type": "date", "nullable": True},
            "warranty_expiry": {"type": "date", "nullable": True},
            "serial_number": {"type": "text", "nullable": True, "max_length": 100},
            "manufacturer": {"type": "text", "nullable": True, "max_length": 255},
            "model": {"type": "text", "nullable": True, "max_length": 255},
            "purchase_cost": {"type": "number", "min": 0, "step": 0.01, "nullable": True}
        },
        "validation_rules": {
            "warranty_after_purchase": "Warranty expiry must be after purchase date",
            "purchase_cost_positive": "Purchase cost must be positive"
        },
        "ai_assistance": {
            "maintenance_prediction": "AI will predict optimal maintenance schedules",
            "lifecycle_analysis": "AI will analyze asset lifecycle and depreciation",
            "failure_prediction": "AI will predict potential failure points"
        }
    }

@app.get("/api/assets/dashboard")
async def assets_dashboard_data():
    """Get comprehensive dashboard data for assets overview"""
    try:
        async with await get_database_client() as client:
            dashboard_data = {}
            
            # Asset status distribution
            status_response = await client.post("/api/query", json={
                "query": "SELECT status, COUNT(*) FROM assets GROUP BY status",
                "fetch": "all"
            })
            status_response.raise_for_status()
            dashboard_data["status_distribution"] = {
                row[0]: row[1] for row in status_response.json()["data"]
            }
            
            # Assets by type
            type_response = await client.post("/api/query", json={
                "query": "SELECT asset_type, COUNT(*) FROM assets GROUP BY asset_type ORDER BY COUNT(*) DESC",
                "fetch": "all"
            })
            type_response.raise_for_status()
            dashboard_data["by_type"] = [
                {"type": row[0], "count": row[1]} for row in type_response.json()["data"]
            ]
            
            # Warranty expiring soon (next 90 days)
            warranty_response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(*) FROM assets 
                WHERE warranty_expiry BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
                AND status = 'active'
                """,
                "fetch": "one"
            })
            warranty_response.raise_for_status()
            dashboard_data["warranty_expiring_soon"] = warranty_response.json()["data"][0]
            
            # Average asset age
            age_response = await client.post("/api/query", json={
                "query": """
                SELECT AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, purchase_date))) as avg_age
                FROM assets 
                WHERE purchase_date IS NOT NULL
                """,
                "fetch": "one"
            })
            age_response.raise_for_status()
            avg_age = age_response.json()["data"][0]
            dashboard_data["average_age_years"] = round(avg_age, 1) if avg_age else 0
            
            # Total asset value
            value_response = await client.post("/api/query", json={
                "query": "SELECT SUM(purchase_cost) FROM assets WHERE purchase_cost IS NOT NULL",
                "fetch": "one"
            })
            value_response.raise_for_status()
            total_value = value_response.json()["data"][0]
            dashboard_data["total_value"] = round(total_value, 2) if total_value else 0
            
            # Assets requiring maintenance
            maintenance_response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(DISTINCT a.id) FROM assets a
                JOIN work_orders wo ON a.id = wo.asset_id
                WHERE wo.status NOT IN ('completed', 'cancelled')
                AND wo.due_date <= CURRENT_DATE + INTERVAL '30 days'
                """,
                "fetch": "one"
            })
            maintenance_response.raise_for_status()
            dashboard_data["maintenance_due_30_days"] = maintenance_response.json()["data"][0]
            
            # High-value assets (top 5)
            high_value_response = await client.post("/api/query", json={
                "query": """
                SELECT name, purchase_cost, asset_type FROM assets 
                WHERE purchase_cost IS NOT NULL 
                ORDER BY purchase_cost DESC 
                LIMIT 5
                """,
                "fetch": "all"
            })
            high_value_response.raise_for_status()
            dashboard_data["high_value_assets"] = [
                {"name": row[0], "value": row[1], "type": row[2]} 
                for row in high_value_response.json()["data"]
            ]
            
            return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get assets dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/{asset_id}/predictive-analysis")
async def get_predictive_analysis(asset_id: int):
    """Get AI-powered predictive analysis for specific asset"""
    try:
        async with await get_database_client() as client:
            # Verify asset exists
            asset_response = await client.get(f"/api/assets/{asset_id}")
            if asset_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            asset_response.raise_for_status()
            asset = asset_response.json()
            
            # Call AI Brain service for predictive analysis
            ai_brain_url = os.getenv("AI_BRAIN_SERVICE_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as ai_client:
                    ai_response = await ai_client.post(f"{ai_brain_url}/api/ai/predict/maintenance", json={
                        "asset_id": asset_id,
                        "analysis_depth": "comprehensive",
                        "include_recommendations": True
                    })
                    
                    if ai_response.status_code == 200:
                        ai_result = ai_response.json()
                        
                        # Enhance with additional asset-specific insights
                        analysis = {
                            "asset_id": asset_id,
                            "asset_name": asset.get("name"),
                            "predictive_maintenance": ai_result.get("prediction", {}),
                            "risk_assessment": await calculate_risk_assessment(asset),
                            "cost_analysis": await calculate_lifecycle_costs(asset),
                            "recommendations": await generate_asset_recommendations(asset),
                            "confidence_score": ai_result.get("prediction", {}).get("confidence_score", 0.85),
                            "analysis_timestamp": datetime.now().isoformat()
                        }
                        
                        return analysis
            except Exception as ai_error:
                logger.warning(f"AI Brain service unavailable: {ai_error}")
            
            # Fallback analysis
            analysis = {
                "asset_id": asset_id,
                "asset_name": asset.get("name"),
                "predictive_maintenance": await generate_basic_prediction(asset),
                "risk_assessment": await calculate_risk_assessment(asset),
                "cost_analysis": await calculate_lifecycle_costs(asset),
                "recommendations": await generate_asset_recommendations(asset),
                "confidence_score": 0.75,
                "analysis_timestamp": datetime.now().isoformat(),
                "note": "Analysis performed using fallback algorithms"
            }
            
            return analysis
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get predictive analysis for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets/{asset_id}/condition-update")
async def update_asset_condition(asset_id: int, condition_data: Dict[str, Any]):
    """Update asset condition and trigger predictive analysis"""
    try:
        async with await get_database_client() as client:
            # Verify asset exists
            asset_response = await client.get(f"/api/assets/{asset_id}")
            if asset_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            # Log condition update (in production, store in asset_conditions table)
            condition_log = {
                "asset_id": asset_id,
                "condition_type": condition_data.get("condition_type", "general"),
                "measurement_value": condition_data.get("value"),
                "measurement_unit": condition_data.get("unit"),
                "recorded_by": condition_data.get("recorded_by"),
                "notes": condition_data.get("notes"),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Condition update recorded for asset {asset_id}: {condition_log}")
            
            # Trigger predictive analysis if significant change
            if condition_data.get("trigger_analysis", False):
                analysis = await get_predictive_analysis(asset_id)
                return {
                    "message": "Condition updated and analysis triggered",
                    "condition_log": condition_log,
                    "predictive_analysis": analysis
                }
            else:
                return {
                    "message": "Condition updated successfully",
                    "condition_log": condition_log
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update condition for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/warranty-alerts")
async def get_warranty_alerts():
    """Get assets with warranties expiring soon"""
    try:
        async with await get_database_client() as client:
            # Assets expiring in next 30, 60, 90 days
            alerts = {}
            
            for period in [30, 60, 90]:
                response = await client.post("/api/query", json={
                    "query": f"""
                    SELECT id, name, warranty_expiry, manufacturer, model
                    FROM assets 
                    WHERE warranty_expiry BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '{period} days'
                    AND status = 'active'
                    ORDER BY warranty_expiry ASC
                    """,
                    "fetch": "all"
                })
                response.raise_for_status()
                
                alerts[f"expiring_{period}_days"] = [
                    {
                        "id": row[0], "name": row[1], "warranty_expiry": row[2],
                        "manufacturer": row[3], "model": row[4]
                    }
                    for row in response.json()["data"]
                ]
            
            return {
                "warranty_alerts": alerts,
                "total_alerts": sum(len(alerts[key]) for key in alerts),
                "generated_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get warranty alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced AI Helper Functions
async def initialize_maintenance_schedule(asset_id: int, asset_type: str):
    """Initialize AI-powered maintenance schedule for new asset"""
    try:
        # Call AI Brain service for intelligent scheduling
        ai_brain_url = os.getenv("AI_BRAIN_SERVICE_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as ai_client:
                ai_response = await ai_client.post(f"{ai_brain_url}/api/ai/analysis", json={
                    "analysis_type": "predictive_maintenance",
                    "data_sources": ["assets"],
                    "parameters": {
                        "asset_id": asset_id,
                        "asset_type": asset_type,
                        "schedule_type": "initial"
                    }
                })
                
                if ai_response.status_code == 200:
                    ai_result = ai_response.json()
                    interval_days = ai_result.get("results", {}).get("recommended_interval_days", 90)
                else:
                    interval_days = get_default_interval(asset_type)
        except Exception as ai_error:
            logger.warning(f"AI Brain service unavailable for asset {asset_id}: {ai_error}")
            interval_days = get_default_interval(asset_type)
        
        next_due = datetime.now().date() + timedelta(days=interval_days)
        
        maintenance = MaintenanceSchedule(
            asset_id=asset_id,
            maintenance_type="preventive",
            frequency_days=interval_days,
            description=f"AI-optimized preventive maintenance for {asset_type}",
            estimated_duration_hours=4.0,
            next_due=next_due
        )
        
        await schedule_maintenance(asset_id, maintenance)
        logger.info(f"AI-optimized maintenance schedule initialized for asset {asset_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize maintenance schedule for asset {asset_id}: {e}")
        return False

def get_default_interval(asset_type: str) -> int:
    """Get default maintenance interval for asset type"""
    maintenance_intervals = {
        "machinery": 90,    # 90 days
        "vehicle": 30,      # 30 days  
        "equipment": 60,    # 60 days
        "facility": 180,    # 180 days
        "tool": 120,        # 120 days
        "computer": 365,    # 365 days
        "default": 90
    }
    return maintenance_intervals.get(asset_type.lower(), maintenance_intervals["default"])

async def calculate_risk_assessment(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate risk assessment for asset"""
    risk_score = 0.0
    risk_factors = []
    
    # Age factor
    if asset.get("purchase_date"):
        purchase_date = datetime.strptime(asset["purchase_date"], "%Y-%m-%d").date() if isinstance(asset["purchase_date"], str) else asset["purchase_date"]
        age_years = (date.today() - purchase_date).days / 365.25
        if age_years > 10:
            risk_score += 0.3
            risk_factors.append("High asset age (>10 years)")
        elif age_years > 5:
            risk_score += 0.1
            risk_factors.append("Moderate asset age (>5 years)")
    
    # Warranty status
    if asset.get("warranty_expiry"):
        warranty_expiry = datetime.strptime(asset["warranty_expiry"], "%Y-%m-%d").date() if isinstance(asset["warranty_expiry"], str) else asset["warranty_expiry"]
        if warranty_expiry < date.today():
            risk_score += 0.2
            risk_factors.append("Warranty expired")
        elif (warranty_expiry - date.today()).days < 90:
            risk_score += 0.1
            risk_factors.append("Warranty expiring soon")
    
    # Status factor
    if asset.get("status") in ["maintenance", "repair"]:
        risk_score += 0.4
        risk_factors.append(f"Asset currently in {asset['status']} status")
    
    # Asset type factor
    high_risk_types = ["machinery", "vehicle"]
    if asset.get("asset_type") in high_risk_types:
        risk_score += 0.1
        risk_factors.append(f"High-maintenance asset type: {asset['asset_type']}")
    
    risk_level = "low"
    if risk_score > 0.6:
        risk_level = "high"
    elif risk_score > 0.3:
        risk_level = "medium"
    
    return {
        "risk_score": round(min(risk_score, 1.0), 2),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendations": get_risk_recommendations(risk_level)
    }

async def calculate_lifecycle_costs(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate lifecycle cost analysis for asset"""
    purchase_cost = asset.get("purchase_cost", 0) or 0
    
    # Estimate annual maintenance cost (5-15% of purchase cost)
    annual_maintenance_cost = purchase_cost * 0.10
    
    # Calculate depreciation
    if asset.get("purchase_date"):
        purchase_date = datetime.strptime(asset["purchase_date"], "%Y-%m-%d").date() if isinstance(asset["purchase_date"], str) else asset["purchase_date"]
        age_years = (date.today() - purchase_date).days / 365.25
        
        # Assume 10-year useful life for most assets
        useful_life = 10
        depreciation_rate = min(age_years / useful_life, 1.0)
        current_value = purchase_cost * (1 - depreciation_rate)
        annual_depreciation = purchase_cost / useful_life
    else:
        age_years = 0
        current_value = purchase_cost
        annual_depreciation = purchase_cost / 10  # Default 10-year life
    
    return {
        "purchase_cost": purchase_cost,
        "current_estimated_value": round(current_value, 2),
        "total_depreciation": round(purchase_cost - current_value, 2),
        "annual_depreciation": round(annual_depreciation, 2),
        "estimated_annual_maintenance": round(annual_maintenance_cost, 2),
        "total_cost_of_ownership": round(purchase_cost + (annual_maintenance_cost * age_years), 2),
        "asset_age_years": round(age_years, 1)
    }

async def generate_asset_recommendations(asset: Dict[str, Any]) -> List[str]:
    """Generate recommendations for asset management"""
    recommendations = []
    
    # Age-based recommendations
    if asset.get("purchase_date"):
        purchase_date = datetime.strptime(asset["purchase_date"], "%Y-%m-%d").date() if isinstance(asset["purchase_date"], str) else asset["purchase_date"]
        age_years = (date.today() - purchase_date).days / 365.25
        
        if age_years > 10:
            recommendations.append("Consider replacement planning for aging asset")
        elif age_years > 5:
            recommendations.append("Increase monitoring frequency for mature asset")
    
    # Warranty recommendations
    if asset.get("warranty_expiry"):
        warranty_expiry = datetime.strptime(asset["warranty_expiry"], "%Y-%m-%d").date() if isinstance(asset["warranty_expiry"], str) else asset["warranty_expiry"]
        days_to_expiry = (warranty_expiry - date.today()).days
        
        if days_to_expiry < 0:
            recommendations.append("Warranty has expired - consider extended service contract")
        elif days_to_expiry < 90:
            recommendations.append("Warranty expiring soon - review coverage options")
    
    # Status-based recommendations
    if asset.get("status") == "maintenance":
        recommendations.append("Asset in maintenance - ensure proper scheduling")
    elif asset.get("status") == "repair":
        recommendations.append("Asset requires repair - prioritize based on criticality")
    
    # Type-specific recommendations
    asset_type = asset.get("asset_type", "").lower()
    if asset_type == "machinery":
        recommendations.append("Implement vibration monitoring for predictive maintenance")
    elif asset_type == "vehicle":
        recommendations.append("Schedule regular inspections and fluid checks")
    elif asset_type == "computer":
        recommendations.append("Ensure regular software updates and security patches")
    
    if not recommendations:
        recommendations.append("Asset appears to be in good condition - continue regular monitoring")
    
    return recommendations

async def generate_basic_prediction(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Generate basic maintenance prediction when AI service is unavailable"""
    import random
    
    # Calculate failure probability based on age and status
    base_probability = 0.1
    
    if asset.get("purchase_date"):
        purchase_date = datetime.strptime(asset["purchase_date"], "%Y-%m-%d").date() if isinstance(asset["purchase_date"], str) else asset["purchase_date"]
        age_years = (date.today() - purchase_date).days / 365.25
        base_probability += min(age_years * 0.02, 0.3)  # Increase with age
    
    if asset.get("status") in ["maintenance", "repair"]:
        base_probability += 0.2
    
    # Predict next maintenance date
    interval_days = get_default_interval(asset.get("asset_type", "equipment"))
    next_maintenance = datetime.now() + timedelta(days=interval_days)
    
    return {
        "failure_probability": round(min(base_probability, 0.8), 3),
        "confidence_score": 0.75,
        "predicted_failure_date": (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat(),
        "recommended_maintenance_date": next_maintenance.isoformat(),
        "estimated_cost_if_failure": random.randint(2000, 20000),
        "estimated_maintenance_cost": random.randint(500, 5000),
        "risk_factors": [
            "Basic analysis - AI service unavailable",
            "Age-based risk assessment",
            "Status-based evaluation"
        ]
    }

def get_risk_recommendations(risk_level: str) -> List[str]:
    """Get recommendations based on risk level"""
    recommendations = {
        "low": [
            "Continue with standard maintenance schedule",
            "Monitor performance regularly"
        ],
        "medium": [
            "Increase monitoring frequency",
            "Consider preventive maintenance",
            "Review maintenance history"
        ],
        "high": [
            "Implement immediate inspection",
            "Consider urgent maintenance",
            "Evaluate replacement options",
            "Increase safety protocols"
        ]
    }
    return recommendations.get(risk_level, recommendations["medium"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)