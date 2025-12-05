from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
# # from app.core.database import get_db_connection
from app.core.db_adapter import get_db_adapter
from app.services.gemini_service import gemini_service
import shutil
import os
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)

# Ensure upload directory exists
UPLOAD_DIR = "app/static/uploads/imports"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Role-specific onboarding configurations
ROLE_ONBOARDING_CONFIG = {
    "technician": {
        "title": "Maintenance Technician Onboarding",
        "description": "Learn core maintenance skills, work order management, and safety protocols",
        "duration_days": 5,
        "modules": [
            {
                "id": "tech_safety",
                "title": "Safety Fundamentals",
                "type": "interactive",
                "duration_minutes": 45,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Personal Protective Equipment (PPE)", "type": "video_quiz"},
                        {"title": "Lockout/Tagout Procedures", "type": "interactive"},
                        {"title": "Hazard Recognition", "type": "scenario"},
                        {"title": "Emergency Procedures", "type": "checklist"}
                    ]
                }
            },
            {
                "id": "tech_work_orders",
                "title": "Work Order Management",
                "type": "hands_on",
                "duration_minutes": 60,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Using ChatterFix CMMS", "type": "guided_tour"},
                        {"title": "Scanning Asset Barcodes", "type": "practice"},
                        {"title": "Creating Work Orders", "type": "hands_on"},
                        {"title": "Parts Management", "type": "practice"},
                        {"title": "Documenting Completion", "type": "hands_on"}
                    ]
                }
            },
            {
                "id": "tech_preventive",
                "title": "Preventive Maintenance",
                "type": "practical",
                "duration_minutes": 90,
                "required": True
            },
            {
                "id": "tech_troubleshooting",
                "title": "Basic Troubleshooting",
                "type": "scenario",
                "duration_minutes": 75,
                "required": False
            }
        ]
    },
    "planner": {
        "title": "Maintenance Planner Onboarding",
        "description": "Master comprehensive maintenance planning, PM automation, scheduling, and resource optimization",
        "duration_days": 7,
        "modules": [
            {
                "id": "plan_fundamentals",
                "title": "Planning & Scheduling Fundamentals",
                "type": "interactive",
                "duration_minutes": 90,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Maintenance Planning Principles", "type": "theory"},
                        {"title": "Work Order Lifecycle Management", "type": "workflow"},
                        {"title": "Resource Allocation & Optimization", "type": "interactive"},
                        {"title": "Maintenance Strategy Development", "type": "case_study"}
                    ]
                }
            },
            {
                "id": "plan_preventive_maintenance",
                "title": "Preventive Maintenance Program Design",
                "type": "comprehensive",
                "duration_minutes": 120,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "PM Strategy & Methodology", "type": "theory"},
                        {"title": "Equipment Criticality Analysis", "type": "assessment"},
                        {"title": "Failure Mode Analysis (FMEA)", "type": "workshop"},
                        {"title": "PM Task Development", "type": "hands_on"},
                        {"title": "Frequency Optimization", "type": "calculation"},
                        {"title": "PM Performance Metrics", "type": "analytics"}
                    ]
                }
            },
            {
                "id": "plan_pm_automation",
                "title": "Automated PM Scheduling & Triggers",
                "type": "technical",
                "duration_minutes": 105,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Calendar-Based PM Setup", "type": "configuration"},
                        {"title": "Meter-Based PM Triggers", "type": "hands_on"},
                        {"title": "Condition-Based Triggers", "type": "advanced"},
                        {"title": "Multi-Criteria PM Scheduling", "type": "workshop"},
                        {"title": "PM Auto-Generation Rules", "type": "configuration"},
                        {"title": "Seasonal & Weather-Based PM", "type": "scenario"}
                    ]
                }
            },
            {
                "id": "plan_inspection_templates",
                "title": "Inspection Templates & Checklists",
                "type": "template_builder",
                "duration_minutes": 135,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Standard Inspection Templates", "type": "template"},
                        {"title": "Equipment-Specific Checklists", "type": "customization"},
                        {"title": "Safety Inspection Protocols", "type": "compliance"},
                        {"title": "Quality Control Templates", "type": "standards"},
                        {"title": "Route-Based Inspections", "type": "optimization"},
                        {"title": "Digital Forms & Mobile Checklists", "type": "technology"},
                        {"title": "Inspection Result Analytics", "type": "reporting"}
                    ]
                }
            },
            {
                "id": "plan_meter_readings",
                "title": "Meter Readings & Monitoring Systems",
                "type": "monitoring",
                "duration_minutes": 120,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Meter Types & Configuration", "type": "setup"},
                        {"title": "Hourly Reading Schedules", "type": "scheduling"},
                        {"title": "Gauge Reading Protocols", "type": "procedure"},
                        {"title": "Temperature & Pressure Monitoring", "type": "technical"},
                        {"title": "Vibration Analysis Setup", "type": "advanced"},
                        {"title": "Flow Rate & Usage Tracking", "type": "measurement"},
                        {"title": "Automated Data Collection", "type": "integration"},
                        {"title": "Threshold Alerts & Warnings", "type": "notification"},
                        {"title": "Trending & Predictive Analysis", "type": "analytics"}
                    ]
                }
            },
            {
                "id": "plan_advanced_scheduling",
                "title": "Advanced Scheduling & Resource Management",
                "type": "optimization",
                "duration_minutes": 150,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Multi-Craft Scheduling", "type": "coordination"},
                        {"title": "Equipment Availability Planning", "type": "logistics"},
                        {"title": "Shutdown & Outage Planning", "type": "project"},
                        {"title": "Emergency Response Scheduling", "type": "emergency"},
                        {"title": "Contractor & Vendor Coordination", "type": "external"},
                        {"title": "Resource Conflict Resolution", "type": "problem_solving"},
                        {"title": "Schedule Optimization Algorithms", "type": "advanced"},
                        {"title": "Capacity Planning & Forecasting", "type": "strategic"}
                    ]
                }
            },
            {
                "id": "plan_work_packages",
                "title": "Work Package Development & Job Planning",
                "type": "detailed_planning",
                "duration_minutes": 135,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Work Package Structure", "type": "framework"},
                        {"title": "Job Hazard Analysis (JHA)", "type": "safety"},
                        {"title": "Permit Requirements Planning", "type": "compliance"},
                        {"title": "Tool & Equipment Staging", "type": "logistics"},
                        {"title": "Materials & Parts Kitting", "type": "preparation"},
                        {"title": "Step-by-Step Procedures", "type": "documentation"},
                        {"title": "Quality Standards & Acceptance", "type": "quality"},
                        {"title": "Documentation & Closeout", "type": "completion"}
                    ]
                }
            },
            {
                "id": "plan_predictive_maintenance",
                "title": "Predictive Maintenance Planning",
                "type": "predictive",
                "duration_minutes": 120,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Condition Monitoring Strategy", "type": "strategy"},
                        {"title": "PdM Technology Integration", "type": "technology"},
                        {"title": "Data Collection Planning", "type": "data"},
                        {"title": "Analysis Frequency & Methods", "type": "methodology"},
                        {"title": "Trend Analysis & Baselines", "type": "analytics"},
                        {"title": "Failure Prediction Models", "type": "modeling"},
                        {"title": "PdM Work Order Triggers", "type": "automation"},
                        {"title": "ROI & Cost-Benefit Analysis", "type": "financial"}
                    ]
                }
            },
            {
                "id": "plan_reliability_engineering",
                "title": "Reliability Engineering & RCM",
                "type": "engineering",
                "duration_minutes": 180,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Reliability-Centered Maintenance (RCM)", "type": "methodology"},
                        {"title": "Asset Criticality Assessment", "type": "evaluation"},
                        {"title": "Root Cause Analysis (RCA)", "type": "investigation"},
                        {"title": "Failure Pattern Recognition", "type": "analysis"},
                        {"title": "Maintenance Task Optimization", "type": "improvement"},
                        {"title": "Reliability Metrics & KPIs", "type": "measurement"},
                        {"title": "MTBF/MTTR Optimization", "type": "performance"},
                        {"title": "Life Cycle Cost Analysis", "type": "economics"}
                    ]
                }
            },
            {
                "id": "plan_compliance_regulatory",
                "title": "Compliance & Regulatory Planning",
                "type": "compliance",
                "duration_minutes": 90,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Regulatory Requirement Mapping", "type": "compliance"},
                        {"title": "Audit Trail Documentation", "type": "documentation"},
                        {"title": "Environmental Compliance", "type": "environmental"},
                        {"title": "Safety Regulation Adherence", "type": "safety"},
                        {"title": "Industry Standards (ISO, API, etc.)", "type": "standards"},
                        {"title": "Certification Management", "type": "certification"}
                    ]
                }
            },
            {
                "id": "plan_kpis_analytics",
                "title": "Advanced KPIs & Analytics Dashboard",
                "type": "analytics",
                "duration_minutes": 105,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Planning Efficiency Metrics", "type": "metrics"},
                        {"title": "Schedule Compliance Tracking", "type": "compliance"},
                        {"title": "Backlog Management Analytics", "type": "management"},
                        {"title": "Resource Utilization Reports", "type": "utilization"},
                        {"title": "Cost per Work Order Analysis", "type": "financial"},
                        {"title": "Predictive Analytics & Forecasting", "type": "prediction"},
                        {"title": "Dashboard Design & Visualization", "type": "visualization"},
                        {"title": "Executive Reporting & Insights", "type": "reporting"}
                    ]
                }
            },
            {
                "id": "plan_integration_systems",
                "title": "System Integration & Workflow Automation",
                "type": "integration",
                "duration_minutes": 120,
                "required": False,
                "content": {
                    "sections": [
                        {"title": "ERP Integration Planning", "type": "integration"},
                        {"title": "IoT Sensor Data Integration", "type": "iot"},
                        {"title": "Mobile Workforce Management", "type": "mobile"},
                        {"title": "Workflow Automation Rules", "type": "automation"},
                        {"title": "API Configuration & Usage", "type": "technical"},
                        {"title": "Data Export & Reporting", "type": "data"},
                        {"title": "Third-Party Tool Integration", "type": "integration"}
                    ]
                }
            }
        ]
    },
    "parts_person": {
        "title": "Parts & Inventory Specialist Onboarding",
        "description": "Learn inventory management, procurement, and parts tracking",
        "duration_days": 3,
        "modules": [
            {
                "id": "parts_inventory",
                "title": "Inventory Management Fundamentals",
                "type": "interactive",
                "duration_minutes": 75,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Stock Level Management", "type": "practice"},
                        {"title": "ABC Classification", "type": "interactive"},
                        {"title": "Reorder Points", "type": "calculation"},
                        {"title": "Physical Inventory", "type": "hands_on"}
                    ]
                }
            },
            {
                "id": "parts_procurement",
                "title": "Procurement & Purchasing",
                "type": "workflow",
                "duration_minutes": 60,
                "required": True
            },
            {
                "id": "parts_tracking",
                "title": "Parts Tracking & Barcode Systems",
                "type": "hands_on",
                "duration_minutes": 45,
                "required": True
            },
            {
                "id": "parts_vendors",
                "title": "Vendor Management",
                "type": "scenarios",
                "duration_minutes": 50,
                "required": False
            }
        ]
    },
    "supervisor": {
        "title": "Maintenance Supervisor Onboarding",
        "description": "Leadership, team management, and operational oversight",
        "duration_days": 6,
        "modules": [
            {
                "id": "sup_leadership",
                "title": "Maintenance Leadership",
                "type": "interactive",
                "duration_minutes": 90,
                "required": True
            },
            {
                "id": "sup_team_mgmt",
                "title": "Team Management & Performance",
                "type": "case_study",
                "duration_minutes": 75,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Performance Coaching", "type": "scenario"},
                        {"title": "Resource Allocation", "type": "simulation"},
                        {"title": "Conflict Resolution", "type": "interactive"},
                        {"title": "Safety Leadership", "type": "checklist"}
                    ]
                }
            },
            {
                "id": "sup_analytics",
                "title": "Performance Analytics & Reporting",
                "type": "dashboard",
                "duration_minutes": 60,
                "required": True
            },
            {
                "id": "sup_compliance",
                "title": "Compliance & Standards",
                "type": "certification",
                "duration_minutes": 80,
                "required": True
            }
        ]
    },
    "manager": {
        "title": "Maintenance Manager Onboarding",
        "description": "Strategic planning, budget management, and organizational leadership",
        "duration_days": 7,
        "modules": [
            {
                "id": "mgr_strategy",
                "title": "Maintenance Strategy & Planning",
                "type": "strategic",
                "duration_minutes": 120,
                "required": True,
                "content": {
                    "sections": [
                        {"title": "Reliability Centered Maintenance", "type": "framework"},
                        {"title": "Asset Life Cycle Management", "type": "case_study"},
                        {"title": "Maintenance Strategy Development", "type": "workshop"},
                        {"title": "Technology Integration", "type": "roadmap"}
                    ]
                }
            },
            {
                "id": "mgr_budget",
                "title": "Budget Management & ROI",
                "type": "financial",
                "duration_minutes": 90,
                "required": True
            },
            {
                "id": "mgr_analytics",
                "title": "Advanced Analytics & KPIs",
                "type": "dashboard",
                "duration_minutes": 75,
                "required": True
            },
            {
                "id": "mgr_continuous_improvement",
                "title": "Continuous Improvement",
                "type": "methodology",
                "duration_minutes": 80,
                "required": True
            }
        ]
    }
}


@router.get("/", response_class=HTMLResponse)
async def onboarding_dashboard(request: Request):
    """Comprehensive onboarding dashboard with role selection"""
    return templates.TemplateResponse(
        "onboarding_dashboard.html", 
        {
            "request": request, 
            "roles": ROLE_ONBOARDING_CONFIG,
            "total_roles": len(ROLE_ONBOARDING_CONFIG)
        }
    )


@router.get("/role-selection", response_class=HTMLResponse)
async def role_selection(request: Request):
    """Role selection page for new users"""
    return templates.TemplateResponse(
        "role_selection.html",
        {
            "request": request,
            "roles": ROLE_ONBOARDING_CONFIG
        }
    )


@router.post("/start-onboarding")
async def start_role_onboarding(
    role: str = Form(...),
    user_name: str = Form(...),
    user_email: str = Form(...),
    department: str = Form(None),
    experience_level: str = Form("beginner")
):
    """Start role-specific onboarding for a user"""
    try:
        if role not in ROLE_ONBOARDING_CONFIG:
            return JSONResponse({"error": "Invalid role selected"}, status_code=400)
        
        # Create onboarding session
        db_adapter = get_db_adapter()
        
        # Create user onboarding record
        onboarding_data = {
            "user_name": user_name,
            "user_email": user_email,
            "role": role,
            "department": department,
            "experience_level": experience_level,
            "status": "active",
            "start_date": datetime.now().isoformat(),
            "expected_completion": (datetime.now() + timedelta(days=ROLE_ONBOARDING_CONFIG[role]["duration_days"])).isoformat(),
            "progress": 0,
            "current_module": 0
        }
        
        # In a real implementation, you'd save this to your database
        session_id = f"onboard_{user_email}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "role_config": ROLE_ONBOARDING_CONFIG[role],
            "redirect_url": f"/onboarding/role/{role}"
        })
        
    except Exception as e:
        logger.error(f"Error starting onboarding: {e}")
        return JSONResponse({"error": "Failed to start onboarding"}, status_code=500)


@router.get("/role/{role}", response_class=HTMLResponse)
async def role_onboarding_page(request: Request, role: str, user_id: int = None):
    """Role-specific onboarding interface"""
    if role not in ROLE_ONBOARDING_CONFIG:
        return RedirectResponse("/onboarding")
    
    config = ROLE_ONBOARDING_CONFIG[role]
    
    # Get user progress (simulated for demo)
    progress_data = {
        "completed_modules": 0,
        "total_modules": len(config["modules"]),
        "current_module": 0,
        "overall_progress": 0,
        "estimated_time_remaining": sum(m["duration_minutes"] for m in config["modules"]),
        "badges_earned": []
    }
    
    return templates.TemplateResponse(
        "role_onboarding.html",
        {
            "request": request,
            "role": role,
            "config": config,
            "progress": progress_data,
            "user_id": user_id or 1
        }
    )


@router.get("/module/{module_id}", response_class=HTMLResponse)
async def onboarding_module(request: Request, module_id: str, role: str = None):
    """Interactive training module"""
    if not role or role not in ROLE_ONBOARDING_CONFIG:
        return RedirectResponse("/onboarding")
    
    # Find the module in role config
    config = ROLE_ONBOARDING_CONFIG[role]
    module = next((m for m in config["modules"] if m["id"] == module_id), None)
    
    if not module:
        return RedirectResponse(f"/onboarding/role/{role}")
    
    # Generate AI-powered content if needed
    if "content" not in module and gemini_service.model:
        module["content"] = await generate_module_content(module, role)
    
    return templates.TemplateResponse(
        "training_module_interactive.html",
        {
            "request": request,
            "module": module,
            "role": role,
            "role_config": config
        }
    )


async def generate_module_content(module: Dict[str, Any], role: str) -> Dict[str, Any]:
    """Generate AI-powered training content"""
    try:
        prompt = f"""
        Create comprehensive training content for {module['title']} for a {role} role.
        Module type: {module['type']}
        Duration: {module['duration_minutes']} minutes
        
        Generate content with:
        1. Learning objectives (3-5 bullet points)
        2. Key concepts with explanations
        3. Interactive exercises or scenarios
        4. Assessment questions (5-10 questions)
        5. Practical tips and best practices
        6. Common mistakes to avoid
        
        Format as structured JSON with sections for each component.
        Make it engaging, practical, and role-specific.
        """
        
        response = await gemini_service.generate_response(prompt)
        
        # Parse and structure the response
        return {
            "sections": [
                {
                    "title": "Learning Objectives",
                    "type": "objectives",
                    "content": response[:200] + "..."  # Simplified for demo
                },
                {
                    "title": "Interactive Content",
                    "type": "interactive",
                    "content": "AI-generated interactive content would appear here"
                },
                {
                    "title": "Knowledge Check",
                    "type": "quiz",
                    "content": "AI-generated quiz questions"
                }
            ],
            "estimated_completion": module["duration_minutes"],
            "ai_generated": True
        }
        
    except Exception as e:
        logger.error(f"Error generating module content: {e}")
        return {
            "sections": [
                {
                    "title": module["title"],
                    "type": "default",
                    "content": f"Training content for {module['title']} is being prepared."
                }
            ]
        }


@router.post("/module/{module_id}/complete")
async def complete_module(
    module_id: str,
    role: str = Form(...),
    user_id: int = Form(...),
    score: float = Form(None),
    time_spent: int = Form(None),
    feedback: str = Form(None)
):
    """Mark module as completed and update progress"""
    try:
        # Update progress in database
        completion_data = {
            "user_id": user_id,
            "module_id": module_id,
            "role": role,
            "completed_at": datetime.now().isoformat(),
            "score": score,
            "time_spent_minutes": time_spent,
            "feedback": feedback
        }
        
        # Calculate badges/achievements
        badges = []
        if score and score >= 90:
            badges.append("Excellence")
        if time_spent and time_spent <= ROLE_ONBOARDING_CONFIG[role]["modules"][0]["duration_minutes"] * 0.8:
            badges.append("Efficiency")
        
        # Determine next module
        config = ROLE_ONBOARDING_CONFIG[role]
        current_index = next((i for i, m in enumerate(config["modules"]) if m["id"] == module_id), 0)
        next_module = config["modules"][current_index + 1] if current_index + 1 < len(config["modules"]) else None
        
        return JSONResponse({
            "success": True,
            "badges_earned": badges,
            "next_module": next_module["id"] if next_module else None,
            "progress_percent": ((current_index + 1) / len(config["modules"])) * 100,
            "completion_message": f"Great job completing {config['modules'][current_index]['title']}!"
        })
        
    except Exception as e:
        logger.error(f"Error completing module: {e}")
        return JSONResponse({"error": "Failed to update progress"}, status_code=500)


@router.get("/progress/{user_id}")
async def get_onboarding_progress(user_id: int, role: str = None):
    """Get detailed onboarding progress for user"""
    try:
        # In real implementation, fetch from database
        if not role:
            role = "technician"  # Default for demo
            
        config = ROLE_ONBOARDING_CONFIG.get(role, {})
        
        progress = {
            "user_id": user_id,
            "role": role,
            "started_date": datetime.now().isoformat(),
            "modules": [
                {
                    "id": module["id"],
                    "title": module["title"],
                    "type": module["type"],
                    "duration_minutes": module["duration_minutes"],
                    "required": module["required"],
                    "status": "not_started",  # not_started, in_progress, completed
                    "score": None,
                    "completion_date": None
                }
                for module in config.get("modules", [])
            ],
            "overall_progress": 0,
            "badges_earned": [],
            "estimated_completion": datetime.now() + timedelta(days=config.get("duration_days", 5)),
            "time_spent_total": 0
        }
        
        return JSONResponse(progress)
        
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        return JSONResponse({"error": "Failed to get progress"}, status_code=500)


@router.get("/certificate/{user_id}/{role}")
async def generate_certificate(user_id: int, role: str):
    """Generate completion certificate"""
    if role not in ROLE_ONBOARDING_CONFIG:
        return JSONResponse({"error": "Invalid role"}, status_code=400)
    
    config = ROLE_ONBOARDING_CONFIG[role]
    
    certificate_data = {
        "user_id": user_id,
        "role": role,
        "program_title": config["title"],
        "completion_date": datetime.now().strftime("%B %d, %Y"),
        "total_hours": sum(m["duration_minutes"] for m in config["modules"]) / 60,
        "modules_completed": len(config["modules"]),
        "certificate_id": f"CERT-{role.upper()}-{user_id}-{datetime.now().strftime('%Y%m%d')}"
    }
    
    return JSONResponse({
        "success": True,
        "certificate": certificate_data,
        "download_url": f"/onboarding/certificate/{user_id}/{role}/download"
    })


@router.get("/template/{type}")
async def get_template(type: str):
    """Download a CSV template for the specified type"""
    if type == "assets":
        df = pd.DataFrame(
            columns=[
                "name",
                "description",
                "asset_tag",
                "serial_number",
                "model",
                "manufacturer",
                "location",
                "department",
                "status",
                "criticality",
            ]
        )
        filename = "assets_template.csv"
    elif type == "parts":
        df = pd.DataFrame(
            columns=[
                "name",
                "description",
                "part_number",
                "category",
                "current_stock",
                "minimum_stock",
                "location",
                "unit_cost",
            ]
        )
        filename = "parts_template.csv"
    elif type == "work_orders":
        df = pd.DataFrame(
            columns=["title", "description", "priority", "assigned_to", "due_date"]
        )
        filename = "work_orders_template.csv"
    else:
        return HTMLResponse("Invalid template type", status_code=400)

    file_path = os.path.join(UPLOAD_DIR, filename)
    df.to_csv(file_path, index=False)
    return FileResponse(file_path, filename=filename)


@router.post("/import/{type}")
async def import_data(type: str, file: UploadFile = File(...)):
    """Import data from CSV or Excel"""
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        return HTMLResponse(
            "Invalid file format. Please upload CSV or Excel.", status_code=400
        )

    # Save file temporarily
    file_path = os.path.join(
        UPLOAD_DIR, f"{type}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    )
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read file
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        return HTMLResponse(f"Error reading file: {str(e)}", status_code=400)

    conn = get_db_connection()

    try:
        if type == "assets":
            # Map columns and insert
            for _, row in df.iterrows():
                conn.execute(
                    """
                    INSERT INTO assets (name, description, asset_tag, serial_number, model, manufacturer, location, department, status, criticality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row.get("name"),
                        row.get("description", ""),
                        row.get("asset_tag", ""),
                        row.get("serial_number", ""),
                        row.get("model", ""),
                        row.get("manufacturer", ""),
                        row.get("location", ""),
                        row.get("department", ""),
                        row.get("status", "Active"),
                        row.get("criticality", "Medium"),
                    ),
                )

        elif type == "parts":
            for _, row in df.iterrows():
                conn.execute(
                    """
                    INSERT INTO parts (name, description, part_number, category, current_stock, minimum_stock, location, unit_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row.get("name"),
                        row.get("description", ""),
                        row.get("part_number", ""),
                        row.get("category", "General"),
                        row.get("current_stock", 0),
                        row.get("minimum_stock", 5),
                        row.get("location", ""),
                        row.get("unit_cost", 0.0),
                    ),
                )

        elif type == "work_orders":
            for _, row in df.iterrows():
                conn.execute(
                    """
                    INSERT INTO work_orders (title, description, priority, assigned_to, due_date)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        row.get("title"),
                        row.get("description", ""),
                        row.get("priority", "Medium"),
                        row.get("assigned_to", ""),
                        row.get("due_date", ""),
                    ),
                )

        conn.commit()
        message = f"Successfully imported {len(df)} records into {type}."

    except Exception as e:
        conn.rollback()
        message = f"Error importing data: {str(e)}"
    finally:
        conn.close()

    return RedirectResponse(url=f"/onboarding?message={message}", status_code=303)
