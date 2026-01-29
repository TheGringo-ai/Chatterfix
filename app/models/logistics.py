"""
Logistics Safety Models
Pydantic models for pallet inspection and warehouse safety analysis
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SafetyStatus(str, Enum):
    """Safety assessment status levels"""
    SAFE = "SAFE"
    WARNING = "WARNING"
    DANGER = "DANGER"


class HazardType(str, Enum):
    """Types of warehouse/logistics hazards"""
    LEANING_STACK = "leaning_stack"
    TORN_WRAP = "torn_wrap"
    DAMAGED_PALLET = "damaged_pallet"
    LEAKING_FLUID = "leaking_fluid"
    OBSTRUCTED_AISLE = "obstructed_aisle"
    OVERLOADED = "overloaded"
    UNSECURED_LOAD = "unsecured_load"
    IMPROPER_STACKING = "improper_stacking"
    NONE = "none"


class InspectionResult(BaseModel):
    """Result of a pallet/load safety inspection"""
    status: SafetyStatus = Field(..., description="Overall safety status: SAFE, WARNING, or DANGER")
    hazards_detected: List[HazardType] = Field(default_factory=list, description="List of detected hazards")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in the assessment")
    description: str = Field(..., description="Short explanation of the safety assessment")
    recommended_action: str = Field(..., description="Immediate action for the forklift driver")

    # Metadata for logging and tracking
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    location_aisle: Optional[str] = Field(None, description="Aisle or location identifier")
    inspector_id: Optional[str] = Field(None, description="ID of the technician/driver who took the photo")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "WARNING",
                "hazards_detected": ["torn_wrap", "leaning_stack"],
                "confidence_score": 0.87,
                "description": "Shrink wrap torn on south side, stack leaning 5 degrees",
                "recommended_action": "Re-wrap load before transport. Do not move until secured.",
                "timestamp": "2024-12-19T15:30:00Z",
                "location_aisle": "A-14"
            }
        }


class SafetyIncident(BaseModel):
    """Record of a safety incident or near-miss for tracking"""
    id: Optional[str] = None
    organization_id: str
    inspection_result: InspectionResult
    image_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    notes: Optional[str] = None


class LoadInspectionRequest(BaseModel):
    """Request model for load inspection"""
    location_aisle: Optional[str] = Field(None, description="Aisle or location where photo was taken")
    notes: Optional[str] = Field(None, description="Additional context from the driver")
