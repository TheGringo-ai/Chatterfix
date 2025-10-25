# Fix It Fred's Assets API Fix
# This file adds the missing /api/assets endpoints to ChatterFix

from fastapi import HTTPException
from datetime import datetime

# Assets data store (in production, this would be a database)
ASSETS_DATA = [
    {
        "id": 1,
        "name": "Main Production Server",
        "description": "Primary server for production workloads",
        "asset_type": "equipment",
        "location": "Data Center A",
        "status": "operational",
        "purchase_date": "2024-01-15",
        "created_at": "2024-01-15T10:00:00"
    },
    {
        "id": 2,
        "name": "Backup Generator", 
        "description": "Emergency power backup system",
        "asset_type": "equipment",
        "location": "Building B", 
        "status": "active",
        "purchase_date": "2023-08-20",
        "created_at": "2023-08-20T14:30:00"
    },
    {
        "id": 3,
        "name": "HVAC Unit #1",
        "description": "Main HVAC system for floor 1", 
        "asset_type": "system",
        "location": "Floor 1",
        "status": "maintenance",
        "purchase_date": "2022-05-10", 
        "created_at": "2022-05-10T09:15:00"
    }
]

# Add these endpoints to your main application

@app.get("/api/assets")
async def get_assets():
    """Get all assets - Fixed by Fix It Fred"""
    try:
        return ASSETS_DATA
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets") 
async def create_asset(asset_data: dict):
    """Create a new asset - Fixed by Fix It Fred"""
    try:
        new_id = max([asset["id"] for asset in ASSETS_DATA], default=0) + 1
        
        new_asset = {
            "id": new_id,
            "name": asset_data.get("name", ""),
            "description": asset_data.get("description", ""),
            "asset_type": asset_data.get("asset_type", "equipment"),
            "location": asset_data.get("location", ""),
            "status": asset_data.get("status", "active"),
            "purchase_date": asset_data.get("purchase_date"),
            "created_at": datetime.now().isoformat()
        }
        
        ASSETS_DATA.append(new_asset)
        
        return {
            "success": True,
            "message": "Asset created successfully by Fix It Fred!",
            "asset": new_asset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
