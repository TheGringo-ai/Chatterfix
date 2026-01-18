from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.auth import require_auth_cookie
from app.models.user import User
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
async def update_location(
    location: LocationUpdate,
    current_user: User = Depends(require_auth_cookie),
):
    """Update user's current location (requires authentication)"""
    result = geolocation_service.update_user_location(
        user_id=current_user.id,
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy=location.accuracy,
        work_order_id=location.work_order_id,
    )
    return JSONResponse(content=result)


@router.get("/current")
async def get_current_location(current_user: User = Depends(require_auth_cookie)):
    """Get user's current location (requires authentication)"""
    location = geolocation_service.get_user_location(current_user.id)

    if location:
        return JSONResponse(content=location)
    else:
        return JSONResponse(
            content={"error": "No location data available"}, status_code=404
        )


@router.get("/team")
async def get_team_locations(current_user: User = Depends(require_auth_cookie)):
    """Get locations of team members (requires authentication)"""
    locations = geolocation_service.get_team_locations(current_user.id)
    return JSONResponse(content={"team_locations": locations})


@router.get("/nearby-work-orders")
async def get_nearby_work_orders(
    radius: int = 500,
    current_user: User = Depends(require_auth_cookie),
):
    """Get work orders near user's location (requires authentication)"""
    work_orders = geolocation_service.get_nearby_work_orders(current_user.id, radius)
    return JSONResponse(content={"work_orders": work_orders})


@router.get("/history")
async def get_location_history(
    limit: int = 100,
    current_user: User = Depends(require_auth_cookie),
):
    """Get user's location history (requires authentication)"""
    history = geolocation_service.get_location_history(current_user.id, limit)
    return JSONResponse(content={"history": history})


@router.get("/privacy")
async def get_privacy_settings(current_user: User = Depends(require_auth_cookie)):
    """Get user's location privacy settings (requires authentication)"""
    settings = geolocation_service.get_privacy_settings(current_user.id)
    return JSONResponse(content=settings)


@router.post("/privacy")
async def update_privacy_settings(
    settings: PrivacySettings,
    current_user: User = Depends(require_auth_cookie),
):
    """Update user's location privacy settings (requires authentication)"""
    success = geolocation_service.update_privacy_settings(current_user.id, settings.dict())

    return JSONResponse(
        content={
            "success": success,
            "message": (
                "Privacy settings updated" if success else "Failed to update settings"
            ),
        }
    )


@router.post("/boundary")
async def add_property_boundary(boundary: PropertyBoundary):
    """Add a new property boundary (admin only)"""
    boundary_id = geolocation_service.add_property_boundary(
        name=boundary.name,
        coordinates=boundary.coordinates,
        boundary_type=boundary.boundary_type,
        description=boundary.description,
    )

    return JSONResponse(
        content={
            "success": True,
            "boundary_id": boundary_id,
            "message": "Property boundary added",
        }
    )


@router.get("/check-permission")
async def check_location_permission(current_user: User = Depends(require_auth_cookie)):
    """Check if user has location tracking enabled (requires authentication)"""
    enabled = geolocation_service.check_location_permission(current_user.id)
    return JSONResponse(content={"location_tracking_enabled": enabled})
