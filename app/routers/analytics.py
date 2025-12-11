"""
Analytics Router for ChatterFix CMMS
Provides API endpoints for advanced analytics, KPIs, reporting, and Sales ROI Dashboard
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import grpc

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.services.analytics_service import analytics_service
from app.services.export_service import export_service
from app.database import get_db
from app.auth import get_current_user
from app.models import User, WorkOrder, PredictiveAlert
from app.schemas import UserResponse

# Import gRPC client for predictor service
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/predictive-engine'))
    from predictor_service_pb2_grpc import PredictorStub
    from predictor_service_pb2 import HealthRequest
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logging.warning("gRPC predictor service not available for analytics")

router = APIRouter(prefix="/analytics", tags=["analytics"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


class ExportRequest(BaseModel):
    report_type: str  # kpi, work_orders, assets, maintenance_history
    format: str  # json, csv, excel, pdf
    days: Optional[int] = 30


# Role-based Access Control for Sales/Admin Features
def check_admin_or_sales_role(current_user: User = Depends(get_current_user)):
    """Verify user has Admin or Sales role access"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user account"
        )
    
    # Check if user has admin privileges or sales role
    if not (current_user.is_superuser or 
            getattr(current_user, 'role', '').lower() in ['admin', 'sales']):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Admin or Sales role required."
        )
    return current_user


def get_predictor_health() -> Dict[str, Any]:
    """Check gRPC Predictor service health status"""
    if not GRPC_AVAILABLE:
        return {
            "status": "FALLBACK",
            "message": "gRPC service unavailable",
            "response_time_ms": 0
        }
    
    try:
        start_time = datetime.now()
        
        # Connect to gRPC service  
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = PredictorStub(channel)
            response = stub.CheckHealth(HealthRequest())
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "ONLINE" if response.healthy else "DEGRADED", 
                "message": response.message,
                "response_time_ms": round(response_time, 2)
            }
            
    except grpc.RpcError as e:
        logger.error(f"gRPC health check failed: {e}")
        return {
            "status": "OFFLINE",
            "message": f"Service unavailable: {e.code()}",
            "response_time_ms": 0
        }
    except Exception as e:
        logger.error(f"Unexpected error in health check: {e}")
        return {
            "status": "FALLBACK",
            "message": f"Health check error: {str(e)}",
            "response_time_ms": 0
        }


# Sales ROI Dashboard Endpoints

@router.get("/roi")
async def get_roi_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_or_sales_role)
) -> Dict[str, Any]:
    """
    Calculate and return ROI metrics for sales dashboard
    
    Returns:
        - downtime_saved_usd: Total customer savings from prevented downtime
        - system_health_score: Real-time AI predictor service status  
        - active_tenants: Count of active customer organizations
        - additional_metrics: Supporting data for sales presentations
    """
    
    try:
        # Calculate downtime savings from high-priority predictive alerts
        high_priority_alerts = db.query(PredictiveAlert).filter(
            and_(
                PredictiveAlert.severity == "High",
                PredictiveAlert.status == "resolved", 
                PredictiveAlert.created_at >= datetime.now() - timedelta(days=365)
            )
        ).count()
        
        # Conservative estimate: $5,000 average cost per prevented high-priority incident
        COST_PER_INCIDENT = 5000
        downtime_saved_usd = high_priority_alerts * COST_PER_INCIDENT
        
        # Get system health status
        predictor_health = get_predictor_health()
        
        # Count active tenants (unique organizations with recent activity)
        active_tenants = db.query(func.count(func.distinct(User.company_name))).filter(
            and_(
                User.is_active == True,
                User.last_login >= datetime.now() - timedelta(days=30)
            )
        ).scalar() or 0
        
        # Additional metrics for comprehensive sales presentation
        total_work_orders = db.query(func.count(WorkOrder.id)).scalar() or 0
        completed_work_orders = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.status == "completed"
        ).scalar() or 0
        completion_rate = (completed_work_orders / total_work_orders * 100) if total_work_orders > 0 else 0
        
        # Calculate recent activity metrics
        recent_alerts = db.query(func.count(PredictiveAlert.id)).filter(
            PredictiveAlert.created_at >= datetime.now() - timedelta(days=30)
        ).scalar() or 0
        
        # ROI calculation for sales presentation
        traditional_reactive_cost = total_work_orders * 2500  # Average reactive maintenance cost
        chatterfix_proactive_cost = active_tenants * 999 * 12  # Annual subscription cost
        total_savings = downtime_saved_usd + (traditional_reactive_cost - chatterfix_proactive_cost)
        
        return {
            "downtime_saved_usd": downtime_saved_usd,
            "system_health_score": predictor_health,
            "active_tenants": active_tenants,
            "metrics": {
                "total_work_orders": total_work_orders,
                "completion_rate": round(completion_rate, 1),
                "recent_predictive_alerts": recent_alerts,
                "high_priority_incidents_prevented": high_priority_alerts,
                "traditional_reactive_cost": traditional_reactive_cost,
                "chatterfix_proactive_cost": chatterfix_proactive_cost,
                "total_savings": max(total_savings, downtime_saved_usd),
                "roi_percentage": round((total_savings / chatterfix_proactive_cost * 100), 1) if chatterfix_proactive_cost > 0 else 0
            },
            "generated_at": datetime.now().isoformat(),
            "user": current_user.email
        }
        
    except Exception as e:
        logger.error(f"Error calculating ROI metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate ROI metrics: {str(e)}"
        )


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_or_sales_role)
) -> Dict[str, Any]:
    """Get high-level dashboard summary for quick sales presentations"""
    
    try:
        roi_data = await get_roi_metrics(db, current_user)
        
        return {
            "customer_savings": f"${roi_data['downtime_saved_usd']:,}",
            "ai_status": roi_data['system_health_score']['status'], 
            "active_clients": roi_data['active_tenants'],
            "system_health": {
                "status": roi_data['system_health_score']['status'],
                "response_time": f"{roi_data['system_health_score']['response_time_ms']}ms"
            },
            "roi_metrics": {
                "total_savings": f"${roi_data['metrics']['total_savings']:,}",
                "roi_percentage": f"{roi_data['metrics']['roi_percentage']}%",
                "completion_rate": f"{roi_data['metrics']['completion_rate']}%"
            },
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate dashboard summary: {str(e)}"
        )


@router.get("/roi-dashboard", response_class=HTMLResponse)
async def roi_dashboard(
    request: Request,
    current_user: User = Depends(check_admin_or_sales_role)
):
    """Render the Sales ROI Dashboard with dark mode enterprise aesthetic"""
    return templates.TemplateResponse(
        "roi_dashboard.html", 
        {"request": request, "user": current_user}
    )


# Dashboard and KPI Endpoints


@router.get("/dashboard", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """Render the advanced analytics dashboard"""
    # Get KPI summary for initial render
    try:
        kpi_data = analytics_service.get_kpi_summary(30)
    except Exception:
        kpi_data = {}

    return templates.TemplateResponse(
        "analytics_dashboard.html", {"request": request, "kpi_data": kpi_data}
    )


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
async def get_trend_data(metric: str, days: int = Query(30, ge=1, le=365)):
    """
    Get historical trend data for a specific metric

    Available metrics: mttr, mtbf, cost, work_orders
    """
    valid_metrics = ["mttr", "mtbf", "cost", "work_orders"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Available: {', '.join(valid_metrics)}",
        )

    try:
        data = analytics_service.get_trend_data(metric, days)
        return JSONResponse(
            content={"metric": metric, "period_days": days, "data": data}
        )
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
            result = export_service.export_maintenance_history(
                request.format, request.days
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid report type: {request.report_type}"
            )

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/kpi/{format}")
async def export_kpi_quick(format: str, days: int = Query(30, ge=1, le=365)):
    """Quick export endpoint for KPI report"""
    valid_formats = ["json", "csv", "excel", "pdf"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {', '.join(valid_formats)}",
        )

    try:
        result = export_service.export_kpi_report(format, days)

        # Return file directly for download
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"'
            },
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
            detail=f"Invalid format. Available: {', '.join(valid_formats)}",
        )

    try:
        result = export_service.export_work_orders(format)

        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"'
            },
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
            detail=f"Invalid format. Available: {', '.join(valid_formats)}",
        )

    try:
        result = export_service.export_assets(format)

        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"'
            },
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

        return JSONResponse(
            content={
                "labels": list(status_breakdown.keys()),
                "data": list(status_breakdown.values()),
                "colors": {
                    "Open": "#f39c12",
                    "In Progress": "#3498db",
                    "Completed": "#27ae60",
                    "Cancelled": "#95a5a6",
                    "On Hold": "#e74c3c",
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/priority-distribution")
async def get_priority_distribution_chart(days: int = Query(30, ge=1, le=365)):
    """Get work order priority distribution for chart"""
    try:
        data = analytics_service.get_work_order_metrics(days)
        priority_breakdown = data.get("priority_breakdown", {})

        return JSONResponse(
            content={
                "labels": list(priority_breakdown.keys()),
                "data": list(priority_breakdown.values()),
                "colors": {
                    "Low": "#27ae60",
                    "Medium": "#3498db",
                    "High": "#f39c12",
                    "urgent": "#e74c3c",
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/cost-trend")
async def get_cost_trend_chart(days: int = Query(30, ge=1, le=365)):
    """Get cost trend for line chart"""
    try:
        data = analytics_service.get_cost_tracking(days)
        daily_trend = data.get("daily_trend", [])

        return JSONResponse(
            content={
                "labels": [d["date"] for d in daily_trend],
                "data": [d["cost"] for d in daily_trend],
                "label": "Daily Maintenance Cost ($)",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/completion-trend")
async def get_completion_trend_chart(days: int = Query(30, ge=1, le=365)):
    """Get work order completion trend for line chart"""
    try:
        data = analytics_service.get_work_order_metrics(days)
        daily_trend = data.get("daily_trend", [])

        return JSONResponse(
            content={
                "labels": [d["date"] for d in daily_trend],
                "datasets": [
                    {
                        "label": "Created",
                        "data": [d["created"] for d in daily_trend],
                        "borderColor": "#3498db",
                        "fill": False,
                    },
                    {
                        "label": "Completed",
                        "data": [d["completed"] for d in daily_trend],
                        "borderColor": "#27ae60",
                        "fill": False,
                    },
                ],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/asset-health")
async def get_asset_health_chart():
    """Get asset health distribution for chart"""
    try:
        data = analytics_service.calculate_asset_utilization(30)
        status_breakdown = data.get("status_breakdown", {})

        return JSONResponse(
            content={
                "labels": list(status_breakdown.keys()),
                "data": list(status_breakdown.values()),
                "colors": {
                    "Active": "#27ae60",
                    "Inactive": "#95a5a6",
                    "Maintenance": "#f39c12",
                    "Retired": "#e74c3c",
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/cost-breakdown")
async def get_cost_breakdown_chart(days: int = Query(30, ge=1, le=365)):
    """Get cost breakdown by maintenance type for chart"""
    try:
        data = analytics_service.get_cost_tracking(days)
        costs_by_type = data.get("costs_by_type", {})

        return JSONResponse(
            content={
                "labels": list(costs_by_type.keys()),
                "data": list(costs_by_type.values()),
                "colors": {
                    "Preventive": "#27ae60",
                    "Corrective": "#f39c12",
                    "Predictive": "#3498db",
                    "Emergency": "#e74c3c",
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
