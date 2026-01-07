import csv
import io
import os
import shutil
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    JSONResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates

# Try to import pandas for Excel support
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

from app.auth import (
    get_current_active_user,
    require_permission,
    require_permission_cookie,
    require_auth_cookie,
    get_current_user_from_cookie,
)
from app.models.user import User
from app.core.firestore_db import get_firestore_manager
from app.services.audit_log_service import log_part_checkout, AuditAction, audit_log_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads/parts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Comprehensive demo inventory data - looks like a real maintenance operation
DEMO_PARTS = [
    {
        "id": "part-001",
        "name": "Hydraulic Filter Element",
        "part_number": "HF-2045-A",
        "category": "Filters",
        "description": "High-efficiency hydraulic filter for industrial pumps",
        "current_stock": 24,
        "minimum_stock": 10,
        "location": "Warehouse A - Shelf 12",
        "unit_cost": 45.99,
        "vendor_name": "FluidPro Supply",
        "image_url": "",
    },
    {
        "id": "part-002",
        "name": "SKF Ball Bearing 6205-2RS",
        "part_number": "SKF-6205-2RS",
        "category": "Bearings",
        "description": "Deep groove ball bearing, sealed, 25x52x15mm",
        "current_stock": 48,
        "minimum_stock": 20,
        "location": "Warehouse A - Shelf 5",
        "unit_cost": 12.75,
        "vendor_name": "BearingWorld Inc",
        "image_url": "",
    },
    {
        "id": "part-003",
        "name": "V-Belt A68",
        "part_number": "VB-A68-IND",
        "category": "Belts & Drives",
        "description": "Industrial V-belt, 68 inch, heavy duty",
        "current_stock": 15,
        "minimum_stock": 8,
        "location": "Warehouse B - Rack 3",
        "unit_cost": 28.50,
        "vendor_name": "PowerTrans Supply",
        "image_url": "",
    },
    {
        "id": "part-004",
        "name": "Mechanical Seal Kit",
        "part_number": "MSK-150-SS",
        "category": "Seals & Gaskets",
        "description": "Stainless steel mechanical seal kit for centrifugal pumps",
        "current_stock": 6,
        "minimum_stock": 4,
        "location": "Warehouse A - Shelf 8",
        "unit_cost": 189.00,
        "vendor_name": "SealTech Industries",
        "image_url": "",
    },
    {
        "id": "part-005",
        "name": "Contactor 3-Pole 40A",
        "part_number": "LC1D40-240V",
        "category": "Electrical",
        "description": "3-pole contactor, 40 amp, 240V coil",
        "current_stock": 8,
        "minimum_stock": 3,
        "location": "Electrical Room - Cabinet 2",
        "unit_cost": 67.50,
        "vendor_name": "ElectroParts Direct",
        "image_url": "",
    },
    {
        "id": "part-006",
        "name": "Lubricant - Shell Omala S4",
        "part_number": "SHELL-OMALA-S4-5G",
        "category": "Lubricants",
        "description": "Synthetic gear oil, 5 gallon pail, ISO 220",
        "current_stock": 12,
        "minimum_stock": 4,
        "location": "Lubrication Storage",
        "unit_cost": 245.00,
        "vendor_name": "Shell Industrial",
        "image_url": "",
    },
    {
        "id": "part-007",
        "name": "Proximity Sensor",
        "part_number": "PS-M18-NPN",
        "category": "Sensors",
        "description": "Inductive proximity sensor, M18, NPN, 8mm range",
        "current_stock": 3,
        "minimum_stock": 5,
        "location": "Electrical Room - Cabinet 4",
        "unit_cost": 42.00,
        "vendor_name": "AutoSense Corp",
        "status": "low_stock",
        "image_url": "",
    },
    {
        "id": "part-008",
        "name": "Conveyor Roller",
        "part_number": "CR-48-HD",
        "category": "Conveyor Parts",
        "description": "Heavy duty conveyor roller, 48 inch width",
        "current_stock": 18,
        "minimum_stock": 6,
        "location": "Warehouse B - Floor Storage",
        "unit_cost": 125.00,
        "vendor_name": "ConveyorParts Plus",
        "image_url": "",
    },
    {
        "id": "part-009",
        "name": "Air Filter Element",
        "part_number": "AF-24X24X2-MERV13",
        "category": "HVAC Filters",
        "description": "HVAC air filter, 24x24x2, MERV 13 rating",
        "current_stock": 36,
        "minimum_stock": 24,
        "location": "HVAC Storage Room",
        "unit_cost": 18.99,
        "vendor_name": "AirQuality Supply",
        "image_url": "",
    },
    {
        "id": "part-010",
        "name": "Pressure Gauge 0-300 PSI",
        "part_number": "PG-300-SS",
        "category": "Instrumentation",
        "description": "Stainless steel pressure gauge, 0-300 PSI, 2.5 inch dial",
        "current_stock": 7,
        "minimum_stock": 4,
        "location": "Instrument Cabinet",
        "unit_cost": 35.00,
        "vendor_name": "InstruTech Supply",
        "image_url": "",
    },
]

DEMO_VENDORS = [
    {
        "id": "vendor-001",
        "name": "FluidPro Supply",
        "contact_name": "John Martinez",
        "email": "orders@fluidpro.com",
        "phone": "(555) 234-5678",
        "address": "1234 Industrial Blvd, Houston, TX 77001",
        "payment_terms": "Net 30",
    },
    {
        "id": "vendor-002",
        "name": "BearingWorld Inc",
        "contact_name": "Sarah Thompson",
        "email": "sales@bearingworld.com",
        "phone": "(555) 345-6789",
        "address": "5678 Manufacturing Way, Chicago, IL 60601",
        "payment_terms": "Net 45",
    },
    {
        "id": "vendor-003",
        "name": "PowerTrans Supply",
        "contact_name": "Mike Chen",
        "email": "mike@powertrans.com",
        "phone": "(555) 456-7890",
        "address": "9012 Power Drive, Detroit, MI 48201",
        "payment_terms": "Net 30",
    },
    {
        "id": "vendor-004",
        "name": "ElectroParts Direct",
        "contact_name": "Lisa Anderson",
        "email": "lisa@electroparts.com",
        "phone": "(555) 567-8901",
        "address": "3456 Circuit Lane, Phoenix, AZ 85001",
        "payment_terms": "Net 15",
    },
    {
        "id": "vendor-005",
        "name": "SealTech Industries",
        "contact_name": "David Wilson",
        "email": "david.wilson@sealtech.com",
        "phone": "(555) 678-9012",
        "address": "7890 Seal Street, Cleveland, OH 44101",
        "payment_terms": "Net 30",
    },
]


# ====== INVENTORY KPI ENDPOINTS ======

@router.get("/inventory/api/kpis")
async def get_inventory_kpis(request: Request):
    """
    Get comprehensive inventory KPIs.
    Returns total value, low stock alerts, category breakdown, turnover metrics.
    """
    current_user = await get_current_user_from_cookie(request)

    try:
        if current_user and current_user.organization_id:
            firestore_manager = get_firestore_manager()
            parts = await firestore_manager.get_org_parts(current_user.organization_id)
            is_demo = False
        else:
            parts = DEMO_PARTS
            is_demo = True

        # Calculate comprehensive KPIs
        total_parts = len(parts)
        total_value = 0
        low_stock_items = []
        out_of_stock_items = []
        by_category = {}
        by_location = {}

        for part in parts:
            current = part.get("current_stock", 0)
            minimum = part.get("minimum_stock", 5)
            unit_cost = part.get("unit_cost", 0)
            category = part.get("category", "General")
            location = part.get("location", "Unknown")

            # Total value
            total_value += current * unit_cost

            # Low stock tracking
            if current == 0:
                out_of_stock_items.append({
                    "id": part.get("id"),
                    "name": part.get("name"),
                    "part_number": part.get("part_number", "N/A"),
                    "minimum_stock": minimum,
                    "severity": "critical"
                })
            elif current <= minimum:
                low_stock_items.append({
                    "id": part.get("id"),
                    "name": part.get("name"),
                    "part_number": part.get("part_number", "N/A"),
                    "current_stock": current,
                    "minimum_stock": minimum,
                    "severity": "warning"
                })

            # Category breakdown
            if category not in by_category:
                by_category[category] = {"count": 0, "value": 0}
            by_category[category]["count"] += 1
            by_category[category]["value"] += current * unit_cost

            # Location breakdown
            if location not in by_location:
                by_location[location] = {"count": 0}
            by_location[location]["count"] += 1

        return JSONResponse(content={
            "is_demo": is_demo,
            "summary": {
                "total_parts": total_parts,
                "total_value": round(total_value, 2),
                "low_stock_count": len(low_stock_items),
                "out_of_stock_count": len(out_of_stock_items),
                "categories_count": len(by_category),
                "locations_count": len(by_location),
            },
            "low_stock_alerts": low_stock_items[:10],
            "out_of_stock_alerts": out_of_stock_items[:10],
            "by_category": by_category,
            "by_location": by_location,
            "health_score": _calculate_inventory_health(total_parts, len(low_stock_items), len(out_of_stock_items)),
        })
    except Exception as e:
        logger.error(f"Error calculating inventory KPIs: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/inventory/api/low-stock")
async def get_low_stock_items(request: Request):
    """Get all low stock and out of stock items for alerts."""
    current_user = await get_current_user_from_cookie(request)

    try:
        if current_user and current_user.organization_id:
            firestore_manager = get_firestore_manager()
            parts = await firestore_manager.get_org_parts(current_user.organization_id)
        else:
            parts = DEMO_PARTS

        alerts = []
        for part in parts:
            current = part.get("current_stock", 0)
            minimum = part.get("minimum_stock", 5)

            if current <= minimum:
                alerts.append({
                    "id": part.get("id"),
                    "name": part.get("name"),
                    "part_number": part.get("part_number", "N/A"),
                    "category": part.get("category", "General"),
                    "current_stock": current,
                    "minimum_stock": minimum,
                    "unit_cost": part.get("unit_cost", 0),
                    "vendor_name": part.get("vendor_name", "N/A"),
                    "severity": "critical" if current == 0 else "warning",
                    "reorder_quantity": max(minimum * 2 - current, minimum),
                })

        # Sort by severity (critical first) then by current stock
        alerts.sort(key=lambda x: (0 if x["severity"] == "critical" else 1, x["current_stock"]))

        return JSONResponse(content={
            "alert_count": len(alerts),
            "critical_count": len([a for a in alerts if a["severity"] == "critical"]),
            "warning_count": len([a for a in alerts if a["severity"] == "warning"]),
            "alerts": alerts,
        })
    except Exception as e:
        logger.error(f"Error getting low stock items: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/inventory/api/value-by-category")
async def get_inventory_value_by_category(request: Request):
    """Get inventory value breakdown by category for charts."""
    current_user = await get_current_user_from_cookie(request)

    try:
        if current_user and current_user.organization_id:
            firestore_manager = get_firestore_manager()
            parts = await firestore_manager.get_org_parts(current_user.organization_id)
        else:
            parts = DEMO_PARTS

        by_category = {}
        for part in parts:
            category = part.get("category", "General")
            current = part.get("current_stock", 0)
            unit_cost = part.get("unit_cost", 0)
            value = current * unit_cost

            if category not in by_category:
                by_category[category] = 0
            by_category[category] += value

        # Format for Chart.js
        return JSONResponse(content={
            "labels": list(by_category.keys()),
            "data": [round(v, 2) for v in by_category.values()],
            "total_value": round(sum(by_category.values()), 2),
        })
    except Exception as e:
        logger.error(f"Error getting inventory value by category: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


def _calculate_inventory_health(total: int, low_stock: int, out_of_stock: int) -> dict:
    """Calculate inventory health score (0-100)."""
    if total == 0:
        return {"score": 100, "status": "N/A", "description": "No inventory tracked"}

    # Deduct points for issues
    critical_penalty = out_of_stock * 10
    warning_penalty = low_stock * 3
    score = max(0, 100 - critical_penalty - warning_penalty)

    if score >= 90:
        status = "Excellent"
        description = "Inventory levels are healthy"
    elif score >= 75:
        status = "Good"
        description = "Minor reorder needed"
    elif score >= 50:
        status = "Fair"
        description = "Several items need attention"
    else:
        status = "Poor"
        description = "Immediate action required"

    return {"score": score, "status": status, "description": description}


@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(request: Request):
    """Render the inventory list - demo data for guests, real data for authenticated"""
    current_user = await get_current_user_from_cookie(request)

    parts = []
    is_demo = False

    if current_user and current_user.organization_id:
        # Authenticated user with organization - show real Firestore data
        firestore_manager = get_firestore_manager()
        try:
            parts = await firestore_manager.get_org_parts(current_user.organization_id)
        except Exception as e:
            logger.error(f"Error loading parts: {e}")
            parts = DEMO_PARTS
            is_demo = True
    else:
        # Not authenticated or no org - show demo data
        parts = DEMO_PARTS
        is_demo = True

    # Calculate inventory stats
    stats = {
        "total_parts": len(parts),
        "low_stock": len([p for p in parts if p.get("current_stock", 0) < p.get("minimum_stock", 5)]),
        "total_value": sum(p.get("current_stock", 0) * p.get("unit_cost", 0) for p in parts),
        "categories": len(set(p.get("category", "General") for p in parts)),
    }

    return templates.TemplateResponse(
        "inventory/list.html",
        {
            "request": request,
            "parts": parts,
            "stats": stats,
            "user": current_user,
            "current_user": current_user,
            "is_demo": is_demo,
        },
    )


@router.get("/inventory/add", response_class=HTMLResponse)
async def add_part_form(
    request: Request,
    current_user: User = Depends(require_permission_cookie("manage_inventory")),
):
    """Render the add part form"""
    firestore_manager = get_firestore_manager()
    # Multi-tenant: filter vendors by user's organization
    if current_user.organization_id:
        vendors = await firestore_manager.get_org_vendors(current_user.organization_id)
    else:
        vendors = await firestore_manager.get_collection("vendors", order_by="name")
    return templates.TemplateResponse(
        "inventory/add.html",
        {
            "request": request,
            "vendors": vendors,
            "user": current_user,
            "current_user": current_user,
            "is_demo": False,
        },
    )


@router.post("/inventory/add")
async def add_part(
    name: str = Form(...),
    part_number: str = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    current_stock: int = Form(0),
    minimum_stock: int = Form(5),
    location: str = Form(""),
    unit_cost: float = Form(0.0),
    vendor_id: str = Form(None),
    files: List[UploadFile] = File(None),
    current_user: User = Depends(require_permission_cookie("manage_inventory")),
):
    """Add a new part to inventory"""
    firestore_manager = get_firestore_manager()
    part_data = {
        "name": name,
        "part_number": part_number,
        "category": category,
        "description": description,
        "current_stock": current_stock,
        "minimum_stock": minimum_stock,
        "location": location,
        "unit_cost": unit_cost,
        "vendor_id": vendor_id,
    }
    # Multi-tenant: associate part with user's organization
    if current_user.organization_id:
        part_id = await firestore_manager.create_org_document(
            "parts", part_data, current_user.organization_id
        )
    else:
        part_id = await firestore_manager.create_document("parts", part_data)

    if files:
        part_dir = os.path.join(UPLOAD_DIR, str(part_id))
        os.makedirs(part_dir, exist_ok=True)
        image_url_set = False
        for file in files:
            if file.filename:
                file_path = os.path.join(part_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                rel_path = f"/static/uploads/parts/{part_id}/{file.filename}"
                if "image" in file.content_type and not image_url_set:
                    await firestore_manager.update_document(
                        "parts", part_id, {"image_url": rel_path}
                    )
                    image_url_set = True

    return RedirectResponse(url="/inventory", status_code=303)


@router.get("/inventory/{part_id}", response_class=HTMLResponse)
async def part_detail(request: Request, part_id: str):
    """Render part details - demo data for guests, real data for authenticated"""
    current_user = await get_current_user_from_cookie(request)

    part = None
    media = []
    is_demo = False

    if current_user and current_user.organization_id:
        # Authenticated user - get real data
        firestore_manager = get_firestore_manager()
        part = await firestore_manager.get_org_document(
            "parts", part_id, current_user.organization_id
        )
        if part:
            vendor = None
            if part.get("vendor_id"):
                vendor = await firestore_manager.get_org_document(
                    "vendors", part["vendor_id"], current_user.organization_id
                )
            part["vendor_name"] = vendor.get("name") if vendor else "N/A"

            media = await firestore_manager.get_collection(
                "part_media", filters=[{"field": "part_id", "operator": "==", "value": part_id}]
            )
    else:
        # Not authenticated - show demo part
        is_demo = True
        part = next((p for p in DEMO_PARTS if p.get("id") == part_id), None)
        if not part:
            part = DEMO_PARTS[0] if DEMO_PARTS else None

    if not part:
        return RedirectResponse(url="/inventory", status_code=302)

    # Demo checkout history
    demo_checkout_history = [
        {"date": "2024-12-18", "quantity": 2, "work_order": "WO-2024-045", "technician": "Mike Johnson"},
        {"date": "2024-12-10", "quantity": 1, "work_order": "WO-2024-038", "technician": "Sarah Chen"},
        {"date": "2024-11-28", "quantity": 3, "work_order": "WO-2024-029", "technician": "Alex Rodriguez"},
    ] if is_demo else []

    return templates.TemplateResponse(
        "inventory/detail.html",
        {
            "request": request,
            "part": part,
            "media": media,
            "checkout_history": demo_checkout_history,
            "user": current_user,
            "current_user": current_user,
            "is_demo": is_demo,
        },
    )


@router.post("/inventory/{part_id}/media")
async def upload_part_media(
    part_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission_cookie("manage_inventory")),
):
    """Upload media for part"""
    part_dir = os.path.join(UPLOAD_DIR, str(part_id))
    os.makedirs(part_dir, exist_ok=True)
    file_path = os.path.join(part_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_path = f"/static/uploads/parts/{part_id}/{file.filename}"

    firestore_manager = get_firestore_manager()
    media_data = {
        "part_id": part_id,
        "file_path": rel_path,
        "file_type": "image" if "image" in file.content_type else "document",
        "title": file.filename,
        "description": "User upload",
    }
    await firestore_manager.create_document("part_media", media_data)

    return RedirectResponse(f"/inventory/{part_id}", status_code=303)


# Vendor Routes
@router.get("/vendors", response_class=HTMLResponse)
async def vendor_list(request: Request):
    """Render vendor list - demo data for guests, real data for authenticated"""
    current_user = await get_current_user_from_cookie(request)

    vendors = []
    is_demo = False

    if current_user and current_user.organization_id:
        # Authenticated user with organization - show real data
        firestore_manager = get_firestore_manager()
        try:
            vendors = await firestore_manager.get_org_vendors(current_user.organization_id)
        except Exception as e:
            logger.error(f"Error loading vendors: {e}")
            vendors = DEMO_VENDORS
            is_demo = True
    else:
        # Not authenticated or no org - show demo data
        vendors = DEMO_VENDORS
        is_demo = True

    return templates.TemplateResponse(
        "inventory/vendors.html",
        {
            "request": request,
            "vendors": vendors,
            "user": current_user,
            "current_user": current_user,
            "is_demo": is_demo,
        },
    )


@router.post("/vendors/add")
async def add_vendor(
    name: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    current_user: User = Depends(require_permission_cookie("manage_vendors")),
):
    """Add a new vendor"""
    firestore_manager = get_firestore_manager()
    vendor_data = {
        "name": name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
    }
    # Multi-tenant: associate vendor with user's organization
    if current_user.organization_id:
        await firestore_manager.create_org_document(
            "vendors", vendor_data, current_user.organization_id
        )
    else:
        await firestore_manager.create_document("vendors", vendor_data)
    return RedirectResponse(url="/vendors", status_code=303)


# ==========================================
# 🔍 PART LOOKUP API ENDPOINTS
# ==========================================


@router.get("/api/parts/search", response_class=JSONResponse)
async def search_parts(
    q: str = "", current_user: User = Depends(require_auth_cookie)
):
    """Search parts by part number, name, or description"""
    firestore_manager = get_firestore_manager()

    if not q or len(q) < 2:
        return JSONResponse(
            {"parts": [], "message": "Enter at least 2 characters to search"}
        )

    # Get all parts and filter (Firestore doesn't support full-text search natively)
    all_parts = await firestore_manager.get_collection("parts", order_by="name")

    search_term = q.lower()
    matching_parts = []

    for part in all_parts:
        # Search in part_number, name, and description
        if (
            search_term in (part.get("part_number") or "").lower()
            or search_term in (part.get("name") or "").lower()
            or search_term in (part.get("description") or "").lower()
        ):
            matching_parts.append(
                {
                    "id": part.get("id"),
                    "part_number": part.get("part_number", "N/A"),
                    "name": part.get("name", "Unknown"),
                    "description": part.get("description", ""),
                    "current_stock": part.get("current_stock", 0),
                    "minimum_stock": part.get("minimum_stock", 0),
                    "location": part.get("location", "N/A"),
                    "unit_cost": part.get("unit_cost", 0),
                    "image_url": part.get("image_url", ""),
                    "category": part.get("category", ""),
                }
            )

    return JSONResponse(
        {
            "parts": matching_parts[:50],  # Limit to 50 results
            "total": len(matching_parts),
            "query": q,
        }
    )


@router.get("/api/parts/by-asset/{asset_id}", response_class=JSONResponse)
async def get_parts_by_asset(
    asset_id: str, current_user: User = Depends(require_auth_cookie)
):
    """Get all parts assigned to a specific asset"""
    firestore_manager = get_firestore_manager()

    # Get asset info
    asset = await firestore_manager.get_document("assets", asset_id)
    if not asset:
        return JSONResponse({"parts": [], "asset": None, "message": "Asset not found"})

    # Get parts for this asset
    parts = await firestore_manager.get_asset_parts(asset_id)

    return JSONResponse(
        {
            "parts": parts,
            "asset": {
                "id": asset.get("id"),
                "name": asset.get("name"),
                "asset_tag": asset.get("asset_tag", ""),
                "location": asset.get("location", ""),
            },
            "total": len(parts),
        }
    )


@router.get("/api/assets/list", response_class=JSONResponse)
async def get_assets_list(current_user: User = Depends(require_auth_cookie)):
    """Get a simple list of all assets for dropdowns"""
    firestore_manager = get_firestore_manager()
    assets = await firestore_manager.get_collection("assets", order_by="name")

    asset_list = [
        {
            "id": asset.get("id"),
            "name": asset.get("name", "Unknown"),
            "asset_tag": asset.get("asset_tag", ""),
            "location": asset.get("location", ""),
            "status": asset.get("status", ""),
        }
        for asset in assets
    ]

    return JSONResponse({"assets": asset_list})


# ==========================================
# 📦 BULK IMPORT ENDPOINTS FOR PARTS
# ==========================================


@router.get("/bulk-import", response_class=HTMLResponse)
async def bulk_import_parts_page(request: Request):
    """Render the bulk import page for parts"""
    # Use cookie-based auth for web pages
    current_user = await get_current_user_from_cookie(request)

    # Redirect to login if not authenticated
    if not current_user:
        return RedirectResponse(url="/auth/login?next=/bulk-import", status_code=302)

    return templates.TemplateResponse(
        "inventory/bulk_import.html",
        {
            "request": request,
            "user": current_user,
            "current_user": current_user,
            "is_demo": False,
            "pandas_available": PANDAS_AVAILABLE,
        },
    )


@router.get("/api/parts/template")
async def download_parts_template(format: str = "csv"):
    """Download a template file for bulk parts import"""
    # Template headers with example data
    headers = [
        "name",
        "part_number",
        "category",
        "description",
        "current_stock",
        "minimum_stock",
        "location",
        "unit_cost",
    ]
    example_data = [
        [
            "Hydraulic Filter",
            "HF-1234",
            "Filters",
            "Heavy duty hydraulic filter for pump systems",
            "25",
            "10",
            "Warehouse A-12",
            "45.99",
        ],
        [
            "Drive Belt",
            "DB-5678",
            "Belts",
            "Industrial drive belt 48 inch",
            "15",
            "5",
            "Warehouse B-3",
            "28.50",
        ],
        [
            "Bearing Assembly",
            "BA-9012",
            "Bearings",
            "Ball bearing assembly 25mm",
            "50",
            "20",
            "Warehouse A-5",
            "12.75",
        ],
    ]

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(example_data)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=parts_import_template.csv"
            },
        )
    elif format.lower() == "xlsx" and PANDAS_AVAILABLE:
        df = pd.DataFrame(example_data, columns=headers)
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name="Parts")
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=parts_import_template.xlsx"
            },
        )
    else:
        return JSONResponse(
            {"error": "Unsupported format. Use csv or xlsx."}, status_code=400
        )


@router.post("/api/parts/bulk-import")
async def bulk_import_parts(
    file: UploadFile = File(...), current_user: User = Depends(require_auth_cookie)
):
    """Bulk import parts from CSV or Excel file"""
    firestore_manager = get_firestore_manager()

    # Validate file type
    filename = file.filename.lower()
    if not (
        filename.endswith(".csv")
        or filename.endswith(".xlsx")
        or filename.endswith(".xls")
    ):
        return JSONResponse(
            {
                "success": False,
                "error": "Invalid file format. Please upload a CSV or Excel file (.csv, .xlsx, .xls)",
            },
            status_code=400,
        )

    try:
        # Read file content
        content = await file.read()

        # Parse file based on type
        if filename.endswith(".csv"):
            # Parse CSV
            text_content = content.decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(text_content))
            rows = list(csv_reader)
        elif PANDAS_AVAILABLE:
            # Parse Excel with pandas
            df = pd.read_excel(io.BytesIO(content))
            rows = df.to_dict("records")
        else:
            return JSONResponse(
                {
                    "success": False,
                    "error": "Excel support not available. Please upload a CSV file.",
                },
                status_code=400,
            )

        if not rows:
            return JSONResponse(
                {"success": False, "error": "File is empty or has no valid data rows."},
                status_code=400,
            )

        # Process and import parts
        imported = 0
        errors = []

        for idx, row in enumerate(rows, start=2):  # Start at 2 (1 for header)
            try:
                # Clean and validate required fields
                name = str(row.get("name", "")).strip()
                if not name:
                    errors.append(f"Row {idx}: Missing required field 'name'")
                    continue

                # Build part data with organization scoping
                part_data = {
                    "name": name,
                    "part_number": str(row.get("part_number", "")).strip(),
                    "category": str(row.get("category", "General")).strip(),
                    "description": str(row.get("description", "")).strip(),
                    "current_stock": int(float(row.get("current_stock", 0) or 0)),
                    "minimum_stock": int(float(row.get("minimum_stock", 5) or 5)),
                    "location": str(row.get("location", "")).strip(),
                    "unit_cost": float(row.get("unit_cost", 0) or 0),
                    "organization_id": current_user.organization_id,
                    "imported_via": "bulk_import",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                # Create part in Firestore
                await firestore_manager.create_document("parts", part_data)
                imported += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        return JSONResponse(
            {
                "success": True,
                "imported": imported,
                "total_rows": len(rows),
                "errors": errors[:20],  # Limit errors to first 20
                "error_count": len(errors),
                "message": f"Successfully imported {imported} of {len(rows)} parts.",
            }
        )

    except Exception as e:
        return JSONResponse(
            {"success": False, "error": f"Error processing file: {str(e)}"},
            status_code=500,
        )


# ==========================================
# 📦 PARTS CHECKOUT ENDPOINTS
# ==========================================


@router.post("/api/parts/checkout", response_class=JSONResponse)
async def checkout_part(
    request: Request,
    part_id: str = Form(...),
    quantity: int = Form(...),
    work_order_id: str = Form(None),
    notes: str = Form(""),
):
    """Checkout a part from inventory (deduct stock)"""
    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        return JSONResponse({"success": False, "error": "Not authenticated"}, status_code=401)

    firestore_manager = get_firestore_manager()

    # Get the part and validate organization
    if current_user.organization_id:
        part = await firestore_manager.get_org_document(
            "parts", part_id, current_user.organization_id
        )
    else:
        part = await firestore_manager.get_document("parts", part_id)

    if not part:
        return JSONResponse({"success": False, "error": "Part not found"}, status_code=404)

    # Check stock availability
    current_stock = part.get("current_stock", 0)
    if quantity > current_stock:
        return JSONResponse({
            "success": False,
            "error": f"Insufficient stock. Available: {current_stock}, Requested: {quantity}"
        }, status_code=400)

    # Update stock
    new_stock = current_stock - quantity
    await firestore_manager.update_document("parts", part_id, {"current_stock": new_stock})

    # Create checkout record
    checkout_data = {
        "part_id": part_id,
        "part_name": part.get("name", "Unknown"),
        "part_number": part.get("part_number", ""),
        "quantity": quantity,
        "work_order_id": work_order_id,
        "checked_out_by": current_user.uid,
        "checked_out_by_name": current_user.full_name or current_user.email,
        "organization_id": current_user.organization_id,
        "notes": notes,
        "checkout_time": datetime.now().isoformat(),
        "previous_stock": current_stock,
        "new_stock": new_stock,
    }
    checkout_id = await firestore_manager.create_document("parts_checkout", checkout_data)

    # Log the checkout for audit trail
    await log_part_checkout(
        part_id=part_id,
        part_name=part.get("name", "Unknown"),
        quantity=quantity,
        work_order_id=work_order_id,
        user_id=current_user.uid,
        user_name=current_user.full_name or current_user.email,
        organization_id=current_user.organization_id,
    )

    logger.info(f"Part checkout: {part.get('name')} x{quantity} by {current_user.full_name} for WO {work_order_id}")

    return JSONResponse({
        "success": True,
        "checkout_id": checkout_id,
        "part_name": part.get("name"),
        "quantity_checked_out": quantity,
        "new_stock": new_stock,
        "message": f"Successfully checked out {quantity} x {part.get('name')}"
    })


@router.post("/api/parts/checkin", response_class=JSONResponse)
async def checkin_part(
    request: Request,
    part_id: str = Form(...),
    quantity: int = Form(...),
    notes: str = Form(""),
):
    """Check in a part to inventory (add stock back)"""
    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        return JSONResponse({"success": False, "error": "Not authenticated"}, status_code=401)

    firestore_manager = get_firestore_manager()

    # Get the part and validate organization
    if current_user.organization_id:
        part = await firestore_manager.get_org_document(
            "parts", part_id, current_user.organization_id
        )
    else:
        part = await firestore_manager.get_document("parts", part_id)

    if not part:
        return JSONResponse({"success": False, "error": "Part not found"}, status_code=404)

    # Update stock
    current_stock = part.get("current_stock", 0)
    new_stock = current_stock + quantity
    await firestore_manager.update_document("parts", part_id, {"current_stock": new_stock})

    # Create checkin record
    checkin_data = {
        "part_id": part_id,
        "part_name": part.get("name", "Unknown"),
        "part_number": part.get("part_number", ""),
        "quantity": quantity,
        "action": "checkin",
        "checked_in_by": current_user.uid,
        "checked_in_by_name": current_user.full_name or current_user.email,
        "organization_id": current_user.organization_id,
        "notes": notes,
        "checkin_time": datetime.now().isoformat(),
        "previous_stock": current_stock,
        "new_stock": new_stock,
    }
    await firestore_manager.create_document("parts_checkout", checkin_data)

    # Log the checkin for audit trail
    await audit_log_service.log_action(
        action=AuditAction.PART_CHECKED_IN,
        entity_type="part",
        entity_id=part_id,
        user_id=current_user.uid,
        user_name=current_user.full_name or current_user.email,
        organization_id=current_user.organization_id,
        new_values={"quantity_checked_in": quantity},
        metadata={"part_name": part.get("name")},
    )

    logger.info(f"Part checkin: {part.get('name')} x{quantity} by {current_user.full_name}")

    return JSONResponse({
        "success": True,
        "part_name": part.get("name"),
        "quantity_checked_in": quantity,
        "new_stock": new_stock,
        "message": f"Successfully checked in {quantity} x {part.get('name')}"
    })


@router.get("/api/parts/checkout-history", response_class=JSONResponse)
async def get_checkout_history(
    request: Request,
    part_id: str = None,
    work_order_id: str = None,
    days: int = 30,
    limit: int = 100,
):
    """Get parts checkout history"""
    current_user = await get_current_user_from_cookie(request)
    if not current_user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    firestore_manager = get_firestore_manager()

    filters = []
    if current_user.organization_id:
        filters.append({
            "field": "organization_id",
            "operator": "==",
            "value": current_user.organization_id
        })

    if part_id:
        filters.append({"field": "part_id", "operator": "==", "value": part_id})

    if work_order_id:
        filters.append({"field": "work_order_id", "operator": "==", "value": work_order_id})

    # Get checkout records
    checkouts = await firestore_manager.get_collection(
        "parts_checkout",
        filters=filters if filters else None,
        limit=limit,
    )

    # Sort by checkout time descending
    checkouts = sorted(
        checkouts,
        key=lambda x: x.get("checkout_time") or x.get("checkin_time") or "",
        reverse=True
    )

    return JSONResponse({
        "checkouts": checkouts,
        "count": len(checkouts),
        "organization_id": current_user.organization_id,
    })
