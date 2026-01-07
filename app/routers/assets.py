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
from app.services.quota_service import quota_service, QuotaExceededError

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
    """Display assets - demo data for guests, real data for authenticated users"""
    # Use cookie-based auth for web pages
    current_user = await get_current_user_from_cookie(request)

    assets = []
    is_demo = False

    if current_user and current_user.organization_id:
        # Authenticated user with organization - show real Firestore data
        firestore_manager = get_firestore_manager()
        try:
            assets = await firestore_manager.get_org_assets(current_user.organization_id)
        except Exception as e:
            logger.error(f"Error loading assets: {e}")
            assets = DEMO_ASSETS
            is_demo = True
    else:
        # Not authenticated or no org - show demo data
        assets = DEMO_ASSETS
        is_demo = True

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
            "is_demo": is_demo,
            "demo_mode": is_demo,
        },
    )


@router.get("/{asset_id}", response_class=HTMLResponse)
async def asset_detail(request: Request, asset_id: str):
    """Asset detail view - demo data for guests, real data for authenticated users"""
    current_user = await get_current_user_from_cookie(request)

    asset = None
    children = []
    media = []
    parts = []
    history = []
    work_orders = []
    pm_schedules = []
    is_demo = False

    if current_user and current_user.organization_id:
        # Authenticated user - get real asset from Firestore
        firestore_manager = get_firestore_manager()
        asset = await firestore_manager.get_org_document(
            "assets", asset_id, current_user.organization_id
        )
        if not asset:
            return RedirectResponse("/assets", status_code=302)

        # Get related data in parallel
        children, media, parts, history, work_orders, pm_schedules = await asyncio.gather(
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
            firestore_manager.get_collection(
                "pm_schedule_rules",
                filters=[
                    {"field": "asset_id", "operator": "==", "value": asset_id},
                    {"field": "is_active", "operator": "==", "value": True},
                ],
            ),
        )
    else:
        # Not authenticated or no org - show demo data
        is_demo = True
        # Find demo asset by ID or show first demo asset
        demo_asset = next((a for a in DEMO_ASSETS if str(a.get("id")) == asset_id), None)
        if not demo_asset:
            demo_asset = DEMO_ASSETS[0] if DEMO_ASSETS else None
        if not demo_asset:
            return RedirectResponse("/assets", status_code=302)
        asset = demo_asset
        # Demo related data
        work_orders = [
            {"id": "WO-DEMO-1", "title": "Quarterly Inspection", "status": "Open", "priority": "Medium"},
            {"id": "WO-DEMO-2", "title": "Belt Replacement", "status": "Completed", "priority": "High"},
        ]
        history = [
            {"description": "Replaced drive belt", "total_cost": 450, "labor_cost": 200, "parts_cost": 250, "downtime_hours": 2},
            {"description": "Lubrication service", "total_cost": 75, "labor_cost": 75, "parts_cost": 0, "downtime_hours": 0.5},
        ]

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
            "pm_schedules": pm_schedules,
            "cost_data": cost_data,
            "user": current_user,
            "current_user": current_user,
            "is_demo": is_demo,
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

    # Quota enforcement: reserve a slot before creating the asset
    if current_user.organization_id:
        try:
            await quota_service.reserve_asset_slot(current_user.organization_id)
        except QuotaExceededError as e:
            logger.warning(f"Quota exceeded for org {current_user.organization_id}: {e}")
            return JSONResponse(
                {
                    "error": str(e),
                    "error_type": "quota_exceeded",
                    "resource_type": e.resource_type,
                    "limit": e.limit,
                    "current": e.current,
                    "tier": e.tier,
                },
                status_code=403,
            )

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
    firestore_manager = get_firestore_manager()

    # Verify asset belongs to user's organization (multi-tenant data isolation)
    org_id = current_user.organization_id if current_user and current_user.organization_id else "demo_org"
    asset = await firestore_manager.get_org_document("assets", asset_id, org_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset_dir = os.path.join(UPLOAD_DIR, str(asset_id))
    os.makedirs(asset_dir, exist_ok=True)

    file_path = os.path.join(asset_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rel_path = f"/static/uploads/assets/{asset_id}/{file.filename}"

    media_data = {
        "asset_id": asset_id,
        "organization_id": org_id,  # Tag with org for multi-tenant isolation
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

    # Verify asset belongs to user's organization (multi-tenant data isolation)
    org_id = current_user.organization_id if current_user and current_user.organization_id else "demo_org"
    asset = await firestore_manager.get_org_document("assets", asset_id, org_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    history_data = {
        "asset_id": asset_id,
        "organization_id": org_id,  # Tag with org for multi-tenant isolation
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

    # Update asset totals (already verified above)
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

    # Get org-scoped asset (multi-tenant data isolation)
    org_id = current_user.organization_id if current_user and current_user.organization_id else "demo_org"
    asset, history = await asyncio.gather(
        firestore_manager.get_org_document("assets", asset_id, org_id),
        firestore_manager.get_collection(
            "maintenance_history",
            filters=[
                {"field": "asset_id", "operator": "==", "value": asset_id},
                {"field": "organization_id", "operator": "==", "value": org_id},
            ],
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

    # Get org-scoped asset (multi-tenant data isolation)
    org_id = current_user.organization_id if current_user and current_user.organization_id else "demo_org"
    asset, parts = await asyncio.gather(
        firestore_manager.get_org_document("assets", asset_id, org_id),
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


# ==========================================
# PM SCHEDULE MANAGEMENT ENDPOINTS
# ==========================================


@router.post("/{asset_id}/ai-generate-pm")
async def ai_generate_pm_schedule(
    asset_id: str,
    current_user: User = Depends(require_permission_cookie("update_asset")),
):
    """
    AI-powered PM schedule generation using ALL available data:
    - Uploaded equipment manuals and documentation
    - Work order history (patterns, common repairs)
    - Maintenance history (what's been done before)
    - AI's general knowledge about this equipment type/manufacturer
    """
    firestore_manager = get_firestore_manager()

    # Get org-scoped asset (multi-tenant data isolation)
    org_id = current_user.organization_id if current_user and current_user.organization_id else "demo_org"
    asset = await firestore_manager.get_org_document("assets", asset_id, org_id)
    if not asset:
        return JSONResponse({"success": False, "error": "Asset not found"}, status_code=404)

    # Get ALL available data in parallel for comprehensive analysis (org-scoped)
    documents, work_orders, maintenance_history, parts = await asyncio.gather(
        firestore_manager.get_collection(
            "asset_media",
            filters=[
                {"field": "asset_id", "operator": "==", "value": asset_id},
                {"field": "organization_id", "operator": "==", "value": org_id},
            ],
        ),
        firestore_manager.get_asset_work_orders(asset_id),
        firestore_manager.get_collection(
            "maintenance_history",
            filters=[
                {"field": "asset_id", "operator": "==", "value": asset_id},
                {"field": "organization_id", "operator": "==", "value": org_id},
            ],
            order_by="-created_date",
            limit=50,
        ),
        firestore_manager.get_asset_parts(asset_id),
    )

    # Filter for document types (not images/videos)
    doc_types = ["manual", "document", "datasheet", "warranty", "certificate", "pdf"]
    manuals = [d for d in documents if d.get("file_type") in doc_types or
               d.get("file_path", "").lower().endswith((".pdf", ".doc", ".docx", ".txt"))]

    # Build context sections
    manual_info = ""
    if manuals:
        manual_info = "UPLOADED DOCUMENTATION:\n" + "\n".join([
            f"- {m.get('title', 'Untitled')} ({m.get('file_type', 'document')}): {m.get('description', 'No description')}"
            for m in manuals[:5]
        ])
    else:
        manual_info = "UPLOADED DOCUMENTATION: None available - use your expert knowledge for this equipment type."

    # Summarize work order history
    wo_summary = ""
    if work_orders:
        wo_types = {}
        for wo in work_orders[:20]:
            wo_type = wo.get("work_order_type", "Unknown")
            wo_types[wo_type] = wo_types.get(wo_type, 0) + 1
        wo_titles = [wo.get("title", "")[:50] for wo in work_orders[:10]]
        wo_summary = f"""WORK ORDER HISTORY ({len(work_orders)} total):
- Types: {', '.join([f'{k}: {v}' for k, v in wo_types.items()])}
- Recent issues: {'; '.join(wo_titles)}"""
    else:
        wo_summary = "WORK ORDER HISTORY: No work orders recorded yet."

    # Summarize maintenance history
    maint_summary = ""
    if maintenance_history:
        maint_types = {}
        total_cost = 0
        total_downtime = 0
        for m in maintenance_history:
            m_type = m.get("maintenance_type", "Unknown")
            maint_types[m_type] = maint_types.get(m_type, 0) + 1
            total_cost += m.get("total_cost", 0)
            total_downtime += m.get("downtime_hours", 0)
        maint_summary = f"""MAINTENANCE HISTORY ({len(maintenance_history)} events):
- Types: {', '.join([f'{k}: {v}' for k, v in maint_types.items()])}
- Total cost: ${total_cost:.2f}
- Total downtime: {total_downtime:.1f} hours"""
    else:
        maint_summary = "MAINTENANCE HISTORY: No maintenance events recorded yet."

    # Summarize parts and their maintenance requirements
    parts_summary = ""
    if parts:
        parts_info = []
        for p in parts[:15]:  # Limit to 15 parts
            part_info = f"- {p.get('name', 'Unknown Part')}"
            if p.get('part_number'):
                part_info += f" (P/N: {p.get('part_number')})"
            if p.get('manufacturer'):
                part_info += f" by {p.get('manufacturer')}"
            # Include any maintenance notes or recommended replacement intervals
            if p.get('maintenance_notes'):
                part_info += f"\n  Maintenance: {p.get('maintenance_notes')}"
            if p.get('replacement_interval_days'):
                part_info += f"\n  Replace every: {p.get('replacement_interval_days')} days"
            if p.get('replacement_interval_hours'):
                part_info += f"\n  Replace every: {p.get('replacement_interval_hours')} operating hours"
            if p.get('inspection_interval'):
                part_info += f"\n  Inspect every: {p.get('inspection_interval')}"
            if p.get('description'):
                part_info += f"\n  Notes: {p.get('description')[:100]}"
            parts_info.append(part_info)
        parts_summary = f"""INSTALLED PARTS & COMPONENTS ({len(parts)} total):
{chr(10).join(parts_info)}

Consider each part's manufacturer recommendations for replacement/inspection intervals."""
    else:
        parts_summary = "INSTALLED PARTS: No parts recorded - use standard component maintenance intervals for this equipment type."

    prompt = f"""You are an expert maintenance engineer with deep knowledge of industrial equipment.

Generate a comprehensive preventive maintenance schedule for this asset using:
1. The uploaded documentation (if available)
2. Work order and maintenance history patterns
3. Your expert knowledge about this type of equipment, manufacturer, and industry best practices

ASSET INFORMATION:
- Name: {asset.get('name')}
- Model: {asset.get('model', 'Unknown')}
- Manufacturer: {asset.get('manufacturer', 'Unknown')}
- Type/Category: {asset.get('asset_type', asset.get('category', 'Equipment'))}
- Location: {asset.get('location', 'Not specified')}
- Department: {asset.get('department', 'Not specified')}
- Criticality: {asset.get('criticality', 'Medium')}
- Serial Number: {asset.get('serial_number', 'Unknown')}
- Installation Date: {asset.get('installation_date', 'Unknown')}
- Total Downtime: {asset.get('total_downtime_hours', 0)} hours
- Total Maintenance Cost: ${asset.get('total_maintenance_cost', 0)}

{manual_info}

{wo_summary}

{maint_summary}

{parts_summary}

Based on ALL this information and your expert knowledge of similar equipment, generate a JSON array of PM schedule recommendations. Each should include:
- title: Short task name (be specific to this equipment)
- description: Detailed step-by-step instructions
- schedule_type: "time_based", "usage_based", "condition_based", "inspection", or "preventive"
- interval_days: Days between tasks (for time-based)
- interval_hours: Operating hours between tasks (for usage-based, if applicable)
- priority: "Low", "Medium", "High", or "Critical"
- estimated_hours: Estimated time to complete

Consider:
- Common failure modes for this type of equipment
- Manufacturer recommendations (from your knowledge if no manual)
- Industry standards and best practices
- Patterns from the work order/maintenance history
- Safety-critical inspections
- Seasonal or environmental factors

Return ONLY valid JSON array, no other text:
[{{"title": "...", "description": "...", "schedule_type": "...", "interval_days": N, "priority": "...", "estimated_hours": N}}, ...]
"""

    if not gemini_service.is_available():
        # Fallback: Generate basic recommendations based on asset type
        return JSONResponse({
            "success": True,
            "message": "Generated default recommendations (AI unavailable)",
            "recommendations": _generate_default_pm_recommendations(asset),
            "data_sources": ["default_templates"]
        })

    try:
        response = await gemini_service.generate_response(prompt, user_id=current_user.uid)

        # Parse JSON from response
        import re
        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if json_match:
            recommendations = json.loads(json_match.group())

            # Track what data sources were used
            data_sources = []
            if manuals:
                data_sources.append("uploaded_documents")
            if work_orders:
                data_sources.append("work_order_history")
            if maintenance_history:
                data_sources.append("maintenance_history")
            if parts:
                data_sources.append("parts_components")
            data_sources.append("ai_knowledge")

            return JSONResponse({
                "success": True,
                "recommendations": recommendations,
                "analyzed_documents": len(manuals),
                "work_orders_analyzed": len(work_orders),
                "maintenance_events_analyzed": len(maintenance_history),
                "parts_analyzed": len(parts),
                "data_sources": data_sources
            })
    except Exception as e:
        logger.error(f"AI PM generation error: {e}")

    # Fallback to default recommendations
    return JSONResponse({
        "success": True,
        "message": "Generated default recommendations",
        "recommendations": _generate_default_pm_recommendations(asset),
        "data_sources": ["default_templates"]
    })


def _generate_default_pm_recommendations(asset: dict) -> list:
    """Generate default PM recommendations based on asset type."""
    asset_name = asset.get("name", "Equipment")
    criticality = asset.get("criticality", "Medium")

    # Adjust intervals based on criticality
    interval_multiplier = {"Critical": 0.5, "High": 0.75, "Medium": 1.0, "Low": 1.5}.get(criticality, 1.0)

    return [
        {
            "title": f"Daily Visual Inspection - {asset_name}",
            "description": "Perform visual inspection for leaks, unusual sounds, vibrations, or damage. Check indicator lights and gauges.",
            "schedule_type": "inspection",
            "interval_days": 1,
            "priority": "Medium",
            "estimated_hours": 0.25
        },
        {
            "title": f"Weekly Cleaning & Lubrication - {asset_name}",
            "description": "Clean external surfaces, check and apply lubrication to moving parts as specified in manual.",
            "schedule_type": "preventive",
            "interval_days": int(7 * interval_multiplier),
            "priority": "Medium",
            "estimated_hours": 0.5
        },
        {
            "title": f"Monthly Safety Inspection - {asset_name}",
            "description": "Inspect safety guards, emergency stops, warning labels, and protective equipment. Test safety interlocks.",
            "schedule_type": "inspection",
            "interval_days": int(30 * interval_multiplier),
            "priority": "High",
            "estimated_hours": 1.0
        },
        {
            "title": f"Quarterly Component Check - {asset_name}",
            "description": "Detailed inspection of belts, filters, bearings, and wear components. Replace as needed.",
            "schedule_type": "preventive",
            "interval_days": int(90 * interval_multiplier),
            "priority": "Medium",
            "estimated_hours": 2.0
        },
        {
            "title": f"Semi-Annual Calibration - {asset_name}",
            "description": "Calibrate sensors, gauges, and control systems. Verify accuracy against standards.",
            "schedule_type": "preventive",
            "interval_days": int(180 * interval_multiplier),
            "priority": "High",
            "estimated_hours": 3.0
        },
        {
            "title": f"Annual Comprehensive Overhaul - {asset_name}",
            "description": "Complete disassembly, cleaning, inspection, and replacement of wear parts. Performance testing and documentation.",
            "schedule_type": "preventive",
            "interval_days": int(365 * interval_multiplier),
            "priority": "Critical",
            "estimated_hours": 8.0
        }
    ]


@router.post("/{asset_id}/pm-schedule")
async def create_pm_schedule(
    asset_id: str,
    request: Request,
    current_user: User = Depends(require_permission_cookie("update_asset")),
):
    """Create a new PM schedule for an asset."""
    firestore_manager = get_firestore_manager()

    # Verify asset exists and belongs to user's organization
    asset = await firestore_manager.get_org_asset(asset_id, current_user.organization_id)
    if not asset:
        return JSONResponse({"success": False, "error": "Asset not found"}, status_code=404)

    try:
        data = await request.json()

        pm_data = {
            "asset_id": asset_id,
            "organization_id": current_user.organization_id,
            "title": data.get("title"),
            "description": data.get("description", ""),
            "schedule_type": data.get("schedule_type", "time_based"),
            "priority": data.get("priority", "Medium"),
            "interval_days": data.get("interval_days"),
            "interval_hours": data.get("interval_hours"),
            "next_due_date": data.get("next_due_date"),
            "estimated_hours": data.get("estimated_hours"),
            "checklist": data.get("checklist", []),
            "is_active": True,
            "created_by": current_user.uid,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        pm_id = await firestore_manager.create_document("pm_schedule_rules", pm_data)

        # Also create a work order for this PM if it has a due date
        work_order_id = None
        if pm_data.get("next_due_date"):
            # Convert due_date string to datetime if needed
            due_date_val = pm_data.get("next_due_date")
            if isinstance(due_date_val, str):
                try:
                    due_date_val = datetime.strptime(due_date_val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    due_date_val = None

            work_order_data = {
                "organization_id": current_user.organization_id,
                "title": f"[PM] {pm_data['title']}",
                "description": pm_data.get("description", "") + (
                    f"\n\nChecklist:\n" + "\n".join(f"• {item}" for item in pm_data.get("checklist", []))
                    if pm_data.get("checklist") else ""
                ),
                "work_order_type": "Preventive",  # Must match WorkOrder model field name
                "status": "Open",
                "priority": pm_data.get("priority", "Medium"),
                "asset_id": asset_id,
                "asset_name": asset.get("name", ""),
                "pm_schedule_id": pm_id,
                "due_date": due_date_val,
                "estimated_hours": pm_data.get("estimated_hours"),
                "created_by": current_user.uid,
                "created_date": datetime.now(timezone.utc),  # Must match WorkOrder model
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            work_order_id = await firestore_manager.create_document("work_orders", work_order_data)
            logger.info(f"Created work order {work_order_id} for PM {pm_id}")

        return JSONResponse({
            "success": True,
            "pm_id": pm_id,
            "work_order_id": work_order_id,
            "message": "PM schedule created" + (" with work order" if work_order_id else "")
        })

    except Exception as e:
        logger.error(f"Error creating PM schedule: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.delete("/{asset_id}/pm-schedule/{pm_id}")
async def delete_pm_schedule(
    asset_id: str,
    pm_id: str,
    current_user: User = Depends(require_permission_cookie("update_asset")),
):
    """Delete a PM schedule."""
    firestore_manager = get_firestore_manager()

    try:
        # Verify PM belongs to this asset and organization
        pm = await firestore_manager.get_document("pm_schedule_rules", pm_id)
        if not pm or pm.get("asset_id") != asset_id:
            return JSONResponse({"success": False, "error": "PM schedule not found"}, status_code=404)

        if pm.get("organization_id") != current_user.organization_id:
            return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=403)

        await firestore_manager.delete_document("pm_schedule_rules", pm_id)

        return JSONResponse({
            "success": True,
            "message": "PM schedule deleted successfully"
        })

    except Exception as e:
        logger.error(f"Error deleting PM schedule: {e}")
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
