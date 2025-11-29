"""
Analytics Router for ChatterFix CMMS
Provides API endpoints for advanced analytics, KPIs, and reporting
"""

from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel
from app.services.analytics_service import analytics_service
from app.services.export_service import export_service

router = APIRouter(prefix="/analytics", tags=["analytics"])
templates = Jinja2Templates(directory="app/templates")


class ExportRequest(BaseModel):
    report_type: str  # kpi, work_orders, assets, maintenance_history
    format: str  # json, csv, excel, pdf
    days: Optional[int] = 30


# Dashboard and KPI Endpoints

@router.get("/dashboard", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """Render the advanced analytics dashboard"""
    # Get KPI summary for initial render
    try:
        kpi_data = analytics_service.get_kpi_summary(30)
    except Exception as e:
        kpi_data = {}
    
    return templates.TemplateResponse("analytics_dashboard.html", {
        "request": request,
        "kpi_data": kpi_data
    })


@router.get("/kpi/summary")
async def get_kpi_summary(days: int = Query(30, ge=1, le=365)):
    """Get comprehensive KPI summary"""
    try:
        data = analytics_service.get_kpi_summary(days)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/mttr")
async def get_mttr(days: int = Query(30, ge=1, le=365)):
    """Get Mean Time To Repair (MTTR) metrics"""
    try:
        data = analytics_service.calculate_mttr(days)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/mtbf")
async def get_mtbf(days: int = Query(30, ge=1, le=365)):
    """Get Mean Time Between Failures (MTBF) metrics"""
    try:
        data = analytics_service.calculate_mtbf(days)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/utilization")
async def get_asset_utilization(days: int = Query(30, ge=1, le=365)):
    """Get asset utilization metrics"""
    try:
        data = analytics_service.calculate_asset_utilization(days)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/costs")
async def get_cost_tracking(days: int = Query(30, ge=1, le=365)):
    """Get cost tracking metrics"""
    try:
        data = analytics_service.get_cost_tracking(days)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/work-orders")
async def get_work_order_metrics(days: int = Query(30, ge=1, le=365)):
    """Get work order metrics"""
    try:
        data = analytics_service.get_work_order_metrics(days)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/compliance")
async def get_compliance_metrics(days: int = Query(30, ge=1, le=365)):
    """Get compliance and PM adherence metrics"""
    try:
        data = analytics_service.get_compliance_metrics(days)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Trend Data Endpoints

@router.get("/trends/{metric}")
async def get_trend_data(
    metric: str,
    days: int = Query(30, ge=1, le=365)
):
    """
    Get historical trend data for a specific metric
    
    Available metrics: mttr, mtbf, cost, work_orders
    """
    valid_metrics = ["mttr", "mtbf", "cost", "work_orders"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric. Available: {', '.join(valid_metrics)}"
        )
    
    try:
        data = analytics_service.get_trend_data(metric, days)
        return JSONResponse(content={
            "metric": metric,
            "period_days": days,
            "data": data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export Endpoints

@router.post("/export")
async def export_report(request: ExportRequest):
    """Export report in specified format"""
    try:
        if request.report_type == "kpi":
            result = export_service.export_kpi_report(request.format, request.days)
        elif request.report_type == "work_orders":
            result = export_service.export_work_orders(request.format)
        elif request.report_type == "assets":
            result = export_service.export_assets(request.format)
        elif request.report_type == "maintenance_history":
            result = export_service.export_maintenance_history(request.format, request.days)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report type: {request.report_type}"
            )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/kpi/{format}")
async def export_kpi_quick(
    format: str,
    days: int = Query(30, ge=1, le=365)
):
    """Quick export endpoint for KPI report"""
    valid_formats = ["json", "csv", "excel", "pdf"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {', '.join(valid_formats)}"
        )
    
    try:
        result = export_service.export_kpi_report(format, days)
        
        # Return file directly for download
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/work-orders/{format}")
async def export_work_orders_quick(format: str):
    """Quick export endpoint for work orders"""
    valid_formats = ["json", "csv", "excel"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {', '.join(valid_formats)}"
        )
    
    try:
        result = export_service.export_work_orders(format)
        
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/assets/{format}")
async def export_assets_quick(format: str):
    """Quick export endpoint for assets"""
    valid_formats = ["json", "csv", "excel"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {', '.join(valid_formats)}"
        )
    
    try:
        result = export_service.export_assets(format)
        
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chart Data Endpoints (for Chart.js integration)

@router.get("/charts/work-order-status")
async def get_work_order_status_chart(days: int = Query(30, ge=1, le=365)):
    """Get work order status distribution for pie/doughnut chart"""
    try:
        data = analytics_service.get_work_order_metrics(days)
        status_breakdown = data.get("status_breakdown", {})
        
        return JSONResponse(content={
            "labels": list(status_breakdown.keys()),
            "data": list(status_breakdown.values()),
            "colors": {
                "Open": "#f39c12",
                "In Progress": "#3498db",
                "Completed": "#27ae60",
                "Cancelled": "#95a5a6",
                "On Hold": "#e74c3c"
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/priority-distribution")
async def get_priority_distribution_chart(days: int = Query(30, ge=1, le=365)):
    """Get work order priority distribution for chart"""
    try:
        data = analytics_service.get_work_order_metrics(days)
        priority_breakdown = data.get("priority_breakdown", {})
        
        return JSONResponse(content={
            "labels": list(priority_breakdown.keys()),
            "data": list(priority_breakdown.values()),
            "colors": {
                "Low": "#27ae60",
                "Medium": "#3498db",
                "High": "#f39c12",
                "urgent": "#e74c3c"
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/cost-trend")
async def get_cost_trend_chart(days: int = Query(30, ge=1, le=365)):
    """Get cost trend for line chart"""
    try:
        data = analytics_service.get_cost_tracking(days)
        daily_trend = data.get("daily_trend", [])
        
        return JSONResponse(content={
            "labels": [d["date"] for d in daily_trend],
            "data": [d["cost"] for d in daily_trend],
            "label": "Daily Maintenance Cost ($)"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/completion-trend")
async def get_completion_trend_chart(days: int = Query(30, ge=1, le=365)):
    """Get work order completion trend for line chart"""
    try:
        data = analytics_service.get_work_order_metrics(days)
        daily_trend = data.get("daily_trend", [])
        
        return JSONResponse(content={
            "labels": [d["date"] for d in daily_trend],
            "datasets": [
                {
                    "label": "Created",
                    "data": [d["created"] for d in daily_trend],
                    "borderColor": "#3498db",
                    "fill": False
                },
                {
                    "label": "Completed",
                    "data": [d["completed"] for d in daily_trend],
                    "borderColor": "#27ae60",
                    "fill": False
                }
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/asset-health")
async def get_asset_health_chart():
    """Get asset health distribution for chart"""
    try:
        data = analytics_service.calculate_asset_utilization(30)
        status_breakdown = data.get("status_breakdown", {})
        
        return JSONResponse(content={
            "labels": list(status_breakdown.keys()),
            "data": list(status_breakdown.values()),
            "colors": {
                "Active": "#27ae60",
                "Inactive": "#95a5a6",
                "Maintenance": "#f39c12",
                "Retired": "#e74c3c"
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/cost-breakdown")
async def get_cost_breakdown_chart(days: int = Query(30, ge=1, le=365)):
    """Get cost breakdown by maintenance type for chart"""
    try:
        data = analytics_service.get_cost_tracking(days)
        costs_by_type = data.get("costs_by_type", {})
        
        return JSONResponse(content={
            "labels": list(costs_by_type.keys()),
            "data": list(costs_by_type.values()),
            "colors": {
                "Preventive": "#27ae60",
                "Corrective": "#f39c12",
                "Predictive": "#3498db",
                "Emergency": "#e74c3c"
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
