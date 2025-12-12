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


# ========== EDITABLE TABLE VIEWS ==========


@router.get("/table/work-orders", response_class=HTMLResponse)
async def work_orders_table_view(request: Request):
    """Editable table view for work orders with bulk operations"""
    try:
        db_adapter = get_db_adapter()
        work_orders = []

        if db_adapter.firestore_manager:
            # Get work orders from Firestore
            work_orders_data = await db_adapter.firestore_manager.get_collection(
                "work_orders", order_by="-created_date"
            )
            work_orders = work_orders_data
        else:
            # Mock data for demonstration
            work_orders = [
                {
                    "id": "wo_001",
                    "title": "HVAC Unit #12 Maintenance",
                    "description": "Replace filters and check refrigerant levels",
                    "priority": "High",
                    "status": "Open",
                    "assigned_to": "Sarah Johnson",
                    "due_date": "2024-12-15",
                    "created_date": "2024-12-01",
                    "estimated_hours": 4.0,
                    "asset_name": "HVAC Unit #12",
                },
                {
                    "id": "wo_002",
                    "title": "Pump Station A Repair",
                    "description": "Fix pump seal leak",
                    "priority": "Critical",
                    "status": "In Progress",
                    "assigned_to": "Mike Rodriguez",
                    "due_date": "2024-12-10",
                    "created_date": "2024-11-28",
                    "estimated_hours": 6.0,
                    "asset_name": "Pump Station A",
                },
                {
                    "id": "wo_003",
                    "title": "Generator #3 Inspection",
                    "description": "Monthly preventive maintenance inspection",
                    "priority": "Medium",
                    "status": "Scheduled",
                    "assigned_to": "Lisa Chen",
                    "due_date": "2024-12-20",
                    "created_date": "2024-12-05",
                    "estimated_hours": 2.0,
                    "asset_name": "Generator #3",
                },
            ]

        return templates.TemplateResponse(
            "manager_work_orders_table.html",
            {"request": request, "work_orders": work_orders},
        )
    except Exception as e:
        logger.error(f"Error loading work orders table: {e}")
        return templates.TemplateResponse(
            "manager_work_orders_table.html",
            {"request": request, "work_orders": [], "error": str(e)},
        )


@router.get("/table/assets", response_class=HTMLResponse)
async def assets_table_view(request: Request):
    """Editable table view for assets with bulk operations"""
    try:
        db_adapter = get_db_adapter()
        assets = []

        if db_adapter.firestore_manager:
            assets_data = await db_adapter.firestore_manager.get_collection(
                "assets", order_by="name"
            )
            assets = assets_data
        else:
            # Mock data
            assets = [
                {
                    "id": "asset_001",
                    "name": "HVAC Unit #12",
                    "asset_tag": "HVAC-012",
                    "location": "Building A - Floor 3",
                    "status": "Active",
                    "criticality": "Critical",
                    "manufacturer": "Trane",
                    "model": "XV20i",
                    "purchase_date": "2020-03-15",
                    "warranty_expiry": "2025-03-15",
                    "last_service_date": "2024-11-15",
                    "next_service_date": "2024-12-15",
                },
                {
                    "id": "asset_002",
                    "name": "Generator #3",
                    "asset_tag": "GEN-003",
                    "location": "Basement Mechanical Room",
                    "status": "Active",
                    "criticality": "Critical",
                    "manufacturer": "Caterpillar",
                    "model": "C18",
                    "purchase_date": "2019-08-20",
                    "warranty_expiry": "2024-08-20",
                    "last_service_date": "2024-11-28",
                    "next_service_date": "2025-02-28",
                },
                {
                    "id": "asset_003",
                    "name": "Pump Station A",
                    "asset_tag": "PMP-A01",
                    "location": "Utility Building",
                    "status": "Needs Attention",
                    "criticality": "High",
                    "manufacturer": "Grundfos",
                    "model": "CR64-4",
                    "purchase_date": "2018-05-10",
                    "warranty_expiry": "2023-05-10",
                    "last_service_date": "2024-10-30",
                    "next_service_date": "2024-12-10",
                },
            ]

        return templates.TemplateResponse(
            "manager_assets_table.html", {"request": request, "assets": assets}
        )
    except Exception as e:
        logger.error(f"Error loading assets table: {e}")
        return templates.TemplateResponse(
            "manager_assets_table.html",
            {"request": request, "assets": [], "error": str(e)},
        )


@router.get("/table/parts", response_class=HTMLResponse)
async def parts_table_view(request: Request):
    """Editable table view for parts/inventory with bulk operations"""
    try:
        db_adapter = get_db_adapter()
        parts = []

        if db_adapter.firestore_manager:
            parts_data = await db_adapter.firestore_manager.get_collection(
                "parts", order_by="name"
            )
            parts = parts_data
        else:
            # Mock data
            parts = [
                {
                    "id": "part_001",
                    "name": "HVAC Air Filter - Standard",
                    "part_number": "HVAC-FLT-001",
                    "category": "HVAC",
                    "current_stock": 25,
                    "minimum_stock": 10,
                    "maximum_stock": 50,
                    "unit_cost": 45.50,
                    "supplier": "HVAC Supply Co",
                    "location": "Warehouse A-1",
                    "last_ordered": "2024-11-15",
                },
                {
                    "id": "part_002",
                    "name": "Circuit Breaker 20A",
                    "part_number": "ELE-SW-205",
                    "category": "Electrical",
                    "current_stock": 5,
                    "minimum_stock": 8,
                    "maximum_stock": 25,
                    "unit_cost": 125.00,
                    "supplier": "Electrical Parts Plus",
                    "location": "Warehouse B-3",
                    "last_ordered": "2024-10-28",
                },
                {
                    "id": "part_003",
                    "name": "Pump Seal Kit",
                    "part_number": "PMP-SL-440",
                    "category": "Mechanical",
                    "current_stock": 0,
                    "minimum_stock": 3,
                    "maximum_stock": 15,
                    "unit_cost": 285.00,
                    "supplier": "Industrial Pump Supply",
                    "location": "Warehouse C-2",
                    "last_ordered": "2024-09-15",
                },
            ]

        return templates.TemplateResponse(
            "manager_parts_table.html", {"request": request, "parts": parts}
        )
    except Exception as e:
        logger.error(f"Error loading parts table: {e}")
        return templates.TemplateResponse(
            "manager_parts_table.html",
            {"request": request, "parts": [], "error": str(e)},
        )


# ========== BULK OPERATIONS ==========


@router.post("/api/bulk-update")
async def bulk_update(
    entity_type: str = Form(...),  # "work_orders", "assets", or "parts"
    updates: str = Form(...),  # JSON string of updates
):
    """Handle bulk updates for table entities"""
    try:
        updates_data = json.loads(updates)
        db_adapter = get_db_adapter()

        success_count = 0
        error_count = 0
        errors = []

        for update in updates_data:
            try:
                entity_id = update.get("id")
                fields = update.get("fields", {})

                if db_adapter.firestore_manager:
                    await db_adapter.firestore_manager.update_document(
                        entity_type, entity_id, fields
                    )
                    success_count += 1
                else:
                    # Mock update
                    success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Failed to update {entity_id}: {str(e)}")

        return JSONResponse(
            {
                "success": error_count == 0,
                "message": f"Updated {success_count} items, {error_count} errors",
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
            }
        )

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/api/bulk-delete")
async def bulk_delete(
    entity_type: str = Form(...),
    ids: str = Form(...),  # JSON array of IDs to delete
):
    """Handle bulk deletion for table entities"""
    try:
        ids_list = json.loads(ids)
        db_adapter = get_db_adapter()

        success_count = 0
        error_count = 0
        errors = []

        for entity_id in ids_list:
            try:
                if db_adapter.firestore_manager:
                    await db_adapter.firestore_manager.delete_document(
                        entity_type, entity_id
                    )
                    success_count += 1
                else:
                    # Mock delete
                    success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Failed to delete {entity_id}: {str(e)}")

        return JSONResponse(
            {
                "success": error_count == 0,
                "message": f"Deleted {success_count} items, {error_count} errors",
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
            }
        )

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ========== FILE UPLOAD & BULK IMPORT ==========


@router.get("/bulk-import", response_class=HTMLResponse)
async def bulk_import_page(request: Request):
    """Bulk import page for uploading CSV/Excel files"""
    return templates.TemplateResponse("manager_bulk_import.html", {"request": request})


@router.post("/api/upload/work-orders")
async def upload_work_orders_file(file: UploadFile = File(...)):
    """Upload and process work orders CSV/Excel file"""
    try:
        if not file.filename:
            return JSONResponse(
                {"success": False, "error": "No file provided"}, status_code=400
            )

        # Read file content
        content = await file.read()

        # Process CSV content (simplified for demo)
        import csv
        import io

        results = []
        errors = []

        # Decode content
        text_content = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(text_content))

        db_adapter = get_db_adapter()
        success_count = 0

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                work_order_data = {
                    "title": row.get("title", ""),
                    "description": row.get("description", ""),
                    "priority": row.get("priority", "Medium"),
                    "assigned_to": row.get("assigned_to", ""),
                    "due_date": row.get("due_date", ""),
                    "asset_id": row.get("asset_id", ""),
                    "status": "Open",
                    "created_date": datetime.now().isoformat(),
                    "created_by": "bulk_import",
                }

                if db_adapter.firestore_manager:
                    wo_id = await db_adapter.firestore_manager.create_document(
                        "work_orders", work_order_data
                    )
                    results.append(
                        {"row": row_num, "id": wo_id, "title": work_order_data["title"]}
                    )
                    success_count += 1
                else:
                    # Mock creation
                    results.append(
                        {
                            "row": row_num,
                            "id": f"wo_{row_num}",
                            "title": work_order_data["title"],
                        }
                    )
                    success_count += 1

            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        return JSONResponse(
            {
                "success": len(errors) == 0,
                "message": f"Processed {success_count} work orders, {len(errors)} errors",
                "success_count": success_count,
                "error_count": len(errors),
                "results": results,
                "errors": errors,
            }
        )

    except Exception as e:
        return JSONResponse(
            {"success": False, "error": f"File processing error: {str(e)}"},
            status_code=500,
        )


@router.post("/api/upload/parts")
async def upload_parts_file(file: UploadFile = File(...)):
    """Upload and process parts inventory CSV/Excel file"""
    try:
        if not file.filename:
            return JSONResponse(
                {"success": False, "error": "No file provided"}, status_code=400
            )

        content = await file.read()

        import csv
        import io

        results = []
        errors = []

        text_content = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(text_content))

        db_adapter = get_db_adapter()
        success_count = 0

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                part_data = {
                    "name": row.get("name", ""),
                    "part_number": row.get("part_number", ""),
                    "category": row.get("category", ""),
                    "current_stock": int(row.get("current_stock", 0)),
                    "minimum_stock": int(row.get("minimum_stock", 0)),
                    "maximum_stock": int(row.get("maximum_stock", 0)),
                    "unit_cost": float(row.get("unit_cost", 0)),
                    "supplier": row.get("supplier", ""),
                    "location": row.get("location", ""),
                    "created_date": datetime.now().isoformat(),
                }

                if db_adapter.firestore_manager:
                    part_id = await db_adapter.firestore_manager.create_document(
                        "parts", part_data
                    )
                    results.append(
                        {"row": row_num, "id": part_id, "name": part_data["name"]}
                    )
                    success_count += 1
                else:
                    results.append(
                        {
                            "row": row_num,
                            "id": f"part_{row_num}",
                            "name": part_data["name"],
                        }
                    )
                    success_count += 1

            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        return JSONResponse(
            {
                "success": len(errors) == 0,
                "message": f"Processed {success_count} parts, {len(errors)} errors",
                "success_count": success_count,
                "error_count": len(errors),
                "results": results,
                "errors": errors,
            }
        )

    except Exception as e:
        return JSONResponse(
            {"success": False, "error": f"File processing error: {str(e)}"},
            status_code=500,
        )


@router.post("/api/upload/pm-schedules")
async def upload_pm_schedules_file(file: UploadFile = File(...)):
    """Upload and process PM schedules CSV/Excel file"""
    try:
        if not file.filename:
            return JSONResponse(
                {"success": False, "error": "No file provided"}, status_code=400
            )

        content = await file.read()

        import csv
        import io

        results = []
        errors = []

        text_content = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(text_content))

        db_adapter = get_db_adapter()
        success_count = 0

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                pm_data = {
                    "asset_id": row.get("asset_id", ""),
                    "asset_name": row.get("asset_name", ""),
                    "task_name": row.get("task_name", ""),
                    "frequency": row.get("frequency", "monthly"),
                    "estimated_hours": float(row.get("estimated_hours", 1)),
                    "assigned_to": row.get("assigned_to", ""),
                    "next_due_date": row.get("next_due_date", ""),
                    "instructions": row.get("instructions", ""),
                    "priority": row.get("priority", "Medium"),
                    "status": "Active",
                    "created_date": datetime.now().isoformat(),
                }

                if db_adapter.firestore_manager:
                    pm_id = await db_adapter.firestore_manager.create_document(
                        "pm_schedules", pm_data
                    )
                    results.append(
                        {"row": row_num, "id": pm_id, "task": pm_data["task_name"]}
                    )
                    success_count += 1
                else:
                    results.append(
                        {
                            "row": row_num,
                            "id": f"pm_{row_num}",
                            "task": pm_data["task_name"],
                        }
                    )
                    success_count += 1

            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        return JSONResponse(
            {
                "success": len(errors) == 0,
                "message": f"Processed {success_count} PM schedules, {len(errors)} errors",
                "success_count": success_count,
                "error_count": len(errors),
                "results": results,
                "errors": errors,
            }
        )

    except Exception as e:
        return JSONResponse(
            {"success": False, "error": f"File processing error: {str(e)}"},
            status_code=500,
        )


# ========== TECHNICIAN ANALYTICS ==========


@router.get("/analytics/technicians", response_class=HTMLResponse)
async def technician_analytics(request: Request):
    """Advanced technician performance analytics and tracking"""
    return templates.TemplateResponse(
        "manager_technician_analytics.html", {"request": request}
    )


@router.get("/api/technician-performance")
async def get_technician_performance_data(
    period: str = "30", department: str = "all", performance_filter: str = "all"
):
    """API endpoint for technician performance data"""
    try:
        db_adapter = get_db_adapter()

        # Mock performance data - in real implementation would query Firestore
        performance_data = [
            {
                "id": "tech1",
                "name": "Sarah Johnson",
                "department": "HVAC",
                "role": "Senior Technician",
                "work_orders_completed": 45,
                "efficiency_rating": 96.5,
                "avg_response_time": 1.8,
                "customer_rating": 4.9,
                "performance_level": "excellent",
                "trend": "up",
            },
            {
                "id": "tech2",
                "name": "Mike Rodriguez",
                "department": "Mechanical",
                "role": "Technician",
                "work_orders_completed": 38,
                "efficiency_rating": 89.2,
                "avg_response_time": 2.1,
                "customer_rating": 4.2,
                "performance_level": "good",
                "trend": "stable",
            },
            {
                "id": "tech3",
                "name": "Lisa Chen",
                "department": "Electrical",
                "role": "Technician",
                "work_orders_completed": 32,
                "efficiency_rating": 75.8,
                "avg_response_time": 3.2,
                "customer_rating": 3.8,
                "performance_level": "average",
                "trend": "down",
            },
        ]

        # Apply filters
        if department != "all":
            performance_data = [
                t for t in performance_data if t["department"].lower() == department
            ]

        if performance_filter != "all":
            if performance_filter == "excellent":
                performance_data = [
                    t for t in performance_data if t["efficiency_rating"] >= 90
                ]
            elif performance_filter == "good":
                performance_data = [
                    t for t in performance_data if 80 <= t["efficiency_rating"] < 90
                ]
            elif performance_filter == "average":
                performance_data = [
                    t for t in performance_data if 70 <= t["efficiency_rating"] < 80
                ]
            elif performance_filter == "needs-improvement":
                performance_data = [
                    t for t in performance_data if t["efficiency_rating"] < 70
                ]

        return JSONResponse(
            {
                "success": True,
                "data": performance_data,
                "summary": {
                    "total_technicians": len(performance_data),
                    "avg_efficiency": (
                        sum(t["efficiency_rating"] for t in performance_data)
                        / len(performance_data)
                        if performance_data
                        else 0
                    ),
                    "avg_response_time": (
                        sum(t["avg_response_time"] for t in performance_data)
                        / len(performance_data)
                        if performance_data
                        else 0
                    ),
                    "avg_rating": (
                        sum(t["customer_rating"] for t in performance_data)
                        / len(performance_data)
                        if performance_data
                        else 0
                    ),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error fetching technician performance data: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ========== PM SCHEDULE MANAGEMENT ==========


@router.get("/pm-schedules", response_class=HTMLResponse)
async def pm_schedule_management(request: Request):
    """Preventive Maintenance Schedule Management"""
    return templates.TemplateResponse("manager_pm_schedules.html", {"request": request})


@router.get("/api/pm-schedules")
async def get_pm_schedules(
    status: str = "all", frequency: str = "all", asset_type: str = "all"
):
    """API endpoint for PM schedule data"""
    try:
        db_adapter = get_db_adapter()

        # Mock PM schedule data - in real implementation would query Firestore
        pm_schedules = [
            {
                "id": "pm1",
                "asset_id": "hvac12",
                "asset_name": "HVAC Unit #12",
                "asset_location": "Building A - Floor 3",
                "asset_type": "HVAC",
                "task_name": "Filter Replacement",
                "task_description": "Replace air filters and check refrigerant levels",
                "frequency": "monthly",
                "next_due_date": "2024-12-15",
                "assigned_to": "Sarah Johnson",
                "status": "overdue",
                "priority": "high",
                "estimated_hours": 2.0,
                "required_parts": ["HVAC-FLT-001"],
                "instructions": "Replace air filters according to manufacturer specs",
                "automation_enabled": True,
            },
            {
                "id": "pm2",
                "asset_id": "gen3",
                "asset_name": "Generator #3",
                "asset_location": "Basement Mechanical Room",
                "asset_type": "Electrical",
                "task_name": "Weekly Inspection",
                "task_description": "Check oil levels, test operation, visual inspection",
                "frequency": "weekly",
                "next_due_date": "2024-12-20",
                "assigned_to": "Mike Rodriguez",
                "status": "active",
                "priority": "medium",
                "estimated_hours": 1.5,
                "required_parts": [],
                "instructions": "Follow weekly inspection checklist",
                "automation_enabled": True,
            },
            {
                "id": "pm3",
                "asset_id": "pump1",
                "asset_name": "Pump Station A",
                "asset_location": "Utility Building",
                "asset_type": "Mechanical",
                "task_name": "Quarterly Service",
                "task_description": "Lubricate bearings, check alignment, replace seals if needed",
                "frequency": "quarterly",
                "next_due_date": "2025-01-15",
                "assigned_to": "Lisa Chen",
                "status": "active",
                "priority": "low",
                "estimated_hours": 4.0,
                "required_parts": ["PMP-SL-440"],
                "instructions": "Complete quarterly maintenance checklist",
                "automation_enabled": False,
            },
        ]

        # Apply filters
        if status != "all":
            pm_schedules = [s for s in pm_schedules if s["status"] == status]

        if frequency != "all":
            pm_schedules = [s for s in pm_schedules if s["frequency"] == frequency]

        if asset_type != "all":
            pm_schedules = [
                s for s in pm_schedules if s["asset_type"].lower() == asset_type.lower()
            ]

        return JSONResponse(
            {
                "success": True,
                "data": pm_schedules,
                "summary": {
                    "total_schedules": len(pm_schedules),
                    "active_schedules": len(
                        [s for s in pm_schedules if s["status"] == "active"]
                    ),
                    "overdue_schedules": len(
                        [s for s in pm_schedules if s["status"] == "overdue"]
                    ),
                    "automation_rate": (
                        len([s for s in pm_schedules if s["automation_enabled"]])
                        / len(pm_schedules)
                        * 100
                        if pm_schedules
                        else 0
                    ),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error fetching PM schedules: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/api/pm-schedules")
async def create_pm_schedule(
    asset_id: str = Form(...),
    task_name: str = Form(...),
    frequency: str = Form(...),
    assigned_to: str = Form(...),
    priority: str = Form(...),
    start_date: str = Form(...),
    estimated_hours: float = Form(...),
    instructions: str = Form(...),
):
    """Create a new PM schedule"""
    try:
        db_adapter = get_db_adapter()

        schedule_data = {
            "asset_id": asset_id,
            "task_name": task_name,
            "frequency": frequency,
            "assigned_to": assigned_to,
            "priority": priority,
            "start_date": start_date,
            "estimated_hours": estimated_hours,
            "instructions": instructions,
            "status": "active",
            "automation_enabled": True,
            "created_date": datetime.now().isoformat(),
            "created_by": "manager",
        }

        if db_adapter.firestore_manager:
            schedule_id = await db_adapter.firestore_manager.create_document(
                "pm_schedules", schedule_data
            )
        else:
            # Mock creation
            schedule_id = f"pm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return JSONResponse(
            {
                "success": True,
                "message": "PM schedule created successfully",
                "schedule_id": schedule_id,
            }
        )

    except Exception as e:
        logger.error(f"Error creating PM schedule: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/api/pm-schedules/{schedule_id}/run-now")
async def run_pm_schedule_now(schedule_id: str):
    """Create immediate work order from PM schedule"""
    try:
        db_adapter = get_db_adapter()

        # Get schedule details
        if db_adapter.firestore_manager:
            schedule = await db_adapter.firestore_manager.get_document(
                "pm_schedules", schedule_id
            )
        else:
            # Mock schedule data
            schedule = {
                "asset_id": "hvac12",
                "task_name": "Filter Replacement",
                "assigned_to": "Sarah Johnson",
                "estimated_hours": 2.0,
                "instructions": "Replace air filters according to manufacturer specs",
            }

        # Create work order
        work_order_data = {
            "title": f"PM: {schedule['task_name']}",
            "description": f"Preventive maintenance task: {schedule['task_name']}",
            "priority": "High",
            "asset_id": schedule["asset_id"],
            "assigned_to": schedule["assigned_to"],
            "estimated_hours": schedule["estimated_hours"],
            "work_instructions": schedule["instructions"],
            "status": "Open",
            "work_order_type": "Preventive",
            "created_date": datetime.now().isoformat(),
            "created_by": "pm_automation",
            "pm_schedule_id": schedule_id,
        }

        if db_adapter.firestore_manager:
            wo_id = await db_adapter.firestore_manager.create_document(
                "work_orders", work_order_data
            )
        else:
            wo_id = f"wo_pm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return JSONResponse(
            {
                "success": True,
                "message": "Work order created successfully",
                "work_order_id": wo_id,
            }
        )

    except Exception as e:
        logger.error(f"Error running PM schedule: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


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
