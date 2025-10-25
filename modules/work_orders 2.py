"""
Work Orders Module - Handles all work order related operations
"""

import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .shared import success_response, error_response, logger

router = APIRouter()

# Pydantic models
class WorkOrderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: str = Field("Medium", pattern="^(Low|Medium|High|Critical)$")
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    asset_id: Optional[int] = None
    estimated_hours: Optional[float] = None

class WorkOrderCreate(WorkOrderBase):
    pass

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = Field(None, pattern="^(Low|Medium|High|Critical)$")
    status: Optional[str] = Field(None, pattern="^(Open|In Progress|On Hold|Completed|Cancelled)$")
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    asset_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

# Sample data (in production, this would come from database)
work_orders_data = [
    {
        "id": 1,
        "code": "WO-2025-001",
        "title": "Replace HVAC Filter - Building A",
        "description": "Monthly replacement of HEPA filter in main HVAC unit",
        "status": "Open",
        "priority": "Medium",
        "requested_by": "Facility Manager",
        "assigned_to": "John Smith",
        "asset_id": 101,
        "due_date": "2025-10-25T17:00:00Z",
        "estimated_hours": 2.0,
        "actual_hours": None,
        "created_at": "2025-10-22T10:00:00Z",
        "updated_at": "2025-10-22T10:00:00Z"
    },
    {
        "id": 2,
        "code": "WO-2025-002", 
        "title": "Fire Safety Equipment Inspection",
        "description": "Quarterly inspection of all fire extinguishers and smoke detectors",
        "status": "In Progress",
        "priority": "High",
        "requested_by": "Safety Officer",
        "assigned_to": "Sarah Johnson",
        "asset_id": 102,
        "due_date": "2025-10-23T17:00:00Z",
        "estimated_hours": 4.0,
        "actual_hours": 2.5,
        "created_at": "2025-10-22T08:00:00Z",
        "updated_at": "2025-10-22T14:30:00Z"
    },
    {
        "id": 3,
        "code": "WO-2025-003",
        "title": "Elevator Annual Inspection - Tower A",
        "description": "Annual safety inspection and certification of passenger elevator",
        "status": "Completed",
        "priority": "High",
        "requested_by": "Building Operations",
        "assigned_to": "Mike Chen",
        "asset_id": 103,
        "due_date": "2025-10-20T17:00:00Z",
        "estimated_hours": 6.0,
        "actual_hours": 5.5,
        "created_at": "2025-10-15T09:00:00Z",
        "updated_at": "2025-10-20T16:30:00Z"
    },
    {
        "id": 4,
        "code": "WO-2025-004",
        "title": "Parking Lot Light Replacement",
        "description": "Replace burned out LED fixtures in employee parking area",
        "status": "Open",
        "priority": "Low",
        "requested_by": "Security Team",
        "assigned_to": "David Wilson",
        "asset_id": 104,
        "due_date": "2025-10-30T17:00:00Z",
        "estimated_hours": 3.0,
        "actual_hours": None,
        "created_at": "2025-10-23T14:00:00Z",
        "updated_at": "2025-10-23T14:00:00Z"
    },
    {
        "id": 5,
        "code": "WO-2025-005",
        "title": "Backup Generator Load Testing",
        "description": "Monthly load test of emergency backup generator system",
        "status": "On Hold",
        "priority": "Critical",
        "requested_by": "Facilities Manager",
        "assigned_to": "Sarah Johnson",
        "asset_id": 105,
        "due_date": "2025-10-18T17:00:00Z",
        "estimated_hours": 4.0,
        "actual_hours": None,
        "created_at": "2025-10-14T11:00:00Z",
        "updated_at": "2025-10-19T09:15:00Z"
    },
    {
        "id": 6,
        "code": "WO-2025-006",
        "title": "Roof Leak Repair - Building B",
        "description": "Emergency repair of roof leak in conference room area",
        "status": "In Progress",
        "priority": "Critical",
        "requested_by": "Operations Manager",
        "assigned_to": "John Smith",
        "asset_id": 106,
        "due_date": "2025-10-24T12:00:00Z",
        "estimated_hours": 8.0,
        "actual_hours": 4.0,
        "created_at": "2025-10-23T08:30:00Z",
        "updated_at": "2025-10-24T10:00:00Z"
    },
    {
        "id": 7,
        "code": "WO-2025-007",
        "title": "Plumbing Preventive Maintenance",
        "description": "Quarterly preventive maintenance on all restroom fixtures",
        "status": "Completed",
        "priority": "Medium",
        "requested_by": "Facilities Team",
        "assigned_to": "Mike Chen",
        "asset_id": 107,
        "due_date": "2025-10-15T17:00:00Z",
        "estimated_hours": 5.0,
        "actual_hours": 4.5,
        "created_at": "2025-10-10T10:00:00Z",
        "updated_at": "2025-10-15T15:30:00Z"
    },
    {
        "id": 8,
        "code": "WO-2025-008",
        "title": "IT Server Room Cooling Check",
        "description": "Verify server room HVAC is maintaining proper temperature and humidity",
        "status": "Open",
        "priority": "High",
        "requested_by": "IT Operations",
        "assigned_to": "David Wilson",
        "asset_id": 108,
        "due_date": "2025-10-26T17:00:00Z",
        "estimated_hours": 2.0,
        "actual_hours": None,
        "created_at": "2025-10-24T13:00:00Z",
        "updated_at": "2025-10-24T13:00:00Z"
    }
]

activity_data = {
    1: [
        {
            "id": 1,
            "work_order_id": 1,
            "actor": "System",
            "action": "created",
            "note": "Work order created from maintenance schedule",
            "ts": "2025-10-22T10:00:00Z"
        }
    ],
    2: [
        {
            "id": 2,
            "work_order_id": 2,
            "actor": "System",
            "action": "created", 
            "note": "Work order created",
            "ts": "2025-10-22T08:00:00Z"
        },
        {
            "id": 3,
            "work_order_id": 2,
            "actor": "Sarah Johnson",
            "action": "status_changed",
            "note": "Started inspection of first floor equipment",
            "old_value": "Open",
            "new_value": "In Progress",
            "ts": "2025-10-22T14:30:00Z"
        }
    ]
}

@router.get("/")
async def get_work_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all work orders with optional filtering"""
    filtered_orders = work_orders_data.copy()
    
    if status:
        filtered_orders = [wo for wo in filtered_orders if wo["status"].lower() == status.lower()]
    
    if priority:
        filtered_orders = [wo for wo in filtered_orders if wo["priority"].lower() == priority.lower()]
    
    if assigned_to:
        filtered_orders = [wo for wo in filtered_orders if wo.get("assigned_to") and assigned_to.lower() in wo["assigned_to"].lower()]
    
    # Apply pagination
    total = len(filtered_orders)
    paginated = filtered_orders[offset:offset + limit]
    
    return {
        "work_orders": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get detailed work order with activity and parts"""
    work_order = next((wo for wo in work_orders_data if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Enhance with related data
    result = work_order.copy()
    result["activity"] = activity_data.get(work_order_id, [])
    result["parts_used"] = []  # TODO: Load from parts module
    result["attachments"] = []  # TODO: Load from attachments
    
    return result

@router.post("/")
async def create_work_order(work_order: WorkOrderCreate):
    """Create a new work order"""
    new_id = max([wo["id"] for wo in work_orders_data]) + 1 if work_orders_data else 1
    
    new_work_order = {
        "id": new_id,
        "code": f"WO-2025-{new_id:03d}",
        "title": work_order.title,
        "description": work_order.description,
        "status": "Open",
        "priority": work_order.priority,
        "requested_by": "API User",
        "assigned_to": work_order.assigned_to,
        "asset_id": work_order.asset_id,
        "due_date": work_order.due_date.isoformat() if work_order.due_date else None,
        "estimated_hours": work_order.estimated_hours,
        "actual_hours": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    work_orders_data.append(new_work_order)
    
    # Add activity log entry
    if new_id not in activity_data:
        activity_data[new_id] = []
    
    activity_data[new_id].append({
        "id": len(activity_data) * 10 + 1,
        "work_order_id": new_id,
        "actor": "API User",
        "action": "created",
        "note": "Work order created via API",
        "ts": datetime.now().isoformat()
    })
    
    return success_response("Work order created successfully", {"work_order": new_work_order})

@router.put("/{work_order_id}")
async def update_work_order(work_order_id: int, updates: WorkOrderUpdate):
    """Update work order fields"""
    work_order = next((wo for wo in work_orders_data if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Track changes for activity log
    changes = []
    update_data = updates.dict(exclude_unset=True)
    
    for field, new_value in update_data.items():
        if field in work_order and work_order[field] != new_value:
            old_value = work_order[field]
            work_order[field] = new_value
            changes.append({
                "field": field,
                "old_value": str(old_value) if old_value is not None else None,
                "new_value": str(new_value) if new_value is not None else None
            })
    
    work_order["updated_at"] = datetime.now().isoformat()
    
    # Add activity log entries for changes
    if work_order_id not in activity_data:
        activity_data[work_order_id] = []
    
    for change in changes:
        activity_data[work_order_id].append({
            "id": len(activity_data) * 10 + len(changes) + 1,
            "work_order_id": work_order_id,
            "actor": "API User",
            "action": f"{change['field']}_changed",
            "note": f"Updated {change['field']} from '{change['old_value']}' to '{change['new_value']}'",
            "old_value": change['old_value'],
            "new_value": change['new_value'],
            "ts": datetime.now().isoformat()
        })
    
    return success_response("Work order updated successfully", {"work_order": work_order})

@router.get("/stats/summary")
async def get_work_order_stats():
    """Get work order statistics"""
    total = len(work_orders_data)
    by_status = {}
    by_priority = {}
    by_assignee = {}
    
    overdue_count = 0
    due_soon_count = 0  # Due in next 7 days
    
    for wo in work_orders_data:
        status = wo["status"]
        priority = wo["priority"]
        assignee = wo.get("assigned_to", "Unassigned")
        
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
        by_assignee[assignee] = by_assignee.get(assignee, 0) + 1
        
        # Check due dates
        if wo.get("due_date"):
            due_date = datetime.fromisoformat(wo["due_date"].replace('Z', '+00:00'))
            now = datetime.now(due_date.tzinfo)
            
            if due_date < now and wo["status"] not in ["Completed", "Cancelled"]:
                overdue_count += 1
            elif due_date < now + timedelta(days=7) and wo["status"] not in ["Completed", "Cancelled"]:
                due_soon_count += 1
    
    return {
        "total_work_orders": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_assignee": by_assignee,
        "overdue_count": overdue_count,
        "due_soon_count": due_soon_count,
        "completion_rate": (by_status.get("Completed", 0) / total * 100) if total > 0 else 0
    }

@router.get("/export.csv")
async def export_work_orders_csv(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None)
):
    """Export work orders as CSV"""
    filtered_orders = work_orders_data.copy()
    
    if status:
        filtered_orders = [wo for wo in filtered_orders if wo["status"].lower() == status.lower()]
    if priority:
        filtered_orders = [wo for wo in filtered_orders if wo["priority"].lower() == priority.lower()]
    if assigned_to:
        filtered_orders = [wo for wo in filtered_orders if wo.get("assigned_to") and assigned_to.lower() in wo["assigned_to"].lower()]
    
    # Create DataFrame
    df = pd.DataFrame(filtered_orders)
    
    # Generate CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=work_orders_export.csv"}
    )