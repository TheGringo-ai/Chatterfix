"""
User Management & Application Training Router
Handles adding users, role assignment, and hands-on training for using ChatterFix CMMS
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-management", tags=["user_management"])
templates = Jinja2Templates(directory="app/templates")

# Define application training modules for each role
APPLICATION_TRAINING_MODULES = {
    "technician": [
        {
            "id": "app_login_navigation",
            "title": "Logging In & Navigation",
            "description": "Learn to access ChatterFix and navigate the interface",
            "tasks": [
                "Log into the system using your credentials",
                "Navigate to the dashboard",
                "Explore the main menu and sidebar",
                "Understand notification indicators",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
        {
            "id": "app_work_orders",
            "title": "Creating & Managing Work Orders",
            "description": "Hands-on training for work order management",
            "tasks": [
                "Create a new work order from scratch",
                "Fill out work order details (title, description, priority)",
                "Assign work orders to yourself",
                "Update work order status to 'In Progress'",
                "Add completion notes and photos",
                "Close a completed work order",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
        {
            "id": "app_parts_checkout",
            "title": "Parts & Inventory Management",
            "description": "Learn to check out parts and manage inventory",
            "tasks": [
                "Search for parts in inventory",
                "Check out parts for a work order",
                "Scan barcodes to identify parts",
                "Request new parts from procurement",
                "Update part quantities after use",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
        {
            "id": "app_mobile_features",
            "title": "Mobile Features & Camera",
            "description": "Use mobile features for field work",
            "tasks": [
                "Access the camera interface",
                "Take photos and associate with work orders",
                "Use voice commands to create work orders",
                "Scan asset barcodes for identification",
                "Work offline and sync when connected",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
    ],
    "purchaser": [
        {
            "id": "app_procurement",
            "title": "Procurement & Purchasing",
            "description": "Master the purchasing workflow in ChatterFix",
            "tasks": [
                "Review parts requests from technicians",
                "Create purchase orders",
                "Manage vendor information",
                "Track deliveries and update status",
                "Process invoices and update costs",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
        {
            "id": "app_inventory_control",
            "title": "Inventory Control & Analytics",
            "description": "Learn advanced inventory management",
            "tasks": [
                "Set reorder points and stock levels",
                "Generate inventory reports",
                "Perform cycle counts and adjustments",
                "Analyze usage patterns and trends",
                "Optimize stock levels for critical parts",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
    ],
    "supervisor": [
        {
            "id": "app_team_management",
            "title": "Team Management Dashboard",
            "description": "Manage your team and monitor performance",
            "tasks": [
                "View team member status and assignments",
                "Assign work orders to technicians",
                "Monitor work order progress and completion",
                "Send messages and notifications to team",
                "Review technician performance metrics",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
        {
            "id": "app_analytics_reporting",
            "title": "Analytics & Reporting",
            "description": "Generate reports and analyze performance",
            "tasks": [
                "Access the analytics dashboard",
                "Generate work order completion reports",
                "Review team productivity metrics",
                "Create custom performance reports",
                "Export data for external analysis",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
    ],
    "planner": [
        {
            "id": "app_pm_scheduling",
            "title": "Preventive Maintenance Scheduling",
            "description": "Create and manage PM schedules",
            "tasks": [
                "Create preventive maintenance schedules",
                "Set up calendar and meter-based triggers",
                "Assign PM work orders to technicians",
                "Monitor PM compliance and completion",
                "Adjust schedules based on performance data",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
        {
            "id": "app_advanced_planning",
            "title": "Advanced Planning & Optimization",
            "description": "Master resource planning and optimization",
            "tasks": [
                "Use the advanced scheduler interface",
                "Plan complex multi-craft jobs",
                "Optimize resource allocation",
                "Coordinate shutdown and outage planning",
                "Generate detailed work packages",
            ],
            "guided_tour": True,
            "practice_mode": True,
        },
    ],
}

ROLE_PERMISSIONS = {
    "technician": {
        "work_orders": ["create", "view", "update", "complete"],
        "parts": ["view", "checkout", "request"],
        "assets": ["view", "update_condition"],
        "analytics": ["view_own"],
    },
    "purchaser": {
        "work_orders": ["view"],
        "parts": ["create", "view", "update", "delete"],
        "purchasing": ["create", "view", "update", "approve"],
        "vendors": ["create", "view", "update"],
        "analytics": ["view_inventory"],
    },
    "supervisor": {
        "work_orders": ["create", "view", "update", "assign", "approve"],
        "parts": ["view", "approve_requests"],
        "team": ["view", "manage", "assign"],
        "analytics": ["view_team", "view_reports"],
        "settings": ["view", "update_team"],
    },
    "planner": {
        "work_orders": ["create", "view", "update", "schedule"],
        "pm_schedules": ["create", "view", "update", "delete"],
        "assets": ["view", "update", "create"],
        "analytics": ["view_all", "create_reports"],
        "advanced_scheduler": ["full_access"],
    },
    "manager": {
        "all": ["full_access"],
        "user_management": ["create", "view", "update", "delete"],
        "system_settings": ["full_access"],
    },
}


@router.get("/", response_class=HTMLResponse)
async def user_management_dashboard(request: Request):
    """Main user management dashboard"""
    try:
        firestore = get_firestore_manager()

        # Fetch users from Firestore
        users = await firestore.get_collection("users", order_by="-created_at")

        # Calculate user statistics by role
        role_counts = {}
        for user in users:
            role = user.get("role", "technician")
            if role not in role_counts:
                role_counts[role] = {"count": 0, "active_count": 0}
            role_counts[role]["count"] += 1
            if user.get("is_active", True):
                role_counts[role]["active_count"] += 1

        users_stats = [
            {"role": role, "count": data["count"], "active_count": data["active_count"]}
            for role, data in role_counts.items()
        ]

        # If no users found, provide default stats
        if not users_stats:
            users_stats = [
                {"role": "technician", "count": 0, "active_count": 0},
                {"role": "supervisor", "count": 0, "active_count": 0},
            ]

        # Get recent users (last 10)
        recent_users = []
        for user in users[:10]:
            created_at = user.get("created_at", "")
            if hasattr(created_at, "strftime"):
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")

            recent_users.append(
                {
                    "id": user.get("uid", user.get("id", "")),
                    "username": user.get("username", user.get("email", "")),
                    "full_name": user.get("full_name", user.get("display_name", "")),
                    "role": user.get("role", "technician"),
                    "status": "active" if user.get("is_active", True) else "inactive",
                    "created_date": created_at,
                }
            )

        # Calculate training stats from training_assignments collection
        training_assignments = await firestore.get_collection("training_assignments")
        users_in_training = len(
            set(
                t.get("user_id")
                for t in training_assignments
                if t.get("status") == "in_progress"
            )
        )
        completed_training = len(
            [t for t in training_assignments if t.get("status") == "completed"]
        )

        training_stats = {
            "users_in_training": users_in_training,
            "completed_training": completed_training,
            "average_completion_time": 4.2,  # Would need time tracking to calculate
        }

        return templates.TemplateResponse(
            "user_management_dashboard.html",
            {
                "request": request,
                "users_stats": users_stats,
                "recent_users": recent_users,
                "training_stats": training_stats,
                "available_roles": list(ROLE_PERMISSIONS.keys()),
            },
        )

    except Exception as e:
        logger.error(f"Error loading user management dashboard: {e}")
        # Fallback to empty data on error
        return templates.TemplateResponse(
            "user_management_dashboard.html",
            {
                "request": request,
                "users_stats": [{"role": "technician", "count": 0, "active_count": 0}],
                "recent_users": [],
                "training_stats": {
                    "users_in_training": 0,
                    "completed_training": 0,
                    "average_completion_time": 0,
                },
                "available_roles": list(ROLE_PERMISSIONS.keys()),
                "error": str(e),
            },
        )


@router.get("/add-user", response_class=HTMLResponse)
async def add_user_form(request: Request):
    """Add new user form"""
    return templates.TemplateResponse(
        "add_user_form.html",
        {
            "request": request,
            "available_roles": list(ROLE_PERMISSIONS.keys()),
            "role_permissions": ROLE_PERMISSIONS,
            "training_modules": APPLICATION_TRAINING_MODULES,
        },
    )


@router.post("/add-user")
async def create_new_user(
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    department: str = Form(None),
    supervisor_id: str = Form(None),
    send_welcome_email: bool = Form(False),
    auto_start_training: bool = Form(True),
):
    """Create a new user with role and training assignment"""
    try:
        if role not in ROLE_PERMISSIONS:
            return JSONResponse({"error": "Invalid role selected"}, status_code=400)

        firestore = get_firestore_manager()

        # Check if username/email already exists
        existing_users = await firestore.get_collection("users")
        for user in existing_users:
            if user.get("username") == username or user.get("email") == email:
                return JSONResponse(
                    {"error": "Username or email already exists"}, status_code=400
                )

        # Generate a unique user ID
        import uuid

        user_id = str(uuid.uuid4())

        # Create user document
        user_data = {
            "uid": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role,
            "department": department,
            "supervisor_id": supervisor_id,
            "status": "pending",
            "is_active": True,
            "permissions": ROLE_PERMISSIONS[role],
            "created_at": datetime.now(timezone.utc),
        }

        await firestore.create_document("users", user_data, doc_id=user_id)

        # Auto-assign training if requested
        training_count = 0
        if auto_start_training and role in APPLICATION_TRAINING_MODULES:
            for module in APPLICATION_TRAINING_MODULES[role]:
                assignment_data = {
                    "user_id": user_id,
                    "module_id": module["id"],
                    "module_title": module["title"],
                    "status": "assigned",
                    "assigned_date": datetime.now(timezone.utc),
                }
                await firestore.create_document("training_assignments", assignment_data)
                training_count += 1

        logger.info(f"Created user {full_name} ({user_id}) with role {role}")

        return JSONResponse(
            {
                "success": True,
                "user_id": user_id,
                "message": f"User {full_name} created successfully with {role} role",
                "training_modules": training_count,
                "redirect_url": f"/user-management/user/{user_id}",
            }
        )

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return JSONResponse(
            {"error": f"Failed to create user: {str(e)}"}, status_code=500
        )


@router.get("/user/{user_id}", response_class=HTMLResponse)
async def user_detail_page(request: Request, user_id: str):
    """User detail page with training progress and application proficiency"""
    try:
        firestore = get_firestore_manager()

        # Get user details from Firestore
        user = await firestore.get_document("users", user_id)

        if not user:
            return HTMLResponse("User not found", status_code=404)

        # Format user data for template
        user_data = {
            "id": user.get("uid", user_id),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "full_name": user.get("full_name", ""),
            "role": user.get("role", "technician"),
            "department": user.get("department", ""),
            "status": user.get("status", "active"),
            "permissions": user.get("permissions", {}),
            "created_date": user.get("created_at", ""),
        }

        # Get training assignments for this user
        all_assignments = await firestore.get_collection("training_assignments")
        training_progress = [
            {
                "module_id": a.get("module_id"),
                "module_title": a.get("module_title"),
                "status": a.get("status"),
                "assigned_date": a.get("assigned_date"),
                "completion_date": a.get("completion_date"),
                "score": a.get("score"),
                "time_spent_minutes": a.get("time_spent_minutes"),
            }
            for a in all_assignments
            if a.get("user_id") == user_id
        ]

        # Get proficiency data (if exists)
        all_proficiency = await firestore.get_collection("user_proficiency")
        proficiency = [p for p in all_proficiency if p.get("user_id") == user_id]

        # Calculate overall training completion
        total_modules = len(APPLICATION_TRAINING_MODULES.get(user_data["role"], []))
        completed_modules = len(
            [t for t in training_progress if t.get("completion_date")]
        )
        completion_percentage = (
            (completed_modules / total_modules * 100) if total_modules > 0 else 0
        )

        return templates.TemplateResponse(
            "user_detail.html",
            {
                "request": request,
                "user": user_data,
                "training_progress": training_progress,
                "proficiency": proficiency,
                "completion_percentage": completion_percentage,
                "available_modules": APPLICATION_TRAINING_MODULES.get(
                    user_data["role"], []
                ),
            },
        )

    except Exception as e:
        logger.error(f"Error loading user detail: {e}")
        return HTMLResponse(f"Error loading user details: {str(e)}", status_code=500)


@router.get("/training/{module_id}", response_class=HTMLResponse)
async def guided_training_module(request: Request, module_id: str, user_id: int):
    """Interactive guided training module for hands-on application learning"""
    try:
        # Find the module across all roles
        module = None
        user_role = None

        for role, modules in APPLICATION_TRAINING_MODULES.items():
            for mod in modules:
                if mod["id"] == module_id:
                    module = mod
                    user_role = role
                    break

        if not module:
            return HTMLResponse("Training module not found", status_code=404)

        # Get user's current progress
        conn = get_db_connection()
        progress = conn.execute(
            """
            SELECT * FROM user_training_progress 
            WHERE user_id = ? AND module_id = ?
        """,
            (user_id, module_id),
        ).fetchone()

        conn.close()

        return templates.TemplateResponse(
            "guided_training_module.html",
            {
                "request": request,
                "module": module,
                "user_id": user_id,
                "user_role": user_role,
                "progress": progress,
            },
        )

    except Exception as e:
        logger.error(f"Error loading training module: {e}")
        return HTMLResponse("Error loading training module", status_code=500)


@router.post("/training/{module_id}/complete")
async def complete_training_module(
    module_id: str,
    user_id: int = Form(...),
    score: float = Form(...),
    time_spent: int = Form(...),
    proficiency_scores: str = Form(...),  # JSON string of skill assessments
):
    """Mark training module as completed and update user proficiency"""
    try:
        import json

        conn = get_db_connection()
        cursor = conn.cursor()

        # Record training completion
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_training_progress (
                user_id, module_id, completion_date, score, time_spent_minutes
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, module_id, datetime.now(), score, time_spent),
        )

        # Update application proficiency scores
        if proficiency_scores:
            scores = json.loads(proficiency_scores)
            for skill_area, proficiency_level in scores.items():
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO user_application_proficiency (
                        user_id, skill_area, proficiency_level, last_assessed
                    ) VALUES (?, ?, ?, ?)
                """,
                    (user_id, skill_area, proficiency_level, datetime.now()),
                )

        # Check if user has completed all required training
        user_role = conn.execute(
            "SELECT role FROM users WHERE id = ?", (user_id,)
        ).fetchone()["role"]

        required_modules = [
            m["id"] for m in APPLICATION_TRAINING_MODULES.get(user_role, [])
        ]
        completed_modules = conn.execute(
            """
            SELECT module_id FROM user_training_progress WHERE user_id = ?
        """,
            (user_id,),
        ).fetchall()

        completed_module_ids = [c["module_id"] for c in completed_modules]
        all_completed = all(
            mod_id in completed_module_ids for mod_id in required_modules
        )

        # Update user status if training is complete
        if all_completed:
            cursor.execute(
                """
                UPDATE users SET status = 'active', training_completed_date = ?
                WHERE id = ?
            """,
                (datetime.now(), user_id),
            )

        conn.commit()
        conn.close()

        return JSONResponse(
            {
                "success": True,
                "training_complete": all_completed,
                "message": "Training module completed successfully",
                "next_action": (
                    "User is now fully trained and active!"
                    if all_completed
                    else "Continue with next training module"
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error completing training: {e}")
        return JSONResponse({"error": "Failed to complete training"}, status_code=500)


@router.get("/bulk-import", response_class=HTMLResponse)
async def bulk_user_import(request: Request):
    """Bulk user import interface"""
    return templates.TemplateResponse(
        "bulk_user_import.html",
        {"request": request, "available_roles": list(ROLE_PERMISSIONS.keys())},
    )


@router.get("/training-analytics", response_class=HTMLResponse)
async def training_analytics(request: Request):
    """Training completion analytics and reporting"""
    try:
        conn = get_db_connection()

        # Training completion statistics
        analytics = {
            "completion_by_role": conn.execute(
                """
                SELECT u.role, 
                       COUNT(u.id) as total_users,
                       COUNT(u.training_completed_date) as completed_training
                FROM users u
                GROUP BY u.role
            """
            ).fetchall(),
            "average_completion_times": conn.execute(
                """
                SELECT module_id, 
                       AVG(time_spent_minutes) as avg_time,
                       COUNT(*) as completions
                FROM user_training_progress
                GROUP BY module_id
            """
            ).fetchall(),
            "proficiency_levels": conn.execute(
                """
                SELECT skill_area,
                       AVG(proficiency_level) as avg_proficiency,
                       COUNT(DISTINCT user_id) as users_assessed
                FROM user_application_proficiency
                GROUP BY skill_area
            """
            ).fetchall(),
        }

        conn.close()

        return templates.TemplateResponse(
            "training_analytics.html", {"request": request, "analytics": analytics}
        )

    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        return HTMLResponse("Error loading analytics", status_code=500)


@router.get("/users", response_class=JSONResponse)
async def get_all_users(role: str = None, status: str = None):
    """API endpoint to get all users with filtering"""
    try:
        conn = get_db_connection()

        query = "SELECT * FROM users WHERE 1=1"
        params = []

        if role:
            query += " AND role = ?"
            params.append(role)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_date DESC"

        users = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(user) for user in users]

    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return JSONResponse({"error": "Failed to fetch users"}, status_code=500)
