"""
PM Automation API Router

Cloud Run service endpoints for Preventive Maintenance automation:
- POST /api/pm/meter-reading - Record meter readings and check triggers
- POST /api/pm/generate-schedule - Generate PM work orders (idempotent)
- GET /api/pm/overview - Get PM dashboard overview

All endpoints support multi-tenant isolation via organization_id.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.auth import (
    get_current_active_user,
    get_optional_current_user,
    get_current_user_from_cookie,
)
from app.models.user import User
from app.services.pm_automation_engine import (
    PMAutomationEngine,
    get_pm_automation_engine,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pm", tags=["pm-automation"])


# ==========================================
# PYDANTIC MODELS - Request/Response
# ==========================================


class MeterReadingRequest(BaseModel):
    """Request model for recording a meter reading."""

    organization_id: Optional[str] = Field(
        None,
        description="Organization ID. If not provided, uses authenticated user's org.",
    )
    meter_id: str = Field(..., description="Meter document ID", min_length=1)
    new_value: float = Field(..., description="New meter reading value")
    reading_time: Optional[datetime] = Field(
        None,
        description="Time of reading (UTC). Defaults to now if not provided.",
    )
    reading_source: str = Field(
        "manual",
        description="Source of reading: 'manual', 'iot', 'api'",
    )
    create_work_orders: bool = Field(
        True,
        description="If true, create work orders for triggered maintenance",
    )

    @validator("reading_source")
    def validate_reading_source(cls, v):
        allowed = {"manual", "iot", "api"}
        if v not in allowed:
            raise ValueError(f"reading_source must be one of: {allowed}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "meter_id": "meter_motor005_vibration",
                "new_value": 5.2,
                "reading_source": "iot",
                "create_work_orders": True,
            }
        }


class MeterReadingResponse(BaseModel):
    """Response model for meter reading result."""

    success: bool
    meter_id: str
    previous_value: Optional[float] = None
    new_value: float
    threshold_status: Optional[str] = None
    triggered_maintenance: int = 0
    triggered_orders: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "meter_id": "meter_motor005_vibration",
                "previous_value": 4.1,
                "new_value": 5.2,
                "threshold_status": "warning",
                "triggered_maintenance": 1,
                "triggered_orders": [
                    {
                        "pm_order_id": "CBM_motor005_1702900000",
                        "title": "CONDITION ALERT: Motor Maintenance",
                        "priority": "HIGH",
                    }
                ],
            }
        }


class GenerateScheduleRequest(BaseModel):
    """Request model for PM schedule generation."""

    organization_id: Optional[str] = Field(
        None,
        description="Organization ID. If not provided, uses authenticated user's org.",
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Start of period (UTC). Defaults to now.",
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End of period (UTC). Defaults to 30 days from start.",
    )
    create_work_orders: bool = Field(
        True,
        description="If true, creates actual work orders in Firestore",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-12-18T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "create_work_orders": True,
            }
        }


class GenerateScheduleResponse(BaseModel):
    """Response model for PM schedule generation."""

    success: bool
    generated_count: int
    work_orders_created: int
    rules_updated: int
    period: Dict[str, str]
    work_order_ids: List[str] = Field(default_factory=list)
    orders: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "generated_count": 5,
                "work_orders_created": 5,
                "rules_updated": 3,
                "period": {
                    "start": "2024-12-18T00:00:00+00:00",
                    "end": "2024-12-31T23:59:59+00:00",
                },
                "work_order_ids": ["wo_abc123", "wo_def456"],
            }
        }


class PMOverviewResponse(BaseModel):
    """Response model for PM overview dashboard."""

    success: bool
    overview: Dict[str, Any]
    by_maintenance_type: Dict[str, int]
    due_rules: List[Dict[str, Any]]
    critical_meters: List[Dict[str, Any]]
    warning_meters: List[Dict[str, Any]]
    recent_pm_orders: List[Dict[str, Any]]
    templates_summary: List[Dict[str, Any]]
    error: Optional[str] = None


class APIErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str
    detail: Optional[str] = None


# ==========================================
# HELPER FUNCTIONS
# ==========================================


def _get_organization_id(
    request_org_id: Optional[str],
    current_user: Optional[User],
) -> str:
    """
    Resolve organization_id from request or authenticated user.

    Priority:
    1. Use authenticated user's organization_id if available
    2. Fall back to explicitly provided organization_id
    3. Raise 400 if neither available

    TODO: In production, organization_id should ALWAYS come from
    Auth token claims. Remove explicit organization_id parameter
    once all clients are updated to use proper authentication.
    """
    # Prefer user's org from auth token
    if current_user and current_user.organization_id:
        # If request also provides org_id, validate they match
        if request_org_id and request_org_id != current_user.organization_id:
            logger.warning(
                f"User {current_user.uid} tried to access org {request_org_id} "
                f"but belongs to {current_user.organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access resources from another organization",
            )
        return current_user.organization_id

    # Fall back to explicit org_id (TODO: remove in production)
    if request_org_id:
        logger.warning(
            "Using explicit organization_id without auth. "
            "TODO: Require auth token with org claim in production."
        )
        return request_org_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="organization_id required. Provide via auth token or request body.",
    )


def _get_pm_engine() -> PMAutomationEngine:
    """Get PM automation engine instance."""
    return get_pm_automation_engine()


# ==========================================
# API ENDPOINTS
# ==========================================


@router.post(
    "/meter-reading",
    response_model=MeterReadingResponse,
    responses={
        200: {"model": MeterReadingResponse, "description": "Meter reading recorded"},
        400: {"model": APIErrorResponse, "description": "Invalid request"},
        401: {"model": APIErrorResponse, "description": "Not authenticated"},
        403: {"model": APIErrorResponse, "description": "Access denied"},
        500: {"model": APIErrorResponse, "description": "Server error"},
    },
    summary="Record a meter reading",
    description="""
    Record a new meter reading and check for triggered maintenance.

    - Stores the reading in asset_meters collection
    - Checks if reading exceeds warning/critical thresholds
    - Optionally creates PM work orders for triggered maintenance
    - Returns threshold status and any triggered orders
    """,
)
async def record_meter_reading(
    request: MeterReadingRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    pm_engine: PMAutomationEngine = Depends(_get_pm_engine),
) -> JSONResponse:
    """
    POST /api/pm/meter-reading

    Record a meter reading, check thresholds, and optionally create work orders.
    """
    try:
        org_id = _get_organization_id(request.organization_id, current_user)

        result = await pm_engine.update_meter_reading(
            organization_id=org_id,
            meter_id=request.meter_id,
            new_value=request.new_value,
            reading_source=request.reading_source,
            create_work_orders=request.create_work_orders,
        )

        # Check for error in result
        if "error" in result:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "meter_id": request.meter_id,
                    "new_value": request.new_value,
                    "error": result["error"],
                },
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "meter_id": request.meter_id,
                "previous_value": result.get("previous_value"),
                "new_value": result.get("current_value", request.new_value),
                "threshold_status": result.get("threshold_status"),
                "triggered_maintenance": result.get("triggered_maintenance", 0),
                "triggered_orders": result.get("triggered_orders", []),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording meter reading: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "meter_id": request.meter_id,
                "new_value": request.new_value,
                "error": f"Internal error: {str(e)}",
            },
        )


@router.post(
    "/generate-schedule",
    response_model=GenerateScheduleResponse,
    responses={
        200: {"model": GenerateScheduleResponse, "description": "Schedule generated"},
        400: {"model": APIErrorResponse, "description": "Invalid request"},
        401: {"model": APIErrorResponse, "description": "Not authenticated"},
        403: {"model": APIErrorResponse, "description": "Access denied"},
        500: {"model": APIErrorResponse, "description": "Server error"},
    },
    summary="Generate PM schedule",
    description="""
    Generate preventive maintenance work orders for the specified period.

    Key features:
    - **Idempotent**: Running multiple times for same date range won't create duplicates
    - Uses idempotency key format: {org_id}_{rule_id}_{YYYYMMDD}
    - Processes time-based, condition-based, and usage-based rules
    - Applies seasonal adjustments to due dates
    - Persists generated orders to pm_generated_orders collection
    """,
)
async def generate_pm_schedule(
    request: GenerateScheduleRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    pm_engine: PMAutomationEngine = Depends(_get_pm_engine),
) -> JSONResponse:
    """
    POST /api/pm/generate-schedule

    Generate PM work orders deterministically and persist to Firestore.
    Idempotent for same date range - won't create duplicate work orders.
    """
    try:
        org_id = _get_organization_id(request.organization_id, current_user)

        result = await pm_engine.generate_pm_schedule(
            organization_id=org_id,
            start_date=request.start_date,
            end_date=request.end_date,
            create_work_orders=request.create_work_orders,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "generated_count": result.get("generated_count", 0),
                "work_orders_created": result.get("work_orders_created", 0),
                "rules_updated": result.get("rules_updated", 0),
                "period": result.get("period", {}),
                "work_order_ids": result.get("work_order_ids", []),
                "orders": result.get("orders", [])[:20],  # Limit response size
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PM schedule: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "generated_count": 0,
                "work_orders_created": 0,
                "rules_updated": 0,
                "period": {},
                "error": f"Internal error: {str(e)}",
            },
        )


@router.get(
    "/overview",
    response_model=PMOverviewResponse,
    responses={
        200: {"model": PMOverviewResponse, "description": "PM overview data"},
        400: {"model": APIErrorResponse, "description": "Invalid request"},
        401: {"model": APIErrorResponse, "description": "Not authenticated"},
        403: {"model": APIErrorResponse, "description": "Access denied"},
        500: {"model": APIErrorResponse, "description": "Server error"},
    },
    summary="Get PM overview",
    description="""
    Get comprehensive PM overview for dashboard display.

    Returns:
    - Summary statistics (active rules, due soon, overdue, meter alerts)
    - Breakdown by maintenance type
    - Due rules list
    - Critical and warning meter alerts
    - Recent PM orders
    - Template summary

    All data is fetched from Firestore (production data).
    """,
)
async def get_pm_overview(
    days_ahead: int = Query(30, ge=1, le=365, description="Days to look ahead"),
    organization_id: Optional[str] = Query(
        None,
        description="Organization ID. If not provided, uses authenticated user's org.",
    ),
    current_user: Optional[User] = Depends(get_optional_current_user),
    pm_engine: PMAutomationEngine = Depends(_get_pm_engine),
) -> JSONResponse:
    """
    GET /api/pm/overview?days_ahead=30

    Get PM dashboard overview with Firestore-backed data.
    """
    try:
        org_id = _get_organization_id(organization_id, current_user)

        result = await pm_engine.get_pm_schedule_overview(
            organization_id=org_id,
            days_ahead=days_ahead,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "overview": result.get("overview", {}),
                "by_maintenance_type": result.get("by_maintenance_type", {}),
                "due_rules": result.get("due_rules", []),
                "critical_meters": result.get("critical_meters", []),
                "warning_meters": result.get("warning_meters", []),
                "recent_pm_orders": result.get("recent_pm_orders", []),
                "templates_summary": result.get("templates_summary", []),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PM overview: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "overview": {},
                "by_maintenance_type": {},
                "due_rules": [],
                "critical_meters": [],
                "warning_meters": [],
                "recent_pm_orders": [],
                "templates_summary": [],
                "error": f"Internal error: {str(e)}",
            },
        )


# ==========================================
# ADDITIONAL UTILITY ENDPOINTS
# ==========================================


@router.get(
    "/templates",
    summary="List PM templates",
    description="Get all PM templates for the organization.",
)
async def list_templates(
    organization_id: Optional[str] = Query(None),
    maintenance_type: Optional[str] = Query(
        None,
        description="Filter by type: preventive, condition_based, usage_based, etc.",
    ),
    current_user: Optional[User] = Depends(get_optional_current_user),
    pm_engine: PMAutomationEngine = Depends(_get_pm_engine),
) -> JSONResponse:
    """GET /api/pm/templates - List all PM templates."""
    try:
        org_id = _get_organization_id(organization_id, current_user)

        templates = await pm_engine.get_maintenance_templates(
            organization_id=org_id,
            maintenance_type=maintenance_type,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "count": len(templates),
                "templates": templates,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "count": 0,
                "templates": [],
                "error": str(e),
            },
        )


@router.get(
    "/rules",
    summary="List PM schedule rules",
    description="Get all PM schedule rules for the organization.",
)
async def list_rules(
    organization_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None, description="Filter by asset"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    pm_engine: PMAutomationEngine = Depends(_get_pm_engine),
) -> JSONResponse:
    """GET /api/pm/rules - List all PM schedule rules."""
    try:
        org_id = _get_organization_id(organization_id, current_user)

        rules = await pm_engine.get_schedule_rules(
            organization_id=org_id,
            asset_id=asset_id,
            is_active=is_active,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "count": len(rules),
                "rules": rules,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing rules: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "count": 0,
                "rules": [],
                "error": str(e),
            },
        )


@router.get(
    "/meters",
    summary="List asset meters",
    description="Get all asset meters for the organization.",
)
async def list_meters(
    organization_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None, description="Filter by asset"),
    meter_type: Optional[str] = Query(
        None,
        description="Filter by type: vibration, temperature, pressure, etc.",
    ),
    current_user: Optional[User] = Depends(get_optional_current_user),
    pm_engine: PMAutomationEngine = Depends(_get_pm_engine),
) -> JSONResponse:
    """GET /api/pm/meters - List all asset meters."""
    try:
        org_id = _get_organization_id(organization_id, current_user)

        meters = await pm_engine.get_asset_meters(
            organization_id=org_id,
            asset_id=asset_id,
            meter_type=meter_type,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "count": len(meters),
                "meters": meters,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing meters: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "count": 0,
                "meters": [],
                "error": str(e),
            },
        )
