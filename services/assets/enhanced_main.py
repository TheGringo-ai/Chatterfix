#!/usr/bin/env python3
"""
ChatterFix Assets Service - Enhanced with CRUD, Attachments, Exports
Phase 7 - Complete asset management with photo galleries and maintenance tracking
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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Assets Service - Enhanced",
    description="Enterprise asset management with photo galleries, maintenance tracking, and exports",
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
class AssetBase(BaseModel):
    asset_code: str = Field(..., max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    criticality: str = Field("Medium", regex="^(Low|Medium|High|Critical)$")
    installation_date: Optional[datetime] = None
    replacement_cost: Optional[float] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    status: Optional[str] = Field(None, regex="^(Active|Inactive|Maintenance|Retired)$")
    criticality: Optional[str] = Field(None, regex="^(Low|Medium|High|Critical)$")
    installation_date: Optional[datetime] = None
    replacement_cost: Optional[float] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None

class AssetFull(BaseModel):
    id: int
    asset_code: str
    name: str
    description: Optional[str]
    asset_type: Optional[str]
    location: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    purchase_date: Optional[datetime]
    warranty_expiry: Optional[datetime]
    status: str
    criticality: str
    installation_date: Optional[datetime]
    last_maintenance: Optional[datetime]
    next_maintenance: Optional[datetime]
    replacement_cost: Optional[float]
    created_at: datetime
    updated_at: datetime
    attachments: List[Dict[str, Any]] = []
    recent_work_orders: List[Dict[str, Any]] = []
    maintenance_schedules: List[Dict[str, Any]] = []

# Enhanced sample data
sample_assets = [
    {
        "id": 101,
        "asset_code": "HVAC-001",
        "name": "Main HVAC Unit - Building A",
        "description": "Primary heating, ventilation, and air conditioning system for Building A",
        "asset_type": "HVAC",
        "location": "Building A - Roof",
        "manufacturer": "Carrier",
        "model": "50TCQ12",
        "serial_number": "CAR50TCQ12-2023-001",
        "purchase_date": "2023-01-15T00:00:00Z",
        "warranty_expiry": "2026-01-15T00:00:00Z",
        "status": "Active",
        "criticality": "High",
        "installation_date": "2023-02-01T00:00:00Z",
        "last_maintenance": "2025-09-15T00:00:00Z",
        "next_maintenance": "2025-12-15T00:00:00Z",
        "replacement_cost": 45000.00,
        "created_at": "2023-01-15T10:00:00Z",
        "updated_at": "2025-09-15T14:30:00Z"
    },
    {
        "id": 102,
        "asset_code": "FIRE-001",
        "name": "Fire Safety Panel - Main Building",
        "description": "Central fire detection and alarm system",
        "asset_type": "Safety",
        "location": "Building A - Lobby",
        "manufacturer": "Honeywell",
        "model": "FS90",
        "serial_number": "HON-FS90-2022-156",
        "purchase_date": "2022-06-10T00:00:00Z",
        "warranty_expiry": "2025-06-10T00:00:00Z",
        "status": "Active",
        "criticality": "Critical",
        "installation_date": "2022-07-01T00:00:00Z",
        "last_maintenance": "2025-09-01T00:00:00Z",
        "next_maintenance": "2025-12-01T00:00:00Z",
        "replacement_cost": 8500.00,
        "created_at": "2022-06-10T10:00:00Z",
        "updated_at": "2025-09-01T09:15:00Z"
    },
    {
        "id": 103,
        "asset_code": "CONV-001",
        "name": "Production Conveyor Belt System",
        "description": "Main production line conveyor belt system",
        "asset_type": "Production",
        "location": "Factory Floor - Line 1",
        "manufacturer": "Dorner",
        "model": "2200 Series",
        "serial_number": "DOR-2200-2021-089",
        "purchase_date": "2021-03-20T00:00:00Z",
        "warranty_expiry": "2024-03-20T00:00:00Z",
        "status": "Active",
        "criticality": "High",
        "installation_date": "2021-04-15T00:00:00Z",
        "last_maintenance": "2025-10-01T00:00:00Z",
        "next_maintenance": "2025-11-01T00:00:00Z",
        "replacement_cost": 25000.00,
        "created_at": "2021-03-20T10:00:00Z",
        "updated_at": "2025-10-01T16:45:00Z"
    },
    {
        "id": 104,
        "asset_code": "GEN-001",
        "name": "Backup Generator - Building A",
        "description": "Emergency backup power generator",
        "asset_type": "Power",
        "location": "Building A - Generator Room",
        "manufacturer": "Generac",
        "model": "RG027",
        "serial_number": "GEN-RG027-2020-043",
        "purchase_date": "2020-08-12T00:00:00Z",
        "warranty_expiry": "2023-08-12T00:00:00Z",
        "status": "Standby",
        "criticality": "Critical",
        "installation_date": "2020-09-15T00:00:00Z",
        "last_maintenance": "2025-08-12T00:00:00Z",
        "next_maintenance": "2026-02-12T00:00:00Z",
        "replacement_cost": 18000.00,
        "created_at": "2020-08-12T10:00:00Z",
        "updated_at": "2025-08-12T11:20:00Z"
    }
]

# Sample maintenance schedules
sample_maintenance_schedules = {
    101: [
        {
            "id": 1,
            "asset_id": 101,
            "title": "Filter Replacement",
            "description": "Replace HEPA filters in HVAC system",
            "frequency_type": "Monthly",
            "frequency_value": 1,
            "last_completed": "2025-10-01",
            "next_due": "2025-11-01",
            "estimated_hours": 2.0,
            "assigned_to": "John Smith",
            "priority": "Medium",
            "is_active": True
        },
        {
            "id": 2,
            "asset_id": 101,
            "title": "Quarterly Inspection",
            "description": "Complete system inspection and performance check",
            "frequency_type": "Quarterly",
            "frequency_value": 3,
            "last_completed": "2025-09-15",
            "next_due": "2025-12-15",
            "estimated_hours": 8.0,
            "assigned_to": "Sarah Johnson",
            "priority": "High",
            "is_active": True
        }
    ],
    102: [
        {
            "id": 3,
            "asset_id": 102,
            "title": "Battery Test",
            "description": "Test backup battery and replace if needed",
            "frequency_type": "Monthly",
            "frequency_value": 1,
            "last_completed": "2025-10-01",
            "next_due": "2025-11-01",
            "estimated_hours": 1.0,
            "assigned_to": "Mike Wilson",
            "priority": "High",
            "is_active": True
        }
    ]
}

# Sample recent work orders for assets
sample_asset_work_orders = {
    101: [
        {
            "id": 1,
            "code": "WO-2025-001",
            "title": "Replace HVAC Filter",
            "status": "Open",
            "priority": "Medium",
            "assigned_to": "John Smith",
            "created_at": "2025-10-22T10:00:00Z",
            "due_date": "2025-10-25T17:00:00Z"
        }
    ],
    102: [
        {
            "id": 2,
            "code": "WO-2025-002",
            "title": "Fire Safety Equipment Inspection",
            "status": "In Progress",
            "priority": "High",
            "assigned_to": "Sarah Johnson",
            "created_at": "2025-10-22T08:00:00Z",
            "due_date": "2025-10-23T17:00:00Z"
        }
    ]
}

# Helper functions
async def generate_signed_upload_url(filename: str, content_type: str) -> Optional[Dict[str, str]]:
    """Generate signed URL for direct upload to GCS"""
    if not gcs_client or not bucket:
        return None
    
    try:
        blob_name = f"assets/{uuid.uuid4()}/{filename}"
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

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gcs_status = "connected" if gcs_client else "disconnected"
    
    return {
        "status": "healthy",
        "service": "assets_enhanced",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "storage": gcs_status,
        "features": ["crud", "attachments", "exports", "maintenance_tracking"]
    }

@app.get("/assets", response_model=List[Dict[str, Any]])
async def get_assets(
    status: Optional[str] = Query(None, description="Filter by status"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all assets with optional filtering"""
    filtered_assets = sample_assets.copy()
    
    if status:
        filtered_assets = [asset for asset in filtered_assets if asset["status"].lower() == status.lower()]
    
    if asset_type:
        filtered_assets = [asset for asset in filtered_assets if asset.get("asset_type", "").lower() == asset_type.lower()]
    
    if location:
        filtered_assets = [asset for asset in filtered_assets if location.lower() in asset.get("location", "").lower()]
    
    if criticality:
        filtered_assets = [asset for asset in filtered_assets if asset["criticality"].lower() == criticality.lower()]
    
    # Apply pagination
    total = len(filtered_assets)
    paginated = filtered_assets[offset:offset + limit]
    
    return {
        "assets": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/assets/{asset_id}", response_model=AssetFull)
async def get_asset(asset_id: int):
    """Get detailed asset with attachments, work orders, and maintenance schedules"""
    asset = next((a for a in sample_assets if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Enhance with related data
    result = asset.copy()
    result["attachments"] = []  # TODO: Load from database/GCS
    result["recent_work_orders"] = sample_asset_work_orders.get(asset_id, [])
    result["maintenance_schedules"] = sample_maintenance_schedules.get(asset_id, [])
    
    return result

@app.post("/assets", response_model=Dict[str, Any])
async def create_asset(asset: AssetCreate):
    """Create a new asset"""
    new_id = max([a["id"] for a in sample_assets]) + 1 if sample_assets else 1
    
    new_asset = {
        "id": new_id,
        "asset_code": asset.asset_code,
        "name": asset.name,
        "description": asset.description,
        "asset_type": asset.asset_type,
        "location": asset.location,
        "manufacturer": asset.manufacturer,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
        "warranty_expiry": asset.warranty_expiry.isoformat() if asset.warranty_expiry else None,
        "status": "Active",
        "criticality": asset.criticality,
        "installation_date": asset.installation_date.isoformat() if asset.installation_date else None,
        "last_maintenance": None,
        "next_maintenance": None,
        "replacement_cost": asset.replacement_cost,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    sample_assets.append(new_asset)
    return new_asset

@app.put("/assets/{asset_id}")
async def update_asset(asset_id: int, updates: AssetUpdate):
    """Update asset fields"""
    asset = next((a for a in sample_assets if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if isinstance(value, datetime):
                asset[field] = value.isoformat()
            else:
                asset[field] = value
    
    asset["updated_at"] = datetime.now().isoformat()
    
    return asset

@app.post("/assets/{asset_id}/attachments/sign")
async def get_upload_signed_url(
    asset_id: int,
    filename: str = Form(...),
    content_type: str = Form(...)
):
    """Get signed URL for direct upload to GCS"""
    asset = next((a for a in sample_assets if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    signed_data = await generate_signed_upload_url(filename, content_type)
    if not signed_data:
        raise HTTPException(status_code=503, detail="File upload service unavailable")
    
    return signed_data

@app.post("/assets/{asset_id}/attachments")
async def upload_attachment(
    asset_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    description: Optional[str] = Form(None)
):
    """Upload attachment directly to service"""
    asset = next((a for a in sample_assets if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Validate file
    if file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File too large")
    
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="File type not allowed")
    
    # TODO: Upload to GCS and save metadata to database
    attachment = {
        "id": len(sample_assets) * 10 + 1,
        "filename": f"asset_{asset_id}_{file.filename}",
        "original_filename": file.filename,
        "mime_type": file.content_type,
        "file_size": file.size,
        "download_url": f"https://api.chatterfix.com/attachments/{asset_id}/download",
        "uploaded_by": "API User",
        "ts": datetime.now().isoformat(),
        "is_primary": is_primary
    }
    
    return {"message": "File uploaded successfully", "attachment": attachment}

@app.post("/assets/{asset_id}/work-order")
async def create_work_order_for_asset(
    asset_id: int,
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form("Medium"),
    assigned_to: Optional[str] = Form(None),
    due_date: Optional[datetime] = Form(None)
):
    """Create a work order for this asset"""
    asset = next((a for a in sample_assets if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # TODO: Call work orders service to create the work order
    work_order_data = {
        "title": title,
        "description": description,
        "priority": priority,
        "assigned_to": assigned_to,
        "due_date": due_date.isoformat() if due_date else None,
        "asset_id": asset_id
    }
    
    # Mock work order creation response
    new_work_order = {
        "id": len(sample_asset_work_orders) + 100,
        "code": f"WO-2025-{len(sample_asset_work_orders) + 100:03d}",
        "title": title,
        "status": "Open",
        "priority": priority,
        "assigned_to": assigned_to,
        "asset_id": asset_id,
        "created_at": datetime.now().isoformat(),
        "due_date": due_date.isoformat() if due_date else None
    }
    
    # Add to sample data
    if asset_id not in sample_asset_work_orders:
        sample_asset_work_orders[asset_id] = []
    sample_asset_work_orders[asset_id].append(new_work_order)
    
    return {"message": "Work order created successfully", "work_order": new_work_order}

@app.get("/assets/{asset_id}/export.pdf")
async def export_asset_pdf(asset_id: int):
    """Export asset details as PDF"""
    asset = next((a for a in sample_assets if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"Asset Report: {asset['asset_code']}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Asset details
    details_data = [
        ['Field', 'Value'],
        ['Asset Code', asset['asset_code']],
        ['Name', asset['name']],
        ['Type', asset.get('asset_type', 'N/A')],
        ['Location', asset.get('location', 'N/A')],
        ['Manufacturer', asset.get('manufacturer', 'N/A')],
        ['Model', asset.get('model', 'N/A')],
        ['Serial Number', asset.get('serial_number', 'N/A')],
        ['Status', asset['status']],
        ['Criticality', asset['criticality']],
        ['Purchase Date', asset.get('purchase_date', 'N/A')],
        ['Warranty Expiry', asset.get('warranty_expiry', 'N/A')],
        ['Last Maintenance', asset.get('last_maintenance', 'N/A')],
        ['Next Maintenance', asset.get('next_maintenance', 'N/A')],
        ['Replacement Cost', f"${asset.get('replacement_cost', 0):,.2f}" if asset.get('replacement_cost') else 'N/A'],
        ['Description', asset.get('description', 'N/A')]
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
    
    # Recent work orders
    work_orders = sample_asset_work_orders.get(asset_id, [])
    if work_orders:
        story.append(Paragraph("Recent Work Orders:", styles['Heading2']))
        wo_data = [['Code', 'Title', 'Status', 'Priority', 'Assigned To', 'Due Date']]
        
        for wo in work_orders[-10:]:  # Last 10 work orders
            wo_data.append([
                wo['code'],
                wo['title'][:30] + '...' if len(wo['title']) > 30 else wo['title'],
                wo['status'],
                wo['priority'],
                wo.get('assigned_to', 'Unassigned'),
                wo.get('due_date', 'N/A')[:10] if wo.get('due_date') else 'N/A'
            ])
        
        wo_table = Table(wo_data, colWidths=[80, 150, 70, 60, 80, 80])
        wo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(wo_table)
        story.append(Spacer(1, 12))
    
    # Maintenance schedules
    schedules = sample_maintenance_schedules.get(asset_id, [])
    if schedules:
        story.append(Paragraph("Maintenance Schedules:", styles['Heading2']))
        for schedule in schedules:
            if schedule['is_active']:
                story.append(Paragraph(
                    f"<b>{schedule['title']}</b> - {schedule['frequency_type']}: {schedule['description']}<br/>"
                    f"Next Due: {schedule['next_due']} | Assigned: {schedule['assigned_to']}", 
                    styles['Normal']
                ))
                story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=asset_{asset['asset_code']}_report.pdf"}
    )

@app.get("/assets/export.csv")
async def export_assets_csv(
    status: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None)
):
    """Export assets as CSV"""
    # Filter assets
    filtered_assets = sample_assets.copy()
    
    if status:
        filtered_assets = [asset for asset in filtered_assets if asset["status"].lower() == status.lower()]
    if asset_type:
        filtered_assets = [asset for asset in filtered_assets if asset.get("asset_type", "").lower() == asset_type.lower()]
    if location:
        filtered_assets = [asset for asset in filtered_assets if location.lower() in asset.get("location", "").lower()]
    if criticality:
        filtered_assets = [asset for asset in filtered_assets if asset["criticality"].lower() == criticality.lower()]
    
    # Create DataFrame
    df = pd.DataFrame(filtered_assets)
    
    # Generate CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assets_export.csv"}
    )

@app.get("/assets/stats/summary")
async def get_asset_stats():
    """Get asset statistics"""
    total = len(sample_assets)
    by_status = {}
    by_type = {}
    by_criticality = {}
    by_location = {}
    
    warranty_expiring_count = 0  # Expiring in next 90 days
    maintenance_due_count = 0    # Maintenance due in next 30 days
    
    for asset in sample_assets:
        status = asset["status"]
        asset_type = asset.get("asset_type", "Unknown")
        criticality = asset["criticality"]
        location = asset.get("location", "Unknown")
        
        by_status[status] = by_status.get(status, 0) + 1
        by_type[asset_type] = by_type.get(asset_type, 0) + 1
        by_criticality[criticality] = by_criticality.get(criticality, 0) + 1
        by_location[location] = by_location.get(location, 0) + 1
        
        # Check warranty expiry
        if asset.get("warranty_expiry"):
            warranty_date = datetime.fromisoformat(asset["warranty_expiry"].replace('Z', '+00:00'))
            if warranty_date < datetime.now(warranty_date.tzinfo) + timedelta(days=90):
                warranty_expiring_count += 1
        
        # Check maintenance due
        if asset.get("next_maintenance"):
            maintenance_date = datetime.fromisoformat(asset["next_maintenance"].replace('Z', '+00:00'))
            if maintenance_date < datetime.now(maintenance_date.tzinfo) + timedelta(days=30):
                maintenance_due_count += 1
    
    total_value = sum(asset.get("replacement_cost", 0) for asset in sample_assets)
    
    return {
        "total_assets": total,
        "by_status": by_status,
        "by_type": by_type,
        "by_criticality": by_criticality,
        "by_location": by_location,
        "warranty_expiring_count": warranty_expiring_count,
        "maintenance_due_count": maintenance_due_count,
        "total_replacement_value": total_value
    }

@app.get("/assets/maintenance/upcoming")
async def get_upcoming_maintenance():
    """Get assets with upcoming maintenance"""
    upcoming = []
    
    for asset in sample_assets:
        if asset.get("next_maintenance"):
            maintenance_date = datetime.fromisoformat(asset["next_maintenance"].replace('Z', '+00:00'))
            days_until = (maintenance_date - datetime.now(maintenance_date.tzinfo)).days
            
            if days_until <= 30:  # Due in next 30 days
                upcoming.append({
                    "asset_id": asset["id"],
                    "asset_code": asset["asset_code"],
                    "asset_name": asset["name"],
                    "next_maintenance": asset["next_maintenance"],
                    "days_until": days_until,
                    "criticality": asset["criticality"],
                    "location": asset.get("location", "Unknown")
                })
    
    # Sort by days until maintenance
    upcoming.sort(key=lambda x: x["days_until"])
    
    return {"upcoming_maintenance": upcoming}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)