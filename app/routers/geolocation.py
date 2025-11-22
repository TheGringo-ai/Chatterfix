from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

from app.services.geolocation_service import geolocation_service

router = APIRouter(prefix="/geolocation", tags=["geolocation"])

# Pydantic models
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    work_order_id: Optional[int] = None

class PrivacySettings(BaseModel):
    location_tracking_enabled: bool = True
    share_location_with_team: bool = True
    track_only_on_shift: bool = True

class PropertyBoundary(BaseModel):
    name: str
    description: Optional[str] = None
    boundary_type: str = "polygon"  # polygon or circle
    coordinates: list  # [[lat, lon], ...] for polygon or {"center": [lat, lon], "radius": meters} for circle

@router.post("/update")
async def update_location(location: LocationUpdate, user_id: int = 1):
    """Update user's current location"""
    result = geolocation_service.update_user_location(
        user_id=user_id,
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy=location.accuracy,
        work_order_id=location.work_order_id
    )
    return JSONResponse(content=result)

@router.get("/current")
async def get_current_location(user_id: int = 1):
    """Get user's current location"""
    location = geolocation_service.get_user_location(user_id)
    
    if location:
        return JSONResponse(content=location)
    else:
        return JSONResponse(content={"error": "No location data available"}, status_code=404)

@router.get("/team")
async def get_team_locations(user_id: int = 1):
    """Get locations of team members"""
    locations = geolocation_service.get_team_locations(user_id)
    return JSONResponse(content={"team_locations": locations})

@router.get("/nearby-work-orders")
async def get_nearby_work_orders(user_id: int = 1, radius: int = 500):
    """Get work orders near user's location"""
    work_orders = geolocation_service.get_nearby_work_orders(user_id, radius)
    return JSONResponse(content={"work_orders": work_orders})

@router.get("/history")
async def get_location_history(user_id: int = 1, limit: int = 100):
    """Get user's location history"""
    history = geolocation_service.get_location_history(user_id, limit)
    return JSONResponse(content={"history": history})

@router.get("/privacy")
async def get_privacy_settings(user_id: int = 1):
    """Get user's location privacy settings"""
    settings = geolocation_service.get_privacy_settings(user_id)
    return JSONResponse(content=settings)

@router.post("/privacy")
async def update_privacy_settings(settings: PrivacySettings, user_id: int = 1):
    """Update user's location privacy settings"""
    success = geolocation_service.update_privacy_settings(user_id, settings.dict())
    
    return JSONResponse(content={
        "success": success,
        "message": "Privacy settings updated" if success else "Failed to update settings"
    })

@router.post("/boundary")
async def add_property_boundary(boundary: PropertyBoundary):
    """Add a new property boundary (admin only)"""
    boundary_id = geolocation_service.add_property_boundary(
        name=boundary.name,
        coordinates=boundary.coordinates,
        boundary_type=boundary.boundary_type,
        description=boundary.description
    )
    
    return JSONResponse(content={
        "success": True,
        "boundary_id": boundary_id,
        "message": "Property boundary added"
    })

@router.get("/check-permission")
async def check_location_permission(user_id: int = 1):
    """Check if user has location tracking enabled"""
    enabled = geolocation_service.check_location_permission(user_id)
    return JSONResponse(content={"location_tracking_enabled": enabled})
