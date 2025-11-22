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
        "criticality": "High"
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
        "criticality": "Medium"
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
        "criticality": "Medium"
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
        "criticality": "Critical"
    }
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
        "description": "Quarterly filter replacement for optimal air quality and system efficiency."
    },
    {
        "id": "WO-2024-002",
        "title": "Compressor oil change and inspection",
        "asset": "Compressor C-5",
        "priority": "Critical",
        "status": "Overdue",
        "assigned_to": "Sarah Chen",
        "created_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
        "due_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "description": "Emergency maintenance required. Compressor showing signs of oil contamination."
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
        "description": "Monthly calibration to ensure product quality standards."
    }
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
        "contact": "mike.johnson@company.com"
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
        "contact": "sarah.chen@company.com"
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
        "contact": "alex.rodriguez@company.com"
    }
]

DEMO_STATS = {
    "total_assets": len(DEMO_ASSETS),
    "operational_assets": len([a for a in DEMO_ASSETS if a["status"] == "Operational"]),
    "assets_needing_maintenance": len([a for a in DEMO_ASSETS if a["status"] in ["Maintenance Required", "Down"]]),
    "total_work_orders": len(DEMO_WORK_ORDERS),
    "open_work_orders": len([w for w in DEMO_WORK_ORDERS if w["status"] in ["In Progress", "Scheduled"]]),
    "overdue_work_orders": len([w for w in DEMO_WORK_ORDERS if w["status"] == "Overdue"]),
    "team_members": len(DEMO_TEAM),
    "average_completion_time": "4.2 days"
}

@router.get("/demo", response_class=HTMLResponse)
async def demo_dashboard(request: Request):
    """Demo dashboard with sample data"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": DEMO_STATS,
        "recent_work_orders": DEMO_WORK_ORDERS[:3],
        "critical_assets": [a for a in DEMO_ASSETS if a["criticality"] == "Critical" or a["status"] == "Down"],
        "is_demo": True
    })

@router.get("/demo/assets", response_class=HTMLResponse)
async def demo_assets(request: Request):
    """Demo assets page with sample data"""
    return templates.TemplateResponse("assets_list.html", {
        "request": request,
        "assets": DEMO_ASSETS,
        "stats": {
            "total_assets": len(DEMO_ASSETS),
            "operational": len([a for a in DEMO_ASSETS if a["status"] == "Operational"]),
            "maintenance_required": len([a for a in DEMO_ASSETS if a["status"] == "Maintenance Required"]),
            "down": len([a for a in DEMO_ASSETS if a["status"] == "Down"])
        },
        "is_demo": True
    })

@router.get("/demo/work-orders", response_class=HTMLResponse)
async def demo_work_orders(request: Request):
    """Demo work orders page with sample data"""
    return templates.TemplateResponse("work_orders.html", {
        "request": request,
        "work_orders": DEMO_WORK_ORDERS,
        "stats": {
            "total": len(DEMO_WORK_ORDERS),
            "in_progress": len([w for w in DEMO_WORK_ORDERS if w["status"] == "In Progress"]),
            "scheduled": len([w for w in DEMO_WORK_ORDERS if w["status"] == "Scheduled"]),
            "overdue": len([w for w in DEMO_WORK_ORDERS if w["status"] == "Overdue"])
        },
        "is_demo": True
    })

@router.get("/demo/team", response_class=HTMLResponse)
async def demo_team(request: Request):
    """Demo team page with sample data"""
    return templates.TemplateResponse("team_dashboard.html", {
        "request": request,
        "team_members": DEMO_TEAM,
        "stats": {
            "total_members": len(DEMO_TEAM),
            "available": len([t for t in DEMO_TEAM if t["availability"] == "Available"]),
            "busy": len([t for t in DEMO_TEAM if t["availability"] == "Busy"]),
            "total_active_orders": sum(t["active_orders"] for t in DEMO_TEAM)
        },
        "is_demo": True
    })

@router.get("/demo/planner", response_class=HTMLResponse)
async def demo_planner(request: Request):
    """Demo planner page with sample data"""
    # Generate sample scheduled maintenance
    planned_maintenance = []
    for i, asset in enumerate(DEMO_ASSETS):
        if asset["next_maintenance"] != "Overdue":
            planned_maintenance.append({
                "id": f"PM-{i+1:03d}",
                "asset": asset["name"],
                "task": f"Scheduled maintenance for {asset['name']}",
                "date": asset["next_maintenance"],
                "duration": f"{random.randint(2, 8)} hours",
                "assigned_to": random.choice(DEMO_TEAM)["name"],
                "priority": asset["criticality"]
            })
    
    return templates.TemplateResponse("planner_dashboard.html", {
        "request": request,
        "planned_maintenance": planned_maintenance,
        "upcoming_tasks": planned_maintenance[:5],
        "is_demo": True
    })

@router.get("/demo/purchasing", response_class=HTMLResponse)
async def demo_purchasing(request: Request):
    """Demo purchasing page with sample data"""
    demo_inventory = [
        {
            "id": 1,
            "part_number": "FLT-001",
            "description": "HVAC Air Filter - 20x25x1",
            "quantity": 15,
            "reorder_point": 10,
            "cost": 12.50,
            "supplier": "FilterPro Inc",
            "status": "In Stock"
        },
        {
            "id": 2,
            "part_number": "OIL-COMP-5W30",
            "description": "Compressor Oil 5W-30 - 5L",
            "quantity": 3,
            "reorder_point": 5,
            "cost": 85.00,
            "supplier": "Industrial Lubricants",
            "status": "Low Stock"
        },
        {
            "id": 3,
            "part_number": "BELT-V001",
            "description": "V-Belt - Industrial Grade",
            "quantity": 0,
            "reorder_point": 2,
            "cost": 45.00,
            "supplier": "PowerTrans Supply",
            "status": "Out of Stock"
        }
    ]
    
    return templates.TemplateResponse("purchasing_dashboard.html", {
        "request": request,
        "inventory": demo_inventory,
        "low_stock_items": [i for i in demo_inventory if i["quantity"] <= i["reorder_point"]],
        "is_demo": True
    })

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
            "total_enrolled": 15
        },
        {
            "id": 2,
            "title": "Safety Procedures for Industrial Equipment",
            "description": "Essential safety protocols for working with industrial machinery",
            "duration": "2 hours",
            "difficulty": "Intermediate",
            "completed_by": 18,
            "total_enrolled": 18
        },
        {
            "id": 3,
            "title": "Predictive Maintenance Techniques",
            "description": "Advanced techniques for predicting equipment failures",
            "duration": "6 hours",
            "difficulty": "Advanced",
            "completed_by": 5,
            "total_enrolled": 8
        }
    ]
    
    return templates.TemplateResponse("training_center.html", {
        "request": request,
        "courses": demo_courses,
        "stats": {
            "total_courses": len(demo_courses),
            "completion_rate": "85%",
            "avg_score": "92%"
        },
        "is_demo": True
    })

@router.get("/demo/ar-mode", response_class=HTMLResponse)
async def demo_ar_mode(request: Request):
    """Demo AR mode page"""
    return templates.TemplateResponse("ar/dashboard.html", {
        "request": request,
        "is_demo": True
    })