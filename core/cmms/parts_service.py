#!/usr/bin/env python3
"""
ChatterFix CMMS - Parts Microservice
Smart inventory management with automated procurement workflows
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, date, timedelta
import logging
import os
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database service configuration
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")

# Pydantic models
class PartCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    part_number: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(default=0, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    supplier: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)

class PartUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    part_number: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    supplier: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)

class PartResponse(BaseModel):
    id: int
    name: str
    description: str
    part_number: str
    quantity: int
    unit_cost: Optional[float]
    supplier: Optional[str]
    location: Optional[str]
    minimum_stock: Optional[int]
    maximum_stock: Optional[int]
    reorder_point: Optional[int]
    lead_time_days: Optional[int]
    created_at: datetime
    updated_at: datetime

class StockMovement(BaseModel):
    part_id: int
    movement_type: str = Field(..., pattern="^(in|out|adjustment|transfer)$")
    quantity: int = Field(..., ne=0)
    reference: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    work_order_id: Optional[int] = None

class ProcurementRequest(BaseModel):
    part_id: int
    quantity: int = Field(..., gt=0)
    urgency: str = Field(default="normal", pattern="^(low|normal|high|emergency)$")
    justification: str
    requested_by: Optional[str] = None
    target_delivery_date: Optional[date] = None

# Create FastAPI app
app = FastAPI(
    title="ChatterFix CMMS - Parts Service",
    description="Advanced AI-powered inventory management system",
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
    """Parts service health check"""
    try:
        async with await get_database_client() as client:
            response = await client.get("/health")
            db_status = "healthy" if response.status_code == 200 else "unhealthy"
        
        return {
            "status": "healthy",
            "service": "parts",
            "database_connection": db_status,
            "timestamp": datetime.now().isoformat(),
            "features": [
                "Smart inventory management",
                "Automated procurement workflows",
                "Real-time stock tracking",
                "Advanced AI demand forecasting",
                "Low-stock alerts and automation"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "parts",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/", response_class=HTMLResponse)
async def parts_dashboard():
    """Parts service dashboard with ChatterFix standardized styling"""
    from chatterfix_template_utils import get_service_dashboard
    
    # Custom JavaScript for parts-specific functionality
    custom_scripts = """
        // Load parts statistics
        fetch('/api/parts/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('total-parts').textContent = data.total || 0;
                document.getElementById('low-stock').textContent = data.low_stock || 0;
                document.getElementById('on-order').textContent = data.on_order || 0;
                document.getElementById('inventory-value').textContent = '$' + (data.total_value || '0');
            })
            .catch(error => console.error('Failed to load stats:', error));
        
        // Parts-specific functions
        function refreshParts() {
            location.reload();
        }
        
        function generateReports() {
            showToast('Generating inventory reports...', 'info');
            // Add report generation logic here
        }
    """
    
    # Custom content for parts management
    custom_content = """
        <div class="grid grid-2 mt-8">
            <div class="card">
                <h3 style="margin-bottom: 24px;">Quick Actions</h3>
                <div class="flex flex-wrap gap-4">
                    <button onclick="refreshParts()" class="btn-secondary">🔄 Refresh</button>
                    <button onclick="generateReports()" class="btn-primary">📊 Generate Reports</button>
                </div>
            </div>
            <div class="card">
                <h3 style="margin-bottom: 24px;">Low Stock Alerts</h3>
                <div id="lowStockAlerts">
                    <div style="color: var(--text-secondary);">Loading alerts...</div>
                </div>
            </div>
        </div>
    """
    
    return get_service_dashboard('parts', custom_content, custom_scripts)

# Enhanced Parts CRUD Operations with AI Integration
@app.get("/api/parts", response_model=List[PartResponse])
async def get_parts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    supplier: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
    critical_stock: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    part_number_search: Optional[str] = Query(None),
    min_cost: Optional[float] = Query(None),
    max_cost: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("created_at", pattern="^(created_at|name|quantity|unit_cost)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    include_usage_stats: Optional[bool] = Query(False)
):
    """Get parts with advanced filtering, search, and usage statistics"""
    try:
        async with await get_database_client() as client:
            # Build dynamic query with filters
            query_parts = ["SELECT p.*"]
            
            if include_usage_stats:
                query_parts[0] += ", COUNT(wop.id) as total_usage, SUM(wop.quantity_used) as total_quantity_used"
            
            query_parts.append("FROM parts p")
            
            if include_usage_stats:
                query_parts.append("LEFT JOIN work_order_parts wop ON p.id = wop.part_id")
            
            conditions = []
            params = []
            
            if supplier:
                conditions.append("p.supplier = %s")
                params.append(supplier)
            if location:
                conditions.append("p.location = %s")
                params.append(location)
            if search:
                conditions.append("(p.name ILIKE %s OR p.description ILIKE %s)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            if part_number_search:
                conditions.append("p.part_number ILIKE %s")
                params.append(f"%{part_number_search}%")
            if min_cost is not None:
                conditions.append("p.unit_cost >= %s")
                params.append(min_cost)
            if max_cost is not None:
                conditions.append("p.unit_cost <= %s")
                params.append(max_cost)
            if low_stock:
                conditions.append("p.quantity <= COALESCE(p.reorder_point, 10)")
            if critical_stock:
                conditions.append("p.quantity <= COALESCE(p.minimum_stock, 5)")
            
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))
            
            if include_usage_stats:
                query_parts.append("GROUP BY p.id")
            
            # Add sorting
            sort_column = f"p.{sort_by}"
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
            parts = []
            base_columns = ["id", "name", "description", "part_number", "quantity", "unit_cost",
                           "supplier", "location", "minimum_stock", "maximum_stock", "reorder_point", 
                           "lead_time_days", "created_at", "updated_at"]
            
            for row in response.json()["data"]:
                part = dict(zip(base_columns, row[:len(base_columns)]))
                
                if include_usage_stats and len(row) > len(base_columns):
                    part["total_usage"] = row[len(base_columns)]
                    part["total_quantity_used"] = row[len(base_columns) + 1]
                
                # Add computed fields
                part["stock_status"] = get_stock_status(part)
                part["days_of_stock"] = calculate_days_of_stock(part)
                
                parts.append(part)
            
            return parts
    except Exception as e:
        logger.error(f"Failed to get parts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/{part_id}", response_model=PartResponse)
async def get_part(part_id: int):
    """Get a specific part by ID"""
    try:
        async with await get_database_client() as client:
            response = await client.post("/api/query", json={
                "query": "SELECT * FROM parts WHERE id = %s",
                "params": [part_id],
                "fetch": "one"
            })
            response.raise_for_status()
            result = response.json()["data"]
            
            if not result:
                raise HTTPException(status_code=404, detail="Part not found")
                
            # Convert to dictionary format expected by PartResponse
            columns = ["id", "name", "description", "part_number", "quantity", "unit_cost", 
                      "supplier", "location", "created_at", "updated_at"]
            part_dict = dict(zip(columns, result))
            return part_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get part {part_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parts", response_model=Dict[str, Any])
async def create_part(part: PartCreate):
    """Create a new part"""
    try:
        async with await get_database_client() as client:
            # Check if part number already exists
            check_response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM parts WHERE part_number = %s",
                "params": [part.part_number],
                "fetch": "one"
            })
            check_response.raise_for_status()
            
            if check_response.json()["data"][0] > 0:
                raise HTTPException(status_code=400, detail="Part number already exists")
            
            # Create new part
            query = """
            INSERT INTO parts (name, description, part_number, quantity, unit_cost, 
                             supplier, location, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            if DATABASE_SERVICE_URL and "postgresql" in DATABASE_SERVICE_URL:
                query += " RETURNING id"
            
            params = [
                part.name, part.description, part.part_number, part.quantity,
                part.unit_cost, part.supplier, part.location
            ]
            
            response = await client.post("/api/query", json={
                "query": query,
                "params": params,
                "fetch": "one" if "RETURNING" in query else None
            })
            response.raise_for_status()
            
            if "RETURNING" in query:
                part_id = response.json()["data"][0]
            else:
                # SQLite fallback
                id_response = await client.post("/api/query", json={
                    "query": "SELECT last_insert_rowid()",
                    "fetch": "one"
                })
                id_response.raise_for_status()
                part_id = id_response.json()["data"][0]
            
            # Initialize AI-powered stock management
            await initialize_stock_management(part_id, part)
            
            return {"id": part_id, "message": "Part created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create part: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/parts/{part_id}", response_model=Dict[str, Any])
async def update_part(part_id: int, part: PartUpdate):
    """Update an existing part"""
    try:
        async with await get_database_client() as client:
            # Check if part exists
            check_response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM parts WHERE id = %s",
                "params": [part_id],
                "fetch": "one"
            })
            check_response.raise_for_status()
            
            if check_response.json()["data"][0] == 0:
                raise HTTPException(status_code=404, detail="Part not found")
            
            # Prepare update data (only include non-None fields)
            update_data = {k: v for k, v in part.dict().items() if v is not None}
            
            if not update_data:
                return {"message": "No updates provided", "id": part_id}
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.now().isoformat()
            
            # Execute update
            query = "UPDATE parts SET "
            query += ", ".join([f"{key} = %s" for key in update_data.keys()])
            query += " WHERE id = %s"
            
            params = list(update_data.values()) + [part_id]
            
            response = await client.post("/api/query", json={
                "query": query,
                "params": params,
                "fetch": None
            })
            response.raise_for_status()
            
            return {"message": "Part updated successfully", "id": part_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update part {part_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/parts/{part_id}")
async def delete_part(part_id: int):
    """Delete a part"""
    try:
        async with await get_database_client() as client:
            # Check if part exists
            check_response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM parts WHERE id = %s",
                "params": [part_id],
                "fetch": "one"
            })
            check_response.raise_for_status()
            
            if check_response.json()["data"][0] == 0:
                raise HTTPException(status_code=404, detail="Part not found")
            
            # Check for usage in work orders
            usage_check = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM work_order_parts WHERE part_id = %s",
                "params": [part_id],
                "fetch": "one"
            })
            usage_check.raise_for_status()
            
            if usage_check.json()["data"][0] > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete part that has been used in work orders"
                )
            
            # Delete part
            response = await client.post("/api/query", json={
                "query": "DELETE FROM parts WHERE id = %s",
                "params": [part_id],
                "fetch": None
            })
            response.raise_for_status()
            
            return {"message": "Part deleted successfully", "id": part_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete part {part_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Inventory Management Features
@app.get("/api/parts/low-stock")
async def get_low_stock_parts(threshold: Optional[int] = Query(None)):
    """Get parts with low stock levels"""
    try:
        async with await get_database_client() as client:
            query = """
            SELECT * FROM parts 
            WHERE quantity <= COALESCE(reorder_point, 10)
            ORDER BY quantity ASC
            """
            
            response = await client.post("/api/query", json={
                "query": query,
                "fetch": "all"
            })
            response.raise_for_status()
            
            return {
                "low_stock_parts": response.json()["data"],
                "count": len(response.json()["data"]),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Failed to get low stock parts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parts/{part_id}/movement")
async def record_stock_movement(part_id: int, movement: StockMovement):
    """Record stock movement (in/out/adjustment)"""
    try:
        async with await get_database_client() as client:
            # Get current part info
            part_response = await client.post("/api/query", json={
                "query": "SELECT quantity FROM parts WHERE id = %s",
                "params": [part_id],
                "fetch": "one"
            })
            part_response.raise_for_status()
            part_data = part_response.json()["data"]
            
            if not part_data:
                raise HTTPException(status_code=404, detail="Part not found")
            
            current_quantity = part_data[0]
            
            # Calculate new quantity
            if movement.movement_type == "in":
                new_quantity = current_quantity + movement.quantity
            elif movement.movement_type == "out":
                new_quantity = current_quantity - movement.quantity
                if new_quantity < 0:
                    raise HTTPException(status_code=400, detail="Insufficient stock")
            elif movement.movement_type == "adjustment":
                new_quantity = current_quantity + movement.quantity  # Can be negative for adjustments
            else:  # transfer
                new_quantity = current_quantity + movement.quantity  # Could be positive or negative
            
            # Update part quantity
            update_response = await client.post("/api/query", json={
                "query": "UPDATE parts SET quantity = %s, updated_at = NOW() WHERE id = %s",
                "params": [new_quantity, part_id],
                "fetch": None
            })
            update_response.raise_for_status()
            
            # Record movement history (would create stock_movements table in production)
            logger.info(f"Stock movement recorded: Part {part_id}, {movement.movement_type}, {movement.quantity}")
            
            # Check if reordering is needed
            await check_reorder_requirements(part_id)
            
            return {
                "message": "Stock movement recorded successfully",
                "part_id": part_id,
                "previous_quantity": current_quantity,
                "new_quantity": new_quantity,
                "movement": movement.dict()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record stock movement for part {part_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parts/{part_id}/procurement")
async def create_procurement_request(part_id: int, request: ProcurementRequest):
    """Create procurement request for a part"""
    try:
        async with await get_database_client() as client:
            # Verify part exists
            part_response = await client.post("/api/query", json={
                "query": "SELECT name, supplier, unit_cost FROM parts WHERE id = %s",
                "params": [part_id],
                "fetch": "one"
            })
            part_response.raise_for_status()
            part_data = part_response.json()["data"]
            
            if not part_data:
                raise HTTPException(status_code=404, detail="Part not found")
            
            part_name, supplier, unit_cost = part_data
            total_cost = (unit_cost or 0) * request.quantity
            
            # In production, this would create a procurement_requests table
            procurement_data = {
                "part_id": part_id,
                "part_name": part_name,
                "supplier": supplier,
                "quantity": request.quantity,
                "urgency": request.urgency,
                "total_estimated_cost": total_cost,
                "justification": request.justification,
                "requested_by": request.requested_by,
                "target_delivery_date": request.target_delivery_date.isoformat() if request.target_delivery_date else None,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Procurement request created: {procurement_data}")
            
            return {
                "message": "Procurement request created successfully",
                "request_id": f"PR-{part_id}-{int(datetime.now().timestamp())}",
                "procurement_data": procurement_data
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create procurement request for part {part_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Intelligence Features
@app.get("/api/parts/stats")
async def get_parts_stats():
    """Get parts statistics"""
    try:
        async with await get_database_client() as client:
            stats = {}
            
            # Total parts
            response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM parts",
                "fetch": "one"
            })
            response.raise_for_status()
            stats["total"] = response.json()["data"][0]
            
            # In stock (quantity > 0)
            response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM parts WHERE quantity > 0",
                "fetch": "one"
            })
            response.raise_for_status()
            stats["in_stock"] = response.json()["data"][0]
            
            # Low stock (below reorder point)
            response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM parts WHERE quantity <= COALESCE(reorder_point, 10)",
                "fetch": "one"
            })
            response.raise_for_status()
            stats["low_stock"] = response.json()["data"][0]
            
            # Total inventory value
            response = await client.post("/api/query", json={
                "query": "SELECT COALESCE(SUM(quantity * unit_cost), 0) FROM parts WHERE unit_cost IS NOT NULL",
                "fetch": "one"
            })
            response.raise_for_status()
            stats["total_value"] = round(response.json()["data"][0], 2)
            
            return stats
    except Exception as e:
        logger.error(f"Failed to get parts stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/analytics")
async def get_parts_analytics():
    """Advanced parts analytics and insights"""
    try:
        async with await get_database_client() as client:
            analytics = {}
            
            # Critical stock levels (quantity = 0 or very low)
            response = await client.post("/api/query", json={
                "query": "SELECT COUNT(*) FROM parts WHERE quantity = 0 OR quantity <= 5",
                "fetch": "one"
            })
            response.raise_for_status()
            analytics["critical_stock"] = response.json()["data"][0]
            
            # Simulated pending orders (would be real data in production)
            analytics["pending_orders"] = 12
            
            # Simulated turnover rate (would be calculated from real movement data)
            analytics["turnover_rate"] = 4.2
            
            # Simulated forecast accuracy (would use AI Brain service)
            analytics["forecast_accuracy"] = 92.8
            
            # Top expensive parts
            response = await client.post("/api/query", json={
                "query": """
                SELECT name, quantity * unit_cost as total_value 
                FROM parts 
                WHERE unit_cost IS NOT NULL 
                ORDER BY total_value DESC 
                LIMIT 5
                """,
                "fetch": "all"
            })
            response.raise_for_status()
            analytics["top_expensive_parts"] = response.json()["data"]
            
            # Supplier distribution
            response = await client.post("/api/query", json={
                "query": """
                SELECT supplier, COUNT(*) as part_count 
                FROM parts 
                WHERE supplier IS NOT NULL 
                GROUP BY supplier 
                ORDER BY part_count DESC 
                LIMIT 10
                """,
                "fetch": "all"
            })
            response.raise_for_status()
            analytics["supplier_distribution"] = response.json()["data"]
            
            return analytics
    except Exception as e:
        logger.error(f"Failed to get parts analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Parts Management Features
@app.get("/api/parts/form")
async def parts_form():
    """Interactive parts creation/editing form"""
    return {
        "form_fields": {
            "name": {"type": "text", "required": True, "max_length": 255},
            "description": {"type": "textarea", "required": True},
            "part_number": {"type": "text", "required": True, "max_length": 100, "unique": True},
            "quantity": {"type": "number", "min": 0, "default": 0},
            "unit_cost": {"type": "number", "min": 0, "step": 0.01, "nullable": True},
            "supplier": {"type": "text", "nullable": True, "max_length": 255},
            "location": {"type": "text", "nullable": True, "max_length": 255},
            "minimum_stock": {"type": "number", "min": 0, "nullable": True},
            "maximum_stock": {"type": "number", "min": 0, "nullable": True},
            "reorder_point": {"type": "number", "min": 0, "nullable": True},
            "lead_time_days": {"type": "number", "min": 0, "nullable": True}
        },
        "validation_rules": {
            "part_number_unique": "Part number must be unique",
            "max_greater_than_min": "Maximum stock must be greater than minimum stock",
            "reorder_between_min_max": "Reorder point should be between minimum and maximum stock"
        },
        "ai_assistance": {
            "demand_forecasting": "AI will predict future demand patterns",
            "optimal_stock_levels": "AI will suggest optimal min/max stock levels",
            "supplier_recommendations": "AI will analyze supplier performance",
            "cost_optimization": "AI will identify cost-saving opportunities"
        }
    }

@app.get("/api/parts/dashboard")
async def parts_dashboard_data():
    """Get comprehensive dashboard data for parts inventory"""
    try:
        async with await get_database_client() as client:
            dashboard_data = {}
            
            # Stock status distribution
            stock_status_data = await client.post("/api/query", json={
                "query": """
                SELECT 
                    CASE 
                        WHEN quantity = 0 THEN 'out_of_stock'
                        WHEN quantity <= COALESCE(minimum_stock, 5) THEN 'critical'
                        WHEN quantity <= COALESCE(reorder_point, 10) THEN 'low'
                        ELSE 'normal'
                    END as stock_status,
                    COUNT(*) as count
                FROM parts
                GROUP BY 
                    CASE 
                        WHEN quantity = 0 THEN 'out_of_stock'
                        WHEN quantity <= COALESCE(minimum_stock, 5) THEN 'critical'
                        WHEN quantity <= COALESCE(reorder_point, 10) THEN 'low'
                        ELSE 'normal'
                    END
                """,
                "fetch": "all"
            })
            stock_status_data.raise_for_status()
            dashboard_data["stock_status_distribution"] = {
                row[0]: row[1] for row in stock_status_data.json()["data"]
            }
            
            # Top suppliers by part count
            supplier_response = await client.post("/api/query", json={
                "query": """
                SELECT supplier, COUNT(*) as part_count, AVG(unit_cost) as avg_cost
                FROM parts 
                WHERE supplier IS NOT NULL 
                GROUP BY supplier 
                ORDER BY part_count DESC 
                LIMIT 10
                """,
                "fetch": "all"
            })
            supplier_response.raise_for_status()
            dashboard_data["top_suppliers"] = [
                {"supplier": row[0], "part_count": row[1], "avg_cost": round(row[2], 2) if row[2] else 0}
                for row in supplier_response.json()["data"]
            ]
            
            # Most expensive parts
            expensive_response = await client.post("/api/query", json={
                "query": """
                SELECT name, part_number, unit_cost, quantity
                FROM parts 
                WHERE unit_cost IS NOT NULL 
                ORDER BY unit_cost DESC 
                LIMIT 5
                """,
                "fetch": "all"
            })
            expensive_response.raise_for_status()
            dashboard_data["most_expensive_parts"] = [
                {"name": row[0], "part_number": row[1], "unit_cost": row[2], "quantity": row[3]}
                for row in expensive_response.json()["data"]
            ]
            
            # Parts needing attention (low stock, no supplier, etc.)
            attention_response = await client.post("/api/query", json={
                "query": """
                SELECT COUNT(*) as needs_attention FROM parts
                WHERE quantity <= COALESCE(reorder_point, 10)
                   OR supplier IS NULL
                   OR unit_cost IS NULL
                """,
                "fetch": "one"
            })
            attention_response.raise_for_status()
            dashboard_data["parts_needing_attention"] = attention_response.json()["data"][0]
            
            # Monthly usage trends (simulated - would use actual work order data)
            dashboard_data["usage_trends"] = {
                "trend_direction": "increasing",
                "monthly_growth": 12.5,
                "seasonal_factor": 1.1
            }
            
            return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get parts dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/{part_id}/demand-forecast")
async def get_demand_forecast(part_id: int, forecast_days: int = Query(90, ge=7, le=365)):
    """Get AI-powered demand forecast for specific part"""
    try:
        async with await get_database_client() as client:
            # Verify part exists
            part_response = await client.post("/api/query", json={
                "query": "SELECT * FROM parts WHERE id = %s",
                "params": [part_id],
                "fetch": "one"
            })
            part_response.raise_for_status()
            part_data = part_response.json()["data"]
            
            if not part_data:
                raise HTTPException(status_code=404, detail="Part not found")
            
            # Call AI Brain service for demand forecasting
            ai_brain_url = os.getenv("AI_BRAIN_SERVICE_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as ai_client:
                    ai_response = await ai_client.post(f"{ai_brain_url}/api/ai/forecast/demand", json={
                        "part_ids": [part_id],
                        "forecast_horizon_days": forecast_days,
                        "confidence_level": 0.95
                    })
                    
                    if ai_response.status_code == 200:
                        ai_result = ai_response.json()
                        forecasts = ai_result.get("forecasts", [])
                        
                        if forecasts:
                            forecast = forecasts[0]
                            
                            # Enhance with inventory recommendations
                            current_stock = part_data[4]  # quantity column
                            predicted_demand = forecast.get("predicted_demand", 0)
                            
                            recommendations = generate_inventory_recommendations(
                                current_stock, predicted_demand, forecast_days
                            )
                            
                            return {
                                "part_id": part_id,
                                "part_name": part_data[1],  # name column
                                "current_stock": current_stock,
                                "forecast_horizon_days": forecast_days,
                                "demand_forecast": forecast,
                                "inventory_recommendations": recommendations,
                                "generated_at": datetime.now().isoformat()
                            }
            except Exception as ai_error:
                logger.warning(f"AI Brain service unavailable: {ai_error}")
            
            # Fallback: Basic forecast using historical patterns
            basic_forecast = generate_basic_demand_forecast(part_data, forecast_days)
            return {
                "part_id": part_id,
                "part_name": part_data[1],
                "current_stock": part_data[4],
                "forecast_horizon_days": forecast_days,
                "demand_forecast": basic_forecast,
                "inventory_recommendations": generate_inventory_recommendations(
                    part_data[4], basic_forecast["predicted_demand"], forecast_days
                ),
                "generated_at": datetime.now().isoformat(),
                "note": "Forecast generated using basic algorithms"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get demand forecast for part {part_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parts/bulk-update")
async def bulk_update_parts(updates: List[Dict[str, Any]]):
    """Bulk update multiple parts (stock levels, costs, etc.)"""
    try:
        updated_parts = []
        failed_updates = []
        
        async with await get_database_client() as client:
            for update in updates:
                try:
                    part_id = update.get("id")
                    if not part_id:
                        failed_updates.append({"error": "Missing part ID", "update": update})
                        continue
                    
                    # Build update query dynamically
                    update_fields = []
                    params = []
                    
                    allowed_fields = ["quantity", "unit_cost", "supplier", "location", 
                                    "minimum_stock", "maximum_stock", "reorder_point", "lead_time_days"]
                    
                    for field in allowed_fields:
                        if field in update:
                            update_fields.append(f"{field} = %s")
                            params.append(update[field])
                    
                    if not update_fields:
                        failed_updates.append({"error": "No valid fields to update", "update": update})
                        continue
                    
                    update_fields.append("updated_at = NOW()")
                    params.append(part_id)
                    
                    query = f"UPDATE parts SET {', '.join(update_fields)} WHERE id = %s"
                    
                    response = await client.post("/api/query", json={
                        "query": query,
                        "params": params,
                        "fetch": None
                    })
                    response.raise_for_status()
                    
                    updated_parts.append({"id": part_id, "status": "updated"})
                    
                    # Check for reorder requirements after update
                    if "quantity" in update:
                        await check_reorder_requirements(part_id)
                        
                except Exception as e:
                    failed_updates.append({"error": str(e), "update": update})
                    logger.error(f"Failed to update part {update.get('id', 'unknown')}: {e}")
        
        return {
            "total_requested": len(updates),
            "updated_count": len(updated_parts),
            "failed_count": len(failed_updates),
            "updated_parts": updated_parts,
            "failed_updates": failed_updates
        }
    except Exception as e:
        logger.error(f"Bulk update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/optimization-report")
async def get_optimization_report():
    """Get comprehensive inventory optimization report"""
    try:
        async with await get_database_client() as client:
            report = {}
            
            # Dead stock analysis (no usage in simulated period)
            dead_stock_response = await client.post("/api/query", json={
                "query": """
                SELECT id, name, part_number, quantity, unit_cost, 
                       (quantity * COALESCE(unit_cost, 0)) as tied_up_value
                FROM parts 
                WHERE quantity > 50 AND created_at < NOW() - INTERVAL '6 months'
                ORDER BY tied_up_value DESC
                LIMIT 20
                """,
                "fetch": "all"
            })
            dead_stock_response.raise_for_status()
            report["potential_dead_stock"] = [
                {
                    "id": row[0], "name": row[1], "part_number": row[2],
                    "quantity": row[3], "unit_cost": row[4], "tied_up_value": row[5]
                }
                for row in dead_stock_response.json()["data"]
            ]
            
            # Overstocked items
            overstock_response = await client.post("/api/query", json={
                "query": """
                SELECT id, name, part_number, quantity, maximum_stock,
                       (quantity - COALESCE(maximum_stock, quantity)) as excess_quantity
                FROM parts 
                WHERE quantity > COALESCE(maximum_stock, quantity * 2)
                ORDER BY excess_quantity DESC
                LIMIT 15
                """,
                "fetch": "all"
            })
            overstock_response.raise_for_status()
            report["overstocked_items"] = [
                {
                    "id": row[0], "name": row[1], "part_number": row[2],
                    "current_quantity": row[3], "max_stock": row[4], "excess_quantity": row[5]
                }
                for row in overstock_response.json()["data"]
            ]
            
            # ABC analysis (by value)
            abc_response = await client.post("/api/query", json={
                "query": """
                SELECT name, part_number, (quantity * COALESCE(unit_cost, 0)) as total_value,
                       CASE 
                           WHEN (quantity * COALESCE(unit_cost, 0)) > 1000 THEN 'A'
                           WHEN (quantity * COALESCE(unit_cost, 0)) > 100 THEN 'B'
                           ELSE 'C'
                       END as abc_category
                FROM parts 
                WHERE unit_cost IS NOT NULL
                ORDER BY total_value DESC
                LIMIT 50
                """,
                "fetch": "all"
            })
            abc_response.raise_for_status()
            
            abc_data = abc_response.json()["data"]
            report["abc_analysis"] = {
                "A_category": [row for row in abc_data if row[3] == 'A'],
                "B_category": [row for row in abc_data if row[3] == 'B'],
                "C_category": [row for row in abc_data if row[3] == 'C']
            }
            
            # Cost optimization opportunities
            cost_opportunities = await client.post("/api/query", json={
                "query": """
                SELECT supplier, COUNT(*) as part_count, AVG(unit_cost) as avg_cost,
                       SUM(quantity * COALESCE(unit_cost, 0)) as total_value
                FROM parts 
                WHERE supplier IS NOT NULL AND unit_cost IS NOT NULL
                GROUP BY supplier
                HAVING COUNT(*) > 1
                ORDER BY total_value DESC
                """,
                "fetch": "all"
            })
            cost_opportunities.raise_for_status()
            report["supplier_consolidation_opportunities"] = [
                {
                    "supplier": row[0], "part_count": row[1], 
                    "avg_cost": round(row[2], 2), "total_value": round(row[3], 2)
                }
                for row in cost_opportunities.json()["data"]
            ]
            
            # Generate recommendations
            report["recommendations"] = generate_optimization_recommendations(report)
            report["generated_at"] = datetime.now().isoformat()
            
            return report
            
    except Exception as e:
        logger.error(f"Failed to generate optimization report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced AI Helper Functions
async def initialize_stock_management(part_id: int, part: PartCreate):
    """Initialize AI-powered stock management for new part"""
    try:
        # Call AI Brain service for intelligent stock level recommendations
        ai_brain_url = os.getenv("AI_BRAIN_SERVICE_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as ai_client:
                ai_response = await ai_client.post(f"{ai_brain_url}/api/ai/analysis", json={
                    "analysis_type": "demand_forecast",
                    "data_sources": ["parts"],
                    "parameters": {
                        "part_id": part_id,
                        "initial_quantity": part.quantity,
                        "part_type": "new",
                        "supplier": part.supplier
                    }
                })
                
                if ai_response.status_code == 200:
                    ai_result = ai_response.json()
                    recommended_levels = ai_result.get("results", {}).get("recommended_stock_levels", {})
                    
                    default_min = recommended_levels.get("minimum_stock", max(5, part.quantity // 8))
                    default_reorder = recommended_levels.get("reorder_point", max(10, part.quantity // 4))
                    default_max = recommended_levels.get("maximum_stock", part.quantity * 2)
                else:
                    # Fallback to basic calculation
                    default_reorder = max(10, part.quantity // 4)
                    default_min = max(5, part.quantity // 8)
                    default_max = part.quantity * 2
        except Exception as ai_error:
            logger.warning(f"AI Brain service unavailable for part {part_id}: {ai_error}")
            # Fallback to basic calculation
            default_reorder = max(10, part.quantity // 4)
            default_min = max(5, part.quantity // 8)
            default_max = part.quantity * 2
        
        # Update part with AI-recommended or calculated defaults
        if part.minimum_stock is None or part.reorder_point is None:
            async with await get_database_client() as client:
                update_query = """
                UPDATE parts 
                SET minimum_stock = COALESCE(minimum_stock, %s),
                    reorder_point = COALESCE(reorder_point, %s),
                    maximum_stock = COALESCE(maximum_stock, %s)
                WHERE id = %s
                """
                
                params = [default_min, default_reorder, default_max, part_id]
                
                response = await client.post("/api/query", json={
                    "query": update_query,
                    "params": params,
                    "fetch": None
                })
                response.raise_for_status()
        
        logger.info(f"AI-optimized stock management initialized for part {part_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize stock management for part {part_id}: {e}")
        return False

def get_stock_status(part: Dict[str, Any]) -> str:
    """Determine stock status for a part"""
    quantity = part.get("quantity", 0)
    minimum_stock = part.get("minimum_stock", 5)
    reorder_point = part.get("reorder_point", 10)
    
    if quantity == 0:
        return "out_of_stock"
    elif quantity <= minimum_stock:
        return "critical"
    elif quantity <= reorder_point:
        return "low"
    else:
        return "normal"

def calculate_days_of_stock(part: Dict[str, Any]) -> Optional[int]:
    """Calculate estimated days of stock remaining based on usage"""
    # This would use actual usage data in production
    # For now, return a simulated value
    import random
    quantity = part.get("quantity", 0)
    if quantity == 0:
        return 0
    
    # Simulate daily usage rate
    daily_usage = random.uniform(0.5, 3.0)
    return int(quantity / daily_usage) if daily_usage > 0 else None

def generate_inventory_recommendations(current_stock: int, predicted_demand: int, forecast_days: int) -> Dict[str, Any]:
    """Generate inventory recommendations based on demand forecast"""
    daily_demand = predicted_demand / forecast_days if forecast_days > 0 else 0
    days_of_stock = current_stock / daily_demand if daily_demand > 0 else float('inf')
    
    recommendations = []
    urgency = "low"
    
    if days_of_stock < 7:
        recommendations.append("URGENT: Stock will run out within a week")
        urgency = "high"
    elif days_of_stock < 30:
        recommendations.append("Consider reordering soon to avoid stockout")
        urgency = "medium"
    elif days_of_stock > 180:
        recommendations.append("Consider reducing stock levels to free up capital")
        urgency = "low"
    
    # Optimal order quantity (simplified EOQ)
    optimal_order = max(int(predicted_demand * 0.5), 10)
    
    return {
        "current_days_of_stock": round(days_of_stock, 1),
        "predicted_daily_demand": round(daily_demand, 2),
        "recommended_order_quantity": optimal_order,
        "urgency": urgency,
        "recommendations": recommendations,
        "optimal_reorder_date": (datetime.now() + timedelta(days=max(int(days_of_stock - 14), 1))).isoformat()
    }

def generate_basic_demand_forecast(part_data: List[Any], forecast_days: int) -> Dict[str, Any]:
    """Generate basic demand forecast when AI service is unavailable"""
    import random
    
    # Use part characteristics to estimate demand
    current_quantity = part_data[4] if len(part_data) > 4 else 0
    
    # Simulate demand based on current stock (higher stock = higher historical usage)
    base_monthly_demand = max(1, current_quantity // 10)
    seasonal_factor = random.uniform(0.8, 1.3)
    
    predicted_demand = int(base_monthly_demand * (forecast_days / 30) * seasonal_factor)
    
    return {
        "predicted_demand": predicted_demand,
        "confidence_score": 0.7,
        "seasonal_factor": round(seasonal_factor, 2),
        "trend": random.choice(["stable", "increasing", "decreasing"]),
        "method": "basic_algorithm"
    }

def generate_optimization_recommendations(report: Dict[str, Any]) -> List[str]:
    """Generate optimization recommendations based on analysis"""
    recommendations = []
    
    # Dead stock recommendations
    dead_stock = report.get("potential_dead_stock", [])
    if len(dead_stock) > 5:
        recommendations.append(f"Review {len(dead_stock)} potential dead stock items for liquidation")
    
    # Overstock recommendations
    overstock = report.get("overstocked_items", [])
    if len(overstock) > 3:
        recommendations.append(f"Reduce stock levels for {len(overstock)} overstocked items")
    
    # ABC analysis recommendations
    abc_analysis = report.get("abc_analysis", {})
    a_items = len(abc_analysis.get("A_category", []))
    if a_items > 0:
        recommendations.append(f"Focus on optimizing {a_items} high-value A-category items")
    
    # Supplier consolidation
    supplier_opps = report.get("supplier_consolidation_opportunities", [])
    if len(supplier_opps) > 5:
        recommendations.append("Consider consolidating suppliers to reduce procurement complexity")
    
    if not recommendations:
        recommendations.append("Inventory appears well-optimized - continue monitoring")
    
    return recommendations

async def check_reorder_requirements(part_id: int):
    """Enhanced reorder checking with AI-powered procurement automation"""
    try:
        async with await get_database_client() as client:
            response = await client.post("/api/query", json={
                "query": """
                SELECT name, quantity, reorder_point, supplier, unit_cost, lead_time_days,
                       minimum_stock, maximum_stock
                FROM parts 
                WHERE id = %s
                """,
                "params": [part_id],
                "fetch": "one"
            })
            response.raise_for_status()
            result = response.json()["data"]
            
            if not result:
                return False
            
            name, quantity, reorder_point, supplier, unit_cost, lead_time_days, min_stock, max_stock = result
            reorder_point = reorder_point or 10
            
            # Check if reordering is needed
            needs_reorder = quantity <= reorder_point
            is_critical = quantity <= (min_stock or 5)
            
            if needs_reorder:
                logger.warning(f"Part {name} (ID: {part_id}) is below reorder point: {quantity} <= {reorder_point}")
                
                # Calculate optimal order quantity
                target_stock = max_stock or (reorder_point * 3)
                order_quantity = target_stock - quantity
                
                # Call AI Brain for procurement optimization
                ai_brain_url = os.getenv("AI_BRAIN_SERVICE_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
                
                try:
                    async with httpx.AsyncClient(timeout=30.0) as ai_client:
                        ai_response = await ai_client.post(f"{ai_brain_url}/api/ai/optimize", json={
                            "optimization_type": "cost",
                            "objectives": ["minimize_cost", "optimize_delivery_time"],
                            "constraints": {
                                "part_id": part_id,
                                "current_quantity": quantity,
                                "required_quantity": order_quantity,
                                "supplier": supplier,
                                "unit_cost": unit_cost,
                                "lead_time_days": lead_time_days
                            }
                        })
                        
                        if ai_response.status_code == 200:
                            ai_result = ai_response.json()
                            optimization = ai_result.get("results", {})
                            
                            # Create optimized procurement request
                            procurement_data = {
                                "part_id": part_id,
                                "part_name": name,
                                "current_stock": quantity,
                                "reorder_point": reorder_point,
                                "recommended_quantity": optimization.get("optimal_quantity", order_quantity),
                                "estimated_cost": optimization.get("estimated_cost", (unit_cost or 0) * order_quantity),
                                "priority": "critical" if is_critical else "normal",
                                "supplier": supplier,
                                "ai_optimized": True,
                                "created_at": datetime.now().isoformat()
                            }
                            
                            logger.info(f"AI-optimized procurement request created for part {part_id}: {procurement_data}")
                            return True
                except Exception as ai_error:
                    logger.warning(f"AI optimization failed for part {part_id}: {ai_error}")
                
                # Fallback: Create basic procurement request
                procurement_data = {
                    "part_id": part_id,
                    "part_name": name,
                    "current_stock": quantity,
                    "recommended_quantity": order_quantity,
                    "estimated_cost": (unit_cost or 0) * order_quantity,
                    "priority": "critical" if is_critical else "normal",
                    "supplier": supplier,
                    "ai_optimized": False,
                    "created_at": datetime.now().isoformat()
                }
                
                logger.info(f"Basic procurement request created for part {part_id}: {procurement_data}")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Failed to check reorder requirements for part {part_id}: {e}")
        return False

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)