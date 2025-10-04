#!/usr/bin/env python3
"""
ChatterFix CMMS - Work Orders Microservice
Complete work order management with AI-powered scheduling and optimization
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
import logging
import os
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database service configuration
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")

# Pydantic models
class WorkOrderCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    status: str = Field(default="open", pattern="^(open|in_progress|completed|on_hold|cancelled)$")
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    status: Optional[str] = Field(None, pattern="^(open|in_progress|completed|on_hold|cancelled)$")
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_notes: Optional[str] = None

class WorkOrderResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    status: str
    assigned_to: Optional[int]
    asset_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    completion_notes: Optional[str]
    assigned_username: Optional[str] = None
    asset_name: Optional[str] = None

# Create FastAPI app
app = FastAPI(
    title="ChatterFix CMMS - Work Orders Service",
    description="Advanced AI-powered work order management system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_database_client():
    """Get HTTP client for database service"""
    return httpx.AsyncClient(base_url=DATABASE_SERVICE_URL, timeout=30.0)

@app.get("/health")
async def health_check():
    """Work Orders service health check"""
    try:
        async with await get_database_client() as client:
            response = await client.get("/health")
            db_status = "healthy" if response.status_code == 200 else "unhealthy"
        
        return {
            "status": "healthy",
            "service": "work-orders",
            "database_connection": db_status,
            "timestamp": datetime.now().isoformat(),
            "features": [
                "Full CRUD operations",
                "Advanced AI scheduling",
                "Priority-based assignment",
                "Real-time status tracking",
                "Automated workflow management"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "work-orders",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/", response_class=HTMLResponse)
async def work_orders_dashboard():
    """Work Orders service dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Work Orders Service - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        :root {
            --primary-dark: #0a0a0a;
            --secondary-dark: #16213e;
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-purple: #667eea;
            --accent-purple-dark: #764ba2;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --bg-primary: #0a0a0a;
            --bg-card: rgba(255, 255, 255, 0.05);
            --bg-gradient: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
            --font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        * { box-sizing: border-box; }
        
        body {
            margin: 0;
            font-family: var(--font-family);
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(10, 10, 10, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 16px 0;
            z-index: 1000;
        }
        
        .navbar-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .navbar-brand {
            background: var(--text-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: 1.25rem;
        }
        
        .page-header {
            padding: 120px 0 64px;
            text-align: center;
            background: var(--bg-gradient);
        }
        
        .page-header h1 {
            font-size: 3rem;
            font-weight: 800;
            background: var(--text-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
            margin: 0;
        }
        
        .page-header .subtitle {
            margin: 1rem 0 0 0;
            color: var(--text-secondary);
            font-size: 1.2rem;
            font-weight: 400;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 24px;
            margin-bottom: 48px;
        }
        
        .stat-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            background: var(--text-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: block;
            margin-bottom: 8px;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin: 48px 0;
        }
        
        .feature-card {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 32px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
            border-color: var(--accent-purple);
        }
        
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 16px;
            color: var(--accent-purple);
        }
        
        .feature-card h3 {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 12px;
        }
        
        .feature-card p {
            color: var(--text-secondary);
            line-height: 1.6;
            margin: 0;
        }
        
        .api-section {
            margin: 48px 0;
            padding: 32px;
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
        }
        
        .api-section h3 {
            font-size: 1.875rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 24px;
        }
        
        .endpoint {
            background: rgba(0, 0, 0, 0.3);
            padding: 16px;
            margin: 8px 0;
            border-radius: 12px;
            font-family: 'Fira Code', 'Monaco', 'Cascadia Code', monospace;
            font-size: 0.875rem;
            color: var(--text-secondary);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        @media (max-width: 768px) {
            .page-header h1 {
                font-size: 2.25rem;
            }
            .container {
                padding: 0 16px;
            }
            .stats-grid,
            .features-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="navbar-content">
                <div class="navbar-brand">ChatterFix CMMS</div>
                <div>Work Orders Service</div>
            </div>
        </nav>

        <div class="page-header">
            <div class="container">
                <h1>🛠️ Work Orders Service</h1>
                <p class="subtitle">Advanced AI-Powered Work Order Management</p>
            </div>
        </div>

        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number" id="total-orders">-</span>
                    <div>Total Work Orders</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="open-orders">-</span>
                    <div>Open Orders</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="in-progress-orders">-</span>
                    <div>In Progress</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="completed-orders">-</span>
                    <div>Completed</div>
                </div>
            </div>

            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <h3>Smart Prioritization</h3>
                    <p>Advanced AI algorithms automatically prioritize work orders based on criticality, asset importance, and resource availability.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📅</div>
                    <h3>Intelligent Scheduling</h3>
                    <p>AI-powered scheduling engine optimizes technician assignments and minimizes equipment downtime.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3>Real-time Tracking</h3>
                    <p>Live status updates and progress tracking with automated notifications and escalations.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔄</div>
                    <h3>Workflow Automation</h3>
                    <p>Automated workflow management with conditional logic and approval processes.</p>
                </div>
            </div>

            <div class="api-section">
                <h3>🔗 API Endpoints</h3>
                <div class="endpoint">GET /api/work-orders - List all work orders</div>
                <div class="endpoint">POST /api/work-orders - Create new work order</div>
                <div class="endpoint">GET /api/work-orders/{id} - Get specific work order</div>
                <div class="endpoint">PUT /api/work-orders/{id} - Update work order</div>
                <div class="endpoint">DELETE /api/work-orders/{id} - Delete work order</div>
                <div class="endpoint">GET /api/work-orders/analytics - Advanced analytics</div>
                <div class="endpoint">POST /api/work-orders/{id}/assign - AI-powered assignment</div>
            </div>
        </div>

        <script>
        // Load work orders statistics
        fetch('/api/work-orders/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('total-orders').textContent = data.total || 0;
                document.getElementById('open-orders').textContent = data.open || 0;
                document.getElementById('in-progress-orders').textContent = data.in_progress || 0;
                document.getElementById('completed-orders').textContent = data.completed || 0;
            })
            .catch(error => console.error('Failed to load stats:', error));
        </script>
    </body>
    </html>
    """

# Enhanced Work Orders CRUD Operations with AI Integration
@app.get("/api/work-orders", response_model=List[WorkOrderResponse])
async def get_work_orders(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, pattern="^(open|in_progress|completed|on_hold|cancelled)$"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    assigned_to: Optional[int] = Query(None),
    asset_id: Optional[int] = Query(None),
    due_date_from: Optional[datetime] = Query(None),
    due_date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at", pattern="^(created_at|due_date|priority|status)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$")
):
    """Get work orders with advanced filtering, search, and pagination"""
    try:
        async with await get_database_client() as client:
            # Build dynamic query with filters
            query_parts = ["SELECT wo.*, u.username as assigned_username, a.name as asset_name FROM work_orders wo"]
            query_parts.append("LEFT JOIN users u ON wo.assigned_to = u.id")
            query_parts.append("LEFT JOIN assets a ON wo.asset_id = a.id")
            
            conditions = []
            params = []
            
            if status:
                conditions.append("wo.status = %s")
                params.append(status)
            if priority:
                conditions.append("wo.priority = %s")
                params.append(priority)
            if assigned_to:
                conditions.append("wo.assigned_to = %s")
                params.append(assigned_to)
            if asset_id:
                conditions.append("wo.asset_id = %s")
                params.append(asset_id)
            if due_date_from:
                conditions.append("wo.due_date >= %s")
                params.append(due_date_from.isoformat())
            if due_date_to:
                conditions.append("wo.due_date <= %s")
                params.append(due_date_to.isoformat())
            if search:
                conditions.append("(wo.title ILIKE %s OR wo.description ILIKE %s)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))
            
            # Add sorting
            sort_column = f"wo.{sort_by}" if sort_by != "asset_name" else "a.name"
            query_parts.append(f"ORDER BY {sort_column} {sort_order.upper()}")
            
            # Add pagination
            query_parts.append("LIMIT %s OFFSET %s")
            params.extend([limit, offset])
            
            query = " ".join(query_parts)
            
            response = await client.post("/api/query", json={
                "query": query,
                "params": params,
                "fetch": "all"
            })
            response.raise_for_status()
            
            # Transform raw data to response format
            work_orders = []
            columns = ["id", "title", "description", "priority", "status", "assigned_to", 
                      "asset_id", "created_by", "created_at", "updated_at", "due_date", 
                      "completed_at", "estimated_hours", "actual_hours", "completion_notes", 
                      "assigned_username", "asset_name"]
            
            for row in response.json()["data"]:
                work_order = dict(zip(columns, row))
                work_orders.append(work_order)
            
            return work_orders
    except Exception as e:
        logger.error(f"Failed to get work orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(work_order_id: int):
    """Get a specific work order by ID"""
    try:
        async with await get_database_client() as client:
            response = await client.get(f"/api/work-orders/{work_order_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Work order not found")
            response.raise_for_status()
            return response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders", response_model=Dict[str, Any])
async def create_work_order(work_order: WorkOrderCreate):
    """Create a new work order"""
    try:
        async with await get_database_client() as client:
            work_order_data = work_order.dict()
            response = await client.post("/api/work-orders", json=work_order_data)
            response.raise_for_status()
            result = response.json()
            
            # Add AI-powered optimization
            if result.get("id"):
                await optimize_work_order_assignment(result["id"])
            
            return result
    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/work-orders/{work_order_id}", response_model=Dict[str, Any])
async def update_work_order(work_order_id: int, work_order: WorkOrderUpdate):
    """Update an existing work order"""
    try:
        async with await get_database_client() as client:
            # First check if work order exists
            check_response = await client.get(f"/api/work-orders/{work_order_id}")
            if check_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Work order not found")
            
            # Prepare update data (only include non-None fields)
            update_data = {k: v for k, v in work_order.dict().items() if v is not None}
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.now().isoformat()
            
            # If status is being changed to completed, add completion timestamp
            if update_data.get("status") == "completed":
                update_data["completed_at"] = datetime.now().isoformat()
            
            # Execute update via database service
            query = "UPDATE work_orders SET "
            query += ", ".join([f"{key} = %s" for key in update_data.keys()])
            query += f" WHERE id = %s"
            
            params = list(update_data.values()) + [work_order_id]
            
            response = await client.post("/api/query", json={
                "query": query,
                "params": params,
                "fetch": None
            })
            response.raise_for_status()
            
            return {"message": "Work order updated successfully", "id": work_order_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete a work order"""
    try:
        async with await get_database_client() as client:
            # First check if work order exists
            check_response = await client.get(f"/api/work-orders/{work_order_id}")
            if check_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Work order not found")
            
            # Delete work order
            response = await client.post("/api/query", json={
                "query": "DELETE FROM work_orders WHERE id = %s",
                "params": [work_order_id],
                "fetch": None
            })
            response.raise_for_status()
            
            return {"message": "Work order deleted successfully", "id": work_order_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Intelligence Features
@app.get("/api/work-orders/stats")
async def get_work_order_stats():
    """Get work order statistics"""
    try:
        async with await get_database_client() as client:
            stats = {}
            
            # Total work orders
            response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM work_orders",
                "fetch": "one"
            })
            response.raise_for_status()
            stats["total"] = response.json()["data"][0]
            
            # By status
            for status in ["open", "in_progress", "completed", "on_hold", "cancelled"]:
                response = await client.post("/api/query", json={
                    "query": "SELECT COUNT(*) FROM work_orders WHERE status = %s",
                    "params": [status],
                    "fetch": "one"
                })
                response.raise_for_status()
                stats[status] = response.json()["data"][0]
            
            # By priority
            for priority in ["low", "medium", "high", "critical"]:
                response = await client.post("/api/query", json={
                    "query": "SELECT COUNT(*) FROM work_orders WHERE priority = %s",
                    "params": [priority],
                    "fetch": "one"
                })
                response.raise_for_status()
                stats[f"priority_{priority}"] = response.json()["data"][0]
            
            return stats
    except Exception as e:
        logger.error(f"Failed to get work order stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/analytics")
async def get_work_order_analytics():
    """Advanced analytics and insights"""
    try:
        async with await get_database_client() as client:
            analytics = {}
            
            # Average completion time
            response = await client.post("/api/query", json={
                "query": """
                SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_hours
                FROM work_orders 
                WHERE status = 'completed' AND completed_at IS NOT NULL
                """,
                "fetch": "one"
            })
            response.raise_for_status()
            result = response.json()["data"]
            analytics["avg_completion_hours"] = round(result[0], 2) if result and result[0] else 0
            
            # Overdue work orders
            response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(*) FROM work_orders 
                WHERE due_date < NOW() AND status NOT IN ('completed', 'cancelled')
                """,
                "fetch": "one"
            })
            response.raise_for_status()
            analytics["overdue_count"] = response.json()["data"][0]
            
            # Work orders by week
            response = await client.post("/api/query", json={
                "query": """
                SELECT DATE_TRUNC('week', created_at) as week, COUNT(*) as count
                FROM work_orders 
                WHERE created_at >= NOW() - INTERVAL '8 weeks'
                GROUP BY week
                ORDER BY week
                """,
                "fetch": "all"
            })
            response.raise_for_status()
            analytics["weekly_trends"] = response.json()["data"]
            
            return analytics
    except Exception as e:
        logger.error(f"Failed to get work order analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders/{work_order_id}/assign")
async def ai_powered_assignment(work_order_id: int):
    """AI-powered technician assignment"""
    try:
        async with await get_database_client() as client:
            # Get work order details
            wo_response = await client.get(f"/api/work-orders/{work_order_id}")
            if wo_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Work order not found")
            
            work_order = wo_response.json()
            
            # AI assignment logic (simplified)
            best_technician = await find_best_technician(work_order)
            
            if best_technician:
                # Update assignment
                response = await client.post("/api/query", json={
                    "query": "UPDATE work_orders SET assigned_to = %s, status = 'in_progress' WHERE id = %s",
                    "params": [best_technician["id"], work_order_id],
                    "fetch": None
                })
                response.raise_for_status()
                
                return {
                    "message": "Work order assigned successfully",
                    "assigned_to": best_technician,
                    "reasoning": "AI selected based on availability, skills, and workload"
                }
            else:
                return {
                    "message": "No suitable technician found",
                    "recommendation": "Consider hiring additional staff or adjusting priorities"
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Work Order Management Features
@app.get("/api/work-orders/form")
async def work_order_form():
    """Interactive work order creation/editing form"""
    return {
        "form_fields": {
            "title": {"type": "text", "required": True, "max_length": 255},
            "description": {"type": "textarea", "required": True},
            "priority": {"type": "select", "options": ["low", "medium", "high", "critical"], "default": "medium"},
            "status": {"type": "select", "options": ["open", "in_progress", "completed", "on_hold", "cancelled"], "default": "open"},
            "assigned_to": {"type": "select", "source": "/api/users?role=technician", "nullable": True},
            "asset_id": {"type": "select", "source": "/api/assets?status=active", "nullable": True},
            "due_date": {"type": "datetime", "nullable": True},
            "estimated_hours": {"type": "number", "min": 0, "step": 0.5, "nullable": True}
        },
        "validation_rules": {
            "due_date_future": "Due date must be in the future",
            "estimated_hours_positive": "Estimated hours must be positive"
        },
        "ai_assistance": {
            "auto_priority": "AI will suggest priority based on asset criticality",
            "smart_assignment": "AI will recommend best technician for the job",
            "duration_estimate": "AI will estimate completion time based on similar work orders"
        }
    }

@app.post("/api/work-orders/bulk")
async def create_bulk_work_orders(work_orders: List[WorkOrderCreate]):
    """Create multiple work orders in bulk"""
    try:
        created_orders = []
        failed_orders = []
        
        for i, work_order in enumerate(work_orders):
            try:
                async with await get_database_client() as client:
                    work_order_data = work_order.dict()
                    response = await client.post("/api/work-orders", json=work_order_data)
                    response.raise_for_status()
                    result = response.json()
                    
                    # Add AI optimization
                    if result.get("id"):
                        await optimize_work_order_assignment(result["id"])
                    
                    created_orders.append({"index": i, "id": result.get("id"), "status": "created"})
            except Exception as e:
                failed_orders.append({"index": i, "error": str(e), "work_order": work_order.dict()})
                logger.error(f"Failed to create work order {i}: {e}")
        
        return {
            "total_requested": len(work_orders),
            "created_count": len(created_orders),
            "failed_count": len(failed_orders),
            "created_orders": created_orders,
            "failed_orders": failed_orders
        }
    except Exception as e:
        logger.error(f"Bulk work order creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/templates")
async def get_work_order_templates():
    """Get work order templates for common maintenance tasks"""
    return {
        "templates": [
            {
                "id": "preventive_maintenance",
                "name": "Preventive Maintenance",
                "description": "Regular preventive maintenance checklist",
                "priority": "medium",
                "estimated_hours": 2.0,
                "checklist": [
                    "Visual inspection of equipment",
                    "Check fluid levels",
                    "Lubricate moving parts",
                    "Test safety systems",
                    "Record readings"
                ]
            },
            {
                "id": "emergency_repair",
                "name": "Emergency Repair",
                "description": "Emergency repair template",
                "priority": "critical",
                "estimated_hours": 4.0,
                "checklist": [
                    "Assess safety risks",
                    "Isolate equipment",
                    "Diagnose issue",
                    "Perform repair",
                    "Test functionality",
                    "Document findings"
                ]
            },
            {
                "id": "calibration",
                "name": "Equipment Calibration",
                "description": "Equipment calibration and testing",
                "priority": "medium",
                "estimated_hours": 1.5,
                "checklist": [
                    "Prepare calibration equipment",
                    "Perform calibration tests",
                    "Adjust parameters",
                    "Verify accuracy",
                    "Update calibration records"
                ]
            }
        ]
    }

@app.post("/api/work-orders/template/{template_id}")
async def create_from_template(template_id: str, asset_id: int, customizations: Optional[Dict[str, Any]] = None):
    """Create work order from template"""
    try:
        # Get template
        templates_response = await get_work_order_templates()
        template = next((t for t in templates_response["templates"] if t["id"] == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Get asset information
        async with await get_database_client() as client:
            asset_response = await client.get(f"/api/assets/{asset_id}")
            if asset_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Asset not found")
            asset_response.raise_for_status()
            asset = asset_response.json()
        
        # Create work order from template
        work_order_data = {
            "title": f"{template['name']} - {asset.get('name', f'Asset {asset_id}')}",
            "description": f"{template['description']}\n\nChecklist:\n" + "\n".join(f"- {item}" for item in template['checklist']),
            "priority": template['priority'],
            "asset_id": asset_id,
            "estimated_hours": template['estimated_hours']
        }
        
        # Apply customizations
        if customizations:
            work_order_data.update(customizations)
        
        # Create work order
        work_order = WorkOrderCreate(**work_order_data)
        response = await client.post("/api/work-orders", json=work_order.dict())
        response.raise_for_status()
        result = response.json()
        
        # Add AI optimization
        if result.get("id"):
            await optimize_work_order_assignment(result["id"])
        
        return {
            "work_order": result,
            "template_used": template_id,
            "customizations_applied": customizations or {}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create work order from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/dashboard")
async def work_orders_dashboard_data():
    """Get dashboard data for work orders overview"""
    try:
        async with await get_database_client() as client:
            dashboard_data = {}
            
            # Active work orders by priority
            priority_response = await client.post("/api/query", json={
                "query": """
                SELECT priority, COUNT(*) as count 
                FROM work_orders 
                WHERE status NOT IN ('completed', 'cancelled')
                GROUP BY priority
                """,
                "fetch": "all"
            })
            priority_response.raise_for_status()
            dashboard_data["active_by_priority"] = {
                row[0]: row[1] for row in priority_response.json()["data"]
            }
            
            # Work orders by technician
            technician_response = await client.post("/api/query", json={
                "query": """
                SELECT u.username, COUNT(*) as count
                FROM work_orders wo
                JOIN users u ON wo.assigned_to = u.id
                WHERE wo.status = 'in_progress'
                GROUP BY u.username
                ORDER BY count DESC
                LIMIT 10
                """,
                "fetch": "all"
            })
            technician_response.raise_for_status()
            dashboard_data["by_technician"] = [
                {"technician": row[0], "active_orders": row[1]} 
                for row in technician_response.json()["data"]
            ]
            
            # Overdue work orders
            overdue_response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(*) as count
                FROM work_orders 
                WHERE due_date < NOW() 
                AND status NOT IN ('completed', 'cancelled')
                """,
                "fetch": "one"
            })
            overdue_response.raise_for_status()
            dashboard_data["overdue_count"] = overdue_response.json()["data"][0]
            
            # Average completion time (last 30 days)
            avg_time_response = await client.post("/api/query", json={
                "query": """
                SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_hours
                FROM work_orders 
                WHERE status = 'completed' 
                AND completed_at >= NOW() - INTERVAL '30 days'
                """,
                "fetch": "one"
            })
            avg_time_response.raise_for_status()
            avg_hours = avg_time_response.json()["data"][0]
            dashboard_data["avg_completion_hours"] = round(avg_hours, 2) if avg_hours else 0
            
            # Recent activity (last 10 work orders)
            recent_response = await client.post("/api/query", json={
                "query": """
                SELECT wo.id, wo.title, wo.status, wo.priority, wo.updated_at, u.username
                FROM work_orders wo
                LEFT JOIN users u ON wo.assigned_to = u.id
                ORDER BY wo.updated_at DESC
                LIMIT 10
                """,
                "fetch": "all"
            })
            recent_response.raise_for_status()
            dashboard_data["recent_activity"] = [
                {
                    "id": row[0], "title": row[1], "status": row[2], 
                    "priority": row[3], "updated_at": row[4], "technician": row[5]
                }
                for row in recent_response.json()["data"]
            ]
            
            return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced AI Helper Functions
async def optimize_work_order_assignment(work_order_id: int):
    """Optimize work order assignment using AI Brain service"""
    try:
        async with await get_database_client() as client:
            # Get work order details
            wo_response = await client.get(f"/api/work-orders/{work_order_id}")
            if wo_response.status_code != 200:
                logger.warning(f"Could not fetch work order {work_order_id} for optimization")
                return False
            
            work_order = wo_response.json()
            
            # Call AI Brain service for optimization
            ai_brain_url = os.getenv("AI_BRAIN_SERVICE_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
            
            async with httpx.AsyncClient(timeout=30.0) as ai_client:
                try:
                    ai_response = await ai_client.post(f"{ai_brain_url}/api/ai/analysis", json={
                        "analysis_type": "resource_allocation",
                        "data_sources": ["work_orders", "users", "assets"],
                        "parameters": {
                            "work_order_id": work_order_id,
                            "priority": work_order.get("priority"),
                            "asset_id": work_order.get("asset_id"),
                            "estimated_hours": work_order.get("estimated_hours")
                        }
                    })
                    
                    if ai_response.status_code == 200:
                        ai_result = ai_response.json()
                        logger.info(f"AI optimization completed for work order {work_order_id}: {ai_result.get('confidence_score', 0)}")
                        return True
                except Exception as ai_error:
                    logger.warning(f"AI Brain service unavailable for work order {work_order_id}: {ai_error}")
        
        # Fallback: Basic assignment logic
        await basic_work_order_optimization(work_order_id)
        return True
        
    except Exception as e:
        logger.error(f"AI optimization failed for work order {work_order_id}: {e}")
        return False

async def basic_work_order_optimization(work_order_id: int):
    """Basic work order optimization when AI Brain is unavailable"""
    try:
        async with await get_database_client() as client:
            # Auto-assign critical priority work orders
            update_response = await client.post("/api/query", json={
                "query": """
                UPDATE work_orders 
                SET status = 'in_progress', updated_at = NOW()
                WHERE id = %s AND priority = 'critical' AND status = 'open'
                """,
                "params": [work_order_id],
                "fetch": None
            })
            update_response.raise_for_status()
            logger.info(f"Basic optimization applied to work order {work_order_id}")
    except Exception as e:
        logger.warning(f"Basic optimization failed for work order {work_order_id}: {e}")

async def find_best_technician(work_order: Dict[str, Any]):
    """Find the best technician for a work order using AI Brain service"""
    try:
        async with await get_database_client() as client:
            # Get available technicians with workload info
            technicians_response = await client.post("/api/query", json={
                "query": """
                SELECT u.id, u.username, u.email, u.role,
                       COUNT(wo.id) as active_workload,
                       AVG(wo.estimated_hours) as avg_hours
                FROM users u
                LEFT JOIN work_orders wo ON u.id = wo.assigned_to AND wo.status = 'in_progress'
                WHERE u.role = 'technician'
                GROUP BY u.id, u.username, u.email, u.role
                ORDER BY active_workload ASC, avg_hours ASC
                """,
                "fetch": "all"
            })
            technicians_response.raise_for_status()
            technicians_data = technicians_response.json()["data"]
            
            if not technicians_data:
                return None
            
            # Call AI Brain for intelligent assignment
            ai_brain_url = os.getenv("AI_BRAIN_SERVICE_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as ai_client:
                    ai_response = await ai_client.post(f"{ai_brain_url}/api/ai/optimize", json={
                        "optimization_type": "resource",
                        "objectives": ["minimize_workload", "maximize_expertise"],
                        "constraints": {
                            "available_technicians": technicians_data,
                            "work_order": work_order
                        }
                    })
                    
                    if ai_response.status_code == 200:
                        ai_result = ai_response.json()
                        # Use AI recommendation if available
                        recommended_id = ai_result.get("results", {}).get("recommended_technician_id")
                        if recommended_id:
                            recommended_tech = next(
                                (t for t in technicians_data if t[0] == recommended_id), 
                                None
                            )
                            if recommended_tech:
                                return {
                                    "id": recommended_tech[0],
                                    "username": recommended_tech[1],
                                    "workload": recommended_tech[4],
                                    "assignment_method": "ai_optimized"
                                }
            except Exception as ai_error:
                logger.warning(f"AI Brain assignment failed: {ai_error}")
            
            # Fallback: Choose technician with lowest workload
            best_tech = technicians_data[0]  # Already sorted by workload
            return {
                "id": best_tech[0],
                "username": best_tech[1],
                "workload": best_tech[4],
                "assignment_method": "workload_balanced"
            }
            
    except Exception as e:
        logger.error(f"Failed to find best technician: {e}")
        return None

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)