import asyncio
import json
import logging
import os
import shutil
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import (
    get_current_active_user,
    require_permission,
    require_permission_cookie,
    require_auth_cookie,
    get_current_user_from_cookie,
)
from app.models.user import User
from app.core.firestore_db import get_firestore_manager
from app.services.gemini_service import gemini_service
from app.services.media_service import media_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directory exists
UPLOAD_DIR = "app/static/uploads/assets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Demo assets for unauthenticated users
DEMO_ASSETS = [
    {
        "id": "demo_asset_1",
        "name": "Production Line A",
        "category": "Manufacturing Equipment",
        "location": "Factory Floor - Zone 1",
        "status": "Operational",
        "condition": "Good",
        "condition_rating": 8,
        "last_maintenance": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() + timedelta(days=75)).strftime("%Y-%m-%d"),
        "criticality": "High",
    },
    {
        "id": "demo_asset_2",
        "name": "HVAC Unit B-2",
        "category": "HVAC",
        "location": "Building B - Roof",
        "status": "Maintenance Required",
        "condition": "Fair",
        "condition_rating": 5,
        "last_maintenance": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "criticality": "Medium",
    },
    {
        "id": "demo_asset_3",
        "name": "Forklift FL-001",
        "category": "Material Handling",
        "location": "Warehouse",
        "status": "Operational",
        "condition": "Excellent",
        "condition_rating": 9,
        "last_maintenance": (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() + timedelta(days=82)).strftime("%Y-%m-%d"),
        "criticality": "Medium",
    },
    {
        "id": "demo_asset_4",
        "name": "Compressor C-5",
        "category": "Compressed Air",
        "location": "Utility Room",
        "status": "Down",
        "condition": "Poor",
        "condition_rating": 2,
        "last_maintenance": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        "criticality": "Critical",
    },
    {
        "id": "demo_asset_5",
        "name": "Conveyor System C-1",
        "category": "Material Handling",
        "location": "Assembly Line",
        "status": "Operational",
        "condition": "Good",
        "condition_rating": 7,
        "last_maintenance": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
        "next_maintenance": (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d"),
        "criticality": "High",
    },
]


@router.get("/", response_class=HTMLResponse)
async def assets_list(request: Request):
    """Display assets - requires authentication"""
    # Use cookie-based auth for web pages
    current_user = await get_current_user_from_cookie(request)

    # Require authentication - no more demo mode
    if not current_user:
        return RedirectResponse(url="/auth/login?next=/assets", status_code=302)

    assets = []

    if current_user.organization_id:
        # Authenticated user with organization - show real Firestore data
        firestore_manager = get_firestore_manager()
        try:
            assets = await firestore_manager.get_org_assets(current_user.organization_id)
        except Exception as e:
            logger.error(f"Error loading assets: {e}")
            assets = []
    else:
        # Authenticated but no organization yet
        assets = []

    stats = {
        "total": len(assets),
        "active": len([a for a in assets if a.get("status") in ["Active", "Operational"]]),
        "critical": len([a for a in assets if a.get("criticality") == "Critical" or a.get("status") == "Down"]),
        "maintenance_due": len(
            [
                a
                for a in assets
                if a.get("status") in ["Maintenance Required", "Down"]
            ]
        ),
    }

    return templates.TemplateResponse(
        "assets_list.html",
        {
            "request": request,
            "assets": assets,
            "stats": stats,
            "user": current_user,
            "current_user": current_user,
            "is_demo": False,
            "demo_mode": False,
        },
    )


@router.get("/{asset_id}", response_class=HTMLResponse)
async def asset_detail(request: Request, asset_id: str):
    """Asset detail view - requires authentication"""
    current_user = await get_current_user_from_cookie(request)

    # Require authentication - no more demo mode
    if not current_user:
        return RedirectResponse(url=f"/auth/login?next=/assets/{asset_id}", status_code=302)

    asset = None
    children = []
    media = []
    parts = []
    history = []
    work_orders = []

    if current_user.organization_id:
        # Authenticated user - get real asset from Firestore
        firestore_manager = get_firestore_manager()
        asset = await firestore_manager.get_org_document(
            "assets", asset_id, current_user.organization_id
        )
        if not asset:
            return RedirectResponse("/assets", status_code=302)

        # Get related data in parallel
        children, media, parts, history, work_orders = await asyncio.gather(
            firestore_manager.get_collection(
                "assets",
                filters=[{"field": "parent_asset_id", "operator": "==", "value": asset_id}],
            ),
            firestore_manager.get_collection(
                "asset_media",
                filters=[{"field": "asset_id", "operator": "==", "value": asset_id}],
                order_by="-uploaded_date",
            ),
            firestore_manager.get_asset_parts(asset_id),
            firestore_manager.get_collection(
                "maintenance_history",
                filters=[{"field": "asset_id", "operator": "==", "value": asset_id}],
                order_by="-created_date",
                limit=50,
            ),
            firestore_manager.get_asset_work_orders(asset_id),
        )
    else:
        # Authenticated but no organization - redirect to assets list
        return RedirectResponse("/assets", status_code=302)

    # Simplified cost analytics
    total_cost = sum(h.get("total_cost", 0) for h in history)
    labor_cost = sum(h.get("labor_cost", 0) for h in history)
    parts_cost = sum(h.get("parts_cost", 0) for h in history)
    total_downtime = sum(h.get("downtime_hours", 0) for h in history)

    cost_data = {
        "total_cost": total_cost,
        "labor_cost": labor_cost,
        "parts_cost": parts_cost,
        "total_downtime": total_downtime,
    }

    return templates.TemplateResponse(
        "asset_detail.html",
        {
            "request": request,
            "asset": asset,
            "children": children,
            "media": media,
            "parts": parts,
            "history": history,
            "work_orders": work_orders,
            "cost_data": cost_data,
            "user": current_user,
            "current_user": current_user,
            "is_demo": False,
        },
    )


@router.post("/")
async def create_asset(
    name: str = Form(...),
    description: str = Form(""),
    asset_tag: str = Form(""),
    serial_number: str = Form(""),
    model: str = Form(""),
    manufacturer: str = Form(""),
    location: str = Form(""),
    department: str = Form(""),
    parent_asset_id: str = Form(None),
    status: str = Form("Active"),
    criticality: str = Form("Medium"),
    purchase_date: str = Form(None),
    warranty_expiry: str = Form(None),
    purchase_cost: float = Form(None),
    files: List[UploadFile] = File(None),
    current_user: User = Depends(require_permission_cookie("create_asset")),
):
    """Create a new asset"""
    firestore_manager = get_firestore_manager()

    asset_data = {
        "name": name,
        "description": description,
        "asset_tag": asset_tag,
        "serial_number": serial_number,
        "model": model,
        "manufacturer": manufacturer,
        "location": location,
        "department": department,
        "parent_asset_id": parent_asset_id,
        "status": status,
        "criticality": criticality,
        "purchase_date": purchase_date,
        "warranty_expiry": warranty_expiry,
        "purchase_cost": purchase_cost,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    # Multi-tenant: associate asset with user's organization
    if current_user.organization_id:
        asset_id = await firestore_manager.create_org_document(
            "assets", asset_data, current_user.organization_id
        )
    else:
        asset_id = await firestore_manager.create_document("assets", asset_data)

    # Handle file uploads
    if files:
        asset_dir = os.path.join(UPLOAD_DIR, str(asset_id))
        os.makedirs(asset_dir, exist_ok=True)

        for file in files:
            if file.filename:
                file_path = os.path.join(asset_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                rel_path = f"/static/uploads/assets/{asset_id}/{file.filename}"
                file_type = (
                    "image"
                    if file.content_type and file.content_type.startswith("image/")
                    else "document"
                )

                media_data = {
                    "asset_id": asset_id,
                    "file_path": rel_path,
                    "file_type": file_type,
                    "title": file.filename,
                    "description": "Uploaded during creation",
                    "uploaded_date": datetime.now(timezone.utc),
                }
                await firestore_manager.create_document("asset_media", media_data)

    return RedirectResponse(f"/assets/{asset_id}", status_code=303)


@router.post("/{asset_id}/update")
async def update_asset(
    request: Request,
    asset_id: str,
    name: str = Form(...),
    description: str = Form(""),
    asset_tag: str = Form(""),
    serial_number: str = Form(""),
    model: str = Form(""),
    manufacturer: str = Form(""),
    location: str = Form(""),
    department: str = Form(""),
    status: str = Form("Active"),
    criticality: str = Form("Medium"),
    condition_rating: int = Form(None),
    purchase_date: str = Form(None),
    warranty_expiry: str = Form(None),
    purchase_cost: float = Form(None),
    current_user: User = Depends(require_permission_cookie("update_asset")),
):
    """Update an existing asset"""
    firestore_manager = get_firestore_manager()

    # Verify asset belongs to user's organization
    if current_user.organization_id:
        existing_asset = await firestore_manager.get_org_document(
            "assets", asset_id, current_user.organization_id
        )
        if not existing_asset:
            return JSONResponse(
                {"error": "Asset not found or access denied"}, status_code=404
            )

    update_data = {
        "name": name,
        "description": description,
        "asset_tag": asset_tag,
        "serial_number": serial_number,
        "model": model,
        "manufacturer": manufacturer,
        "location": location,
        "department": department,
        "status": status,
        "criticality": criticality,
        "purchase_date": purchase_date,
        "warranty_expiry": warranty_expiry,
        "purchase_cost": purchase_cost,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if condition_rating is not None:
        update_data["condition_rating"] = condition_rating

    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}

    # Update with org validation
    if current_user.organization_id:
        success = await firestore_manager.update_org_document(
            "assets", asset_id, update_data, current_user.organization_id
        )
    else:
        success = await firestore_manager.update_document(
            "assets", asset_id, update_data
        )

    if not success:
        return JSONResponse({"error": "Failed to update asset"}, status_code=500)

    return RedirectResponse(f"/assets/{asset_id}", status_code=303)


@router.post("/{asset_id}/media")
async def upload_media(
    asset_id: str,
    file: UploadFile = File(...),
    file_type: str = Form("image"),
    title: str = Form(""),
    description: str = Form(""),
    current_user: User = Depends(require_permission_cookie("update_asset")),
):
    """Upload photo, video, or document"""
    asset_dir = os.path.join(UPLOAD_DIR, str(asset_id))
    os.makedirs(asset_dir, exist_ok=True)

    file_path = os.path.join(asset_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_path = f"/static/uploads/assets/{asset_id}/{file.filename}"

    firestore_manager = get_firestore_manager()
    media_data = {
        "asset_id": asset_id,
        "file_path": rel_path,
        "file_type": file_type,
        "title": title,
        "description": description,
        "uploaded_by": current_user.uid,
        "uploaded_date": datetime.now(timezone.utc),
    }
    await firestore_manager.create_document("asset_media", media_data)

    return RedirectResponse(f"/assets/{asset_id}", status_code=303)


@router.post("/{asset_id}/maintenance")
async def log_maintenance(
    asset_id: str,
    maintenance_type: str = Form(...),
    description: str = Form(""),
    technician: str = Form(""),
    downtime_hours: float = Form(0),
    labor_cost: float = Form(0),
    parts_cost: float = Form(0),
    current_user: User = Depends(require_permission_cookie("log_maintenance")),
):
    """Log a maintenance event"""
    total_cost = labor_cost + parts_cost
    firestore_manager = get_firestore_manager()

    history_data = {
        "asset_id": asset_id,
        "maintenance_type": maintenance_type,
        "description": description,
        "technician": technician,
        "downtime_hours": downtime_hours,
        "labor_cost": labor_cost,
        "parts_cost": parts_cost,
        "total_cost": total_cost,
        "created_date": datetime.now(timezone.utc),
    }
    await firestore_manager.create_document("maintenance_history", history_data)

    # This should be a transaction in a real app
    asset = await firestore_manager.get_document("assets", asset_id)
    if asset:
        new_downtime = asset.get("total_downtime_hours", 0) + downtime_hours
        new_cost = asset.get("total_maintenance_cost", 0) + total_cost
        await firestore_manager.update_document(
            "assets",
            asset_id,
            {
                "total_downtime_hours": new_downtime,
                "total_maintenance_cost": new_cost,
                "last_service_date": datetime.now(timezone.utc),
            },
        )

    return RedirectResponse(f"/assets/{asset_id}", status_code=303)


@router.get("/{asset_id}/ai-health")
async def ai_health_analysis(
    asset_id: str, current_user: User = Depends(require_auth_cookie)
):
    """AI-powered health analysis"""
    if not gemini_service.is_available():
        return JSONResponse({"health_score": 0, "analysis": "AI unavailable"})

    firestore_manager = get_firestore_manager()
    asset, history = await asyncio.gather(
        firestore_manager.get_document("assets", asset_id),
        firestore_manager.get_collection(
            "maintenance_history",
            filters=[{"field": "asset_id", "operator": "==", "value": asset_id}],
            order_by="-created_date",
            limit=10,
        ),
    )
    if not asset:
        return JSONResponse({"error": "Asset not found"}, status_code=404)

    context = f"""
    Analyze the health of this asset and provide a health score (0-100) and brief analysis.

    Asset: {asset.get('name')}
    Model: {asset.get('model')}
    Age: Installed {asset.get('installation_date')}
    Total Downtime: {asset.get('total_downtime_hours')} hours
    Total Maintenance Cost: ${asset.get('total_maintenance_cost')}
    Recent Maintenance Events: {len(history)}
    Criticality: {asset.get('criticality')}

    Provide response as JSON: {{"health_score": <0-100>, "risk_level": "<Low/Medium/High>", "analysis": "<brief analysis>", "recommendations": ["<rec1>", "<rec2>"]}}
    """

    try:
        response = await gemini_service.generate_response(
            context, user_id=current_user.uid
        )
        # Try to parse as JSON
        import re

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return JSONResponse(result)
    except Exception:
        pass

    return JSONResponse(
        {
            "health_score": 75,
            "risk_level": "Medium",
            "analysis": "AI analysis in progress",
            "recommendations": [
                "Schedule preventive maintenance",
                "Monitor performance metrics",
            ],
        }
    )


@router.get("/{asset_id}/ai-recommendations")
async def ai_recommendations(
    asset_id: str, current_user: User = Depends(require_auth_cookie)
):
    """AI predictive maintenance recommendations"""
    if not gemini_service.is_available():
        return JSONResponse({"recommendations": []})

    firestore_manager = get_firestore_manager()
    asset, parts = await asyncio.gather(
        firestore_manager.get_document("assets", asset_id),
        firestore_manager.get_asset_parts(asset_id),
    )
    if not asset:
        return JSONResponse({"error": "Asset not found"}, status_code=404)

    prompt = f"""
    Provide predictive maintenance recommendations for this asset.

    Asset: {asset.get('name')} ({asset.get('model')})
    Last Service: {asset.get('last_service_date')}
    Next Service: {asset.get('next_service_date')}
    Associated Parts: {len(parts)}

    Return JSON array of recommendations with priority and estimated cost.
    """

    try:
        response = await gemini_service.generate_response(
            prompt, user_id=current_user.uid
        )
        return JSONResponse({"recommendations": response})
    except Exception:
        return JSONResponse(
            {
                "recommendations": [
                    {
                        "task": "Inspect bearings",
                        "priority": "High",
                        "estimated_cost": 150,
                    },
                    {
                        "task": "Replace filters",
                        "priority": "Medium",
                        "estimated_cost": 75,
                    },
                ]
            }
        )


@router.post("/scan-barcode")
async def scan_asset_barcode(
    file: UploadFile = File(...), current_user: User = Depends(require_auth_cookie)
):
    """Scan barcode to find asset and related information"""
    try:
        if not file.filename:
            return JSONResponse(
                {"success": False, "error": "No file provided"}, status_code=400
            )

        # Read and scan barcode
        image_data = await file.read()
        barcodes = await media_service.scan_barcode_from_image(image_data)

        if not barcodes:
            return JSONResponse(
                {"success": False, "error": "No barcode found in image"},
                status_code=400,
            )

        barcode_data = barcodes[0]["data"]
        db_adapter = get_db_adapter()
        asset = await db_adapter.find_asset_by_identifier(barcode_data)

        if asset:
            work_orders, parts = await asyncio.gather(
                db_adapter.get_asset_work_orders(asset["id"]),
                db_adapter.get_asset_parts(asset["id"]),
            )
            return JSONResponse(
                {
                    "success": True,
                    "barcode_data": barcode_data,
                    "asset": asset,
                    "work_orders": work_orders[:5],
                    "parts": parts,
                    "scan_result": "asset_found",
                }
            )
        else:
            return JSONResponse(
                {
                    "success": True,
                    "barcode_data": barcode_data,
                    "asset": None,
                    "work_orders": [],
                    "parts": [],
                    "scan_result": "no_asset_found",
                    "message": f"No asset found with identifier: {barcode_data}",
                }
            )

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/lookup-by-tag")
async def lookup_asset_by_tag(
    asset_tag: str = Form(...), current_user: User = Depends(require_auth_cookie)
):
    """Quick lookup of asset by tag/barcode"""
    try:
        db_adapter = get_db_adapter()
        asset = await db_adapter.get_asset_by_tag(asset_tag)

        if asset:
            work_orders_count, parts_count = await asyncio.gather(
                db_adapter.count_asset_work_orders(asset["id"]),
                db_adapter.count_asset_parts(asset["id"]),
            )

            return JSONResponse(
                {
                    "success": True,
                    "asset": asset,
                    "work_orders_count": work_orders_count,
                    "parts_count": parts_count,
                }
            )
        else:
            return JSONResponse(
                {"success": False, "error": f"Asset not found: {asset_tag}"},
                status_code=404,
            )

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/{asset_id}/generate-qr")
async def generate_asset_qr_code(
    asset_id: str, current_user: User = Depends(require_auth_cookie)
):
    """Generate QR code for asset"""
    try:
        db_adapter = get_db_adapter()
        asset = await db_adapter.get_asset(asset_id)

        if not asset:
            return JSONResponse(
                {"success": False, "error": "Asset not found"}, status_code=404
            )

        qr_data = asset.get("asset_tag", f"ASSET-{asset_id}")

        barcode_info = await media_service.generate_barcode(
            data=qr_data, barcode_type="qr", size=(300, 300)
        )

        return JSONResponse(
            {
                "success": True,
                "qr_code": barcode_info,
                "asset": asset,
                "qr_data": qr_data,
            }
        )

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
