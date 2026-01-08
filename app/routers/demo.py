import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

from app.routers.onboarding import ROLE_ONBOARDING_CONFIG
from app.services.demo_service import demo_service

logger = logging.getLogger(__name__)


def generate_manager_demo_data():
    """Generate realistic demo data for Manager Dashboard features"""

    # Demo technicians with realistic performance data
    demo_technicians = [
        {
            "id": 1,
            "name": "Mike Rodriguez",
            "role": "Senior Technician",
            "completion_rate": 94,
            "avg_response_time": "12 min",
            "certifications": ["HVAC", "Electrical", "Plumbing"],
            "status": "Active",
            "last_login": "2 hours ago",
            "work_orders_today": 8,
            "efficiency_score": 92,
            "customer_rating": 4.8,
        },
        {
            "id": 2,
            "name": "Sarah Chen",
            "role": "Lead Technician",
            "completion_rate": 98,
            "avg_response_time": "8 min",
            "certifications": ["HVAC", "Refrigeration", "Safety"],
            "status": "Active",
            "last_login": "30 min ago",
            "work_orders_today": 12,
            "efficiency_score": 96,
            "customer_rating": 4.9,
        },
        {
            "id": 3,
            "name": "James Wilson",
            "role": "Technician",
            "completion_rate": 87,
            "avg_response_time": "15 min",
            "certifications": ["Basic HVAC"],
            "status": "Training",
            "last_login": "1 hour ago",
            "work_orders_today": 5,
            "efficiency_score": 85,
            "customer_rating": 4.6,
        },
        {
            "id": 4,
            "name": "Maria Garcia",
            "role": "Senior Technician",
            "completion_rate": 91,
            "avg_response_time": "11 min",
            "certifications": ["Electrical", "Plumbing", "Safety"],
            "status": "Active",
            "last_login": "45 min ago",
            "work_orders_today": 9,
            "efficiency_score": 89,
            "customer_rating": 4.7,
        },
    ]

    # Demo assets with performance metrics
    demo_assets = [
        {
            "id": "HVAC-001",
            "name": "Main HVAC Unit - Building A",
            "type": "HVAC System",
            "health_score": 85,
            "status": "Operational",
            "last_maintenance": "2024-11-15",
            "next_maintenance": "2024-12-15",
            "cost_this_month": 1250.00,
            "efficiency": 92,
            "uptime": 99.2,
            "critical_alerts": 0,
        },
        {
            "id": "PUMP-002",
            "name": "Water Pump System",
            "type": "Pump",
            "health_score": 72,
            "status": "Needs Attention",
            "last_maintenance": "2024-10-20",
            "next_maintenance": "2024-12-08",
            "cost_this_month": 890.00,
            "efficiency": 78,
            "uptime": 95.5,
            "critical_alerts": 2,
        },
        {
            "id": "GEN-003",
            "name": "Backup Generator",
            "type": "Generator",
            "health_score": 96,
            "status": "Excellent",
            "last_maintenance": "2024-11-20",
            "next_maintenance": "2025-01-20",
            "cost_this_month": 450.00,
            "efficiency": 98,
            "uptime": 100.0,
            "critical_alerts": 0,
        },
    ]

    # Demo inventory with stock levels
    demo_inventory = [
        {
            "id": "PART-001",
            "name": "HVAC Air Filters",
            "category": "Filters",
            "current_stock": 45,
            "min_stock": 20,
            "max_stock": 100,
            "unit_cost": 25.50,
            "supplier": "FilterPro Inc",
            "status": "In Stock",
            "last_ordered": "2024-11-20",
            "monthly_usage": 18,
        },
        {
            "id": "PART-002",
            "name": "Water Pump Seals",
            "category": "Seals & Gaskets",
            "current_stock": 8,
            "min_stock": 15,
            "max_stock": 50,
            "unit_cost": 85.00,
            "supplier": "AquaParts Ltd",
            "status": "Low Stock",
            "last_ordered": "2024-10-15",
            "monthly_usage": 12,
        },
        {
            "id": "PART-003",
            "name": "Electrical Contactors",
            "category": "Electrical",
            "current_stock": 0,
            "min_stock": 10,
            "max_stock": 40,
            "unit_cost": 120.00,
            "supplier": "ElectroSupply Co",
            "status": "Out of Stock",
            "last_ordered": "2024-11-01",
            "monthly_usage": 8,
        },
    ]

    # Recent activities for activity feed
    recent_activities = [
        {
            "type": "work_order",
            "message": "Work Order #WO-2024-1156 completed by Mike Rodriguez",
            "timestamp": datetime.now() - timedelta(minutes=15),
            "priority": "normal",
        },
        {
            "type": "alert",
            "message": "Critical Alert: Water Pump System pressure warning",
            "timestamp": datetime.now() - timedelta(minutes=22),
            "priority": "high",
        },
        {
            "type": "inventory",
            "message": "Low stock alert: Water Pump Seals (8 remaining)",
            "timestamp": datetime.now() - timedelta(minutes=35),
            "priority": "medium",
        },
        {
            "type": "maintenance",
            "message": "Preventive maintenance scheduled for Backup Generator",
            "timestamp": datetime.now() - timedelta(hours=1),
            "priority": "normal",
        },
        {
            "type": "technician",
            "message": "Sarah Chen achieved 98% completion rate this month",
            "timestamp": datetime.now() - timedelta(hours=2),
            "priority": "good",
        },
    ]

    # Overview statistics
    overview_stats = {
        "total_technicians": len(demo_technicians),
        "active_work_orders": 24,
        "assets_monitored": len(demo_assets),
        "inventory_items": len(demo_inventory),
        "avg_response_time": "11.5 min",
        "system_uptime": 98.7,
        "monthly_costs": 15750.00,
        "efficiency_score": 91.2,
    }

    return {
        "technicians": demo_technicians,
        "assets": demo_assets,
        "inventory": demo_inventory,
        "activities": recent_activities,
        "overview_stats": overview_stats,
    }


router = APIRouter()
# Disable template caching to ensure fresh templates are always loaded
env = Environment(
    loader=FileSystemLoader("app/templates"),
    auto_reload=True,
    cache_size=0,
    autoescape=True,
)
templates = Jinja2Templates(env=env)


# =============================================================================
# ONE-CLICK DEMO API ENDPOINTS
# =============================================================================


@router.post("/api/v1/demo/start")
async def start_demo_session(request: Request, response: Response):
    """
    Create a new isolated demo organization with seed data.

    Returns session cookie and redirect URL for one-click demo access.
    No signup required.

    Rate limited to 5 demos per IP per hour.
    """
    # Get client IP for rate limiting (optional)
    client_ip = request.client.host if request.client else None

    logger.info(f"Starting demo session for IP: {client_ip}")

    try:
        result = await demo_service.create_demo_session(client_ip=client_ip)

        if not result.get("success"):
            return JSONResponse(
                {"error": result.get("error", "Failed to create demo session")},
                status_code=500,
            )

        # Set session cookie for demo user
        json_response = JSONResponse({
            "success": True,
            "org_id": result["org_id"],
            "redirect_url": result["redirect_url"],
            "expires_at": result["expires_at"],
            "message": "Demo workspace created! You have 2 hours to explore.",
        })

        # Set demo session cookie (same format as regular sessions)
        json_response.set_cookie(
            key="session_token",
            value=result["session_token"],
            path="/",
            httponly=True,
            samesite="lax",
            max_age=7200,  # 2 hours
        )

        logger.info(f"Demo session created: org={result['org_id']}")

        return json_response

    except Exception as e:
        logger.error(f"Error creating demo session: {e}")
        return JSONResponse(
            {"error": "Failed to create demo workspace. Please try again."},
            status_code=500,
        )


@router.post("/api/v1/demo/cleanup")
async def cleanup_expired_demos(request: Request):
    """
    Clean up expired demo organizations.

    Should be called periodically (e.g., daily via Cloud Scheduler).
    Protected by:
    - X-Admin-Secret header (for manual invocation)
    - OIDC token from Cloud Scheduler (Authorization header)
    """
    import os

    # Check for admin secret (manual invocation)
    admin_secret = request.headers.get("X-Admin-Secret")
    expected_secret = os.environ.get("ADMIN_SECRET", "")

    # Check for OIDC token from Cloud Scheduler
    auth_header = request.headers.get("Authorization", "")
    has_oidc_token = auth_header.startswith("Bearer ")

    # Check for Cloud Scheduler user agent
    user_agent = request.headers.get("User-Agent", "")
    is_cloud_scheduler = "Google-Cloud-Scheduler" in user_agent

    # Allow if:
    # 1. Valid admin secret, OR
    # 2. OIDC token from Cloud Scheduler
    is_authorized = (
        (expected_secret and admin_secret == expected_secret) or
        (has_oidc_token and is_cloud_scheduler)
    )

    if not is_authorized:
        logger.warning(f"Unauthorized cleanup attempt from {request.client.host}")
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        logger.info("Starting scheduled demo cleanup...")
        result = await demo_service.cleanup_expired_demos()
        logger.info(f"Demo cleanup completed: {result}")
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error cleaning up demos: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/v1/demo/status")
async def get_demo_status(request: Request):
    """
    Check if current session is a demo session.

    Returns demo org info if in demo mode, otherwise indicates not a demo.
    """
    from app.auth import get_current_user_from_cookie

    try:
        current_user = await get_current_user_from_cookie(request)

        if current_user and hasattr(current_user, 'is_demo') and current_user.is_demo:
            return JSONResponse({
                "is_demo": True,
                "org_id": current_user.organization_id,
                "org_name": current_user.organization_name,
                "message": "You are using a demo workspace. Data will be deleted after 2 hours.",
            })

        return JSONResponse({
            "is_demo": False,
            "message": "Not a demo session",
        })

    except Exception:
        return JSONResponse({
            "is_demo": False,
            "message": "Unable to determine session status",
        })


# ==================== DEMO DATA API ENDPOINTS ====================
# These endpoints provide demo data for unauthenticated users


@router.get("/api/demo/parts")
async def get_demo_parts():
    """Return demo parts data for unauthenticated users."""
    from app.routers.inventory import DEMO_PARTS
    return JSONResponse({
        "parts": DEMO_PARTS,
        "is_demo": True,
        "message": "Demo parts data - sign up for your own inventory"
    })


@router.get("/api/demo/assets")
async def get_demo_assets():
    """Return demo assets data for unauthenticated users."""
    return JSONResponse({
        "assets": DEMO_ASSETS,
        "is_demo": True,
        "message": "Demo assets data - sign up for your own asset management"
    })


@router.get("/api/demo/work-orders")
async def get_demo_work_orders():
    """Return demo work orders data for unauthenticated users."""
    return JSONResponse({
        "work_orders": DEMO_WORK_ORDERS,
        "is_demo": True,
        "message": "Demo work orders - sign up to create your own"
    })


@router.get("/api/demo/team")
async def get_demo_team():
    """Return demo team data for unauthenticated users."""
    return JSONResponse({
        "team": DEMO_TEAM,
        "is_demo": True,
        "message": "Demo team data - sign up to manage your own team"
    })


@router.get("/api/demo/stats")
async def get_demo_stats():
    """Return demo statistics for unauthenticated users."""
    return JSONResponse({
        "stats": DEMO_STATS,
        "is_demo": True,
        "message": "Demo statistics - sign up to track your own metrics"
    })


# Sample data for demo mode
DEMO_ASSETS = [
    {
        "id": 1,
        "name": "Production Line A",
        "category": "Manufacturing Equipment",
        "location": "Factory Floor - Zone 1",
        "status": "Operational",
        "condition": "Good",
        "condition_rating": 8,
        "last_maintenance": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() + timedelta(days=75)).strftime("%Y-%m-%d"),
        "criticality": "High",
    },
    {
        "id": 2,
        "name": "HVAC Unit B-2",
        "category": "HVAC",
        "location": "Building B - Roof",
        "status": "Maintenance Required",
        "condition": "Fair",
        "condition_rating": 5,
        "last_maintenance": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "criticality": "Medium",
    },
    {
        "id": 3,
        "name": "Forklift FL-001",
        "category": "Material Handling",
        "location": "Warehouse",
        "status": "Operational",
        "condition": "Excellent",
        "condition_rating": 9,
        "last_maintenance": (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() + timedelta(days=82)).strftime("%Y-%m-%d"),
        "criticality": "Medium",
    },
    {
        "id": 4,
        "name": "Compressor C-5",
        "category": "Compressed Air",
        "location": "Utility Room",
        "status": "Down",
        "condition": "Poor",
        "condition_rating": 2,
        "last_maintenance": (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d"),
        "next_maintenance": "Overdue",
        "criticality": "Critical",
    },
]

DEMO_WORK_ORDERS = [
    {
        "id": "WO-2024-001",
        "title": "Replace HVAC filters in Building B",
        "asset": "HVAC Unit B-2",
        "priority": "High",
        "status": "In Progress",
        "assigned_to": "Mike Johnson",
        "created_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "description": "Quarterly filter replacement for optimal air quality and system efficiency.",
    },
    {
        "id": "WO-2024-002",
        "title": "Compressor oil change and inspection",
        "asset": "Compressor C-5",
        "priority": "Critical",
        "status": "Overdue",
        "assigned_to": "Sarah Chen",
        "created_date": (datetime.now() - timedelta(days=10)).strftime(
            "%Y-%m-%d %H:%M"
        ),
        "due_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "description": "Emergency maintenance required. Compressor showing signs of oil contamination.",
    },
    {
        "id": "WO-2024-003",
        "title": "Production line calibration",
        "asset": "Production Line A",
        "priority": "Medium",
        "status": "Scheduled",
        "assigned_to": "Alex Rodriguez",
        "created_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "description": "Monthly calibration to ensure product quality standards.",
    },
]

DEMO_TEAM = [
    {
        "id": 1,
        "full_name": "Mike Johnson",
        "username": "mike.johnson@company.com",
        "role": "Senior Technician",
        "department": "Maintenance",
        "skills": ["HVAC", "Electrical", "Plumbing"],
        "certifications": ["EPA 608", "OSHA 30", "First Aid/CPR"],
        "active_work_orders": 3,
        "completed_orders": 47,
        "status": "Available",
        "contact": "mike.johnson@company.com",
        "phone": "(555) 123-4567",
        "start_date": "2021-03-15",
        "employee_id": "EMP-001",
        "hourly_rate": 32.50,
        "shift": "Day Shift (7am-3pm)",
        "supervisor": "Sarah Chen",
        "notes": "Excellent troubleshooting skills. Lead tech for HVAC systems.",
    },
    {
        "id": 2,
        "full_name": "Sarah Chen",
        "username": "sarah.chen@company.com",
        "role": "Maintenance Manager",
        "department": "Operations",
        "skills": ["Project Management", "Mechanical", "Safety", "Team Leadership"],
        "certifications": ["PMP", "CMRP", "OSHA 30", "Six Sigma Green Belt"],
        "active_work_orders": 5,
        "completed_orders": 128,
        "status": "Busy",
        "contact": "sarah.chen@company.com",
        "phone": "(555) 234-5678",
        "start_date": "2018-06-01",
        "employee_id": "EMP-002",
        "hourly_rate": 55.00,
        "shift": "Day Shift (7am-3pm)",
        "supervisor": "Director of Operations",
        "notes": "Department head. Responsible for all maintenance operations.",
    },
    {
        "id": 3,
        "full_name": "Alex Rodriguez",
        "username": "alex.rodriguez@company.com",
        "role": "Maintenance Technician",
        "department": "Maintenance",
        "skills": ["Mechanical", "Pneumatics", "Preventive Maintenance"],
        "certifications": ["OSHA 10", "Forklift Operator"],
        "active_work_orders": 2,
        "completed_orders": 23,
        "status": "Available",
        "contact": "alex.rodriguez@company.com",
        "phone": "(555) 345-6789",
        "start_date": "2023-01-10",
        "employee_id": "EMP-003",
        "hourly_rate": 26.00,
        "shift": "Swing Shift (3pm-11pm)",
        "supervisor": "Mike Johnson",
        "notes": "New hire showing great progress. Strong mechanical aptitude.",
    },
    {
        "id": 4,
        "full_name": "Maria Garcia",
        "username": "maria.garcia@company.com",
        "role": "Maintenance Technician",
        "department": "Maintenance",
        "skills": ["Electrical", "PLC Programming", "Instrumentation"],
        "certifications": ["Journeyman Electrician", "OSHA 30", "Arc Flash Safety"],
        "active_work_orders": 4,
        "completed_orders": 67,
        "status": "On Call",
        "contact": "maria.garcia@company.com",
        "phone": "(555) 456-7890",
        "start_date": "2020-09-20",
        "employee_id": "EMP-004",
        "hourly_rate": 35.00,
        "shift": "Night Shift (11pm-7am)",
        "supervisor": "Sarah Chen",
        "notes": "Electrical specialist. Primary contact for PLC troubleshooting.",
    },
    {
        "id": 5,
        "full_name": "James Wilson",
        "username": "james.wilson@company.com",
        "role": "Maintenance Planner",
        "department": "Planning",
        "skills": ["Work Order Management", "Scheduling", "Inventory Control", "CMMS"],
        "certifications": ["CMRP", "CPIM"],
        "active_work_orders": 0,
        "completed_orders": 0,
        "status": "Available",
        "contact": "james.wilson@company.com",
        "phone": "(555) 567-8901",
        "start_date": "2022-04-05",
        "employee_id": "EMP-005",
        "hourly_rate": 42.00,
        "shift": "Day Shift (7am-3pm)",
        "supervisor": "Sarah Chen",
        "notes": "Responsible for PM scheduling and parts ordering.",
    },
]

DEMO_STATS = {
    "total_assets": len(DEMO_ASSETS),
    "operational_assets": len([a for a in DEMO_ASSETS if a["status"] == "Operational"]),
    "assets_needing_maintenance": len(
        [a for a in DEMO_ASSETS if a["status"] in ["Maintenance Required", "Down"]]
    ),
    "total_work_orders": len(DEMO_WORK_ORDERS),
    "open_work_orders": len(
        [w for w in DEMO_WORK_ORDERS if w["status"] in ["In Progress", "Scheduled"]]
    ),
    "overdue_work_orders": len(
        [w for w in DEMO_WORK_ORDERS if w["status"] == "Overdue"]
    ),
    "team_members": len(DEMO_TEAM),
    "average_completion_time": "4.2 days",
}

# Demo user context for templates
DEMO_USER = {
    "uid": "demo-user-001",
    "id": "demo-user-001",
    "username": "demo_visitor",
    "email": "demo@chatterfix.com",
    "full_name": "Demo Visitor",
    "role": "technician",
}


# ==================== MAIN DEMO ENTRY POINTS ====================


@router.get("/demo", response_class=RedirectResponse)
async def demo_home(request: Request):
    """Demo home - redirect to unified dashboard (handles demo mode automatically)"""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/demo/", response_class=RedirectResponse)
async def demo_home_slash(request: Request):
    """Demo home with trailing slash - redirect to unified dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/demo/dashboard", response_class=RedirectResponse)
async def demo_dashboard_redirect(request: Request):
    """Redirect to unified dashboard (handles demo mode automatically)"""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/demo/assets", response_class=RedirectResponse)
async def demo_assets_redirect(request: Request):
    """Redirect to unified assets (handles demo mode automatically)"""
    return RedirectResponse(url="/assets", status_code=302)


@router.get("/demo/work-orders", response_class=RedirectResponse)
async def demo_work_orders_redirect(request: Request):
    """Redirect to unified work orders (handles demo mode automatically)"""
    return RedirectResponse(url="/work-orders", status_code=302)


@router.get("/demo/team", response_class=RedirectResponse)
async def demo_team_redirect(request: Request):
    """Redirect to unified team (handles demo mode automatically)"""
    return RedirectResponse(url="/team", status_code=302)


# NOTE: The original /demo/dashboard, /demo/assets, /demo/work-orders, /demo/team
# handlers have been removed. These routes now redirect to the unified routes
# which handle both demo and authenticated modes automatically.


@router.get("/demo/planner", response_class=HTMLResponse)
async def demo_planner(request: Request):
    """Demo planner page - comprehensive enterprise scheduler interface"""
    return templates.TemplateResponse(
        "planner_dashboard.html",
        {
            "request": request,
            "is_demo": True,
            "advanced_mode": True,
            "page_title": "Advanced Enterprise Scheduler",
        },
    )


@router.get("/demo/planner-debug")
async def debug_planner_template():
    """Debug endpoint to check template content"""
    import os

    template_path = "app/templates/planner_dashboard.html"
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            content = f.read()
            return {
                "template_exists": True,
                "has_advanced_scheduler": "Advanced Enterprise Scheduler" in content,
                "has_create_job": "Create Job" in content,
                "has_schedule_pm": "Schedule PM" in content,
                "has_fullcalendar": "FullCalendar" in content,
                "content_length": len(content),
                "first_100_chars": content[:100],
            }
    else:
        return {"template_exists": False}


@router.get("/demo/purchasing", response_class=HTMLResponse)
async def demo_purchasing(request: Request):
    """Demo purchasing page - ALWAYS uses mock data for security (never real customer data)"""
    # SECURITY: Demo mode ONLY uses mock data to prevent data leakage between organizations
    vendors = [
        {
            "id": "vendor_1",
            "name": "Grundfos Pumps",
            "contact": "sales@grundfos.com",
            "phone": "(555) 123-4567",
        },
        {
            "id": "vendor_2",
            "name": "Schneider Electric",
            "contact": "orders@schneider.com",
            "phone": "(555) 234-5678",
        },
        {
            "id": "vendor_3",
            "name": "ABB Motors",
            "contact": "support@abb.com",
            "phone": "(555) 345-6789",
        },
    ]

    parts = [
        {
            "id": "part_1",
            "name": "CR1 Centrifugal Pump",
            "sku": "GRU-CR1-001",
            "price": 1250.00,
            "stock": 15,
            "vendor": "Grundfos Pumps",
        },
        {
            "id": "part_2",
            "name": "Variable Frequency Drive",
            "sku": "SCH-VFD-200",
            "price": 850.00,
            "stock": 8,
            "vendor": "Schneider Electric",
        },
        {
            "id": "part_3",
            "name": "3-Phase Motor 15HP",
            "sku": "ABB-MOT-15HP",
            "price": 950.00,
            "stock": 12,
            "vendor": "ABB Motors",
        },
        {
            "id": "part_4",
            "name": "PLC Control Module",
            "sku": "SIE-PLC-300",
            "price": 650.00,
            "stock": 20,
            "vendor": "Siemens Controls",
        },
    ]

    return templates.TemplateResponse(
        "purchasing_pos.html",
        {"request": request, "vendors": vendors, "parts": parts, "is_demo": True},
    )


@router.get("/demo/training", response_class=HTMLResponse)
async def demo_training(request: Request):
    """Demo training page with sample data"""
    try:
        demo_courses = [
            {
                "id": 1,
                "title": "Pump Station Maintenance Manual",
                "description": "Complete technician training based on Grundfos pump system manuals - maintenance procedures, troubleshooting guides, and safety protocols",
                "duration": "3 hours",
                "difficulty": "Intermediate",
                "completed_by": 8,
                "total_enrolled": 12,
                "type": "equipment_manual",
            },
            {
                "id": 2,
                "title": "HVAC System Troubleshooting SOP",
                "description": "Standard Operating Procedures for diagnosing and repairing HVAC systems - step-by-step guides with AI assistance",
                "duration": "4 hours",
                "difficulty": "Intermediate",
                "completed_by": 15,
                "total_enrolled": 18,
                "type": "sop",
            },
            {
                "id": 3,
                "title": "Electrical Safety & Lockout/Tagout Procedures",
                "description": "Essential safety training for electrical work - OSHA compliance, LOTO procedures, and emergency response",
                "duration": "2 hours",
                "difficulty": "Beginner",
                "completed_by": 22,
                "total_enrolled": 22,
                "type": "safety_sop",
            },
            {
                "id": 4,
                "title": "Conveyor Belt Maintenance Manual",
                "description": "Technical training derived from manufacturer manuals - belt tensioning, bearing replacement, and preventive maintenance schedules",
                "duration": "5 hours",
                "difficulty": "Advanced",
                "completed_by": 4,
                "total_enrolled": 8,
                "type": "equipment_manual",
            },
            {
                "id": 5,
                "title": "AI-Assisted Diagnostics Training",
                "description": "Learn to use ChatterFix's AI assistant for equipment diagnostics, fault analysis, and maintenance recommendations",
                "duration": "3 hours",
                "difficulty": "Intermediate",
                "completed_by": 12,
                "total_enrolled": 16,
                "type": "ai_assisted",
            },
            {
                "id": 6,
                "title": "Compressor Maintenance SOP",
                "description": "Standard procedures for air compressor maintenance - oil changes, filter replacement, and performance monitoring",
                "duration": "2 hours",
                "difficulty": "Beginner",
                "completed_by": 18,
                "total_enrolled": 20,
                "type": "sop",
            },
        ]

        # Map demo courses to the structure expected by the template
        available_modules = [
            {
                "id": c["id"],
                "title": c["title"],
                "description": c["description"],
                "difficulty_level": c["difficulty"],
                "estimated_duration_minutes": int(c["duration"].split()[0]) * 60,
                "ai_generated": True if c["type"] == "ai_assisted" else False,
                "content_type": c["type"],
            }
            for c in demo_courses[3:]  # Show last 3 as available
        ]

        # Sample user training - show technician has some assigned training
        my_training = [
            {
                "training_module_id": 1,
                "title": "Pump Station Maintenance Manual",
                "description": "Complete technician training based on Grundfos pump system manuals",
                "status": "in_progress",
                "estimated_duration_minutes": 180,
                "score": None,
            },
            {
                "training_module_id": 2,
                "title": "HVAC System Troubleshooting SOP",
                "description": "Standard Operating Procedures for diagnosing and repairing HVAC systems",
                "status": "assigned",
                "estimated_duration_minutes": 240,
                "score": None,
            },
            {
                "training_module_id": 3,
                "title": "Electrical Safety & Lockout/Tagout Procedures",
                "description": "Essential safety training for electrical work - OSHA compliance",
                "status": "completed",
                "estimated_duration_minutes": 120,
                "score": 95,
            },
        ]

        return templates.TemplateResponse(
            "training_center.html",
            {
                "request": request,
                "available_modules": available_modules,
                "my_training": my_training,
                "stats": {
                    "total_assigned": 3,
                    "completed": 1,
                    "in_progress": 1,
                    "avg_score": 95.0,
                },
                "is_demo": True,
                "user_id": "demo_user",
            },
        )
    except Exception:
        import traceback

        return HTMLResponse(
            content=f"<h1>Error</h1><pre>{traceback.format_exc()}</pre>",
            status_code=500,
        )


@router.get("/demo/training/modules/{module_id}", response_class=HTMLResponse)
async def demo_training_module_detail(request: Request, module_id: str):
    """Demo training module detail page - interactive technician experience"""
    try:
        # Demo training modules data
        demo_modules = {
            "1": {
                "id": "1",
                "title": "Pump Station Maintenance Manual",
                "description": "Complete technician training based on Grundfos pump system manuals - maintenance procedures, troubleshooting guides, and safety protocols",
                "difficulty_level": "Intermediate",
                "estimated_duration_minutes": 180,
                "ai_generated": True,
                "content": {
                    "sections": [
                        {
                            "title": "Safety Procedures",
                            "content": "Essential safety protocols for pump maintenance operations.",
                            "type": "text",
                        },
                        {
                            "title": "Diagnostic Procedures",
                            "content": "Step-by-step diagnostic procedures for common pump issues.",
                            "type": "interactive",
                        },
                        {
                            "title": "Maintenance Tasks",
                            "content": "Regular maintenance procedures and schedules.",
                            "type": "hands_on",
                        },
                    ]
                },
            },
            "2": {
                "id": "2",
                "title": "HVAC System Troubleshooting SOP",
                "description": "Standard Operating Procedures for diagnosing and repairing HVAC systems - step-by-step guides with AI assistance",
                "difficulty_level": "Intermediate",
                "estimated_duration_minutes": 240,
                "ai_generated": True,
                "content": {
                    "sections": [
                        {
                            "title": "System Overview",
                            "content": "Understanding HVAC system components and operation principles.",
                            "type": "text",
                        },
                        {
                            "title": "Troubleshooting Guide",
                            "content": "Systematic approach to diagnosing HVAC problems.",
                            "type": "interactive",
                        },
                    ]
                },
            },
            "3": {
                "id": "3",
                "title": "Electrical Safety & Lockout/Tagout Procedures",
                "description": "Essential safety training for electrical work - OSHA compliance, LOTO procedures, and emergency response",
                "difficulty_level": "Beginner",
                "estimated_duration_minutes": 120,
                "ai_generated": False,
                "content": {
                    "sections": [
                        {
                            "title": "Electrical Safety Fundamentals",
                            "content": "Basic electrical safety principles and OSHA requirements.",
                            "type": "text",
                        },
                        {
                            "title": "Lockout/Tagout Procedures",
                            "content": "Step-by-step LOTO procedures for electrical systems.",
                            "type": "hands_on",
                        },
                    ]
                },
            },
        }

        module = demo_modules.get(module_id)
        if not module:
            return HTMLResponse(
                content=f"<h1>Training Module Not Found</h1><p>Module ID '{module_id}' not found in demo data.</p>",
                status_code=404,
            )

        return templates.TemplateResponse(
            "training_module_interactive.html",
            {
                "request": request,
                "module": module,
                "content": module["content"],
                "role": "technician",
                "role_config": {"title": "Technician Training"},
                "is_demo": True,
                "demo_banner": f"Demo: {module['title']} - Interactive training experience",
            },
        )

    except Exception:
        import traceback

        return HTMLResponse(
            content=f"<h1>Error Loading Training Module</h1><pre>{traceback.format_exc()}</pre>",
            status_code=500,
        )


@router.get("/demo/ar-mode", response_class=HTMLResponse)
async def demo_ar_mode(request: Request):
    """Demo AR mode page"""
    return templates.TemplateResponse(
        "ar/dashboard.html", {"request": request, "is_demo": True}
    )


@router.get("/demo/analytics", response_class=HTMLResponse)
async def demo_analytics(request: Request):
    """Demo analytics dashboard with predictive insights"""
    from datetime import datetime, timedelta

    # Generate sample predictions
    predictions = [
        {
            "asset_id": 2,
            "asset_name": "HVAC Unit B-2",
            "issue": "Filter clogging and reduced airflow",
            "days_until": 5,
            "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "confidence": 87,
            "severity": "warning",
            "recommendation": "Schedule filter replacement within 3 days to prevent system strain and maintain air quality",
        },
        {
            "asset_id": 4,
            "asset_name": "Compressor C-5",
            "issue": "Oil contamination and overheating risk",
            "days_until": 2,
            "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "confidence": 91,
            "severity": "critical",
            "recommendation": "Immediate oil change and cooling system inspection required to prevent catastrophic failure",
        },
        {
            "asset_id": 1,
            "asset_name": "Production Line A",
            "issue": "Belt wear detected",
            "days_until": 12,
            "date": (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),
            "confidence": 73,
            "severity": "warning",
            "recommendation": "Inspect drive belts and order replacements. Schedule maintenance during next planned downtime",
        },
        {
            "asset_id": 3,
            "asset_name": "Forklift FL-001",
            "issue": "Battery performance degradation",
            "days_until": 18,
            "date": (datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d"),
            "confidence": 65,
            "severity": "good",
            "recommendation": "Monitor battery health. Consider battery replacement in next quarter",
        },
    ]

    return templates.TemplateResponse(
        "analytics_dashboard.html",
        {
            "request": request,
            "predictions": predictions,
            "predictions_count": len(predictions),
            "accuracy": 89,
            "cost_savings": 24750,
            "prevented_failures": 12,
            "correct_predictions": 34,
            "early_warnings": 8,
            "total_predictions": 38,
            "downtime_hours": 156,
            "downtime_cost": 78000,
            "roi": 4.2,
            "is_demo": True,
        },
    )


@router.get("/demo/analytics/dashboard")
async def demo_analytics_dashboard_redirect():
    """Redirect to demo analytics - for URL consistency"""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/demo/analytics", status_code=302)


@router.get("/demo/diagnostics", response_class=HTMLResponse)
async def demo_diagnostics(request: Request):
    """Demo equipment diagnostics tool"""
    return templates.TemplateResponse(
        "diagnostics_tool.html",
        {
            "request": request,
            "assets": DEMO_ASSETS,
            "is_demo": True,
        },
    )


@router.get("/demo/inventory", response_class=HTMLResponse)
async def demo_inventory(request: Request):
    """Demo inventory page - ALWAYS uses mock data for security (never real customer data)"""
    # SECURITY: Demo mode ONLY uses mock data to prevent data leakage between organizations
    demo_parts = [
        {
            "id": 1,
            "part_number": "FLT-001",
            "name": "HVAC Air Filter",
            "quantity": 15,
            "reorder_point": 10,
            "cost": 12.50,
            "status": "In Stock",
        },
        {
            "id": 2,
            "part_number": "OIL-COMP",
            "name": "Compressor Oil 5W-30",
            "quantity": 3,
            "reorder_point": 5,
            "cost": 85.00,
            "status": "Low Stock",
        },
        {
            "id": 3,
            "part_number": "BRG-001",
            "name": "Ball Bearing 6205",
            "quantity": 25,
            "reorder_point": 10,
            "cost": 18.75,
            "status": "In Stock",
        },
        {
            "id": 4,
            "part_number": "BLT-002",
            "name": "Drive Belt A-68",
            "quantity": 8,
            "reorder_point": 5,
            "cost": 32.00,
            "status": "In Stock",
        },
        {
            "id": 5,
            "part_number": "SEN-TEMP",
            "name": "Temperature Sensor PT100",
            "quantity": 2,
            "reorder_point": 5,
            "cost": 145.00,
            "status": "Low Stock",
        },
    ]

    low_stock_count = len(
        [p for p in demo_parts if p.get("quantity", 0) <= p.get("reorder_point", 5)]
    )
    total_value = sum((p.get("quantity", 0) * p.get("cost", 0)) for p in demo_parts)

    return templates.TemplateResponse(
        "parts_catalog.html",
        {
            "request": request,
            "parts": demo_parts,
            "low_stock_count": low_stock_count,
            "total_value": total_value,
            "is_demo": True,
            "demo_mode": True,
            "current_user": {
                "uid": "demo",
                "role": "technician",
                "full_name": "Demo User",
            },
        },
    )


@router.get("/demo/reports", response_class=HTMLResponse)
async def demo_reports(request: Request):
    """Demo reports dashboard"""
    report_templates = [
        {
            "id": 1,
            "name": "Executive KPI Summary",
            "description": "High-level overview of key performance indicators",
            "category": "Executive",
            "frequency": "Weekly",
            "last_generated": "2 days ago",
        },
        {
            "id": 2,
            "name": "Maintenance Cost Analysis",
            "description": "Detailed breakdown of maintenance costs by asset and type",
            "category": "Financial",
            "frequency": "Monthly",
            "last_generated": "5 days ago",
        },
        {
            "id": 3,
            "name": "Asset Performance Report",
            "description": "Individual asset health, utilization, and maintenance history",
            "category": "Operations",
            "frequency": "Monthly",
            "last_generated": "1 week ago",
        },
        {
            "id": 4,
            "name": "Compliance Audit Report",
            "description": "PM compliance, safety certifications, and regulatory status",
            "category": "Compliance",
            "frequency": "Quarterly",
            "last_generated": "3 weeks ago",
        },
    ]

    return templates.TemplateResponse(
        "reports_dashboard.html",
        {
            "request": request,
            "report_templates": report_templates,
            "is_demo": True,
        },
    )


@router.get("/demo/onboarding", response_class=HTMLResponse)
async def demo_onboarding_dashboard(request: Request):
    """Demo onboarding dashboard with role selection"""
    return templates.TemplateResponse(
        "onboarding_dashboard.html",
        {
            "request": request,
            "roles": ROLE_ONBOARDING_CONFIG,
            "is_demo": True,
            "page_title": "Demo: Role-Based Onboarding",
            "demo_banner": "Experience our comprehensive training system - all features available in demo mode",
        },
    )


@router.get("/demo/onboarding/{role}", response_class=HTMLResponse)
async def demo_role_onboarding(request: Request, role: str):
    """Demo role-specific onboarding experience"""
    if role not in ROLE_ONBOARDING_CONFIG:
        return RedirectResponse(url="/demo/onboarding")

    role_config = ROLE_ONBOARDING_CONFIG[role]

    # Demo progress simulation - show some modules as completed for showcase
    demo_progress = {}
    if role == "planner":
        # Show planner has made some progress for demo purposes
        demo_progress = {
            "plan_fundamentals": {
                "status": "completed",
                "completion_date": "2025-11-28",
            },
            "plan_preventive_maintenance": {
                "status": "completed",
                "completion_date": "2025-11-29",
            },
            "plan_pm_automation": {"status": "in_progress", "progress": 65},
            "plan_inspection_templates": {"status": "pending"},
            "plan_meter_readings": {"status": "pending"},
        }
    elif role == "technician":
        demo_progress = {
            "tech_safety": {"status": "completed", "completion_date": "2025-11-25"},
            "tech_work_orders": {"status": "in_progress", "progress": 80},
        }

    return templates.TemplateResponse(
        "role_onboarding.html",
        {
            "request": request,
            "role": role,
            "role_config": role_config,
            "progress": demo_progress,
            "is_demo": True,
            "demo_banner": f"Demo: {role_config['title']} - Interactive training simulation",
            "completion_rate": 35 if role == "planner" else 25,
        },
    )


@router.get("/demo/onboarding/{role}/{module_id}", response_class=HTMLResponse)
async def demo_training_module(request: Request, role: str, module_id: str):
    """Demo individual training module experience"""
    if role not in ROLE_ONBOARDING_CONFIG:
        return RedirectResponse(url="/demo/onboarding")

    role_config = ROLE_ONBOARDING_CONFIG[role]
    module = None

    for mod in role_config["modules"]:
        if mod["id"] == module_id:
            module = mod
            break

    if not module:
        return RedirectResponse(url=f"/demo/onboarding/{role}")

    # Demo content simulation with realistic planner examples
    demo_content = {
        "current_section": 0,
        "total_sections": len(module.get("content", {}).get("sections", [])),
        "progress": 0,
        "interactive_elements": True,
    }

    if role == "planner":
        # Add specific demo content for planner modules
        if module_id == "plan_pm_automation":
            demo_content["demo_data"] = {
                "pm_schedules": 15,
                "automated_triggers": 8,
                "meter_readings": 45,
                "active_routes": 12,
            }
        elif module_id == "plan_meter_readings":
            demo_content["demo_data"] = {
                "meter_points": 127,
                "daily_readings": 340,
                "alerts_configured": 23,
                "trending_charts": 8,
            }

    return templates.TemplateResponse(
        "training_module_interactive.html",
        {
            "request": request,
            "role": role,
            "role_config": role_config,
            "module": module,
            "content": demo_content,
            "is_demo": True,
            "demo_banner": f"Demo: {module['title']} - Full interactive experience available",
        },
    )


# Manager Dashboard Demo Routes
@router.get("/manager", response_class=HTMLResponse)
async def demo_manager_dashboard(request: Request):
    """Interactive Demo Manager Dashboard - Auto-play demonstration of all features"""
    demo_data = generate_manager_demo_data()

    return templates.TemplateResponse(
        "demo_manager_dashboard.html",
        {
            "request": request,
            "demo_data": demo_data,
            "demo_data_json": json.dumps(demo_data, default=str),
            "is_demo": True,
            "auto_play": True,
        },
    )


@router.get("/manager/technicians", response_class=HTMLResponse)
async def demo_manager_technicians(request: Request):
    """Demo Manager Technician Management with Interactive Features"""
    demo_data = generate_manager_demo_data()

    return templates.TemplateResponse(
        "demo_manager_technicians.html",
        {
            "request": request,
            "technicians": demo_data["technicians"],
            "demo_data_json": json.dumps(demo_data, default=str),
            "is_demo": True,
            "auto_play": True,
        },
    )


@router.get("/manager/performance", response_class=HTMLResponse)
async def demo_manager_performance(request: Request):
    """Demo Manager Performance Analytics with Live Charts"""
    demo_data = generate_manager_demo_data()

    return templates.TemplateResponse(
        "demo_manager_performance.html",
        {
            "request": request,
            "technicians": demo_data["technicians"],
            "demo_data_json": json.dumps(demo_data, default=str),
            "is_demo": True,
            "auto_play": True,
        },
    )


@router.get("/manager/assets", response_class=HTMLResponse)
async def demo_manager_assets(request: Request):
    """Demo Manager Asset Management with Health Monitoring"""
    demo_data = generate_manager_demo_data()

    return templates.TemplateResponse(
        "demo_manager_assets.html",
        {
            "request": request,
            "assets": demo_data["assets"],
            "demo_data_json": json.dumps(demo_data, default=str),
            "is_demo": True,
            "auto_play": True,
        },
    )


@router.get("/manager/inventory", response_class=HTMLResponse)
async def demo_manager_inventory(request: Request):
    """Demo Manager Inventory Management with Stock Alerts"""
    demo_data = generate_manager_demo_data()

    return templates.TemplateResponse(
        "demo_manager_inventory.html",
        {
            "request": request,
            "inventory": demo_data["inventory"],
            "demo_data_json": json.dumps(demo_data, default=str),
            "is_demo": True,
            "auto_play": True,
        },
    )


# =============================================================================
# DEMO ANALYTICS API ENDPOINTS (No Authentication Required)
# =============================================================================


@router.get("/demo/analytics/kpi/summary")
async def demo_analytics_kpi_summary(days: int = 30):
    """Demo KPI summary data for analytics dashboard"""
    return {
        "mttr": {
            "value": 2.4,
            "unit": "hours",
            "total_repairs": 47,
            "total_repair_time": 112.8,
            "min_repair_time": 0.5,
            "max_repair_time": 8.0,
            "trend": "improving",
            "status": "good",
        },
        "mtbf": {
            "value": 168.5,
            "unit": "hours",
            "failure_count": 12,
            "total_operating_hours": 2022,
            "total_downtime": 28.8,
            "trend": "stable",
            "status": "good",
        },
        "asset_utilization": {
            "average_utilization": 87.3,
            "unit": "percent",
            "total_assets": 24,
            "active_assets": 21,
            "status_breakdown": {"Active": 21, "Maintenance": 2, "Inactive": 1},
            "trend": "improving",
            "status": "good",
        },
        "cost_tracking": {
            "total_cost": 24750,
            "labor_cost": 15250,
            "parts_cost": 9500,
            "maintenance_count": 47,
            "avg_cost_per_event": 526.60,
            "costs_by_type": {
                "Preventive": 8500,
                "Corrective": 12250,
                "Emergency": 4000,
            },
            "trend": "stable",
            "currency": "USD",
        },
        "work_order_metrics": {
            "total_created": 156,
            "completion_rate": 89.7,
            "overdue_count": 8,
            "status_breakdown": {
                "Open": 12,
                "In Progress": 18,
                "Completed": 140,
                "On Hold": 4,
            },
            "priority_breakdown": {"Low": 45, "Medium": 68, "High": 32, "Critical": 11},
            "trend": "improving",
            "status": "good",
        },
        "compliance_metrics": {
            "pm_compliance_rate": 92.5,
            "total_pm_work_orders": 40,
            "on_time_completions": 37,
            "training_compliance_rate": 88.0,
            "total_training_assigned": 25,
            "training_completed": 22,
            "certification_status": {"total": 18, "valid": 16, "expired": 2},
            "overall_compliance": 90.25,
            "status": "good",
        },
        "generated_at": datetime.now().isoformat(),
        "period_days": days,
    }


@router.get("/demo/analytics/charts/work-order-status")
async def demo_analytics_work_order_status(days: int = 30):
    """Demo work order status chart data"""
    return {
        "labels": ["Open", "In Progress", "Completed", "On Hold"],
        "data": [12, 18, 140, 4],
        "colors": {
            "Open": "#f39c12",
            "In Progress": "#3498db",
            "Completed": "#27ae60",
            "On Hold": "#e74c3c",
        },
    }


@router.get("/demo/analytics/charts/priority-distribution")
async def demo_analytics_priority_distribution(days: int = 30):
    """Demo priority distribution chart data"""
    return {
        "labels": ["Low", "Medium", "High", "Critical"],
        "data": [45, 68, 32, 11],
        "colors": {
            "Low": "#27ae60",
            "Medium": "#3498db",
            "High": "#f39c12",
            "Critical": "#e74c3c",
        },
    }


@router.get("/demo/analytics/charts/cost-trend")
async def demo_analytics_cost_trend(days: int = 30):
    """Demo cost trend chart data"""
    today = datetime.now()
    labels = []
    data = []

    # Generate realistic cost data
    import random

    random.seed(42)  # Consistent demo data
    for i in range(min(days, 30)):
        date = today - timedelta(days=29 - i)
        labels.append(date.strftime("%Y-%m-%d"))
        # Realistic daily cost between $200-$1500
        data.append(random.randint(200, 1500))

    return {"labels": labels, "data": data, "label": "Daily Maintenance Cost ($)"}


@router.get("/demo/analytics/charts/completion-trend")
async def demo_analytics_completion_trend(days: int = 30):
    """Demo completion trend chart data"""
    today = datetime.now()
    labels = []
    created = []
    completed = []

    import random

    random.seed(42)
    for i in range(min(days, 30)):
        date = today - timedelta(days=29 - i)
        labels.append(date.strftime("%Y-%m-%d"))
        c = random.randint(3, 8)
        created.append(c)
        completed.append(max(0, c - random.randint(0, 2)))

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Created",
                "data": created,
                "borderColor": "#3498db",
                "fill": False,
            },
            {
                "label": "Completed",
                "data": completed,
                "borderColor": "#27ae60",
                "fill": False,
            },
        ],
    }


@router.get("/demo/analytics/charts/asset-health")
async def demo_analytics_asset_health():
    """Demo asset health chart data"""
    return {
        "labels": ["Active", "Maintenance", "Inactive"],
        "data": [21, 2, 1],
        "colors": {
            "Active": "#27ae60",
            "Maintenance": "#f39c12",
            "Inactive": "#95a5a6",
        },
    }


@router.get("/demo/food-processing-quality", response_class=HTMLResponse)
async def demo_food_processing_quality(
    request: Request, industry: str = "cheese_plant"
):
    """Demo Food Processing Quality Management System with HACCP, GMP, and Food Safety Compliance"""
    try:
        # Industry configurations
        industry_configs = {
            "cheese_plant": {
                "name": "Cheese Processing Plant",
                "haccp_focus": ["Pasteurization", "Cooling", "Aging", "Packaging"],
                "critical_limits": {
                    "milk_temp": {"min": 4, "max": 7, "unit": "°C"},
                    "pasteurization_temp": {"min": 72, "max": 75, "unit": "°C"},
                    "aging_temp": {"min": 7, "max": 15, "unit": "°C"},
                },
                "certifications": ["SQF", "FSMA", "EU Organic", "Halal"],
            },
            "beverage_plant": {
                "name": "Beverage Processing Plant",
                "haccp_focus": [
                    "Filtration",
                    "Pasteurization",
                    "Carbonation",
                    "Packaging",
                ],
                "critical_limits": {
                    "product_temp": {"min": 2, "max": 8, "unit": "°C"},
                    "pasteurization_temp": {"min": 85, "max": 95, "unit": "°C"},
                    "ph_range": {"min": 2.5, "max": 4.5, "unit": "pH"},
                },
                "certifications": ["FSSC 22000", "BRC", "IFS", "Organic"],
            },
            "dairy_processing": {
                "name": "Dairy Processing Plant",
                "haccp_focus": [
                    "Pasteurization",
                    "Homogenization",
                    "Cooling",
                    "Packaging",
                ],
                "critical_limits": {
                    "milk_temp": {"min": 4, "max": 7, "unit": "°C"},
                    "pasteurization_temp": {"min": 72, "max": 75, "unit": "°C"},
                },
                "certifications": ["SQF", "FSMA", "ISO 22000"],
            },
        }

        industry_config = industry_configs.get(
            industry, industry_configs["cheese_plant"]
        )

        # Demo HACCP plans
        haccp_plans = [
            {
                "plan_id": "HACCP-001",
                "process_step": "Milk Receiving & Storage",
                "hazard_type": "Biological",
                "hazard_description": "Pathogenic bacteria growth in raw milk",
                "critical_control_point": True,
                "critical_limits": {
                    "temperature": {"min": 0, "max": 7, "unit": "°C"},
                    "time": {"max": 2, "unit": "hours"},
                },
                "monitoring_procedures": "Temperature monitoring every 2 hours, visual inspection",
                "corrective_actions": "Reject milk if temperature >7°C or holding time >2 hours",
                "verification_procedures": "Daily calibration of thermometers, weekly review",
                "responsible_person": "Receiving Supervisor",
                "review_frequency": "Daily",
                "status": "Active",
            },
            {
                "plan_id": "HACCP-002",
                "process_step": "Pasteurization",
                "hazard_type": "Biological",
                "hazard_description": "Survival of pathogenic microorganisms",
                "critical_control_point": True,
                "critical_limits": {
                    "temperature": {"min": 72, "max": 75, "unit": "°C"},
                    "time": {"min": 15, "unit": "seconds"},
                },
                "monitoring_procedures": "Continuous temperature recording, time-temperature integration",
                "corrective_actions": "Stop production, re-pasteurize if temperature drops below 72°C",
                "verification_procedures": "Weekly validation of pasteurization equipment",
                "responsible_person": "Production Manager",
                "review_frequency": "Daily",
                "status": "Active",
            },
        ]

        # Demo temperature readings
        temperature_readings = [
            {
                "reading_id": "TEMP-001",
                "location": "Raw Milk Storage Tank A1",
                "equipment_id": "TANK-001",
                "temperature": 4.2,
                "unit": "°C",
                "critical_limit_min": 0,
                "critical_limit_max": 7,
                "within_limits": True,
                "recorded_by": "Maria Sanchez",
                "reading_time": "2024-12-14T06:00:00",
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
                "recorded_by": "Carlos Rodriguez",
                "reading_time": "2024-12-14T08:30:00",
            },
        ]

        # Demo batch records
        batch_records = [
            {
                "batch_id": "BATCH-2024-001",
                "product_code": "CHEDDAR-001",
                "product_name": "Sharp Cheddar Cheese",
                "batch_number": "CH24121401",
                "production_date": "2024-12-14T08:00:00",
                "expiry_date": "2025-06-14T00:00:00",
                "quantity_produced": 2500,
                "unit_of_measure": "kg",
                "status": "Released",
                "release_date": "2024-12-14T16:00:00",
            }
        ]

        # Demo suppliers
        suppliers = [
            {
                "supplier_id": "SUP-001",
                "supplier_name": "Dairy Farms Inc",
                "supplier_type": "Raw Materials",
                "audit_score": 94.5,
                "status": "Approved",
            },
            {
                "supplier_id": "SUP-002",
                "supplier_name": "Packaging Solutions Ltd",
                "supplier_type": "Packaging",
                "audit_score": 91.2,
                "status": "Approved",
            },
        ]

        # Demo inspections
        inspections = [
            {
                "inspection_id": "FSI-2024-001",
                "inspection_type": "HACCP Verification",
                "area_location": "Pasteurization Area",
                "inspector_name": "Dr. Sarah Johnson",
                "inspection_date": "2024-12-14T09:00:00",
                "overall_score": 92.5,
                "status": "Pass",
            }
        ]

        # Demo sanitation schedules
        sanitation_schedules = [
            {
                "schedule_id": "SAN-001",
                "area": "Cheese Processing Line A",
                "frequency": "Daily",
                "status": "Completed",
                "last_completed": "2024-12-14T06:00:00",
            }
        ]

        # Demo CAPA records
        capa_records = [
            {
                "capa_id": "CAPA-2024-001",
                "source": "HACCP Deviation",
                "problem_description": "Pasteurization temperature dropped below 72°C",
                "status": "In Progress",
                "target_completion_date": "2025-01-31",
            }
        ]

        context = {
            "request": request,
            "industry_config": industry_config,
            "industry": industry,
            "active_haccp_plans": len(
                [p for p in haccp_plans if p["status"] == "Active"]
            ),
            "critical_control_points": len(
                [p for p in haccp_plans if p["critical_control_point"]]
            ),
            "temperature_deviations": len(
                [t for t in temperature_readings if not t["within_limits"]]
            ),
            "approved_suppliers": len(
                [s for s in suppliers if s["status"] == "Approved"]
            ),
            "completed_batches": len(
                [b for b in batch_records if b["status"] == "Released"]
            ),
            "sanitation_compliance": 95.0,
            "environmental_compliance": 98.0,
            "food_safety_metrics": {
                "haccp_compliance": 96.8,
                "gmp_compliance": 94.2,
                "certification_status": "SQF Level 3",
                "last_audit_score": 92.5,
            },
            "haccp_plans": haccp_plans,
            "temperature_readings": temperature_readings,
            "batch_records": batch_records,
            "suppliers": suppliers,
            "inspections": inspections,
            "sanitation_schedules": sanitation_schedules,
            "capa_records": capa_records,
            "is_demo": True,
            "demo_banner": f"Demo: {industry_config['name']} - Complete HACCP & GMP Quality Management System",
        }

        return templates.TemplateResponse("quality_dashboard.html", context)

    except Exception as e:
        import traceback

        return HTMLResponse(
            content=f"<h1>Demo Error</h1><pre>{traceback.format_exc()}</pre>",
            status_code=500,
        )
