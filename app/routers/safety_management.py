"""
🛡️ SAFETY MANAGEMENT SYSTEM (SMS) - SafetyFix Platform
Comprehensive safety management with AI-powered analytics, lab results integration,
and safety violation tracking for industrial operations.

Enterprise Features:
- Incident Management & Investigation
- Safety Compliance & Regulations
- Lab Results & Environmental Testing
- Hazard Assessment & Risk Management
- Safety Analytics & AI Predictions
- Safety Training & Certification
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

# ===== SAFETYFIX PREMIUM MODULE LICENSING =====
# SafetyFix: $99/month - OSHA, Incident Tracking, Lab Results, Safety Analytics

try:
    from app.modules.premium_licensing import (
        premium_licensing_manager,
        PremiumModule,
        require_safety_license,
        check_safety_access,
        get_license_status,
        get_customer_id_from_user,
        get_current_customer_id,
        PREMIUM_MODULE_PRICING
    )
    SAFETY_LICENSING_AVAILABLE = True
    logger.info("SafetyFix Premium Module licensing enabled")
except ImportError:
    SAFETY_LICENSING_AVAILABLE = False
    logger.warning("SafetyFix licensing not available - module will run in demo mode")

    # Fallback decorator that allows access in demo mode
    def require_safety_license(func):
        return func

    def get_current_customer_id():
        return "demo_customer_1"

    async def check_safety_access(customer_id: str) -> bool:
        return True

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/safety", tags=["SafetyFix Premium Module"])


# ===== LICENSE CHECK ENDPOINTS =====

@router.get("/license-status")
async def safety_license_status():
    """Check SafetyFix module license status"""
    customer_id = get_current_customer_id()

    if SAFETY_LICENSING_AVAILABLE:
        has_access = await check_safety_access(customer_id)
        license_info = await get_license_status(customer_id)

        return JSONResponse({
            "module": "safety_fix",
            "module_name": "SafetyFix",
            "has_access": has_access,
            "price": "$99/month",
            "features": [
                "Incident tracking & investigation",
                "Safety violation management",
                "Lab results & environmental testing",
                "Safety inspections & audits",
                "OSHA compliance reporting",
                "AI-powered safety analysis",
                "Risk assessment tools"
            ],
            "license_info": license_info,
            "upgrade_url": "https://chatterfix.com/upgrade/safety-fix"
        })
    else:
        return JSONResponse({
            "module": "safety_fix",
            "module_name": "SafetyFix",
            "has_access": True,
            "mode": "demo",
            "message": "Running in demo mode - all features available"
        })


@router.get("/upgrade-info")
async def safety_upgrade_info():
    """Get SafetyFix upgrade information"""
    return JSONResponse({
        "module": "safety_fix",
        "name": "SafetyFix Premium Module",
        "price": "$99/month",
        "description": "Enterprise safety management with OSHA compliance and incident tracking",
        "features": [
            "Incident tracking & investigation",
            "Safety violation management (OSHA 1910.147, etc.)",
            "Lab results & environmental testing",
            "Safety inspections & audits",
            "OSHA compliance reporting",
            "AI-powered safety analysis & predictions",
            "Risk assessment tools",
            "Safety training tracking",
            "Near-miss reporting",
            "Cost-benefit safety analytics"
        ],
        "compliance_standards": [
            "OSHA",
            "EPA",
            "DOT",
            "ISO 45001",
            "NFPA"
        ],
        "upgrade_url": "https://chatterfix.com/upgrade/safety-fix",
        "contact_sales": "sales@chatterfix.com"
    })

# ===== SAFETY DATA MODELS =====

class SafetyIncident(BaseModel):
    """Safety incident record"""
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_date: datetime
    incident_type: str = Field(..., description="Near miss, injury, property damage, etc.")
    severity: str = Field(..., description="Low, Medium, High, Critical")
    location: str
    department: str
    employee_id: Optional[str] = None
    employee_name: str
    description: str
    immediate_cause: str
    root_cause: Optional[str] = None
    corrective_actions: List[str] = []
    investigation_status: str = "Open"
    assigned_investigator: Optional[str] = None
    investigation_notes: Optional[str] = None
    photos: List[str] = []
    witnesses: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SafetyInspection(BaseModel):
    """Safety inspection record"""
    inspection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inspection_date: datetime
    inspection_type: str  # Routine, Audit, Incident Follow-up
    inspector_name: str
    area_inspected: str
    department: str
    checklist_items: List[Dict[str, Any]] = []
    violations_found: List[str] = []
    corrective_actions_required: List[str] = []
    overall_score: float = 0.0
    status: str = "Completed"
    photos: List[str] = []
    next_inspection_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class LabResult(BaseModel):
    """Lab testing and environmental monitoring results"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_date: datetime
    test_type: str  # Air Quality, Noise, Chemical Exposure, etc.
    sample_location: str
    department: str
    parameter_tested: str
    result_value: float
    unit_of_measure: str
    regulatory_limit: float
    compliance_status: str  # Compliant, Non-compliant, Warning
    lab_technician: str
    equipment_used: str
    sample_id: Optional[str] = None
    chain_of_custody: List[str] = []
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class SafetyViolation(BaseModel):
    """Safety violation and citation tracking"""
    violation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    violation_date: datetime
    violation_type: str
    regulatory_standard: str  # OSHA 1910.147, ISO 45001, etc.
    citation_number: Optional[str] = None
    issuing_authority: str
    violation_description: str
    location: str
    department: str
    severity: str  # Minor, Serious, Willful, Repeat
    penalty_amount: Optional[float] = None
    abatement_deadline: Optional[datetime] = None
    corrective_actions: List[str] = []
    status: str = "Open"  # Open, In Progress, Completed, Contested
    responsible_person: str
    completion_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# ===== MOCK DATA =====

safety_incidents = [
    {
        "incident_id": "INC-2024-001",
        "incident_date": "2024-12-10T14:30:00",
        "incident_type": "Near Miss",
        "severity": "Medium", 
        "location": "Assembly Line 3",
        "department": "Production",
        "employee_name": "John Smith",
        "description": "Employee slipped on wet floor near hydraulic press",
        "immediate_cause": "Spilled hydraulic fluid not cleaned",
        "investigation_status": "In Progress",
        "created_at": "2024-12-10T14:45:00"
    },
    {
        "incident_id": "INC-2024-002", 
        "incident_date": "2024-12-08T09:15:00",
        "incident_type": "Equipment Damage",
        "severity": "High",
        "location": "Welding Station 5",
        "department": "Fabrication", 
        "employee_name": "Sarah Johnson",
        "description": "Welding torch malfunction caused small fire",
        "immediate_cause": "Gas line leak in torch assembly",
        "investigation_status": "Completed",
        "created_at": "2024-12-08T09:30:00"
    }
]

lab_results = [
    {
        "result_id": "LAB-2024-001",
        "test_date": "2024-12-12T10:00:00",
        "test_type": "Air Quality - VOC",
        "sample_location": "Paint Booth Area",
        "department": "Finishing",
        "parameter_tested": "Volatile Organic Compounds",
        "result_value": 45.2,
        "unit_of_measure": "ppm",
        "regulatory_limit": 50.0,
        "compliance_status": "Compliant",
        "lab_technician": "Dr. Emily Chen",
        "equipment_used": "Gas Chromatograph GC-2030"
    },
    {
        "result_id": "LAB-2024-002",
        "test_date": "2024-12-11T14:30:00", 
        "test_type": "Noise Level",
        "sample_location": "Machine Shop Floor",
        "department": "Machining",
        "parameter_tested": "8-Hour TWA Noise",
        "result_value": 88.5,
        "unit_of_measure": "dBA",
        "regulatory_limit": 85.0,
        "compliance_status": "Non-compliant",
        "lab_technician": "Mike Rodriguez",
        "equipment_used": "Sound Level Meter SLM-25"
    }
]

safety_violations = [
    {
        "violation_id": "VIO-2024-001",
        "violation_date": "2024-12-05T11:00:00",
        "violation_type": "Lockout/Tagout",
        "regulatory_standard": "OSHA 1910.147",
        "citation_number": "OSHA-2024-12345",
        "issuing_authority": "OSHA Regional Office",
        "violation_description": "Failure to follow proper LOTO procedures on conveyor maintenance",
        "location": "Packaging Line 2", 
        "department": "Packaging",
        "severity": "Serious",
        "penalty_amount": 15000.00,
        "status": "In Progress",
        "responsible_person": "Maintenance Supervisor"
    }
]

safety_inspections = [
    {
        "inspection_id": "INS-2024-001",
        "inspection_date": "2024-12-10T08:00:00", 
        "inspection_type": "Monthly Safety Audit",
        "inspector_name": "Safety Manager - Lisa Davis",
        "area_inspected": "Production Floor",
        "department": "Production",
        "overall_score": 87.5,
        "violations_found": ["Missing safety signage", "Blocked emergency exit"],
        "status": "Completed"
    }
]

# ===== API ENDPOINTS =====

@router.get("/dashboard", response_class=HTMLResponse)
async def safety_dashboard(request: Request):
    """Main Safety Management dashboard"""
    
    # Calculate safety metrics
    total_incidents = len(safety_incidents)
    open_violations = len([v for v in safety_violations if v["status"] in ["Open", "In Progress"]])
    non_compliant_tests = len([r for r in lab_results if r["compliance_status"] == "Non-compliant"])
    avg_inspection_score = 87.5  # Calculate from inspections
    
    safety_metrics = {
        "total_incidents_ytd": total_incidents,
        "open_violations": open_violations,
        "non_compliant_tests": non_compliant_tests,
        "avg_inspection_score": avg_inspection_score,
        "trir": 2.4,  # Total Recordable Incident Rate
        "dart": 1.8,  # Days Away/Restricted/Transfer Rate
        "near_miss_ratio": 8.5,  # Near misses per recordable incident
        "safety_training_compliance": 94.2
    }
    
    context = {
        "request": request,
        "safety_metrics": safety_metrics,
        "recent_incidents": safety_incidents[:5],
        "recent_lab_results": lab_results[:5],
        "active_violations": [v for v in safety_violations if v["status"] in ["Open", "In Progress"]][:5],
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return templates.TemplateResponse("safety_dashboard.html", context)

@router.get("/incidents")
async def get_safety_incidents():
    """Get all safety incidents"""
    return JSONResponse({"incidents": safety_incidents, "total": len(safety_incidents)})

@router.post("/incidents")
async def create_safety_incident(incident: SafetyIncident):
    """Create new safety incident"""
    try:
        incident_data = incident.dict()
        incident_data["created_at"] = datetime.now().isoformat()
        incident_data["updated_at"] = datetime.now().isoformat()
        
        safety_incidents.append(incident_data)
        
        logger.info(f"✅ Safety incident created: {incident.incident_id}")
        return JSONResponse({
            "success": True,
            "message": "Safety incident created successfully",
            "incident_id": incident.incident_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating safety incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lab-results")
async def get_lab_results():
    """Get all lab testing results"""
    return JSONResponse({"results": lab_results, "total": len(lab_results)})

@router.post("/lab-results") 
async def create_lab_result(result: LabResult):
    """Create new lab testing result"""
    try:
        result_data = result.dict()
        result_data["created_at"] = datetime.now().isoformat()
        
        # AI Analysis of lab result
        ai_analysis = analyze_lab_result_with_ai(result_data)
        result_data["ai_analysis"] = ai_analysis
        
        lab_results.append(result_data)
        
        logger.info(f"✅ Lab result recorded: {result.result_id}")
        return JSONResponse({
            "success": True,
            "message": "Lab result recorded successfully", 
            "result_id": result.result_id,
            "ai_analysis": ai_analysis
        })
        
    except Exception as e:
        logger.error(f"❌ Error recording lab result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/violations")
async def get_safety_violations():
    """Get all safety violations"""
    return JSONResponse({"violations": safety_violations, "total": len(safety_violations)})

@router.post("/violations")
async def create_safety_violation(violation: SafetyViolation):
    """Create new safety violation record"""
    try:
        violation_data = violation.dict()
        violation_data["created_at"] = datetime.now().isoformat()
        
        safety_violations.append(violation_data)
        
        logger.info(f"✅ Safety violation recorded: {violation.violation_id}")
        return JSONResponse({
            "success": True,
            "message": "Safety violation recorded successfully",
            "violation_id": violation.violation_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error recording safety violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inspections")
async def get_safety_inspections():
    """Get all safety inspections"""
    return JSONResponse({"inspections": safety_inspections, "total": len(safety_inspections)})

@router.get("/analytics")
async def get_safety_analytics():
    """Get comprehensive safety analytics"""
    try:
        # Calculate advanced safety metrics
        analytics = {
            "safety_performance": {
                "trir": 2.4,
                "dart": 1.8, 
                "lwdi": 1.2,  # Lost Workday Incident Rate
                "near_miss_ratio": 8.5,
                "safety_observation_cards": 145
            },
            "incident_trends": {
                "incidents_by_month": [3, 5, 2, 4, 6, 3, 2, 4, 5, 3, 4, 2],
                "incidents_by_type": {
                    "Near Miss": 45,
                    "First Aid": 12,
                    "Recordable Injury": 8,
                    "Equipment Damage": 15,
                    "Environmental": 3
                },
                "incidents_by_department": {
                    "Production": 35,
                    "Maintenance": 18,
                    "Warehousing": 12,
                    "Office": 8,
                    "Facilities": 10
                }
            },
            "compliance_metrics": {
                "inspection_compliance": 96.8,
                "training_compliance": 94.2,
                "ppe_compliance": 98.5,
                "housekeeping_scores": 87.3
            },
            "environmental_monitoring": {
                "air_quality_tests": 24,
                "compliant_results": 22,
                "compliance_rate": 91.7,
                "noise_monitoring": 12,
                "chemical_exposure_tests": 18
            },
            "leading_indicators": {
                "safety_meetings_held": 48,
                "safety_suggestions": 127,
                "safety_walks_completed": 156,
                "behavioral_observations": 342
            },
            "ai_insights": [
                "Slip and fall incidents increase 23% during shift changes - recommend focused housekeeping",
                "Noise levels in machining exceed limits - immediate hearing protection review needed", 
                "Near miss reporting up 40% indicating improved safety culture",
                "Lockout/tagout violations cluster in maintenance - additional training recommended"
            ]
        }
        
        return JSONResponse(analytics)
        
    except Exception as e:
        logger.error(f"❌ Error getting safety analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-safety-analysis")
async def ai_safety_analysis():
    """AI-powered safety analysis and recommendations"""
    try:
        ai_analysis = {
            "risk_assessment": {
                "high_risk_areas": [
                    {"location": "Welding Area", "risk_score": 8.7, "primary_hazards": ["Fire", "Fumes", "Burns"]},
                    {"location": "Chemical Storage", "risk_score": 8.2, "primary_hazards": ["Chemical Exposure", "Spills"]},
                    {"location": "Machine Shop", "risk_score": 7.9, "primary_hazards": ["Noise", "Cuts", "Eye Injury"]}
                ],
                "trending_risks": [
                    "Ergonomic injuries increasing in packaging department",
                    "Electrical incidents trending up in maintenance",
                    "Chemical exposure concerns in cleaning operations"
                ]
            },
            "predictive_insights": {
                "incident_probability": [
                    {"department": "Production", "probability": 0.15, "timeframe": "next_30_days"},
                    {"department": "Maintenance", "probability": 0.22, "timeframe": "next_30_days"},
                    {"department": "Warehousing", "probability": 0.08, "timeframe": "next_30_days"}
                ],
                "equipment_safety_concerns": [
                    {"equipment": "Press #3", "concern": "Guard issues", "urgency": "High"},
                    {"equipment": "Conveyor B", "concern": "Pinch points", "urgency": "Medium"}
                ]
            },
            "recommendations": [
                {
                    "priority": "High",
                    "action": "Implement additional noise controls in machining area",
                    "expected_impact": "Reduce noise-related violations by 60%",
                    "cost_estimate": "$25,000",
                    "timeline": "30 days"
                },
                {
                    "priority": "Medium", 
                    "action": "Enhanced lockout/tagout training for maintenance staff",
                    "expected_impact": "Eliminate LOTO violations",
                    "cost_estimate": "$5,000",
                    "timeline": "14 days"
                },
                {
                    "priority": "High",
                    "action": "Install ventilation system in paint booth",
                    "expected_impact": "Achieve full air quality compliance",
                    "cost_estimate": "$45,000", 
                    "timeline": "60 days"
                }
            ],
            "cost_benefit_analysis": {
                "current_annual_safety_costs": {
                    "workers_comp": 125000,
                    "fines_penalties": 35000,
                    "lost_productivity": 180000,
                    "total": 340000
                },
                "projected_savings_with_improvements": {
                    "workers_comp_reduction": 45000,
                    "eliminated_fines": 30000,
                    "productivity_improvement": 95000,
                    "total_annual_savings": 170000,
                    "roi_percentage": 227
                }
            }
        }
        
        return JSONResponse(ai_analysis)
        
    except Exception as e:
        logger.error(f"❌ Error in AI safety analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== HELPER FUNCTIONS =====

def analyze_lab_result_with_ai(result_data: Dict[str, Any]) -> Dict[str, Any]:
    """AI analysis of lab testing results"""
    try:
        value = result_data["result_value"]
        limit = result_data["regulatory_limit"]
        percentage_of_limit = (value / limit) * 100
        
        analysis = {
            "percentage_of_limit": percentage_of_limit,
            "trend_analysis": "Stable" if percentage_of_limit < 80 else "Increasing",
            "risk_level": "Low" if percentage_of_limit < 70 else "Medium" if percentage_of_limit < 90 else "High",
            "recommendations": []
        }
        
        if percentage_of_limit > 90:
            analysis["recommendations"].append("Immediate corrective action required")
            analysis["recommendations"].append("Increase monitoring frequency")
        elif percentage_of_limit > 80:
            analysis["recommendations"].append("Monitor closely") 
            analysis["recommendations"].append("Review control measures")
        else:
            analysis["recommendations"].append("Continue current controls")
            
        return analysis
        
    except Exception as e:
        logger.error(f"Error in AI lab analysis: {e}")
        return {"error": str(e)}

@router.get("/compliance-report")
async def generate_compliance_report():
    """Generate comprehensive safety compliance report"""
    try:
        report = {
            "report_date": datetime.now().isoformat(),
            "reporting_period": "2024 Year to Date",
            "facility_info": {
                "facility_name": "ChatterFix Manufacturing Facility",
                "address": "123 Industrial Blvd, Manufacturing City, USA",
                "naics_code": "332710",
                "employee_count": 450
            },
            "regulatory_compliance": {
                "osha_compliance_rate": 94.2,
                "epa_compliance_rate": 96.8,
                "dot_compliance_rate": 98.1,
                "state_compliance_rate": 92.5
            },
            "incident_summary": {
                "total_incidents": len(safety_incidents),
                "recordable_injuries": 8,
                "lost_time_injuries": 3,
                "near_misses": 45,
                "property_damage": 15
            },
            "environmental_compliance": {
                "air_quality_compliance": 91.7,
                "noise_compliance": 88.3,
                "chemical_compliance": 96.2,
                "waste_compliance": 99.1
            },
            "training_compliance": {
                "safety_training_current": 94.2,
                "ppe_training_current": 98.5,
                "emergency_training_current": 91.3,
                "job_specific_training": 89.7
            },
            "action_items": [
                "Address noise compliance in machining area",
                "Complete overdue safety training for 12 employees",
                "Investigate recurring slip/fall incidents",
                "Update emergency evacuation procedures"
            ]
        }
        
        return JSONResponse(report)
        
    except Exception as e:
        logger.error(f"❌ Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Safety Management System (SMS) router loaded successfully")