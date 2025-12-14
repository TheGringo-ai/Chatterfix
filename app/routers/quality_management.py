"""
�️ Food Processing Quality Management System (QMS) Router
Comprehensive HACCP, GMP, and Food Safety Compliance for Cheese & Beverage Plants
Industry-specific quality control, supplier management, and regulatory compliance
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and templates
router = APIRouter(prefix="/quality", tags=["Food Processing Quality Management"])
templates = Jinja2Templates(directory="app/templates")

# ===== INDUSTRY CONFIGURATIONS =====

INDUSTRY_CONFIGS = {
    "cheese_plant": {
        "name": "Cheese Processing Plant",
        "haccp_focus": ["Pasteurization", "Cooling", "Aging", "Packaging"],
        "critical_limits": {
            "milk_temp": {"min": 4, "max": 7, "unit": "°C"},
            "pasteurization_temp": {"min": 72, "max": 75, "unit": "°C"},
            "aging_temp": {"min": 7, "max": 15, "unit": "°C"},
            "ph_range": {"min": 4.5, "max": 7.0, "unit": "pH"}
        },
        "common_allergens": ["Milk", "Lactose"],
        "certifications": ["SQF", "FSMA", "EU Organic", "Halal"],
        "monitoring_points": ["Raw Milk Receiving", "Pasteurization", "Cheese Making", "Aging Rooms", "Packaging"]
    },
    "beverage_plant": {
        "name": "Beverage Processing Plant",
        "haccp_focus": ["Filtration", "Pasteurization", "Carbonation", "Packaging"],
        "critical_limits": {
            "product_temp": {"min": 2, "max": 8, "unit": "°C"},
            "pasteurization_temp": {"min": 85, "max": 95, "unit": "°C"},
            "ph_range": {"min": 2.5, "max": 4.5, "unit": "pH"},
            "brix_level": {"min": 8, "max": 15, "unit": "°Brix"}
        },
        "common_allergens": ["None"],
        "certifications": ["FSSC 22000", "BRC", "IFS", "Organic"],
        "monitoring_points": ["Raw Material Receiving", "Mixing", "Filtration", "Pasteurization", "Carbonation", "Packaging"]
    },
    "dairy_processing": {
        "name": "Dairy Processing Plant",
        "haccp_focus": ["Pasteurization", "Homogenization", "Cooling", "Packaging"],
        "critical_limits": {
            "milk_temp": {"min": 4, "max": 7, "unit": "°C"},
            "pasteurization_temp": {"min": 72, "max": 75, "unit": "°C"},
            "storage_temp": {"min": 2, "max": 6, "unit": "°C"}
        },
        "common_allergens": ["Milk", "Lactose"],
        "certifications": ["SQF", "FSMA", "ISO 22000"],
        "monitoring_points": ["Milk Receiving", "Storage", "Processing", "Pasteurization", "Packaging"]
    }
}

# ===== PYDANTIC MODELS =====

class IndustrySelection(BaseModel):
    industry_type: str = Field(..., description="cheese_plant, beverage_plant, dairy_processing")
    plant_name: str
    location: str
    certifications: List[str] = []
    haccp_team: List[str] = []

class HACCPPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    industry_type: str
    process_step: str
    hazard_type: str = Field(..., description="Biological, Chemical, Physical")
    hazard_description: str
    critical_control_point: bool
    critical_limits: Dict[str, Any]
    monitoring_procedures: str
    corrective_actions: str
    verification_procedures: str
    records_required: List[str]
    responsible_person: str
    review_frequency: str = Field(..., description="Daily, Weekly, Monthly")
    status: str = Field(..., description="Active, Under Review, Suspended")
    created_at: datetime = Field(default_factory=datetime.now)

class TemperatureMonitoring(BaseModel):
    reading_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location: str
    equipment_id: str
    temperature: float
    unit: str = Field(default="°C")
    critical_limit_min: float
    critical_limit_max: float
    within_limits: bool
    corrective_action_taken: bool = False
    corrective_action_details: Optional[str] = None
    recorded_by: str
    reading_time: datetime = Field(default_factory=datetime.now)

class BatchRecord(BaseModel):
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_code: str
    product_name: str
    batch_number: str
    production_date: datetime
    expiry_date: datetime
    quantity_produced: float
    unit_of_measure: str
    raw_materials: List[Dict[str, Any]]  # [{"supplier": "", "material": "", "lot": "", "quantity": ""}]
    processing_steps: List[Dict[str, Any]]  # [{"step": "", "operator": "", "time": "", "parameters": ""}]
    quality_checks: List[Dict[str, Any]]  # [{"check": "", "result": "", "inspector": ""}]
    packaging_details: Dict[str, Any]
    storage_conditions: Dict[str, Any]
    status: str = Field(..., description="In Production, Completed, Released, Quarantined, Rejected")
    release_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class AllergenManagement(BaseModel):
    allergen_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    allergen_name: str
    allergen_type: str = Field(..., description="Major, Minor")
    detection_method: str
    threshold_level: float
    unit: str
    control_measures: List[str]
    cross_contamination_risks: List[str]
    labeling_requirements: str
    last_updated: datetime = Field(default_factory=datetime.now)

class SupplierQuality(BaseModel):
    supplier_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_name: str
    supplier_type: str = Field(..., description="Raw Materials, Packaging, Services")
    certifications: List[str] = []
    audit_score: float = Field(default=0.0, ge=0, le=100)
    last_audit_date: Optional[datetime] = None
    next_audit_date: Optional[datetime] = None
    approved_materials: List[str] = []
    quality_incidents: int = 0
    delivery_performance: float = Field(default=100.0, ge=0, le=100)
    status: str = Field(..., description="Approved, Conditional, Rejected, Under Review")
    contact_info: Dict[str, str]
    created_at: datetime = Field(default_factory=datetime.now)

class FoodSafetyInspection(BaseModel):
    inspection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inspection_type: str = Field(..., description="HACCP Verification, GMP Audit, Environmental, Product")
    area_location: str
    inspector_name: str
    inspection_date: datetime
    checklist_items: List[Dict[str, Any]]  # [{"item": "", "compliant": bool, "notes": ""}]
    overall_score: float = Field(..., ge=0, le=100)
    critical_findings: int = 0
    major_findings: int = 0
    minor_findings: int = 0
    corrective_actions_required: bool
    follow_up_date: Optional[datetime] = None
    status: str = Field(..., description="Pass, Conditional Pass, Fail")
    created_at: datetime = Field(default_factory=datetime.now)

class ProductRecall(BaseModel):
    recall_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recall_type: str = Field(..., description="Voluntary, Regulatory")
    reason: str
    affected_products: List[str]
    affected_batches: List[str]
    affected_lots: List[str]
    quantity_affected: float
    distribution_areas: List[str]
    recall_date: datetime
    notification_method: str
    effectiveness_check: bool = False
    status: str = Field(..., description="Initiated, In Progress, Completed")
    responsible_person: str
    created_at: datetime = Field(default_factory=datetime.now)

class SanitationSchedule(BaseModel):
    schedule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    area: str
    frequency: str = Field(..., description="Daily, Shift, Weekly, Monthly")
    sanitation_type: str = Field(..., description="Deep Clean, Routine, Sanitize, Disinfect")
    responsible_person: str
    checklist_items: List[str]
    chemicals_used: List[Dict[str, Any]]  # [{"chemical": "", "concentration": "", "contact_time": ""}]
    verification_method: str
    last_completed: Optional[datetime] = None
    next_due: datetime
    status: str = Field(..., description="Scheduled, In Progress, Completed, Overdue")
    created_at: datetime = Field(default_factory=datetime.now)

class EnvironmentalMonitoring(BaseModel):
    monitoring_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location: str
    parameter_type: str = Field(..., description="Air Quality, Water Quality, Surface Hygiene, Pest Activity")
    parameter_name: str
    measured_value: float
    unit: str
    acceptable_range_min: float
    acceptable_range_max: float
    within_limits: bool
    sampling_method: str
    technician: str
    monitoring_date: datetime = Field(default_factory=datetime.now)

class CAPA(BaseModel):
    capa_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field(..., description="NCR, Audit, Complaint, HACCP Deviation")
    source_reference: str
    problem_description: str
    root_cause: str
    corrective_actions: List[Dict[str, Any]]  # [{"action": "", "responsible": "", "due_date": "", "status": ""}]
    preventive_actions: List[Dict[str, Any]]  # [{"action": "", "responsible": "", "due_date": "", "status": ""}]
    effectiveness_verification: str
    target_completion_date: datetime
    actual_completion_date: Optional[datetime] = None
    status: str = Field(..., description="Open, In Progress, Closed, Verified")
    created_at: datetime = Field(default_factory=datetime.now)

# ===== MOCK DATA FOR FOOD PROCESSING =====

def get_mock_haccp_plans():
    return [
        {
            "plan_id": "HACCP-001",
            "industry_type": "cheese_plant",
            "process_step": "Milk Receiving & Storage",
            "hazard_type": "Biological",
            "hazard_description": "Pathogenic bacteria growth in raw milk",
            "critical_control_point": True,
            "critical_limits": {"temperature": {"min": 0, "max": 7, "unit": "°C"}, "time": {"max": 2, "unit": "hours"}},
            "monitoring_procedures": "Temperature monitoring every 2 hours, visual inspection for signs of spoilage",
            "corrective_actions": "Reject milk if temperature >7°C or holding time >2 hours",
            "verification_procedures": "Daily calibration of thermometers, weekly review of records",
            "records_required": ["Temperature logs", "Receiving inspection forms", "Rejection records"],
            "responsible_person": "Receiving Supervisor",
            "review_frequency": "Daily",
            "status": "Active"
        },
        {
            "plan_id": "HACCP-002",
            "industry_type": "cheese_plant",
            "process_step": "Pasteurization",
            "hazard_type": "Biological",
            "hazard_description": "Survival of pathogenic microorganisms",
            "critical_control_point": True,
            "critical_limits": {"temperature": {"min": 72, "max": 75, "unit": "°C"}, "time": {"min": 15, "unit": "seconds"}},
            "monitoring_procedures": "Continuous temperature recording, time-temperature integration",
            "corrective_actions": "Stop production, re-pasteurize if temperature drops below 72°C",
            "verification_procedures": "Weekly validation of pasteurization equipment",
            "records_required": ["Pasteurization charts", "Equipment validation records"],
            "responsible_person": "Production Manager",
            "review_frequency": "Daily",
            "status": "Active"
        },
        {
            "plan_id": "HACCP-003",
            "industry_type": "beverage_plant",
            "process_step": "Carbonation Process",
            "hazard_type": "Chemical",
            "hazard_description": "Incorrect CO2 levels affecting product safety",
            "critical_control_point": True,
            "critical_limits": {"co2_level": {"min": 2.5, "max": 3.5, "unit": "volumes"}},
            "monitoring_procedures": "CO2 analyzer readings every 30 minutes",
            "corrective_actions": "Adjust CO2 injection, re-test product",
            "verification_procedures": "Monthly calibration of CO2 analyzer",
            "records_required": ["CO2 monitoring logs", "Calibration records"],
            "responsible_person": "Quality Control Technician",
            "review_frequency": "Daily",
            "status": "Active"
        }
    ]

def get_mock_temperature_readings():
    return [
        {
            "reading_id": "TEMP-001",
            "location": "Raw Milk Storage Tank A1",
            "equipment_id": "TANK-001",
            "temperature": 4.2,
            "unit": "°C",
            "critical_limit_min": 0,
            "critical_limit_max": 7,
            "within_limits": True,
            "corrective_action_taken": False,
            "recorded_by": "Maria Sanchez",
            "reading_time": "2024-12-14T06:00:00"
        },
        {
            "reading_id": "TEMP-002",
            "location": "Cheese Aging Room B2",
            "equipment_id": "ROOM-B2",
            "temperature": 12.8,
            "unit": "°C",
            "critical_limit_min": 7,
            "critical_limit_max": 15,
            "within_limits": True,
            "corrective_action_taken": False,
            "recorded_by": "Carlos Rodriguez",
            "reading_time": "2024-12-14T08:30:00"
        },
        {
            "reading_id": "TEMP-003",
            "location": "Beverage Cooler C1",
            "equipment_id": "COOLER-C1",
            "temperature": 3.1,
            "unit": "°C",
            "critical_limit_min": 2,
            "critical_limit_max": 8,
            "within_limits": True,
            "corrective_action_taken": False,
            "recorded_by": "Anna Chen",
            "reading_time": "2024-12-14T10:15:00"
        }
    ]

def get_mock_batch_records():
    return [
        {
            "batch_id": "BATCH-2024-001",
            "product_code": "CHEDDAR-001",
            "product_name": "Sharp Cheddar Cheese",
            "batch_number": "CH24121401",
            "production_date": "2024-12-14T08:00:00",
            "expiry_date": "2025-06-14T00:00:00",
            "quantity_produced": 2500,
            "unit_of_measure": "kg",
            "raw_materials": [
                {"supplier": "Dairy Farms Inc", "material": "Raw Milk", "lot": "MILK24121301", "quantity": 2800},
                {"supplier": "Starter Cultures Ltd", "material": "Cheese Culture", "lot": "CULT24121001", "quantity": 5},
                {"supplier": "Enzymes Corp", "material": "Rennet", "lot": "RENN24121101", "quantity": 2.5}
            ],
            "processing_steps": [
                {"step": "Milk Reception", "operator": "Maria Sanchez", "time": "08:00", "parameters": "Temp: 4°C"},
                {"step": "Pasteurization", "operator": "Carlos Rodriguez", "time": "09:30", "parameters": "72°C for 15s"},
                {"step": "Cheese Making", "operator": "Anna Chen", "time": "11:00", "parameters": "pH: 6.2"}
            ],
            "quality_checks": [
                {"check": "Fat Content", "result": "32.5%", "inspector": "Dr. Sarah Johnson"},
                {"check": "Microbial Count", "result": "<10 CFU/g", "inspector": "Lab Technician Mike"},
                {"check": "pH Level", "result": "5.2", "inspector": "QC Lead Tom"}
            ],
            "packaging_details": {"type": "Vacuum Sealed", "weight_per_unit": "250g", "units_produced": 10000},
            "storage_conditions": {"temperature": "4°C", "humidity": "85%", "location": "Cold Storage A"},
            "status": "Released",
            "release_date": "2024-12-14T16:00:00"
        },
        {
            "batch_id": "BATCH-2024-002",
            "product_code": "BEVERAGE-001",
            "product_name": "Orange Juice",
            "batch_number": "OJ24121401",
            "production_date": "2024-12-14T07:00:00",
            "expiry_date": "2025-03-14T00:00:00",
            "quantity_produced": 5000,
            "unit_of_measure": "liters",
            "raw_materials": [
                {"supplier": "Citrus Growers Co", "material": "Fresh Oranges", "lot": "ORANGE24121301", "quantity": 8000},
                {"supplier": "Sweeteners Inc", "material": "Sugar", "lot": "SUGAR24121201", "quantity": 250}
            ],
            "processing_steps": [
                {"step": "Fruit Reception", "operator": "Juan Martinez", "time": "07:00", "parameters": "Temp: 8°C"},
                {"step": "Juice Extraction", "operator": "Lisa Wong", "time": "08:30", "parameters": "Yield: 65%"},
                {"step": "Pasteurization", "operator": "David Kim", "time": "10:00", "parameters": "95°C for 30s"}
            ],
            "quality_checks": [
                {"check": "Brix Level", "result": "12.5°", "inspector": "QC Tech Sarah"},
                {"check": "Acidity", "result": "0.8%", "inspector": "Lab Tech John"},
                {"check": "Microbial Test", "result": "Negative", "inspector": "Microbiologist Emma"}
            ],
            "packaging_details": {"type": "Tetra Pak", "volume_per_unit": "1L", "units_produced": 5000},
            "storage_conditions": {"temperature": "4°C", "location": "Warehouse B"},
            "status": "In Production"
        }
    ]

def get_mock_allergens():
    return [
        {
            "allergen_id": "ALL-001",
            "allergen_name": "Milk Protein",
            "allergen_type": "Major",
            "detection_method": "ELISA Test",
            "threshold_level": 2.5,
            "unit": "ppm",
            "control_measures": ["Dedicated equipment", "Allergen cleaning procedures", "Staff training"],
            "cross_contamination_risks": ["Shared processing lines", "Inadequate cleaning"],
            "labeling_requirements": "Contains Milk"
        },
        {
            "allergen_id": "ALL-002",
            "allergen_name": "Peanuts",
            "allergen_type": "Major",
            "detection_method": "PCR Test",
            "threshold_level": 5.0,
            "unit": "ppm",
            "control_measures": ["Separate facility", "Allergen management plan", "Supplier verification"],
            "cross_contamination_risks": ["Airborne particles", "Shared storage"],
            "labeling_requirements": "May Contain Peanuts"
        },
        {
            "allergen_id": "ALL-003",
            "allergen_name": "Soy",
            "allergen_type": "Major",
            "detection_method": "ELISA Test",
            "threshold_level": 10.0,
            "unit": "ppm",
            "control_measures": ["Supplier specifications", "Incoming testing", "Label verification"],
            "cross_contamination_risks": ["Shared transportation", "Cross-contact during storage"],
            "labeling_requirements": "Contains Soy"
        }
    ]

def get_mock_suppliers():
    return [
        {
            "supplier_id": "SUP-001",
            "supplier_name": "Dairy Farms Inc",
            "supplier_type": "Raw Materials",
            "certifications": ["SQF Certified", "Organic Certified", "GAP Compliant"],
            "audit_score": 94.5,
            "last_audit_date": "2024-10-15T00:00:00",
            "next_audit_date": "2025-10-15T00:00:00",
            "approved_materials": ["Raw Milk", "Cream", "Butter"],
            "quality_incidents": 0,
            "delivery_performance": 98.5,
            "status": "Approved",
            "contact_info": {
                "contact_person": "John Smith",
                "email": "quality@dairyfarms.com",
                "phone": "(555) 123-4567",
                "address": "123 Farm Road, Rural Valley, CA 90210"
            }
        },
        {
            "supplier_id": "SUP-002",
            "supplier_name": "Packaging Solutions Ltd",
            "supplier_type": "Packaging",
            "certifications": ["ISO 9001", "FSSC 22000"],
            "audit_score": 91.2,
            "last_audit_date": "2024-11-20T00:00:00",
            "next_audit_date": "2025-11-20T00:00:00",
            "approved_materials": ["Cheese packaging", "Labels", "Boxes"],
            "quality_incidents": 1,
            "delivery_performance": 95.8,
            "status": "Approved",
            "contact_info": {
                "contact_person": "Maria Garcia",
                "email": "maria.garcia@packagingsolutions.com",
                "phone": "(555) 234-5678",
                "address": "456 Industrial Blvd, Manufacturing City, NY 10001"
            }
        }
    ]

def get_mock_food_safety_inspections():
    return [
        {
            "inspection_id": "FSI-2024-001",
            "inspection_type": "HACCP Verification",
            "area_location": "Pasteurization Area",
            "inspector_name": "Dr. Sarah Johnson",
            "inspection_date": "2024-12-14T09:00:00",
            "checklist_items": [
                {"item": "Temperature monitoring system calibrated", "compliant": True, "notes": ""},
                {"item": "Critical limits documented and current", "compliant": True, "notes": ""},
                {"item": "Corrective action records up to date", "compliant": True, "notes": ""},
                {"item": "Staff training records current", "compliant": False, "notes": "2 operators need refresher training"}
            ],
            "overall_score": 92.5,
            "critical_findings": 0,
            "major_findings": 1,
            "minor_findings": 0,
            "corrective_actions_required": True,
            "follow_up_date": "2024-12-21T09:00:00",
            "status": "Conditional Pass"
        },
        {
            "inspection_id": "FSI-2024-002",
            "inspection_type": "GMP Audit",
            "area_location": "Packaging Line A",
            "inspector_name": "Mike Chen",
            "inspection_date": "2024-12-13T14:30:00",
            "checklist_items": [
                {"item": "Personal hygiene standards maintained", "compliant": True, "notes": ""},
                {"item": "Equipment cleaning schedules followed", "compliant": True, "notes": ""},
                {"item": "Pest control program effective", "compliant": True, "notes": ""},
                {"item": "Allergen control procedures in place", "compliant": True, "notes": ""}
            ],
            "overall_score": 98.2,
            "critical_findings": 0,
            "major_findings": 0,
            "minor_findings": 0,
            "corrective_actions_required": False,
            "status": "Pass"
        }
    ]

def get_mock_sanitation_schedules():
    return [
        {
            "schedule_id": "SAN-001",
            "area": "Cheese Processing Line A",
            "frequency": "Daily",
            "sanitation_type": "Deep Clean",
            "responsible_person": "Sanitation Lead - Maria Sanchez",
            "checklist_items": [
                "Disassemble equipment components",
                "Pre-rinse with warm water",
                "Apply alkaline detergent",
                "Scrub all surfaces thoroughly",
                "Rinse with potable water",
                "Apply sanitizer (200 ppm chlorine)",
                "Air dry and reassemble"
            ],
            "chemicals_used": [
                {"chemical": "Alkaline Detergent", "concentration": "2%", "contact_time": "10 minutes"},
                {"chemical": "Chlorine Sanitizer", "concentration": "200 ppm", "contact_time": "5 minutes"}
            ],
            "verification_method": "ATP swab testing and visual inspection",
            "last_completed": "2024-12-14T06:00:00",
            "next_due": "2024-12-15T06:00:00",
            "status": "Completed"
        },
        {
            "schedule_id": "SAN-002",
            "area": "Beverage Mixing Tank B",
            "frequency": "Shift",
            "sanitation_type": "Routine",
            "responsible_person": "Production Operator - Carlos Rodriguez",
            "checklist_items": [
                "Drain and rinse tank",
                "Apply CIP (Clean In Place) solution",
                "Circulate for 15 minutes",
                "Rinse thoroughly",
                "Sanitize with hot water",
                "Verify cleanliness"
            ],
            "chemicals_used": [
                {"chemical": "CIP Detergent", "concentration": "1%", "contact_time": "15 minutes"},
                {"chemical": "Hot Water", "concentration": "85°C", "contact_time": "10 minutes"}
            ],
            "verification_method": "Conductivity testing and visual inspection",
            "last_completed": "2024-12-14T14:00:00",
            "next_due": "2024-12-14T22:00:00",
            "status": "Scheduled"
        }
    ]

def get_mock_environmental_monitoring():
    return [
        {
            "monitoring_id": "ENV-001",
            "location": "Processing Area A",
            "parameter_type": "Air Quality",
            "parameter_name": "Total Airborne Particles",
            "measured_value": 125000,
            "unit": "particles/m³",
            "acceptable_range_min": 0,
            "acceptable_range_max": 350000,
            "within_limits": True,
            "sampling_method": "Laser particle counter",
            "technician": "Environmental Tech Anna",
            "monitoring_date": "2024-12-14T10:00:00"
        },
        {
            "monitoring_id": "ENV-002",
            "location": "Packaging Area B",
            "parameter_type": "Surface Hygiene",
            "parameter_name": "ATP Level",
            "measured_value": 15,
            "unit": "RLU",
            "acceptable_range_min": 0,
            "acceptable_range_max": 30,
            "within_limits": True,
            "sampling_method": "ATP swab test",
            "technician": "QC Technician Mike",
            "monitoring_date": "2024-12-14T11:30:00"
        },
        {
            "monitoring_id": "ENV-003",
            "location": "Raw Material Storage",
            "parameter_type": "Pest Activity",
            "parameter_name": "Rodent Trap Status",
            "measured_value": 0,
            "unit": "captures",
            "acceptable_range_min": 0,
            "acceptable_range_max": 0,
            "within_limits": True,
            "sampling_method": "Visual inspection and trap checks",
            "technician": "Pest Control Specialist Lisa",
            "monitoring_date": "2024-12-14T08:00:00"
        }
    ]

def get_mock_capa_records():
    return [
        {
            "capa_id": "CAPA-2024-001",
            "source": "HACCP Deviation",
            "source_reference": "DEV-2024-012",
            "problem_description": "Pasteurization temperature dropped below 72°C for 45 seconds during production run",
            "root_cause": "Fouled heat exchanger reducing heat transfer efficiency",
            "corrective_actions": [
                {"action": "Clean and inspect heat exchanger", "responsible": "Maintenance Team", "due_date": "2024-12-16", "status": "Completed"},
                {"action": "Implement preventive maintenance schedule", "responsible": "Engineering", "due_date": "2024-12-20", "status": "In Progress"}
            ],
            "preventive_actions": [
                {"action": "Add temperature monitoring redundancy", "responsible": "Engineering", "due_date": "2024-12-30", "status": "Pending"},
                {"action": "Train operators on deviation response", "responsible": "Training Dept", "due_date": "2025-01-15", "status": "Pending"}
            ],
            "effectiveness_verification": "Monitor pasteurization temperatures for 30 days, verify no deviations occur",
            "target_completion_date": "2025-01-31",
            "actual_completion_date": None,
            "status": "In Progress",
            "created_at": datetime.now()
        }
    ]

def get_mock_supplier_audits():
    return [
        {
            "audit_id": "SA-2024-001",
            "supplier_name": "Precision Components Inc",
            "audit_date": "2024-12-05T09:00:00",
            "audit_type": "Annual",
            "auditor_name": "David Wilson",
            "quality_score": 92.0,
            "delivery_score": 88.5,
            "service_score": 94.0,
            "overall_score": 91.5,
            "certification_status": "Approved",
            "findings": [
                "Minor documentation gaps in quality procedures",
                "Calibration schedule needs updating"
            ],
            "recommendations": [
                "Update quality manual to latest revision",
                "Implement automated calibration reminders"
            ],
            "next_audit_date": "2025-12-05T09:00:00"
        },
        {
            "audit_id": "SA-2024-002",
            "supplier_name": "FastTrack Logistics",
            "audit_date": "2024-12-03T13:30:00",
            "audit_type": "Follow-up",
            "auditor_name": "Emily Brown",
            "quality_score": 85.0,
            "delivery_score": 96.0,
            "service_score": 90.0,
            "overall_score": 90.3,
            "certification_status": "Conditional",
            "findings": [
                "Packaging damage rate slightly elevated",
                "Delivery performance excellent"
            ],
            "recommendations": [
                "Implement additional packaging protection",
                "Review handling procedures at warehouse"
            ],
            "next_audit_date": "2025-06-03T13:30:00"
        }
    ]

def get_mock_product_tests():
    return [
        {
            "test_id": "PT-2024-001",
            "test_date": "2024-12-09T16:00:00",
            "test_type": "Performance",
            "product_code": "MOTOR-F600",
            "test_protocol": "IEC 60034-1 Efficiency Test",
            "test_criteria": "Motor efficiency at rated load",
            "measured_value": 94.2,
            "specification_min": 92.0,
            "specification_max": 100.0,
            "pass_status": True,
            "test_engineer": "Frank Martinez",
            "equipment_used": "Dynamometer System DS-5000"
        },
        {
            "test_id": "PT-2024-002",
            "test_date": "2024-12-08T11:30:00",
            "test_type": "Durability",
            "product_code": "BEARING-G700",
            "test_protocol": "ASTM D4170 Endurance Test",
            "test_criteria": "Operating hours before failure",
            "measured_value": 8750.0,
            "specification_min": 8000.0,
            "specification_max": 999999.0,
            "pass_status": True,
            "test_engineer": "Grace Chen",
            "equipment_used": "Endurance Test Rig ETR-200",
            "environmental_conditions": "Temperature: 25°C, Humidity: 45%"
        }
    ]

def get_mock_ncr_records():
    """Mock Non-Conformance Records for food processing quality management"""
    return [
        {
            "ncr_id": "NCR-2024-001",
            "date_reported": "2024-12-10T09:15:00",
            "product_batch": "CHEESE-2024-1208-001",
            "description": "Temperature deviation in aging room - exceeded upper limit by 2.5°C",
            "severity": "Major",
            "category": "Process Control",
            "source": "Temperature Monitoring System",
            "status": "Open",
            "assigned_to": "Quality Manager",
            "cost_impact": 2500.00,
            "capa_required": True,
            "root_cause": "HVAC system calibration drift",
            "corrective_action": "Recalibrate HVAC sensors and implement daily temperature checks"
        },
        {
            "ncr_id": "NCR-2024-002",
            "date_reported": "2024-12-08T14:30:00",
            "product_batch": "BEVERAGE-2024-1207-003",
            "description": "pH level outside specification in final product (measured: 4.8, spec: 4.2-4.6)",
            "severity": "Critical",
            "category": "Product Quality",
            "source": "Lab Analysis",
            "status": "Closed",
            "assigned_to": "Production Supervisor",
            "cost_impact": 15000.00,
            "capa_required": True,
            "root_cause": "Inadequate mixing time in carbonation process",
            "corrective_action": "Extended mixing time by 5 minutes and added pH monitoring checkpoint"
        },
        {
            "ncr_id": "NCR-2024-003",
            "date_reported": "2024-12-06T11:00:00",
            "product_batch": "DAIRY-2024-1205-002",
            "description": "Foreign material found in packaged product (metal fragment)",
            "severity": "Critical",
            "category": "Contamination",
            "source": "Customer Complaint",
            "status": "Open",
            "assigned_to": "Safety Officer",
            "cost_impact": 8500.00,
            "capa_required": True,
            "root_cause": "Metal detector sensitivity calibration issue",
            "corrective_action": "Immediate recalibration of metal detectors and product recall initiated"
        }
    ]

def get_mock_spc_data():
    """Statistical Process Control data for charts"""
    return {
        "control_charts": [
            {
                "parameter": "Shaft Diameter",
                "unit": "mm",
                "target": 25.00,
                "ucl": 25.15,
                "lcl": 24.85,
                "measurements": [25.02, 25.01, 24.98, 25.05, 24.97, 25.03, 25.00, 24.99, 25.04, 25.01],
                "cp": 1.33,
                "cpk": 1.28,
                "process_capability": "Capable"
            },
            {
                "parameter": "Surface Roughness",
                "unit": "μm",
                "target": 3.2,
                "ucl": 4.0,
                "lcl": 2.4,
                "measurements": [3.1, 3.3, 3.0, 3.4, 2.9, 3.2, 3.5, 3.1, 3.0, 3.3],
                "cp": 1.11,
                "cpk": 1.05,
                "process_capability": "Marginally Capable"
            }
        ]
    }

# ===== ROUTE HANDLERS =====

@router.get("/dashboard", response_class=HTMLResponse)
async def quality_dashboard(request: Request, industry: str = Query("cheese_plant", description="Industry type: cheese_plant, beverage_plant, dairy_processing")):
    """Food Processing Quality Management dashboard with HACCP and GMP compliance"""
    try:
        # Get industry configuration
        industry_config = INDUSTRY_CONFIGS.get(industry, INDUSTRY_CONFIGS["cheese_plant"])

        # Get comprehensive data
        haccp_plans = get_mock_haccp_plans()
        temperature_readings = get_mock_temperature_readings()
        batch_records = get_mock_batch_records()
        suppliers = get_mock_suppliers()
        supplier_audits = get_mock_supplier_audits()
        inspections = get_mock_food_safety_inspections()
        sanitation_schedules = get_mock_sanitation_schedules()
        environmental_monitoring = get_mock_environmental_monitoring()
        capa_records = get_mock_capa_records()
        spc_data = get_mock_spc_data()

        # Calculate key metrics
        active_haccp_plans = len([p for p in haccp_plans if p["status"] == "Active"])
        critical_control_points = len([p for p in haccp_plans if p["critical_control_point"]])
        temperature_deviations = len([t for t in temperature_readings if not t["within_limits"]])
        approved_suppliers = len([s for s in suppliers if s["status"] == "Approved"])
        completed_batches = len([b for b in batch_records if b["status"] == "Released"])
        sanitation_compliance = len([s for s in sanitation_schedules if s["status"] == "Completed"]) / len(sanitation_schedules) * 100 if sanitation_schedules else 0
        environmental_compliance = len([e for e in environmental_monitoring if e["within_limits"]]) / len(environmental_monitoring) * 100 if environmental_monitoring else 0

        # Calculate average scores
        avg_quality_score = sum(audit["quality_score"] for audit in supplier_audits) / len(supplier_audits) if supplier_audits else 0
        avg_supplier_score = sum(audit["overall_score"] for audit in supplier_audits) / len(supplier_audits) if supplier_audits else 0

        # Additional metrics
        first_pass_yield = 98.2
        iso_compliance = 94.5
        total_coq = 125000  # Cost of Quality in dollars
        cost_of_quality = {
            "prevention": 25000,
            "appraisal": 35000,
            "internal_failure": 45000,
            "external_failure": 20000
        }

        # Get additional data
        ncr_records = get_mock_ncr_records()
        product_tests = get_mock_product_tests()

        # Food safety compliance metrics
        food_safety_metrics = {
            "haccp_compliance": 96.8,
            "gmp_compliance": 94.2,
            "certification_status": {
                "current": "SQF Level 3",
                "score": 92.5
            },
            "last_audit_score": 92.5,
            "next_audit_due": "2025-03-15"
        }

        context = {
            "request": request,
            "industry_config": industry_config,
            "industry": industry,
            "active_haccp_plans": active_haccp_plans,
            "critical_control_points": critical_control_points,
            "temperature_deviations": temperature_deviations,
            "approved_suppliers": approved_suppliers,
            "completed_batches": completed_batches,
            "sanitation_compliance": round(sanitation_compliance, 1),
            "environmental_compliance": round(environmental_compliance, 1),
            "avg_quality_score": round(avg_quality_score, 1),
            "avg_supplier_score": round(avg_supplier_score, 1),
            "first_pass_yield": first_pass_yield,
            "iso_compliance": iso_compliance,
            "total_coq": total_coq,
            "cost_of_quality": cost_of_quality,
            "ncr_records": ncr_records,
            "product_tests": product_tests,
            "spc_data": spc_data,
            "food_safety_metrics": food_safety_metrics,
            "haccp_plans": haccp_plans[:5],
            "temperature_readings": temperature_readings[:10],
            "batch_records": batch_records[:3],
            "suppliers": suppliers,
            "supplier_audits": supplier_audits,
            "inspections": inspections,
            "sanitation_schedules": sanitation_schedules,
            "environmental_monitoring": environmental_monitoring[:5],
            "capa_records": capa_records,
            "chart": spc_data["control_charts"][0] if spc_data and spc_data.get("control_charts") else {}
        }

        logger.info(f"✅ Food Processing Quality Management dashboard loaded for {industry}")
        return templates.TemplateResponse("quality_dashboard.html", context)

    except Exception as e:
        logger.error(f"❌ Error loading quality dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@router.get("/haccp-plans")
async def get_haccp_plans(industry_type: Optional[str] = Query(None)):
    """Get HACCP plans with optional industry filtering"""
    try:
        plans = get_mock_haccp_plans()

        if industry_type:
            plans = [p for p in plans if p["industry_type"] == industry_type]

        return {
            "haccp_plans": plans,
            "total": len(plans),
            "summary": {
                "active_plans": len([p for p in plans if p["status"] == "Active"]),
                "critical_control_points": len([p for p in plans if p["critical_control_point"]]),
                "by_hazard_type": {
                    "Biological": len([p for p in plans if p["hazard_type"] == "Biological"]),
                    "Chemical": len([p for p in plans if p["hazard_type"] == "Chemical"]),
                    "Physical": len([p for p in plans if p["hazard_type"] == "Physical"])
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching HACCP plans: {e}")
        raise HTTPException(status_code=500, detail=f"HACCP plans error: {str(e)}")

@router.get("/temperature-monitoring")
async def get_temperature_monitoring(
    location: Optional[str] = Query(None),
    within_limits: Optional[bool] = Query(None),
    hours: int = Query(24, description="Hours of data to retrieve")
):
    """Get temperature monitoring data with filtering"""
    try:
        readings = get_mock_temperature_readings()

        # Apply filters
        if location:
            readings = [r for r in readings if location.lower() in r["location"].lower()]

        if within_limits is not None:
            readings = [r for r in readings if r["within_limits"] == within_limits]

        # Filter by time (mock recent data)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        readings = [r for r in readings if datetime.fromisoformat(r["reading_time"]) > cutoff_time]

        return {
            "temperature_readings": readings,
            "total": len(readings),
            "summary": {
                "within_limits": len([r for r in readings if r["within_limits"]]),
                "deviations": len([r for r in readings if not r["within_limits"]]),
                "compliance_rate": len([r for r in readings if r["within_limits"]]) / len(readings) * 100 if readings else 100
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching temperature data: {e}")
        raise HTTPException(status_code=500, detail=f"Temperature monitoring error: {str(e)}")

@router.get("/batch-records")
async def get_batch_records(
    status: Optional[str] = Query(None),
    product_code: Optional[str] = Query(None),
    days: int = Query(30, description="Days of data to retrieve")
):
    """Get batch records with filtering"""
    try:
        batches = get_mock_batch_records()

        # Apply filters
        if status:
            batches = [b for b in batches if b["status"] == status]

        if product_code:
            batches = [b for b in batches if b["product_code"] == product_code]

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        batches = [b for b in batches if datetime.fromisoformat(b["production_date"]) > cutoff_date]

        return {
            "batch_records": batches,
            "total": len(batches),
            "summary": {
                "completed": len([b for b in batches if b["status"] == "Released"]),
                "in_production": len([b for b in batches if b["status"] == "In Production"]),
                "quarantined": len([b for b in batches if b["status"] == "Quarantined"]),
                "rejected": len([b for b in batches if b["status"] == "Rejected"])
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching batch records: {e}")
        raise HTTPException(status_code=500, detail=f"Batch records error: {str(e)}")

@router.get("/suppliers")
async def get_suppliers(status: Optional[str] = Query(None)):
    """Get supplier quality data"""
    try:
        suppliers = get_mock_suppliers()

        if status:
            suppliers = [s for s in suppliers if s["status"] == status]

        return {
            "suppliers": suppliers,
            "total": len(suppliers),
            "summary": {
                "approved": len([s for s in suppliers if s["status"] == "Approved"]),
                "conditional": len([s for s in suppliers if s["status"] == "Conditional"]),
                "rejected": len([s for s in suppliers if s["status"] == "Rejected"]),
                "avg_audit_score": sum(s["audit_score"] for s in suppliers) / len(suppliers) if suppliers else 0,
                "avg_delivery_performance": sum(s["delivery_performance"] for s in suppliers) / len(suppliers) if suppliers else 0
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching suppliers: {e}")
        raise HTTPException(status_code=500, detail=f"Suppliers error: {str(e)}")

@router.get("/food-safety-inspections")
async def get_food_safety_inspections(
    inspection_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get food safety inspections"""
    try:
        inspections = get_mock_food_safety_inspections()

        if inspection_type:
            inspections = [i for i in inspections if i["inspection_type"] == inspection_type]

        if status:
            inspections = [i for i in inspections if i["status"] == status]

        return {
            "inspections": inspections,
            "total": len(inspections),
            "summary": {
                "pass": len([i for i in inspections if i["status"] == "Pass"]),
                "conditional_pass": len([i for i in inspections if i["status"] == "Conditional Pass"]),
                "fail": len([i for i in inspections if i["status"] == "Fail"]),
                "avg_score": sum(i["overall_score"] for i in inspections) / len(inspections) if inspections else 0,
                "critical_findings": sum(i["critical_findings"] for i in inspections),
                "major_findings": sum(i["major_findings"] for i in inspections),
                "minor_findings": sum(i["minor_findings"] for i in inspections)
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching food safety inspections: {e}")
        raise HTTPException(status_code=500, detail=f"Food safety inspections error: {str(e)}")

@router.get("/sanitation-schedules")
async def get_sanitation_schedules(
    frequency: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get sanitation schedules"""
    try:
        schedules = get_mock_sanitation_schedules()

        if frequency:
            schedules = [s for s in schedules if s["frequency"] == frequency]

        if status:
            schedules = [s for s in schedules if s["status"] == status]

        return {
            "sanitation_schedules": schedules,
            "total": len(schedules),
            "summary": {
                "scheduled": len([s for s in schedules if s["status"] == "Scheduled"]),
                "in_progress": len([s for s in schedules if s["status"] == "In Progress"]),
                "completed": len([s for s in schedules if s["status"] == "Completed"]),
                "overdue": len([s for s in schedules if s["status"] == "Overdue"]),
                "compliance_rate": len([s for s in schedules if s["status"] == "Completed"]) / len(schedules) * 100 if schedules else 0
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching sanitation schedules: {e}")
        raise HTTPException(status_code=500, detail=f"Sanitation schedules error: {str(e)}")

@router.get("/environmental-monitoring")
async def get_environmental_monitoring(
    parameter_type: Optional[str] = Query(None),
    within_limits: Optional[bool] = Query(None)
):
    """Get environmental monitoring data"""
    try:
        monitoring = get_mock_environmental_monitoring()

        if parameter_type:
            monitoring = [m for m in monitoring if m["parameter_type"] == parameter_type]

        if within_limits is not None:
            monitoring = [m for m in monitoring if m["within_limits"] == within_limits]

        return {
            "environmental_monitoring": monitoring,
            "total": len(monitoring),
            "summary": {
                "within_limits": len([m for m in monitoring if m["within_limits"]]),
                "deviations": len([m for m in monitoring if not m["within_limits"]]),
                "compliance_rate": len([m for m in monitoring if m["within_limits"]]) / len(monitoring) * 100 if monitoring else 100,
                "by_parameter_type": {
                    param_type: len([m for m in monitoring if m["parameter_type"] == param_type])
                    for param_type in set(m["parameter_type"] for m in monitoring)
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching environmental monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Environmental monitoring error: {str(e)}")

@router.get("/capa-records")
async def get_capa_records(status: Optional[str] = Query(None)):
    """Get CAPA (Corrective and Preventive Actions) records"""
    try:
        capa_records = get_mock_capa_records()

        if status:
            capa_records = [c for c in capa_records if c["status"] == status]

        return {
            "capa_records": capa_records,
            "total": len(capa_records),
            "summary": {
                "open": len([c for c in capa_records if c["status"] == "Open"]),
                "in_progress": len([c for c in capa_records if c["status"] == "In Progress"]),
                "closed": len([c for c in capa_records if c["status"] == "Closed"]),
                "verified": len([c for c in capa_records if c["status"] == "Verified"])
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching CAPA records: {e}")
        raise HTTPException(status_code=500, detail=f"CAPA records error: {str(e)}")

@router.get("/allergens")
async def get_allergens(allergen_type: Optional[str] = Query(None)):
    """Get allergen management data"""
    try:
        allergens = get_mock_allergens()

        if allergen_type:
            allergens = [a for a in allergens if a["allergen_type"] == allergen_type]

        return {
            "allergens": allergens,
            "total": len(allergens),
            "summary": {
                "major": len([a for a in allergens if a["allergen_type"] == "Major"]),
                "minor": len([a for a in allergens if a["allergen_type"] == "Minor"])
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching allergens: {e}")
        raise HTTPException(status_code=500, detail=f"Allergens error: {str(e)}")

@router.get("/industry-config")
async def get_industry_config(industry: str = Query("cheese_plant")):
    """Get industry-specific configuration"""
    try:
        config = INDUSTRY_CONFIGS.get(industry)
        if not config:
            raise HTTPException(status_code=404, detail=f"Industry configuration not found: {industry}")

        return {
            "industry": industry,
            "config": config,
            "available_industries": list(INDUSTRY_CONFIGS.keys())
        }
    except Exception as e:
        logger.error(f"❌ Error fetching industry config: {e}")
        raise HTTPException(status_code=500, detail=f"Industry config error: {str(e)}")

@router.get("/compliance-dashboard")
async def get_compliance_dashboard(industry: str = Query("cheese_plant")):
    """Get comprehensive compliance dashboard data"""
    try:
        industry_config = INDUSTRY_CONFIGS.get(industry, INDUSTRY_CONFIGS["cheese_plant"])

        # Mock compliance data
        compliance_data = {
            "haccp_compliance": 96.8,
            "gmp_compliance": 94.2,
            "certification_status": {
                "current": "SQF Level 3",
                "valid_until": "2025-12-31",
                "last_audit": "2024-10-15",
                "next_audit": "2025-10-15",
                "score": 92.5
            },
            "regulatory_requirements": {
                "fsma_compliance": 98.2,
                "allergen_labeling": 100.0,
                "nutrition_labeling": 97.8,
                "organic_certification": 95.5 if "Organic" in industry_config["certifications"] else None
            },
            "critical_metrics": {
                "temperature_deviations": 2,
                "microbial_failures": 0,
                "allergen_incidents": 1,
                "foreign_material_findings": 3
            },
            "audit_history": [
                {"date": "2024-10-15", "type": "SQF", "score": 92.5, "status": "Pass"},
                {"date": "2024-07-20", "type": "Internal", "score": 94.8, "status": "Pass"},
                {"date": "2024-04-10", "type": "Supplier", "score": 89.2, "status": "Conditional"}
            ]
        }

        return {
            "industry": industry,
            "compliance_data": compliance_data,
            "industry_config": industry_config
        }
    except Exception as e:
        logger.error(f"❌ Error fetching compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance dashboard error: {str(e)}")

@router.get("/traceability/{batch_id}")
async def get_batch_traceability(batch_id: str):
    """Get complete traceability for a batch"""
    try:
        # Mock traceability data
        traceability_data = {
            "batch_id": batch_id,
            "forward_trace": [
                {"step": "Production", "location": "Line A", "timestamp": "2024-12-14T08:00:00"},
                {"step": "Packaging", "location": "Pack Station 1", "timestamp": "2024-12-14T12:00:00"},
                {"step": "Storage", "location": "Cold Storage A", "timestamp": "2024-12-14T14:00:00"},
                {"step": "Shipping", "location": "Loading Dock 2", "timestamp": "2024-12-14T16:00:00"}
            ],
            "backward_trace": {
                "raw_materials": [
                    {"material": "Milk", "supplier": "Dairy Farms Inc", "lot": "MILK24121301", "origin": "Farm A, Wisconsin"},
                    {"material": "Culture", "supplier": "Starter Cultures Ltd", "lot": "CULT24121001", "origin": "Lab B, California"}
                ],
                "processing_equipment": ["Pasteurizer P-001", "Cheese Vat V-002", "Packaging Line PL-003"],
                "personnel": ["Operator: Maria Sanchez", "QC: Dr. Sarah Johnson", "Supervisor: Carlos Rodriguez"]
            },
            "quality_checks": [
                {"check": "Raw Material Inspection", "result": "Pass", "inspector": "Receiving QC"},
                {"check": "In-Process pH", "result": "5.2", "inspector": "Production QC"},
                {"check": "Final Microbial", "result": "<10 CFU/g", "inspector": "Lab Tech"}
            ],
            "distribution": {
                "customers": ["Retail Chain A", "Distributor B"],
                "quantities": [500, 300],
                "locations": ["Store 1-10", "Warehouse B"]
            }
        }

        return traceability_data
    except Exception as e:
        logger.error(f"❌ Error fetching traceability: {e}")
        raise HTTPException(status_code=500, detail=f"Traceability error: {str(e)}")

@router.get("/analytics")
async def get_quality_analytics(
    industry: str = Query("cheese_plant"),
    timeframe: str = Query("30d", description="7d, 30d, 90d, 1y")
):
    """Get comprehensive quality analytics"""
    try:
        # Mock analytics data
        analytics = {
            "timeframe": timeframe,
            "industry": industry,
            "kpi_summary": {
                "overall_quality_score": 94.8,
                "haccp_compliance": 96.8,
                "supplier_performance": 91.5,
                "batch_success_rate": 98.2,
                "audit_scores": 92.5
            },
            "trends": {
                "quality_score_trend": [92.1, 93.5, 94.2, 95.1, 94.8],
                "deviation_trend": [8, 5, 3, 2, 2],
                "supplier_score_trend": [89.2, 90.8, 91.5, 92.1, 91.5]
            },
            "top_issues": [
                {"issue": "Temperature deviations", "count": 12, "severity": "Medium"},
                {"issue": "Packaging defects", "count": 8, "severity": "Low"},
                {"issue": "Labeling errors", "count": 5, "severity": "High"}
            ],
            "certification_status": {
                "sqf": {"status": "Certified", "valid_until": "2025-12-31", "score": 92.5},
                "fsma": {"status": "Compliant", "last_review": "2024-11-15"},
                "organic": {"status": "Certified", "valid_until": "2025-06-30"} if "Organic" in INDUSTRY_CONFIGS[industry]["certifications"] else None
            }
        }

        return analytics
    except Exception as e:
        logger.error(f"❌ Error fetching quality analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@router.get("/ai-quality-insights")
async def get_ai_quality_insights(industry: str = Query("cheese_plant")):
    """Get AI-powered quality insights and recommendations"""
    try:
        insights = {
            "industry": industry,
            "predictive_alerts": [
                {
                    "type": "Temperature",
                    "severity": "High",
                    "prediction": "Pasteurizer P-001 likely to exceed temperature limits in 48 hours",
                    "confidence": 87,
                    "recommendation": "Schedule preventive maintenance on heat exchanger"
                },
                {
                    "type": "Microbial",
                    "severity": "Medium",
                    "prediction": "Increased risk of yeast contamination in aging rooms",
                    "confidence": 73,
                    "recommendation": "Enhance air filtration and increase monitoring frequency"
                }
            ],
            "quality_trends": {
                "improving": ["Supplier delivery times", "Packaging integrity"],
                "declining": ["Raw material consistency"],
                "stable": ["Microbial counts", "Allergen control"]
            },
            "optimization_opportunities": [
                {
                    "area": "Sanitation",
                    "opportunity": "Reduce cleaning time by 25% through optimized chemical concentrations",
                    "potential_savings": "$12,000/year",
                    "implementation_effort": "Medium"
                },
                {
                    "area": "Quality Testing",
                    "opportunity": "Implement automated microbial testing to reduce analysis time by 60%",
                    "potential_savings": "$8,500/year",
                    "implementation_effort": "High"
                }
            ],
            "risk_assessment": {
                "overall_risk_level": "Low",
                "critical_risks": ["Supplier raw material quality", "Equipment calibration drift"],
                "mitigation_actions": [
                    "Implement supplier quality scoring system",
                    "Establish automated calibration reminders"
                ]
            }
        }

        return insights
    except Exception as e:
        logger.error(f"❌ Error fetching AI quality insights: {e}")
        raise HTTPException(status_code=500, detail=f"AI insights error: {str(e)}")

@router.get("/iso-compliance-report")
async def get_iso_compliance_report(industry: str = Query("cheese_plant")):
    """Generate ISO 22000/FSSC 22000 compliance report"""
    try:
        compliance_report = {
            "industry": industry,
            "standard": "ISO 22000:2018 / FSSC 22000",
            "assessment_date": datetime.now().isoformat(),
            "overall_compliance": 94.2,
            "sections": {
                "context_of_organization": {
                    "compliance": 96.5,
                    "requirements": 12,
                    "met": 11,
                    "gaps": ["Stakeholder analysis documentation could be enhanced"]
                },
                "leadership": {
                    "compliance": 98.2,
                    "requirements": 8,
                    "met": 8,
                    "gaps": []
                },
                "planning": {
                    "compliance": 92.1,
                    "requirements": 15,
                    "met": 14,
                    "gaps": ["Risk treatment plan needs updating"]
                },
                "support": {
                    "compliance": 95.8,
                    "requirements": 10,
                    "met": 9,
                    "gaps": ["Training records retention policy clarification needed"]
                },
                "operation": {
                    "compliance": 91.5,
                    "requirements": 25,
                    "met": 22,
                    "gaps": ["HACCP plan verification frequency", "Prerequisite program monitoring"]
                },
                "performance_evaluation": {
                    "compliance": 93.7,
                    "requirements": 12,
                    "met": 11,
                    "gaps": ["Management review meeting frequency"]
                },
                "improvement": {
                    "compliance": 97.3,
                    "requirements": 6,
                    "met": 6,
                    "gaps": []
                }
            },
            "critical_non_conformities": 0,
            "major_non_conformities": 2,
            "minor_non_conformities": 5,
            "recommendations": [
                "Update HACCP verification schedule",
                "Enhance prerequisite program documentation",
                "Implement automated compliance monitoring"
            ],
            "next_audit_due": "2025-03-15"
        }

        return compliance_report
    except Exception as e:
        logger.error(f"❌ Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance report error: {str(e)}")

# Log successful router initialization
logger.info("✅ Food Processing Quality Management System (QMS) router loaded successfully")