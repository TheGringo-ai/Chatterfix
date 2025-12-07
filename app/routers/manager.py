"""
Manager Dashboard Router
Comprehensive management interface for ChatterFix CMMS
- Technician onboarding and management
- Performance reviews and analytics
- Asset performance monitoring
- Inventory and cost management
- Complete application control
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.db_adapter import get_db_adapter
from app.core.firestore_db import get_db_connection
from app.services.gemini_service import gemini_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manager", tags=["manager"])
templates = Jinja2Templates(directory="app/templates")


# ========== MAIN MANAGER DASHBOARD ==========


@router.get("/", response_class=HTMLResponse)
async def manager_dashboard(request: Request):
    """Comprehensive Manager Dashboard - Central Command Center"""
    conn = get_db_connection()
    try:
        # Get overview metrics
        overview_stats = {
            "total_technicians": 15,  # Mock data for demo
            "active_work_orders": 28,
            "pending_onboarding": 3,
            "critical_assets": 5,
            "overdue_maintenance": 8,
            "monthly_costs": 45250.00,
            "efficiency_score": 87.5,
            "inventory_alerts": 12,
        }

        # Get recent activities for timeline
        recent_activities = [
            {
                "type": "technician_added",
                "message": "New technician John Smith completed onboarding",
                "timestamp": datetime.now() - timedelta(hours=2),
                "priority": "normal",
            },
            {
                "type": "asset_alert",
                "message": "Pump #347 requires immediate attention",
                "timestamp": datetime.now() - timedelta(hours=4),
                "priority": "high",
            },
            {
                "type": "performance_review",
                "message": "Monthly performance reviews ready for 8 technicians",
                "timestamp": datetime.now() - timedelta(hours=6),
                "priority": "normal",
            },
            {
                "type": "cost_alert",
                "message": "Parts inventory costs exceeded budget by 12%",
                "timestamp": datetime.now() - timedelta(hours=8),
                "priority": "high",
            },
        ]

        # Get top performing technicians
        top_technicians = [
            {
                "name": "Sarah Johnson",
                "completion_rate": 96.5,
                "avg_time": 2.3,
                "rating": 4.8,
            },
            {
                "name": "Mike Rodriguez",
                "completion_rate": 94.2,
                "avg_time": 2.1,
                "rating": 4.7,
            },
            {
                "name": "Lisa Chen",
                "completion_rate": 92.8,
                "avg_time": 2.5,
                "rating": 4.6,
            },
        ]

        # Get critical assets requiring attention
        critical_assets = [
            {
                "name": "HVAC Unit #12",
                "criticality": "Critical",
                "last_service": "2024-11-15",
                "status": "Overdue",
            },
            {
                "name": "Generator #3",
                "criticality": "High",
                "last_service": "2024-11-28",
                "status": "Due Soon",
            },
            {
                "name": "Pump Station A",
                "criticality": "Critical",
                "last_service": "2024-10-30",
                "status": "Overdue",
            },
        ]

        return templates.TemplateResponse(
            "manager_dashboard.html",
            {
                "request": request,
                "overview_stats": overview_stats,
                "recent_activities": recent_activities,
                "top_technicians": top_technicians,
                "critical_assets": critical_assets,
            },
        )
    finally:
        conn.close()


# ========== TECHNICIAN MANAGEMENT ==========


@router.get("/technicians", response_class=HTMLResponse)
async def technician_management(request: Request):
    """Technician Management - Onboarding, Performance, Scheduling"""
    conn = get_db_connection()
    try:
        # Get all technicians with performance data
        technicians = [
            {
                "id": 1,
                "name": "Sarah Johnson",
                "role": "Senior Technician",
                "department": "HVAC",
                "hire_date": "2023-03-15",
                "status": "Active",
                "completion_rate": 96.5,
                "avg_response_time": 2.3,
                "customer_rating": 4.8,
                "certifications": ["HVAC Level 3", "Electrical Basic"],
                "last_training": "2024-11-01",
                "onboarding_status": "Complete",
            },
            {
                "id": 2,
                "name": "Mike Rodriguez",
                "role": "Technician",
                "department": "Mechanical",
                "hire_date": "2024-01-20",
                "status": "Active",
                "completion_rate": 94.2,
                "avg_response_time": 2.1,
                "customer_rating": 4.7,
                "certifications": ["Mechanical Repair", "Safety Level 2"],
                "last_training": "2024-10-15",
                "onboarding_status": "Complete",
            },
            {
                "id": 3,
                "name": "Jessica Wang",
                "role": "Apprentice",
                "department": "Electrical",
                "hire_date": "2024-11-15",
                "status": "Onboarding",
                "completion_rate": 0,
                "avg_response_time": 0,
                "customer_rating": 0,
                "certifications": [],
                "last_training": None,
                "onboarding_status": "In Progress",
            },
        ]

        # Get onboarding pipeline
        onboarding_pipeline = [
            {
                "name": "Jessica Wang",
                "position": "Electrical Apprentice",
                "start_date": "2024-11-15",
                "progress": 65,
                "current_module": "Electrical Safety Protocols",
                "expected_completion": "2024-12-15",
                "status": "On Track",
            },
            {
                "name": "David Kim",
                "position": "HVAC Technician",
                "start_date": "2024-12-01",
                "progress": 25,
                "current_module": "HVAC Fundamentals",
                "expected_completion": "2024-12-30",
                "status": "On Track",
            },
            {
                "name": "Maria Santos",
                "position": "Maintenance Coordinator",
                "start_date": "2024-12-05",
                "progress": 10,
                "current_module": "CMMS Overview",
                "expected_completion": "2025-01-05",
                "status": "Just Started",
            },
        ]

        return templates.TemplateResponse(
            "manager_technicians.html",
            {
                "request": request,
                "technicians": technicians,
                "onboarding_pipeline": onboarding_pipeline,
            },
        )
    finally:
        conn.close()


@router.post("/technicians/onboard")
async def start_technician_onboarding(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    department: str = Form(...),
    start_date: str = Form(...),
):
    """Start onboarding process for new technician"""
    conn = get_db_connection()
    try:
        # Create onboarding record
        onboarding_data = {
            "name": name,
            "email": email,
            "role": role,
            "department": department,
            "start_date": start_date,
            "status": "initiated",
            "progress": 0,
            "created_by": "manager",
            "created_date": datetime.now(),
        }

        # In real implementation, would save to Firestore
        logger.info(f"Started onboarding for {name} as {role}")

        return JSONResponse(
            {
                "success": True,
                "message": f"Onboarding initiated for {name}",
                "onboarding_id": "onboard_001",
            }
        )
    except Exception as e:
        logger.error(f"Error starting onboarding: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        conn.close()


# ========== PERFORMANCE ANALYTICS ==========


@router.get("/performance", response_class=HTMLResponse)
async def performance_analytics(request: Request):
    """Performance Analytics - Technician & Asset Performance"""
    conn = get_db_connection()
    try:
        # Get technician performance metrics
        technician_performance = [
            {
                "name": "Sarah Johnson",
                "work_orders_completed": 28,
                "avg_completion_time": 2.3,
                "customer_satisfaction": 4.8,
                "efficiency_score": 96.5,
                "trend": "up",
            },
            {
                "name": "Mike Rodriguez",
                "work_orders_completed": 24,
                "avg_completion_time": 2.1,
                "customer_satisfaction": 4.7,
                "efficiency_score": 94.2,
                "trend": "up",
            },
            {
                "name": "Lisa Chen",
                "work_orders_completed": 22,
                "avg_completion_time": 2.5,
                "customer_satisfaction": 4.6,
                "efficiency_score": 92.8,
                "trend": "stable",
            },
        ]

        # Get asset performance data
        asset_performance = [
            {
                "name": "HVAC Unit #12",
                "uptime": 94.5,
                "maintenance_cost": 2450.00,
                "mtbf": 720,  # Mean time between failures
                "last_failure": "2024-10-15",
                "efficiency_rating": "Good",
            },
            {
                "name": "Generator #3",
                "uptime": 98.2,
                "maintenance_cost": 1875.00,
                "mtbf": 1440,
                "last_failure": "2024-08-22",
                "efficiency_rating": "Excellent",
            },
            {
                "name": "Pump Station A",
                "uptime": 87.3,
                "maintenance_cost": 3250.00,
                "mtbf": 480,
                "last_failure": "2024-11-28",
                "efficiency_rating": "Needs Attention",
            },
        ]

        # Get department performance overview
        department_stats = [
            {
                "department": "HVAC",
                "technicians": 5,
                "avg_performance": 94.2,
                "work_orders": 45,
                "customer_rating": 4.7,
            },
            {
                "department": "Mechanical",
                "technicians": 4,
                "avg_performance": 91.8,
                "work_orders": 38,
                "customer_rating": 4.5,
            },
            {
                "department": "Electrical",
                "technicians": 3,
                "avg_performance": 89.5,
                "work_orders": 28,
                "customer_rating": 4.4,
            },
        ]

        return templates.TemplateResponse(
            "manager_performance.html",
            {
                "request": request,
                "technician_performance": technician_performance,
                "asset_performance": asset_performance,
                "department_stats": department_stats,
            },
        )
    finally:
        conn.close()


# ========== ASSET MONITORING ==========


@router.get("/assets", response_class=HTMLResponse)
async def asset_monitoring(request: Request):
    """Asset Performance Monitoring & Management"""
    conn = get_db_connection()
    try:
        # Get asset overview with health scores
        assets_overview = [
            {
                "id": 1,
                "name": "HVAC Unit #12",
                "type": "HVAC System",
                "location": "Building A - Floor 3",
                "health_score": 75,
                "status": "Needs Attention",
                "last_service": "2024-11-15",
                "next_service": "2024-12-15",
                "total_cost_ytd": 4250.00,
                "downtime_hours": 12.5,
                "criticality": "Critical",
            },
            {
                "id": 2,
                "name": "Generator #3",
                "type": "Power Generation",
                "location": "Basement Mechanical Room",
                "health_score": 92,
                "status": "Excellent",
                "last_service": "2024-11-28",
                "next_service": "2025-02-28",
                "total_cost_ytd": 1875.00,
                "downtime_hours": 2.0,
                "criticality": "Critical",
            },
            {
                "id": 3,
                "name": "Pump Station A",
                "type": "Water System",
                "location": "Utility Building",
                "health_score": 58,
                "status": "Poor",
                "last_service": "2024-10-30",
                "next_service": "2024-12-10",
                "total_cost_ytd": 6750.00,
                "downtime_hours": 28.5,
                "criticality": "High",
            },
        ]

        # Get maintenance schedule
        maintenance_schedule = [
            {
                "asset": "HVAC Unit #12",
                "type": "Preventive",
                "scheduled_date": "2024-12-15",
                "technician": "Sarah Johnson",
                "estimated_duration": 4,
                "status": "Scheduled",
            },
            {
                "asset": "Pump Station A",
                "type": "Corrective",
                "scheduled_date": "2024-12-10",
                "technician": "Mike Rodriguez",
                "estimated_duration": 6,
                "status": "Urgent",
            },
            {
                "asset": "Elevator #2",
                "type": "Inspection",
                "scheduled_date": "2024-12-12",
                "technician": "Lisa Chen",
                "estimated_duration": 2,
                "status": "Scheduled",
            },
        ]

        # Get cost analysis by asset category
        cost_analysis = [
            {
                "category": "HVAC Systems",
                "total_cost": 18500.00,
                "percentage": 35.2,
                "trend": "up",
            },
            {
                "category": "Electrical",
                "total_cost": 12750.00,
                "percentage": 24.3,
                "trend": "stable",
            },
            {
                "category": "Mechanical",
                "total_cost": 15200.00,
                "percentage": 28.9,
                "trend": "down",
            },
            {
                "category": "Plumbing",
                "total_cost": 6100.00,
                "percentage": 11.6,
                "trend": "stable",
            },
        ]

        return templates.TemplateResponse(
            "manager_assets.html",
            {
                "request": request,
                "assets_overview": assets_overview,
                "maintenance_schedule": maintenance_schedule,
                "cost_analysis": cost_analysis,
            },
        )
    finally:
        conn.close()


# ========== INVENTORY & COST MANAGEMENT ==========


@router.get("/inventory", response_class=HTMLResponse)
async def inventory_management(request: Request):
    """Inventory & Cost Management Dashboard"""
    conn = get_db_connection()
    try:
        # Get inventory overview
        inventory_overview = [
            {
                "part_number": "HVAC-FLT-001",
                "name": "HVAC Air Filter - Standard",
                "category": "HVAC",
                "current_stock": 25,
                "min_stock": 10,
                "max_stock": 50,
                "unit_cost": 45.50,
                "total_value": 1137.50,
                "status": "In Stock",
                "supplier": "HVAC Supply Co",
                "last_ordered": "2024-11-15",
            },
            {
                "part_number": "ELE-SW-205",
                "name": "Circuit Breaker 20A",
                "category": "Electrical",
                "current_stock": 5,
                "min_stock": 8,
                "max_stock": 25,
                "unit_cost": 125.00,
                "total_value": 625.00,
                "status": "Low Stock",
                "supplier": "Electrical Parts Plus",
                "last_ordered": "2024-10-28",
            },
            {
                "part_number": "PMP-SL-440",
                "name": "Pump Seal Kit",
                "category": "Mechanical",
                "current_stock": 0,
                "min_stock": 3,
                "max_stock": 15,
                "unit_cost": 285.00,
                "total_value": 0.00,
                "status": "Out of Stock",
                "supplier": "Industrial Pump Supply",
                "last_ordered": "2024-09-15",
            },
        ]

        # Get cost breakdown by month
        monthly_costs = [
            {
                "month": "Nov 2024",
                "labor": 15250.00,
                "parts": 8975.00,
                "external": 3200.00,
                "total": 27425.00,
            },
            {
                "month": "Oct 2024",
                "labor": 16800.00,
                "parts": 12450.00,
                "external": 2750.00,
                "total": 32000.00,
            },
            {
                "month": "Sep 2024",
                "labor": 14600.00,
                "parts": 9875.00,
                "external": 4100.00,
                "total": 28575.00,
            },
            {
                "month": "Aug 2024",
                "labor": 15950.00,
                "parts": 11250.00,
                "external": 1850.00,
                "total": 29050.00,
            },
        ]

        # Get supplier performance
        supplier_performance = [
            {
                "name": "HVAC Supply Co",
                "orders": 12,
                "on_time_delivery": 95.8,
                "quality_rating": 4.7,
                "total_spent": 18750.00,
            },
            {
                "name": "Electrical Parts Plus",
                "orders": 8,
                "on_time_delivery": 88.5,
                "quality_rating": 4.3,
                "total_spent": 12450.00,
            },
            {
                "name": "Industrial Pump Supply",
                "orders": 6,
                "on_time_delivery": 92.3,
                "quality_rating": 4.8,
                "total_spent": 9875.00,
            },
        ]

        # Get pending purchase orders
        pending_orders = [
            {
                "po_number": "PO-2024-0158",
                "supplier": "HVAC Supply Co",
                "items": 5,
                "total_amount": 2450.00,
                "order_date": "2024-12-03",
                "expected_delivery": "2024-12-10",
                "status": "Approved",
            },
            {
                "po_number": "PO-2024-0159",
                "supplier": "Electrical Parts Plus",
                "items": 8,
                "total_amount": 1875.00,
                "order_date": "2024-12-05",
                "expected_delivery": "2024-12-12",
                "status": "Pending Approval",
            },
        ]

        return templates.TemplateResponse(
            "manager_inventory.html",
            {
                "request": request,
                "inventory_overview": inventory_overview,
                "monthly_costs": monthly_costs,
                "supplier_performance": supplier_performance,
                "pending_orders": pending_orders,
            },
        )
    finally:
        conn.close()


# ========== REPORTS & ANALYTICS ==========


@router.get("/reports", response_class=HTMLResponse)
async def reports_analytics(request: Request):
    """Comprehensive Reports & Analytics"""
    conn = get_db_connection()
    try:
        # Get KPI summary
        kpis = {
            "mttr": 4.2,  # Mean Time To Repair (hours)
            "mtbf": 168,  # Mean Time Between Failures (hours)
            "asset_uptime": 94.7,  # Overall asset uptime percentage
            "work_order_completion": 87.3,  # Work order completion rate
            "cost_variance": -8.2,  # Cost variance from budget
            "technician_utilization": 78.5,  # Technician utilization rate
            "customer_satisfaction": 4.6,  # Average customer satisfaction
            "preventive_maintenance": 65.8,  # Preventive maintenance percentage
        }

        # Get trending data for charts
        performance_trends = [
            {"period": "Q4 2023", "uptime": 92.1, "costs": 125000, "satisfaction": 4.3},
            {"period": "Q1 2024", "uptime": 93.5, "costs": 118000, "satisfaction": 4.4},
            {"period": "Q2 2024", "uptime": 94.2, "costs": 115000, "satisfaction": 4.5},
            {"period": "Q3 2024", "uptime": 94.7, "costs": 112000, "satisfaction": 4.6},
        ]

        return templates.TemplateResponse(
            "manager_reports.html",
            {
                "request": request,
                "kpis": kpis,
                "performance_trends": performance_trends,
            },
        )
    finally:
        conn.close()


# ========== SYSTEM ADMINISTRATION ==========


@router.get("/admin", response_class=HTMLResponse)
async def system_administration(request: Request):
    """System Administration & Settings"""
    conn = get_db_connection()
    try:
        # Get system health metrics
        system_health = {
            "database_status": "Healthy",
            "api_response_time": 245,  # milliseconds
            "active_users": 28,
            "system_uptime": 99.7,
            "last_backup": "2024-12-06 02:00:00",
            "storage_used": 67.3,  # percentage
            "cpu_usage": 23.5,
            "memory_usage": 41.2,
        }

        # Get user management data
        user_summary = {
            "total_users": 35,
            "active_users": 28,
            "managers": 3,
            "technicians": 15,
            "admin_users": 2,
            "pending_approvals": 2,
        }

        return templates.TemplateResponse(
            "manager_admin.html",
            {
                "request": request,
                "system_health": system_health,
                "user_summary": user_summary,
            },
        )
    finally:
        conn.close()


# ========== API ENDPOINTS ==========


@router.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """API endpoint for real-time dashboard statistics"""
    return JSONResponse(
        {
            "active_work_orders": 28,
            "pending_maintenance": 12,
            "technicians_available": 8,
            "critical_alerts": 3,
            "system_efficiency": 87.5,
            "monthly_budget_used": 78.3,
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.post("/api/technician/{technician_id}/performance-review")
async def create_performance_review(
    technician_id: int,
    rating: float = Form(...),
    comments: str = Form(...),
    goals: str = Form(...),
):
    """Create performance review for technician"""
    try:
        review_data = {
            "technician_id": technician_id,
            "rating": rating,
            "comments": comments,
            "goals": goals,
            "review_date": datetime.now(),
            "reviewer": "manager",
        }

        # In real implementation, save to Firestore
        logger.info(f"Performance review created for technician {technician_id}")

        return JSONResponse(
            {"success": True, "message": "Performance review saved successfully"}
        )
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/api/asset/{asset_id}/schedule-maintenance")
async def schedule_asset_maintenance(
    asset_id: int,
    maintenance_type: str = Form(...),
    scheduled_date: str = Form(...),
    technician_id: int = Form(...),
    priority: str = Form(...),
):
    """Schedule maintenance for asset"""
    try:
        maintenance_data = {
            "asset_id": asset_id,
            "maintenance_type": maintenance_type,
            "scheduled_date": scheduled_date,
            "technician_id": technician_id,
            "priority": priority,
            "status": "scheduled",
            "created_by": "manager",
        }

        # In real implementation, save to Firestore and notify technician
        logger.info(f"Maintenance scheduled for asset {asset_id}")

        return JSONResponse(
            {"success": True, "message": "Maintenance scheduled successfully"}
        )
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
