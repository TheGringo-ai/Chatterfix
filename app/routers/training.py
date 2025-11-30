"""
Training Router
Handles AI-generated training modules and technician learning
"""

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.database import get_db_connection
from app.services.training_generator import training_generator
from app.services.notification_service import notification_service
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])
templates = Jinja2Templates(directory="app/templates")

# ========== TRAINING CENTER ==========


@router.get("/", response_class=HTMLResponse)
async def training_center(request: Request, user_id: int = 1):
    """Training center dashboard"""
    conn = get_db_connection()
    try:
        # Get user's assigned training
        my_training = conn.execute(
            """
            SELECT ut.*, tm.title, tm.description, tm.estimated_duration_minutes, tm.difficulty_level
            FROM user_training ut
            JOIN training_modules tm ON ut.training_module_id = tm.id
            WHERE ut.user_id = ?
            ORDER BY
                CASE ut.status
                    WHEN 'assigned' THEN 1
                    WHEN 'in_progress' THEN 2
                    WHEN 'completed' THEN 3
                END,
                ut.started_date DESC
        """,
            (user_id,),
        ).fetchall()

        # Get available modules
        available_modules = conn.execute(
            """
            SELECT tm.*
            FROM training_modules tm
            WHERE tm.id NOT IN (
                SELECT training_module_id FROM user_training WHERE user_id = ?
            )
            ORDER BY tm.created_date DESC
        """,
            (user_id,),
        ).fetchall()

        # Get completion stats
        stats = conn.execute(
            """
            SELECT
                COUNT(*) as total_assigned,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                AVG(CASE WHEN score IS NOT NULL THEN score ELSE NULL END) as avg_score
            FROM user_training
            WHERE user_id = ?
        """,
            (user_id,),
        ).fetchone()

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
    finally:
        conn.close()


# ========== TRAINING MODULES ==========


@router.get("/modules")
async def get_modules(skill_category: str = None, asset_type: str = None):
    """Get all training modules"""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM training_modules WHERE 1=1"
        params = []

        if skill_category:
            query += " AND skill_category = ?"
            params.append(skill_category)

        if asset_type:
            query += " AND asset_type = ?"
            params.append(asset_type)

        query += " ORDER BY created_date DESC"

        modules = conn.execute(query, params).fetchall()
        return [dict(m) for m in modules]
    finally:
        conn.close()


@router.get("/modules/{module_id}", response_class=HTMLResponse)
async def module_detail(request: Request, module_id: int):
    """Training module detail page"""
    conn = get_db_connection()
    try:
        module = conn.execute(
            "SELECT * FROM training_modules WHERE id = ?", (module_id,)
        ).fetchone()

        if not module:
            return RedirectResponse("/training")

        # Parse content if AI-generated
        content = None
        if module["ai_generated"] and module["content_path"]:
            try:
                content = json.loads(module["content_path"])
            except:
                pass

        return templates.TemplateResponse(
            "training_module.html",
            {"request": request, "module": module, "content": content},
        )
    finally:
        conn.close()


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
async def start_training(module_id: int, user_id: int = Form(...)):
    """Start a training module"""
    conn = get_db_connection()
    try:
        # Check if already assigned
        existing = conn.execute(
            """
            SELECT id FROM user_training
            WHERE user_id = ? AND training_module_id = ?
        """,
            (user_id, module_id),
        ).fetchone()

        if existing:
            # Update to in_progress
            conn.execute(
                """
                UPDATE user_training
                SET status = 'in_progress', started_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (existing[0],),
            )
        else:
            # Create new assignment
            conn.execute(
                """
                INSERT INTO user_training (user_id, training_module_id, status, started_date)
                VALUES (?, ?, 'in_progress', CURRENT_TIMESTAMP)
            """,
                (user_id, module_id),
            )

        conn.commit()
        return {"success": True}
    finally:
        conn.close()


@router.post("/modules/{module_id}/complete")
async def complete_training(
    module_id: int, user_id: int = Form(...), score: float = Form(None)
):
    """Complete a training module"""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE user_training
            SET status = 'completed', completed_date = CURRENT_TIMESTAMP, score = ?
            WHERE user_id = ? AND training_module_id = ?
        """,
            (score, user_id, module_id),
        )
        conn.commit()

        # Update performance metrics
        conn.execute(
            """
            UPDATE user_performance
            SET training_hours = training_hours + (
                SELECT estimated_duration_minutes / 60.0
                FROM training_modules
                WHERE id = ?
            )
            WHERE user_id = ? AND period = 'monthly'
        """,
            (module_id, user_id),
        )
        conn.commit()

        return {"success": True}
    finally:
        conn.close()


@router.get("/my-training")
async def get_my_training(user_id: int):
    """Get user's training assignments"""
    training = training_generator.get_user_training(user_id)
    return [dict(t) for t in training]


@router.post("/assign")
async def assign_training(user_id: int = Form(...), module_id: int = Form(...)):
    """Assign training to a user"""
    training_generator.assign_training(user_id, module_id)

    # Get module title
    conn = get_db_connection()
    module = conn.execute(
        "SELECT title FROM training_modules WHERE id = ?", (module_id,)
    ).fetchone()
    conn.close()

    # Notify user
    await notification_service.notify_training_due(user_id, module[0], module_id)

    return {"success": True}
