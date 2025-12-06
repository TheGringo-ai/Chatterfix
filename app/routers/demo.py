from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
import json
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
    loader=FileSystemLoader("app/templates"), auto_reload=True, cache_size=0
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
        "name": "Mike Johnson",
        "role": "Senior Technician",
        "department": "Maintenance",
        "skills": ["HVAC", "Electrical", "Plumbing"],
        "active_orders": 3,
        "completed_orders": 47,
        "availability": "Available",
        "contact": "mike.johnson@company.com",
    },
    {
        "id": 2,
        "name": "Sarah Chen",
        "role": "Maintenance Manager",
        "department": "Operations",
        "skills": ["Project Management", "Mechanical", "Safety"],
        "active_orders": 5,
        "completed_orders": 128,
        "availability": "Busy",
        "contact": "sarah.chen@company.com",
    },
    {
        "id": 3,
        "name": "Alex Rodriguez",
        "role": "Maintenance Technician",
        "department": "Maintenance",
        "skills": ["Mechanical", "Pneumatics", "Preventive Maintenance"],
        "active_orders": 2,
        "completed_orders": 23,
        "availability": "Available",
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
    """Demo dashboard with sample data"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": DEMO_STATS,
            "recent_work_orders": DEMO_WORK_ORDERS[:3],
            "critical_assets": [
                a
                for a in DEMO_ASSETS
                if a["criticality"] == "Critical" or a["status"] == "Down"
            ],
            "is_demo": True,
        },
    )


@router.get("/demo/assets", response_class=HTMLResponse)
async def demo_assets(request: Request):
    """Demo assets page with sample data"""
    return templates.TemplateResponse(
        "assets_list.html",
        {
            "request": request,
            "assets": DEMO_ASSETS,
            "stats": {
                "total_assets": len(DEMO_ASSETS),
                "operational": len(
                    [a for a in DEMO_ASSETS if a["status"] == "Operational"]
                ),
                "maintenance_required": len(
                    [a for a in DEMO_ASSETS if a["status"] == "Maintenance Required"]
                ),
                "down": len([a for a in DEMO_ASSETS if a["status"] == "Down"]),
            },
            "is_demo": True,
        },
    )


@router.get("/demo/work-orders", response_class=HTMLResponse)
async def demo_work_orders(request: Request):
    """Demo work orders page with sample data"""
    return templates.TemplateResponse(
        "work_orders.html",
        {
            "request": request,
            "work_orders": DEMO_WORK_ORDERS,
            "stats": {
                "total": len(DEMO_WORK_ORDERS),
                "in_progress": len(
                    [w for w in DEMO_WORK_ORDERS if w["status"] == "In Progress"]
                ),
                "scheduled": len(
                    [w for w in DEMO_WORK_ORDERS if w["status"] == "Scheduled"]
                ),
                "overdue": len(
                    [w for w in DEMO_WORK_ORDERS if w["status"] == "Overdue"]
                ),
            },
            "is_demo": True,
        },
    )


@router.get("/demo/team", response_class=HTMLResponse)
async def demo_team(request: Request):
    """Demo team page with sample data"""
    return templates.TemplateResponse(
        "team_dashboard.html",
        {
            "request": request,
            "team_members": DEMO_TEAM,
            "stats": {
                "total_members": len(DEMO_TEAM),
                "available": len(
                    [t for t in DEMO_TEAM if t["availability"] == "Available"]
                ),
                "busy": len([t for t in DEMO_TEAM if t["availability"] == "Busy"]),
                "total_active_orders": sum(t["active_orders"] for t in DEMO_TEAM),
            },
            "is_demo": True,
        },
    )


@router.get("/demo/planner", response_class=HTMLResponse)
async def demo_planner(request: Request):
    """Demo planner page - comprehensive enterprise scheduler interface"""
    # Return the planner dashboard but mark it as advanced mode for the frontend
    print("🔧 DEBUG: Serving planner with advanced_mode=True")
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
    """Demo purchasing page - full POS system identical to main app"""
    from app.core.firestore_db import get_firestore_manager

    db = get_firestore_manager()

    # Get live vendors and parts data (same as main POS system)
    vendors = await db.get_collection("vendors", order_by="name")
    parts = await db.get_collection("parts", order_by="name", limit=50)

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
    """Demo intelligent parts/inventory page"""
    demo_parts = [
        {
            "id": 1,
            "part_number": "FLT-001",
            "name": "HVAC Air Filter - 20x25x1",
            "category": "Filters",
            "quantity": 15,
            "reorder_point": 10,
            "cost": 12.50,
            "supplier": "FilterPro Inc",
            "status": "In Stock",
            "compatible_assets": ["HVAC Unit B-2", "HVAC Unit C-1"],
            "monthly_usage": 4,
            "ai_recommendation": "Current stock sufficient for 3.75 months",
        },
        {
            "id": 2,
            "part_number": "OIL-COMP-5W30",
            "name": "Compressor Oil 5W-30 - 5L",
            "category": "Lubricants",
            "quantity": 3,
            "reorder_point": 5,
            "cost": 85.00,
            "supplier": "Industrial Lubricants",
            "status": "Low Stock",
            "compatible_assets": ["Compressor C-5", "Compressor D-2"],
            "monthly_usage": 2,
            "ai_recommendation": "⚠️ Reorder recommended - only 1.5 months supply remaining",
        },
        {
            "id": 3,
            "part_number": "BELT-V001",
            "name": "V-Belt - Industrial Grade",
            "category": "Belts",
            "quantity": 0,
            "reorder_point": 2,
            "cost": 45.00,
            "supplier": "PowerTrans Supply",
            "status": "Out of Stock",
            "compatible_assets": ["Production Line A", "Conveyor System"],
            "monthly_usage": 1,
            "ai_recommendation": "🚨 Critical - Order immediately! Predicted need in 12 days",
        },
        {
            "id": 4,
            "part_number": "BRG-6205",
            "name": "Deep Groove Ball Bearing 6205",
            "category": "Bearings",
            "quantity": 8,
            "reorder_point": 4,
            "cost": 15.75,
            "supplier": "Bearing Depot",
            "status": "In Stock",
            "compatible_assets": ["Production Line A", "Forklift FL-001"],
            "monthly_usage": 1,
            "ai_recommendation": "Stock level optimal for 8 months",
        },
    ]

    return templates.TemplateResponse(
        "parts_catalog.html",
        {
            "request": request,
            "parts": demo_parts,
            "low_stock_count": len(
                [p for p in demo_parts if p["quantity"] <= p["reorder_point"]]
            ),
            "total_value": sum(p["quantity"] * p["cost"] for p in demo_parts),
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
