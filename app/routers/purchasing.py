from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import shutil
import os
from datetime import datetime

from app.services.purchasing_service import purchasing_service
from app.core.database import get_db_connection

router = APIRouter(prefix="/purchasing", tags=["purchasing"])
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directories exist
PO_UPLOAD_DIR = "app/static/uploads/purchase_orders"
VENDOR_UPLOAD_DIR = "app/static/uploads/vendors"
INVOICE_UPLOAD_DIR = "app/static/uploads/invoices"
os.makedirs(PO_UPLOAD_DIR, exist_ok=True)
os.makedirs(VENDOR_UPLOAD_DIR, exist_ok=True)
os.makedirs(INVOICE_UPLOAD_DIR, exist_ok=True)


class ApprovalRequest(BaseModel):
    request_id: int
    approver_id: int
    action: str  # 'approve' or 'deny'
    reason: str = None


@router.get("/", response_class=HTMLResponse)
async def purchasing_dashboard(request: Request):
    """Enhanced purchasing dashboard with media and barcode capabilities"""
    return templates.TemplateResponse("enhanced_purchasing.html", {"request": request})


@router.get("/purchase-orders")
async def get_purchase_orders(status: str = None):
    """Get purchase orders"""
    orders = purchasing_service.get_purchase_orders(status)
    return JSONResponse(content={"purchase_orders": orders})


@router.get("/pending-approvals")
async def get_pending_approvals():
    """Get pending approval requests"""
    approvals = purchasing_service.get_pending_approvals()
    return JSONResponse(content=approvals)


@router.get("/vendor-performance")
async def get_vendor_performance():
    """Get vendor performance metrics"""
    vendors = purchasing_service.get_vendor_performance()
    return JSONResponse(content={"vendors": vendors})


@router.get("/budget-tracking")
async def get_budget_tracking():
    """Get budget tracking data"""
    budget = purchasing_service.get_budget_tracking()
    return JSONResponse(content=budget)


@router.get("/low-stock")
async def get_low_stock():
    """Get low stock alerts"""
    items = purchasing_service.get_low_stock_alerts()
    return JSONResponse(content={"low_stock_items": items})


@router.get("/price-trends")
async def get_price_trends():
    """Get price trends"""
    trends = purchasing_service.get_price_trends()
    return JSONResponse(content=trends)


@router.get("/contract-renewals")
async def get_contract_renewals():
    """Get upcoming contract renewals"""
    renewals = purchasing_service.get_contract_renewals()
    return JSONResponse(content={"renewals": renewals})


@router.get("/spend-analytics")
async def get_spend_analytics(days: int = 30):
    """Get spend analytics"""
    analytics = purchasing_service.get_spend_analytics(days)
    return JSONResponse(content=analytics)


@router.post("/approve")
async def process_approval(approval: ApprovalRequest):
    """Approve or deny a purchase request"""
    if approval.action == "approve":
        success = purchasing_service.approve_purchase_request(
            approval.request_id, approval.approver_id
        )
        message = "Request approved" if success else "Approval failed"
    else:
        success = purchasing_service.deny_purchase_request(
            approval.request_id, approval.reason
        )
        message = "Request denied" if success else "Denial failed"

    return JSONResponse(content={"success": success, "message": message})


@router.get("/summary")
async def get_purchasing_summary():
    """Get comprehensive purchasing summary"""
    approvals = purchasing_service.get_pending_approvals()
    budget = purchasing_service.get_budget_tracking()
    low_stock = purchasing_service.get_low_stock_alerts()
    analytics = purchasing_service.get_spend_analytics(30)

    return JSONResponse(
        content={
            "pending_approvals": approvals["pending_count"],
            "budget_utilization": budget["utilization_percentage"],
            "low_stock_count": len(low_stock),
            "monthly_spend": budget["total_spent"],
            "total_requests": analytics["total_requests"],
        }
    )


# =============================================================================
# COMPREHENSIVE POS & PARTS MANAGEMENT SYSTEM
# =============================================================================

@router.get("/pos", response_class=HTMLResponse)
async def pos_system(request: Request):
    """Point of Sale system for purchasing"""
    conn = get_db_connection()
    
    # Get vendors for dropdown
    vendors = conn.execute(
        "SELECT * FROM vendors ORDER BY name"
    ).fetchall()
    
    # Get parts for quick add
    parts = conn.execute(
        "SELECT id, name, part_number, unit_cost, current_stock FROM parts ORDER BY name"
    ).fetchall()
    
    conn.close()
    return templates.TemplateResponse(
        "purchasing_pos.html", 
        {
            "request": request, 
            "vendors": vendors,
            "parts": parts
        }
    )

@router.post("/purchase-orders/create")
async def create_purchase_order(
    vendor_id: int = Form(...),
    po_number: str = Form(...),
    description: str = Form(""),
    total_amount: float = Form(0.0),
    delivery_date: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Create new purchase order with documents"""
    conn = get_db_connection()
    
    # Create purchase order
    cursor = conn.execute(
        """INSERT INTO purchase_orders 
           (po_number, vendor_id, description, total_amount, delivery_date, status, created_date)
           VALUES (?, ?, ?, ?, ?, 'Draft', ?)""",
        (po_number, vendor_id, description, total_amount, delivery_date, datetime.now())
    )
    po_id = cursor.lastrowid
    
    # Handle file uploads
    if files:
        po_dir = os.path.join(PO_UPLOAD_DIR, str(po_id))
        os.makedirs(po_dir, exist_ok=True)
        
        for file in files:
            if file.filename:
                file_path = os.path.join(po_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                rel_path = f"/static/uploads/purchase_orders/{po_id}/{file.filename}"
                file_type = (
                    "image" if file.content_type and file.content_type.startswith("image/") 
                    else "document"
                )
                
                conn.execute(
                    """INSERT INTO po_documents (po_id, file_path, file_type, filename, description)
                       VALUES (?, ?, ?, ?, ?)""",
                    (po_id, rel_path, file_type, file.filename, "Uploaded during creation")
                )
    
    conn.commit()
    conn.close()
    return JSONResponse({"success": True, "po_id": po_id, "message": "Purchase order created successfully"})

@router.post("/parts/add")
async def add_part_with_media(
    name: str = Form(...),
    part_number: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    vendor_id: Optional[int] = Form(None),
    unit_cost: float = Form(0.0),
    current_stock: int = Form(0),
    minimum_stock: int = Form(5),
    location: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Add new part with pictures and documents"""
    conn = get_db_connection()
    
    # Create part
    cursor = conn.execute(
        """INSERT INTO parts 
           (name, part_number, description, category, vendor_id, unit_cost, 
            current_stock, minimum_stock, location)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, part_number, description, category, vendor_id, unit_cost, 
         current_stock, minimum_stock, location)
    )
    part_id = cursor.lastrowid
    
    # Handle file uploads
    if files:
        part_dir = os.path.join("app/static/uploads/parts", str(part_id))
        os.makedirs(part_dir, exist_ok=True)
        
        for file in files:
            if file.filename:
                file_path = os.path.join(part_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                rel_path = f"/static/uploads/parts/{part_id}/{file.filename}"
                file_type = (
                    "image" if file.content_type and file.content_type.startswith("image/") 
                    else "document"
                )
                
                # Update part image if it's the first image
                if file_type == "image":
                    existing_image = conn.execute(
                        "SELECT image_url FROM parts WHERE id = ?", (part_id,)
                    ).fetchone()
                    if not existing_image[0]:
                        conn.execute(
                            "UPDATE parts SET image_url = ? WHERE id = ?",
                            (rel_path, part_id)
                        )
                
                conn.execute(
                    """INSERT INTO part_media (part_id, file_path, file_type, title, description)
                       VALUES (?, ?, ?, ?, ?)""",
                    (part_id, rel_path, file_type, file.filename, "Uploaded during creation")
                )
    
    conn.commit()
    conn.close()
    return JSONResponse({"success": True, "part_id": part_id, "message": "Part added successfully"})

@router.post("/vendors/create")
async def create_vendor(
    name: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    payment_terms: str = Form("Net 30"),
    tax_id: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Create vendor with documents"""
    conn = get_db_connection()
    
    # Create vendor
    cursor = conn.execute(
        """INSERT INTO vendors 
           (name, contact_name, email, phone, address, payment_terms, tax_id, created_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, contact_name, email, phone, address, payment_terms, tax_id, datetime.now())
    )
    vendor_id = cursor.lastrowid
    
    # Handle file uploads
    if files:
        vendor_dir = os.path.join(VENDOR_UPLOAD_DIR, str(vendor_id))
        os.makedirs(vendor_dir, exist_ok=True)
        
        for file in files:
            if file.filename:
                file_path = os.path.join(vendor_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                rel_path = f"/static/uploads/vendors/{vendor_id}/{file.filename}"
                file_type = "document"  # Vendor files are typically documents
                
                conn.execute(
                    """INSERT INTO vendor_documents (vendor_id, file_path, file_type, filename, description)
                       VALUES (?, ?, ?, ?, ?)""",
                    (vendor_id, rel_path, file_type, file.filename, "Uploaded during creation")
                )
    
    conn.commit()
    conn.close()
    return JSONResponse({"success": True, "vendor_id": vendor_id, "message": "Vendor created successfully"})

@router.post("/invoices/upload")
async def upload_invoice(
    po_id: int = Form(...),
    invoice_number: str = Form(...),
    invoice_amount: float = Form(...),
    invoice_date: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """Upload invoice with documents"""
    conn = get_db_connection()
    
    # Create invoice record
    cursor = conn.execute(
        """INSERT INTO invoices 
           (po_id, invoice_number, amount, invoice_date, status, created_date)
           VALUES (?, ?, ?, ?, 'Pending', ?)""",
        (po_id, invoice_number, invoice_amount, invoice_date, datetime.now())
    )
    invoice_id = cursor.lastrowid
    
    # Handle file uploads
    invoice_dir = os.path.join(INVOICE_UPLOAD_DIR, str(invoice_id))
    os.makedirs(invoice_dir, exist_ok=True)
    
    for file in files:
        if file.filename:
            file_path = os.path.join(invoice_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            rel_path = f"/static/uploads/invoices/{invoice_id}/{file.filename}"
            file_type = (
                "image" if file.content_type and file.content_type.startswith("image/") 
                else "document"
            )
            
            conn.execute(
                """INSERT INTO invoice_documents (invoice_id, file_path, file_type, filename, description)
                   VALUES (?, ?, ?, ?, ?)""",
                (invoice_id, rel_path, file_type, file.filename, "Invoice document")
            )
    
    conn.commit()
    conn.close()
    return JSONResponse({"success": True, "invoice_id": invoice_id, "message": "Invoice uploaded successfully"})

@router.get("/parts/search")
async def search_parts(q: str = ""):
    """Search parts by name or part number"""
    conn = get_db_connection()
    
    if q:
        parts = conn.execute(
            """SELECT p.*, v.name as vendor_name 
               FROM parts p 
               LEFT JOIN vendors v ON p.vendor_id = v.id
               WHERE p.name LIKE ? OR p.part_number LIKE ?
               ORDER BY p.name LIMIT 50""",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        parts = conn.execute(
            """SELECT p.*, v.name as vendor_name 
               FROM parts p 
               LEFT JOIN vendors v ON p.vendor_id = v.id
               ORDER BY p.name LIMIT 50"""
        ).fetchall()
    
    conn.close()
    return JSONResponse({
        "parts": [dict(row) for row in parts]
    })

@router.get("/barcode/{barcode}")
async def lookup_by_barcode(barcode: str):
    """Lookup part by barcode/part number"""
    conn = get_db_connection()
    
    part = conn.execute(
        """SELECT p.*, v.name as vendor_name 
           FROM parts p 
           LEFT JOIN vendors v ON p.vendor_id = v.id
           WHERE p.part_number = ? OR p.barcode = ?""",
        (barcode, barcode)
    ).fetchone()
    
    conn.close()
    
    if part:
        return JSONResponse({"success": True, "part": dict(part)})
    else:
        return JSONResponse({"success": False, "message": "Part not found"})

@router.get("/inventory/low-stock")
async def get_low_stock_items():
    """Get items below minimum stock level"""
    conn = get_db_connection()
    
    items = conn.execute(
        """SELECT p.*, v.name as vendor_name 
           FROM parts p 
           LEFT JOIN vendors v ON p.vendor_id = v.id
           WHERE p.current_stock <= p.minimum_stock
           ORDER BY (p.current_stock - p.minimum_stock) ASC"""
    ).fetchall()
    
    conn.close()
    return JSONResponse({
        "low_stock_items": [dict(row) for row in items]
    })
