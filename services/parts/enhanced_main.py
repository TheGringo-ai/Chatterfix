#!/usr/bin/env python3
"""
ChatterFix Parts Service - Enhanced with Checkout, Inventory, Exports
Phase 7 - Complete parts management with inventory tracking and barcode support
"""

import os
import io
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal

import uvicorn
from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Parts Service - Enhanced",
    description="Enterprise parts management with inventory tracking, checkout, and barcode support",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
GCS_BUCKET = os.getenv("GCS_BUCKET", "chatterfix-attachments")
GCS_SIGNED_URL_TTL = int(os.getenv("GCS_SIGNED_URL_TTL", "900"))

# GCS client setup
try:
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(GCS_BUCKET)
except Exception as e:
    logger.warning(f"GCS not configured: {e}")
    gcs_client = None
    bucket = None

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

class PartFull(BaseModel):
    id: int
    sku: str
    part_number: Optional[str]
    name: str
    description: Optional[str]
    category: str
    uom: str
    stock_qty: int
    min_qty: int
    max_qty: Optional[int]
    location: Optional[str]
    bin_location: Optional[str]
    unit_cost: float
    last_cost: Optional[float]
    supplier_id: Optional[int]
    supplier_part_number: Optional[str]
    photo_uri: Optional[str]
    barcode: Optional[str]
    weight: Optional[float]
    dimensions: Optional[str]
    created_at: datetime
    updated_at: datetime
    attachments: List[Dict[str, Any]] = []
    recent_transactions: List[Dict[str, Any]] = []
    supplier_info: Optional[Dict[str, Any]] = None

# Enhanced sample data
sample_parts = [
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
        "sku": "GEN-FILTER-001",
        "part_number": "GEN-OF-001",
        "name": "Generator Oil Filter",
        "description": "Oil filter for backup generator maintenance",
        "category": "Power",
        "uom": "Each",
        "stock_qty": 8,
        "min_qty": 3,
        "max_qty": 20,
        "location": "Warehouse C-1",
        "bin_location": "C1-12-A",
        "unit_cost": 24.99,
        "last_cost": 23.75,
        "supplier_id": 1,
        "supplier_part_number": "GEN-OIL-FILT-001",
        "photo_uri": None,
        "barcode": "123456789004",
        "weight": 1.2,
        "dimensions": "4x4x3 inches",
        "created_at": "2023-08-25T10:00:00Z",
        "updated_at": "2025-08-25T13:20:00Z"
    },
    {
        "id": 1005,
        "sku": "PROD-BEARING-001",
        "part_number": "BRG-BALL-6205",
        "name": "Ball Bearing Assembly - 6205",
        "description": "Ball bearing assembly for conveyor and production equipment",
        "category": "Production",
        "uom": "Each",
        "stock_qty": 2,
        "min_qty": 5,
        "max_qty": 25,
        "location": "Warehouse B-1",
        "bin_location": "B1-20-B",
        "unit_cost": 45.99,
        "last_cost": 44.25,
        "supplier_id": 2,
        "supplier_part_number": "BW-6205-BALL",
        "photo_uri": None,
        "barcode": "123456789005",
        "weight": 0.8,
        "dimensions": "2x2x0.6 inches",
        "created_at": "2023-07-15T10:00:00Z",
        "updated_at": "2025-07-15T16:30:00Z"
    }
]

# Sample suppliers
sample_suppliers = [
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
    },
    {
        "id": 3,
        "name": "Safety First Supplies",
        "contact_person": "Mike Wilson",
        "email": "mike@safetyfirst.com",
        "phone": "555-0103",
        "address": "789 Safety Blvd, Secure City, SC 11111",
        "website": "https://safetyfirst.com",
        "payment_terms": "Net 15"
    }
]

# Sample inventory transactions
sample_transactions = {
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
        },
        {
            "id": 2,
            "part_id": 1001,
            "transaction_type": "OUT",
            "quantity": 1,
            "unit_cost": 34.99,
            "reference_type": "work_order",
            "reference_id": 1,
            "work_order_id": 1,
            "notes": "Used for WO-2025-001",
            "performed_by": "Tech User",
            "ts": "2025-10-18T09:15:00Z"
        }
    ],
    1003: [
        {
            "id": 3,
            "part_id": 1003,
            "transaction_type": "OUT",
            "quantity": 12,
            "unit_cost": 8.99,
            "reference_type": "work_order",
            "reference_id": 2,
            "work_order_id": 2,
            "notes": "Fire safety inspection - battery replacement",
            "performed_by": "Sarah Johnson",
            "ts": "2025-10-22T14:45:00Z"
        }
    ]
}

# Helper functions
async def generate_signed_upload_url(filename: str, content_type: str) -> Optional[Dict[str, str]]:
    """Generate signed URL for direct upload to GCS"""
    if not gcs_client or not bucket:
        return None
    
    try:
        blob_name = f"parts/{uuid.uuid4()}/{filename}"
        blob = bucket.blob(blob_name)
        
        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=GCS_SIGNED_URL_TTL),
            method="PUT",
            content_type=content_type
        )
        
        return {
            "upload_url": upload_url,
            "blob_name": blob_name,
            "gcs_uri": f"gs://{GCS_BUCKET}/{blob_name}"
        }
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        return None

def record_transaction(part_id: int, transaction_type: str, quantity: int, 
                      unit_cost: float = None, reference_type: str = None, 
                      reference_id: int = None, work_order_id: int = None,
                      notes: str = None, performed_by: str = "API User"):
    """Record an inventory transaction"""
    if part_id not in sample_transactions:
        sample_transactions[part_id] = []
    
    transaction = {
        "id": len(sample_transactions) * 10 + len(sample_transactions[part_id]) + 1,
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
    
    sample_transactions[part_id].append(transaction)
    return transaction

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gcs_status = "connected" if gcs_client else "disconnected"
    
    return {
        "status": "healthy",
        "service": "parts_enhanced",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "storage": gcs_status,
        "features": ["crud", "checkout", "inventory_tracking", "barcode", "exports"]
    }

@app.get("/parts", response_model=List[Dict[str, Any]])
async def get_parts(
    category: Optional[str] = Query(None, description="Filter by category"),
    low_stock: Optional[bool] = Query(None, description="Show only low stock items"),
    supplier: Optional[str] = Query(None, description="Filter by supplier"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search in name, sku, or part_number"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all parts with optional filtering"""
    filtered_parts = sample_parts.copy()
    
    if category:
        filtered_parts = [part for part in filtered_parts if part["category"].lower() == category.lower()]
    
    if low_stock:
        filtered_parts = [part for part in filtered_parts if part["stock_qty"] <= part["min_qty"]]
    
    if supplier:
        # Get supplier by name
        supplier_obj = next((s for s in sample_suppliers if supplier.lower() in s["name"].lower()), None)
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

@app.get("/parts/{part_id}", response_model=PartFull)
async def get_part(part_id: int):
    """Get detailed part with attachments and transaction history"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Enhance with related data
    result = part.copy()
    result["attachments"] = []  # TODO: Load from database/GCS
    result["recent_transactions"] = sample_transactions.get(part_id, [])[-20:]  # Last 20 transactions
    
    # Add supplier info
    if part.get("supplier_id"):
        supplier = next((s for s in sample_suppliers if s["id"] == part["supplier_id"]), None)
        result["supplier_info"] = supplier
    else:
        result["supplier_info"] = None
    
    return result

@app.post("/parts", response_model=Dict[str, Any])
async def create_part(part: PartCreate):
    """Create a new part"""
    new_id = max([p["id"] for p in sample_parts]) + 1 if sample_parts else 1
    
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
    
    sample_parts.append(new_part)
    
    # Record initial stock transaction if quantity > 0
    if part.stock_qty > 0:
        record_transaction(
            new_id, "IN", part.stock_qty, part.unit_cost,
            "initial_stock", None, None, "Initial inventory",
            "System"
        )
    
    return new_part

@app.put("/parts/{part_id}")
async def update_part(part_id: int, updates: PartUpdate):
    """Update part fields"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            part[field] = value
    
    part["updated_at"] = datetime.now().isoformat()
    
    return part

@app.post("/parts/{part_id}/checkout")
async def checkout_part(part_id: int, checkout: CheckoutRequest):
    """Checkout parts from inventory"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
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
    
    return {
        "message": f"Successfully checked out {checkout.qty} {part['uom']} of {part['name']}",
        "remaining_stock": part["stock_qty"],
        "transaction": transaction,
        "low_stock_warning": part["stock_qty"] <= part["min_qty"]
    }

@app.post("/parts/{part_id}/restock")
async def restock_part(part_id: int, restock: RestockRequest):
    """Restock parts inventory"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
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
    
    return {
        "message": f"Successfully restocked {restock.qty} {part['uom']} of {part['name']}",
        "new_stock": part["stock_qty"],
        "transaction": transaction
    }

@app.post("/parts/{part_id}/adjust")
async def adjust_inventory(part_id: int, adjustment: InventoryAdjustment):
    """Adjust part inventory (positive or negative)"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Check if adjustment would result in negative stock
    new_qty = part["stock_qty"] + adjustment.qty
    if new_qty < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Adjustment would result in negative stock. Current: {part['stock_qty']}, Adjustment: {adjustment.qty}"
        )
    
    # Update stock quantity
    part["stock_qty"] = new_qty
    part["updated_at"] = datetime.now().isoformat()
    
    # Record transaction
    transaction = record_transaction(
        part_id, "ADJUST", adjustment.qty, part["unit_cost"],
        "adjustment", None, None, 
        f"{adjustment.reason}: {adjustment.notes}" if adjustment.notes else adjustment.reason,
        "API User"
    )
    
    return {
        "message": f"Inventory adjusted by {adjustment.qty} {part['uom']}",
        "new_stock": part["stock_qty"],
        "transaction": transaction
    }

@app.get("/parts/{part_id}/transactions")
async def get_part_transactions(
    part_id: int,
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0)
):
    """Get transaction history for a part"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    transactions = sample_transactions.get(part_id, [])
    
    if transaction_type:
        transactions = [t for t in transactions if t["transaction_type"].lower() == transaction_type.lower()]
    
    # Sort by timestamp (newest first)
    transactions.sort(key=lambda x: x["ts"], reverse=True)
    
    # Apply pagination
    total = len(transactions)
    paginated = transactions[offset:offset + limit]
    
    return {
        "transactions": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.post("/parts/{part_id}/attachments/sign")
async def get_upload_signed_url(
    part_id: int,
    filename: str = Form(...),
    content_type: str = Form(...)
):
    """Get signed URL for direct upload to GCS"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    signed_data = await generate_signed_upload_url(filename, content_type)
    if not signed_data:
        raise HTTPException(status_code=503, detail="File upload service unavailable")
    
    return signed_data

@app.post("/parts/{part_id}/attachments")
async def upload_attachment(
    part_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    description: Optional[str] = Form(None)
):
    """Upload attachment (photo/document) for part"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Validate file
    if file.size > 25 * 1024 * 1024:  # 25MB limit for parts
        raise HTTPException(status_code=413, detail="File too large")
    
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="File type not allowed")
    
    # TODO: Upload to GCS and save metadata to database
    # For now, if it's an image and primary, update the part's photo_uri
    if is_primary and file.content_type.startswith("image/"):
        part["photo_uri"] = f"gs://{GCS_BUCKET}/parts/{part_id}/primary_{file.filename}"
    
    attachment = {
        "id": len(sample_parts) * 10 + 1,
        "filename": f"part_{part_id}_{file.filename}",
        "original_filename": file.filename,
        "mime_type": file.content_type,
        "file_size": file.size,
        "download_url": f"https://api.chatterfix.com/attachments/{part_id}/download",
        "uploaded_by": "API User",
        "ts": datetime.now().isoformat(),
        "is_primary": is_primary
    }
    
    return {"message": "File uploaded successfully", "attachment": attachment}

@app.get("/parts/{part_id}/export.pdf")
async def export_part_pdf(part_id: int):
    """Export part details as PDF label/report"""
    part = next((p for p in sample_parts if p["id"] == part_id), None)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"Part Report: {part['sku']}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Part details
    details_data = [
        ['Field', 'Value'],
        ['SKU', part['sku']],
        ['Part Number', part.get('part_number', 'N/A')],
        ['Name', part['name']],
        ['Category', part['category']],
        ['Location', part.get('location', 'N/A')],
        ['Bin Location', part.get('bin_location', 'N/A')],
        ['Stock Quantity', f"{part['stock_qty']} {part['uom']}"],
        ['Min Quantity', f"{part['min_qty']} {part['uom']}"],
        ['Unit Cost', f"${part['unit_cost']:.2f}"],
        ['Barcode', part.get('barcode', 'N/A')],
        ['Weight', f"{part.get('weight', 'N/A')} lbs" if part.get('weight') else 'N/A'],
        ['Dimensions', part.get('dimensions', 'N/A')],
        ['Description', part.get('description', 'N/A')]
    ]
    
    details_table = Table(details_data, colWidths=[120, 380])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 12))
    
    # Recent transactions
    transactions = sample_transactions.get(part_id, [])
    if transactions:
        story.append(Paragraph("Recent Transactions:", styles['Heading2']))
        trans_data = [['Date', 'Type', 'Qty', 'Reference', 'Performed By']]
        
        for trans in transactions[-10:]:  # Last 10 transactions
            trans_data.append([
                trans['ts'][:10],
                trans['transaction_type'],
                f"{trans['quantity']} {part['uom']}",
                trans.get('notes', 'N/A')[:30],
                trans['performed_by']
            ])
        
        trans_table = Table(trans_data, colWidths=[80, 60, 80, 150, 100])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(trans_table)
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=part_{part['sku']}_report.pdf"}
    )

@app.get("/parts/export.csv")
async def export_parts_csv(
    category: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
    location: Optional[str] = Query(None)
):
    """Export parts as CSV"""
    # Filter parts
    filtered_parts = sample_parts.copy()
    
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

@app.get("/parts/stats/summary")
async def get_parts_stats():
    """Get parts inventory statistics"""
    total = len(sample_parts)
    total_value = sum(part["stock_qty"] * part["unit_cost"] for part in sample_parts)
    low_stock_items = [part for part in sample_parts if part["stock_qty"] <= part["min_qty"]]
    
    by_category = {}
    by_location = {}
    
    for part in sample_parts:
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

@app.get("/parts/alerts/low-stock")
async def get_low_stock_alerts():
    """Get low stock alerts"""
    low_stock_items = [part for part in sample_parts if part["stock_qty"] <= part["min_qty"]]
    
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

@app.get("/suppliers")
async def get_suppliers():
    """Get list of suppliers"""
    return {"suppliers": sample_suppliers}

@app.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int):
    """Get supplier details"""
    supplier = next((s for s in sample_suppliers if s["id"] == supplier_id), None)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get parts supplied by this supplier
    supplier_parts = [part for part in sample_parts if part.get("supplier_id") == supplier_id]
    
    result = supplier.copy()
    result["parts_count"] = len(supplier_parts)
    result["parts"] = supplier_parts
    
    return result

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)