#!/usr/bin/env python3
"""
ChatterFix CMMS - Assets Service (Port 8003)
Handles all asset management operations for the microservices architecture
"""

import os
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(title="ChatterFix Assets Service", version="1.0.0")

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
class Asset(BaseModel):
    name: str
    description: Optional[str] = ""
    asset_type: Optional[str] = "equipment"
    location: Optional[str] = ""
    status: Optional[str] = "active"
    manufacturer: Optional[str] = ""
    model: Optional[str] = ""
    serial_number: Optional[str] = ""
    purchase_date: Optional[str] = None
    warranty_expiry: Optional[str] = None
    next_maintenance_date: Optional[str] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    asset_type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_expiry: Optional[str] = None
    next_maintenance_date: Optional[str] = None

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
            "service": "ChatterFix Assets Service",
            "port": 8003,
            "database_status": db_response.get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/assets")
async def get_assets(
    status: Optional[str] = None,
    asset_type: Optional[str] = None,
    location: Optional[str] = None,
    limit: Optional[int] = 100
):
    """Get assets with optional filtering"""
    try:
        query = "SELECT * FROM assets"
        params = {}
        conditions = []
        
        if status:
            conditions.append("status = :status")
            params["status"] = status
        
        if asset_type:
            conditions.append("asset_type = :asset_type")
            params["asset_type"] = asset_type
        
        if location:
            conditions.append("location = :location")
            params["location"] = location
        
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
            return {"success": True, "assets": response.get("data", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: int):
    """Get a specific asset by ID"""
    try:
        response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT * FROM assets WHERE id = :id",
                "params": {"id": asset_id}
            }
        )
        
        if response.get("success"):
            data = response.get("data", [])
            if data:
                return {"success": True, "asset": data[0]}
            else:
                raise HTTPException(status_code=404, detail="Asset not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets")
async def create_asset(asset: Asset):
    """Create a new asset"""
    try:
        query = """
            INSERT INTO assets 
            (name, description, asset_type, location, status, manufacturer, model, 
             serial_number, purchase_date, warranty_expiry, next_maintenance_date, created_at)
            VALUES (:name, :description, :asset_type, :location, :status, :manufacturer, 
                   :model, :serial_number, :purchase_date, :warranty_expiry, :next_maintenance_date, :created_at)
        """
        
        params = {
            "name": asset.name,
            "description": asset.description,
            "asset_type": asset.asset_type,
            "location": asset.location,
            "status": asset.status,
            "manufacturer": asset.manufacturer,
            "model": asset.model,
            "serial_number": asset.serial_number,
            "purchase_date": asset.purchase_date,
            "warranty_expiry": asset.warranty_expiry,
            "next_maintenance_date": asset.next_maintenance_date,
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
                "message": "Asset created successfully",
                "rows_affected": response.get("rows_affected", 0)
            }
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to create asset"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/assets/{asset_id}")
async def update_asset(asset_id: int, updates: AssetUpdate):
    """Update an existing asset"""
    try:
        # Build dynamic update query
        update_fields = []
        params = {"id": asset_id}
        
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        query = f"UPDATE assets SET {', '.join(update_fields)} WHERE id = :id"
        
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
                    "message": "Asset updated successfully",
                    "rows_affected": rows_affected
                }
            else:
                raise HTTPException(status_code=404, detail="Asset not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to update asset"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: int):
    """Delete an asset"""
    try:
        response = call_database_service(
            "/api/execute",
            "POST",
            {
                "query": "DELETE FROM assets WHERE id = :id",
                "params": {"id": asset_id}
            }
        )
        
        if response.get("success"):
            rows_affected = response.get("rows_affected", 0)
            if rows_affected > 0:
                return {
                    "success": True,
                    "message": "Asset deleted successfully",
                    "rows_affected": rows_affected
                }
            else:
                raise HTTPException(status_code=404, detail="Asset not found")
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to delete asset"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/stats/dashboard")
async def get_asset_stats():
    """Get asset statistics for dashboard"""
    try:
        # Get status counts
        status_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT status, COUNT(*) as count FROM assets GROUP BY status"}
        )
        
        # Get type counts
        type_response = call_database_service(
            "/api/query",
            "POST",
            {"query": "SELECT asset_type, COUNT(*) as count FROM assets GROUP BY asset_type"}
        )
        
        # Get maintenance due count
        maintenance_response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT COUNT(*) as count FROM assets WHERE next_maintenance_date <= :due_date",
                "params": {"due_date": (datetime.now() + timedelta(days=7)).isoformat()}
            }
        )
        
        # Get warranty expiring count
        warranty_response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT COUNT(*) as count FROM assets WHERE warranty_expiry <= :expiry_date AND warranty_expiry IS NOT NULL",
                "params": {"expiry_date": (datetime.now() + timedelta(days=30)).isoformat()}
            }
        )
        
        stats = {
            "status_breakdown": status_response.get("data", []) if status_response.get("success") else [],
            "type_breakdown": type_response.get("data", []) if type_response.get("success") else [],
            "maintenance_due_count": maintenance_response.get("data", [{}])[0].get("count", 0) if maintenance_response.get("success") else 0,
            "warranty_expiring_count": warranty_response.get("data", [{}])[0].get("count", 0) if warranty_response.get("success") else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return {"success": True, "stats": stats}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/maintenance/due")
async def get_maintenance_due_assets():
    """Get assets with maintenance due soon"""
    try:
        response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": """
                    SELECT * FROM assets 
                    WHERE next_maintenance_date <= :due_date 
                    AND status = 'active'
                    ORDER BY next_maintenance_date ASC
                """,
                "params": {"due_date": (datetime.now() + timedelta(days=7)).isoformat()}
            }
        )
        
        if response.get("success"):
            return {"success": True, "assets": response.get("data", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/{asset_id}/work_orders")
async def get_asset_work_orders(asset_id: int):
    """Get work orders associated with an asset"""
    try:
        response = call_database_service(
            "/api/query",
            "POST",
            {
                "query": "SELECT * FROM work_orders WHERE asset_id = :asset_id ORDER BY created_at DESC",
                "params": {"asset_id": asset_id}
            }
        )
        
        if response.get("success"):
            return {"success": True, "work_orders": response.get("data", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("error", "Database query failed"))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatterFix Assets Service')
    parser.add_argument('--port', type=int, default=8003, help='Port to run service on')
    
    args = parser.parse_args()
    
    print(f"🏭 Starting ChatterFix Assets Service on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)