#!/usr/bin/env python3
"""
ChatterFix CMMS - Parts Service (Port 8004)
Handles all parts inventory management operations for the microservices architecture
"""

import os
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(title="ChatterFix Parts Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database service URL
DATABASE_SERVICE_URL = "http://localhost:8001"

# Pydantic models
class Part(BaseModel):
    name: str
    description: Optional[str] = ""
    part_number: Optional[str] = ""
    category: Optional[str] = "general"
    current_stock: Optional[int] = 0
    min_stock_level: Optional[int] = 5
    max_stock_level: Optional[int] = 100
    unit_cost: Optional[float] = 0.0
    supplier: Optional[str] = ""
    location: Optional[str] = ""

class PartUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    part_number: Optional[str] = None
    category: Optional[str] = None
    current_stock: Optional[int] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    unit_cost: Optional[float] = None
    supplier: Optional[str] = None
    location: Optional[str] = None

class StockUpdate(BaseModel):
    quantity: int
    operation: str  # 'add', 'subtract', 'set'
    reason: Optional[str] = ""

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
            "service": "ChatterFix Parts Service",
            "port": 8004,
            "database_status": db_response.get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/parts")
async def get_parts(
    category: Optional[str] = None,
    supplier: Optional[str] = None,
    location: Optional[str] = None,
    low_stock: Optional[bool] = None,
    limit: Optional[int] = 100
):
    """Get parts with optional filtering"""
    try:
        query = "SELECT * FROM parts"
        params = {}
        conditions = []
        
        if category:
            conditions.append("category = :category")
            params["category"] = category
        
        if supplier:
            conditions.append("supplier = :supplier")
            params["supplier"] = supplier
        
        if location:
            conditions.append("location = :location")
            params["location"] = location
        
        if low_stock:
            conditions.append("current_stock <= min_stock_level")
        
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
            return {"success": True, "parts": response.get("data", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/{part_id}")
async def get_part(part_id: int):
    """Get a specific part by ID"""
    try:
        response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT * FROM parts WHERE id = :id",
                "params": {"id": part_id}
            }
        )
        
        if response.get("success"):
            data = response.get("data", [])
            if data:
                return {"success": True, "part": data[0]}
            else:
                raise HTTPException(status_code=404, detail="Part not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parts")
async def create_part(part: Part):
    """Create a new part"""
    try:
        query = """
            INSERT INTO parts 
            (name, description, part_number, category, current_stock, min_stock_level, 
             max_stock_level, unit_cost, supplier, location, created_at)
            VALUES (:name, :description, :part_number, :category, :current_stock, 
                   :min_stock_level, :max_stock_level, :unit_cost, :supplier, :location, :created_at)
        """
        
        params = {
            "name": part.name,
            "description": part.description,
            "part_number": part.part_number,
            "category": part.category,
            "current_stock": part.current_stock,
            "min_stock_level": part.min_stock_level,
            "max_stock_level": part.max_stock_level,
            "unit_cost": part.unit_cost,
            "supplier": part.supplier,
            "location": part.location,
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
                "message": "Part created successfully",
                "rows_affected": response.get("rows_affected", 0)
            }
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to create part"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/parts/{part_id}")
async def update_part(part_id: int, updates: PartUpdate):
    """Update an existing part"""
    try:
        # Build dynamic update query
        update_fields = []
        params = {"id": part_id}
        
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        query = f"UPDATE parts SET {', '.join(update_fields)} WHERE id = :id"
        
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
                    "message": "Part updated successfully",
                    "rows_affected": rows_affected
                }
            else:
                raise HTTPException(status_code=404, detail="Part not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to update part"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/parts/{part_id}/stock")
async def update_part_stock(part_id: int, stock_update: StockUpdate):
    """Update part stock levels"""
    try:
        # First get current stock
        current_response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT current_stock FROM parts WHERE id = :id",
                "params": {"id": part_id}
            }
        )
        
        if not current_response.get("success") or not current_response.get("data"):
            raise HTTPException(status_code=404, detail="Part not found")
        
        current_stock = current_response.get("data")[0]["current_stock"]
        
        # Calculate new stock level
        if stock_update.operation == "add":
            new_stock = current_stock + stock_update.quantity
        elif stock_update.operation == "subtract":
            new_stock = max(0, current_stock - stock_update.quantity)  # Don't go below 0
        elif stock_update.operation == "set":
            new_stock = stock_update.quantity
        else:
            raise HTTPException(status_code=400, detail="Invalid operation. Use 'add', 'subtract', or 'set'")
        
        # Update stock
        response = call_database_service(
            "/api/execute",
            "POST",
            {
                "query": "UPDATE parts SET current_stock = :new_stock WHERE id = :id",
                "params": {"id": part_id, "new_stock": new_stock}
            }
        )
        
        if response.get("success"):
            return {
                "success": True,
                "message": f"Stock updated from {current_stock} to {new_stock}",
                "old_stock": current_stock,
                "new_stock": new_stock,
                "operation": stock_update.operation,
                "quantity": stock_update.quantity
            }
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to update stock"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/parts/{part_id}")
async def delete_part(part_id: int):
    """Delete a part"""
    try:
        response = call_database_service(
            "/api/execute",
            "POST",
            {
                "query": "DELETE FROM parts WHERE id = :id",
                "params": {"id": part_id}
            }
        )
        
        if response.get("success"):
            rows_affected = response.get("rows_affected", 0)
            if rows_affected > 0:
                return {
                    "success": True,
                    "message": "Part deleted successfully",
                    "rows_affected": rows_affected
                }
            else:
                raise HTTPException(status_code=404, detail="Part not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to delete part"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/stats/dashboard")
async def get_parts_stats():
    """Get parts statistics for dashboard"""
    try:
        # Get category counts
        category_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT category, COUNT(*) as count FROM parts GROUP BY category"}
        )
        
        # Get low stock count
        low_stock_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT COUNT(*) as count FROM parts WHERE current_stock <= min_stock_level"}
        )
        
        # Get total value
        value_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT SUM(current_stock * unit_cost) as total_value FROM parts"}
        )
        
        # Get supplier counts
        supplier_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT supplier, COUNT(*) as count FROM parts WHERE supplier != '' GROUP BY supplier"}
        )
        
        stats = {
            "category_breakdown": category_response.get("data", []) if category_response.get("success") else [],
            "low_stock_count": low_stock_response.get("data", [{}])[0].get("count", 0) if low_stock_response.get("success") else 0,
            "total_inventory_value": value_response.get("data", [{}])[0].get("total_value", 0) if value_response.get("success") else 0,
            "supplier_breakdown": supplier_response.get("data", []) if supplier_response.get("success") else [],
            "timestamp": datetime.now().isoformat()
        }
        
        return {"success": True, "stats": stats}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/low-stock")
async def get_low_stock_parts():
    """Get parts with low stock levels"""
    try:
        response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": """
                    SELECT *, (min_stock_level - current_stock) as shortage
                    FROM parts 
                    WHERE current_stock <= min_stock_level
                    ORDER BY shortage DESC
                """
            }
        )
        
        if response.get("success"):
            return {"success": True, "parts": response.get("data", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/search")
async def search_parts(q: str):
    """Search parts by name, description, or part number"""
    try:
        response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": """
                    SELECT * FROM parts 
                    WHERE name LIKE :query 
                    OR description LIKE :query 
                    OR part_number LIKE :query
                    ORDER BY name ASC
                """,
                "params": {"query": f"%{q}%"}
            }
        )
        
        if response.get("success"):
            return {"success": True, "parts": response.get("data", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatterFix Parts Service')
    parser.add_argument('--port', type=int, default=8004, help='Port to run service on')
    
    args = parser.parse_args()
    
    print(f"⚙️  Starting ChatterFix Parts Service on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)