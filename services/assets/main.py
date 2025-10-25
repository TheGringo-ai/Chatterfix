#!/usr/bin/env python3
"""
ChatterFix Assets Service - Asset Management Microservice
Enterprise asset tracking and management
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Assets Service",
    description="Enterprise asset management microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Asset(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    location: str
    status: str = "Active"
    category: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None

class AssetCreate(BaseModel):
    name: str
    description: str
    location: str
    category: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

# Sample data for development
sample_assets = [
    {
        "id": 101,
        "name": "Main HVAC Unit",
        "description": "Primary heating and cooling system",
        "location": "Building A - Rooftop",
        "status": "Active",
        "category": "HVAC",
        "manufacturer": "Carrier",
        "model": "50TCQ",
        "serial_number": "HV001",
        "purchase_date": "2023-01-15T00:00:00Z",
        "warranty_expiry": "2028-01-15T00:00:00Z",
        "last_maintenance": "2025-09-15T00:00:00Z"
    },
    {
        "id": 102,
        "name": "Fire Safety Panel",
        "description": "Central fire alarm control panel",
        "location": "Building A - Lobby",
        "status": "Active",
        "category": "Safety",
        "manufacturer": "Honeywell",
        "model": "FS90",
        "serial_number": "FS001",
        "purchase_date": "2022-06-01T00:00:00Z",
        "warranty_expiry": "2027-06-01T00:00:00Z",
        "last_maintenance": "2025-10-01T00:00:00Z"
    },
    {
        "id": 103,
        "name": "Conveyor Belt System",
        "description": "Main production line conveyor",
        "location": "Factory Floor - Line 1",
        "status": "Active",
        "category": "Production",
        "manufacturer": "Dorner",
        "model": "2200",
        "serial_number": "CB001",
        "purchase_date": "2024-03-10T00:00:00Z",
        "warranty_expiry": "2026-03-10T00:00:00Z",
        "last_maintenance": "2025-10-10T00:00:00Z"
    },
    {
        "id": 104,
        "name": "Backup Generator",
        "description": "Emergency power backup generator",
        "location": "Building A - Basement",
        "status": "Standby",
        "category": "Power",
        "manufacturer": "Generac",
        "model": "RG027",
        "serial_number": "GN001",
        "purchase_date": "2023-08-20T00:00:00Z",
        "warranty_expiry": "2026-08-20T00:00:00Z",
        "last_maintenance": "2025-08-20T00:00:00Z"
    }
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "assets",
        "status": "running", 
        "version": "7.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "assets",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/assets", response_model=List[Dict[str, Any]])
async def get_assets(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """Get all assets with optional filtering"""
    filtered_assets = sample_assets.copy()
    
    if status:
        filtered_assets = [asset for asset in filtered_assets if asset["status"].lower() == status.lower()]
    
    if category:
        filtered_assets = [asset for asset in filtered_assets if asset["category"].lower() == category.lower()]
    
    if location:
        filtered_assets = [asset for asset in filtered_assets if location.lower() in asset["location"].lower()]
    
    return filtered_assets

@app.get("/assets/{asset_id}")
async def get_asset(asset_id: int):
    """Get a specific asset by ID"""
    asset = next((asset for asset in sample_assets if asset["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@app.post("/assets", response_model=Dict[str, Any])
async def create_asset(asset: AssetCreate):
    """Create a new asset"""
    new_id = max([asset["id"] for asset in sample_assets]) + 1 if sample_assets else 1
    
    new_asset = {
        "id": new_id,
        "name": asset.name,
        "description": asset.description,
        "location": asset.location,
        "status": "Active",
        "category": asset.category,
        "manufacturer": asset.manufacturer,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
        "warranty_expiry": asset.warranty_expiry.isoformat() if asset.warranty_expiry else None,
        "last_maintenance": None
    }
    
    sample_assets.append(new_asset)
    return new_asset

@app.put("/assets/{asset_id}")
async def update_asset_status(asset_id: int, status: str):
    """Update asset status"""
    asset = next((asset for asset in sample_assets if asset["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset["status"] = status
    return asset

@app.post("/assets/{asset_id}/maintenance")
async def record_maintenance(asset_id: int):
    """Record maintenance performed on asset"""
    asset = next((asset for asset in sample_assets if asset["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset["last_maintenance"] = datetime.now().isoformat()
    return {"message": "Maintenance recorded", "asset": asset}

@app.get("/assets/stats/summary")
async def get_asset_stats():
    """Get asset statistics"""
    total = len(sample_assets)
    by_status = {}
    by_category = {}
    
    for asset in sample_assets:
        status = asset["status"]
        category = asset["category"]
        
        by_status[status] = by_status.get(status, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
    
    return {
        "total_assets": total,
        "by_status": by_status,
        "by_category": by_category,
        "active_percentage": (by_status.get("Active", 0) / total * 100) if total > 0 else 0
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)