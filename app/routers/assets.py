from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
# # from app.core.database import get_db_connection
from app.core.db_adapter import get_db_adapter
from app.services.gemini_service import gemini_service
from app.services.media_service import media_service
import shutil
import os
from datetime import datetime
import json
from typing import List, Dict, Any

router = APIRouter(prefix="/assets", tags=["assets"])
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directory exists
UPLOAD_DIR = "app/static/uploads/assets"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def assets_list(request: Request):
    """Display all assets with filtering"""
    conn = get_db_connection()

    # Get all assets with parent asset names
    assets = conn.execute(
        """
        SELECT a.*, p.name as parent_name
        FROM assets a
        LEFT JOIN assets p ON a.parent_asset_id = p.id
        ORDER BY a.criticality DESC, a.name
    """
    ).fetchall()

    # Get summary stats
    stats = {
        "total": len(assets),
        "active": len([a for a in assets if a["status"] == "Active"]),
        "critical": len([a for a in assets if a["criticality"] == "Critical"]),
        "maintenance_due": len(
            [
                a
                for a in assets
                if a["next_service_date"]
                and a["next_service_date"] <= datetime.now().strftime("%Y-%m-%d")
            ]
        ),
    }

    conn.close()
    return templates.TemplateResponse(
        "assets_list.html", {"request": request, "assets": assets, "stats": stats}
    )


@router.get("/{asset_id}", response_class=HTMLResponse)
async def asset_detail(request: Request, asset_id: int):
    """Comprehensive asset detail view"""
    conn = get_db_connection()

    # Get asset details
    asset = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if not asset:
        conn.close()
        return RedirectResponse("/assets")

    # Get child assets
    children = conn.execute(
        "SELECT * FROM assets WHERE parent_asset_id = ?", (asset_id,)
    ).fetchall()

    # Get media
    media = conn.execute(
        "SELECT * FROM asset_media WHERE asset_id = ? ORDER BY uploaded_date DESC",
        (asset_id,),
    ).fetchall()

    # Get associated parts
    parts = conn.execute(
        """
        SELECT p.*, ap.quantity_used, ap.last_replaced, ap.replacement_interval_days
        FROM parts p
        JOIN asset_parts ap ON p.id = ap.part_id
        WHERE ap.asset_id = ?
    """,
        (asset_id,),
    ).fetchall()

    # Get maintenance history
    history = conn.execute(
        """
        SELECT * FROM maintenance_history
        WHERE asset_id = ?
        ORDER BY created_date DESC
        LIMIT 50
    """,
        (asset_id,),
    ).fetchall()

    # Get related work orders
    work_orders = conn.execute(
        """
        SELECT wo.* FROM work_orders wo
        JOIN maintenance_history mh ON wo.id = mh.work_order_id
        WHERE mh.asset_id = ?
        GROUP BY wo.id
        ORDER BY wo.created_date DESC
    """,
        (asset_id,),
    ).fetchall()

    # Calculate cost analytics
    cost_data = conn.execute(
        """
        SELECT
            SUM(total_cost) as total_cost,
            SUM(labor_cost) as labor_cost,
            SUM(parts_cost) as parts_cost,
            SUM(downtime_hours) as total_downtime
        FROM maintenance_history
        WHERE asset_id = ?
    """,
        (asset_id,),
    ).fetchone()

    conn.close()

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
    parent_asset_id: int = Form(None),
    status: str = Form("Active"),
    criticality: str = Form("Medium"),
    purchase_date: str = Form(None),
    warranty_expiry: str = Form(None),
    purchase_cost: float = Form(None),
    files: list[UploadFile] = File(None),
):
    """Create a new asset"""
    conn = get_db_connection()

    cursor = conn.execute(
        """
        INSERT INTO assets (
            name, description, asset_tag, serial_number, model, manufacturer,
            location, department, parent_asset_id, status, criticality,
            purchase_date, warranty_expiry, purchase_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            name,
            description,
            asset_tag,
            serial_number,
            model,
            manufacturer,
            location,
            department,
            parent_asset_id,
            status,
            criticality,
            purchase_date,
            warranty_expiry,
            purchase_cost,
        ),
    )

    asset_id = cursor.lastrowid

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
                    "image" if file.content_type.startswith("image/") else "document"
                )

                conn.execute(
                    """
                    INSERT INTO asset_media (asset_id, file_path, file_type, title, description)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        asset_id,
                        rel_path,
                        file_type,
                        file.filename,
                        "Uploaded during creation",
                    ),
                )

    conn.commit()
    conn.close()

    return RedirectResponse(f"/assets/{asset_id}", status_code=303)


@router.post("/{asset_id}/media")
async def upload_media(
    asset_id: int,
    file: UploadFile = File(...),
    file_type: str = Form("image"),
    title: str = Form(""),
    description: str = Form(""),
):
    """Upload photo, video, or document"""
    # Create asset-specific directory
    asset_dir = os.path.join(UPLOAD_DIR, str(asset_id))
    os.makedirs(asset_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(asset_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store in database
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO asset_media (asset_id, file_path, file_type, title, description)
        VALUES (?, ?, ?, ?, ?)
    """,
        (asset_id, file_path, file_type, title, description),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(f"/assets/{asset_id}", status_code=303)


@router.post("/{asset_id}/maintenance")
async def log_maintenance(
    asset_id: int,
    maintenance_type: str = Form(...),
    description: str = Form(""),
    technician: str = Form(""),
    downtime_hours: float = Form(0),
    labor_cost: float = Form(0),
    parts_cost: float = Form(0),
):
    """Log a maintenance event"""
    total_cost = labor_cost + parts_cost

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO maintenance_history (
            asset_id, maintenance_type, description, technician,
            downtime_hours, labor_cost, parts_cost, total_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            asset_id,
            maintenance_type,
            description,
            technician,
            downtime_hours,
            labor_cost,
            parts_cost,
            total_cost,
        ),
    )

    # Update asset totals
    conn.execute(
        """
        UPDATE assets
        SET total_downtime_hours = total_downtime_hours + ?,
            total_maintenance_cost = total_maintenance_cost + ?,
            last_service_date = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (downtime_hours, total_cost, asset_id),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(f"/assets/{asset_id}", status_code=303)


@router.get("/{asset_id}/ai-health")
async def ai_health_analysis(asset_id: int):
    """AI-powered health analysis"""
    if not gemini_service.model:
        return JSONResponse({"health_score": 0, "analysis": "AI unavailable"})

    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    history = conn.execute(
        """
        SELECT * FROM maintenance_history
        WHERE asset_id = ?
        ORDER BY created_date DESC
        LIMIT 10
    """,
        (asset_id,),
    ).fetchall()
    conn.close()

    # Prepare context for AI
    context = f"""
    Analyze the health of this asset and provide a health score (0-100) and brief analysis.

    Asset: {asset['name']}
    Model: {asset['model']}
    Age: Installed {asset['installation_date']}
    Total Downtime: {asset['total_downtime_hours']} hours
    Total Maintenance Cost: ${asset['total_maintenance_cost']}
    Recent Maintenance Events: {len(history)}
    Criticality: {asset['criticality']}

    Provide response as JSON: {{"health_score": <0-100>, "risk_level": "<Low/Medium/High>", "analysis": "<brief analysis>", "recommendations": ["<rec1>", "<rec2>"]}}
    """

    try:
        response = await gemini_service.generate_response(context)
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
async def ai_recommendations(asset_id: int):
    """AI predictive maintenance recommendations"""
    if not gemini_service.model:
        return JSONResponse({"recommendations": []})

    conn = get_db_connection()
    asset = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    parts = conn.execute(
        """
        SELECT p.name, ap.last_replaced, ap.replacement_interval_days
        FROM parts p
        JOIN asset_parts ap ON p.id = ap.part_id
        WHERE ap.asset_id = ?
    """,
        (asset_id,),
    ).fetchall()
    conn.close()

    prompt = f"""
    Provide predictive maintenance recommendations for this asset.

    Asset: {asset['name']} ({asset['model']})
    Last Service: {asset['last_service_date']}
    Next Service: {asset['next_service_date']}
    Associated Parts: {len(parts)}

    Return JSON array of recommendations with priority and estimated cost.
    """

    try:
        response = await gemini_service.generate_response(prompt)
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
async def scan_asset_barcode(file: UploadFile = File(...)):
    """Scan barcode to find asset and related information"""
    try:
        if not file.filename:
            return JSONResponse({"success": False, "error": "No file provided"}, status_code=400)

        # Read and scan barcode
        image_data = await file.read()
        barcodes = await media_service.scan_barcode_from_image(image_data)
        
        if not barcodes:
            return JSONResponse({"success": False, "error": "No barcode found in image"}, status_code=400)
        
        # Get the first barcode
        barcode_data = barcodes[0]["data"]
        
        # Look up asset by barcode (asset_tag, serial_number, or name)
        db_adapter = get_db_adapter()
        
        # First try to find by asset_tag
        asset = await db_adapter.get_asset_by_tag(barcode_data)
        
        if not asset:
            # Try by serial number or partial name match
            asset = await db_adapter.find_asset_by_identifier(barcode_data)
        
        if asset:
            # Get related information
            work_orders = await db_adapter.get_asset_work_orders(asset["id"])
            parts = await db_adapter.get_asset_parts(asset["id"])
            
            return JSONResponse({
                "success": True,
                "barcode_data": barcode_data,
                "asset": asset,
                "work_orders": work_orders[:5],  # Latest 5 work orders
                "parts": parts,
                "scan_result": "asset_found"
            })
        else:
            return JSONResponse({
                "success": True,
                "barcode_data": barcode_data,
                "asset": None,
                "work_orders": [],
                "parts": [],
                "scan_result": "no_asset_found",
                "message": f"No asset found with identifier: {barcode_data}"
            })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/lookup-by-tag")
async def lookup_asset_by_tag(asset_tag: str = Form(...)):
    """Quick lookup of asset by tag/barcode"""
    try:
        db_adapter = get_db_adapter()
        asset = await db_adapter.get_asset_by_tag(asset_tag)
        
        if asset:
            # Get summary info
            work_orders_count = await db_adapter.count_asset_work_orders(asset["id"])
            parts_count = await db_adapter.count_asset_parts(asset["id"])
            
            return JSONResponse({
                "success": True,
                "asset": asset,
                "work_orders_count": work_orders_count,
                "parts_count": parts_count
            })
        else:
            return JSONResponse({
                "success": False,
                "error": f"Asset not found: {asset_tag}"
            }, status_code=404)
            
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/{asset_id}/generate-qr")
async def generate_asset_qr_code(asset_id: int):
    """Generate QR code for asset"""
    try:
        db_adapter = get_db_adapter()
        asset = await db_adapter.get_asset(asset_id)
        
        if not asset:
            return JSONResponse({"success": False, "error": "Asset not found"}, status_code=404)
        
        # Generate QR code with asset tag or ID
        qr_data = asset.get("asset_tag", f"ASSET-{asset_id}")
        
        barcode_info = await media_service.generate_barcode(
            data=qr_data,
            barcode_type="qr",
            size=(300, 300)
        )
        
        return JSONResponse({
            "success": True,
            "qr_code": barcode_info,
            "asset": asset,
            "qr_data": qr_data
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
