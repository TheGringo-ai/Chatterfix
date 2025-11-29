from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.services.planner_service import planner_service

router = APIRouter(prefix="/planner", tags=["planner"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def planner_dashboard(request: Request):
    """Render planner dashboard"""
    return templates.TemplateResponse("planner_dashboard.html", {"request": request})


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
