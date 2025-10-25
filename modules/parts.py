"""
Parts Module - Handles all parts inventory and checkout operations
"""

import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Form, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .shared import success_response, error_response, logger, verify_api_key

router = APIRouter()

# Pydantic models
class PartBase(BaseModel):
    sku: str = Field(..., max_length=100)
    part_number: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., max_length=100)
    uom: str = Field("Each", max_length=20)  # Unit of Measure
    min_qty: int = Field(0, ge=0)
    max_qty: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    bin_location: Optional[str] = None
    unit_cost: float = Field(0.0, ge=0)
    supplier_id: Optional[int] = None
    supplier_part_number: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0)
    dimensions: Optional[str] = None

class PartCreate(PartBase):
    stock_qty: int = Field(0, ge=0)

class PartUpdate(BaseModel):
    part_number: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    uom: Optional[str] = None
    min_qty: Optional[int] = Field(None, ge=0)
    max_qty: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    bin_location: Optional[str] = None
    unit_cost: Optional[float] = Field(None, ge=0)
    supplier_id: Optional[int] = None
    supplier_part_number: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0)
    dimensions: Optional[str] = None

class CheckoutRequest(BaseModel):
    qty: int = Field(..., gt=0)
    work_order_id: Optional[int] = None
    notes: Optional[str] = None

class RestockRequest(BaseModel):
    qty: int = Field(..., gt=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class InventoryAdjustment(BaseModel):
    qty: int  # Can be negative for decreases
    reason: str
    notes: Optional[str] = None

# Sample data
parts_data = [
    {
        "id": 1001,
        "sku": "HVAC-FILTER-001",
        "part_number": "HEPA-001",
        "name": "HVAC Air Filter - HEPA",
        "description": "High-efficiency particulate air filter for HVAC systems",
        "category": "HVAC",
        "uom": "Each",
        "stock_qty": 25,
        "min_qty": 5,
        "max_qty": 50,
        "location": "Warehouse A-1",
        "bin_location": "A1-15-B",
        "unit_cost": 34.99,
        "last_cost": 32.50,
        "supplier_id": 1,
        "supplier_part_number": "FC-HEPA-001",
        "photo_uri": None,
        "barcode": "123456789001",
        "weight": 2.5,
        "dimensions": "20x16x1 inches",
        "created_at": "2023-01-15T10:00:00Z",
        "updated_at": "2025-10-15T14:30:00Z"
    },
    {
        "id": 1002,
        "sku": "CONV-BELT-001",
        "part_number": "CB-10FT",
        "name": "Conveyor Belt - 10ft",
        "description": "Replacement conveyor belt for production line",
        "category": "Production",
        "uom": "Each",
        "stock_qty": 3,
        "min_qty": 2,
        "max_qty": 10,
        "location": "Warehouse B-2",
        "bin_location": "B2-08-A",
        "unit_cost": 299.99,
        "last_cost": 285.00,
        "supplier_id": 2,
        "supplier_part_number": "DOR-BELT-10",
        "photo_uri": None,
        "barcode": "123456789002",
        "weight": 45.0,
        "dimensions": "10ft x 12in x 0.5in",
        "created_at": "2023-03-20T10:00:00Z",
        "updated_at": "2025-09-20T11:15:00Z"
    },
    {
        "id": 1003,
        "sku": "SAFETY-BAT-001",
        "part_number": "BAT-LI-9V",
        "name": "Lithium Battery - 9V",
        "description": "Lithium battery for smoke detectors and safety equipment",
        "category": "Safety",
        "uom": "Each",
        "stock_qty": 50,
        "min_qty": 10,
        "max_qty": 100,
        "location": "Warehouse A-3",
        "bin_location": "A3-05-C",
        "unit_cost": 8.99,
        "last_cost": 8.50,
        "supplier_id": 3,
        "supplier_part_number": "SF-BATT-9V-LI",
        "photo_uri": None,
        "barcode": "123456789003",
        "weight": 0.2,
        "dimensions": "1.7x1.2x0.6 inches",
        "created_at": "2023-06-10T10:00:00Z",
        "updated_at": "2025-10-10T09:45:00Z"
    },
    {
        "id": 1004,
        "sku": "ELEV-CABLE-001",
        "part_number": "CABLE-STL-8MM",
        "name": "Elevator Steel Cable - 8mm",
        "description": "High-strength steel cable for elevator system",
        "category": "Elevator",
        "uom": "Meter",
        "stock_qty": 150,
        "min_qty": 50,
        "max_qty": 500,
        "location": "Warehouse C-1",
        "bin_location": "C1-02-A",
        "unit_cost": 12.50,
        "last_cost": 11.75,
        "supplier_id": 4,
        "supplier_part_number": "OTIS-CABLE-8MM",
        "photo_uri": None,
        "barcode": "123456789004",
        "weight": 0.8,
        "dimensions": "8mm diameter",
        "created_at": "2023-08-15T10:00:00Z",
        "updated_at": "2025-10-18T16:20:00Z"
    },
    {
        "id": 1005,
        "sku": "LIGHT-LED-001",
        "part_number": "LED-100W-5K",
        "name": "LED Fixture - 100W 5000K",
        "description": "High-efficiency LED light fixture for parking lot",
        "category": "Lighting",
        "uom": "Each",
        "stock_qty": 8,
        "min_qty": 5,
        "max_qty": 20,
        "location": "Warehouse B-1",
        "bin_location": "B1-12-C",
        "unit_cost": 89.99,
        "last_cost": 85.00,
        "supplier_id": 5,
        "supplier_part_number": "CREE-LED-100W",
        "photo_uri": None,
        "barcode": "123456789005",
        "weight": 3.2,
        "dimensions": "12x8x4 inches",
        "created_at": "2023-11-20T10:00:00Z",
        "updated_at": "2025-10-20T12:15:00Z"
    },
    {
        "id": 1006,
        "sku": "GEN-FILTER-001",
        "part_number": "AIR-FILTER-HD",
        "name": "Generator Air Filter - Heavy Duty",
        "description": "Heavy duty air filter for backup generator",
        "category": "Power",
        "uom": "Each",
        "stock_qty": 4,
        "min_qty": 2,
        "max_qty": 10,
        "location": "Warehouse A-2",
        "bin_location": "A2-07-B",
        "unit_cost": 45.99,
        "last_cost": 42.50,
        "supplier_id": 6,
        "supplier_part_number": "CAT-AIR-FILTER-HD",
        "photo_uri": None,
        "barcode": "123456789006",
        "weight": 1.8,
        "dimensions": "14x10x3 inches",
        "created_at": "2023-12-05T10:00:00Z",
        "updated_at": "2025-09-18T14:45:00Z"
    },
    {
        "id": 1007,
        "sku": "ROOF-SEAL-001",
        "part_number": "SEAL-EPDM-50FT",
        "name": "EPDM Roof Sealant - 50ft Roll",
        "description": "EPDM membrane sealant for roof repairs",
        "category": "Structure",
        "uom": "Roll",
        "stock_qty": 2,
        "min_qty": 1,
        "max_qty": 5,
        "location": "Warehouse C-2",
        "bin_location": "C2-01-A",
        "unit_cost": 199.99,
        "last_cost": 185.00,
        "supplier_id": 7,
        "supplier_part_number": "DL-EPDM-50",
        "photo_uri": None,
        "barcode": "123456789007",
        "weight": 25.0,
        "dimensions": "50ft x 2ft x 0.045in",
        "created_at": "2024-02-10T10:00:00Z",
        "updated_at": "2025-10-22T11:30:00Z"
    },
    {
        "id": 1008,
        "sku": "PLUMB-VALVE-001",
        "part_number": "VALVE-BALL-1IN",
        "name": "Ball Valve - 1 inch",
        "description": "Brass ball valve for plumbing system",
        "category": "Plumbing",
        "uom": "Each",
        "stock_qty": 12,
        "min_qty": 5,
        "max_qty": 25,
        "location": "Warehouse A-4",
        "bin_location": "A4-09-C",
        "unit_cost": 24.99,
        "last_cost": 22.50,
        "supplier_id": 8,
        "supplier_part_number": "KOH-VALVE-1IN",
        "photo_uri": None,
        "barcode": "123456789008",
        "weight": 0.7,
        "dimensions": "3x2x2 inches",
        "created_at": "2024-03-15T10:00:00Z",
        "updated_at": "2025-10-12T09:20:00Z"
    },
    {
        "id": 1009,
        "sku": "HVAC-COOL-001",
        "part_number": "COOLANT-R410A-25LB",
        "name": "R410A Refrigerant - 25lb",
        "description": "R410A refrigerant for HVAC systems",
        "category": "HVAC",
        "uom": "Tank",
        "stock_qty": 6,
        "min_qty": 3,
        "max_qty": 15,
        "location": "Warehouse B-3",
        "bin_location": "B3-04-A",
        "unit_cost": 149.99,
        "last_cost": 135.00,
        "supplier_id": 9,
        "supplier_part_number": "LIE-R410A-25",
        "photo_uri": None,
        "barcode": "123456789009",
        "weight": 25.0,
        "dimensions": "Tank - 25lb capacity",
        "created_at": "2024-05-20T10:00:00Z",
        "updated_at": "2025-09-25T15:10:00Z"
    }
]

suppliers_data = [
    {
        "id": 1,
        "name": "Industrial Supply Co",
        "contact_person": "John Smith",
        "email": "john@industrialsupply.com",
        "phone": "555-0101",
        "address": "123 Industrial Ave, Manufacturing City, MC 12345",
        "website": "https://industrialsupply.com",
        "payment_terms": "Net 30"
    },
    {
        "id": 2,
        "name": "MRO Parts Direct",
        "contact_person": "Sarah Johnson",
        "email": "sarah@mroparts.com",
        "phone": "555-0102",
        "address": "456 MRO Lane, Parts Town, PT 67890",
        "website": "https://mroparts.com",
        "payment_terms": "2/10 Net 30"
    }
]

transactions_data = {
    1001: [
        {
            "id": 1,
            "part_id": 1001,
            "transaction_type": "IN",
            "quantity": 20,
            "unit_cost": 34.99,
            "reference_type": "purchase",
            "reference_id": 100,
            "notes": "Monthly restocking",
            "performed_by": "John Smith",
            "ts": "2025-10-15T14:30:00Z"
        }
    ]
}

def record_transaction(part_id: int, transaction_type: str, quantity: int, 
                      unit_cost: float = None, reference_type: str = None, 
                      reference_id: int = None, work_order_id: int = None,
                      notes: str = None, performed_by: str = "API User"):
    """Record an inventory transaction"""
    if part_id not in transactions_data:
        transactions_data[part_id] = []
    
    transaction = {
        "id": len(transactions_data) * 10 + len(transactions_data[part_id]) + 1,
        "part_id": part_id,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "unit_cost": unit_cost,
        "reference_type": reference_type,
        "reference_id": reference_id,
        "work_order_id": work_order_id,
        "notes": notes,
        "performed_by": performed_by,
        "ts": datetime.now().isoformat()
    }
    
    transactions_data[part_id].append(transaction)
    return transaction

@router.get("/")
async def get_parts(
    authenticated: bool = Depends(verify_api_key),
    category: Optional[str] = Query(None, description="Filter by category"),
    low_stock: Optional[bool] = Query(None, description="Show only low stock items"),
    supplier: Optional[str] = Query(None, description="Filter by supplier"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in name, sku, or part_number"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all parts with optional filtering"""
    filtered_parts = parts_data.copy()
    
    if category:
        filtered_parts = [part for part in filtered_parts if part["category"].lower() == category.lower()]
    
    if low_stock:
        filtered_parts = [part for part in filtered_parts if part["stock_qty"] <= part["min_qty"]]
    
    if supplier:
        # Get supplier by name
        supplier_obj = next((s for s in suppliers_data if supplier.lower() in s["name"].lower()), None)
        if supplier_obj:
            filtered_parts = [part for part in filtered_parts if part.get("supplier_id") == supplier_obj["id"]]
    
    if location:
        filtered_parts = [part for part in filtered_parts if location.lower() in part.get("location", "").lower()]
    
    if search:
        search_lower = search.lower()
        filtered_parts = [
            part for part in filtered_parts 
            if (search_lower in part["name"].lower() or 
                search_lower in part["sku"].lower() or
                search_lower in part.get("part_number", "").lower())
        ]
    
    # Apply pagination
    total = len(filtered_parts)
    paginated = filtered_parts[offset:offset + limit]
    
    return {
        "parts": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{part_id}")
async def get_part(part_id: int, authenticated: bool = Depends(verify_api_key)):
    """Get detailed part with transaction history"""
    part = next((p for p in parts_data if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Enhance with related data
    result = part.copy()
    result["attachments"] = []  # TODO: Load from attachments
    result["recent_transactions"] = transactions_data.get(part_id, [])[-20:]  # Last 20 transactions
    
    # Add supplier info
    if part.get("supplier_id"):
        supplier = next((s for s in suppliers_data if s["id"] == part["supplier_id"]), None)
        result["supplier_info"] = supplier
    else:
        result["supplier_info"] = None
    
    return result

@router.post("/")
async def create_part(part: PartCreate, authenticated: bool = Depends(verify_api_key)):
    """Create a new part"""
    new_id = max([p["id"] for p in parts_data]) + 1 if parts_data else 1
    
    new_part = {
        "id": new_id,
        "sku": part.sku,
        "part_number": part.part_number,
        "name": part.name,
        "description": part.description,
        "category": part.category,
        "uom": part.uom,
        "stock_qty": part.stock_qty,
        "min_qty": part.min_qty,
        "max_qty": part.max_qty,
        "location": part.location,
        "bin_location": part.bin_location,
        "unit_cost": part.unit_cost,
        "last_cost": part.unit_cost,
        "supplier_id": part.supplier_id,
        "supplier_part_number": part.supplier_part_number,
        "photo_uri": None,
        "barcode": part.barcode,
        "weight": part.weight,
        "dimensions": part.dimensions,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    parts_data.append(new_part)
    
    # Record initial stock transaction if quantity > 0
    if part.stock_qty > 0:
        record_transaction(
            new_id, "IN", part.stock_qty, part.unit_cost,
            "initial_stock", None, None, "Initial inventory",
            "System"
        )
    
    return success_response("Part created successfully", {"part": new_part})

@router.post("/{part_id}/checkout")
async def checkout_part(part_id: int, checkout: CheckoutRequest, authenticated: bool = Depends(verify_api_key)):
    """Checkout parts from inventory"""
    part = next((p for p in parts_data if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    if part["stock_qty"] < checkout.qty:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient stock. Available: {part['stock_qty']}, Requested: {checkout.qty}"
        )
    
    # Update stock quantity
    part["stock_qty"] -= checkout.qty
    part["updated_at"] = datetime.now().isoformat()
    
    # Record transaction
    transaction = record_transaction(
        part_id, "OUT", checkout.qty, part["unit_cost"],
        "work_order" if checkout.work_order_id else "checkout",
        checkout.work_order_id, checkout.work_order_id,
        checkout.notes, "API User"
    )
    
    return success_response(
        f"Successfully checked out {checkout.qty} {part['uom']} of {part['name']}",
        {
            "remaining_stock": part["stock_qty"],
            "transaction": transaction,
            "low_stock_warning": part["stock_qty"] <= part["min_qty"]
        }
    )

@router.post("/{part_id}/restock")
async def restock_part(part_id: int, restock: RestockRequest, authenticated: bool = Depends(verify_api_key)):
    """Restock parts inventory"""
    part = next((p for p in parts_data if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Update stock quantity and cost
    part["stock_qty"] += restock.qty
    if restock.unit_cost is not None:
        part["last_cost"] = part["unit_cost"]
        part["unit_cost"] = restock.unit_cost
    part["updated_at"] = datetime.now().isoformat()
    
    # Record transaction
    transaction = record_transaction(
        part_id, "IN", restock.qty, restock.unit_cost or part["unit_cost"],
        "restock", None, None, restock.notes, "API User"
    )
    
    return success_response(
        f"Successfully restocked {restock.qty} {part['uom']} of {part['name']}",
        {
            "new_stock": part["stock_qty"],
            "transaction": transaction
        }
    )

@router.get("/stats/summary")
async def get_parts_stats(authenticated: bool = Depends(verify_api_key)):
    """Get parts inventory statistics"""
    total = len(parts_data)
    total_value = sum(part["stock_qty"] * part["unit_cost"] for part in parts_data)
    low_stock_items = [part for part in parts_data if part["stock_qty"] <= part["min_qty"]]
    
    by_category = {}
    by_location = {}
    
    for part in parts_data:
        category = part["category"]
        location = part.get("location", "Unknown")
        
        if category not in by_category:
            by_category[category] = {"count": 0, "total_quantity": 0, "total_value": 0}
        
        by_category[category]["count"] += 1
        by_category[category]["total_quantity"] += part["stock_qty"]
        by_category[category]["total_value"] += part["stock_qty"] * part["unit_cost"]
        
        by_location[location] = by_location.get(location, 0) + 1
    
    return {
        "total_parts": total,
        "total_inventory_value": round(total_value, 2),
        "low_stock_items": len(low_stock_items),
        "low_stock_parts": [
            {
                "id": p["id"], 
                "name": p["name"], 
                "sku": p["sku"],
                "stock_qty": p["stock_qty"], 
                "min_qty": p["min_qty"]
            } for p in low_stock_items
        ],
        "by_category": by_category,
        "by_location": by_location
    }

@router.get("/alerts/low-stock")
async def get_low_stock_alerts(
    authenticated: bool = Depends(verify_api_key),):
    """Get low stock alerts"""
    low_stock_items = [part for part in parts_data if part["stock_qty"] <= part["min_qty"]]
    
    alerts = []
    for part in low_stock_items:
        alerts.append({
            "id": part["id"],
            "sku": part["sku"],
            "name": part["name"],
            "part_number": part.get("part_number"),
            "current_quantity": part["stock_qty"],
            "min_stock_level": part["min_qty"],
            "unit_cost": part["unit_cost"],
            "location": part.get("location"),
            "supplier_id": part.get("supplier_id"),
            "urgency": "Critical" if part["stock_qty"] == 0 else "Low"
        })
    
    # Sort by urgency (critical first, then by quantity)
    alerts.sort(key=lambda x: (x["urgency"] != "Critical", x["current_quantity"]))
    
    return {"alerts": alerts, "total_alerts": len(alerts)}

@router.get("/export.csv")
async def export_parts_csv(
    authenticated: bool = Depends(verify_api_key),
    category: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
    location: Optional[str] = Query(None)
):
    """Export parts as CSV"""
    filtered_parts = parts_data.copy()
    
    if category:
        filtered_parts = [part for part in filtered_parts if part["category"].lower() == category.lower()]
    if low_stock:
        filtered_parts = [part for part in filtered_parts if part["stock_qty"] <= part["min_qty"]]
    if location:
        filtered_parts = [part for part in filtered_parts if location.lower() in part.get("location", "").lower()]
    
    # Create DataFrame
    df = pd.DataFrame(filtered_parts)
    
    # Generate CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=parts_export.csv"}
    )