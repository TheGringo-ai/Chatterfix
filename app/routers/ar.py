from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ar-mode", response_class=HTMLResponse)
async def ar_dashboard(request: Request):
    """Render the AR dashboard"""
    return templates.TemplateResponse("ar/dashboard.html", {"request": request})


@router.get("/ar/work-orders", response_class=HTMLResponse)
async def ar_work_orders(request: Request):
    """Render the AR work orders list"""
    conn = get_db_connection()
    work_orders = conn.execute(
        "SELECT * FROM work_orders WHERE status != 'Completed' ORDER BY priority DESC"
    ).fetchall()
    conn.close()
    return templates.TemplateResponse(
        "ar/work_orders.html", {"request": request, "work_orders": work_orders}
    )


@router.get("/ar/work-order/{wo_id}", response_class=HTMLResponse)
async def ar_work_order_detail(request: Request, wo_id: int):
    """Render the AR work order detail"""
    conn = get_db_connection()
    wo = conn.execute("SELECT * FROM work_orders WHERE id = ?", (wo_id,)).fetchone()
    conn.close()

    if not wo:
        return HTMLResponse("<h1>Work Order Not Found</h1>")

    return templates.TemplateResponse(
        "ar/work_order_detail.html", {"request": request, "wo": wo}
    )
