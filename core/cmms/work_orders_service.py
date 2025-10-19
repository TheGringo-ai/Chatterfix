#!/usr/bin/env python3
"""
ChatterFix CMMS - Work Orders Service (Port 8002)
Handles all work order operations for the microservices architecture
"""

import os
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(title="ChatterFix Work Orders Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database service URL
DATABASE_SERVICE_URL = "http://localhost:8012"

# Pydantic models
class WorkOrder(BaseModel):
    title: str
    description: Optional[str] = ""
    status: Optional[str] = "open"
    priority: Optional[str] = "medium"
    asset_id: Optional[int] = None
    technician: Optional[str] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    asset_id: Optional[int] = None
    technician: Optional[str] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

def call_database_service(endpoint: str, method: str = "GET", data: Dict = None):
    """Call the database service"""
    try:
        url = f"{DATABASE_SERVICE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Database service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database service error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_response = call_database_service("/health")
        
        return {
            "status": "healthy",
            "service": "ChatterFix Work Orders Service",
            "port": 8002,
            "database_status": db_response.get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/work_orders")
async def get_work_orders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: Optional[int] = 100
):
    """Get work orders with optional filtering"""
    try:
        query = "SELECT * FROM work_orders"
        params = {}
        conditions = []
        
        if status:
            conditions.append("status = :status")
            params["status"] = status
        
        if priority:
            conditions.append("priority = :priority")
            params["priority"] = priority
        
        if assigned_to:
            conditions.append("technician = :assigned_to")
            params["assigned_to"] = assigned_to
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        response = call_database_service(
            "/api/query",
            "POST",
            {"query": query, "params": params}
        )
        
        if response.get("success"):
            return {"success": True, "work_orders": response.get("data", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work_orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get a specific work order by ID"""
    try:
        response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT * FROM work_orders WHERE id = :id",
                "params": {"id": work_order_id}
            }
        )
        
        if response.get("success"):
            data = response.get("data", [])
            if data:
                return {"success": True, "work_order": data[0]}
            else:
                raise HTTPException(status_code=404, detail="Work order not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work_orders")
async def create_work_order(work_order: WorkOrder):
    """Create a new work order"""
    try:
        query = """
            INSERT INTO work_orders 
            (title, description, status, priority, asset_id, assigned_to, due_date, estimated_hours, created_at)
            VALUES (:title, :description, :status, :priority, :asset_id, :assigned_to, :due_date, :estimated_hours, :created_at)
        """
        
        params = {
            "title": work_order.title,
            "description": work_order.description,
            "status": work_order.status,
            "priority": work_order.priority,
            "asset_id": work_order.asset_id,
            "assigned_to": work_order.technician,
            "due_date": work_order.due_date,
            "estimated_hours": work_order.estimated_hours,
            "created_at": datetime.now().isoformat()
        }
        
        response = call_database_service(
            "/api/execute",
            "POST",
            {"query": query, "params": params}
        )
        
        if response.get("success"):
            return {
                "success": True,
                "message": "Work order created successfully",
                "rows_affected": response.get("rows_affected", 0)
            }
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to create work order"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/work_orders/{work_order_id}")
async def update_work_order(work_order_id: int, updates: WorkOrderUpdate):
    """Update an existing work order"""
    try:
        # Build dynamic update query
        update_fields = []
        params = {"id": work_order_id}
        
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add completion timestamp if status is being set to completed
        if updates.status == "completed":
            update_fields.append("completed_at = :completed_at")
            params["completed_at"] = datetime.now().isoformat()
        
        query = f"UPDATE work_orders SET {', '.join(update_fields)} WHERE id = :id"
        
        response = call_database_service(
            "/api/execute",
            "POST",
            {"query": query, "params": params}
        )
        
        if response.get("success"):
            rows_affected = response.get("rows_affected", 0)
            if rows_affected > 0:
                return {
                    "success": True,
                    "message": "Work order updated successfully",
                    "rows_affected": rows_affected
                }
            else:
                raise HTTPException(status_code=404, detail="Work order not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to update work order"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/work_orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete a work order"""
    try:
        response = call_database_service(
            "/api/execute",
            "POST",
            {
                "query": "DELETE FROM work_orders WHERE id = :id",
                "params": {"id": work_order_id}
            }
        )
        
        if response.get("success"):
            rows_affected = response.get("rows_affected", 0)
            if rows_affected > 0:
                return {
                    "success": True,
                    "message": "Work order deleted successfully",
                    "rows_affected": rows_affected
                }
            else:
                raise HTTPException(status_code=404, detail="Work order not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to delete work order"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work_orders/stats/dashboard")
async def get_work_order_stats():
    """Get work order statistics for dashboard"""
    try:
        # Get status counts
        status_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT status, COUNT(*) as count FROM work_orders GROUP BY status"}
        )
        
        # Get priority counts
        priority_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT priority, COUNT(*) as count FROM work_orders GROUP BY priority"}
        )
        
        # Get overdue count
        overdue_response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT COUNT(*) as count FROM work_orders WHERE due_date < :now AND status != 'completed'",
                "params": {"now": datetime.now().isoformat()}
            }
        )
        
        stats = {
            "status_breakdown": status_response.get("data", []) if status_response.get("success") else [],
            "priority_breakdown": priority_response.get("data", []) if priority_response.get("success") else [],
            "overdue_count": overdue_response.get("data", [{}])[0].get("count", 0) if overdue_response.get("success") else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return {"success": True, "stats": stats}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatterFix Work Orders Service')
    parser.add_argument('--port', type=int, default=8002, help='Port to run service on')
    
    args = parser.parse_args()
    
    print(f"🔧 Starting ChatterFix Work Orders Service on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)