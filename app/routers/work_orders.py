import logging
import os
import shutil
import json
from datetime import datetime

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.core.db_adapter import get_db_adapter
from app.core.firestore_db import get_db_connection, get_firestore_manager
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directory exists
UPLOAD_DIR = "app/static/uploads/work_orders"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/work-orders", response_class=HTMLResponse)
async def work_orders_list(request: Request):
    """Render the work orders list"""
    try:
        db_adapter = get_db_adapter()
        work_orders = []

        if db_adapter.firestore_manager:
            # Get work orders from Firestore
            work_orders_data = await db_adapter.firestore_manager.get_collection(
                "work_orders", order_by="-created_date"  # Descending order
            )

            # Enrich with asset information
            for wo in work_orders_data:
                if wo.get("asset_id"):
                    asset_data = await db_adapter.firestore_manager.get_document(
                        "assets", wo["asset_id"]
                    )
                    if asset_data:
                        wo["asset_image_url"] = asset_data.get("image_url")
                        wo["asset_name"] = asset_data.get("name")

                work_orders.append(wo)
        else:
            logger.warning("Firestore not available for work orders list")

        return templates.TemplateResponse(
            "work_orders.html", {"request": request, "work_orders": work_orders}
        )
    except Exception as e:
        logger.error(f"Failed to load work orders: {e}")
        return templates.TemplateResponse(
            "work_orders.html",
            {
                "request": request,
                "work_orders": [],
                "error": "Failed to load work orders",
            },
        )


@router.get("/work-orders/{wo_id}", response_class=HTMLResponse)
async def work_order_detail(request: Request, wo_id: str):
    """Render work order details"""
    try:
        db_adapter = get_db_adapter()

        if not db_adapter.firestore_manager:
            logger.error("Firestore not available for work order detail")
            return RedirectResponse(url="/work-orders")

        # Get work order from Firestore
        wo = await db_adapter.firestore_manager.get_document("work_orders", wo_id)
        if not wo:
            return RedirectResponse(url="/work-orders")

        # Get media for this work order
        media_data = await db_adapter.firestore_manager.get_collection(
            "work_order_media",
            filters=[{"field": "work_order_id", "operator": "==", "value": wo_id}],
            order_by="-uploaded_date",
        )

        return templates.TemplateResponse(
            "work_order_detail.html",
            {"request": request, "wo": wo, "media": media_data},
        )
    except Exception as e:
        logger.error(f"Failed to load work order detail: {e}")
        return RedirectResponse(url="/work-orders")


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
    asset_id: str = Form(None),
    work_order_type: str = Form("Corrective"),
    scheduled_time: str = Form(None),
    estimated_hours: float = Form(None),
    work_instructions: str = Form(""),
    files: list[UploadFile] = File(None),
):
    """Create a new work order"""
    try:
        db_adapter = get_db_adapter()
        if not db_adapter.firestore_manager:
            logger.error("Firestore not available for work order creation")
            return RedirectResponse(
                url="/work-orders?error=database_unavailable", status_code=303
            )

        # Prepare work order data
        from datetime import datetime

        work_order_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "assigned_to": assigned_to,
            "due_date": due_date,
            "asset_id": asset_id,
            "work_order_type": work_order_type,
            "scheduled_time": scheduled_time,
            "estimated_hours": estimated_hours,
            "work_instructions": work_instructions,
            "status": "Open",
            "created_date": datetime.now().isoformat(),
        }

        # Create work order in Firestore
        wo_id = await db_adapter.firestore_manager.create_document(
            "work_orders", work_order_data
        )
        logger.info(f"Created work order {wo_id}: {title}")

        # Handle file uploads if provided
        media_files = []
        if files:
            wo_dir = os.path.join(UPLOAD_DIR, str(wo_id))
            os.makedirs(wo_dir, exist_ok=True)

            for file in files:
                if file.filename:
                    file_path = os.path.join(wo_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)

                    rel_path = f"/static/uploads/work_orders/{wo_id}/{file.filename}"
                    file_type = (
                        "image"
                        if file.content_type and file.content_type.startswith("image/")
                        else "document"
                    )

                    media_data = {
                        "work_order_id": wo_id,
                        "file_path": rel_path,
                        "file_type": file_type,
                        "title": file.filename,
                        "description": "Uploaded during creation",
                        "uploaded_date": datetime.now().isoformat(),
                    }

                    media_id = await db_adapter.firestore_manager.create_document(
                        "work_order_media", media_data
                    )
                    media_files.append(media_id)

        # Process parts checkout if any parts were selected
        try:
            # Get form data for parts (this would come from the form as parts[0][part_id], etc.)
            # For now, we'll implement the processing logic that can be called from JavaScript
            
            # Extract parts data from request (this is a simplified approach)
            # In a real implementation, you'd parse the form data for parts arrays
            logger.info("Parts checkout processing will be implemented in separate endpoint")
            
        except Exception as e:
            logger.error(f"Error processing parts checkout: {e}")
            # Don't fail the work order creation if parts processing fails

        # Send notification if assigned to someone
        if assigned_to and assigned_to != "unassigned":
            try:
                # Convert assigned_to to user_id if needed (assuming it's user_id)
                technician_id = int(assigned_to) if assigned_to.isdigit() else None
                if technician_id:
                    # Add asset name to work order data if available
                    if asset_id:
                        asset_data = await db_adapter.firestore_manager.get_document(
                            "assets", asset_id
                        )
                        work_order_data["asset_name"] = (
                            asset_data.get("name", "Unknown Asset")
                            if asset_data
                            else "Unknown Asset"
                        )

                    await NotificationService.notify_work_order_assigned(
                        work_order_id=int(wo_id) if wo_id.isdigit() else hash(wo_id),
                        technician_id=technician_id,
                        title=title,
                        work_order_data=work_order_data,
                    )
                    logger.info(f"Sent work order assignment notification for {wo_id}")
            except Exception as e:
                logger.error(f"Failed to send work order notification: {e}")

        return RedirectResponse(url="/work-orders", status_code=303)

    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        return RedirectResponse(
            url="/work-orders?error=creation_failed", status_code=303
        )


@router.post("/work-orders/{wo_id}/parts-checkout")
async def checkout_parts_for_work_order(
    wo_id: str,
    parts_data: str = Form(...),  # JSON string of parts data
):
    """Checkout parts for a work order and deduct from inventory"""
    try:
        db_adapter = get_db_adapter()
        if not db_adapter.firestore_manager:
            return JSONResponse({"success": False, "error": "Database unavailable"}, status_code=500)

        # Parse parts data
        parts_list = json.loads(parts_data)
        
        for part_info in parts_list:
            part_id = part_info.get("part_id")
            quantity = int(part_info.get("quantity", 0))
            
            if not part_id or quantity <= 0:
                continue
                
            # Get current part inventory
            part_doc = await db_adapter.firestore_manager.get_document("parts", part_id)
            if not part_doc:
                logger.warning(f"Part {part_id} not found for checkout")
                continue
                
            current_stock = part_doc.get("current_stock", 0)
            if current_stock < quantity:
                return JSONResponse({
                    "success": False, 
                    "error": f"Insufficient stock for {part_doc.get('name', 'Unknown Part')}. Available: {current_stock}, Requested: {quantity}"
                }, status_code=400)
        
        # If we get here, all parts have sufficient stock - proceed with checkout
        for part_info in parts_list:
            part_id = part_info.get("part_id")
            quantity = int(part_info.get("quantity", 0))
            
            if not part_id or quantity <= 0:
                continue
                
            # Get current stock again (to handle concurrent requests)
            part_doc = await db_adapter.firestore_manager.get_document("parts", part_id)
            current_stock = part_doc.get("current_stock", 0)
            new_stock = max(0, current_stock - quantity)
            
            # Update part inventory
            await db_adapter.firestore_manager.update_document(
                "parts", part_id, {"current_stock": new_stock}
            )
            
            # Create parts checkout record
            checkout_record = {
                "work_order_id": wo_id,
                "part_id": part_id,
                "quantity_checked_out": quantity,
                "checkout_date": datetime.now().isoformat(),
                "part_name": part_doc.get("name", ""),
                "part_number": part_doc.get("part_number", ""),
            }
            await db_adapter.firestore_manager.create_document("work_order_parts_checkout", checkout_record)
        
        logger.info(f"Parts checkout completed for work order {wo_id}")
        return JSONResponse({"success": True, "message": "Parts checked out successfully"})
        
    except Exception as e:
        logger.error(f"Error in parts checkout: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/work-orders/{wo_id}/complete")
async def complete_work_order_basic(wo_id: str):
    """Basic completion endpoint (legacy)"""
    return await complete_work_order_enhanced(
        wo_id=wo_id,
        actual_hours=0,
        completion_time="",
        work_summary="Work order completed",
        asset_status="Operational",
        next_service_date=None,
        follow_up_notes="",
        completion_parts_data="[]",
        files=None
    )


@router.post("/work-orders/{wo_id}/complete-enhanced")
async def complete_work_order_enhanced(
    wo_id: str,
    actual_hours: float = Form(...),
    completion_time: str = Form(...),
    work_summary: str = Form(...),
    asset_status: str = Form("Operational"),
    next_service_date: Optional[str] = Form(None),
    follow_up_notes: str = Form(""),
    completion_parts_data: str = Form("[]"),  # JSON string of parts used
    files: list[UploadFile] = File(None),
):
    """Enhanced work order completion with detailed tracking"""
    try:
        db_adapter = get_db_adapter()

        if not db_adapter.firestore_manager:
            logger.error("Firestore not available for work order completion")
            return RedirectResponse(url="/work-orders", status_code=303)

        # Get work order for notification
        wo = await db_adapter.firestore_manager.get_document("work_orders", wo_id)
        
        # Process parts used during completion
        completion_parts = []
        if completion_parts_data and completion_parts_data != "[]":
            try:
                parts_list = json.loads(completion_parts_data)
                
                for part_info in parts_list:
                    part_id = part_info.get("part_id")
                    quantity_used = int(part_info.get("quantity_used", 0))
                    
                    if not part_id or quantity_used <= 0:
                        continue
                    
                    # Get part info and update inventory
                    part_doc = await db_adapter.firestore_manager.get_document("parts", part_id)
                    if part_doc:
                        current_stock = part_doc.get("current_stock", 0)
                        new_stock = max(0, current_stock - quantity_used)
                        
                        # Update inventory
                        await db_adapter.firestore_manager.update_document(
                            "parts", part_id, {"current_stock": new_stock}
                        )
                        
                        # Record part usage
                        completion_parts.append({
                            "part_id": part_id,
                            "part_name": part_doc.get("name", ""),
                            "part_number": part_doc.get("part_number", ""),
                            "quantity_used": quantity_used,
                            "unit_cost": part_doc.get("unit_cost", 0),
                            "total_cost": quantity_used * part_doc.get("unit_cost", 0)
                        })
                        
                        # Create parts usage record
                        usage_record = {
                            "work_order_id": wo_id,
                            "part_id": part_id,
                            "quantity_used": quantity_used,
                            "usage_date": completion_time or datetime.now().isoformat(),
                            "part_name": part_doc.get("name", ""),
                            "part_number": part_doc.get("part_number", ""),
                            "unit_cost": part_doc.get("unit_cost", 0),
                        }
                        await db_adapter.firestore_manager.create_document("work_order_parts_usage", usage_record)
                        
                        logger.info(f"Used {quantity_used} of part {part_doc.get('name')} in work order {wo_id}")
                        
            except Exception as e:
                logger.error(f"Error processing completion parts: {e}")

        # Handle completion file uploads
        completion_media = []
        if files:
            wo_dir = os.path.join(UPLOAD_DIR, str(wo_id), "completion")
            os.makedirs(wo_dir, exist_ok=True)

            for file in files:
                if file.filename:
                    file_path = os.path.join(wo_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)

                    rel_path = f"/static/uploads/work_orders/{wo_id}/completion/{file.filename}"
                    file_type = (
                        "image"
                        if file.content_type and file.content_type.startswith("image/")
                        else "document"
                    )

                    media_data = {
                        "work_order_id": wo_id,
                        "file_path": rel_path,
                        "file_type": file_type,
                        "title": file.filename,
                        "description": "Completion documentation",
                        "uploaded_date": datetime.now().isoformat(),
                        "upload_stage": "completion"
                    }

                    media_id = await db_adapter.firestore_manager.create_document(
                        "work_order_media", media_data
                    )
                    completion_media.append(media_id)

        # Calculate total parts cost
        total_parts_cost = sum(part["total_cost"] for part in completion_parts)

        # Update work order with comprehensive completion data
        completion_data = {
            "status": "Completed",
            "completed_date": completion_time or datetime.now().isoformat(),
            "actual_hours": actual_hours,
            "work_summary": work_summary,
            "asset_status_after_completion": asset_status,
            "next_service_date": next_service_date,
            "follow_up_notes": follow_up_notes,
            "completion_parts": completion_parts,
            "total_parts_cost": total_parts_cost,
            "completion_media_count": len(completion_media),
            "completed_by": wo.get("assigned_to", "Unknown"),
        }
        
        await db_adapter.firestore_manager.update_document(
            "work_orders", wo_id, completion_data
        )
        
        # Update asset status if asset_id is provided
        if wo.get("asset_id") and asset_status:
            try:
                asset_update = {"status": asset_status}
                if next_service_date:
                    asset_update["next_service_date"] = next_service_date
                
                await db_adapter.firestore_manager.update_document(
                    "assets", wo["asset_id"], asset_update
                )
                logger.info(f"Updated asset {wo['asset_id']} status to {asset_status}")
            except Exception as e:
                logger.error(f"Error updating asset status: {e}")

        logger.info(f"Work order {wo_id} completed successfully with {len(completion_parts)} parts used")

        # Send completion notification if work order has assignment
        if wo and wo.get("assigned_to"):
            try:
                technician_id = (
                    int(wo["assigned_to"]) if wo["assigned_to"].isdigit() else None
                )
                if technician_id:
                    work_order_info = {
                        "id": wo_id,
                        "title": wo.get("title", "Work Order"),
                        "description": wo.get("description", "No description"),
                        "priority": wo.get("priority", "normal"),
                        "asset_name": wo.get("asset_name", "Unknown Asset"),
                    }

                    # Get user data for email
                    user_data = await NotificationService._get_user_data(technician_id)
                    user_email = user_data.get("email")
                    user_name = user_data.get("fullName", "Technician")

                    if user_email:
                        from app.services.email_service import email_service

                        await email_service.send_work_order_notification(
                            to_email=user_email,
                            to_name=user_name,
                            work_order=work_order_info,
                            notification_type="completed",
                        )
                        logger.info(f"Sent work order completion email to {user_email}")

                        # Also send in-app notification
                        await NotificationService.send_notification(
                            user_id=technician_id,
                            notification_type="work_order_completed",
                            title="Work Order Completed",
                            message=f"Work order '{wo.get('title')}' has been completed",
                            link=f"/work-orders/{wo_id}",
                            priority="normal",
                        )

            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")

        return RedirectResponse(url="/work-orders", status_code=303)
    except Exception as e:
        logger.error(f"Failed to complete work order: {e}")
        return RedirectResponse(url="/work-orders", status_code=303)


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


# API endpoints for frontend data loading
@router.get("/api/assets")
async def get_assets_api():
    """Get assets for dropdown population"""
    try:
        db_adapter = get_db_adapter()
        if not db_adapter.firestore_manager:
            return JSONResponse({"assets": []})
            
        assets = await db_adapter.firestore_manager.get_collection("assets", order_by="name")
        return JSONResponse(assets)
        
    except Exception as e:
        logger.error(f"Error fetching assets: {e}")
        return JSONResponse({"assets": []})


@router.get("/api/users")
async def get_users_api(role: str = None):
    """Get users for dropdown population"""
    try:
        db_adapter = get_db_adapter()
        if not db_adapter.firestore_manager:
            # Return mock data if no database available
            return JSONResponse([
                {"id": "1", "full_name": "John Technician", "name": "John Technician"},
                {"id": "2", "full_name": "Jane Maintenance", "name": "Jane Maintenance"},
                {"id": "3", "full_name": "Mike Engineer", "name": "Mike Engineer"},
            ])
            
        # For now, return mock technician data
        # In production, you'd query a users collection with role filtering
        users = [
            {"id": "1", "full_name": "John Technician", "name": "John Technician"},
            {"id": "2", "full_name": "Jane Maintenance", "name": "Jane Maintenance"}, 
            {"id": "3", "full_name": "Mike Engineer", "name": "Mike Engineer"},
        ]
        
        if role == "technician":
            users = [u for u in users if "technician" in u["full_name"].lower() or "maintenance" in u["full_name"].lower() or "engineer" in u["full_name"].lower()]
            
        return JSONResponse(users)
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return JSONResponse([])
