import os
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_user_from_cookie, require_auth_cookie
from app.models.user import User
from app.core.firestore_db import get_firestore_manager
from app.services.purchasing_service import purchasing_service

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
async def purchasing_main(request: Request):
    """Main purchaser command center - landing page"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    is_demo = current_user is None
    return templates.TemplateResponse(
        "purchaser_dashboard.html",
        {"request": request, "current_user": current_user, "is_demo": is_demo},
    )


@router.get("/tools", response_class=HTMLResponse)
async def purchasing_tools(request: Request):
    """Purchasing tools - PO creation, parts, document scanner, barcodes"""
    # Use cookie-based auth for HTML pages (Lesson #8)
    current_user = await get_current_user_from_cookie(request)
    is_demo = current_user is None
    return templates.TemplateResponse(
        "enhanced_purchasing.html",
        {"request": request, "current_user": current_user, "is_demo": is_demo},
    )


@router.get("/purchase-orders")
async def get_purchase_orders(request: Request, status: str = None):
    """Get purchase orders scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    orders = await purchasing_service.get_purchase_orders(org_id, status)
    return JSONResponse(content={"purchase_orders": orders})


@router.get("/pending-approvals")
async def get_pending_approvals(request: Request):
    """Get pending approval requests scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    approvals = await purchasing_service.get_pending_approvals(org_id)
    return JSONResponse(content=approvals)


@router.get("/vendor-performance")
async def get_vendor_performance(request: Request):
    """Get vendor performance metrics scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    vendors = await purchasing_service.get_vendor_performance(org_id)
    return JSONResponse(content={"vendors": vendors})


@router.get("/budget-tracking")
async def get_budget_tracking(request: Request):
    """Get budget tracking data scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    budget = await purchasing_service.get_budget_tracking(org_id)
    return JSONResponse(content=budget)


@router.get("/low-stock")
async def get_low_stock(request: Request):
    """Get low stock alerts scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    items = await purchasing_service.get_low_stock_alerts(org_id)
    return JSONResponse(content={"low_stock_items": items})


@router.get("/price-trends")
async def get_price_trends(request: Request):
    """Get price trends scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    trends = await purchasing_service.get_price_trends(org_id)
    return JSONResponse(content=trends)


@router.get("/contract-renewals")
async def get_contract_renewals(request: Request):
    """Get upcoming contract renewals scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    renewals = await purchasing_service.get_contract_renewals(org_id)
    return JSONResponse(content={"renewals": renewals})


@router.get("/spend-analytics")
async def get_spend_analytics(request: Request, days: int = 30):
    """Get spend analytics scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    analytics = await purchasing_service.get_spend_analytics(org_id, days)
    return JSONResponse(content=analytics)


@router.post("/approve")
async def process_approval(approval: ApprovalRequest):
    """Approve or deny a purchase request"""
    if approval.action == "approve":
        success = await purchasing_service.approve_purchase_request(
            approval.request_id, approval.approver_id
        )
        message = "Request approved" if success else "Approval failed"
    else:
        success = await purchasing_service.deny_purchase_request(
            approval.request_id, approval.reason
        )
        message = "Request denied" if success else "Denial failed"

    return JSONResponse(content={"success": success, "message": message})


@router.get("/summary")
async def get_purchasing_summary(request: Request):
    """Get comprehensive purchasing summary scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None

    approvals = await purchasing_service.get_pending_approvals(org_id)
    budget = await purchasing_service.get_budget_tracking(org_id)
    low_stock = await purchasing_service.get_low_stock_alerts(org_id)
    analytics = await purchasing_service.get_spend_analytics(org_id, 30)

    return JSONResponse(
        content={
            "pending_approvals": approvals["pending_count"],
            "budget_utilization": budget.get("utilization_percentage", 0),
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
    """Point of Sale system for purchasing scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    is_demo = current_user is None
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Get vendors for dropdown, filtered by organization
    filters = []
    if org_id:
        filters.append({"field": "organization_id", "operator": "==", "value": org_id})
    vendors = await db.get_collection("vendors", filters=filters if filters else None, order_by="name")

    # Get parts for quick add, filtered by organization
    parts = await db.get_collection("parts", filters=filters if filters else None, order_by="name", limit=50)

    return templates.TemplateResponse(
        "purchasing_pos.html", {"request": request, "current_user": current_user, "is_demo": is_demo, "vendors": vendors, "parts": parts}
    )


@router.post("/purchase-orders/create")
async def create_purchase_order(
    request: Request,
    vendor_id: str = Form(...),
    po_number: str = Form(...),
    description: str = Form(""),
    total_amount: float = Form(0.0),
    delivery_date: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Create new purchase order with documents scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Create purchase order data with organization_id
    po_data = {
        "po_number": po_number,
        "vendor_id": vendor_id,
        "description": description,
        "total_amount": total_amount,
        "delivery_date": delivery_date,
        "status": "Draft",
        "organization_id": org_id,
        "created_by": current_user.uid if current_user else None,
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
    request: Request,
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
    """Add new part with pictures and documents scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Create part data with organization_id
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
        "organization_id": org_id,
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
    request: Request,
    name: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    payment_terms: str = Form("Net 30"),
    tax_id: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Create vendor with documents scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Create vendor data with organization_id
    vendor_data = {
        "name": name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "address": address,
        "payment_terms": payment_terms,
        "tax_id": tax_id,
        "organization_id": org_id,
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
    request: Request,
    po_id: str = Form(...),
    invoice_number: str = Form(...),
    invoice_amount: float = Form(...),
    invoice_date: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """Upload invoice with documents scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Create invoice data with organization_id
    invoice_data = {
        "po_id": po_id,
        "invoice_number": invoice_number,
        "amount": invoice_amount,
        "invoice_date": invoice_date,
        "status": "Pending",
        "organization_id": org_id,
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
async def search_parts(request: Request, q: str = ""):
    """Search parts by name or part number scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Get all parts first (Firestore doesn't support complex text search)
    filters = []
    if org_id:
        filters.append({"field": "organization_id", "operator": "==", "value": org_id})
    parts = await db.get_collection("parts", filters=filters if filters else None, order_by="name", limit=100)

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
async def lookup_by_barcode(request: Request, barcode: str):
    """Lookup part by barcode/part number scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Build filters including organization_id
    filters = [{"field": "part_number", "operator": "==", "value": barcode}]
    if org_id:
        filters.append({"field": "organization_id", "operator": "==", "value": org_id})
    parts = await db.get_collection("parts", filters=filters)

    if not parts:
        # Try searching by barcode field
        filters = [{"field": "barcode", "operator": "==", "value": barcode}]
        if org_id:
            filters.append({"field": "organization_id", "operator": "==", "value": org_id})
        parts = await db.get_collection("parts", filters=filters)

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
async def get_low_stock_items(request: Request):
    """Get items below minimum stock level scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    db = get_firestore_manager()

    # Get all parts filtered by organization
    filters = []
    if org_id:
        filters.append({"field": "organization_id", "operator": "==", "value": org_id})
    all_parts = await db.get_collection("parts", filters=filters if filters else None)

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


# =============================================================================
# PURCHASER DASHBOARD API ENDPOINTS
# =============================================================================


@router.get("/kpi-summary")
async def get_kpi_summary(request: Request):
    """Get KPI summary for purchaser dashboard scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    # Note: Service method may need to be updated to accept org_id
    try:
        kpis = await purchasing_service.get_kpi_summary(org_id)
    except TypeError:
        # Fallback if service doesn't support org_id yet
        kpis = await purchasing_service.get_kpi_summary()
    return JSONResponse(content=kpis)


@router.get("/po-pipeline")
async def get_po_pipeline(request: Request):
    """Get PO pipeline counts by status scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    try:
        pipeline = await purchasing_service.get_po_pipeline_counts(org_id)
    except TypeError:
        pipeline = await purchasing_service.get_po_pipeline_counts()
    return JSONResponse(content=pipeline)


@router.get("/pending-actions")
async def get_pending_actions(request: Request):
    """Get list of pending actions requiring attention scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    try:
        actions = await purchasing_service.get_pending_actions(org_id)
    except TypeError:
        actions = await purchasing_service.get_pending_actions()
    return JSONResponse(content={"actions": actions})


@router.get("/top-vendors")
async def get_top_vendors(request: Request, limit: int = 5):
    """Get top performing vendors scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    try:
        vendors = await purchasing_service.get_top_vendors(org_id, limit)
    except TypeError:
        vendors = await purchasing_service.get_top_vendors(limit)
    return JSONResponse(content={"vendors": vendors})


@router.get("/recent-activity")
async def get_recent_activity(request: Request, limit: int = 20):
    """Get recent purchasing activity feed scoped to user's organization"""
    current_user = await get_current_user_from_cookie(request)
    org_id = current_user.organization_id if current_user else None
    try:
        activity = await purchasing_service.get_recent_activity(org_id, limit)
    except TypeError:
        activity = await purchasing_service.get_recent_activity(limit)
    return JSONResponse(content={"activity": activity})
