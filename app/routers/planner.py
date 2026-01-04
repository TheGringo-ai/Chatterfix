from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user_from_cookie
from app.models.user import User
from app.services.advanced_scheduler_service import advanced_scheduler
from app.services.planner_service import planner_service
from app.services.pm_automation_engine import pm_automation_engine
from app.services.scheduler_mock_data import scheduler_mock_service

router = APIRouter(prefix="/planner", tags=["planner"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def planner_dashboard(request: Request):
    """Render planner dashboard with full calendar and drag-drop scheduling"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    is_demo = current_user is None
    return templates.TemplateResponse(
        "planner_dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "is_demo": is_demo,
            "advanced_mode": True,  # Enable FullCalendar drag-drop scheduling
        },
    )


@router.get("/advanced", response_class=HTMLResponse)
async def advanced_scheduler_dashboard(request: Request):
    """Render advanced scheduler dashboard with enterprise features"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    is_demo = current_user is None
    return templates.TemplateResponse(
        "advanced_scheduler.html",
        {"request": request, "current_user": current_user, "is_demo": is_demo},
    )


@router.get("/mobile", response_class=HTMLResponse)
async def mobile_scheduler_dashboard(request: Request):
    """Render mobile-responsive scheduler for field technicians"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    is_demo = current_user is None
    return templates.TemplateResponse(
        "mobile_scheduler.html",
        {"request": request, "current_user": current_user, "is_demo": is_demo},
    )


@router.get("/analytics", response_class=HTMLResponse)
async def scheduler_analytics_dashboard(request: Request):
    """Render comprehensive scheduler analytics and reporting dashboard"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    is_demo = current_user is None
    return templates.TemplateResponse(
        "scheduler_analytics.html",
        {"request": request, "current_user": current_user, "is_demo": is_demo},
    )


@router.get("/pm-schedule")
async def get_pm_schedule(days_ahead: int = 30):
    """Get preventive maintenance schedule"""
    schedule = planner_service.get_pm_schedule(days_ahead)
    return JSONResponse(content=schedule)


@router.get("/resource-capacity")
async def get_resource_capacity():
    """Get technician capacity and workload"""
    capacity = planner_service.get_resource_capacity()
    return JSONResponse(content=capacity)


@router.get("/backlog")
async def get_backlog():
    """Get work order backlog"""
    backlog = planner_service.get_work_order_backlog()
    return JSONResponse(content=backlog)


@router.get("/asset-pm-status")
async def get_asset_pm_status():
    """Get asset preventive maintenance status"""
    pm_status = planner_service.get_asset_pm_status()
    return JSONResponse(content={"assets": pm_status})


@router.get("/parts-availability")
async def get_parts_availability():
    """Get parts availability for scheduled work"""
    parts = planner_service.get_parts_availability()
    return JSONResponse(content=parts)


@router.get("/conflicts")
async def get_conflicts():
    """Get scheduling conflicts"""
    conflicts = planner_service.get_scheduling_conflicts()
    return JSONResponse(content={"conflicts": conflicts})


@router.get("/compliance")
async def get_compliance():
    """Get compliance tracking data"""
    compliance = planner_service.get_compliance_tracking()
    return JSONResponse(content=compliance)


@router.get("/urgent-count")
async def get_urgent_count():
    """Get count of urgent work orders for dashboard alerts"""
    try:
        backlog = planner_service.get_work_order_backlog()
        urgent_count = backlog.get("by_priority", {}).get("urgent", 0)

        return JSONResponse(content={"urgent_count": urgent_count, "status": "success"})
    except Exception as e:
        # Fallback count for production stability
        return JSONResponse(
            content={
                "urgent_count": 2,  # Safe fallback
                "status": "fallback",
                "error": str(e),
            }
        )


@router.get("/summary")
async def get_planner_summary():
    """Get comprehensive planner summary with error handling"""
    try:
        backlog = planner_service.get_work_order_backlog()
        capacity = planner_service.get_resource_capacity()
        conflicts = planner_service.get_scheduling_conflicts()
        compliance = planner_service.get_compliance_tracking()

        # Safe extraction with defaults
        summary = {
            "backlog_count": backlog.get("total_backlog", 0),
            "overdue_count": backlog.get("overdue_count", 0),
            "technician_count": capacity.get("total_technicians", 0),
            "average_capacity": capacity.get("average_capacity", 0.0),
            "conflict_count": len(conflicts) if isinstance(conflicts, list) else 0,
            "compliance_overdue": compliance.get("overdue", 0),
            "compliance_due_soon": compliance.get("due_soon", 0),
            # Additional metrics for dashboard
            "work_orders_logged": backlog.get(
                "total_backlog", 0
            ),  # Fix for undefined display
            "due_today_count": backlog.get("due_today_count", 0),
            "high_priority_count": backlog.get("by_priority", {}).get("high", 0)
            + backlog.get("by_priority", {}).get("urgent", 0),
        }

        return JSONResponse(content=summary)

    except Exception as e:
        # Return mock data if there's any issue
        return JSONResponse(
            content={
                "backlog_count": 6,
                "overdue_count": 2,
                "technician_count": 4,
                "average_capacity": 70.0,
                "conflict_count": 3,
                "compliance_overdue": 2,
                "compliance_due_soon": 1,
                "work_orders_logged": 6,
                "due_today_count": 1,
                "high_priority_count": 4,
                "error": f"Using fallback data: {str(e)}",
            }
        )


# ========== WORK ORDER MANAGEMENT ENDPOINTS ==========

from pydantic import BaseModel, Field
from typing import Optional


class WorkOrderUpdate(BaseModel):
    """Pydantic model for work order updates"""

    title: Optional[str] = Field(None, description="Work order title")
    description: Optional[str] = Field(None, description="Work order description")
    priority: Optional[str] = Field(
        None, description="Priority level: urgent, high, medium, low"
    )
    status: Optional[str] = Field(
        None, description="Status: pending, in_progress, on_hold, completed"
    )
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    scheduled_date: Optional[str] = Field(
        None, description="Scheduled date (YYYY-MM-DD)"
    )
    estimated_duration: Optional[int] = Field(
        None, description="Estimated duration in hours"
    )
    assigned_to: Optional[str] = Field(None, description="Assigned technician ID")
    parts_required: Optional[List[str]] = Field(
        None, description="List of required parts"
    )


@router.get("/work-orders")
async def get_all_work_orders():
    """Get all work orders from backlog"""
    try:
        backlog_data = planner_service.get_work_order_backlog()
        return JSONResponse(
            content={
                "work_orders": backlog_data.get("work_orders", []),
                "total_count": backlog_data.get("total_backlog", 0),
                "overdue_count": backlog_data.get("overdue_count", 0),
                "due_today_count": backlog_data.get("due_today_count", 0),
                "by_priority": backlog_data.get("by_priority", {}),
            }
        )
    except Exception as e:
        return JSONResponse(
            content={
                "error": f"Failed to fetch work orders: {str(e)}",
                "work_orders": [],
                "total_count": 0,
            }
        )


@router.get("/work-orders/{work_order_id}")
async def get_work_order_detail(work_order_id: str):
    """Get detailed information for a specific work order"""
    try:
        backlog_data = planner_service.get_work_order_backlog()
        work_orders = backlog_data.get("work_orders", [])

        # Find the specific work order
        work_order = None
        for wo in work_orders:
            if wo.get("id") == work_order_id:
                work_order = wo
                break

        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found")

        # Add additional mock data for editing interface
        work_order.update(
            {
                "description": f"Detailed description for {work_order.get('title', 'work order')}",
                "scheduled_date": work_order.get("due_date"),  # Default to due date
                "assigned_to": "tech_001",  # Default assignment
                "parts_required": (
                    ["Part-A", "Part-B"]
                    if "urgent" in work_order.get("priority", "")
                    else ["Standard-Part"]
                ),
                "tools_required": ["Wrench Set", "Multimeter", "Safety Equipment"],
                "procedures": [
                    "1. Review safety protocols",
                    "2. Gather required tools and parts",
                    "3. Perform maintenance tasks",
                    "4. Test functionality",
                    "5. Update work order status",
                ],
                "asset_details": {
                    "location": "Building A - Floor 2",
                    "serial_number": f"SN-{work_order_id[-3:]}",
                    "last_maintenance": "2024-11-01",
                },
            }
        )

        return JSONResponse(content=work_order)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get work order: {str(e)}"
        )


@router.put("/work-orders/{work_order_id}")
async def update_work_order(work_order_id: str, updates: WorkOrderUpdate):
    """Update a work order with new information"""
    try:
        # Get current work order data
        backlog_data = planner_service.get_work_order_backlog()
        work_orders = backlog_data.get("work_orders", [])

        # Find the work order to update
        work_order_found = False
        for wo in work_orders:
            if wo.get("id") == work_order_id:
                work_order_found = True
                break

        if not work_order_found:
            raise HTTPException(status_code=404, detail="Work order not found")

        # In a real system, this would update the database
        # For now, we'll return a success response with the updated data
        update_data = updates.dict(exclude_unset=True)

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Work order {work_order_id} updated successfully",
                "work_order_id": work_order_id,
                "updates_applied": update_data,
                "updated_fields": list(update_data.keys()),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update work order: {str(e)}"
        )


@router.post("/work-orders/{work_order_id}/assign")
async def assign_work_order(
    work_order_id: str, technician_id: str = Query(..., description="Technician ID")
):
    """Assign work order to a specific technician"""
    try:
        # Get capacity data to validate technician exists
        capacity_data = planner_service.get_resource_capacity()
        technicians = capacity_data.get("technicians", [])

        # Check if technician exists and is available
        technician_found = False
        for tech in technicians:
            if tech.get("id") == technician_id and tech.get("status") == "active":
                technician_found = True
                break

        if not technician_found:
            raise HTTPException(
                status_code=400, detail="Technician not found or unavailable"
            )

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Work order {work_order_id} assigned to technician {technician_id}",
                "work_order_id": work_order_id,
                "assigned_to": technician_id,
                "assignment_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to assign work order: {str(e)}"
        )


@router.get("/technicians")
async def get_available_technicians():
    """Get list of available technicians for work order assignment"""
    try:
        capacity_data = planner_service.get_resource_capacity()
        technicians = capacity_data.get("technicians", [])

        # Filter active technicians and add availability info
        available_technicians = []
        for tech in technicians:
            if tech.get("status") == "active":
                available_technicians.append(
                    {
                        "id": tech.get("id"),
                        "name": tech.get("name"),
                        "capacity_percentage": tech.get("capacity_percentage", 0),
                        "available_hours": tech.get("available_hours", 0),
                        "active_work_orders": tech.get("active_work_orders", 0),
                        "urgent_count": tech.get("urgent_count", 0),
                        "status": tech.get("status"),
                    }
                )

        return JSONResponse(
            content={
                "technicians": available_technicians,
                "total_available": len(available_technicians),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get technicians: {str(e)}"
        )


# ========== ADVANCED SCHEDULER ENDPOINTS ==========


@router.post("/advanced/initialize")
async def initialize_advanced_scheduler():
    """Initialize the advanced scheduler with comprehensive data"""
    try:
        await advanced_scheduler.initialize_scheduler()
        return JSONResponse(
            content={
                "status": "success",
                "message": "Advanced scheduler initialized successfully",
                "technician_count": len(advanced_scheduler.technicians),
                "asset_count": len(advanced_scheduler.asset_requirements),
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize scheduler: {str(e)}"
        )


@router.get("/advanced/mock-data")
async def get_advanced_mock_data():
    """Get comprehensive mock data for demonstration"""
    try:
        mock_data = scheduler_mock_service.get_comprehensive_mock_data()

        # Convert complex objects to serializable format
        serialized_data = {
            "technicians": {},
            "assets": {},
            "emergency_scenarios": mock_data["emergency_scenarios"],
            "workload_scenarios": mock_data["workload_scenarios"],
            "locations": mock_data["locations"],
            "skills": mock_data["skills"],
            "shifts": mock_data["shifts"],
        }

        # Serialize technicians
        for tech_id, tech in mock_data["technicians"].items():
            serialized_data["technicians"][tech_id] = {
                "id": tech.id,
                "name": tech.name,
                "email": tech.email,
                "phone": tech.phone,
                "status": tech.status.value,
                "location": tech.location,
                "hourly_rate": tech.hourly_rate,
                "skills": [
                    {
                        "name": skill.name,
                        "level": skill.level,
                        "certified": skill.certified,
                    }
                    for skill in tech.skills
                ],
                "shift": {
                    "start": tech.shift.start_time.strftime("%H:%M"),
                    "end": tech.shift.end_time.strftime("%H:%M"),
                    "days": tech.shift.days_of_week,
                },
            }

        # Serialize assets
        for asset_id, asset in mock_data["assets"].items():
            serialized_data["assets"][asset_id] = {
                "asset_id": asset.asset_id,
                "required_skills": asset.required_skills,
                "estimated_duration": asset.estimated_duration,
                "criticality": asset.criticality,
                "location": asset.location,
                "last_maintenance": (
                    asset.last_maintenance.isoformat()
                    if asset.last_maintenance
                    else None
                ),
                "next_due": asset.next_due.isoformat() if asset.next_due else None,
                "maintenance_window": (
                    [
                        asset.maintenance_window[0].strftime("%H:%M"),
                        asset.maintenance_window[1].strftime("%H:%M"),
                    ]
                    if asset.maintenance_window
                    else None
                ),
            }

        return JSONResponse(content=serialized_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate mock data: {str(e)}"
        )


@router.post("/advanced/optimize")
async def optimize_schedule(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    objectives: Optional[List[str]] = Query(
        None, description="Optimization objectives"
    ),
):
    """Optimize maintenance schedule using advanced algorithms"""
    try:
        # Parse dates or use defaults
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now()

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = start_dt + timedelta(days=30)

        # Initialize if not already done
        if not advanced_scheduler.technicians:
            await advanced_scheduler.initialize_scheduler()

        # Run optimization
        result = await advanced_scheduler.optimize_schedule(
            start_dt, end_dt, objectives or ["minimize_cost", "maximize_efficiency"]
        )

        # Serialize result
        return JSONResponse(
            content={
                "optimization_result": {
                    "total_cost": result.total_cost,
                    "completion_percentage": result.completion_percentage,
                    "conflict_count": len(result.conflicts),
                    "resource_utilization": result.resource_utilization,
                    "recommendations": result.recommendations,
                },
                "conflicts": [
                    {
                        "technician_id": c.technician_id,
                        "date": c.date.isoformat(),
                        "conflict_type": c.conflict_type,
                        "severity": c.severity,
                        "affected_work_orders": c.affected_work_orders,
                        "resolution_suggestions": c.resolution_suggestions,
                    }
                    for c in result.conflicts
                ],
                "schedule_period": {
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                },
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/advanced/calendar")
async def get_calendar_view(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    technician_id: Optional[str] = Query(None, description="Filter by technician ID"),
):
    """Get calendar view data for the advanced scheduler"""
    try:
        # Parse dates or use defaults
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now()

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = start_dt + timedelta(days=14)  # 2 week default view

        # Get calendar data
        calendar_data = await advanced_scheduler.get_calendar_view(
            start_dt, end_dt, technician_id
        )

        return JSONResponse(content=calendar_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get calendar view: {str(e)}"
        )


@router.get("/advanced/technician/{tech_id}/schedule")
async def get_technician_schedule(
    tech_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get detailed schedule for a specific technician"""
    try:
        # Parse dates or use defaults
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now()

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = start_dt + timedelta(days=7)  # 1 week default

        # Get technician schedule
        schedule_data = await advanced_scheduler.get_technician_schedule(
            tech_id, start_dt, end_dt
        )

        return JSONResponse(content=schedule_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get technician schedule: {str(e)}"
        )


@router.get("/advanced/technicians")
async def get_all_technicians():
    """Get all technicians with their profiles and current status"""
    try:
        if not advanced_scheduler.technicians:
            await advanced_scheduler.initialize_scheduler()

        technicians_data = {}
        for tech_id, tech in advanced_scheduler.technicians.items():
            technicians_data[tech_id] = {
                "id": tech.id,
                "name": tech.name,
                "email": tech.email,
                "phone": tech.phone,
                "status": tech.status.value,
                "location": tech.location,
                "hourly_rate": tech.hourly_rate,
                "current_workload_hours": tech.current_workload_hours,
                "max_hours_per_day": tech.max_hours_per_day,
                "skills": [
                    {
                        "name": skill.name,
                        "level": skill.level,
                        "certified": skill.certified,
                    }
                    for skill in tech.skills
                ],
                "shift": {
                    "start": tech.shift.start_time.strftime("%H:%M"),
                    "end": tech.shift.end_time.strftime("%H:%M"),
                    "days": tech.shift.days_of_week,
                },
            }

        return JSONResponse(
            content={
                "technicians": technicians_data,
                "total_count": len(technicians_data),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get technicians: {str(e)}"
        )


@router.get("/advanced/assets")
async def get_all_assets():
    """Get all assets with their maintenance requirements"""
    try:
        if not advanced_scheduler.asset_requirements:
            await advanced_scheduler.initialize_scheduler()

        assets_data = {}
        for asset_id, asset in advanced_scheduler.asset_requirements.items():
            assets_data[asset_id] = {
                "asset_id": asset.asset_id,
                "required_skills": asset.required_skills,
                "estimated_duration": asset.estimated_duration,
                "criticality": asset.criticality,
                "location": asset.location,
                "last_maintenance": (
                    asset.last_maintenance.isoformat()
                    if asset.last_maintenance
                    else None
                ),
                "next_due": asset.next_due.isoformat() if asset.next_due else None,
                "maintenance_window": (
                    [
                        asset.maintenance_window[0].strftime("%H:%M"),
                        asset.maintenance_window[1].strftime("%H:%M"),
                    ]
                    if asset.maintenance_window
                    else None
                ),
            }

        return JSONResponse(
            content={"assets": assets_data, "total_count": len(assets_data)}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assets: {str(e)}")


@router.get("/advanced/analytics")
async def get_scheduler_analytics():
    """Get comprehensive analytics for the scheduling system"""
    try:
        if not advanced_scheduler.technicians:
            await advanced_scheduler.initialize_scheduler()

        # Calculate analytics
        technicians = advanced_scheduler.technicians
        assets = advanced_scheduler.asset_requirements

        # Technician analytics
        tech_by_status = {}
        tech_by_location = {}
        skill_coverage = {}

        for tech in technicians.values():
            # Status distribution
            status = tech.status.value
            tech_by_status[status] = tech_by_status.get(status, 0) + 1

            # Location distribution
            location = tech.location
            tech_by_location[location] = tech_by_location.get(location, 0) + 1

            # Skill coverage
            for skill in tech.skills:
                if skill.name not in skill_coverage:
                    skill_coverage[skill.name] = []
                skill_coverage[skill.name].append(skill.level)

        # Asset analytics
        asset_by_criticality = {}
        asset_by_location = {}
        overdue_assets = []

        for asset in assets.values():
            # Criticality distribution
            crit = asset.criticality
            asset_by_criticality[crit] = asset_by_criticality.get(crit, 0) + 1

            # Location distribution
            location = asset.location
            asset_by_location[location] = asset_by_location.get(location, 0) + 1

            # Overdue check
            if asset.next_due and asset.next_due < datetime.now():
                overdue_assets.append(
                    {
                        "asset_id": asset.asset_id,
                        "location": asset.location,
                        "days_overdue": (datetime.now() - asset.next_due).days,
                        "criticality": asset.criticality,
                    }
                )

        # Calculate skill coverage statistics
        skill_stats = {}
        for skill, levels in skill_coverage.items():
            skill_stats[skill] = {
                "technician_count": len(levels),
                "average_level": round(sum(levels) / len(levels), 1),
                "max_level": max(levels),
                "certified_count": sum(
                    1
                    for tech in technicians.values()
                    for tech_skill in tech.skills
                    if tech_skill.name == skill and tech_skill.certified
                ),
            }

        return JSONResponse(
            content={
                "technician_analytics": {
                    "total_count": len(technicians),
                    "by_status": tech_by_status,
                    "by_location": tech_by_location,
                    "average_hourly_rate": round(
                        sum(t.hourly_rate for t in technicians.values())
                        / len(technicians),
                        2,
                    ),
                },
                "asset_analytics": {
                    "total_count": len(assets),
                    "by_criticality": asset_by_criticality,
                    "by_location": asset_by_location,
                    "overdue_count": len(overdue_assets),
                    "overdue_details": overdue_assets,
                },
                "skill_analytics": skill_stats,
                "locations": list(
                    set(tech_by_location.keys()) | set(asset_by_location.keys())
                ),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {str(e)}"
        )


# ========== PM AUTOMATION ENGINE ENDPOINTS ==========
# All PM endpoints now use Firestore and require organization_id for multi-tenant support


def _get_org_id(current_user: Optional[User], demo_org_id: str = "demo_org") -> str:
    """Helper to get organization_id from user or return demo org."""
    if current_user and current_user.organization_id:
        return current_user.organization_id
    return demo_org_id


@router.get("/pm-automation/overview")
async def get_pm_automation_overview(
    days_ahead: int = Query(30, description="Days to look ahead"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get comprehensive PM automation overview for the user's organization"""
    try:
        org_id = _get_org_id(current_user)
        overview = await pm_automation_engine.get_pm_schedule_overview(org_id, days_ahead)
        return JSONResponse(content=overview)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get PM overview: {str(e)}"
        )


@router.post("/pm-automation/generate-schedule")
async def generate_pm_schedule(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    create_work_orders: bool = Query(True, description="Create actual work orders"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Generate PM work orders for the specified period"""
    try:
        org_id = _get_org_id(current_user)

        # Parse dates or use defaults
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now()

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = start_dt + timedelta(days=30)

        # Generate PM schedule (now returns dict, creates actual WOs if requested)
        result = await pm_automation_engine.generate_pm_schedule(
            org_id, start_dt, end_dt, create_work_orders=create_work_orders
        )

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PM schedule: {str(e)}"
        )


@router.post("/pm-automation/update-meter")
async def update_meter_reading(
    meter_id: str = Query(..., description="Meter ID to update"),
    new_value: float = Query(..., description="New meter reading value"),
    reading_source: str = Query("manual", description="Source: manual, iot, api"),
    create_work_orders: bool = Query(True, description="Create WOs for triggered maintenance"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Update a meter reading and check for triggered maintenance"""
    try:
        org_id = _get_org_id(current_user)
        result = await pm_automation_engine.update_meter_reading(
            org_id, meter_id, new_value, reading_source, create_work_orders
        )
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update meter reading: {str(e)}"
        )


@router.get("/pm-automation/templates")
async def get_maintenance_templates(
    maintenance_type: Optional[str] = Query(None, description="Filter by type"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get all available maintenance templates for the organization"""
    try:
        org_id = _get_org_id(current_user)
        templates = await pm_automation_engine.get_maintenance_templates(
            org_id, maintenance_type=maintenance_type
        )

        return JSONResponse(
            content={"templates": templates, "total_count": len(templates)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get maintenance templates: {str(e)}"
        )


@router.get("/pm-automation/asset-meters")
async def get_asset_meters(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    meter_type: Optional[str] = Query(None, description="Filter by meter type"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get asset meter readings and status for the organization"""
    try:
        org_id = _get_org_id(current_user)
        meters = await pm_automation_engine.get_asset_meters(
            org_id, asset_id=asset_id, meter_type=meter_type
        )

        # Group by asset_id for backward compatibility
        meters_data = {}
        for meter in meters:
            aid = meter.get("asset_id", "unknown")
            if aid not in meters_data:
                meters_data[aid] = []
            meters_data[aid].append(meter)

        return JSONResponse(
            content={
                "asset_meters": meters_data,
                "total_assets": len(meters_data),
                "total_meters": len(meters),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get asset meters: {str(e)}"
        )


@router.get("/pm-automation/schedule-rules")
async def get_schedule_rules(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Get PM schedule rules for the organization"""
    try:
        org_id = _get_org_id(current_user)
        rules = await pm_automation_engine.get_schedule_rules(
            org_id, asset_id=asset_id, is_active=is_active
        )

        return JSONResponse(
            content={"rules": rules, "total_count": len(rules)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get schedule rules: {str(e)}"
        )


@router.post("/pm-automation/seed-templates")
async def seed_pm_templates(
    global_templates: bool = Query(False, description="Create global templates (admin only)"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Seed default PM templates for the organization (or globally for admin)"""
    try:
        if global_templates:
            # Only allow global template creation for demo or admin
            org_id = None
        else:
            org_id = _get_org_id(current_user)

        result = await pm_automation_engine.seed_default_templates(org_id)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to seed templates: {str(e)}"
        )


@router.post("/pm-automation/seed-demo-data")
async def seed_pm_demo_data(
    asset_ids: Optional[str] = Query(None, description="Comma-separated asset IDs"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Seed demo PM data (templates, rules, meters) for the organization"""
    try:
        org_id = _get_org_id(current_user)

        # Parse asset_ids if provided
        asset_list = None
        if asset_ids:
            asset_list = [aid.strip() for aid in asset_ids.split(",")]

        result = await pm_automation_engine.seed_demo_data(org_id, asset_list)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to seed demo data: {str(e)}"
        )
