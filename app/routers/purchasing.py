from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import shutil
import os

from app.services.purchasing_service import purchasing_service
from app.core.firestore_db import get_firestore_manager

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
    db = get_firestore_manager()

    # Get vendors for dropdown
    vendors = await db.get_collection("vendors", order_by="name")

    # Get parts for quick add
    parts = await db.get_collection("parts", order_by="name", limit=50)

    return templates.TemplateResponse(
        "purchasing_pos.html", {"request": request, "vendors": vendors, "parts": parts}
    )


@router.post("/purchase-orders/create")
async def create_purchase_order(
    vendor_id: str = Form(...),
    po_number: str = Form(...),
    description: str = Form(""),
    total_amount: float = Form(0.0),
    delivery_date: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Create new purchase order with documents"""
    db = get_firestore_manager()

    # Create purchase order data
    po_data = {
        "po_number": po_number,
        "vendor_id": vendor_id,
        "description": description,
        "total_amount": total_amount,
        "delivery_date": delivery_date,
        "status": "Draft",
    }

    # Create purchase order
    po_id = await db.create_document("purchase_orders", po_data)

    # Handle file uploads
    if files:
        po_dir = os.path.join(PO_UPLOAD_DIR, po_id)
        os.makedirs(po_dir, exist_ok=True)

        for file in files:
            if file.filename:
                file_path = os.path.join(po_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                rel_path = f"/static/uploads/purchase_orders/{po_id}/{file.filename}"
                file_type = (
                    "image"
                    if file.content_type and file.content_type.startswith("image/")
                    else "document"
                )

                doc_data = {
                    "po_id": po_id,
                    "file_path": rel_path,
                    "file_type": file_type,
                    "filename": file.filename,
                    "description": "Uploaded during creation",
                }
                await db.create_document("po_documents", doc_data)

    return JSONResponse(
        {
            "success": True,
            "po_id": po_id,
            "message": "Purchase order created successfully",
        }
    )


@router.post("/parts/add")
async def add_part_with_media(
    name: str = Form(...),
    part_number: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    vendor_id: Optional[str] = Form(None),
    unit_cost: float = Form(0.0),
    current_stock: int = Form(0),
    minimum_stock: int = Form(5),
    location: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Add new part with pictures and documents"""
    db = get_firestore_manager()

    # Create part data
    part_data = {
        "name": name,
        "part_number": part_number,
        "description": description,
        "category": category,
        "vendor_id": vendor_id,
        "unit_cost": unit_cost,
        "current_stock": current_stock,
        "minimum_stock": minimum_stock,
        "location": location,
        "image_url": "",
    }

    # Create part
    part_id = await db.create_document("parts", part_data)

    # Handle file uploads
    if files:
        part_dir = os.path.join("app/static/uploads/parts", part_id)
        os.makedirs(part_dir, exist_ok=True)

        first_image = True
        for file in files:
            if file.filename:
                file_path = os.path.join(part_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                rel_path = f"/static/uploads/parts/{part_id}/{file.filename}"
                file_type = (
                    "image"
                    if file.content_type and file.content_type.startswith("image/")
                    else "document"
                )

                # Update part image if it's the first image
                if file_type == "image" and first_image:
                    await db.update_document("parts", part_id, {"image_url": rel_path})
                    first_image = False

                # Create document record
                doc_data = {
                    "part_id": part_id,
                    "file_path": rel_path,
                    "file_type": file_type,
                    "title": file.filename,
                    "description": "Uploaded during creation",
                }
                await db.create_document("part_media", doc_data)

    return JSONResponse(
        {"success": True, "part_id": part_id, "message": "Part added successfully"}
    )


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
    db = get_firestore_manager()

    # Create vendor data
    vendor_data = {
        "name": name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "address": address,
        "payment_terms": payment_terms,
        "tax_id": tax_id,
    }

    # Create vendor
    vendor_id = await db.create_document("vendors", vendor_data)

    # Handle file uploads
    if files:
        vendor_dir = os.path.join(VENDOR_UPLOAD_DIR, vendor_id)
        os.makedirs(vendor_dir, exist_ok=True)

        for file in files:
            if file.filename:
                file_path = os.path.join(vendor_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                rel_path = f"/static/uploads/vendors/{vendor_id}/{file.filename}"
                file_type = "document"  # Vendor files are typically documents

                doc_data = {
                    "vendor_id": vendor_id,
                    "file_path": rel_path,
                    "file_type": file_type,
                    "filename": file.filename,
                    "description": "Uploaded during creation",
                }
                await db.create_document("vendor_documents", doc_data)

    return JSONResponse(
        {
            "success": True,
            "vendor_id": vendor_id,
            "message": "Vendor created successfully",
        }
    )


@router.post("/invoices/upload")
async def upload_invoice(
    po_id: str = Form(...),
    invoice_number: str = Form(...),
    invoice_amount: float = Form(...),
    invoice_date: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """Upload invoice with documents"""
    db = get_firestore_manager()

    # Create invoice data
    invoice_data = {
        "po_id": po_id,
        "invoice_number": invoice_number,
        "amount": invoice_amount,
        "invoice_date": invoice_date,
        "status": "Pending",
    }

    # Create invoice record
    invoice_id = await db.create_document("invoices", invoice_data)

    # Handle file uploads
    invoice_dir = os.path.join(INVOICE_UPLOAD_DIR, invoice_id)
    os.makedirs(invoice_dir, exist_ok=True)

    for file in files:
        if file.filename:
            file_path = os.path.join(invoice_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            rel_path = f"/static/uploads/invoices/{invoice_id}/{file.filename}"
            file_type = (
                "image"
                if file.content_type and file.content_type.startswith("image/")
                else "document"
            )

            doc_data = {
                "invoice_id": invoice_id,
                "file_path": rel_path,
                "file_type": file_type,
                "filename": file.filename,
                "description": "Invoice document",
            }
            await db.create_document("invoice_documents", doc_data)

    return JSONResponse(
        {
            "success": True,
            "invoice_id": invoice_id,
            "message": "Invoice uploaded successfully",
        }
    )


@router.get("/parts/search")
async def search_parts(q: str = ""):
    """Search parts by name or part number"""
    db = get_firestore_manager()

    # Get all parts first (Firestore doesn't support complex text search)
    parts = await db.get_collection("parts", order_by="name", limit=100)

    # Filter by search query if provided
    if q:
        q_lower = q.lower()
        parts = [
            part
            for part in parts
            if q_lower in part.get("name", "").lower()
            or q_lower in part.get("part_number", "").lower()
        ]

    # Get vendor names for each part
    for part in parts:
        if part.get("vendor_id"):
            vendor = await db.get_document("vendors", part["vendor_id"])
            part["vendor_name"] = vendor.get("name", "") if vendor else ""
        else:
            part["vendor_name"] = ""

    return JSONResponse({"parts": parts[:50]})  # Limit to 50 results


@router.get("/barcode/{barcode}")
async def lookup_by_barcode(barcode: str):
    """Lookup part by barcode/part number"""
    db = get_firestore_manager()

    # Search by part number or barcode
    parts = await db.get_collection(
        "parts", filters=[{"field": "part_number", "operator": "==", "value": barcode}]
    )

    if not parts:
        # Try searching by barcode field
        parts = await db.get_collection(
            "parts", filters=[{"field": "barcode", "operator": "==", "value": barcode}]
        )

    if parts:
        part = parts[0]
        # Get vendor name if vendor_id exists
        if part.get("vendor_id"):
            vendor = await db.get_document("vendors", part["vendor_id"])
            part["vendor_name"] = vendor.get("name", "") if vendor else ""
        else:
            part["vendor_name"] = ""

        return JSONResponse({"success": True, "part": part})
    else:
        return JSONResponse({"success": False, "message": "Part not found"})


@router.get("/inventory/low-stock")
async def get_low_stock_items():
    """Get items below minimum stock level"""
    db = get_firestore_manager()

    # Get all parts (Firestore doesn't support complex filtering)
    all_parts = await db.get_collection("parts")

    # Filter for low stock items
    low_stock_items = [
        part
        for part in all_parts
        if part.get("current_stock", 0) <= part.get("minimum_stock", 0)
    ]

    # Get vendor names and sort by stock difference
    for part in low_stock_items:
        if part.get("vendor_id"):
            vendor = await db.get_document("vendors", part["vendor_id"])
            part["vendor_name"] = vendor.get("name", "") if vendor else ""
        else:
            part["vendor_name"] = ""

    # Sort by stock difference (most critical first)
    low_stock_items.sort(
        key=lambda x: x.get("current_stock", 0) - x.get("minimum_stock", 0)
    )

    return JSONResponse({"low_stock_items": low_stock_items})
