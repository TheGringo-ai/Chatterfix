from datetime import datetime, timedelta
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user_from_cookie, get_optional_current_user
from app.models.user import User
from app.services.advanced_scheduler_service import advanced_scheduler
from app.services.planner_service import planner_service
from app.services.pm_automation_engine import pm_automation_engine
from app.services.scheduler_mock_data import scheduler_mock_service
from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)
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
async def get_pm_schedule(request: Request, days_ahead: int = 30):
    """Get preventive maintenance schedule - real Firestore data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    if current_user and current_user.organization_id:
        try:
            firestore_manager = get_firestore_manager()

            # Get PM schedule rules from Firestore
            pm_rules = await firestore_manager.get_collection(
                "pm_schedule_rules",
                filters=[
                    {"field": "organization_id", "operator": "==", "value": current_user.organization_id},
                    {"field": "is_active", "operator": "==", "value": True}
                ]
            )

            today = datetime.now()
            end_date = today + timedelta(days=days_ahead)
            schedule_by_date = {}

            for rule in pm_rules:
                # Calculate next due date based on interval
                next_due = rule.get("next_due_date")
                if next_due:
                    if hasattr(next_due, 'strftime'):
                        date_str = next_due.strftime("%Y-%m-%d")
                    else:
                        date_str = str(next_due)[:10]
                else:
                    # Use interval to calculate
                    interval_days = rule.get("interval_days", 30)
                    date_str = (today + timedelta(days=interval_days)).strftime("%Y-%m-%d")

                if date_str not in schedule_by_date:
                    schedule_by_date[date_str] = []

                schedule_by_date[date_str].append({
                    "id": rule.get("id"),
                    "asset_name": rule.get("asset_name", "Asset"),
                    "pm_type": rule.get("schedule_type", "time_based"),
                    "title": rule.get("title", "PM Task"),
                    "estimated_duration": rule.get("estimated_hours", 2),
                    "priority": rule.get("priority", "Medium"),
                })

            return JSONResponse(content={
                "schedule": schedule_by_date,
                "total_scheduled": len(pm_rules),
                "date_range": {
                    "start": today.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
            })
        except Exception as e:
            logger.error(f"Error fetching PM schedule: {e}")
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
    schedule = planner_service.get_pm_schedule(days_ahead)
    return JSONResponse(content=schedule)


@router.get("/resource-capacity")
async def get_resource_capacity(request: Request):
    """Get technician capacity and workload - real Firestore data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    if current_user and current_user.organization_id:
        try:
            firestore_manager = get_firestore_manager()

            # Get team members (technicians) from users collection
            users_data = await firestore_manager.get_collection(
                "users",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}],
                limit=50
            )

            # Get work orders to calculate workload
            work_orders_data = await firestore_manager.get_collection(
                "work_orders",
                filters=[
                    {"field": "organization_id", "operator": "==", "value": current_user.organization_id},
                    {"field": "status", "operator": "in", "value": ["Open", "In Progress"]}
                ],
                limit=200
            )

            # Build technician workload map
            tech_workload = {}
            for wo in work_orders_data:
                assigned_to = wo.get("assigned_to_uid")
                if assigned_to:
                    if assigned_to not in tech_workload:
                        tech_workload[assigned_to] = {"hours": 0, "count": 0, "urgent": 0}
                    tech_workload[assigned_to]["hours"] += wo.get("estimated_hours", 2)
                    tech_workload[assigned_to]["count"] += 1
                    if wo.get("priority", "").lower() in ["high", "critical", "urgent"]:
                        tech_workload[assigned_to]["urgent"] += 1

            technicians = []
            total_capacity = 0
            max_hours_per_day = 8

            for user in users_data:
                user_id = user.get("id") or user.get("uid")
                role = user.get("role", "").lower()

                # Include technicians, managers, and owners
                if role in ["technician", "tech", "manager", "owner", "admin"]:
                    workload = tech_workload.get(user_id, {"hours": 0, "count": 0, "urgent": 0})
                    capacity_pct = min(100, int((workload["hours"] / max_hours_per_day) * 100)) if max_hours_per_day > 0 else 0

                    technicians.append({
                        "id": user_id,
                        "name": user.get("full_name") or user.get("name") or user.get("email", "Unknown"),
                        "status": "active",
                        "capacity_percentage": capacity_pct,
                        "available_hours": max(0, max_hours_per_day - workload["hours"]),
                        "total_hours": workload["hours"],
                        "active_work_orders": workload["count"],
                        "urgent_count": workload["urgent"],
                    })
                    total_capacity += capacity_pct

            avg_capacity = int(total_capacity / len(technicians)) if technicians else 0

            return JSONResponse(content={
                "technicians": technicians,
                "total_technicians": len(technicians),
                "average_capacity": avg_capacity,
            })
        except Exception as e:
            logger.error(f"Error fetching resource capacity: {e}")
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
    capacity = planner_service.get_resource_capacity()
    return JSONResponse(content=capacity)


@router.get("/debug-auth")
async def debug_auth(request: Request):
    """Debug endpoint to check authentication status"""
    current_user = await get_current_user_from_cookie(request)
    session_token = request.cookies.get("session_token")

    return JSONResponse(content={
        "has_session_token": session_token is not None,
        "session_token_preview": session_token[:20] + "..." if session_token else None,
        "user_authenticated": current_user is not None,
        "user_email": current_user.email if current_user else None,
        "user_uid": current_user.uid if current_user else None,
        "organization_id": current_user.organization_id if current_user else None,
        "organization_name": current_user.organization_name if current_user else None,
        "role": current_user.role if current_user else None,
    })


@router.get("/backlog")
async def get_backlog(request: Request):
    """Get work order backlog - real Firestore data for authenticated users - BUILD_ID_20260105_0200"""
    current_user = await get_current_user_from_cookie(request)
    session_token = request.cookies.get("session_token")

    # UNIQUE MARKER FOR DEBUGGING - BUILD 20260105_0200
    build_marker = "BUILD_20260105_0200"

    # Debug info to include in response
    debug_info = {
        "build_marker": build_marker,
        "has_session_token": session_token is not None,
        "user_authenticated": current_user is not None,
        "user_email": current_user.email if current_user else None,
        "organization_id": current_user.organization_id if current_user else None,
        "data_source": "unknown"
    }

    # Debug logging
    logger.info(f"Backlog request - User: {current_user.email if current_user else 'None'}, Org: {current_user.organization_id if current_user else 'None'}")

    if current_user and current_user.organization_id:
        # Authenticated user - get real data from Firestore
        try:
            firestore_manager = get_firestore_manager()
            work_orders_data = await firestore_manager.get_collection(
                "work_orders",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}],
                order_by="-created_at",
                limit=100
            )

            today = datetime.now().strftime("%Y-%m-%d")
            work_orders = []
            for wo in work_orders_data:
                # Normalize the work order format for the calendar
                due_date = wo.get("due_date")
                if hasattr(due_date, 'strftime'):
                    due_date = due_date.strftime("%Y-%m-%d")
                elif due_date is None:
                    due_date = today

                work_orders.append({
                    "id": wo.get("id"),
                    "title": wo.get("title", "Untitled"),
                    "asset_name": wo.get("asset_name", ""),
                    "priority": wo.get("priority", "Medium"),
                    "status": wo.get("status", "Open"),
                    "due_date": due_date,
                    "estimated_duration": wo.get("estimated_hours", 2),
                    "assigned_to": wo.get("assigned_to_uid"),
                    "work_order_type": wo.get("work_order_type", "Corrective"),
                })

            # Calculate statistics
            overdue = [wo for wo in work_orders if wo["due_date"] < today and wo["status"] != "Completed"]
            due_today = [wo for wo in work_orders if wo["due_date"] == today]

            by_priority = {}
            for wo in work_orders:
                priority = wo["priority"].lower()
                by_priority[priority] = by_priority.get(priority, 0) + 1

            debug_info["data_source"] = "firestore"
            return JSONResponse(content={
                "work_orders": work_orders,
                "total_backlog": len([wo for wo in work_orders if wo["status"] != "Completed"]),
                "overdue_count": len(overdue),
                "due_today_count": len(due_today),
                "by_priority": by_priority,
                "_debug": debug_info,
            })
        except Exception as e:
            logger.error(f"Error fetching work orders for planner: {e}")
            debug_info["data_source"] = f"error: {str(e)}"
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
    debug_info["data_source"] = "mock_data"
    backlog = planner_service.get_work_order_backlog()
    backlog["_debug"] = debug_info
    return JSONResponse(content=backlog)


@router.get("/asset-pm-status")
async def get_asset_pm_status(request: Request):
    """Get asset preventive maintenance status - real Firestore data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    if current_user and current_user.organization_id:
        try:
            firestore_manager = get_firestore_manager()

            # Get assets from Firestore
            assets_data = await firestore_manager.get_collection(
                "assets",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}],
                limit=100
            )

            # Get PM schedule rules to determine status
            pm_rules = await firestore_manager.get_collection(
                "pm_schedule_rules",
                filters=[
                    {"field": "organization_id", "operator": "==", "value": current_user.organization_id},
                    {"field": "is_active", "operator": "==", "value": True}
                ]
            )

            # Create a map of asset_id to PM rules
            asset_pm_map = {}
            for rule in pm_rules:
                asset_id = rule.get("asset_id")
                if asset_id:
                    if asset_id not in asset_pm_map:
                        asset_pm_map[asset_id] = []
                    asset_pm_map[asset_id].append(rule)

            today = datetime.now()
            assets_with_status = []

            for asset in assets_data:
                asset_id = asset.get("id")
                pm_rules_for_asset = asset_pm_map.get(asset_id, [])

                # Determine PM status based on rules
                pm_status = "No PM Scheduled"
                if pm_rules_for_asset:
                    # Check if any PM is overdue or due soon
                    for rule in pm_rules_for_asset:
                        next_due = rule.get("next_due_date")
                        if next_due:
                            if hasattr(next_due, 'date'):
                                next_due_date = next_due.date()
                            else:
                                try:
                                    next_due_date = datetime.strptime(str(next_due)[:10], "%Y-%m-%d").date()
                                except:
                                    continue

                            days_until = (next_due_date - today.date()).days
                            if days_until < 0:
                                pm_status = "Overdue"
                                break
                            elif days_until <= 7:
                                pm_status = "Due Soon"
                            elif pm_status == "No PM Scheduled":
                                pm_status = "On Schedule"

                    if pm_status == "No PM Scheduled":
                        pm_status = "On Schedule"

                assets_with_status.append({
                    "asset_id": asset_id,
                    "name": asset.get("name", "Unknown Asset"),
                    "location": asset.get("location", ""),
                    "pm_status": pm_status,
                    "pm_count": len(pm_rules_for_asset),
                })

            return JSONResponse(content={"assets": assets_with_status})
        except Exception as e:
            logger.error(f"Error fetching asset PM status: {e}")
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
    pm_status = planner_service.get_asset_pm_status()
    return JSONResponse(content={"assets": pm_status})


@router.get("/parts-availability")
async def get_parts_availability(request: Request):
    """Get parts availability for scheduled work - real Firestore data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    if current_user and current_user.organization_id:
        try:
            firestore_manager = get_firestore_manager()

            # Get parts/inventory from Firestore
            parts_data = await firestore_manager.get_collection(
                "parts",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}],
                limit=100
            )

            # Find low stock items
            low_stock_items = []
            parts_needed = []

            for part in parts_data:
                current_stock = part.get("current_stock", part.get("quantity", 0))
                min_stock = part.get("minimum_stock", part.get("min_quantity", 0))

                if current_stock <= min_stock:
                    low_stock_items.append({
                        "part_id": part.get("id"),
                        "part_name": part.get("name", "Unknown Part"),
                        "part_number": part.get("part_number", ""),
                        "quantity": current_stock,
                        "min_quantity": min_stock,
                        "status": "critical" if current_stock == 0 else "low"
                    })

            return JSONResponse(content={
                "low_stock_items": low_stock_items,
                "parts_needed": parts_needed,
                "total_parts": len(parts_data),
                "low_stock_count": len(low_stock_items)
            })
        except Exception as e:
            logger.error(f"Error fetching parts availability: {e}")
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
    parts = planner_service.get_parts_availability()
    return JSONResponse(content=parts)


@router.get("/conflicts")
async def get_conflicts(request: Request):
    """Get scheduling conflicts - real Firestore data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    if current_user and current_user.organization_id:
        try:
            firestore_manager = get_firestore_manager()

            # Get work orders to analyze for conflicts
            work_orders_data = await firestore_manager.get_collection(
                "work_orders",
                filters=[
                    {"field": "organization_id", "operator": "==", "value": current_user.organization_id},
                    {"field": "status", "operator": "in", "value": ["Open", "In Progress"]}
                ],
                limit=100
            )

            # Analyze for conflicts (multiple WOs same day/technician)
            conflicts = []
            tech_date_map = {}

            for wo in work_orders_data:
                assigned_to = wo.get("assigned_to_uid")
                due_date = wo.get("due_date")

                if assigned_to and due_date:
                    if hasattr(due_date, 'strftime'):
                        date_str = due_date.strftime("%Y-%m-%d")
                    else:
                        date_str = str(due_date)[:10]

                    key = f"{assigned_to}_{date_str}"
                    if key not in tech_date_map:
                        tech_date_map[key] = []
                    tech_date_map[key].append(wo)

            # Find conflicts (more than 8 hours of work on same day)
            for key, wos in tech_date_map.items():
                if len(wos) > 1:
                    total_hours = sum(wo.get("estimated_hours", 2) for wo in wos)
                    if total_hours > 8:
                        tech_id, date_str = key.rsplit("_", 1)
                        conflicts.append({
                            "technician_id": tech_id,
                            "technician_name": tech_id,  # Could lookup name
                            "date": date_str,
                            "work_order_count": len(wos),
                            "total_hours": total_hours,
                            "conflict_type": "Overbooked"
                        })

            return JSONResponse(content={"conflicts": conflicts})
        except Exception as e:
            logger.error(f"Error fetching conflicts: {e}")
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
    conflicts = planner_service.get_scheduling_conflicts()
    return JSONResponse(content={"conflicts": conflicts})


@router.get("/compliance")
async def get_compliance(request: Request):
    """Get compliance tracking data - real Firestore data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    if current_user and current_user.organization_id:
        try:
            firestore_manager = get_firestore_manager()

            # Get assets and their PM status for compliance
            assets_data = await firestore_manager.get_collection(
                "assets",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}],
                limit=100
            )

            # Get PM schedule rules
            pm_rules = await firestore_manager.get_collection(
                "pm_schedule_rules",
                filters=[
                    {"field": "organization_id", "operator": "==", "value": current_user.organization_id},
                    {"field": "is_active", "operator": "==", "value": True}
                ]
            )

            today = datetime.now()
            compliant = 0
            due_soon = 0
            overdue = 0
            never_inspected = 0

            # Create asset PM map
            asset_pm_map = {}
            for rule in pm_rules:
                asset_id = rule.get("asset_id")
                if asset_id:
                    if asset_id not in asset_pm_map:
                        asset_pm_map[asset_id] = []
                    asset_pm_map[asset_id].append(rule)

            for asset in assets_data:
                asset_id = asset.get("id")
                rules = asset_pm_map.get(asset_id, [])

                if not rules:
                    never_inspected += 1
                else:
                    asset_status = "compliant"
                    for rule in rules:
                        next_due = rule.get("next_due_date")
                        if next_due:
                            if hasattr(next_due, 'date'):
                                next_due_date = next_due.date()
                            else:
                                try:
                                    next_due_date = datetime.strptime(str(next_due)[:10], "%Y-%m-%d").date()
                                except:
                                    continue

                            days_until = (next_due_date - today.date()).days
                            if days_until < 0:
                                asset_status = "overdue"
                                break
                            elif days_until <= 7:
                                asset_status = "due_soon"

                    if asset_status == "overdue":
                        overdue += 1
                    elif asset_status == "due_soon":
                        due_soon += 1
                    else:
                        compliant += 1

            return JSONResponse(content={
                "compliant": compliant,
                "due_soon": due_soon,
                "overdue": overdue,
                "never_inspected": never_inspected,
                "total_assets": len(assets_data)
            })
        except Exception as e:
            logger.error(f"Error fetching compliance: {e}")
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
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
async def get_planner_summary(request: Request):
    """Get comprehensive planner summary - real Firestore data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    if current_user and current_user.organization_id:
        try:
            firestore_manager = get_firestore_manager()
            today = datetime.now().strftime("%Y-%m-%d")

            # Get work orders
            work_orders_data = await firestore_manager.get_collection(
                "work_orders",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}],
                limit=200
            )

            # Get users for technician count
            users_data = await firestore_manager.get_collection(
                "users",
                filters=[{"field": "organization_id", "operator": "==", "value": current_user.organization_id}],
                limit=50
            )

            # Calculate backlog stats
            total_backlog = 0
            overdue_count = 0
            due_today_count = 0
            high_priority_count = 0
            by_priority = {}

            for wo in work_orders_data:
                status = wo.get("status", "")
                if status != "Completed":
                    total_backlog += 1

                    due_date = wo.get("due_date")
                    if due_date:
                        if hasattr(due_date, 'strftime'):
                            due_str = due_date.strftime("%Y-%m-%d")
                        else:
                            due_str = str(due_date)[:10]

                        if due_str < today:
                            overdue_count += 1
                        elif due_str == today:
                            due_today_count += 1

                    priority = wo.get("priority", "medium").lower()
                    by_priority[priority] = by_priority.get(priority, 0) + 1
                    if priority in ["high", "critical", "urgent"]:
                        high_priority_count += 1

            # Count technicians
            technician_count = sum(1 for u in users_data if u.get("role", "").lower() in ["technician", "tech", "manager", "owner", "admin"])

            summary = {
                "backlog_count": total_backlog,
                "overdue_count": overdue_count,
                "technician_count": technician_count,
                "average_capacity": 0,  # Would need workload calculation
                "conflict_count": 0,  # Simplified for now
                "compliance_overdue": 0,
                "compliance_due_soon": 0,
                "work_orders_logged": total_backlog,
                "due_today_count": due_today_count,
                "high_priority_count": high_priority_count,
            }

            return JSONResponse(content=summary)
        except Exception as e:
            logger.error(f"Error fetching planner summary: {e}")
            # Fall through to mock data

    # Demo/unauthenticated - use mock data
    try:
        backlog = planner_service.get_work_order_backlog()
        capacity = planner_service.get_resource_capacity()
        conflicts = planner_service.get_scheduling_conflicts()
        compliance = planner_service.get_compliance_tracking()

        summary = {
            "backlog_count": backlog.get("total_backlog", 0),
            "overdue_count": backlog.get("overdue_count", 0),
            "technician_count": capacity.get("total_technicians", 0),
            "average_capacity": capacity.get("average_capacity", 0.0),
            "conflict_count": len(conflicts) if isinstance(conflicts, list) else 0,
            "compliance_overdue": compliance.get("overdue", 0),
            "compliance_due_soon": compliance.get("due_soon", 0),
            "work_orders_logged": backlog.get("total_backlog", 0),
            "due_today_count": backlog.get("due_today_count", 0),
            "high_priority_count": backlog.get("by_priority", {}).get("high", 0)
            + backlog.get("by_priority", {}).get("urgent", 0),
        }

        return JSONResponse(content=summary)

    except Exception as e:
        return JSONResponse(
            content={
                "backlog_count": 0,
                "overdue_count": 0,
                "technician_count": 0,
                "average_capacity": 0,
                "conflict_count": 0,
                "compliance_overdue": 0,
                "compliance_due_soon": 0,
                "work_orders_logged": 0,
                "due_today_count": 0,
                "high_priority_count": 0,
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
