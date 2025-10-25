"""
Assets Module - Handles all asset management operations
"""

import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .shared import success_response, error_response, logger

router = APIRouter()

# Pydantic models
class AssetBase(BaseModel):
    asset_code: str = Field(..., max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    criticality: str = Field("Medium", pattern="^(Low|Medium|High|Critical)$")
    installation_date: Optional[datetime] = None
    replacement_cost: Optional[float] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(Active|Inactive|Maintenance|Retired)$")
    criticality: Optional[str] = Field(None, pattern="^(Low|Medium|High|Critical)$")
    installation_date: Optional[datetime] = None
    replacement_cost: Optional[float] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None

# Sample data
assets_data = [
    {
        "id": 101,
        "asset_code": "HVAC-001",
        "name": "Main HVAC Unit - Building A",
        "description": "Primary heating, ventilation, and air conditioning system",
        "asset_type": "HVAC",
        "location": "Building A - Roof",
        "manufacturer": "Carrier",
        "model": "50TCQ12",
        "serial_number": "CAR50TCQ12-2023-001",
        "purchase_date": "2023-01-15T00:00:00Z",
        "warranty_expiry": "2026-01-15T00:00:00Z",
        "status": "Active",
        "criticality": "High",
        "installation_date": "2023-02-01T00:00:00Z",
        "last_maintenance": "2025-09-15T00:00:00Z",
        "next_maintenance": "2025-12-15T00:00:00Z",
        "replacement_cost": 45000.00,
        "created_at": "2023-01-15T10:00:00Z",
        "updated_at": "2025-09-15T14:30:00Z"
    },
    {
        "id": 102,
        "asset_code": "FIRE-001",
        "name": "Fire Safety Panel - Main Building",
        "description": "Central fire detection and alarm system",
        "asset_type": "Safety",
        "location": "Building A - Lobby",
        "manufacturer": "Honeywell",
        "model": "FS90",
        "serial_number": "HON-FS90-2022-156",
        "purchase_date": "2022-06-10T00:00:00Z",
        "warranty_expiry": "2025-06-10T00:00:00Z",
        "status": "Active",
        "criticality": "Critical",
        "installation_date": "2022-07-01T00:00:00Z",
        "last_maintenance": "2025-09-01T00:00:00Z",
        "next_maintenance": "2025-12-01T00:00:00Z",
        "replacement_cost": 8500.00,
        "created_at": "2022-06-10T10:00:00Z",
        "updated_at": "2025-09-01T09:15:00Z"
    },
    {
        "id": 103,
        "asset_code": "CONV-001",
        "name": "Production Conveyor Belt System",
        "description": "Main production line conveyor belt system",
        "asset_type": "Production",
        "location": "Factory Floor - Line 1",
        "manufacturer": "Dorner",
        "model": "2200 Series",
        "serial_number": "DOR-2200-2021-089",
        "purchase_date": "2021-03-20T00:00:00Z",
        "warranty_expiry": "2024-03-20T00:00:00Z",
        "status": "Active",
        "criticality": "High",
        "installation_date": "2021-04-15T00:00:00Z",
        "last_maintenance": "2025-10-01T00:00:00Z",
        "next_maintenance": "2025-11-01T00:00:00Z",
        "replacement_cost": 25000.00,
        "created_at": "2021-03-20T10:00:00Z",
        "updated_at": "2025-10-01T16:45:00Z"
    },
    {
        "id": 104,
        "asset_code": "ELEV-001",
        "name": "Passenger Elevator - Tower A",
        "description": "Main passenger elevator serving floors 1-15",
        "asset_type": "Elevator",
        "location": "Building A - Central Core",
        "manufacturer": "Otis",
        "model": "Gen2",
        "serial_number": "OTIS-GEN2-2020-445",
        "purchase_date": "2020-08-15T00:00:00Z",
        "warranty_expiry": "2025-08-15T00:00:00Z",
        "status": "Active",
        "criticality": "Critical",
        "installation_date": "2020-09-30T00:00:00Z",
        "last_maintenance": "2025-10-20T00:00:00Z",
        "next_maintenance": "2026-04-20T00:00:00Z",
        "replacement_cost": 85000.00,
        "created_at": "2020-08-15T10:00:00Z",
        "updated_at": "2025-10-20T16:30:00Z"
    },
    {
        "id": 105,
        "asset_code": "LIGHT-001",
        "name": "LED Parking Lot Fixtures",
        "description": "Employee parking area LED light fixtures",
        "asset_type": "Lighting",
        "location": "Exterior - Employee Parking",
        "manufacturer": "Cree",
        "model": "XSP-Series",
        "serial_number": "CREE-XSP-2022-001-025",
        "purchase_date": "2022-03-10T00:00:00Z",
        "warranty_expiry": "2027-03-10T00:00:00Z",
        "status": "Maintenance",
        "criticality": "Low",
        "installation_date": "2022-04-01T00:00:00Z",
        "last_maintenance": "2025-08-15T00:00:00Z",
        "next_maintenance": "2026-02-15T00:00:00Z",
        "replacement_cost": 12500.00,
        "created_at": "2022-03-10T10:00:00Z",
        "updated_at": "2025-10-23T14:00:00Z"
    },
    {
        "id": 106,
        "asset_code": "GEN-001",
        "name": "Emergency Backup Generator",
        "description": "Diesel backup generator for emergency power",
        "asset_type": "Power",
        "location": "Building A - Generator Room",
        "manufacturer": "Caterpillar",
        "model": "C32 ACERT",
        "serial_number": "CAT-C32-2019-887",
        "purchase_date": "2019-11-05T00:00:00Z",
        "warranty_expiry": "2024-11-05T00:00:00Z",
        "status": "On Hold",
        "criticality": "Critical",
        "installation_date": "2019-12-15T00:00:00Z",
        "last_maintenance": "2025-09-18T00:00:00Z",
        "next_maintenance": "2025-11-18T00:00:00Z",
        "replacement_cost": 120000.00,
        "created_at": "2019-11-05T10:00:00Z",
        "updated_at": "2025-10-19T09:15:00Z"
    },
    {
        "id": 107,
        "asset_code": "ROOF-001",
        "name": "Building B Roof Structure",
        "description": "Main building roof structure and weatherproofing",
        "asset_type": "Structure",
        "location": "Building B - Roof",
        "manufacturer": "Duro-Last",
        "model": "Commercial Membrane",
        "serial_number": "DL-CM-2018-B02",
        "purchase_date": "2018-05-20T00:00:00Z",
        "warranty_expiry": "2028-05-20T00:00:00Z",
        "status": "Maintenance",
        "criticality": "High",
        "installation_date": "2018-06-30T00:00:00Z",
        "last_maintenance": "2025-06-01T00:00:00Z",
        "next_maintenance": "2026-06-01T00:00:00Z",
        "replacement_cost": 65000.00,
        "created_at": "2018-05-20T10:00:00Z",
        "updated_at": "2025-10-23T08:30:00Z"
    },
    {
        "id": 108,
        "asset_code": "PLUMB-001",
        "name": "Restroom Plumbing System",
        "description": "Main building restroom plumbing and fixtures",
        "asset_type": "Plumbing",
        "location": "Building A - All Floors",
        "manufacturer": "Kohler",
        "model": "Commercial Series",
        "serial_number": "KOH-CS-2020-001-050",
        "purchase_date": "2020-02-10T00:00:00Z",
        "warranty_expiry": "2025-02-10T00:00:00Z",
        "status": "Active",
        "criticality": "Medium",
        "installation_date": "2020-03-15T00:00:00Z",
        "last_maintenance": "2025-10-15T00:00:00Z",
        "next_maintenance": "2026-01-15T00:00:00Z",
        "replacement_cost": 35000.00,
        "created_at": "2020-02-10T10:00:00Z",
        "updated_at": "2025-10-15T15:30:00Z"
    },
    {
        "id": 109,
        "asset_code": "HVAC-002",
        "name": "IT Server Room HVAC",
        "description": "Dedicated HVAC system for server room cooling",
        "asset_type": "HVAC",
        "location": "Building A - Server Room",
        "manufacturer": "Liebert",
        "model": "CRV",
        "serial_number": "LIE-CRV-2021-445",
        "purchase_date": "2021-07-20T00:00:00Z",
        "warranty_expiry": "2026-07-20T00:00:00Z",
        "status": "Active",
        "criticality": "Critical",
        "installation_date": "2021-08-15T00:00:00Z",
        "last_maintenance": "2025-09-20T00:00:00Z",
        "next_maintenance": "2025-12-20T00:00:00Z",
        "replacement_cost": 28000.00,
        "created_at": "2021-07-20T10:00:00Z",
        "updated_at": "2025-10-24T13:00:00Z"
    }
]

maintenance_schedules_data = {
    101: [
        {
            "id": 1,
            "asset_id": 101,
            "title": "Filter Replacement",
            "description": "Replace HEPA filters in HVAC system",
            "frequency_type": "Monthly",
            "frequency_value": 1,
            "last_completed": "2025-10-01",
            "next_due": "2025-11-01",
            "estimated_hours": 2.0,
            "assigned_to": "John Smith",
            "priority": "Medium",
            "is_active": True
        }
    ],
    102: [
        {
            "id": 2,
            "asset_id": 102,
            "title": "Battery Test",
            "description": "Test backup battery and replace if needed",
            "frequency_type": "Monthly", 
            "frequency_value": 1,
            "last_completed": "2025-10-01",
            "next_due": "2025-11-01",
            "estimated_hours": 1.0,
            "assigned_to": "Mike Wilson",
            "priority": "High",
            "is_active": True
        }
    ]
}

@router.get("/")
async def get_assets(
    status: Optional[str] = Query(None, description="Filter by status"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all assets with optional filtering"""
    filtered_assets = assets_data.copy()
    
    if status:
        filtered_assets = [asset for asset in filtered_assets if asset["status"].lower() == status.lower()]
    
    if asset_type:
        filtered_assets = [asset for asset in filtered_assets if asset.get("asset_type", "").lower() == asset_type.lower()]
    
    if location:
        filtered_assets = [asset for asset in filtered_assets if location.lower() in asset.get("location", "").lower()]
    
    if criticality:
        filtered_assets = [asset for asset in filtered_assets if asset["criticality"].lower() == criticality.lower()]
    
    # Apply pagination
    total = len(filtered_assets)
    paginated = filtered_assets[offset:offset + limit]
    
    return {
        "assets": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{asset_id}")
async def get_asset(asset_id: int):
    """Get detailed asset with maintenance schedules"""
    asset = next((a for a in assets_data if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Enhance with related data
    result = asset.copy()
    result["attachments"] = []  # TODO: Load from attachments
    result["recent_work_orders"] = []  # TODO: Cross-reference with work orders
    result["maintenance_schedules"] = maintenance_schedules_data.get(asset_id, [])
    
    return result

@router.post("/")
async def create_asset(asset: AssetCreate):
    """Create a new asset"""
    new_id = max([a["id"] for a in assets_data]) + 1 if assets_data else 1
    
    new_asset = {
        "id": new_id,
        "asset_code": asset.asset_code,
        "name": asset.name,
        "description": asset.description,
        "asset_type": asset.asset_type,
        "location": asset.location,
        "manufacturer": asset.manufacturer,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
        "warranty_expiry": asset.warranty_expiry.isoformat() if asset.warranty_expiry else None,
        "status": "Active",
        "criticality": asset.criticality,
        "installation_date": asset.installation_date.isoformat() if asset.installation_date else None,
        "last_maintenance": None,
        "next_maintenance": None,
        "replacement_cost": asset.replacement_cost,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    assets_data.append(new_asset)
    return success_response("Asset created successfully", {"asset": new_asset})

@router.put("/{asset_id}")
async def update_asset(asset_id: int, updates: AssetUpdate):
    """Update asset fields"""
    asset = next((a for a in assets_data if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if isinstance(value, datetime):
                asset[field] = value.isoformat()
            else:
                asset[field] = value
    
    asset["updated_at"] = datetime.now().isoformat()
    
    return success_response("Asset updated successfully", {"asset": asset})

@router.get("/stats/summary")
async def get_asset_stats():
    """Get asset statistics"""
    total = len(assets_data)
    by_status = {}
    by_type = {}
    by_criticality = {}
    by_location = {}
    
    warranty_expiring_count = 0  # Expiring in next 90 days
    maintenance_due_count = 0    # Maintenance due in next 30 days
    
    for asset in assets_data:
        status = asset["status"]
        asset_type = asset.get("asset_type", "Unknown")
        criticality = asset["criticality"]
        location = asset.get("location", "Unknown")
        
        by_status[status] = by_status.get(status, 0) + 1
        by_type[asset_type] = by_type.get(asset_type, 0) + 1
        by_criticality[criticality] = by_criticality.get(criticality, 0) + 1
        by_location[location] = by_location.get(location, 0) + 1
        
        # Check warranty expiry
        if asset.get("warranty_expiry"):
            warranty_date = datetime.fromisoformat(asset["warranty_expiry"].replace('Z', '+00:00'))
            if warranty_date < datetime.now(warranty_date.tzinfo) + timedelta(days=90):
                warranty_expiring_count += 1
        
        # Check maintenance due
        if asset.get("next_maintenance"):
            maintenance_date = datetime.fromisoformat(asset["next_maintenance"].replace('Z', '+00:00'))
            if maintenance_date < datetime.now(maintenance_date.tzinfo) + timedelta(days=30):
                maintenance_due_count += 1
    
    total_value = sum(asset.get("replacement_cost", 0) for asset in assets_data)
    
    return {
        "total_assets": total,
        "by_status": by_status,
        "by_type": by_type,
        "by_criticality": by_criticality,
        "by_location": by_location,
        "warranty_expiring_count": warranty_expiring_count,
        "maintenance_due_count": maintenance_due_count,
        "total_replacement_value": total_value
    }

@router.get("/maintenance/upcoming")
async def get_upcoming_maintenance():
    """Get assets with upcoming maintenance"""
    upcoming = []
    
    for asset in assets_data:
        if asset.get("next_maintenance"):
            maintenance_date = datetime.fromisoformat(asset["next_maintenance"].replace('Z', '+00:00'))
            days_until = (maintenance_date - datetime.now(maintenance_date.tzinfo)).days
            
            if days_until <= 30:  # Due in next 30 days
                upcoming.append({
                    "asset_id": asset["id"],
                    "asset_code": asset["asset_code"],
                    "asset_name": asset["name"],
                    "next_maintenance": asset["next_maintenance"],
                    "days_until": days_until,
                    "criticality": asset["criticality"],
                    "location": asset.get("location", "Unknown")
                })
    
    # Sort by days until maintenance
    upcoming.sort(key=lambda x: x["days_until"])
    
    return {"upcoming_maintenance": upcoming}

@router.get("/export.csv")
async def export_assets_csv(
    status: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None)
):
    """Export assets as CSV"""
    filtered_assets = assets_data.copy()
    
    if status:
        filtered_assets = [asset for asset in filtered_assets if asset["status"].lower() == status.lower()]
    if asset_type:
        filtered_assets = [asset for asset in filtered_assets if asset.get("asset_type", "").lower() == asset_type.lower()]
    if location:
        filtered_assets = [asset for asset in filtered_assets if location.lower() in asset.get("location", "").lower()]
    if criticality:
        filtered_assets = [asset for asset in filtered_assets if asset["criticality"].lower() == criticality.lower()]
    
    # Create DataFrame
    df = pd.DataFrame(filtered_assets)
    
    # Generate CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assets_export.csv"}
    )