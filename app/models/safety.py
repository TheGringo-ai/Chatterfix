"""
SafetyFix Models
The "Guardian Angel" - Proactive safety intelligence for industrial environments

This module transforms safety from reactive paperwork to proactive accident prevention.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    """Incident severity levels for triage"""
    CRITICAL = "critical"  # Immediate danger, stop work
    HIGH = "high"          # Urgent attention required
    MEDIUM = "medium"      # Address within shift
    LOW = "low"            # Track and monitor


class IncidentType(str, Enum):
    """Types of safety incidents"""
    NEAR_MISS = "near_miss"           # Almost happened
    HAZARD_REPORT = "hazard_report"   # Dangerous condition spotted
    PPE_VIOLATION = "ppe_violation"   # Missing safety equipment
    EQUIPMENT_FAILURE = "equipment_failure"
    SLIP_TRIP_FALL = "slip_trip_fall"
    CHEMICAL_SPILL = "chemical_spill"
    FIRE_HAZARD = "fire_hazard"
    ELECTRICAL = "electrical"
    ERGONOMIC = "ergonomic"
    MAN_DOWN = "man_down"             # Fall detection triggered
    OTHER = "other"


class PPEType(str, Enum):
    """Personal Protective Equipment types"""
    HARD_HAT = "hard_hat"
    SAFETY_GLASSES = "safety_glasses"
    SAFETY_VEST = "safety_vest"
    SAFETY_HARNESS = "safety_harness"
    STEEL_TOE_BOOTS = "steel_toe_boots"
    GLOVES = "gloves"
    EAR_PROTECTION = "ear_protection"
    RESPIRATOR = "respirator"
    FACE_SHIELD = "face_shield"


class PPEViolation(BaseModel):
    """Detected PPE violation"""
    missing_ppe: List[PPEType]
    person_description: Optional[str] = None
    location: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class SafetyIncidentReport(BaseModel):
    """
    Voice-reported safety incident
    The "Near-Miss" button that turns every worker into a safety officer
    """
    id: Optional[str] = None
    organization_id: str

    # Report details
    incident_type: IncidentType
    severity: IncidentSeverity
    description: str
    voice_transcript: Optional[str] = None

    # Location data
    location: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    zone: Optional[str] = None  # "Confined Space", "High Voltage", etc.

    # Evidence
    image_url: Optional[str] = None
    video_url: Optional[str] = None  # Black Box footage

    # Metadata
    reporter_id: Optional[str] = None
    reporter_name: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Resolution tracking
    status: str = "open"  # open, assigned, in_progress, resolved
    assigned_to: Optional[str] = None
    work_order_id: Optional[str] = None  # Auto-created work order
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "incident_type": "near_miss",
                "severity": "medium",
                "description": "Oil slick on Walkway B near dock door 3",
                "location": "Walkway B",
                "voice_transcript": "Hey ChatterFix, near miss. Oil slick on Walkway B.",
                "status": "assigned",
                "assigned_to": "maintenance_team"
            }
        }


class ManDownEvent(BaseModel):
    """
    The "Black Box" - Automatic fall detection event
    Captures the 30 seconds before and after a fall
    """
    id: Optional[str] = None
    organization_id: str

    # Event data
    user_id: str
    user_name: Optional[str] = None

    # Detection metrics
    g_force_detected: float  # Peak G-force that triggered detection
    fall_duration_ms: int    # How long the fall lasted
    impact_severity: str     # "light", "moderate", "severe"

    # Location
    location: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None

    # Black Box footage
    video_buffer_url: Optional[str] = None  # 30-second rolling buffer saved to cloud
    video_start_offset: int = -30  # Seconds before trigger
    video_end_offset: int = 30     # Seconds after trigger

    # Response tracking
    triggered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    emergency_contacted: bool = False
    supervisor_notified: bool = False
    false_alarm: bool = False
    false_alarm_confirmed_by: Optional[str] = None

    # Medical response
    medical_response_required: bool = False
    medical_response_time: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "tech_123",
                "user_name": "Jake Martinez",
                "g_force_detected": 4.2,
                "fall_duration_ms": 850,
                "impact_severity": "moderate",
                "location": "Warehouse Section C, Aisle 7",
                "gps_lat": 29.7604,
                "gps_lng": -95.3698,
                "emergency_contacted": True,
                "supervisor_notified": True
            }
        }


class ZoneAlert(BaseModel):
    """
    Geofenced safety zone alert
    Triggers when worker enters hazardous zone
    """
    zone_id: str
    zone_name: str  # "Confined Space Tank A", "High Voltage Room"
    zone_type: str  # "confined_space", "high_voltage", "chemical", "fall_hazard"

    required_ppe: List[PPEType] = []
    required_certifications: List[str] = []  # "Confined Space Entry", "Lockout/Tagout"

    warning_message: str
    checklist_items: List[str] = []  # Things to verify before entering

    class Config:
        json_schema_extra = {
            "example": {
                "zone_id": "zone_tank_a",
                "zone_name": "Chemical Storage Tank A",
                "zone_type": "confined_space",
                "required_ppe": ["respirator", "safety_harness", "hard_hat"],
                "required_certifications": ["Confined Space Entry", "Chemical Handling"],
                "warning_message": "STOP! Confined Space Entry. Check oxygen levels before proceeding.",
                "checklist_items": [
                    "Oxygen level verified > 19.5%",
                    "Atmospheric testing complete",
                    "Spotter present at entry point",
                    "Rescue equipment ready"
                ]
            }
        }


class PPECheckResult(BaseModel):
    """Result of AI-powered PPE compliance check"""
    compliant: bool
    violations: List[PPEViolation] = []
    persons_checked: int = 0
    all_ppe_detected: List[PPEType] = []
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    recommended_action: str

    class Config:
        json_schema_extra = {
            "example": {
                "compliant": False,
                "violations": [
                    {
                        "missing_ppe": ["hard_hat", "safety_glasses"],
                        "person_description": "Worker in blue shirt near forklift",
                        "confidence": 0.89
                    }
                ],
                "persons_checked": 2,
                "all_ppe_detected": ["safety_vest", "steel_toe_boots"],
                "confidence": 0.92,
                "description": "1 of 2 workers missing required PPE",
                "recommended_action": "Remind worker to wear hard hat and safety glasses before entering work area"
            }
        }


class SafetyDashboardStats(BaseModel):
    """Safety metrics for executive dashboard"""
    total_incidents_today: int = 0
    total_incidents_week: int = 0
    total_incidents_month: int = 0

    near_misses_reported: int = 0
    ppe_violations_detected: int = 0
    man_down_events: int = 0

    # The money metric
    estimated_accidents_prevented: int = 0
    estimated_cost_savings: float = 0.0  # Average workplace injury costs $40k+

    # Trends
    safety_score: float = 100.0  # 0-100, higher is better
    trend_direction: str = "stable"  # "improving", "declining", "stable"

    class Config:
        json_schema_extra = {
            "example": {
                "total_incidents_today": 3,
                "total_incidents_week": 12,
                "total_incidents_month": 47,
                "near_misses_reported": 31,
                "ppe_violations_detected": 8,
                "man_down_events": 1,
                "estimated_accidents_prevented": 5,
                "estimated_cost_savings": 200000.0,
                "safety_score": 94.5,
                "trend_direction": "improving"
            }
        }
