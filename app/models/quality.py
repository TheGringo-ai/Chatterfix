"""
QualityFix Models
The "Digital Inspector" - AI-powered quality management and CAPA

Module C of the Gringo Industrial OS Trinity:
- ChatterFix (Maintenance)
- FactoryFix (Production)
- QualityFix (QMS) <- THIS
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class InspectionResult(str, Enum):
    """Inspection outcome"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"  # Pass with notes
    PENDING = "pending"


class DefectSeverity(str, Enum):
    """Non-conformance severity"""
    CRITICAL = "critical"    # Safety/regulatory issue - STOP
    MAJOR = "major"          # Affects function - needs rework
    MINOR = "minor"          # Cosmetic - may ship with waiver
    OBSERVATION = "observation"  # Trend to watch


class CAPAStatus(str, Enum):
    """Corrective/Preventive Action status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    VERIFICATION = "verification"  # Waiting to confirm effectiveness
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ChecklistItem(BaseModel):
    """Single item in an inspection checklist"""
    id: str
    question: str
    response_type: str = "pass_fail"  # pass_fail, numeric, text, photo
    required: bool = True

    # Response
    response: Optional[str] = None
    numeric_value: Optional[float] = None
    numeric_min: Optional[float] = None
    numeric_max: Optional[float] = None
    photo_url: Optional[str] = None

    # Result
    passed: Optional[bool] = None
    notes: Optional[str] = None


class InspectionTemplate(BaseModel):
    """
    Reusable inspection checklist template
    The "Template Library" - like SafetyCulture's 100k+ forms
    """
    id: Optional[str] = None
    organization_id: str

    name: str
    description: Optional[str] = None
    category: str  # incoming, in_process, final, audit

    # Template definition
    items: List[ChecklistItem] = []

    # Applicability
    asset_types: List[str] = []  # Which assets this applies to
    product_skus: List[str] = []  # Which products

    # Metadata
    version: str = "1.0"
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Final Assembly Inspection",
                "category": "final",
                "items": [
                    {"id": "1", "question": "All fasteners torqued to spec?", "response_type": "pass_fail"},
                    {"id": "2", "question": "Surface finish acceptable?", "response_type": "pass_fail"},
                    {"id": "3", "question": "Dimension A (mm)", "response_type": "numeric", "numeric_min": 99.5, "numeric_max": 100.5}
                ]
            }
        }


class Inspection(BaseModel):
    """
    Completed inspection record
    """
    id: Optional[str] = None
    organization_id: str

    # What was inspected
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    production_run_id: Optional[str] = None
    product_sku: Optional[str] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None

    # The checklist
    items: List[ChecklistItem] = []

    # Result
    result: InspectionResult = InspectionResult.PENDING
    pass_count: int = 0
    fail_count: int = 0
    total_items: int = 0

    # Who/When
    inspector_id: Optional[str] = None
    inspector_name: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Follow-up
    nc_ids: List[str] = []  # Generated non-conformances
    notes: Optional[str] = None

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "Final Assembly Inspection",
                "asset_name": "Assembly Station 5",
                "result": "fail",
                "pass_count": 8,
                "fail_count": 2,
                "total_items": 10,
                "inspector_name": "Maria Garcia"
            }
        }


class NonConformance(BaseModel):
    """
    The "Snitch" - Record of a quality defect
    """
    id: Optional[str] = None
    organization_id: str

    # Source
    source_type: str = "inspection"  # inspection, production, customer, audit
    inspection_id: Optional[str] = None
    production_run_id: Optional[str] = None
    machine_id: Optional[str] = None

    # What's wrong
    defect_type: str  # scratch, dimension, missing_part, contamination, etc.
    description: str
    severity: DefectSeverity

    # Evidence
    image_url: Optional[str] = None
    image_urls: List[str] = []
    ai_analysis: Optional[str] = None  # From Visual QA
    ai_defect_location: Optional[str] = None  # Where AI circled the defect

    # Affected items
    product_sku: Optional[str] = None
    lot_number: Optional[str] = None
    serial_numbers: List[str] = []
    quantity_affected: int = 1

    # Disposition
    disposition: str = "pending"  # pending, scrap, rework, use_as_is, return_to_vendor
    disposition_by: Optional[str] = None
    disposition_at: Optional[str] = None
    disposition_notes: Optional[str] = None

    # CAPA link
    capa_required: bool = False
    capa_id: Optional[str] = None

    # Reporting
    reported_by: Optional[str] = None
    reported_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Voice command support
    voice_transcript: Optional[str] = None  # "Reject, scratch on surface"

    class Config:
        json_schema_extra = {
            "example": {
                "defect_type": "surface_scratch",
                "description": "Deep scratch on front panel, 3cm length",
                "severity": "major",
                "disposition": "rework",
                "voice_transcript": "Reject, scratch on surface, needs buffing"
            }
        }


class CAPA(BaseModel):
    """
    Corrective Action / Preventive Action
    The systematic problem-solving follow-up
    """
    id: Optional[str] = None
    organization_id: str

    # Link to problem
    nc_ids: List[str] = []  # Source non-conformances
    problem_statement: str

    # Root Cause Analysis
    root_cause_method: str = "5_why"  # 5_why, fishbone, fmea
    root_cause_analysis: Optional[str] = None
    root_cause: Optional[str] = None

    # Corrective Action (Fix the current problem)
    corrective_action_plan: Optional[str] = None
    corrective_action_owner: Optional[str] = None
    corrective_action_due: Optional[str] = None
    corrective_action_completed: Optional[str] = None

    # Preventive Action (Stop it from happening again)
    preventive_action_plan: Optional[str] = None
    preventive_action_owner: Optional[str] = None
    preventive_action_due: Optional[str] = None
    preventive_action_completed: Optional[str] = None

    # Verification (Did it work?)
    verification_method: Optional[str] = None
    verification_date: Optional[str] = None
    verification_result: Optional[str] = None
    effectiveness_confirmed: bool = False

    # Status
    status: CAPAStatus = CAPAStatus.OPEN
    priority: str = "medium"  # low, medium, high, critical

    # Cross-module triggers
    triggered_work_order_ids: List[str] = []  # ChatterFix maintenance
    triggered_training_ids: List[str] = []    # LineSmart training

    # Metadata
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: Optional[str] = None
    closed_by: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "problem_statement": "5 scratched panels in lot #2024-1220",
                "root_cause": "Worn conveyor belt causing friction damage",
                "corrective_action_plan": "Replace conveyor belt section 3",
                "preventive_action_plan": "Add belt inspection to weekly PM checklist",
                "status": "in_progress"
            }
        }


class VisualQAResult(BaseModel):
    """
    Result of AI visual comparison (Actual vs Golden Sample)
    """
    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)

    # Defect detection
    defects_found: List[Dict[str, Any]] = []  # [{type, location, severity}]
    defect_count: int = 0

    # Image analysis
    similarity_score: float = Field(ge=0.0, le=1.0, description="How similar to golden sample")
    annotated_image_url: Optional[str] = None  # Image with defects circled

    # AI explanation
    analysis_summary: str
    recommended_action: str

    class Config:
        json_schema_extra = {
            "example": {
                "passed": False,
                "confidence": 0.94,
                "defects_found": [
                    {"type": "scratch", "location": "upper-left quadrant", "severity": "major"}
                ],
                "defect_count": 1,
                "similarity_score": 0.82,
                "analysis_summary": "Surface scratch detected that deviates from golden sample",
                "recommended_action": "Mark as non-conforming. Route to rework station."
            }
        }


class QualityDashboard(BaseModel):
    """
    Quality metrics overview
    """
    # Inspection stats
    inspections_today: int = 0
    inspections_passed: int = 0
    inspections_failed: int = 0
    first_pass_yield: float = 100.0

    # NC stats
    open_ncs: int = 0
    ncs_today: int = 0
    ncs_by_severity: Dict[str, int] = {}

    # CAPA stats
    open_capas: int = 0
    overdue_capas: int = 0

    # Trends
    yield_trend: str = "stable"  # improving, declining, stable
    top_defect_types: List[Dict[str, Any]] = []

    class Config:
        json_schema_extra = {
            "example": {
                "inspections_today": 45,
                "inspections_passed": 42,
                "inspections_failed": 3,
                "first_pass_yield": 93.3,
                "open_ncs": 7,
                "open_capas": 2,
                "top_defect_types": [
                    {"type": "scratch", "count": 12},
                    {"type": "dimension", "count": 5}
                ]
            }
        }
