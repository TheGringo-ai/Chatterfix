"""
🏭 Quality Management System (QMS) Router
Enterprise-grade quality control, supplier management, and ISO 9001 compliance
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
router = APIRouter(prefix="/quality", tags=["Quality Management"])
templates = Jinja2Templates(directory="app/templates")

# ===== PYDANTIC MODELS =====

class QualityInspection(BaseModel):
    inspection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inspection_date: datetime
    inspection_type: str = Field(..., description="Incoming, In-Process, Final, Audit")
    product_code: str
    batch_number: str
    inspector_name: str
    quality_score: float = Field(..., ge=0, le=100, description="Quality score 0-100%")
    defects_found: int = Field(default=0, ge=0)
    status: str = Field(..., description="Pass, Fail, Conditional")
    specifications_met: bool
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class NonConformanceRecord(BaseModel):
    ncr_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ncr_date: datetime
    severity: str = Field(..., description="Minor, Major, Critical")
    description: str
    affected_product: str
    quantity_affected: int
    root_cause: str
    disposition: str = Field(..., description="Use As-Is, Rework, Return, Scrap")
    cost_impact: float = Field(default=0.0, ge=0)
    responsible_person: str
    target_closure_date: datetime
    status: str = Field(..., description="Open, In Progress, Closed")
    capa_required: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)

class SupplierAudit(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_name: str
    audit_date: datetime
    audit_type: str = Field(..., description="Annual, Initial, Follow-up, Complaint")
    auditor_name: str
    quality_score: float = Field(..., ge=0, le=100)
    delivery_score: float = Field(..., ge=0, le=100)
    service_score: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    certification_status: str = Field(..., description="Approved, Conditional, Rejected")
    findings: List[str] = []
    recommendations: List[str] = []
    next_audit_date: datetime
    created_at: datetime = Field(default_factory=datetime.now)

class ProductTest(BaseModel):
    test_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_date: datetime
    test_type: str = Field(..., description="Performance, Durability, Safety, Environmental")
    product_code: str
    test_protocol: str
    test_criteria: str
    measured_value: float
    specification_min: float
    specification_max: float
    pass_status: bool
    test_engineer: str
    equipment_used: str
    environmental_conditions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# ===== MOCK DATA =====

def get_mock_quality_inspections():
    return [
        {
            "inspection_id": "QI-2024-001",
            "inspection_date": "2024-12-10T08:30:00",
            "inspection_type": "Incoming",
            "product_code": "WIDGET-A100",
            "batch_number": "B24120801",
            "inspector_name": "Alice Johnson",
            "quality_score": 98.5,
            "defects_found": 2,
            "status": "Pass",
            "specifications_met": True,
            "notes": "Minor surface scratches on 2 units"
        },
        {
            "inspection_id": "QI-2024-002", 
            "inspection_date": "2024-12-09T14:15:00",
            "inspection_type": "Final",
            "product_code": "ASSEMBLY-B200",
            "batch_number": "B24120902",
            "inspector_name": "Bob Smith",
            "quality_score": 95.2,
            "defects_found": 1,
            "status": "Conditional",
            "specifications_met": False,
            "notes": "Torque specification slightly below minimum"
        },
        {
            "inspection_id": "QI-2024-003",
            "inspection_date": "2024-12-08T10:45:00", 
            "inspection_type": "In-Process",
            "product_code": "COMPONENT-C300",
            "batch_number": "B24120803",
            "inspector_name": "Carol Davis",
            "quality_score": 99.8,
            "defects_found": 0,
            "status": "Pass",
            "specifications_met": True,
            "notes": "Excellent quality, no issues found"
        }
    ]

def get_mock_ncr_records():
    return [
        {
            "ncr_id": "NCR-2024-001",
            "ncr_date": "2024-12-09T11:30:00",
            "severity": "Major",
            "description": "Dimensional variance in shaft diameter exceeding tolerance",
            "affected_product": "SHAFT-D400",
            "quantity_affected": 25,
            "root_cause": "Tool wear causing drift in machining center",
            "disposition": "Rework",
            "cost_impact": 2500.00,
            "responsible_person": "Manufacturing Supervisor",
            "target_closure_date": "2024-12-15T17:00:00",
            "status": "In Progress",
            "capa_required": True
        },
        {
            "ncr_id": "NCR-2024-002",
            "ncr_date": "2024-12-07T15:20:00",
            "severity": "Minor", 
            "description": "Packaging label misalignment on finished goods",
            "affected_product": "PACKAGE-E500",
            "quantity_affected": 100,
            "root_cause": "Label applicator calibration drift",
            "disposition": "Use As-Is",
            "cost_impact": 150.00,
            "responsible_person": "Packaging Lead",
            "target_closure_date": "2024-12-12T17:00:00",
            "status": "Closed",
            "capa_required": False
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
async def quality_dashboard(request: Request):
    """Quality Management dashboard with comprehensive metrics"""
    try:
        # Calculate key metrics
        inspections = get_mock_quality_inspections()
        ncr_records = get_mock_ncr_records()
        supplier_audits = get_mock_supplier_audits()
        product_tests = get_mock_product_tests()
        
        # Quality metrics calculations
        avg_quality_score = sum(i["quality_score"] for i in inspections) / len(inspections) if inspections else 0
        open_ncrs = len([ncr for ncr in ncr_records if ncr["status"] != "Closed"])
        first_pass_yield = len([i for i in inspections if i["status"] == "Pass"]) / len(inspections) * 100 if inspections else 0
        avg_supplier_score = sum(s["overall_score"] for s in supplier_audits) / len(supplier_audits) if supplier_audits else 0
        
        # Cost of Quality (mock data)
        cost_of_quality = {
            "prevention": 15000,
            "appraisal": 25000, 
            "internal_failure": 8500,
            "external_failure": 3200
        }
        
        context = {
            "request": request,
            "avg_quality_score": round(avg_quality_score, 1),
            "open_ncrs": open_ncrs,
            "first_pass_yield": round(first_pass_yield, 1),
            "avg_supplier_score": round(avg_supplier_score, 1),
            "iso_compliance": 94.5,  # Mock ISO compliance percentage
            "cost_of_quality": cost_of_quality,
            "total_coq": sum(cost_of_quality.values()),
            "inspections": inspections[:5],  # Recent inspections
            "ncr_records": ncr_records,
            "supplier_audits": supplier_audits,
            "product_tests": product_tests[:3],  # Recent tests
            "spc_data": get_mock_spc_data()
        }
        
        logger.info("✅ Quality Management dashboard loaded successfully")
        return templates.TemplateResponse("quality_dashboard.html", context)
        
    except Exception as e:
        logger.error(f"❌ Error loading quality dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@router.get("/inspections")
async def get_quality_inspections(
    inspection_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """Get quality inspections with optional filtering"""
    try:
        inspections = get_mock_quality_inspections()
        
        # Apply filters if provided
        if inspection_type:
            inspections = [i for i in inspections if i["inspection_type"] == inspection_type]
            
        return {
            "inspections": inspections,
            "total": len(inspections),
            "summary": {
                "pass_rate": len([i for i in inspections if i["status"] == "Pass"]) / len(inspections) * 100 if inspections else 0,
                "avg_quality_score": sum(i["quality_score"] for i in inspections) / len(inspections) if inspections else 0,
                "total_defects": sum(i["defects_found"] for i in inspections)
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching quality inspections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inspections")
async def create_quality_inspection(inspection: QualityInspection):
    """Create a new quality inspection record"""
    try:
        # Here you would save to database
        logger.info(f"✅ Quality inspection created: {inspection.inspection_id}")
        return {
            "success": True,
            "message": "Quality inspection created successfully",
            "inspection_id": inspection.inspection_id
        }
    except Exception as e:
        logger.error(f"❌ Error creating quality inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ncr")
async def get_ncr_records(status: Optional[str] = Query(None)):
    """Get Non-Conformance Records with optional status filtering"""
    try:
        ncr_records = get_mock_ncr_records()
        
        if status:
            ncr_records = [ncr for ncr in ncr_records if ncr["status"] == status]
            
        return {
            "ncr_records": ncr_records,
            "total": len(ncr_records),
            "summary": {
                "total_cost_impact": sum(ncr["cost_impact"] for ncr in ncr_records),
                "open_records": len([ncr for ncr in ncr_records if ncr["status"] != "Closed"]),
                "capa_required": len([ncr for ncr in ncr_records if ncr["capa_required"]])
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching NCR records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ncr")
async def create_ncr_record(ncr: NonConformanceRecord):
    """Create a new Non-Conformance Record"""
    try:
        logger.info(f"✅ NCR record created: {ncr.ncr_id}")
        return {
            "success": True,
            "message": "NCR record created successfully", 
            "ncr_id": ncr.ncr_id
        }
    except Exception as e:
        logger.error(f"❌ Error creating NCR record: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supplier-audits")
async def get_supplier_audits(supplier_name: Optional[str] = Query(None)):
    """Get supplier audit records"""
    try:
        audits = get_mock_supplier_audits()
        
        if supplier_name:
            audits = [audit for audit in audits if supplier_name.lower() in audit["supplier_name"].lower()]
            
        return {
            "supplier_audits": audits,
            "total": len(audits),
            "summary": {
                "avg_overall_score": sum(a["overall_score"] for a in audits) / len(audits) if audits else 0,
                "approved_suppliers": len([a for a in audits if a["certification_status"] == "Approved"]),
                "conditional_suppliers": len([a for a in audits if a["certification_status"] == "Conditional"])
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching supplier audits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/supplier-audits")
async def create_supplier_audit(audit: SupplierAudit):
    """Create a new supplier audit record"""
    try:
        logger.info(f"✅ Supplier audit created: {audit.audit_id}")
        return {
            "success": True,
            "message": "Supplier audit created successfully",
            "audit_id": audit.audit_id
        }
    except Exception as e:
        logger.error(f"❌ Error creating supplier audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/product-tests")
async def get_product_tests(test_type: Optional[str] = Query(None)):
    """Get product test results"""
    try:
        tests = get_mock_product_tests()
        
        if test_type:
            tests = [test for test in tests if test["test_type"] == test_type]
            
        return {
            "product_tests": tests,
            "total": len(tests),
            "summary": {
                "pass_rate": len([t for t in tests if t["pass_status"]]) / len(tests) * 100 if tests else 0,
                "failed_tests": len([t for t in tests if not t["pass_status"]])
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching product tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/product-tests")
async def create_product_test(test: ProductTest):
    """Create a new product test record"""
    try:
        logger.info(f"✅ Product test created: {test.test_id}")
        return {
            "success": True,
            "message": "Product test created successfully",
            "test_id": test.test_id
        }
    except Exception as e:
        logger.error(f"❌ Error creating product test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spc-data")
async def get_spc_data():
    """Get Statistical Process Control data for charts"""
    try:
        return get_mock_spc_data()
    except Exception as e:
        logger.error(f"❌ Error fetching SPC data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def get_quality_documents():
    """Get quality management documents"""
    try:
        return {
            "documents": [
                {
                    "document_id": "QD-001",
                    "title": "Quality Manual",
                    "version": "3.2",
                    "approved_date": "2024-11-15T10:00:00",
                    "approved_by": "Quality Manager",
                    "next_review": "2025-11-15T10:00:00",
                    "status": "Active"
                },
                {
                    "document_id": "QD-002", 
                    "title": "Inspection Procedures",
                    "version": "2.1",
                    "approved_date": "2024-10-20T14:30:00",
                    "approved_by": "Senior Inspector",
                    "next_review": "2025-10-20T14:30:00",
                    "status": "Active"
                }
            ],
            "total": 2
        }
    except Exception as e:
        logger.error(f"❌ Error fetching quality documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_quality_analytics():
    """Get comprehensive quality analytics"""
    try:
        return {
            "quality_trends": {
                "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "first_pass_yield": [92, 94, 93, 96, 95, 97, 96, 98, 97, 95, 96, 97],
                "defect_rate": [8, 6, 7, 4, 5, 3, 4, 2, 3, 5, 4, 3]
            },
            "defect_analysis": {
                "categories": ["Dimensional", "Surface", "Assembly", "Packaging", "Electrical"],
                "counts": [15, 8, 12, 5, 3]
            },
            "cost_trends": {
                "prevention_costs": [12000, 13500, 14000, 15000],
                "appraisal_costs": [22000, 23500, 24000, 25000],
                "failure_costs": [8000, 7200, 6800, 5700]
            },
            "supplier_performance": {
                "suppliers": ["Precision Components", "FastTrack Logistics", "Quality Materials", "Expert Assembly"],
                "scores": [91.5, 90.3, 88.7, 92.1]
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching quality analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-quality-insights") 
async def get_ai_quality_insights():
    """Get AI-powered quality insights and predictions"""
    try:
        return {
            "insights": [
                {
                    "category": "Quality Prediction",
                    "insight": "Based on current trends, First Pass Yield is predicted to reach 98.5% next month",
                    "confidence": 92,
                    "recommendation": "Continue current quality processes and consider expanding best practices to other production lines"
                },
                {
                    "category": "Cost Optimization",
                    "insight": "Implementing predictive maintenance could reduce internal failure costs by 25%",
                    "confidence": 87,
                    "recommendation": "Invest in IoT sensors for critical equipment monitoring"
                },
                {
                    "category": "Supplier Risk",
                    "insight": "Quality Materials supplier shows declining performance trend", 
                    "confidence": 89,
                    "recommendation": "Schedule follow-up audit and discuss improvement action plan"
                },
                {
                    "category": "Process Improvement",
                    "insight": "Shaft diameter control could be optimized by adjusting tool change frequency",
                    "confidence": 94,
                    "recommendation": "Reduce tool change interval from 500 to 400 parts to improve Cpk from 1.28 to 1.45"
                }
            ],
            "predictions": {
                "next_month_yield": 98.2,
                "predicted_ncr_count": 2,
                "cost_reduction_opportunity": 12500
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching AI quality insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/iso-compliance-report")
async def get_iso_compliance_report():
    """Get ISO 9001 compliance reporting"""
    try:
        return {
            "overall_compliance": 94.5,
            "sections": [
                {"section": "4. Context of Organization", "compliance": 96, "status": "Compliant"},
                {"section": "5. Leadership", "compliance": 98, "status": "Compliant"},
                {"section": "6. Planning", "compliance": 92, "status": "Minor Gaps"},
                {"section": "7. Support", "compliance": 94, "status": "Compliant"},
                {"section": "8. Operation", "compliance": 93, "status": "Minor Gaps"}, 
                {"section": "9. Performance Evaluation", "compliance": 96, "status": "Compliant"},
                {"section": "10. Improvement", "compliance": 91, "status": "Minor Gaps"}
            ],
            "action_items": [
                "Update risk assessment documentation for planning section",
                "Complete remaining staff training on new procedures",
                "Implement additional performance metrics for operation monitoring"
            ],
            "next_audit": "2025-06-15T09:00:00"
        }
    except Exception as e:
        logger.error(f"❌ Error fetching ISO compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Log successful router initialization
logger.info("✅ Quality Management System (QMS) router loaded successfully")