#!/usr/bin/env python3
"""
ChatterFix Work Orders Service - Microservice Entry Point
Enhanced work order management with AI integration
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Work Orders Service",
    description="Enterprise work order management microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class WorkOrder(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    status: str = "Open"
    priority: str = "Medium"
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    asset_id: Optional[int] = None

class WorkOrderCreate(BaseModel):
    title: str
    description: str
    priority: str = "Medium"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    asset_id: Optional[int] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "work_orders", 
        "status": "running",
        "version": "7.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "work_orders",
        "version": "1.0.0", 
        "timestamp": datetime.now().isoformat()
    }

# Sample data for development
sample_work_orders = [
    {
        "id": 1,
        "title": "Replace HVAC Filter",
        "description": "Replace air filter in main HVAC unit",
        "status": "Open",
        "priority": "Medium",
        "assigned_to": "John Smith",
        "created_at": "2025-10-22T10:00:00Z",
        "due_date": "2025-10-25T17:00:00Z",
        "asset_id": 101
    },
    {
        "id": 2,
        "title": "Inspect Fire Safety Equipment",
        "description": "Monthly inspection of fire extinguishers and alarms",
        "status": "In Progress",
        "priority": "High",
        "assigned_to": "Sarah Johnson",
        "created_at": "2025-10-22T08:00:00Z",
        "due_date": "2025-10-23T17:00:00Z",
        "asset_id": 102
    },
    {
        "id": 3,
        "title": "Lubricate Conveyor Belt",
        "description": "Apply lubrication to conveyor belt bearings",
        "status": "Open",
        "priority": "Low",
        "assigned_to": None,
        "created_at": "2025-10-22T12:00:00Z",
        "due_date": "2025-10-28T17:00:00Z",
        "asset_id": 103
    }
]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "work_orders",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/work_orders", response_model=List[Dict[str, Any]])
async def get_work_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee")
):
    """Get all work orders with optional filtering"""
    filtered_orders = sample_work_orders.copy()
    
    if status:
        filtered_orders = [wo for wo in filtered_orders if wo["status"].lower() == status.lower()]
    
    if priority:
        filtered_orders = [wo for wo in filtered_orders if wo["priority"].lower() == priority.lower()]
    
    if assigned_to:
        filtered_orders = [wo for wo in filtered_orders if wo.get("assigned_to") and assigned_to.lower() in wo["assigned_to"].lower()]
    
    return filtered_orders

@app.get("/work_orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get a specific work order by ID"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    return work_order

@app.post("/work_orders", response_model=Dict[str, Any])
async def create_work_order(work_order: WorkOrderCreate):
    """Create a new work order"""
    new_id = max([wo["id"] for wo in sample_work_orders]) + 1 if sample_work_orders else 1
    
    new_work_order = {
        "id": new_id,
        "title": work_order.title,
        "description": work_order.description,
        "status": "Open",
        "priority": work_order.priority,
        "assigned_to": work_order.assigned_to,
        "created_at": datetime.now().isoformat(),
        "due_date": work_order.due_date.isoformat() if work_order.due_date else None,
        "asset_id": work_order.asset_id
    }
    
    sample_work_orders.append(new_work_order)
    return new_work_order

@app.put("/work_orders/{work_order_id}")
async def update_work_order(work_order_id: int, status: str):
    """Update work order status"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    work_order["status"] = status
    return work_order

@app.delete("/work_orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete a work order"""
    global sample_work_orders
    sample_work_orders = [wo for wo in sample_work_orders if wo["id"] != work_order_id]
    return {"message": "Work order deleted successfully"}

@app.get("/work_orders/stats/summary")
async def get_work_order_stats():
    """Get work order statistics"""
    total = len(sample_work_orders)
    by_status = {}
    by_priority = {}
    
    for wo in sample_work_orders:
        status = wo["status"]
        priority = wo["priority"]
        
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
    
    return {
        "total_work_orders": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "completion_rate": (by_status.get("Completed", 0) / total * 100) if total > 0 else 0
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)