import csv
import io
import os
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

# Try to import pandas for Excel support
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

from app.auth import get_current_active_user, require_permission
from app.models.user import User
from app.core.firestore_db import get_firestore_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads/parts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(request: Request, current_user: User = Depends(get_current_active_user)):
    """Render the inventory list (filtered by organization)"""
    firestore_manager = get_firestore_manager()
    # Multi-tenant: filter by user's organization
    if current_user.organization_id:
        parts = await firestore_manager.get_org_parts(current_user.organization_id)
    else:
        parts = await firestore_manager.get_collection("parts", order_by="name")
    return templates.TemplateResponse(
        "inventory/list.html", {"request": request, "parts": parts, "user": current_user, "current_user": current_user, "is_demo": False}
    )

@router.get("/inventory/add", response_class=HTMLResponse)
async def add_part_form(request: Request, current_user: User = Depends(require_permission("manage_inventory"))):
    """Render the add part form"""
    firestore_manager = get_firestore_manager()
    # Multi-tenant: filter vendors by user's organization
    if current_user.organization_id:
        vendors = await firestore_manager.get_org_vendors(current_user.organization_id)
    else:
        vendors = await firestore_manager.get_collection("vendors", order_by="name")
    return templates.TemplateResponse(
        "inventory/add.html", {"request": request, "vendors": vendors, "user": current_user, "current_user": current_user, "is_demo": False}
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
    current_user: User = Depends(require_permission("manage_inventory")),
):
    """Add a new part to inventory"""
    firestore_manager = get_firestore_manager()
    part_data = {
        "name": name, "part_number": part_number, "category": category,
        "description": description, "current_stock": current_stock,
        "minimum_stock": minimum_stock, "location": location,
        "unit_cost": unit_cost, "vendor_id": vendor_id
    }
    # Multi-tenant: associate part with user's organization
    if current_user.organization_id:
        part_id = await firestore_manager.create_org_document("parts", part_data, current_user.organization_id)
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
                    await firestore_manager.update_document("parts", part_id, {"image_url": rel_path})
                    image_url_set = True
    
    return RedirectResponse(url="/inventory", status_code=303)

@router.get("/inventory/{part_id}", response_class=HTMLResponse)
async def part_detail(request: Request, part_id: str, current_user: User = Depends(get_current_active_user)):
    """Render part details (validates organization ownership)"""
    firestore_manager = get_firestore_manager()
    # Multi-tenant: validate part belongs to user's organization
    if current_user.organization_id:
        part = await firestore_manager.get_org_document("parts", part_id, current_user.organization_id)
    else:
        part = await firestore_manager.get_document("parts", part_id)
    if not part:
        return RedirectResponse(url="/inventory")
    
    vendor = None
    if part.get("vendor_id"):
        # SECURITY: Validate vendor belongs to same organization
        if current_user.organization_id:
            vendor = await firestore_manager.get_org_document("vendors", part["vendor_id"], current_user.organization_id)
        else:
            vendor = await firestore_manager.get_document("vendors", part["vendor_id"])

    media = await firestore_manager.get_collection(
        "part_media", filters=[{"field": "part_id", "operator": "==", "value": part_id}]
    )
    
    part["vendor_name"] = vendor.get("name") if vendor else "N/A"

    return templates.TemplateResponse(
        "inventory/detail.html", {"request": request, "part": part, "media": media, "user": current_user, "current_user": current_user, "is_demo": False}
    )

@router.post("/inventory/{part_id}/media")
async def upload_part_media(
    part_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("manage_inventory")),
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
        "part_id": part_id, "file_path": rel_path,
        "file_type": "image" if "image" in file.content_type else "document",
        "title": file.filename, "description": "User upload",
    }
    await firestore_manager.create_document("part_media", media_data)
    
    return RedirectResponse(f"/inventory/{part_id}", status_code=303)

# Vendor Routes
@router.get("/vendors", response_class=HTMLResponse)
async def vendor_list(request: Request, current_user: User = Depends(require_permission("manage_vendors"))):
    """Render vendor list (filtered by organization)"""
    firestore_manager = get_firestore_manager()
    # Multi-tenant: filter vendors by user's organization
    if current_user.organization_id:
        vendors = await firestore_manager.get_org_vendors(current_user.organization_id)
    else:
        vendors = await firestore_manager.get_collection("vendors", order_by="name")
    return templates.TemplateResponse(
        "inventory/vendors.html", {"request": request, "vendors": vendors, "user": current_user, "current_user": current_user, "is_demo": False}
    )

@router.post("/vendors/add")
async def add_vendor(
    name: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    current_user: User = Depends(require_permission("manage_vendors")),
):
    """Add a new vendor"""
    firestore_manager = get_firestore_manager()
    vendor_data = {
        "name": name, "contact_name": contact_name,
        "email": email, "phone": phone
    }
    # Multi-tenant: associate vendor with user's organization
    if current_user.organization_id:
        await firestore_manager.create_org_document("vendors", vendor_data, current_user.organization_id)
    else:
        await firestore_manager.create_document("vendors", vendor_data)
    return RedirectResponse(url="/vendors", status_code=303)


# ==========================================
# 🔍 PART LOOKUP API ENDPOINTS
# ==========================================

@router.get("/api/parts/search", response_class=JSONResponse)
async def search_parts(q: str = "", current_user: User = Depends(get_current_active_user)):
    """Search parts by part number, name, or description"""
    firestore_manager = get_firestore_manager()

    if not q or len(q) < 2:
        return JSONResponse({"parts": [], "message": "Enter at least 2 characters to search"})

    # Get all parts and filter (Firestore doesn't support full-text search natively)
    all_parts = await firestore_manager.get_collection("parts", order_by="name")

    search_term = q.lower()
    matching_parts = []

    for part in all_parts:
        # Search in part_number, name, and description
        if (search_term in (part.get("part_number") or "").lower() or
            search_term in (part.get("name") or "").lower() or
            search_term in (part.get("description") or "").lower()):
            matching_parts.append({
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
            })

    return JSONResponse({
        "parts": matching_parts[:50],  # Limit to 50 results
        "total": len(matching_parts),
        "query": q
    })


@router.get("/api/parts/by-asset/{asset_id}", response_class=JSONResponse)
async def get_parts_by_asset(asset_id: str, current_user: User = Depends(get_current_active_user)):
    """Get all parts assigned to a specific asset"""
    firestore_manager = get_firestore_manager()

    # Get asset info
    asset = await firestore_manager.get_document("assets", asset_id)
    if not asset:
        return JSONResponse({"parts": [], "asset": None, "message": "Asset not found"})

    # Get parts for this asset
    parts = await firestore_manager.get_asset_parts(asset_id)

    return JSONResponse({
        "parts": parts,
        "asset": {
            "id": asset.get("id"),
            "name": asset.get("name"),
            "asset_tag": asset.get("asset_tag", ""),
            "location": asset.get("location", "")
        },
        "total": len(parts)
    })


@router.get("/api/assets/list", response_class=JSONResponse)
async def get_assets_list(current_user: User = Depends(get_current_active_user)):
    """Get a simple list of all assets for dropdowns"""
    firestore_manager = get_firestore_manager()
    assets = await firestore_manager.get_collection("assets", order_by="name")

    asset_list = [{
        "id": asset.get("id"),
        "name": asset.get("name", "Unknown"),
        "asset_tag": asset.get("asset_tag", ""),
        "location": asset.get("location", ""),
        "status": asset.get("status", "")
    } for asset in assets]

    return JSONResponse({"assets": asset_list})


# ==========================================
# 📦 BULK IMPORT ENDPOINTS FOR PARTS
# ==========================================

@router.get("/bulk-import", response_class=HTMLResponse)
async def bulk_import_parts_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """Render the bulk import page for parts"""
    return templates.TemplateResponse(
        "inventory/bulk_import.html",
        {"request": request, "user": current_user, "current_user": current_user, "is_demo": False, "pandas_available": PANDAS_AVAILABLE}
    )


@router.get("/api/parts/template")
async def download_parts_template(format: str = "csv"):
    """Download a template file for bulk parts import"""
    # Template headers with example data
    headers = ["name", "part_number", "category", "description", "current_stock", "minimum_stock", "location", "unit_cost"]
    example_data = [
        ["Hydraulic Filter", "HF-1234", "Filters", "Heavy duty hydraulic filter for pump systems", "25", "10", "Warehouse A-12", "45.99"],
        ["Drive Belt", "DB-5678", "Belts", "Industrial drive belt 48 inch", "15", "5", "Warehouse B-3", "28.50"],
        ["Bearing Assembly", "BA-9012", "Bearings", "Ball bearing assembly 25mm", "50", "20", "Warehouse A-5", "12.75"],
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
            headers={"Content-Disposition": "attachment; filename=parts_import_template.csv"}
        )
    elif format.lower() == "xlsx" and PANDAS_AVAILABLE:
        df = pd.DataFrame(example_data, columns=headers)
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name="Parts")
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=parts_import_template.xlsx"}
        )
    else:
        return JSONResponse({"error": "Unsupported format. Use csv or xlsx."}, status_code=400)


@router.post("/api/parts/bulk-import")
async def bulk_import_parts(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk import parts from CSV or Excel file"""
    firestore_manager = get_firestore_manager()

    # Validate file type
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        return JSONResponse({
            "success": False,
            "error": "Invalid file format. Please upload a CSV or Excel file (.csv, .xlsx, .xls)"
        }, status_code=400)

    try:
        # Read file content
        content = await file.read()

        # Parse file based on type
        if filename.endswith('.csv'):
            # Parse CSV
            text_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(text_content))
            rows = list(csv_reader)
        elif PANDAS_AVAILABLE:
            # Parse Excel with pandas
            df = pd.read_excel(io.BytesIO(content))
            rows = df.to_dict('records')
        else:
            return JSONResponse({
                "success": False,
                "error": "Excel support not available. Please upload a CSV file."
            }, status_code=400)

        if not rows:
            return JSONResponse({
                "success": False,
                "error": "File is empty or has no valid data rows."
            }, status_code=400)

        # Process and import parts
        imported = 0
        errors = []

        for idx, row in enumerate(rows, start=2):  # Start at 2 (1 for header)
            try:
                # Clean and validate required fields
                name = str(row.get('name', '')).strip()
                if not name:
                    errors.append(f"Row {idx}: Missing required field 'name'")
                    continue

                # Build part data
                part_data = {
                    "name": name,
                    "part_number": str(row.get('part_number', '')).strip(),
                    "category": str(row.get('category', 'General')).strip(),
                    "description": str(row.get('description', '')).strip(),
                    "current_stock": int(float(row.get('current_stock', 0) or 0)),
                    "minimum_stock": int(float(row.get('minimum_stock', 5) or 5)),
                    "location": str(row.get('location', '')).strip(),
                    "unit_cost": float(row.get('unit_cost', 0) or 0),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                # Create part in Firestore
                await firestore_manager.create_document("parts", part_data)
                imported += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        return JSONResponse({
            "success": True,
            "imported": imported,
            "total_rows": len(rows),
            "errors": errors[:20],  # Limit errors to first 20
            "error_count": len(errors),
            "message": f"Successfully imported {imported} of {len(rows)} parts."
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Error processing file: {str(e)}"
        }, status_code=500)
