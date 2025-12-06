"""
Public Demo Router
Provides full demo access without authentication requirements
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core.db_adapter import get_db_adapter
import logging
from datetime import datetime

router = APIRouter(prefix="/demo", tags=["demo"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


# Mock demo user for public access
DEMO_USER = {
    "id": 999,  # Special demo user ID
    "username": "demo_visitor",
    "email": "demo@chatterfix.com",
    "full_name": "Demo Visitor",
    "role": "viewer",
}


@router.get("/dashboard", response_class=HTMLResponse)
async def demo_dashboard(request: Request):
    """Full dashboard demo without authentication"""
    try:
        # Get real-time demo data from Firestore
        db_adapter = get_db_adapter()
        dashboard_data = await db_adapter.get_dashboard_data(str(DEMO_USER["id"]))

        # Extract data for template
        work_orders = dashboard_data.get("work_orders", [])
        assets = dashboard_data.get("assets", [])

        # Build demo workload stats
        active_count = len([wo for wo in work_orders if wo.get("status") == "active"])
        pending_count = len([wo for wo in work_orders if wo.get("status") == "pending"])
        completed_count = len(
            [wo for wo in work_orders if wo.get("status") == "completed"]
        )

        workload = {
            "stats": {
                "active": max(active_count, 12),  # Ensure demo has interesting numbers
                "pending": max(pending_count, 8),
                "completed": max(completed_count, 45),
                "total": max(len(work_orders), 65),
            }
        }

        # Demo performance metrics
        performance = {
            "today": {
                "completion_rate": 94.7,
                "total_work_orders": workload["stats"]["total"],
                "completed_today": 7,
            }
        }

        # Demo equipment status
        equipment = {
            "total_assets": max(len(assets), 150),
            "healthy": max(len(assets) - 5, 142),
            "warning": 6,
            "critical": 2,
            "uptime_percentage": 95.3,
        }

        # Demo notifications
        notifications = {
            "unread_count": 4,
            "recent_interactions": [
                {
                    "type": "AI Analysis",
                    "message": "Pump Station A shows early wear indicators",
                    "timestamp": "5 minutes ago",
                    "priority": "medium",
                },
                {
                    "type": "Work Order",
                    "message": "Conveyor Belt maintenance completed",
                    "timestamp": "15 minutes ago",
                    "priority": "low",
                },
            ],
        }

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "workload": workload,
                "performance": performance,
                "notifications": notifications,
                "equipment": equipment,
                "demo_mode": True,
                "demo_banner": "🎭 DEMO MODE - Full functionality with sample data",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo dashboard: {e}")
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "workload": {
                    "stats": {"active": 12, "pending": 8, "completed": 45, "total": 65}
                },
                "performance": {
                    "today": {
                        "completion_rate": 94.7,
                        "total_work_orders": 65,
                        "completed_today": 7,
                    }
                },
                "notifications": {"unread_count": 4, "recent_interactions": []},
                "equipment": {
                    "total_assets": 150,
                    "healthy": 142,
                    "warning": 6,
                    "critical": 2,
                    "uptime_percentage": 95.3,
                },
                "demo_mode": True,
                "demo_banner": "🎭 DEMO MODE - Full functionality with sample data",
                "error": "Demo running with fallback data",
            },
        )


@router.get("/features", response_class=HTMLResponse)
async def demo_features(request: Request):
    """Feature showcase demo"""
    return templates.TemplateResponse(
        "demo_features.html",
        {"request": request, "current_user": DEMO_USER, "demo_mode": True},
    )


@router.get("/mobile", response_class=HTMLResponse)
async def demo_mobile(request: Request):
    """Mobile-optimized demo"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": DEMO_USER,
            "workload": {
                "stats": {"active": 8, "pending": 5, "completed": 32, "total": 45}
            },
            "performance": {
                "today": {
                    "completion_rate": 92.1,
                    "total_work_orders": 45,
                    "completed_today": 5,
                }
            },
            "notifications": {"unread_count": 2, "recent_interactions": []},
            "equipment": {
                "total_assets": 85,
                "healthy": 80,
                "warning": 3,
                "critical": 2,
                "uptime_percentage": 94.1,
            },
            "demo_mode": True,
            "mobile_demo": True,
            "demo_banner": "📱 MOBILE DEMO - Optimized for mobile devices",
        },
    )


@router.get("/ai", response_class=HTMLResponse)
async def demo_ai(request: Request):
    """AI features demo"""
    return templates.TemplateResponse(
        "ai_demo.html",
        {
            "request": request,
            "current_user": DEMO_USER,
            "demo_mode": True,
            "ai_features": {
                "predictive_maintenance": True,
                "computer_vision": True,
                "automated_scheduling": True,
                "smart_alerts": True,
            },
        },
    )


@router.get("/work-orders", response_class=HTMLResponse)
async def demo_work_orders(request: Request):
    """Work orders demo"""
    try:
        # Generate demo work orders
        demo_work_orders = [
            {
                "id": "WO-2024-001",
                "title": "Conveyor Belt Maintenance",
                "description": "Routine belt inspection and tension adjustment",
                "priority": "Medium",
                "status": "In Progress",
                "assigned_to": "Mike Johnson",
                "asset_name": "Conveyor Belt A-12",
                "created_date": "2024-12-05",
                "due_date": "2024-12-07",
            },
            {
                "id": "WO-2024-002",
                "title": "Pump Station Leak Repair",
                "description": "AI detected unusual vibration patterns indicating potential seal failure",
                "priority": "High",
                "status": "Open",
                "assigned_to": "Sarah Chen",
                "asset_name": "Hydraulic Pump Station B",
                "created_date": "2024-12-06",
                "due_date": "2024-12-06",
            },
            {
                "id": "WO-2024-003",
                "title": "HVAC Filter Replacement",
                "description": "Scheduled filter replacement - East Wing",
                "priority": "Low",
                "status": "Completed",
                "assigned_to": "David Rodriguez",
                "asset_name": "HVAC Unit East-03",
                "created_date": "2024-12-04",
                "due_date": "2024-12-05",
            },
        ]

        return templates.TemplateResponse(
            "work_orders.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "work_orders": demo_work_orders,
                "demo_mode": True,
                "demo_banner": "🔧 WORK ORDERS DEMO - Sample maintenance requests",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo work orders: {e}")
        return JSONResponse({"error": "Demo work orders unavailable"}, status_code=500)


@router.get("/training", response_class=HTMLResponse)
async def demo_training(request: Request):
    """Training center demo"""
    try:
        demo_training = [
            {
                "id": "TRN-001",
                "title": "Hydraulic Systems Safety",
                "description": "Comprehensive training on hydraulic system maintenance and safety protocols",
                "status": "in_progress",
                "progress": 65,
                "estimated_duration_minutes": 45,
                "difficulty_level": "Intermediate",
            },
            {
                "id": "TRN-002",
                "title": "AI-Assisted Diagnostics",
                "description": "Learn how to interpret AI-generated maintenance recommendations",
                "status": "assigned",
                "progress": 0,
                "estimated_duration_minutes": 30,
                "difficulty_level": "Advanced",
            },
        ]

        stats = {
            "total_assigned": 8,
            "completed": 5,
            "in_progress": 2,
            "avg_score": 87.5,
        }

        return templates.TemplateResponse(
            "training_center.html",
            {
                "request": request,
                "current_user": DEMO_USER,
                "my_training": demo_training,
                "available_modules": [],
                "stats": stats,
                "demo_mode": True,
                "demo_banner": "🎓 TRAINING DEMO - Interactive learning modules",
            },
        )
    except Exception as e:
        logger.error(f"Error loading demo training: {e}")
        return JSONResponse({"error": "Demo training unavailable"}, status_code=500)


@router.get("/assets", response_class=HTMLResponse)
async def demo_assets(request: Request):
    """Asset management demo"""
    demo_assets = [
        {
            "id": "AST-001",
            "name": "Conveyor Belt System A-12",
            "type": "Conveyor",
            "status": "Operational",
            "location": "Production Floor - Zone A",
            "condition_rating": 8,
            "last_maintenance": "2024-11-28",
            "next_maintenance": "2024-12-15",
        },
        {
            "id": "AST-002",
            "name": "Hydraulic Pump Station B",
            "type": "Pump",
            "status": "Warning",
            "location": "Utility Room - Level 2",
            "condition_rating": 6,
            "last_maintenance": "2024-11-15",
            "next_maintenance": "2024-12-08",
        },
    ]

    return templates.TemplateResponse(
        "assets.html",
        {
            "request": request,
            "current_user": DEMO_USER,
            "assets": demo_assets,
            "demo_mode": True,
            "demo_banner": "🏭 ASSETS DEMO - Equipment and machinery tracking",
        },
    )


@router.get("/api/demo/stats")
async def demo_api_stats():
    """Demo API endpoint for live stats"""
    return {
        "status": "demo",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "active_work_orders": 12,
            "completed_today": 7,
            "assets_monitored": 150,
            "uptime_percentage": 95.3,
            "ai_predictions": 24,
            "users_online": 8,
        },
        "demo_mode": True,
    }


@router.get("/api/demo/health")
async def demo_health():
    """Demo health check"""
    return {
        "status": "healthy",
        "mode": "demo",
        "timestamp": datetime.now().isoformat(),
        "features": ["dashboard", "work_orders", "assets", "training", "ai_analysis"],
        "database": "demo_data_active",
    }
