from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.purchasing_service import purchasing_service

router = APIRouter(prefix="/purchasing", tags=["purchasing"])
templates = Jinja2Templates(directory="app/templates")


class ApprovalRequest(BaseModel):
    request_id: int
    approver_id: int
    action: str  # 'approve' or 'deny'
    reason: str = None


@router.get("/", response_class=HTMLResponse)
async def purchasing_dashboard(request: Request):
    """Enhanced purchasing dashboard with media and barcode capabilities"""
    return templates.TemplateResponse("enhanced_purchasing.html", {"request": request})


@router.get("/purchase-orders")
async def get_purchase_orders(status: str = None):
    """Get purchase orders"""
    orders = purchasing_service.get_purchase_orders(status)
    return JSONResponse(content={"purchase_orders": orders})


@router.get("/pending-approvals")
async def get_pending_approvals():
    """Get pending approval requests"""
    approvals = purchasing_service.get_pending_approvals()
    return JSONResponse(content=approvals)


@router.get("/vendor-performance")
async def get_vendor_performance():
    """Get vendor performance metrics"""
    vendors = purchasing_service.get_vendor_performance()
    return JSONResponse(content={"vendors": vendors})


@router.get("/budget-tracking")
async def get_budget_tracking():
    """Get budget tracking data"""
    budget = purchasing_service.get_budget_tracking()
    return JSONResponse(content=budget)


@router.get("/low-stock")
async def get_low_stock():
    """Get low stock alerts"""
    items = purchasing_service.get_low_stock_alerts()
    return JSONResponse(content={"low_stock_items": items})


@router.get("/price-trends")
async def get_price_trends():
    """Get price trends"""
    trends = purchasing_service.get_price_trends()
    return JSONResponse(content=trends)


@router.get("/contract-renewals")
async def get_contract_renewals():
    """Get upcoming contract renewals"""
    renewals = purchasing_service.get_contract_renewals()
    return JSONResponse(content={"renewals": renewals})


@router.get("/spend-analytics")
async def get_spend_analytics(days: int = 30):
    """Get spend analytics"""
    analytics = purchasing_service.get_spend_analytics(days)
    return JSONResponse(content=analytics)


@router.post("/approve")
async def process_approval(approval: ApprovalRequest):
    """Approve or deny a purchase request"""
    if approval.action == "approve":
        success = purchasing_service.approve_purchase_request(
            approval.request_id, approval.approver_id
        )
        message = "Request approved" if success else "Approval failed"
    else:
        success = purchasing_service.deny_purchase_request(
            approval.request_id, approval.reason
        )
        message = "Request denied" if success else "Denial failed"

    return JSONResponse(content={"success": success, "message": message})


@router.get("/summary")
async def get_purchasing_summary():
    """Get comprehensive purchasing summary"""
    approvals = purchasing_service.get_pending_approvals()
    budget = purchasing_service.get_budget_tracking()
    low_stock = purchasing_service.get_low_stock_alerts()
    analytics = purchasing_service.get_spend_analytics(30)

    return JSONResponse(
        content={
            "pending_approvals": approvals["pending_count"],
            "budget_utilization": budget["utilization_percentage"],
            "low_stock_count": len(low_stock),
            "monthly_spend": budget["total_spent"],
            "total_requests": analytics["total_requests"],
        }
    )
