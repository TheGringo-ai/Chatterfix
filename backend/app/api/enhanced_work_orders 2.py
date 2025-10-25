#!/usr/bin/env python3
"""
ChatterFix CMMS - Enhanced Work Orders Service
Industry-leading work order management with AI integration
Created by Claude Code in collaboration with Fix It Fred and Grok AI
"""

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import asyncio
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Enhanced Work Orders Service",
    description="Industry-leading work order management with AI integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database service URL (using existing GCP database)
DATABASE_SERVICE_URL = "http://localhost:8001"

# AI Services URLs  
FIX_IT_FRED_URL = "http://localhost:8005"
GROK_CONNECTOR_URL = "http://localhost:8006"

# Enums for better data integrity
class WorkOrderStatus(str, Enum):
    DRAFT = "Draft"
    OPEN = "Open" 
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    CLOSED = "Closed"

class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class WorkOrderType(str, Enum):
    CORRECTIVE = "Corrective"
    PREVENTIVE = "Preventive"
    PREDICTIVE = "Predictive"
    EMERGENCY = "Emergency"
    INSPECTION = "Inspection"
    CALIBRATION = "Calibration"

# Pydantic models
class WorkOrderCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    asset_id: Optional[int] = None
    priority: Priority = Priority.MEDIUM
    work_order_type: WorkOrderType = WorkOrderType.CORRECTIVE
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0.1, le=999.9)
    due_date: Optional[str] = None
    parts_required: Optional[List[str]] = Field(default_factory=list)
    safety_requirements: Optional[str] = None
    skills_required: Optional[List[str]] = Field(default_factory=list)

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkOrderStatus] = None
    priority: Optional[Priority] = None
    assigned_to: Optional[str] = None
    progress_notes: Optional[str] = None
    actual_hours: Optional[float] = None
    completion_notes: Optional[str] = None

class WorkOrderResponse(BaseModel):
    id: int
    title: str
    description: str
    status: WorkOrderStatus
    priority: Priority
    work_order_type: WorkOrderType
    asset_id: Optional[int]
    asset_name: Optional[str]
    assigned_to: Optional[str]
    created_date: str
    updated_date: str
    due_date: Optional[str]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    progress_notes: Optional[str]
    completion_notes: Optional[str]
    parts_required: List[str]
    safety_requirements: Optional[str]
    skills_required: List[str]
    ai_recommendations: Optional[Dict[str, Any]]

async def execute_database_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = True):
    """Execute database query through GCP database service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DATABASE_SERVICE_URL}/api/execute",
                json={
                    "query": query,
                    "params": list(params),
                    "fetch_one": fetch_one,
                    "fetch_all": fetch_all
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Database query failed: {response.text}")
                raise HTTPException(status_code=500, detail="Database query failed")
                
    except httpx.TimeoutException:
        logger.error("Database query timeout")
        raise HTTPException(status_code=500, detail="Database timeout")
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def init_enhanced_work_orders_table():
    """Initialize enhanced work orders table with all industry-standard fields"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Enhanced work orders table with industry-leading features
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enhanced_work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            priority TEXT DEFAULT 'Medium',
            work_order_type TEXT DEFAULT 'Corrective',
            asset_id INTEGER,
            asset_name TEXT,
            assigned_to TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            estimated_hours REAL,
            actual_hours REAL,
            progress_notes TEXT,
            completion_notes TEXT,
            parts_required TEXT, -- JSON array
            safety_requirements TEXT,
            skills_required TEXT, -- JSON array
            ai_recommendations TEXT, -- JSON object
            created_by TEXT,
            updated_by TEXT,
            completion_date TIMESTAMP,
            labor_cost REAL DEFAULT 0.0,
            parts_cost REAL DEFAULT 0.0,
            total_cost REAL DEFAULT 0.0,
            satisfaction_rating INTEGER,
            feedback TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_status ON enhanced_work_orders(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_priority ON enhanced_work_orders(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_assigned ON enhanced_work_orders(assigned_to)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_asset ON enhanced_work_orders(asset_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_created ON enhanced_work_orders(created_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_due ON enhanced_work_orders(due_date)")
    
    conn.commit()
    conn.close()

async def get_ai_recommendations(work_order_data: dict) -> dict:
    """Get AI recommendations from Fix It Fred and Grok for work order optimization"""
    recommendations = {
        "fred_suggestions": None,
        "grok_analysis": None,
        "priority_suggestion": None,
        "estimated_time": None,
        "safety_alerts": [],
        "parts_suggestions": [],
        "similar_work_orders": []
    }
    
    try:
        # Get Fix It Fred recommendations
        async with httpx.AsyncClient() as client:
            fred_response = await client.post(
                f"{FIX_IT_FRED_URL}/api/chat",
                json={
                    "message": f"Analyze this work order: {work_order_data['title']} - {work_order_data['description']}. Provide maintenance recommendations, safety considerations, and estimated time.",
                    "context": "work_order_analysis",
                    "provider": "ollama"
                },
                timeout=10.0
            )
            if fred_response.status_code == 200:
                fred_data = fred_response.json()
                recommendations["fred_suggestions"] = fred_data.get("response")
    except Exception as e:
        logger.warning(f"Fix It Fred AI not available: {e}")
    
    try:
        # Get Grok strategic analysis
        async with httpx.AsyncClient() as client:
            grok_response = await client.post(
                f"{GROK_CONNECTOR_URL}/grok/chat",
                json={
                    "message": f"Provide strategic analysis for work order: {work_order_data['title']}. Focus on optimization, resource allocation, and predictive insights.",
                    "context": "work_order_strategy"
                },
                timeout=10.0
            )
            if grok_response.status_code == 200:
                grok_data = grok_response.json()
                recommendations["grok_analysis"] = grok_data.get("response")
    except Exception as e:
        logger.warning(f"Grok AI not available: {e}")
    
    return recommendations

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing Enhanced Work Orders Service...")
    init_enhanced_work_orders_table()
    logger.info("Enhanced Work Orders Service ready!")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM enhanced_work_orders")
        count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "service": "Enhanced Work Orders Service",
            "database": "connected",
            "work_orders_count": count,
            "features": [
                "AI-Powered Recommendations",
                "Real-time Status Tracking", 
                "Advanced Priority Management",
                "Predictive Analytics",
                "Safety Integration",
                "Cost Tracking",
                "Performance Metrics"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/work-orders", response_model=List[WorkOrderResponse])
async def get_work_orders(
    status: Optional[WorkOrderStatus] = None,
    priority: Optional[Priority] = None,
    assigned_to: Optional[str] = None,
    asset_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get work orders with advanced filtering and pagination"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build dynamic query based on filters
        query = """
            SELECT wo.*, a.name as asset_name
            FROM enhanced_work_orders wo
            LEFT JOIN assets a ON wo.asset_id = a.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND wo.status = ?"
            params.append(status.value)
        if priority:
            query += " AND wo.priority = ?"
            params.append(priority.value)
        if assigned_to:
            query += " AND wo.assigned_to LIKE ?"
            params.append(f"%{assigned_to}%")
        if asset_id:
            query += " AND wo.asset_id = ?"
            params.append(asset_id)
        
        query += """
            ORDER BY 
                CASE wo.priority 
                    WHEN 'Critical' THEN 1 
                    WHEN 'High' THEN 2 
                    WHEN 'Medium' THEN 3 
                    WHEN 'Low' THEN 4 
                END,
                wo.created_date DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        work_orders = []
        for row in rows:
            work_order = WorkOrderResponse(
                id=row[0],
                title=row[1],
                description=row[2],
                status=WorkOrderStatus(row[3]),
                priority=Priority(row[4]),
                work_order_type=WorkOrderType(row[5]),
                asset_id=row[6],
                asset_name=row[26] if len(row) > 26 else None,
                assigned_to=row[8],
                created_date=row[9],
                updated_date=row[10],
                due_date=row[11],
                estimated_hours=row[12],
                actual_hours=row[13],
                progress_notes=row[14],
                completion_notes=row[15],
                parts_required=json.loads(row[16]) if row[16] else [],
                safety_requirements=row[17],
                skills_required=json.loads(row[18]) if row[18] else [],
                ai_recommendations=json.loads(row[19]) if row[19] else None
            )
            work_orders.append(work_order)
        
        return work_orders
        
    except Exception as e:
        logger.error(f"Error getting work orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders", response_model=WorkOrderResponse)
async def create_work_order(work_order: WorkOrderCreate, background_tasks: BackgroundTasks):
    """Create a new work order with AI-powered enhancements"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get asset name if asset_id provided
        asset_name = None
        if work_order.asset_id:
            cursor.execute("SELECT name FROM assets WHERE id = ?", (work_order.asset_id,))
            asset_result = cursor.fetchone()
            if asset_result:
                asset_name = asset_result[0]
        
        # Insert work order
        cursor.execute("""
            INSERT INTO enhanced_work_orders (
                title, description, status, priority, work_order_type, asset_id, asset_name,
                assigned_to, due_date, estimated_hours, parts_required, safety_requirements,
                skills_required, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            work_order.title,
            work_order.description,
            WorkOrderStatus.OPEN.value,
            work_order.priority.value,
            work_order.work_order_type.value,
            work_order.asset_id,
            asset_name,
            work_order.assigned_to,
            work_order.due_date,
            work_order.estimated_hours,
            json.dumps(work_order.parts_required),
            work_order.safety_requirements,
            json.dumps(work_order.skills_required),
            "system"  # TODO: Replace with actual user
        ))
        
        work_order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Get AI recommendations in background
        background_tasks.add_task(
            update_work_order_with_ai_recommendations, 
            work_order_id, 
            work_order.dict()
        )
        
        # Return created work order
        return await get_work_order_by_id(work_order_id)
        
    except Exception as e:
        logger.error(f"Error creating work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_work_order_with_ai_recommendations(work_order_id: int, work_order_data: dict):
    """Background task to get AI recommendations and update work order"""
    try:
        recommendations = await get_ai_recommendations(work_order_data)
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE enhanced_work_orders 
            SET ai_recommendations = ?, updated_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (json.dumps(recommendations), work_order_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"AI recommendations updated for work order {work_order_id}")
        
    except Exception as e:
        logger.error(f"Error updating AI recommendations: {e}")

@app.get("/api/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order_by_id(work_order_id: int):
    """Get specific work order by ID"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT wo.*, a.name as asset_name
            FROM enhanced_work_orders wo
            LEFT JOIN assets a ON wo.asset_id = a.id
            WHERE wo.id = ?
        """, (work_order_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Work order not found")
        
        return WorkOrderResponse(
            id=row[0],
            title=row[1],
            description=row[2],
            status=WorkOrderStatus(row[3]),
            priority=Priority(row[4]),
            work_order_type=WorkOrderType(row[5]),
            asset_id=row[6],
            asset_name=row[26] if len(row) > 26 else None,
            assigned_to=row[8],
            created_date=row[9],
            updated_date=row[10],
            due_date=row[11],
            estimated_hours=row[12],
            actual_hours=row[13],
            progress_notes=row[14],
            completion_notes=row[15],
            parts_required=json.loads(row[16]) if row[16] else [],
            safety_requirements=row[17],
            skills_required=json.loads(row[18]) if row[18] else [],
            ai_recommendations=json.loads(row[19]) if row[19] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(work_order_id: int, updates: WorkOrderUpdate):
    """Update work order with advanced tracking"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        set_clauses = ["updated_date = CURRENT_TIMESTAMP"]
        params = []
        
        if updates.title is not None:
            set_clauses.append("title = ?")
            params.append(updates.title)
        if updates.description is not None:
            set_clauses.append("description = ?")
            params.append(updates.description)
        if updates.status is not None:
            set_clauses.append("status = ?")
            params.append(updates.status.value)
            if updates.status == WorkOrderStatus.COMPLETED:
                set_clauses.append("completion_date = CURRENT_TIMESTAMP")
        if updates.priority is not None:
            set_clauses.append("priority = ?")
            params.append(updates.priority.value)
        if updates.assigned_to is not None:
            set_clauses.append("assigned_to = ?")
            params.append(updates.assigned_to)
        if updates.progress_notes is not None:
            set_clauses.append("progress_notes = ?")
            params.append(updates.progress_notes)
        if updates.actual_hours is not None:
            set_clauses.append("actual_hours = ?")
            params.append(updates.actual_hours)
        if updates.completion_notes is not None:
            set_clauses.append("completion_notes = ?")
            params.append(updates.completion_notes)
        
        params.append(work_order_id)
        
        query = f"UPDATE enhanced_work_orders SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Work order not found")
        
        conn.commit()
        conn.close()
        
        return await get_work_order_by_id(work_order_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete work order (soft delete by setting status to Cancelled)"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE enhanced_work_orders 
            SET status = 'Cancelled', updated_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (work_order_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Work order not found")
        
        conn.commit()
        conn.close()
        
        return {"message": f"Work order {work_order_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/analytics/dashboard")
async def get_work_order_analytics():
    """Get comprehensive work order analytics"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM enhanced_work_orders
            GROUP BY status
        """)
        status_stats = dict(cursor.fetchall())
        
        # Get priority distribution
        cursor.execute("""
            SELECT priority, COUNT(*) as count
            FROM enhanced_work_orders
            GROUP BY priority
        """)
        priority_stats = dict(cursor.fetchall())
        
        # Get completion metrics
        cursor.execute("""
            SELECT 
                AVG(actual_hours) as avg_completion_time,
                COUNT(*) as total_completed
            FROM enhanced_work_orders
            WHERE status = 'Completed' AND actual_hours IS NOT NULL
        """)
        completion_metrics = cursor.fetchone()
        
        # Get overdue work orders
        cursor.execute("""
            SELECT COUNT(*) as overdue_count
            FROM enhanced_work_orders
            WHERE due_date < CURRENT_TIMESTAMP AND status NOT IN ('Completed', 'Cancelled', 'Closed')
        """)
        overdue_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status_distribution": status_stats,
            "priority_distribution": priority_stats,
            "avg_completion_time_hours": completion_metrics[0] if completion_metrics[0] else 0,
            "total_completed": completion_metrics[1],
            "overdue_count": overdue_count,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders/{work_order_id}/ai-analyze")
async def get_ai_analysis(work_order_id: int):
    """Get comprehensive AI analysis for a specific work order"""
    try:
        work_order = await get_work_order_by_id(work_order_id)
        
        # Get fresh AI recommendations
        recommendations = await get_ai_recommendations({
            "title": work_order.title,
            "description": work_order.description,
            "asset_id": work_order.asset_id,
            "priority": work_order.priority,
            "status": work_order.status
        })
        
        return {
            "work_order_id": work_order_id,
            "ai_analysis": recommendations,
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8010))
    print(f"🚀 Starting Enhanced Work Orders Service on port {port}...")
    print("🤖 Features: AI-Powered, Real-time Tracking, Advanced Analytics")
    uvicorn.run(app, host="0.0.0.0", port=port)