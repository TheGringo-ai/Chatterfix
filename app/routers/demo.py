from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
import random

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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
    """Demo planner page with sample data"""
    # Generate sample scheduled maintenance
    planned_maintenance = []
    for i, asset in enumerate(DEMO_ASSETS):
        if asset["next_maintenance"] != "Overdue":
            planned_maintenance.append(
                {
                    "id": f"PM-{i + 1:03d}",
                    "asset": asset["name"],
                    "task": f"Scheduled maintenance for {asset['name']}",
                    "date": asset["next_maintenance"],
                    "duration": f"{random.randint(2, 8)} hours",
                    "assigned_to": random.choice(DEMO_TEAM)["name"],
                    "priority": asset["criticality"],
                }
            )

    return templates.TemplateResponse(
        "planner_dashboard.html",
        {
            "request": request,
            "planned_maintenance": planned_maintenance,
            "upcoming_tasks": planned_maintenance[:5],
            "is_demo": True,
        },
    )


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
        {
            "request": request, 
            "vendors": vendors,
            "parts": parts,
            "is_demo": True
        }
    )


@router.get("/demo/training", response_class=HTMLResponse)
async def demo_training(request: Request):
    """Demo training page with sample data"""
    demo_courses = [
        {
            "id": 1,
            "title": "HVAC Maintenance Fundamentals",
            "description": "Learn the basics of HVAC system maintenance and troubleshooting",
            "duration": "4 hours",
            "difficulty": "Beginner",
            "completed_by": 12,
            "total_enrolled": 15,
        },
        {
            "id": 2,
            "title": "Safety Procedures for Industrial Equipment",
            "description": "Essential safety protocols for working with industrial machinery",
            "duration": "2 hours",
            "difficulty": "Intermediate",
            "completed_by": 18,
            "total_enrolled": 18,
        },
        {
            "id": 3,
            "title": "Predictive Maintenance Techniques",
            "description": "Advanced techniques for predicting equipment failures",
            "duration": "6 hours",
            "difficulty": "Advanced",
            "completed_by": 5,
            "total_enrolled": 8,
        },
    ]

    return templates.TemplateResponse(
        "training_center.html",
        {
            "request": request,
            "courses": demo_courses,
            "stats": {
                "total_courses": len(demo_courses),
                "completion_rate": "85%",
                "avg_score": "92%",
            },
            "is_demo": True,
        },
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
