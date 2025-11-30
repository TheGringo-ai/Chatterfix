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
UPLOAD_DIR = "app/static/uploads/work_orders"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/work-orders", response_class=HTMLResponse)
async def work_orders_list(request: Request):
    """Render the work orders list"""
    conn = get_db_connection()
    work_orders = conn.execute(
        """
        SELECT wo.*, a.image_url as asset_image_url
        FROM work_orders wo
        LEFT JOIN assets a ON wo.asset_id = a.id
        ORDER BY wo.created_date DESC
    """
    ).fetchall()
    conn.close()
    return templates.TemplateResponse(
        "work_orders.html", {"request": request, "work_orders": work_orders}
    )


@router.get("/work-orders/{wo_id}", response_class=HTMLResponse)
async def work_order_detail(request: Request, wo_id: int):
    """Render work order details"""
    conn = get_db_connection()
    wo = conn.execute("SELECT * FROM work_orders WHERE id = ?", (wo_id,)).fetchone()

    if not wo:
        conn.close()
        return RedirectResponse(url="/work-orders")

    media = conn.execute(
        "SELECT * FROM work_order_media WHERE work_order_id = ? ORDER BY uploaded_date DESC",
        (wo_id,),
    ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "work_order_detail.html", {"request": request, "wo": wo, "media": media}
    )


@router.post("/work-orders/{wo_id}/media")
async def upload_wo_media(
    wo_id: int,
    file: UploadFile = File(...),
    file_type: str = Form("image"),
    title: str = Form(""),
    description: str = Form(""),
):
    """Upload media for work order"""
    # Create wo-specific directory
    wo_dir = os.path.join(UPLOAD_DIR, str(wo_id))
    os.makedirs(wo_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(wo_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store in database
    # Use relative path for serving
    rel_path = f"/static/uploads/work_orders/{wo_id}/{file.filename}"

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO work_order_media (work_order_id, file_path, file_type, title, description)
        VALUES (?, ?, ?, ?, ?)
    """,
        (wo_id, rel_path, file_type, title, description),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(f"/work-orders/{wo_id}", status_code=303)


@router.post("/work-orders")
async def create_work_order(
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    assigned_to: str = Form(...),
    due_date: str = Form(...),
):
    """Create a new work order"""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO work_orders (title, description, priority, assigned_to, due_date) VALUES (?, ?, ?, ?, ?)",
        (title, description, priority, assigned_to, due_date),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/work-orders", status_code=303)


@router.post("/work-orders/{wo_id}/complete")
async def complete_work_order(wo_id: int):
    """Mark a work order as completed"""
    conn = get_db_connection()
    conn.execute("UPDATE work_orders SET status = 'Completed' WHERE id = ?", (wo_id,))
    conn.commit()
    conn.close()
    # Redirect to detail view if we are there, or list view
    return RedirectResponse(url=f"/work-orders", status_code=303)


@router.post("/work-orders/{wo_id}/update")
async def update_work_order(
    wo_id: int,
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    assigned_to: str = Form(...),
    due_date: str = Form(...),
):
    """Update an existing work order"""
    conn = get_db_connection()
    conn.execute(
        "UPDATE work_orders SET title = ?, description = ?, priority = ?, assigned_to = ?, due_date = ? WHERE id = ?",
        (title, description, priority, assigned_to, due_date, wo_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/work-orders/{wo_id}", status_code=303)
