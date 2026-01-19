"""
Zapier Integration Router for ChatterFix CMMS

Provides REST API endpoints for:
- Triggers: Webhook subscriptions that notify Zapier when events occur
- Actions: API endpoints that Zapier calls to create/update data
- Searches: API endpoints that Zapier uses to find records

Authentication: API key in X-API-Key header
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field, HttpUrl

from app.auth import get_current_user_from_cookie
from app.core.db_adapter import get_db_adapter
from app.services.zapier_service import (
    ZapierEventType,
    ZapierService,
    get_zapier_service,
    set_zapier_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/zapier", tags=["Zapier Integration"])


# ==================== Models ====================

class SubscriptionCreate(BaseModel):
    """Request to create a webhook subscription"""
    event_type: ZapierEventType
    webhook_url: HttpUrl


class SubscriptionResponse(BaseModel):
    """Response when subscription is created"""
    subscription_id: str
    event_type: str
    webhook_url: str
    api_key: Optional[str] = None  # Only on creation
    message: str


class WorkOrderCreate(BaseModel):
    """Zapier action: Create a work order"""
    title: str
    description: Optional[str] = ""
    priority: str = "Medium"
    work_order_type: str = "Corrective"
    asset_id: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    due_date: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    """Zapier action: Update a work order"""
    work_order_id: str
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    work_summary: Optional[str] = None


class AssetCreate(BaseModel):
    """Zapier action: Create an asset"""
    name: str
    asset_tag: Optional[str] = None
    asset_type: str = "Equipment"
    location: Optional[str] = None
    status: str = "operational"
    criticality: str = "Medium"


class PartCreate(BaseModel):
    """Zapier action: Create an inventory part"""
    name: str
    part_number: Optional[str] = None
    current_stock: int = 0
    minimum_stock: int = 0
    unit_cost: Optional[float] = None
    location: Optional[str] = None


# ==================== Authentication ====================

async def verify_zapier_api_key(
    x_api_key: str = Header(..., description="Zapier API Key"),
    x_organization_id: str = Header(..., description="Organization ID"),
) -> Dict[str, str]:
    """
    Verify Zapier API key from headers.
    Returns organization_id if valid.
    """
    if not x_api_key or not x_api_key.startswith("zk_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    # For now, we trust the API key format
    # In production, you'd verify against stored hashes
    return {
        "organization_id": x_organization_id,
        "api_key": x_api_key
    }


# ==================== Trigger Endpoints (Webhook Subscriptions) ====================

@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    request: Request,
    current_user=Depends(get_current_user_from_cookie)
):
    """
    Subscribe to ChatterFix events (Zapier Trigger).

    Creates a webhook subscription that will POST to your URL whenever
    the specified event occurs. Returns an API key for authentication.

    **Available Events:**
    - `work_order.created` - New work order created
    - `work_order.completed` - Work order marked complete
    - `work_order.status_changed` - Status changed (Open → In Progress, etc.)
    - `asset.created` - New asset added
    - `asset.critical` - Asset marked critical condition
    - `pm.due` - Preventive maintenance is due
    - `part.low_stock` - Part below minimum stock level
    - `safety.incident` - Safety incident reported
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    organization_id = current_user.organization_id
    if not organization_id:
        raise HTTPException(status_code=400, detail="Organization required")

    service = get_zapier_service()

    # Initialize service with Firestore if not already
    if service.firestore_manager is None:
        db = await get_db_adapter()
        service.firestore_manager = db

    result = await service.create_subscription(
        organization_id=organization_id,
        event_type=subscription.event_type,
        webhook_url=str(subscription.webhook_url)
    )

    return SubscriptionResponse(
        subscription_id=result["subscription"]["id"],
        event_type=result["subscription"]["event_type"],
        webhook_url=result["subscription"]["webhook_url"],
        api_key=result["api_key"],
        message=result["message"]
    )


@router.get("/subscriptions")
async def list_subscriptions(
    request: Request,
    current_user=Depends(get_current_user_from_cookie)
):
    """List all webhook subscriptions for your organization"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    organization_id = current_user.organization_id
    if not organization_id:
        raise HTTPException(status_code=400, detail="Organization required")

    service = get_zapier_service()

    if service.firestore_manager is None:
        db = await get_db_adapter()
        service.firestore_manager = db

    subscriptions = await service.get_subscriptions(organization_id)

    return {
        "subscriptions": [
            {
                "id": sub.id,
                "event_type": sub.event_type,
                "webhook_url": sub.webhook_url,
                "is_active": sub.is_active,
                "created_at": sub.created_at,
                "last_triggered": sub.last_triggered,
                "trigger_count": sub.trigger_count
            }
            for sub in subscriptions
        ]
    }


@router.delete("/subscribe/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    auth: Dict = Depends(verify_zapier_api_key)
):
    """Delete a webhook subscription (requires API key)"""
    service = get_zapier_service()

    if service.firestore_manager is None:
        db = await get_db_adapter()
        service.firestore_manager = db

    success = await service.delete_subscription(
        subscription_id=subscription_id,
        organization_id=auth["organization_id"],
        api_key=auth["api_key"]
    )

    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found or unauthorized")

    return {"success": True, "message": "Subscription deleted"}


# ==================== Action Endpoints (Zapier → ChatterFix) ====================

@router.post("/actions/work-order")
async def create_work_order_action(
    work_order: WorkOrderCreate,
    auth: Dict = Depends(verify_zapier_api_key)
):
    """
    Create a work order from Zapier.

    Use this action to create work orders from other apps like:
    - Google Forms submissions
    - Slack messages
    - Email triggers
    - Calendar events
    """
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    wo_data = {
        "organization_id": organization_id,
        "title": work_order.title,
        "description": work_order.description or "",
        "priority": work_order.priority,
        "work_order_type": work_order.work_order_type,
        "status": "Open",
        "source": "zapier",
        "asset_id": work_order.asset_id,
        "assigned_to_uid": work_order.assigned_to_uid,
        "due_date": work_order.due_date,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Remove None values
    wo_data = {k: v for k, v in wo_data.items() if v is not None}

    doc_ref = await db.create_document("work_orders", wo_data)

    logger.info(f"Zapier created work order: {doc_ref}")

    return {
        "success": True,
        "work_order_id": doc_ref,
        "title": work_order.title,
        "status": "Open",
        "message": "Work order created successfully"
    }


@router.patch("/actions/work-order")
async def update_work_order_action(
    update: WorkOrderUpdate,
    auth: Dict = Depends(verify_zapier_api_key)
):
    """
    Update a work order from Zapier.

    Use this to update status, assignment, or add notes from other apps.
    """
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    # Verify work order exists and belongs to org
    wo = await db.get_document("work_orders", update.work_order_id)
    if not wo or wo.get("organization_id") != organization_id:
        raise HTTPException(status_code=404, detail="Work order not found")

    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if update.status:
        update_data["status"] = update.status
        if update.status == "Completed":
            update_data["completed_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if update.priority:
        update_data["priority"] = update.priority

    if update.assigned_to_uid:
        update_data["assigned_to_uid"] = update.assigned_to_uid

    if update.work_summary:
        update_data["work_summary"] = update.work_summary

    await db.update_document("work_orders", update.work_order_id, update_data)

    logger.info(f"Zapier updated work order: {update.work_order_id}")

    return {
        "success": True,
        "work_order_id": update.work_order_id,
        "updated_fields": list(update_data.keys()),
        "message": "Work order updated successfully"
    }


@router.post("/actions/asset")
async def create_asset_action(
    asset: AssetCreate,
    auth: Dict = Depends(verify_zapier_api_key)
):
    """
    Create an asset from Zapier.

    Use this to automatically add equipment from:
    - Purchase orders
    - Inventory systems
    - Spreadsheet imports
    """
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    asset_data = {
        "organization_id": organization_id,
        "name": asset.name,
        "asset_tag": asset.asset_tag,
        "asset_type": asset.asset_type,
        "location": asset.location or "",
        "status": asset.status,
        "criticality": asset.criticality,
        "source": "zapier",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    asset_data = {k: v for k, v in asset_data.items() if v is not None}

    doc_ref = await db.create_document("assets", asset_data)

    logger.info(f"Zapier created asset: {doc_ref}")

    return {
        "success": True,
        "asset_id": doc_ref,
        "name": asset.name,
        "message": "Asset created successfully"
    }


@router.post("/actions/part")
async def create_part_action(
    part: PartCreate,
    auth: Dict = Depends(verify_zapier_api_key)
):
    """
    Create an inventory part from Zapier.

    Use this to sync inventory from:
    - Purchase orders
    - Supplier systems
    - Barcode scans
    """
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    part_data = {
        "organization_id": organization_id,
        "name": part.name,
        "part_number": part.part_number,
        "current_stock": part.current_stock,
        "minimum_stock": part.minimum_stock,
        "unit_cost": part.unit_cost,
        "location": part.location or "",
        "source": "zapier",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    part_data = {k: v for k, v in part_data.items() if v is not None}

    doc_ref = await db.create_document("parts", part_data)

    logger.info(f"Zapier created part: {doc_ref}")

    return {
        "success": True,
        "part_id": doc_ref,
        "name": part.name,
        "message": "Part created successfully"
    }


@router.post("/actions/maintenance-record")
async def create_maintenance_record_action(
    record: Dict[str, Any],
    auth: Dict = Depends(verify_zapier_api_key)
):
    """
    Log a maintenance record from Zapier.

    Use this to record maintenance from:
    - External technician apps
    - IoT sensor triggers
    - Service provider reports
    """
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    maintenance_data = {
        "organization_id": organization_id,
        "asset_id": record.get("asset_id"),
        "description": record.get("description", "Maintenance performed"),
        "maintenance_type": record.get("maintenance_type", "Corrective"),
        "performed_by": record.get("performed_by"),
        "cost": record.get("cost"),
        "notes": record.get("notes"),
        "source": "zapier",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    maintenance_data = {k: v for k, v in maintenance_data.items() if v is not None}

    doc_ref = await db.create_document("maintenance_history", maintenance_data)

    logger.info(f"Zapier created maintenance record: {doc_ref}")

    return {
        "success": True,
        "record_id": doc_ref,
        "message": "Maintenance record created successfully"
    }


# ==================== Search Endpoints (Zapier Lookups) ====================

@router.get("/search/work-orders")
async def search_work_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(20, le=100),
    auth: Dict = Depends(verify_zapier_api_key)
):
    """
    Search work orders (Zapier Search).

    Use this to find work orders for:
    - Populating dropdowns in other apps
    - Looking up existing records
    - Building reports
    """
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    filters = [
        {"field": "organization_id", "operator": "==", "value": organization_id}
    ]

    if status:
        filters.append({"field": "status", "operator": "==", "value": status})

    if priority:
        filters.append({"field": "priority", "operator": "==", "value": priority})

    work_orders = await db.get_collection(
        "work_orders",
        filters=filters,
        limit=limit,
        order_by="created_at",
        order_direction="desc"
    )

    return {
        "work_orders": [
            {
                "id": wo.get("id"),
                "title": wo.get("title"),
                "status": wo.get("status"),
                "priority": wo.get("priority"),
                "created_at": wo.get("created_at"),
                "due_date": wo.get("due_date"),
            }
            for wo in work_orders
        ]
    }


@router.get("/search/assets")
async def search_assets(
    status: Optional[str] = Query(None, description="Filter by status"),
    asset_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(20, le=100),
    auth: Dict = Depends(verify_zapier_api_key)
):
    """Search assets (Zapier Search)"""
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    filters = [
        {"field": "organization_id", "operator": "==", "value": organization_id}
    ]

    if status:
        filters.append({"field": "status", "operator": "==", "value": status})

    if asset_type:
        filters.append({"field": "asset_type", "operator": "==", "value": asset_type})

    assets = await db.get_collection(
        "assets",
        filters=filters,
        limit=limit,
        order_by="name",
        order_direction="asc"
    )

    return {
        "assets": [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "asset_tag": a.get("asset_tag"),
                "status": a.get("status"),
                "location": a.get("location"),
            }
            for a in assets
        ]
    }


@router.get("/search/parts")
async def search_parts(
    low_stock: bool = Query(False, description="Only parts below minimum"),
    limit: int = Query(20, le=100),
    auth: Dict = Depends(verify_zapier_api_key)
):
    """Search inventory parts (Zapier Search)"""
    db = await get_db_adapter()
    organization_id = auth["organization_id"]

    filters = [
        {"field": "organization_id", "operator": "==", "value": organization_id}
    ]

    parts = await db.get_collection(
        "parts",
        filters=filters,
        limit=limit,
        order_by="name",
        order_direction="asc"
    )

    # Filter low stock if requested
    if low_stock:
        parts = [
            p for p in parts
            if p.get("current_stock", 0) <= p.get("minimum_stock", 0)
        ]

    return {
        "parts": [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "part_number": p.get("part_number"),
                "current_stock": p.get("current_stock"),
                "minimum_stock": p.get("minimum_stock"),
            }
            for p in parts
        ]
    }


# ==================== Test/Sample Endpoints ====================

@router.post("/test/trigger")
async def test_trigger(
    event_type: ZapierEventType,
    request: Request,
    current_user=Depends(get_current_user_from_cookie)
):
    """
    Test a trigger by dispatching a sample event to all subscribers.

    Use this to verify your Zapier webhook is receiving events correctly.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    organization_id = current_user.organization_id
    if not organization_id:
        raise HTTPException(status_code=400, detail="Organization required")

    service = get_zapier_service()

    if service.firestore_manager is None:
        db = await get_db_adapter()
        service.firestore_manager = db

    sample_data = {
        "test": True,
        "message": "This is a test event from ChatterFix",
        "triggered_by": current_user.email,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    result = await service.dispatch_event(
        organization_id=organization_id,
        event_type=event_type,
        data=sample_data
    )

    return {
        "success": True,
        "event_type": event_type,
        "dispatched_to": result["dispatched"],
        "successful": result.get("successful", 0),
        "message": f"Test event sent to {result['dispatched']} webhook(s)"
    }


@router.get("/events")
async def list_available_events():
    """List all available events for Zapier triggers"""
    return {
        "events": [
            {
                "type": e.value,
                "name": e.name.replace("_", " ").title(),
                "description": _get_event_description(e)
            }
            for e in ZapierEventType
        ]
    }


def _get_event_description(event: ZapierEventType) -> str:
    """Get human-readable description for event type"""
    descriptions = {
        ZapierEventType.WORK_ORDER_CREATED: "Triggered when a new work order is created",
        ZapierEventType.WORK_ORDER_UPDATED: "Triggered when a work order is modified",
        ZapierEventType.WORK_ORDER_COMPLETED: "Triggered when a work order is marked complete",
        ZapierEventType.WORK_ORDER_STATUS_CHANGED: "Triggered when work order status changes",
        ZapierEventType.WORK_ORDER_ASSIGNED: "Triggered when a work order is assigned to someone",
        ZapierEventType.WORK_ORDER_OVERDUE: "Triggered when a work order becomes overdue",
        ZapierEventType.ASSET_CREATED: "Triggered when a new asset is added",
        ZapierEventType.ASSET_UPDATED: "Triggered when an asset is modified",
        ZapierEventType.ASSET_STATUS_CHANGED: "Triggered when asset status changes",
        ZapierEventType.ASSET_CRITICAL: "Triggered when an asset becomes critical",
        ZapierEventType.PM_DUE: "Triggered when preventive maintenance is due",
        ZapierEventType.PM_OVERDUE: "Triggered when preventive maintenance is overdue",
        ZapierEventType.PM_COMPLETED: "Triggered when preventive maintenance is completed",
        ZapierEventType.PART_LOW_STOCK: "Triggered when a part falls below minimum stock",
        ZapierEventType.PART_OUT_OF_STOCK: "Triggered when a part reaches zero stock",
        ZapierEventType.SAFETY_INCIDENT: "Triggered when a safety incident is reported",
        ZapierEventType.SAFETY_HAZARD_DETECTED: "Triggered when AI detects a safety hazard",
    }
    return descriptions.get(event, "Event trigger")
