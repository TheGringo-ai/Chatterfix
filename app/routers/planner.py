from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from typing import Optional, List

from app.services.planner_service import planner_service
from app.services.advanced_scheduler_service import advanced_scheduler
from app.services.scheduler_mock_data import scheduler_mock_service
from app.services.pm_automation_engine import pm_automation_engine

router = APIRouter(prefix="/planner", tags=["planner"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def planner_dashboard(request: Request):
    """Render planner dashboard"""
    return templates.TemplateResponse("planner_dashboard.html", {"request": request})


@router.get("/advanced", response_class=HTMLResponse)
async def advanced_scheduler_dashboard(request: Request):
    """Render advanced scheduler dashboard with enterprise features"""
    return templates.TemplateResponse("advanced_scheduler.html", {"request": request})


@router.get("/mobile", response_class=HTMLResponse)
async def mobile_scheduler_dashboard(request: Request):
    """Render mobile-responsive scheduler for field technicians"""
    return templates.TemplateResponse("mobile_scheduler.html", {"request": request})


@router.get("/analytics", response_class=HTMLResponse)
async def scheduler_analytics_dashboard(request: Request):
    """Render comprehensive scheduler analytics and reporting dashboard"""
    return templates.TemplateResponse("scheduler_analytics.html", {"request": request})


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


@router.get("/summary")
async def get_planner_summary():
    """Get comprehensive planner summary"""
    backlog = planner_service.get_work_order_backlog()
    capacity = planner_service.get_resource_capacity()
    conflicts = planner_service.get_scheduling_conflicts()
    compliance = planner_service.get_compliance_tracking()

    return JSONResponse(
        content={
            "backlog_count": backlog["total_backlog"],
            "overdue_count": backlog["overdue_count"],
            "technician_count": capacity["total_technicians"],
            "average_capacity": capacity["average_capacity"],
            "conflict_count": len(conflicts),
            "compliance_overdue": compliance["overdue"],
            "compliance_due_soon": compliance["due_soon"],
        }
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


@router.get("/pm-automation/overview")
async def get_pm_automation_overview(
    days_ahead: int = Query(30, description="Days to look ahead")
):
    """Get comprehensive PM automation overview"""
    try:
        overview = await pm_automation_engine.get_pm_schedule_overview(days_ahead)
        return JSONResponse(content=overview)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get PM overview: {str(e)}"
        )


@router.post("/pm-automation/generate-schedule")
async def generate_pm_schedule(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Generate PM work orders for the specified period"""
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

        # Generate PM schedule
        generated_orders = await pm_automation_engine.generate_pm_schedule(
            start_dt, end_dt
        )

        # Serialize work orders
        serialized_orders = []
        for order in generated_orders:
            serialized_orders.append(
                {
                    "id": order.work_order_id,
                    "asset_id": order.asset_id,
                    "template_id": order.template_id,
                    "title": order.title,
                    "description": order.description,
                    "priority": order.priority.name,
                    "due_date": order.due_date.isoformat(),
                    "estimated_duration": order.estimated_duration,
                    "required_skills": order.required_skills,
                    "required_parts": order.required_parts,
                    "required_tools": order.required_tools,
                    "generated_date": order.generated_date.isoformat(),
                    "trigger_reason": order.trigger_reason,
                    "can_be_deferred": order.can_be_deferred,
                    "deferral_count": order.deferral_count,
                }
            )

        return JSONResponse(
            content={
                "generated_orders": serialized_orders,
                "total_count": len(serialized_orders),
                "period": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PM schedule: {str(e)}"
        )


@router.post("/pm-automation/update-meter")
async def update_meter_reading(
    meter_id: str = Query(..., description="Meter ID to update"),
    new_value: float = Query(..., description="New meter reading value"),
):
    """Update a meter reading and check for triggered maintenance"""
    try:
        result = await pm_automation_engine.update_meter_reading(meter_id, new_value)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update meter reading: {str(e)}"
        )


@router.get("/pm-automation/templates")
async def get_maintenance_templates():
    """Get all available maintenance templates"""
    try:
        templates = {}
        for template_id, template in pm_automation_engine.maintenance_templates.items():
            templates[template_id] = {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "maintenance_type": template.maintenance_type.value,
                "triggers": [
                    {
                        "trigger_type": trigger.trigger_type.value,
                        "threshold_value": trigger.threshold_value,
                        "warning_threshold": trigger.warning_threshold,
                        "description": trigger.description,
                        "unit": trigger.unit,
                    }
                    for trigger in template.triggers
                ],
                "required_skills": template.required_skills,
                "estimated_duration": template.estimated_duration,
                "required_parts": template.required_parts,
                "required_tools": template.required_tools,
                "safety_requirements": template.safety_requirements,
                "procedures": template.procedures,
                "criticality": template.criticality,
                "can_be_deferred": template.can_be_deferred,
                "max_deferral_days": template.max_deferral_days,
            }

        return JSONResponse(
            content={"templates": templates, "total_count": len(templates)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get maintenance templates: {str(e)}"
        )


@router.get("/pm-automation/asset-meters")
async def get_asset_meters(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID")
):
    """Get asset meter readings and status"""
    try:
        if asset_id:
            if asset_id not in pm_automation_engine.asset_meters:
                return JSONResponse(content={"error": "Asset not found"})

            meters_data = {asset_id: []}
            for meter in pm_automation_engine.asset_meters[asset_id]:
                meters_data[asset_id].append(
                    {
                        "meter_id": meter.meter_id,
                        "asset_id": meter.asset_id,
                        "meter_type": meter.meter_type,
                        "current_value": meter.current_value,
                        "last_reading_date": meter.last_reading_date.isoformat(),
                        "reading_frequency": meter.reading_frequency,
                        "unit": meter.unit,
                        "is_automated": meter.is_automated,
                    }
                )
        else:
            meters_data = {}
            for asset_id, meters in pm_automation_engine.asset_meters.items():
                meters_data[asset_id] = []
                for meter in meters:
                    meters_data[asset_id].append(
                        {
                            "meter_id": meter.meter_id,
                            "asset_id": meter.asset_id,
                            "meter_type": meter.meter_type,
                            "current_value": meter.current_value,
                            "last_reading_date": meter.last_reading_date.isoformat(),
                            "reading_frequency": meter.reading_frequency,
                            "unit": meter.unit,
                            "is_automated": meter.is_automated,
                        }
                    )

        return JSONResponse(
            content={
                "asset_meters": meters_data,
                "total_assets": len(meters_data),
                "total_meters": sum(len(meters) for meters in meters_data.values()),
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get asset meters: {str(e)}"
        )
