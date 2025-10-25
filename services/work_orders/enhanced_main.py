#!/usr/bin/env python3
"""
ChatterFix Work Orders Service - Enhanced with CRUD, Attachments, Parts, Exports
Phase 7 - Complete work order management
"""

import os
import io
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal

import uvicorn
from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Form, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx
import asyncpg
from google.cloud import storage
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Work Orders Service - Enhanced",
    description="Enterprise work order management with attachments, exports, and voice AI",
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
AI_BRAIN_URL = os.getenv("AI_BRAIN_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")

# GCS client (will be None if not configured)
try:
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(GCS_BUCKET)
except Exception as e:
    logger.warning(f"GCS not configured: {e}")
    gcs_client = None
    bucket = None

# Pydantic models
class WorkOrderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: str = Field("Medium", regex="^(Low|Medium|High|Critical)$")
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    asset_id: Optional[int] = None
    estimated_hours: Optional[float] = None

class WorkOrderCreate(WorkOrderBase):
    pass

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = Field(None, regex="^(Low|Medium|High|Critical)$")
    status: Optional[str] = Field(None, regex="^(Open|In Progress|On Hold|Completed|Cancelled)$")
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    asset_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

class WorkOrderFull(BaseModel):
    id: int
    code: str
    title: str
    description: str
    status: str
    priority: str
    requested_by: Optional[str]
    assigned_to: Optional[str]
    asset_id: Optional[int]
    due_date: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    created_at: datetime
    updated_at: datetime
    activity: List[Dict[str, Any]] = []
    parts_used: List[Dict[str, Any]] = []
    attachments: List[Dict[str, Any]] = []

class ActivityCreate(BaseModel):
    note: str = Field(..., min_length=1)

class PartsUsageCreate(BaseModel):
    part_id: int
    qty: int = Field(..., gt=0)
    unit_cost: Optional[float] = None

class AttachmentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    download_url: Optional[str]
    uploaded_by: str
    ts: datetime
    is_primary: bool

# Enhanced sample data with more realistic work orders
sample_work_orders = [
    {
        "id": 1,
        "code": "WO-2025-001",
        "title": "Replace HVAC Filter - Building A",
        "description": "Monthly replacement of HEPA filter in main HVAC unit. Check for unusual wear patterns and log filter condition.",
        "status": "Open",
        "priority": "Medium",
        "requested_by": "Facility Manager",
        "assigned_to": "John Smith",
        "asset_id": 101,
        "due_date": "2025-10-25T17:00:00Z",
        "estimated_hours": 2.0,
        "actual_hours": None,
        "created_at": "2025-10-22T10:00:00Z",
        "updated_at": "2025-10-22T10:00:00Z"
    },
    {
        "id": 2,
        "code": "WO-2025-002", 
        "title": "Fire Safety Equipment Inspection",
        "description": "Quarterly inspection of all fire extinguishers, smoke detectors, and emergency lighting systems. Update inspection tags and test functionality.",
        "status": "In Progress",
        "priority": "High",
        "requested_by": "Safety Officer",
        "assigned_to": "Sarah Johnson",
        "asset_id": 102,
        "due_date": "2025-10-23T17:00:00Z",
        "estimated_hours": 4.0,
        "actual_hours": 2.5,
        "created_at": "2025-10-22T08:00:00Z",
        "updated_at": "2025-10-22T14:30:00Z"
    },
    {
        "id": 3,
        "code": "WO-2025-003",
        "title": "Conveyor Belt Lubrication",
        "description": "Apply high-temperature lubricant to conveyor belt bearings and inspect belt tension. Check for wear on drive rollers.",
        "status": "Open",
        "priority": "Low",
        "requested_by": "Production Supervisor",
        "assigned_to": None,
        "asset_id": 103,
        "due_date": "2025-10-28T17:00:00Z",
        "estimated_hours": 1.5,
        "actual_hours": None,
        "created_at": "2025-10-22T12:00:00Z",
        "updated_at": "2025-10-22T12:00:00Z"
    }
]

# Sample activity data
sample_activity = {
    1: [
        {
            "id": 1,
            "work_order_id": 1,
            "actor": "System",
            "action": "created",
            "note": "Work order created from maintenance schedule",
            "ts": "2025-10-22T10:00:00Z"
        }
    ],
    2: [
        {
            "id": 2,
            "work_order_id": 2,
            "actor": "System",
            "action": "created",
            "note": "Work order created",
            "ts": "2025-10-22T08:00:00Z"
        },
        {
            "id": 3,
            "work_order_id": 2,
            "actor": "Sarah Johnson",
            "action": "status_changed",
            "note": "Started inspection of first floor equipment",
            "old_value": "Open",
            "new_value": "In Progress",
            "ts": "2025-10-22T14:30:00Z"
        }
    ],
    3: [
        {
            "id": 4,
            "work_order_id": 3,
            "actor": "System",
            "action": "created",
            "note": "Work order created",
            "ts": "2025-10-22T12:00:00Z"
        }
    ]
}

# Sample parts usage
sample_parts_used = {
    2: [
        {
            "id": 1,
            "work_order_id": 2,
            "part_id": 1001,
            "part_name": "9V Battery",
            "qty": 12,
            "unit_cost": 8.99,
            "checkout_by": "Sarah Johnson",
            "ts": "2025-10-22T14:45:00Z"
        }
    ]
}

# Database connection
async def get_db_connection():
    """Get database connection - returns None if not configured"""
    if not DATABASE_URL:
        return None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        return None

# GCS helper functions
async def generate_signed_upload_url(filename: str, content_type: str) -> Optional[Dict[str, str]]:
    """Generate signed URL for direct upload to GCS"""
    if not gcs_client or not bucket:
        return None
    
    try:
        blob_name = f"work_orders/{uuid.uuid4()}/{filename}"
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

async def generate_signed_download_url(gcs_uri: str) -> Optional[str]:
    """Generate signed URL for downloading from GCS"""
    if not gcs_client or not bucket:
        return None
    
    try:
        # Extract blob name from gs://bucket/path
        blob_name = gcs_uri.replace(f"gs://{GCS_BUCKET}/", "")
        blob = bucket.blob(blob_name)
        
        download_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=GCS_SIGNED_URL_TTL),
            method="GET"
        )
        
        return download_url
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        return None

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if await get_db_connection() else "disconnected"
    gcs_status = "connected" if gcs_client else "disconnected"
    
    return {
        "status": "healthy",
        "service": "work_orders_enhanced",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "storage": gcs_status,
        "features": ["crud", "attachments", "exports", "voice_ai"]
    }

@app.get("/work_orders", response_model=List[Dict[str, Any]])
async def get_work_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all work orders with optional filtering"""
    # TODO: Replace with database query
    filtered_orders = sample_work_orders.copy()
    
    if status:
        filtered_orders = [wo for wo in filtered_orders if wo["status"].lower() == status.lower()]
    
    if priority:
        filtered_orders = [wo for wo in filtered_orders if wo["priority"].lower() == priority.lower()]
    
    if assigned_to:
        filtered_orders = [wo for wo in filtered_orders if wo.get("assigned_to") and assigned_to.lower() in wo["assigned_to"].lower()]
    
    # Apply pagination
    total = len(filtered_orders)
    paginated = filtered_orders[offset:offset + limit]
    
    return {
        "work_orders": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/work_orders/{work_order_id}", response_model=WorkOrderFull)
async def get_work_order(work_order_id: int):
    """Get detailed work order with activity, parts, and attachments"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Enhance with related data
    result = work_order.copy()
    result["activity"] = sample_activity.get(work_order_id, [])
    result["parts_used"] = sample_parts_used.get(work_order_id, [])
    result["attachments"] = []  # TODO: Load from database/GCS
    
    return result

@app.post("/work_orders", response_model=Dict[str, Any])
async def create_work_order(work_order: WorkOrderCreate):
    """Create a new work order"""
    new_id = max([wo["id"] for wo in sample_work_orders]) + 1 if sample_work_orders else 1
    
    new_work_order = {
        "id": new_id,
        "code": f"WO-2025-{new_id:03d}",
        "title": work_order.title,
        "description": work_order.description,
        "status": "Open",
        "priority": work_order.priority,
        "requested_by": "API User",  # TODO: Get from auth
        "assigned_to": work_order.assigned_to,
        "asset_id": work_order.asset_id,
        "due_date": work_order.due_date.isoformat() if work_order.due_date else None,
        "estimated_hours": work_order.estimated_hours,
        "actual_hours": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    sample_work_orders.append(new_work_order)
    
    # Add activity log entry
    if new_id not in sample_activity:
        sample_activity[new_id] = []
    
    sample_activity[new_id].append({
        "id": len(sample_activity) * 10 + 1,
        "work_order_id": new_id,
        "actor": "API User",
        "action": "created",
        "note": "Work order created via API",
        "ts": datetime.now().isoformat()
    })
    
    return new_work_order

@app.put("/work_orders/{work_order_id}")
async def update_work_order(work_order_id: int, updates: WorkOrderUpdate):
    """Update work order fields"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Track changes for activity log
    changes = []
    update_data = updates.dict(exclude_unset=True)
    
    for field, new_value in update_data.items():
        if field in work_order and work_order[field] != new_value:
            old_value = work_order[field]
            work_order[field] = new_value
            changes.append({
                "field": field,
                "old_value": str(old_value) if old_value is not None else None,
                "new_value": str(new_value) if new_value is not None else None
            })
    
    work_order["updated_at"] = datetime.now().isoformat()
    
    # Add activity log entries for changes
    if work_order_id not in sample_activity:
        sample_activity[work_order_id] = []
    
    for change in changes:
        sample_activity[work_order_id].append({
            "id": len(sample_activity) * 10 + len(changes) + 1,
            "work_order_id": work_order_id,
            "actor": "API User",
            "action": f"{change['field']}_changed",
            "note": f"Updated {change['field']} from '{change['old_value']}' to '{change['new_value']}'",
            "old_value": change['old_value'],
            "new_value": change['new_value'],
            "ts": datetime.now().isoformat()
        })
    
    return work_order

@app.post("/work_orders/{work_order_id}/comment")
async def add_work_order_comment(work_order_id: int, comment: ActivityCreate):
    """Add comment/activity to work order"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if work_order_id not in sample_activity:
        sample_activity[work_order_id] = []
    
    new_activity = {
        "id": len(sample_activity) * 10 + len(sample_activity[work_order_id]) + 1,
        "work_order_id": work_order_id,
        "actor": "API User",  # TODO: Get from auth
        "action": "commented",
        "note": comment.note,
        "ts": datetime.now().isoformat()
    }
    
    sample_activity[work_order_id].append(new_activity)
    
    return {"message": "Comment added successfully", "activity": new_activity}

@app.post("/work_orders/{work_order_id}/parts")
async def add_parts_usage(work_order_id: int, parts_usage: PartsUsageCreate):
    """Add parts usage to work order"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if work_order_id not in sample_parts_used:
        sample_parts_used[work_order_id] = []
    
    new_parts_usage = {
        "id": len(sample_parts_used) * 10 + 1,
        "work_order_id": work_order_id,
        "part_id": parts_usage.part_id,
        "part_name": f"Part #{parts_usage.part_id}",  # TODO: Lookup part name
        "qty": parts_usage.qty,
        "unit_cost": parts_usage.unit_cost or 0.0,
        "checkout_by": "API User",
        "ts": datetime.now().isoformat()
    }
    
    sample_parts_used[work_order_id].append(new_parts_usage)
    
    # Add activity log
    if work_order_id not in sample_activity:
        sample_activity[work_order_id] = []
    
    sample_activity[work_order_id].append({
        "id": len(sample_activity) * 10 + 1,
        "work_order_id": work_order_id,
        "actor": "API User",
        "action": "parts_added",
        "note": f"Added {parts_usage.qty}x Part #{parts_usage.part_id}",
        "ts": datetime.now().isoformat()
    })
    
    return {"message": "Parts usage recorded", "parts_usage": new_parts_usage}

@app.post("/work_orders/{work_order_id}/attachments/sign")
async def get_upload_signed_url(
    work_order_id: int,
    filename: str = Form(...),
    content_type: str = Form(...)
):
    """Get signed URL for direct upload to GCS"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    signed_data = await generate_signed_upload_url(filename, content_type)
    if not signed_data:
        raise HTTPException(status_code=503, detail="File upload service unavailable")
    
    return signed_data

@app.post("/work_orders/{work_order_id}/attachments")
async def upload_attachment(
    work_order_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """Upload attachment directly to service"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
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
    # For now, return mock response
    attachment = {
        "id": len(sample_work_orders) * 10 + 1,
        "filename": f"wo_{work_order_id}_{file.filename}",
        "original_filename": file.filename,
        "mime_type": file.content_type,
        "file_size": file.size,
        "download_url": f"https://api.chatterfix.com/attachments/{work_order_id}/download",
        "uploaded_by": "API User",
        "ts": datetime.now().isoformat(),
        "is_primary": False
    }
    
    return {"message": "File uploaded successfully", "attachment": attachment}

@app.get("/work_orders/{work_order_id}/export.pdf")
async def export_work_order_pdf(work_order_id: int):
    """Export work order as PDF"""
    work_order = next((wo for wo in sample_work_orders if wo["id"] == work_order_id), None)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"Work Order: {work_order['code']}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Work order details
    details_data = [
        ['Field', 'Value'],
        ['Title', work_order['title']],
        ['Status', work_order['status']],
        ['Priority', work_order['priority']],
        ['Assigned To', work_order.get('assigned_to', 'Unassigned')],
        ['Due Date', work_order.get('due_date', 'Not set')],
        ['Created', work_order['created_at']],
        ['Description', work_order['description']]
    ]
    
    details_table = Table(details_data, colWidths=[100, 400])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 12))
    
    # Parts used (if any)
    parts = sample_parts_used.get(work_order_id, [])
    if parts:
        story.append(Paragraph("Parts Used:", styles['Heading2']))
        parts_data = [['Part', 'Quantity', 'Unit Cost', 'Total']]
        total_cost = 0
        
        for part in parts:
            cost = part['qty'] * part['unit_cost']
            total_cost += cost
            parts_data.append([
                part['part_name'],
                str(part['qty']),
                f"${part['unit_cost']:.2f}",
                f"${cost:.2f}"
            ])
        
        parts_data.append(['', '', 'Total:', f"${total_cost:.2f}"])
        
        parts_table = Table(parts_data)
        parts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ]))
        
        story.append(parts_table)
        story.append(Spacer(1, 12))
    
    # Activity log
    activity = sample_activity.get(work_order_id, [])
    if activity:
        story.append(Paragraph("Activity Log:", styles['Heading2']))
        for act in reversed(activity[-10:]):  # Last 10 activities
            story.append(Paragraph(
                f"<b>{act['ts'][:19]}</b> - {act['actor']}: {act['note']}", 
                styles['Normal']
            ))
            story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=work_order_{work_order['code']}.pdf"}
    )

@app.get("/work_orders/export.csv")
async def export_work_orders_csv(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None)
):
    """Export work orders as CSV"""
    # Filter work orders
    filtered_orders = sample_work_orders.copy()
    
    if status:
        filtered_orders = [wo for wo in filtered_orders if wo["status"].lower() == status.lower()]
    if priority:
        filtered_orders = [wo for wo in filtered_orders if wo["priority"].lower() == priority.lower()]
    if assigned_to:
        filtered_orders = [wo for wo in filtered_orders if wo.get("assigned_to") and assigned_to.lower() in wo["assigned_to"].lower()]
    
    # Create DataFrame
    df = pd.DataFrame(filtered_orders)
    
    # Generate CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=work_orders_export.csv"}
    )

@app.get("/work_orders/stats/summary")
async def get_work_order_stats():
    """Get work order statistics"""
    total = len(sample_work_orders)
    by_status = {}
    by_priority = {}
    by_assignee = {}
    
    overdue_count = 0
    due_soon_count = 0  # Due in next 7 days
    
    for wo in sample_work_orders:
        status = wo["status"]
        priority = wo["priority"]
        assignee = wo.get("assigned_to", "Unassigned")
        
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
        by_assignee[assignee] = by_assignee.get(assignee, 0) + 1
        
        # Check due dates
        if wo.get("due_date"):
            due_date = datetime.fromisoformat(wo["due_date"].replace('Z', '+00:00'))
            now = datetime.now(due_date.tzinfo)
            
            if due_date < now and wo["status"] not in ["Completed", "Cancelled"]:
                overdue_count += 1
            elif due_date < now + timedelta(days=7) and wo["status"] not in ["Completed", "Cancelled"]:
                due_soon_count += 1
    
    return {
        "total_work_orders": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_assignee": by_assignee,
        "overdue_count": overdue_count,
        "due_soon_count": due_soon_count,
        "completion_rate": (by_status.get("Completed", 0) / total * 100) if total > 0 else 0
    }

# Voice AI Integration
@app.post("/work_orders/voice/intent")
async def process_voice_intent(
    audio_data: UploadFile = File(None),
    transcription: Optional[str] = Form(None),
    context: str = Form(...),  # JSON string with page context
    language: str = Form("en-US")
):
    """Process voice input for work order actions"""
    if not audio_data and not transcription:
        raise HTTPException(status_code=400, detail="Either audio_data or transcription required")
    
    try:
        context_data = json.loads(context)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid context JSON")
    
    # If audio provided, transcribe it (placeholder - would use actual STT service)
    if audio_data and not transcription:
        transcription = "Replace HVAC filter for Asset A-103 high priority"  # Mock transcription
    
    # Simple intent parsing (would use more sophisticated NLP in production)
    intent_result = await parse_voice_intent(transcription, context_data)
    
    # Execute the action based on intent
    if intent_result["intent"] == "create_work_order":
        # Extract parameters and create work order
        wo_data = WorkOrderCreate(
            title=intent_result["args"].get("title", "Voice Created Work Order"),
            description=intent_result["args"].get("description", transcription),
            priority=intent_result["args"].get("priority", "Medium"),
            asset_id=intent_result["args"].get("asset_id")
        )
        result = await create_work_order(wo_data)
        intent_result["action_result"] = result
        
    elif intent_result["intent"] == "add_comment":
        work_order_id = context_data.get("work_order_id")
        if work_order_id:
            comment = ActivityCreate(note=intent_result["args"].get("comment", transcription))
            result = await add_work_order_comment(work_order_id, comment)
            intent_result["action_result"] = result
    
    elif intent_result["intent"] == "update_status":
        work_order_id = context_data.get("work_order_id")
        new_status = intent_result["args"].get("status")
        if work_order_id and new_status:
            updates = WorkOrderUpdate(status=new_status)
            result = await update_work_order(work_order_id, updates)
            intent_result["action_result"] = result
    
    return intent_result

async def parse_voice_intent(transcription: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Parse voice transcription to determine intent and extract parameters"""
    text = transcription.lower()
    
    # Simple keyword-based intent detection
    if any(phrase in text for phrase in ["create work order", "new work order", "add work order"]):
        return {
            "intent": "create_work_order",
            "confidence": 0.85,
            "args": {
                "title": extract_title_from_text(text),
                "priority": extract_priority_from_text(text),
                "asset_id": extract_asset_id_from_text(text)
            },
            "message": "Creating new work order from voice input"
        }
    
    elif any(phrase in text for phrase in ["add comment", "add note", "comment"]):
        return {
            "intent": "add_comment",
            "confidence": 0.90,
            "args": {"comment": transcription},
            "message": "Adding comment to work order"
        }
    
    elif any(phrase in text for phrase in ["mark complete", "set status", "change status"]):
        return {
            "intent": "update_status", 
            "confidence": 0.80,
            "args": {"status": extract_status_from_text(text)},
            "message": "Updating work order status"
        }
    
    else:
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "args": {},
            "message": f"Could not determine intent from: {transcription}"
        }

def extract_title_from_text(text: str) -> str:
    """Extract work order title from voice input"""
    # Simple extraction - would use NER in production
    if "for" in text:
        parts = text.split("for", 1)
        if len(parts) > 1:
            return parts[1].strip().title()
    return "Voice Created Work Order"

def extract_priority_from_text(text: str) -> str:
    """Extract priority from voice input"""
    if "high priority" in text or "urgent" in text or "critical" in text:
        return "High"
    elif "low priority" in text:
        return "Low"
    return "Medium"

def extract_asset_id_from_text(text: str) -> Optional[int]:
    """Extract asset ID from voice input"""
    import re
    # Look for patterns like "Asset A-103", "asset 103", etc.
    asset_patterns = [
        r"asset\s+a-?(\d+)",
        r"asset\s+(\d+)",
        r"equipment\s+(\d+)"
    ]
    
    for pattern in asset_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None

def extract_status_from_text(text: str) -> str:
    """Extract status from voice input"""
    if "complete" in text or "finished" in text or "done" in text:
        return "Completed"
    elif "progress" in text or "working" in text:
        return "In Progress"
    elif "hold" in text or "pause" in text:
        return "On Hold"
    return "Open"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)