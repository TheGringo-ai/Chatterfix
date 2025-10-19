#!/usr/bin/env python3
"""
ChatterFix CMMS - Enhanced Main Application
Properly routes to all microservices with correct port mappings
"""

import logging
import httpx
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix CMMS",
    description="Complete AI-Enhanced Maintenance Management System",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Microservice URLs (matching the port configuration from local setup)
DATABASE_SERVICE_URL = "http://localhost:8001"
WORK_ORDERS_SERVICE_URL = "http://localhost:8002"
ASSETS_SERVICE_URL = "http://localhost:8003"
PARTS_SERVICE_URL = "http://localhost:8004"
FIX_IT_FRED_URL = "http://localhost:8005"
GROK_CONNECTOR_URL = "http://localhost:8006"
SECURITY_SERVICE_URL = "http://localhost:8007"
DOCUMENT_SERVICE_URL = "http://localhost:8008"

# Pydantic models
class WorkOrderCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    technician: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    technician: Optional[str] = None

class AssetCreate(BaseModel):
    name: str
    type: str
    location: str

class PartCreate(BaseModel):
    name: str
    part_number: str
    quantity: int
    min_stock: int
    price: float
    location: str
    category: str

@app.get("/")
async def root():
    """Main dashboard"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .services { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
            .service-card { background: #ecf0f1; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
            .service-card h3 { margin: 0 0 10px 0; color: #2c3e50; }
            .service-card p { margin: 0; color: #7f8c8d; }
            .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .status.running { background: #2ecc71; color: white; }
            .nav-links { text-align: center; margin: 30px 0; }
            .nav-links a { display: inline-block; margin: 0 15px; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
            .nav-links a:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 ChatterFix CMMS</h1>
            <p style="text-align: center; color: #7f8c8d; font-size: 18px;">Complete Maintenance Management System</p>
            
            <div class="nav-links">
                <a href="/work-orders">Work Orders</a>
                <a href="/assets">Assets</a>
                <a href="/parts">Parts</a>
                <a href="/health">System Health</a>
                <a href="/docs">API Documentation</a>
            </div>
            
            <div class="services">
                <div class="service-card">
                    <h3>🗄️ Database Service</h3>
                    <p>Central data management - Port 8001</p>
                    <span class="status running">Running</span>
                </div>
                <div class="service-card">
                    <h3>🔧 Work Orders Service</h3>
                    <p>Maintenance request management - Port 8002</p>
                    <span class="status running">Running</span>
                </div>
                <div class="service-card">
                    <h3>🏭 Assets Service</h3>
                    <p>Equipment and facility tracking - Port 8003</p>
                    <span class="status running">Running</span>
                </div>
                <div class="service-card">
                    <h3>📦 Parts Service</h3>
                    <p>Inventory and parts management - Port 8004</p>
                    <span class="status running">Running</span>
                </div>
                <div class="service-card">
                    <h3>🤖 Fix It Fred AI</h3>
                    <p>AI-powered maintenance assistant - Port 8005</p>
                    <span class="status running">Running</span>
                </div>
                <div class="service-card">
                    <h3>🧠 Grok AI Connector</h3>
                    <p>Strategic analysis and optimization - Port 8006</p>
                    <span class="status running">Running</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Comprehensive health check of all services"""
    services = {}
    
    # Check each microservice
    service_urls = {
        "database": DATABASE_SERVICE_URL,
        "work_orders": WORK_ORDERS_SERVICE_URL,
        "assets": ASSETS_SERVICE_URL,
        "parts": PARTS_SERVICE_URL,
        "fix_it_fred": FIX_IT_FRED_URL,
        "grok_connector": GROK_CONNECTOR_URL,
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, url in service_urls.items():
            try:
                response = await client.get(f"{url}/health")
                services[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": url,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
                }
            except Exception as e:
                services[service_name] = {
                    "status": "down",
                    "url": url,
                    "error": str(e)
                }
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "main_app": {
            "port": 8000,
            "version": "4.0.0"
        }
    }

# Work Orders API Proxy
@app.get("/api/work-orders")
async def get_work_orders():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{WORK_ORDERS_SERVICE_URL}/api/work-orders")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Work Orders service unavailable: {str(e)}")

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrderCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{WORK_ORDERS_SERVICE_URL}/api/work-orders", json=work_order.dict())
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Work Orders service unavailable: {str(e)}")

# Assets API Proxy
@app.get("/api/assets")
async def get_assets():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{ASSETS_SERVICE_URL}/api/assets")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Assets service unavailable: {str(e)}")

@app.post("/api/assets")
async def create_asset(asset: AssetCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{ASSETS_SERVICE_URL}/api/assets", json=asset.dict())
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Assets service unavailable: {str(e)}")

# Parts API Proxy
@app.get("/api/parts")
async def get_parts():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PARTS_SERVICE_URL}/api/parts")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Parts service unavailable: {str(e)}")

@app.post("/api/parts")
async def create_part(part: PartCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{PARTS_SERVICE_URL}/api/parts", json=part.dict())
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Parts service unavailable: {str(e)}")

# AI Services Proxy
@app.post("/api/ai/analyze")
async def ai_analyze(request: dict):
    async with httpx.AsyncClient() as client:
        try:
            # Try Fix It Fred first
            response = await client.post(f"{FIX_IT_FRED_URL}/api/analyze", json=request)
            return response.json()
        except Exception as e:
            # Fallback to Grok if Fred is down
            try:
                response = await client.post(f"{GROK_CONNECTOR_URL}/api/analyze", json=request)
                return response.json()
            except Exception as e2:
                raise HTTPException(status_code=503, detail=f"AI services unavailable: {str(e2)}")

# Frontend routes with proper HTML responses
@app.get("/work-orders")
async def work_orders_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Work Orders - ChatterFix CMMS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #2c3e50; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }
            .work-order { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>🔧 Work Orders</h1>
            <p>Maintenance request management system</p>
            <div id="work-orders-list">
                <div class="work-order">
                    <h3>Sample Work Order #1</h3>
                    <p>Status: Open | Priority: High</p>
                    <p>Description: Check HVAC system in Building A</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/assets")
async def assets_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Assets - ChatterFix CMMS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #2c3e50; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }
            .asset { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>🏭 Assets</h1>
            <p>Equipment and facility tracking</p>
            <div id="assets-list">
                <div class="asset">
                    <h3>HVAC Unit #1</h3>
                    <p>Location: Building A | Status: Operational</p>
                    <p>Health Score: 85%</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/parts")
async def parts_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Parts - ChatterFix CMMS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #2c3e50; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }
            .part { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>📦 Parts Inventory</h1>
            <p>Parts and inventory management</p>
            <div id="parts-list">
                <div class="part">
                    <h3>HVAC Filter - HEPA</h3>
                    <p>Part #: HVF-001 | Quantity: 25 | Min Stock: 5</p>
                    <p>Location: Warehouse A-3</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    
    print(f"🚀 Starting ChatterFix CMMS Main Application on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
