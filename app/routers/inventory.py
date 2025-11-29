from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.database import get_db_connection
import sqlite3
import shutil
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directory exists
UPLOAD_DIR = "app/static/uploads/parts"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(request: Request):
    """Render the inventory list"""
    conn = get_db_connection()
    parts = conn.execute(
        """
        SELECT p.*, v.name as vendor_name 
        FROM parts p 
        LEFT JOIN vendors v ON p.vendor_id = v.id 
        ORDER BY p.name
    """
    ).fetchall()
    conn.close()
    return templates.TemplateResponse(
        "inventory/list.html", {"request": request, "parts": parts}
    )


@router.get("/inventory/add", response_class=HTMLResponse)
async def add_part_form(request: Request):
    """Render the add part form"""
    conn = get_db_connection()
    vendors = conn.execute("SELECT * FROM vendors ORDER BY name").fetchall()
    conn.close()
    return templates.TemplateResponse(
        "inventory/add.html", {"request": request, "vendors": vendors}
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
    vendor_id: int = Form(None),
    files: list[UploadFile] = File(None),
):
    """Add a new part to inventory"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO parts (name, part_number, category, description, current_stock, minimum_stock, location, unit_cost, vendor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                name,
                part_number,
                category,
                description,
                current_stock,
                minimum_stock,
                location,
                unit_cost,
                vendor_id,
            ),
        )

        part_id = cursor.lastrowid

        # Handle file uploads
        if files:
            part_dir = os.path.join(UPLOAD_DIR, str(part_id))
            os.makedirs(part_dir, exist_ok=True)

            for file in files:
                if file.filename:
                    file_path = os.path.join(part_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)

                    rel_path = f"/static/uploads/parts/{part_id}/{file.filename}"
                    file_type = (
                        "image"
                        if file.content_type.startswith("image/")
                        else "document"
                    )

                    # If it's the first image, set it as the main image_url for the part
                    if file_type == "image":
                        # Check if part already has an image
                        current_image = conn.execute(
                            "SELECT image_url FROM parts WHERE id = ?", (part_id,)
                        ).fetchone()[0]
                        if not current_image:
                            conn.execute(
                                "UPDATE parts SET image_url = ? WHERE id = ?",
                                (rel_path, part_id),
                            )

                    conn.execute(
                        """
                        INSERT INTO part_media (part_id, file_path, file_type, title, description)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            part_id,
                            rel_path,
                            file_type,
                            file.filename,
                            "Uploaded during creation",
                        ),
                    )

        conn.commit()
    except sqlite3.IntegrityError:
        # Handle duplicate part number
        pass  # In a real app, show error
    finally:
        conn.close()

    return RedirectResponse(url="/inventory", status_code=303)


@router.get("/inventory/{part_id}", response_class=HTMLResponse)
async def part_detail(request: Request, part_id: int):
    """Render part details"""
    conn = get_db_connection()
    part = conn.execute(
        """
        SELECT p.*, v.name as vendor_name, v.phone as vendor_phone, v.email as vendor_email
        FROM parts p 
        LEFT JOIN vendors v ON p.vendor_id = v.id 
        WHERE p.id = ?
    """,
        (part_id,),
    ).fetchone()

    if not part:
        conn.close()
        return RedirectResponse(url="/inventory")

    media = conn.execute(
        "SELECT * FROM part_media WHERE part_id = ? ORDER BY uploaded_date DESC",
        (part_id,),
    ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "inventory/detail.html", {"request": request, "part": part, "media": media}
    )


@router.post("/inventory/{part_id}/media")
async def upload_part_media(
    part_id: int,
    file: UploadFile = File(...),
    file_type: str = Form("image"),
    title: str = Form(""),
    description: str = Form(""),
):
    """Upload media for part"""
    # Create part-specific directory
    part_dir = os.path.join(UPLOAD_DIR, str(part_id))
    os.makedirs(part_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(part_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store in database
    rel_path = f"/static/uploads/parts/{part_id}/{file.filename}"

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO part_media (part_id, file_path, file_type, title, description)
        VALUES (?, ?, ?, ?, ?)
    """,
        (part_id, rel_path, file_type, title, description),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(f"/inventory/{part_id}", status_code=303)


# Vendor Routes
@router.get("/vendors", response_class=HTMLResponse)
async def vendor_list(request: Request):
    """Render vendor list"""
    conn = get_db_connection()
    vendors = conn.execute("SELECT * FROM vendors ORDER BY name").fetchall()
    conn.close()
    return templates.TemplateResponse(
        "inventory/vendors.html", {"request": request, "vendors": vendors}
    )


@router.post("/vendors/add")
async def add_vendor(
    name: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
):
    """Add a new vendor"""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO vendors (name, contact_name, email, phone) VALUES (?, ?, ?, ?)",
        (name, contact_name, email, phone),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/vendors", status_code=303)
