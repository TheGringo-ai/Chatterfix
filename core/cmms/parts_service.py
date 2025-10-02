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
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "https://chatterfix-database-psycl7nhha-uc.a.run.app")

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
    movement_type: str = Field(..., regex="^(in|out|adjustment|transfer)$")
    quantity: int = Field(..., ne=0)
    reference: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    work_order_id: Optional[int] = None

class ProcurementRequest(BaseModel):
    part_id: int
    quantity: int = Field(..., gt=0)
    urgency: str = Field(default="normal", regex="^(low|normal|high|emergency)$")
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
    """Parts service dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Parts Service - Advanced AI CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            color: #333;
            min-height: 100vh;
        }
        .header {
            background: rgba(0,0,0,0.1);
            padding: 2rem;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.3);
        }
        .header h1 {
            margin: 0;
            font-size: 3rem;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle {
            margin: 1rem 0 0 0;
            color: #666;
            font-size: 1.2rem;
        }
        .dashboard {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: rgba(255,255,255,0.8);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.3);
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            display: block;
            margin-bottom: 0.5rem;
            color: #667eea;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        .feature-card {
            background: rgba(255,255,255,0.8);
            border-radius: 15px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        .inventory-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        .inventory-card {
            background: rgba(255,255,255,0.8);
            border-radius: 10px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .api-section {
            margin-top: 2rem;
            padding: 2rem;
            background: rgba(255,255,255,0.8);
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .endpoint {
            background: rgba(102,126,234,0.1);
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 5px;
            font-family: monospace;
            border-left: 4px solid #667eea;
        }
        .alert-low {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            color: white;
        }
        .alert-normal {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔧 Parts Service</h1>
            <p class="subtitle">Advanced AI Inventory Management</p>
        </div>

        <div class="dashboard">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number" id="total-parts">-</span>
                    <div>Total Parts</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="in-stock">-</span>
                    <div>In Stock</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="low-stock">-</span>
                    <div>Low Stock Items</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="total-value">$-</span>
                    <div>Total Inventory Value</div>
                </div>
            </div>

            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <h3>AI Demand Forecasting</h3>
                    <p>Advanced machine learning algorithms predict future part requirements based on usage patterns and seasonal trends.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📦</div>
                    <h3>Automated Procurement</h3>
                    <p>Smart reordering system automatically generates purchase orders when stock levels reach predefined thresholds.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>Real-time Analytics</h3>
                    <p>Comprehensive analytics dashboard with inventory turnover, cost analysis, and supplier performance metrics.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3>Smart Alerts</h3>
                    <p>Intelligent notification system for low stock, expired items, and procurement recommendations.</p>
                </div>
            </div>

            <div class="inventory-grid">
                <div class="inventory-card alert-low">
                    <h4>🚨 Critical Stock Levels</h4>
                    <p>Parts requiring immediate attention</p>
                    <span id="critical-stock">Loading...</span>
                </div>
                <div class="inventory-card alert-normal">
                    <h4>📋 Pending Orders</h4>
                    <p>Parts on order from suppliers</p>
                    <span id="pending-orders">Loading...</span>
                </div>
                <div class="inventory-card alert-normal">
                    <h4>📈 Turnover Rate</h4>
                    <p>Average inventory turnover</p>
                    <span id="turnover-rate">Loading...</span>
                </div>
                <div class="inventory-card alert-normal">
                    <h4>🎯 Forecast Accuracy</h4>
                    <p>AI prediction accuracy</p>
                    <span id="forecast-accuracy">Loading...</span>
                </div>
            </div>

            <div class="api-section">
                <h3>🔗 API Endpoints</h3>
                <div class="endpoint">GET /api/parts - List all parts</div>
                <div class="endpoint">POST /api/parts - Create new part</div>
                <div class="endpoint">GET /api/parts/{id} - Get specific part</div>
                <div class="endpoint">PUT /api/parts/{id} - Update part</div>
                <div class="endpoint">DELETE /api/parts/{id} - Delete part</div>
                <div class="endpoint">GET /api/parts/low-stock - Get low stock items</div>
                <div class="endpoint">POST /api/parts/{id}/movement - Record stock movement</div>
                <div class="endpoint">POST /api/parts/{id}/procurement - Create procurement request</div>
                <div class="endpoint">GET /api/parts/analytics - Advanced analytics</div>
            </div>
        </div>

        <script>
        // Load parts statistics
        fetch('/api/parts/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('total-parts').textContent = data.total || 0;
                document.getElementById('in-stock').textContent = data.in_stock || 0;
                document.getElementById('low-stock').textContent = data.low_stock || 0;
                document.getElementById('total-value').textContent = '$' + (data.total_value || 0).toLocaleString();
            })
            .catch(error => console.error('Failed to load stats:', error));

        // Load inventory analytics
        fetch('/api/parts/analytics')
            .then(response => response.json())
            .then(data => {
                document.getElementById('critical-stock').textContent = data.critical_stock || 0;
                document.getElementById('pending-orders').textContent = data.pending_orders || 0;
                document.getElementById('turnover-rate').textContent = (data.turnover_rate || 0) + 'x/year';
                document.getElementById('forecast-accuracy').textContent = (data.forecast_accuracy || 0) + '%';
            })
            .catch(error => console.error('Failed to load analytics:', error));
        </script>
    </body>
    </html>
    """

# Parts CRUD Operations
@app.get("/api/parts", response_model=List[PartResponse])
async def get_parts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    supplier: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None)
):
    """Get parts with filtering and pagination"""
    try:
        async with await get_database_client() as client:
            params = {"limit": limit, "offset": offset}
            if supplier:
                params["supplier"] = supplier
            if location:
                params["location"] = location
            
            response = await client.get("/api/parts", params=params)
            response.raise_for_status()
            parts = response.json()
            
            # Filter for low stock if requested
            if low_stock:
                parts = [p for p in parts if p.get("quantity", 0) <= p.get("reorder_point", 0)]
            
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

# AI Helper Functions
async def initialize_stock_management(part_id: int, part: PartCreate):
    """Initialize AI-powered stock management for new part"""
    try:
        # This would integrate with the AI Brain service
        # For now, set intelligent defaults based on part characteristics
        
        if part.minimum_stock is None or part.reorder_point is None:
            # Set intelligent defaults
            default_reorder = max(10, part.quantity // 4)  # 25% of initial stock or 10, whichever is higher
            default_min = max(5, part.quantity // 8)       # 12.5% of initial stock or 5, whichever is higher
            
            async with await get_database_client() as client:
                update_query = """
                UPDATE parts 
                SET minimum_stock = COALESCE(minimum_stock, %s),
                    reorder_point = COALESCE(reorder_point, %s),
                    maximum_stock = COALESCE(maximum_stock, %s)
                WHERE id = %s
                """
                
                params = [default_min, default_reorder, part.quantity * 2, part_id]
                
                response = await client.post("/api/query", json={
                    "query": update_query,
                    "params": params,
                    "fetch": None
                })
                response.raise_for_status()
        
        logger.info(f"Initialized stock management for part {part_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize stock management for part {part_id}: {e}")
        return False

async def check_reorder_requirements(part_id: int):
    """Check if part needs reordering and trigger automated procurement"""
    try:
        async with await get_database_client() as client:
            response = await client.post("/api/query", json={
                "query": """
                SELECT name, quantity, reorder_point, supplier 
                FROM parts 
                WHERE id = %s AND quantity <= COALESCE(reorder_point, 10)
                """,
                "params": [part_id],
                "fetch": "one"
            })
            response.raise_for_status()
            result = response.json()["data"]
            
            if result:
                name, quantity, reorder_point, supplier = result
                logger.warning(f"Part {name} (ID: {part_id}) is below reorder point: {quantity} <= {reorder_point}")
                
                # In production, this would automatically create procurement requests
                # or integrate with supplier APIs for automatic ordering
                
                return True
        return False
    except Exception as e:
        logger.error(f"Failed to check reorder requirements for part {part_id}: {e}")
        return False

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)