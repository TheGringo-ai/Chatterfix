#!/usr/bin/env python3
"""
ChatterFix Parts Service - Inventory Management Microservice
Enterprise parts and inventory management
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
    title="ChatterFix Parts Service",
    description="Enterprise parts and inventory management microservice",
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
class Part(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    part_number: str
    category: str
    quantity: int = 0
    unit_price: float
    min_stock_level: int = 5
    supplier: Optional[str] = None
    location: Optional[str] = None
    last_restocked: Optional[datetime] = None

class PartCreate(BaseModel):
    name: str
    description: str
    part_number: str
    category: str
    quantity: int = 0
    unit_price: float
    min_stock_level: int = 5
    supplier: Optional[str] = None
    location: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "parts",
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
        "service": "parts",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Sample data for development
sample_parts = [
    {
        "id": 1001,
        "name": "HVAC Air Filter",
        "description": "High-efficiency particulate air filter",
        "part_number": "HEPA-001",
        "category": "HVAC",
        "quantity": 25,
        "unit_price": 34.99,
        "min_stock_level": 5,
        "supplier": "FilterCorp",
        "location": "Warehouse A-1",
        "last_restocked": "2025-10-15T00:00:00Z"
    },
    {
        "id": 1002,
        "name": "Conveyor Belt",
        "description": "Replacement conveyor belt 10ft",
        "part_number": "CB-10FT",
        "category": "Production",
        "quantity": 3,
        "unit_price": 299.99,
        "min_stock_level": 2,
        "supplier": "Dorner Manufacturing",
        "location": "Warehouse B-2",
        "last_restocked": "2025-09-20T00:00:00Z"
    },
    {
        "id": 1003,
        "name": "Fire Detector Battery",
        "description": "Lithium battery for smoke detectors",
        "part_number": "BAT-LI-9V",
        "category": "Safety",
        "quantity": 50,
        "unit_price": 8.99,
        "min_stock_level": 10,
        "supplier": "SafetyFirst Supplies",
        "location": "Warehouse A-3",
        "last_restocked": "2025-10-10T00:00:00Z"
    },
    {
        "id": 1004,
        "name": "Generator Oil Filter",
        "description": "Oil filter for backup generator",
        "part_number": "GEN-OF-001",
        "category": "Power",
        "quantity": 8,
        "unit_price": 24.99,
        "min_stock_level": 3,
        "supplier": "Generac Parts",
        "location": "Warehouse C-1",
        "last_restocked": "2025-08-25T00:00:00Z"
    },
    {
        "id": 1005,
        "name": "Bearing Assembly",
        "description": "Ball bearing assembly for conveyor",
        "part_number": "BRG-BALL-6205",
        "category": "Production",
        "quantity": 2,
        "unit_price": 45.99,
        "min_stock_level": 5,
        "supplier": "BearingWorld",
        "location": "Warehouse B-1",
        "last_restocked": "2025-07-15T00:00:00Z"
    }
]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "parts",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/parts", response_model=List[Dict[str, Any]])
async def get_parts(
    category: Optional[str] = Query(None, description="Filter by category"),
    low_stock: Optional[bool] = Query(None, description="Show only low stock items"),
    supplier: Optional[str] = Query(None, description="Filter by supplier")
):
    """Get all parts with optional filtering"""
    filtered_parts = sample_parts.copy()
    
    if category:
        filtered_parts = [part for part in filtered_parts if part["category"].lower() == category.lower()]
    
    if low_stock:
        filtered_parts = [part for part in filtered_parts if part["quantity"] <= part["min_stock_level"]]
    
    if supplier:
        filtered_parts = [part for part in filtered_parts if part.get("supplier") and supplier.lower() in part["supplier"].lower()]
    
    return filtered_parts

@app.get("/parts/{part_id}")
async def get_part(part_id: int):
    """Get a specific part by ID"""
    part = next((part for part in sample_parts if part["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part

@app.post("/parts", response_model=Dict[str, Any])
async def create_part(part: PartCreate):
    """Create a new part"""
    new_id = max([part["id"] for part in sample_parts]) + 1 if sample_parts else 1
    
    new_part = {
        "id": new_id,
        "name": part.name,
        "description": part.description,
        "part_number": part.part_number,
        "category": part.category,
        "quantity": part.quantity,
        "unit_price": part.unit_price,
        "min_stock_level": part.min_stock_level,
        "supplier": part.supplier,
        "location": part.location,
        "last_restocked": datetime.now().isoformat() if part.quantity > 0 else None
    }
    
    sample_parts.append(new_part)
    return new_part

@app.put("/parts/{part_id}/restock")
async def restock_part(part_id: int, quantity: int):
    """Restock a part"""
    part = next((part for part in sample_parts if part["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    part["quantity"] += quantity
    part["last_restocked"] = datetime.now().isoformat()
    return part

@app.put("/parts/{part_id}/consume")
async def consume_part(part_id: int, quantity: int):
    """Consume/use parts from inventory"""
    part = next((part for part in sample_parts if part["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    if part["quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    part["quantity"] -= quantity
    return part

@app.get("/parts/stats/summary")
async def get_parts_stats():
    """Get parts inventory statistics"""
    total = len(sample_parts)
    total_value = sum(part["quantity"] * part["unit_price"] for part in sample_parts)
    low_stock_items = [part for part in sample_parts if part["quantity"] <= part["min_stock_level"]]
    
    by_category = {}
    for part in sample_parts:
        category = part["category"]
        if category not in by_category:
            by_category[category] = {"count": 0, "total_quantity": 0, "total_value": 0}
        
        by_category[category]["count"] += 1
        by_category[category]["total_quantity"] += part["quantity"]
        by_category[category]["total_value"] += part["quantity"] * part["unit_price"]
    
    return {
        "total_parts": total,
        "total_inventory_value": round(total_value, 2),
        "low_stock_items": len(low_stock_items),
        "low_stock_parts": [{"id": p["id"], "name": p["name"], "quantity": p["quantity"], "min_level": p["min_stock_level"]} for p in low_stock_items],
        "by_category": by_category
    }

@app.get("/parts/alerts/low-stock")
async def get_low_stock_alerts():
    """Get low stock alerts"""
    low_stock_items = [part for part in sample_parts if part["quantity"] <= part["min_stock_level"]]
    
    alerts = []
    for part in low_stock_items:
        alerts.append({
            "id": part["id"],
            "name": part["name"],
            "part_number": part["part_number"],
            "current_quantity": part["quantity"],
            "min_stock_level": part["min_stock_level"],
            "supplier": part.get("supplier"),
            "urgency": "Critical" if part["quantity"] == 0 else "Low"
        })
    
    return {"alerts": alerts, "total_alerts": len(alerts)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)