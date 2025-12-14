import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

from app.routers.onboarding import ROLE_ONBOARDING_CONFIG


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
        "active_work_orders": 3,
        "completed_orders": 47,
        "status": "Available",
        "contact": "mike.johnson@company.com",
    },
    {
        "id": 2,
        "full_name": "Sarah Chen",
        "username": "sarah.chen@company.com",
        "role": "Maintenance Manager",
        "department": "Operations",
        "skills": ["Project Management", "Mechanical", "Safety"],
        "active_work_orders": 5,
        "completed_orders": 128,
        "status": "Busy",
        "contact": "sarah.chen@company.com",
    },
    {
        "id": 3,
        "full_name": "Alex Rodriguez",
        "username": "alex.rodriguez@company.com",
        "role": "Maintenance Technician",
        "department": "Maintenance",
        "skills": ["Mechanical", "Pneumatics", "Preventive Maintenance"],
        "active_work_orders": 2,
        "completed_orders": 23,
        "status": "Available",
        "contact": "alex.rodriguez@company.com",
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


@router.get("/demo", response_class=HTMLResponse)
async def demo_dashboard(request: Request):
    """Demo dashboard with real Firestore data"""
    # Redirect to public_demo dashboard which uses real data
    return RedirectResponse(url="/demo/dashboard", status_code=302)


@router.get("/demo/assets", response_class=HTMLResponse)
async def demo_assets(request: Request):
    """Demo assets page with real Firestore data"""
    from app.core.firestore_db import get_firestore_manager

    try:
        fm = get_firestore_manager()
        assets = await fm.get_assets()

        # Calculate stats from real data
        stats = {
            "total": len(assets),
            "active": len([a for a in assets if a.get("status") in ["Operational", "Active", "operational"]]),
            "critical": len([a for a in assets if a.get("criticality") == "Critical" or a.get("status") in ["Critical", "Down"]]),
            "maintenance_due": len([a for a in assets if a.get("status") in ["Maintenance Required", "Warning", "Needs Attention"]]),
        }

        return templates.TemplateResponse(
            "assets_list.html",
            {
                "request": request,
                "assets": assets,
                "stats": stats,
                "is_demo": True,
                "demo_mode": True,
                "current_user": {"uid": "demo", "role": "technician", "full_name": "Demo User"},
            },
        )
    except Exception as e:
        import logging
        logging.error(f"Error loading demo assets: {e}")
        # Fallback to mock data if Firestore fails
        return templates.TemplateResponse(
            "assets_list.html",
            {
                "request": request,
                "assets": DEMO_ASSETS,
                "stats": {"total": len(DEMO_ASSETS), "active": 3, "critical": 1, "maintenance_due": 1},
                "is_demo": True,
            },
        )


@router.get("/demo/work-orders", response_class=HTMLResponse)
async def demo_work_orders(request: Request):
    """Demo work orders page with real Firestore data"""
    from app.core.firestore_db import get_firestore_manager

    try:
        fm = get_firestore_manager()
        work_orders = await fm.get_work_orders()

        # Calculate stats from real data
        stats = {
            "total": len(work_orders),
            "in_progress": len([w for w in work_orders if w.get("status") in ["In Progress", "active"]]),
            "scheduled": len([w for w in work_orders if w.get("status") in ["Scheduled", "Open", "pending"]]),
            "overdue": len([w for w in work_orders if w.get("status") in ["Overdue", "On Hold"]]),
            "completed": len([w for w in work_orders if w.get("status") in ["Completed", "completed"]]),
        }

        return templates.TemplateResponse(
            "work_orders.html",
            {
                "request": request,
                "work_orders": work_orders,
                "stats": stats,
                "is_demo": True,
                "demo_mode": True,
                "current_user": {"uid": "demo", "role": "technician", "full_name": "Demo User"},
            },
        )
    except Exception as e:
        import logging
        logging.error(f"Error loading demo work orders: {e}")
        # Fallback to mock data if Firestore fails
        return templates.TemplateResponse(
            "work_orders.html",
            {
                "request": request,
                "work_orders": DEMO_WORK_ORDERS,
                "stats": {"total": len(DEMO_WORK_ORDERS), "in_progress": 2, "scheduled": 1, "overdue": 1},
                "is_demo": True,
            },
        )


@router.get("/demo/team", response_class=HTMLResponse)
async def demo_team(request: Request):
    """Demo team page with sample data"""

    # Convert DEMO_TEAM dictionaries to objects that support dot notation
    class DictObj:
        def __init__(self, d):
            for k, v in d.items():
                setattr(self, k, v)

    demo_users = [DictObj(user) for user in DEMO_TEAM]

    # Add mock user for WebSocket connection - also convert to object
    mock_user = DictObj(
        {
            "id": "demo_user_1",
            "username": "demo@chatterfix.com",
            "full_name": "Demo Manager",
            "role": "manager",
        }
    )

    return templates.TemplateResponse(
        "team_dashboard.html",
        {
            "request": request,
            "users": demo_users,  # Convert dictionaries to objects with dot notation
            "messages": [],  # Empty messages for demo
            "online_users": [],  # No online users in demo mode
            "user": mock_user,  # Pass current user for WebSocket as object
            "is_demo": True,
        },
    )


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
    """Demo purchasing page - uses Firestore when available, demo data as fallback"""
    try:
        from app.core.firestore_db import get_firestore_manager

        db = get_firestore_manager()

        # Try to get live vendors and parts data from Firestore
        vendors = await db.get_collection("vendors", order_by="name")
        parts = await db.get_collection("parts", order_by="name", limit=50)

    except Exception as e:
        # Fallback to demo data if Firestore fails
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
                            "type": "text"
                        },
                        {
                            "title": "Diagnostic Procedures",
                            "content": "Step-by-step diagnostic procedures for common pump issues.",
                            "type": "interactive"
                        },
                        {
                            "title": "Maintenance Tasks",
                            "content": "Regular maintenance procedures and schedules.",
                            "type": "hands_on"
                        }
                    ]
                }
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
                            "type": "text"
                        },
                        {
                            "title": "Troubleshooting Guide",
                            "content": "Systematic approach to diagnosing HVAC problems.",
                            "type": "interactive"
                        }
                    ]
                }
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
                            "type": "text"
                        },
                        {
                            "title": "Lockout/Tagout Procedures",
                            "content": "Step-by-step LOTO procedures for electrical systems.",
                            "type": "hands_on"
                        }
                    ]
                }
            }
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
    """Demo intelligent parts/inventory page with real Firestore data"""
    from app.core.firestore_db import get_firestore_manager

    try:
        fm = get_firestore_manager()
        parts_docs = list(fm.db.collection("parts").limit(100).stream())
        parts = [{"id": p.id, **p.to_dict()} for p in parts_docs]

        # Calculate stats from real data
        low_stock_count = len([p for p in parts if p.get("quantity", 0) <= p.get("reorder_point", 5)])
        total_value = sum((p.get("quantity", 0) * p.get("cost", 0)) for p in parts)

        return templates.TemplateResponse(
            "parts_catalog.html",
            {
                "request": request,
                "parts": parts,
                "low_stock_count": low_stock_count,
                "total_value": total_value,
                "is_demo": True,
                "demo_mode": True,
                "current_user": {"uid": "demo", "role": "technician", "full_name": "Demo User"},
            },
        )
    except Exception as e:
        import logging
        logging.error(f"Error loading demo inventory: {e}")
        # Fallback to mock data
        demo_parts = [
            {"id": 1, "part_number": "FLT-001", "name": "HVAC Air Filter", "quantity": 15, "reorder_point": 10, "cost": 12.50, "status": "In Stock"},
            {"id": 2, "part_number": "OIL-COMP", "name": "Compressor Oil 5W-30", "quantity": 3, "reorder_point": 5, "cost": 85.00, "status": "Low Stock"},
        ]
        return templates.TemplateResponse(
            "parts_catalog.html",
            {
                "request": request,
                "parts": demo_parts,
                "low_stock_count": 1,
                "total_value": 442.50,
                "is_demo": True,
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

@router.get("/analytics/kpi/summary")
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
            "status": "good"
        },
        "mtbf": {
            "value": 168.5,
            "unit": "hours",
            "failure_count": 12,
            "total_operating_hours": 2022,
            "total_downtime": 28.8,
            "trend": "stable",
            "status": "good"
        },
        "asset_utilization": {
            "average_utilization": 87.3,
            "unit": "percent",
            "total_assets": 24,
            "active_assets": 21,
            "status_breakdown": {
                "Active": 21,
                "Maintenance": 2,
                "Inactive": 1
            },
            "trend": "improving",
            "status": "good"
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
                "Emergency": 4000
            },
            "trend": "stable",
            "currency": "USD"
        },
        "work_order_metrics": {
            "total_created": 156,
            "completion_rate": 89.7,
            "overdue_count": 8,
            "status_breakdown": {
                "Open": 12,
                "In Progress": 18,
                "Completed": 140,
                "On Hold": 4
            },
            "priority_breakdown": {
                "Low": 45,
                "Medium": 68,
                "High": 32,
                "Critical": 11
            },
            "trend": "improving",
            "status": "good"
        },
        "compliance_metrics": {
            "pm_compliance_rate": 92.5,
            "total_pm_work_orders": 40,
            "on_time_completions": 37,
            "training_compliance_rate": 88.0,
            "total_training_assigned": 25,
            "training_completed": 22,
            "certification_status": {
                "total": 18,
                "valid": 16,
                "expired": 2
            },
            "overall_compliance": 90.25,
            "status": "good"
        },
        "generated_at": datetime.now().isoformat(),
        "period_days": days
    }


@router.get("/analytics/charts/work-order-status")
async def demo_analytics_work_order_status(days: int = 30):
    """Demo work order status chart data"""
    return {
        "labels": ["Open", "In Progress", "Completed", "On Hold"],
        "data": [12, 18, 140, 4],
        "colors": {
            "Open": "#f39c12",
            "In Progress": "#3498db",
            "Completed": "#27ae60",
            "On Hold": "#e74c3c"
        }
    }


@router.get("/analytics/charts/priority-distribution")
async def demo_analytics_priority_distribution(days: int = 30):
    """Demo priority distribution chart data"""
    return {
        "labels": ["Low", "Medium", "High", "Critical"],
        "data": [45, 68, 32, 11],
        "colors": {
            "Low": "#27ae60",
            "Medium": "#3498db",
            "High": "#f39c12",
            "Critical": "#e74c3c"
        }
    }


@router.get("/analytics/charts/cost-trend")
async def demo_analytics_cost_trend(days: int = 30):
    """Demo cost trend chart data"""
    today = datetime.now()
    labels = []
    data = []

    # Generate realistic cost data
    import random
    random.seed(42)  # Consistent demo data
    for i in range(min(days, 30)):
        date = today - timedelta(days=29-i)
        labels.append(date.strftime("%Y-%m-%d"))
        # Realistic daily cost between $200-$1500
        data.append(random.randint(200, 1500))

    return {
        "labels": labels,
        "data": data,
        "label": "Daily Maintenance Cost ($)"
    }


@router.get("/analytics/charts/completion-trend")
async def demo_analytics_completion_trend(days: int = 30):
    """Demo completion trend chart data"""
    today = datetime.now()
    labels = []
    created = []
    completed = []

    import random
    random.seed(42)
    for i in range(min(days, 30)):
        date = today - timedelta(days=29-i)
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
                "fill": False
            },
            {
                "label": "Completed",
                "data": completed,
                "borderColor": "#27ae60",
                "fill": False
            }
        ]
    }


@router.get("/analytics/charts/asset-health")
async def demo_analytics_asset_health():
    """Demo asset health chart data"""
    return {
        "labels": ["Active", "Maintenance", "Inactive"],
        "data": [21, 2, 1],
        "colors": {
            "Active": "#27ae60",
            "Maintenance": "#f39c12",
            "Inactive": "#95a5a6"
        }
    }


@router.get("/analytics/charts/cost-breakdown")
async def demo_analytics_cost_breakdown(days: int = 30):
    """Demo cost breakdown chart data"""
    return {
        "labels": ["Preventive", "Corrective", "Emergency"],
        "data": [8500, 12250, 4000],
        "colors": {
            "Preventive": "#27ae60",
            "Corrective": "#f39c12",
            "Emergency": "#e74c3c"
        }
    }
