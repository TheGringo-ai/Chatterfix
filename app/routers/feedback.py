"""
Feedback Router
Handles work order feedback and quality tracking
"""

from fastapi import APIRouter, Form
from fastapi.templating import Jinja2Templates
from app.core.database import get_db_connection
from app.services.notification_service import notification_service
import os
import logging

# Import Google Generative AI with error handling
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Google Generative AI not available: {e}")
    genai = None
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])
templates = Jinja2Templates(directory="app/templates")

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GENAI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)

# ========== WORK ORDER FEEDBACK ==========


@router.post("/work-order/{work_order_id}")
async def submit_feedback(
    work_order_id: int,
    technician_id: int = Form(...),
    asset_id: int = Form(...),
    feedback_type: str = Form(...),
    description: str = Form(...),
    time_to_failure_hours: float = Form(None),
    root_cause: str = Form(None),
):
    """Submit feedback on a completed work order"""
    conn = get_db_connection()
    try:
        # Get work order and asset details for AI analysis
        wo = conn.execute(
            """
            SELECT wo.*, a.name as asset_name, a.type as asset_type
            FROM work_orders wo
            JOIN assets a ON wo.asset_id = a.id
            WHERE wo.id = ?
        """,
            (work_order_id,),
        ).fetchone()

        # Generate AI analysis
        ai_analysis = ""
        if GEMINI_API_KEY and GENAI_AVAILABLE and feedback_type == "immediate_failure":
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"""
                Analyze this maintenance failure and provide insights:

                Asset: {wo['asset_name']} ({wo['asset_type']})
                Work Order: {wo['title']}
                Time to Failure: {time_to_failure_hours} hours after completion
                Description: {description}
                Root Cause: {root_cause or 'Not specified'}

                Provide:
                1. Likely root cause (if not specified)
                2. Preventive actions to avoid recurrence
                3. Whether this indicates a systemic issue
                4. Recommended follow-up actions

                Be concise and actionable.
                """

                response = model.generate_content(prompt)
                ai_analysis = response.text
            except Exception as e:
                logger.error(f"Error generating AI analysis: {e}")
                ai_analysis = "AI analysis unavailable"

        # Save feedback
        conn.execute(
            """
            INSERT INTO work_order_feedback
            (work_order_id, asset_id, technician_id, feedback_type, description,
             time_to_failure_hours, root_cause, ai_analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                work_order_id,
                asset_id,
                technician_id,
                feedback_type,
                description,
                time_to_failure_hours,
                root_cause,
                ai_analysis,
            ),
        )
        conn.commit()
        feedback_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Notify managers if immediate failure
        if feedback_type == "immediate_failure":
            managers = conn.execute(
                "SELECT id FROM users WHERE role IN ('manager', 'supervisor')"
            ).fetchall()

            for manager in managers:
                await notification_service.notify_immediate_failure(
                    [manager[0]],
                    wo["asset_name"],
                    work_order_id,
                    time_to_failure_hours or 0,
                )

        return {"success": True, "feedback_id": feedback_id, "ai_analysis": ai_analysis}
    finally:
        conn.close()


# ========== FEEDBACK ANALYTICS ==========


@router.get("/asset/{asset_id}")
async def get_asset_feedback(asset_id: int):
    """Get all feedback for an asset"""
    conn = get_db_connection()
    try:
        feedback = conn.execute(
            """
            SELECT f.*, u.full_name as technician_name, wo.title as work_order_title
            FROM work_order_feedback f
            JOIN users u ON f.technician_id = u.id
            JOIN work_orders wo ON f.work_order_id = wo.id
            WHERE f.asset_id = ?
            ORDER BY f.created_date DESC
        """,
            (asset_id,),
        ).fetchall()

        return [dict(f) for f in feedback]
    finally:
        conn.close()


@router.get("/recurring-issues")
async def get_recurring_issues():
    """Get AI-identified recurring problems"""
    conn = get_db_connection()
    try:
        # Find assets with multiple failures
        recurring = conn.execute(
            """
            SELECT
                a.id as asset_id,
                a.name as asset_name,
                a.type as asset_type,
                COUNT(f.id) as failure_count,
                AVG(f.time_to_failure_hours) as avg_time_to_failure,
                GROUP_CONCAT(f.feedback_type) as feedback_types
            FROM work_order_feedback f
            JOIN assets a ON f.asset_id = a.id
            WHERE f.feedback_type IN ('immediate_failure', 'recurring_issue')
            GROUP BY a.id
            HAVING failure_count >= 2
            ORDER BY failure_count DESC, avg_time_to_failure ASC
        """
        ).fetchall()

        return [dict(r) for r in recurring]
    finally:
        conn.close()


@router.get("/quality-alerts")
async def get_quality_alerts():
    """Get quality concerns requiring attention"""
    conn = get_db_connection()
    try:
        alerts = conn.execute(
            """
            SELECT f.*,
                   a.name as asset_name,
                   u.full_name as technician_name,
                   wo.title as work_order_title
            FROM work_order_feedback f
            JOIN assets a ON f.asset_id = a.id
            JOIN users u ON f.technician_id = u.id
            JOIN work_orders wo ON f.work_order_id = wo.id
            WHERE f.feedback_type IN ('immediate_failure', 'quality_concern')
            ORDER BY f.created_date DESC
            LIMIT 50
        """
        ).fetchall()

        return [dict(a) for a in alerts]
    finally:
        conn.close()


@router.get("/technician-quality/{technician_id}")
async def get_technician_quality(technician_id: int):
    """Get quality metrics for a technician"""
    conn = get_db_connection()
    try:
        # Get feedback stats
        stats = conn.execute(
            """
            SELECT
                COUNT(*) as total_feedback,
                SUM(CASE WHEN feedback_type = 'immediate_failure' THEN 1 ELSE 0 END) as immediate_failures,
                SUM(CASE WHEN feedback_type = 'recurring_issue' THEN 1 ELSE 0 END) as recurring_issues,
                AVG(time_to_failure_hours) as avg_time_to_failure
            FROM work_order_feedback
            WHERE technician_id = ?
        """,
            (technician_id,),
        ).fetchone()

        # Get work order completion rate
        wo_stats = conn.execute(
            """
            SELECT
                COUNT(*) as total_work_orders,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM work_orders
            WHERE assigned_to = ?
        """,
            (technician_id,),
        ).fetchone()

        # Calculate quality score (0-100)
        quality_score = 100
        if stats["total_feedback"] > 0:
            failure_rate = (stats["immediate_failures"] or 0) / stats["total_feedback"]
            quality_score = max(0, 100 - (failure_rate * 100))

        return {
            "feedback_stats": dict(stats),
            "work_order_stats": dict(wo_stats),
            "quality_score": round(quality_score, 1),
        }
    finally:
        conn.close()
