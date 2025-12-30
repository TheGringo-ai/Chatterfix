#!/usr/bin/env python3
"""
Assets Management Module
Easily editable asset tracking system
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/assets", tags=["Assets"])

# Asset Models
class AssetStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    BROKEN = "broken"

class Asset(BaseModel):
    id: str
    name: str
    description: str
    model: str
    serial_number: str
    manufacturer: str
    location: str
    status: AssetStatus
    purchase_date: datetime
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    cost: float

class AssetCreate(BaseModel):
    name: str
    description: str
    model: str
    serial_number: str
    manufacturer: str
    location: str
    purchase_date: datetime
    cost: float

# In-memory assets database
assets_db = {}

@router.get("/", response_model=List[Asset])
async def get_all_assets():
    """Get all assets"""
    return list(assets_db.values())

@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str):
    """Get specific asset by ID"""
    if asset_id not in assets_db:
        raise HTTPException(status_code=404, detail="Asset not found")
    return assets_db[asset_id]

@router.post("/", response_model=Asset)
async def create_asset(asset: AssetCreate):
    """Create new asset"""
    asset_id = f"ASSET_{len(assets_db) + 1:05d}"
    new_asset = Asset(
        id=asset_id,
        **asset.dict(),
        status=AssetStatus.ACTIVE
    )
    assets_db[asset_id] = new_asset
    return new_asset

@router.put("/{asset_id}/status")
async def update_asset_status(asset_id: str, status: AssetStatus):
    """Update asset status"""
    if asset_id not in assets_db:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    assets_db[asset_id].status = status
    return assets_db[asset_id]

@router.put("/{asset_id}/maintenance")
async def record_maintenance(asset_id: str, next_maintenance: Optional[datetime] = None):
    """Record maintenance performed"""
    if asset_id not in assets_db:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset = assets_db[asset_id]
    asset.last_maintenance = datetime.now()
    if next_maintenance:
        asset.next_maintenance = next_maintenance
    
    return asset

@router.get("/status/{status}")
async def get_assets_by_status(status: AssetStatus):
    """Get assets by status"""
    return [asset for asset in assets_db.values() if asset.status == status]

@router.get("/location/{location}")
async def get_assets_by_location(location: str):
    """Get assets by location"""
    return [asset for asset in assets_db.values() if asset.location.lower() == location.lower()]