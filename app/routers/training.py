"""
Training Router
Handles AI-generated training modules and technician learning
Converted to use Firestore database instead of SQLite
"""

from fastapi import APIRouter, Request, Form, UploadFile, File, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.core.db_adapter import get_db_adapter
from app.core.firestore_db import get_firestore_manager
from app.services.training_generator import training_generator
from app.services.notification_service import notification_service
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])

def get_current_user_from_session(session_token: Optional[str]):
    """Helper to get current user from session token"""
    if not session_token:
        return None
    try:
        if len(session_token) < 10 or session_token == "invalid":
            return None
        return {
            "id": 1,
            "username": "demo_user", 
            "email": "user@demo.com",
            "full_name": "Demo User",
            "role": "technician"
        }
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return None

# Redirect /training (without slash) to /training/ (with slash)
@router.get("", response_class=HTMLResponse)
async def training_center_redirect(request: Request):
    """Redirect /training to /training/ for consistent URL handling"""
    return RedirectResponse(url="/training/", status_code=301)
templates = Jinja2Templates(directory="app/templates")

# ========== FIRESTORE HELPER FUNCTIONS ==========

async def get_user_training_with_modules(firestore_manager, user_id: str) -> List[Dict[str, Any]]:
    """Get user's training assignments with module details"""
    try:
        # Get user training records
        user_training = await firestore_manager.get_collection(
            "user_training",
            filters=[{"field": "user_id", "operator": "==", "value": user_id}]
        )
        
        # Enrich with module details
        enriched_training = []
        for training in user_training:
            module_id = training.get("training_module_id")
            if module_id:
                module = await firestore_manager.get_document("training_modules", module_id)
                if module:
                    training.update({
                        "title": module.get("title"),
                        "description": module.get("description"),
                        "estimated_duration_minutes": module.get("estimated_duration_minutes"),
                        "difficulty_level": module.get("difficulty_level")
                    })
            enriched_training.append(training)
        
        # Sort by status priority and date
        status_order = {"assigned": 1, "in_progress": 2, "completed": 3}
        enriched_training.sort(key=lambda x: (
            status_order.get(x.get("status", "assigned"), 4),
            x.get("started_date") or datetime.min
        ), reverse=True)
        
        return enriched_training
    except Exception as e:
        logger.error(f"Error getting user training with modules: {e}")
        return []

async def get_available_training_modules(firestore_manager, user_id: str) -> List[Dict[str, Any]]:
    """Get training modules not assigned to the user"""
    try:
        # Get all modules
        all_modules = await firestore_manager.get_collection(
            "training_modules",
            order_by="-created_at"
        )
        
        # Get user's assigned modules
        user_training = await firestore_manager.get_collection(
            "user_training",
            filters=[{"field": "user_id", "operator": "==", "value": user_id}]
        )
        
        assigned_module_ids = {t.get("training_module_id") for t in user_training}
        
        # Filter out assigned modules
        available_modules = [
            module for module in all_modules
            if module.get("id") not in assigned_module_ids
        ]
        
        return available_modules
    except Exception as e:
        logger.error(f"Error getting available training modules: {e}")
        return []

async def get_user_training_stats(firestore_manager, user_id: str) -> Dict[str, Any]:
    """Get user training completion statistics"""
    try:
        user_training = await firestore_manager.get_collection(
            "user_training",
            filters=[{"field": "user_id", "operator": "==", "value": user_id}]
        )
        
        total_assigned = len(user_training)
        completed = len([t for t in user_training if t.get("status") == "completed"])
        in_progress = len([t for t in user_training if t.get("status") == "in_progress"])
        
        # Calculate average score for completed trainings
        scores = [t.get("score") for t in user_training if t.get("score") is not None]
        avg_score = sum(scores) / len(scores) if scores else None
        
        return {
            "total_assigned": total_assigned,
            "completed": completed,
            "in_progress": in_progress,
            "avg_score": avg_score
        }
    except Exception as e:
        logger.error(f"Error getting user training stats: {e}")
        return {"total_assigned": 0, "completed": 0, "in_progress": 0, "avg_score": 0}

async def update_user_performance_training_hours(firestore_manager, user_id: str, hours: float):
    """Update user performance metrics with training hours"""
    try:
        # Get or create monthly performance record
        current_month = datetime.now().strftime("%Y-%m")
        
        performance_records = await firestore_manager.get_collection(
            "user_performance",
            filters=[
                {"field": "user_id", "operator": "==", "value": user_id},
                {"field": "period", "operator": "==", "value": "monthly"},
                {"field": "period_date", "operator": "==", "value": current_month}
            ]
        )
        
        if performance_records:
            # Update existing record
            record = performance_records[0]
            current_hours = record.get("training_hours", 0)
            await firestore_manager.update_document(
                "user_performance",
                record["id"],
                {"training_hours": current_hours + hours}
            )
        else:
            # Create new record
            performance_data = {
                "user_id": user_id,
                "period": "monthly",
                "period_date": current_month,
                "training_hours": hours,
                "work_orders_completed": 0,
                "efficiency_rating": 0
            }
            await firestore_manager.create_document("user_performance", performance_data)
            
    except Exception as e:
        logger.error(f"Error updating user performance training hours: {e}")

# ========== TRAINING CENTER ==========


@router.get("/", response_class=HTMLResponse)
async def training_center(request: Request, session_token: Optional[str] = Cookie(None)):
    """Training center dashboard"""
    user = get_current_user_from_session(session_token)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    user_id = str(user["id"])
    firestore_manager = get_firestore_manager()
    try:
        # Get user's assigned training with module details
        my_training = await get_user_training_with_modules(firestore_manager, user_id)

        # Get available modules (modules not assigned to user)
        available_modules = await get_available_training_modules(firestore_manager, user_id)

        # Get completion stats
        stats = await get_user_training_stats(firestore_manager, user_id)

        return templates.TemplateResponse(
            "training_center.html",
            {
                "request": request,
                "my_training": my_training,
                "available_modules": available_modules,
                "stats": stats,
                "user_id": user_id,
            },
        )
    except Exception as e:
        logger.error(f"Error loading training center: {e}")
        return templates.TemplateResponse(
            "training_center.html",
            {
                "request": request,
                "my_training": [],
                "available_modules": [],
                "stats": {"total_assigned": 0, "completed": 0, "in_progress": 0, "avg_score": 0},
                "user_id": user_id,
                "error": "Failed to load training data"
            },
        )


# ========== TRAINING MODULES ==========


@router.get("/modules")
async def get_modules(skill_category: str = None, asset_type: str = None):
    """Get all training modules"""
    firestore_manager = get_firestore_manager()
    try:
        filters = []
        
        if skill_category:
            filters.append({"field": "skill_category", "operator": "==", "value": skill_category})
        
        if asset_type:
            filters.append({"field": "asset_type", "operator": "==", "value": asset_type})

        modules = await firestore_manager.get_collection(
            "training_modules", 
            order_by="-created_at",
            filters=filters if filters else None
        )
        
        return modules
    except Exception as e:
        logger.error(f"Error getting training modules: {e}")
        return []


@router.get("/modules/{module_id}", response_class=HTMLResponse)
async def module_detail(request: Request, module_id: str):
    """Training module detail page - interactive technician experience"""
    firestore_manager = get_firestore_manager()
    try:
        module = await firestore_manager.get_document("training_modules", module_id)

        if not module:
            return RedirectResponse("/training")

        # Parse content if AI-generated
        content = None
        if module.get("ai_generated") and module.get("content_path"):
            try:
                content = json.loads(module["content_path"])
            except Exception:
                pass

        return templates.TemplateResponse(
            "training_module_interactive.html",
            {
                "request": request,
                "module": module,
                "content": content,
                # For now, provide simple defaults for role-based fields
                "role": "technician",
                "role_config": {"title": "Technician Training"},
            },
        )
    except Exception as e:
        logger.error(f"Error loading training module {module_id}: {e}")
        return RedirectResponse("/training")


# ========== AI TRAINING GENERATION ==========


@router.post("/generate")
async def generate_training(
    manual_file: UploadFile = File(...),
    asset_type: str = Form(...),
    skill_category: str = Form(...),
):
    """Generate training from uploaded manual"""
    try:
        # Save uploaded file
        import os

        upload_dir = "data/manuals"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = f"{upload_dir}/{manual_file.filename}"
        with open(file_path, "wb") as f:
            content = await manual_file.read()
            f.write(content)

        # Generate training
        module_id = await training_generator.generate_from_manual(
            file_path, asset_type, skill_category
        )

        if module_id:
            return {"success": True, "module_id": module_id}
        else:
            return {"success": False, "error": "Failed to generate training"}

    except Exception as e:
        logger.error(f"Error generating training: {e}")
        return {"success": False, "error": str(e)}


@router.post("/quick-guide")
async def generate_quick_guide(
    equipment_name: str = Form(...), task_description: str = Form(...)
):
    """Generate a quick reference guide"""
    guide = await training_generator.generate_quick_guide(
        equipment_name, task_description
    )
    return {"guide": guide}


@router.post("/ask")
async def ask_question(question: str = Form(...), context: str = Form(None)):
    """Ask a technical question to the AI assistant"""
    answer = await training_generator.answer_technical_question(question, context)
    return {"answer": answer}


# ========== USER TRAINING MANAGEMENT ==========


@router.post("/modules/{module_id}/start")
async def start_training(module_id: str, user_id: str = Form(...)):
    """Start a training module"""
    firestore_manager = get_firestore_manager()
    try:
        # Check if already assigned
        existing_training = await firestore_manager.get_collection(
            "user_training",
            filters=[
                {"field": "user_id", "operator": "==", "value": user_id},
                {"field": "training_module_id", "operator": "==", "value": module_id}
            ],
            limit=1
        )

        if existing_training:
            # Update existing to in_progress
            await firestore_manager.update_document(
                "user_training", 
                existing_training[0]["id"], 
                {
                    "status": "in_progress", 
                    "started_date": datetime.now()
                }
            )
        else:
            # Create new training assignment
            training_data = {
                "user_id": user_id,
                "training_module_id": module_id,
                "status": "in_progress",
                "started_date": datetime.now(),
                "completed_date": None,
                "score": None
            }
            await firestore_manager.create_document("user_training", training_data)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error starting training {module_id} for user {user_id}: {e}")
        return {"success": False, "error": str(e)}


@router.post("/modules/{module_id}/complete")
async def complete_training(
    module_id: str, user_id: str = Form(...), score: float = Form(None)
):
    """Complete a training module"""
    firestore_manager = get_firestore_manager()
    try:
        # Find the user training record
        user_training = await firestore_manager.get_collection(
            "user_training",
            filters=[
                {"field": "user_id", "operator": "==", "value": user_id},
                {"field": "training_module_id", "operator": "==", "value": module_id}
            ],
            limit=1
        )

        if not user_training:
            return {"success": False, "error": "Training assignment not found"}

        # Update training completion
        await firestore_manager.update_document(
            "user_training", 
            user_training[0]["id"], 
            {
                "status": "completed",
                "completed_date": datetime.now(),
                "score": score
            }
        )

        # Get training module for duration
        module = await firestore_manager.get_document("training_modules", module_id)
        if module:
            duration_hours = module.get("estimated_duration_minutes", 0) / 60.0
            
            # Update user performance metrics
            await update_user_performance_training_hours(firestore_manager, user_id, duration_hours)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error completing training {module_id} for user {user_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/my-training")
async def get_my_training(user_id: str):
    """Get user's training assignments"""
    firestore_manager = get_firestore_manager()
    try:
        training = await get_user_training_with_modules(firestore_manager, user_id)
        return training
    except Exception as e:
        logger.error(f"Error getting training for user {user_id}: {e}")
        return []


@router.post("/assign")
async def assign_training(user_id: str = Form(...), module_id: str = Form(...)):
    """Assign training to a user"""
    firestore_manager = get_firestore_manager()
    try:
        # Create training assignment
        training_data = {
            "user_id": user_id,
            "training_module_id": module_id,
            "status": "assigned",
            "assigned_date": datetime.now(),
            "started_date": None,
            "completed_date": None,
            "score": None
        }
        
        await firestore_manager.create_document("user_training", training_data)

        # Get module title for notification
        module = await firestore_manager.get_document("training_modules", module_id)
        module_title = module.get("title", "Training Module") if module else "Training Module"

        # Notify user
        await notification_service.notify_training_due(user_id, module_title, module_id)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error assigning training {module_id} to user {user_id}: {e}")
        return {"success": False, "error": str(e)}
