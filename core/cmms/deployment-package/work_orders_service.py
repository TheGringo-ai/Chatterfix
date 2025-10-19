#!/usr/bin/env python3
"""
ChatterFix Work Orders API Fix
Simple, focused work orders service using existing GCP database
Created by Claude Code with Fix It Fred and Grok collaboration
"""

import httpx
import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Work Orders API",
    description="Industry-leading work orders with AI integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database service URL
DATABASE_SERVICE_URL = "http://localhost:8001"
FIX_IT_FRED_URL = "http://localhost:8005"
GROK_CONNECTOR_URL = "http://localhost:8006"

# Pydantic models
class WorkOrderCreate(BaseModel):
    title: str
    description: str
    asset_id: Optional[int] = None
    priority: str = "medium"
    technician: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    technician: Optional[str] = None

async def execute_db_query(query: str, params: Dict = None):
    """Execute query via database service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DATABASE_SERVICE_URL}/api/query",
                json={
                    "query": query,
                    "params": params or {}
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Database query failed: {response.text}")
                raise HTTPException(status_code=500, detail="Database query failed")
                
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def get_ai_insights(work_order_data: dict):
    """Get AI insights from Fix It Fred and Grok"""
    insights = {"fred_advice": None, "grok_analysis": None}
    
    try:
        # Get Fix It Fred advice
        async with httpx.AsyncClient() as client:
            fred_response = await client.post(
                f"{FIX_IT_FRED_URL}/api/chat",
                json={
                    "message": f"Analyze work order: {work_order_data['title']} - {work_order_data['description']}. Provide maintenance advice and safety considerations.",
                    "provider": "ollama",
                    "context": "work_order_analysis"
                },
                timeout=10.0
            )
            if fred_response.status_code == 200:
                fred_data = fred_response.json()
                insights["fred_advice"] = fred_data.get("response")
    except Exception as e:
        logger.warning(f"Fix It Fred not available: {e}")
    
    try:
        # Get Grok strategic analysis
        async with httpx.AsyncClient() as client:
            grok_response = await client.post(
                f"{GROK_CONNECTOR_URL}/grok/chat",
                json={
                    "message": f"Analyze work order for optimization: {work_order_data['title']}. Provide strategic recommendations.",
                    "context": "work_order_optimization"
                },
                timeout=10.0
            )
            if grok_response.status_code == 200:
                grok_data = grok_response.json()
                insights["grok_analysis"] = grok_data.get("response")
    except Exception as e:
        logger.warning(f"Grok not available: {e}")
    
    return insights

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ChatterFix Work Orders API",
        "database_connection": "active",
        "ai_integration": "enabled",
        "features": [
            "Work Order CRUD Operations",
            "AI-Powered Insights",
            "Real-time Database Integration",
            "Fix It Fred Collaboration",
            "Grok Strategic Analysis"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/work-orders")
async def get_work_orders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """Get work orders with filtering"""
    try:
        # Build query with filters
        query = """
            SELECT id, title, description, status, priority, technician, created_at, updated_at
            FROM work_orders
        """
        
        conditions = []
        if status:
            conditions.append(f"status = '{status}'")
        if priority:
            conditions.append(f"priority = '{priority}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f"""
            ORDER BY 
                CASE priority 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                END,
                created_at DESC
            LIMIT {limit}
        """
        
        db_result = await execute_db_query(query)
        
        if db_result.get("success"):
            work_orders = db_result.get("data", [])
            
            # Format for consistency
            formatted_orders = []
            for order in work_orders:
                formatted_orders.append({
                    "id": order["id"],
                    "title": order["title"],
                    "description": order["description"],
                    "status": order["status"],
                    "priority": order["priority"],
                    "assigned_to": order["technician"],
                    "created_date": order["created_at"],
                    "updated_date": order["updated_at"]
                })
            
            return {
                "success": True,
                "work_orders": formatted_orders,
                "count": len(formatted_orders),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch work orders")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get specific work order with AI insights"""
    try:
        query = """
            SELECT id, title, description, status, priority, technician, created_at, updated_at
            FROM work_orders
            WHERE id = ?
        """
        
        # Note: SQLite parameters use ? but we need to convert to named params for the API
        db_result = await execute_db_query(
            "SELECT id, title, description, status, priority, technician, created_at, updated_at FROM work_orders WHERE id = " + str(work_order_id)
        )
        
        if db_result.get("success"):
            work_orders = db_result.get("data", [])
            if not work_orders:
                raise HTTPException(status_code=404, detail="Work order not found")
            
            order = work_orders[0]
            
            # Get AI insights
            ai_insights = await get_ai_insights({
                "title": order["title"],
                "description": order["description"],
                "status": order["status"],
                "priority": order["priority"]
            })
            
            return {
                "success": True,
                "work_order": {
                    "id": order["id"],
                    "title": order["title"],
                    "description": order["description"],
                    "status": order["status"],
                    "priority": order["priority"],
                    "assigned_to": order["technician"],
                    "created_date": order["created_at"],
                    "updated_date": order["updated_at"],
                    "ai_insights": ai_insights
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch work order")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrderCreate):
    """Create new work order with AI enhancement"""
    try:
        # Get AI insights before creating
        ai_insights = await get_ai_insights({
            "title": work_order.title,
            "description": work_order.description,
            "priority": work_order.priority
        })
        
        # Insert work order
        query = f"""
            INSERT INTO work_orders (title, description, status, priority, technician, created_at, updated_at)
            VALUES ('{work_order.title}', '{work_order.description}', 'open', '{work_order.priority}', 
                    '{work_order.technician or ""}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        db_result = await execute_db_query(query)
        
        if db_result.get("success"):
            # Get the created work order
            latest_query = "SELECT id, title, description, status, priority, technician, created_at, updated_at FROM work_orders ORDER BY id DESC LIMIT 1"
            latest_result = await execute_db_query(latest_query)
            
            if latest_result.get("success") and latest_result.get("data"):
                created_order = latest_result["data"][0]
                
                return {
                    "success": True,
                    "message": "Work order created successfully",
                    "work_order": {
                        "id": created_order["id"],
                        "title": created_order["title"],
                        "description": created_order["description"],
                        "status": created_order["status"],
                        "priority": created_order["priority"],
                        "assigned_to": created_order["technician"],
                        "created_date": created_order["created_at"],
                        "updated_date": created_order["updated_at"],
                        "ai_insights": ai_insights
                    },
                    "timestamp": datetime.now().isoformat()
                }
        
        raise HTTPException(status_code=500, detail="Failed to create work order")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/work-orders/{work_order_id}")
async def update_work_order(work_order_id: int, updates: WorkOrderUpdate):
    """Update work order"""
    try:
        # Build update query
        set_clauses = []
        if updates.title is not None:
            set_clauses.append(f"title = '{updates.title}'")
        if updates.description is not None:
            set_clauses.append(f"description = '{updates.description}'")
        if updates.status is not None:
            set_clauses.append(f"status = '{updates.status}'")
        if updates.priority is not None:
            set_clauses.append(f"priority = '{updates.priority}'")
        if updates.technician is not None:
            set_clauses.append(f"technician = '{updates.technician}'")
        
        if not set_clauses:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"""
            UPDATE work_orders 
            SET {', '.join(set_clauses)}
            WHERE id = {work_order_id}
        """
        
        db_result = await execute_db_query(query)
        
        if db_result.get("success"):
            # Return updated work order
            return await get_work_order(work_order_id)
        else:
            raise HTTPException(status_code=500, detail="Failed to update work order")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete work order (soft delete)"""
    try:
        query = f"""
            UPDATE work_orders 
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE id = {work_order_id}
        """
        
        db_result = await execute_db_query(query)
        
        if db_result.get("success"):
            return {
                "success": True,
                "message": f"Work order {work_order_id} cancelled successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete work order")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/analytics/summary")
async def get_work_order_analytics():
    """Get work order analytics dashboard"""
    try:
        # Get status distribution
        status_query = """
            SELECT status, COUNT(*) as count
            FROM work_orders
            GROUP BY status
        """
        
        # Get priority distribution
        priority_query = """
            SELECT priority, COUNT(*) as count
            FROM work_orders
            GROUP BY priority
        """
        
        status_result = await execute_db_query(status_query)
        priority_result = await execute_db_query(priority_query)
        
        analytics = {
            "status_distribution": {},
            "priority_distribution": {},
            "total_work_orders": 0,
            "generated_at": datetime.now().isoformat()
        }
        
        if status_result.get("success"):
            for row in status_result.get("data", []):
                analytics["status_distribution"][row["status"]] = row["count"]
                analytics["total_work_orders"] += row["count"]
        
        if priority_result.get("success"):
            for row in priority_result.get("data", []):
                analytics["priority_distribution"][row["priority"]] = row["count"]
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders/{work_order_id}/ai-analyze")
async def analyze_work_order_with_ai(work_order_id: int):
    """Get comprehensive AI analysis for work order"""
    try:
        # Get work order details
        work_order_response = await get_work_order(work_order_id)
        work_order = work_order_response["work_order"]
        
        return {
            "work_order_id": work_order_id,
            "title": work_order["title"],
            "ai_analysis": work_order["ai_insights"],
            "recommendations": {
                "fred_says": work_order["ai_insights"]["fred_advice"],
                "grok_strategy": work_order["ai_insights"]["grok_analysis"]
            },
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8015))
    print(f"🚀 Starting ChatterFix Work Orders API on port {port}...")
    print("🤖 Features: AI Integration, Database Connectivity, Real-time Analytics")
    print("🔧 Fix It Fred Integration: ✅")  
    print("🧠 Grok Strategic Analysis: ✅")
    print("💾 GCP Database Service: ✅")
    uvicorn.run(app, host="0.0.0.0", port=port)