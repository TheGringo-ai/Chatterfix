#!/usr/bin/env python3
"""
Work Orders Module
Easily editable work order management system
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

# Work Order Models
class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class Status(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WorkOrder(BaseModel):
    id: str
    title: str
    description: str
    priority: Priority
    status: Status
    assigned_to: Optional[str] = None
    equipment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class WorkOrderCreate(BaseModel):
    title: str
    description: str
    priority: Priority = Priority.NORMAL
    assigned_to: Optional[str] = None
    equipment_id: Optional[str] = None

# In-memory work orders database
work_orders_db = {}

@router.get("/", response_model=List[WorkOrder])
async def get_all_work_orders():
    """Get all work orders"""
    return list(work_orders_db.values())

@router.get("/{work_order_id}", response_model=WorkOrder)
async def get_work_order(work_order_id: str):
    """Get specific work order by ID"""
    if work_order_id not in work_orders_db:
        raise HTTPException(status_code=404, detail="Work order not found")
    return work_orders_db[work_order_id]

@router.post("/", response_model=WorkOrder)
async def create_work_order(work_order: WorkOrderCreate):
    """Create new work order"""
    work_order_id = f"WO_{len(work_orders_db) + 1:06d}"
    new_work_order = WorkOrder(
        id=work_order_id,
        **work_order.dict(),
        status=Status.OPEN,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    work_orders_db[work_order_id] = new_work_order
    return new_work_order

@router.put("/{work_order_id}/status")
async def update_work_order_status(work_order_id: str, status: Status):
    """Update work order status"""
    if work_order_id not in work_orders_db:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    work_order = work_orders_db[work_order_id]
    work_order.status = status
    work_order.updated_at = datetime.now()
    
    if status == Status.COMPLETED:
        work_order.completed_at = datetime.now()
    
    return work_order

@router.get("/priority/{priority}")
async def get_work_orders_by_priority(priority: Priority):
    """Get work orders by priority level"""
    return [wo for wo in work_orders_db.values() if wo.priority == priority]

@router.get("/status/{status}")
async def get_work_orders_by_status(status: Status):
    """Get work orders by status"""
    return [wo for wo in work_orders_db.values() if wo.status == status]