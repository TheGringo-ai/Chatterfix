import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_active_user, require_permission
from app.models.user import User
from app.core.firestore_db import get_firestore_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads/parts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(request: Request, current_user: User = Depends(get_current_active_user)):
    """Render the inventory list"""
    firestore_manager = get_firestore_manager()
    parts = await firestore_manager.get_collection("parts", order_by="name")
    return templates.TemplateResponse(
        "inventory/list.html", {"request": request, "parts": parts, "user": current_user}
    )

@router.get("/inventory/add", response_class=HTMLResponse)
async def add_part_form(request: Request, current_user: User = Depends(require_permission("manage_inventory"))):
    """Render the add part form"""
    firestore_manager = get_firestore_manager()
    vendors = await firestore_manager.get_collection("vendors", order_by="name")
    return templates.TemplateResponse(
        "inventory/add.html", {"request": request, "vendors": vendors, "user": current_user}
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
    """Render part details"""
    firestore_manager = get_firestore_manager()
    part = await firestore_manager.get_document("parts", part_id)
    if not part:
        return RedirectResponse(url="/inventory")
    
    vendor = None
    if part.get("vendor_id"):
        vendor = await firestore_manager.get_document("vendors", part["vendor_id"])

    media = await firestore_manager.get_collection(
        "part_media", filters=[{"field": "part_id", "operator": "==", "value": part_id}]
    )
    
    part["vendor_name"] = vendor.get("name") if vendor else "N/A"

    return templates.TemplateResponse(
        "inventory/detail.html", {"request": request, "part": part, "media": media, "user": current_user}
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
    """Render vendor list"""
    firestore_manager = get_firestore_manager()
    vendors = await firestore_manager.get_collection("vendors", order_by="name")
    return templates.TemplateResponse(
        "inventory/vendors.html", {"request": request, "vendors": vendors, "user": current_user}
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
    await firestore_manager.create_document("vendors", vendor_data)
    return RedirectResponse(url="/vendors", status_code=303)
