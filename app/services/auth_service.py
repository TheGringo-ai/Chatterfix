"""
Authentication Service
Handles user authentication, password hashing, and session management
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_PATH = os.getenv("CMMS_DB_PATH", "./data/cmms.db")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
SESSION_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username and password

    Returns:
        User dict if successful, None if failed
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user
    cursor.execute(
        """
        SELECT * FROM users
        WHERE username = ? AND is_active = 1
    """,
        (username,),
    )

    user = cursor.fetchone()

    if not user:
        conn.close()
        return None

    # Check if account is locked
    if user["locked_until"]:
        locked_until = datetime.fromisoformat(user["locked_until"])
        if datetime.now() < locked_until:
            conn.close()
            return None

    # Verify password
    if not user["password_hash"] or not verify_password(
        password, user["password_hash"]
    ):
        # Increment failed attempts
        cursor.execute(
            """
            UPDATE users
            SET failed_login_attempts = failed_login_attempts + 1,
                locked_until = CASE
                    WHEN failed_login_attempts >= 4
                    THEN datetime('now', '+30 minutes')
                    ELSE NULL
                END
            WHERE id = ?
        """,
            (user["id"],),
        )
        conn.commit()
        conn.close()
        return None

    # Reset failed attempts on successful login
    cursor.execute(
        """
        UPDATE users
        SET failed_login_attempts = 0,
            locked_until = NULL,
            last_seen = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (user["id"],),
    )

    conn.commit()
    conn.close()

    return dict(user)


def create_session(user_id: int, ip_address: str = None, user_agent: str = None) -> str:
    """
    Create a new session for a user

    Returns:
        Session token
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    session_id = secrets.token_urlsafe(16)
    token = create_session_token()
    expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRE_HOURS)

    cursor.execute(
        """
        INSERT INTO user_sessions (id, user_id, token, expires_at, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (session_id, user_id, token, expires_at.isoformat(), ip_address, user_agent),
    )

    conn.commit()
    conn.close()

    return token


def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a session token and return user info

    Returns:
        User dict if valid, None if invalid/expired
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT s.*, u.*
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
        AND s.is_active = 1
        AND datetime(s.expires_at) > datetime('now')
        AND u.is_active = 1
    """,
        (token,),
    )

    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    return dict(result)


def invalidate_session(token: str) -> bool:
    """Invalidate a session (logout)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE user_sessions
        SET is_active = 0
        WHERE token = ?
    """,
        (token,),
    )

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def create_user(
    username: str,
    email: str,
    password: str,
    full_name: str = None,
    role: str = "technician",
) -> Optional[int]:
    """
    Create a new user

    Returns:
        User ID if successful, None if failed
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    password_hash = hash_password(password)

    try:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, full_name, role, last_password_change)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (username, email, password_hash, full_name, role),
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except Exception:
        conn.close()
        return None


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    """Change a user's password"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify old password
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user or not verify_password(old_password, user["password_hash"]):
        conn.close()
        return False

    # Update password
    new_hash = hash_password(new_password)
    cursor.execute(
        """
        UPDATE users
        SET password_hash = ?,
            last_password_change = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (new_hash, user_id),
    )

    conn.commit()
    conn.close()
    return True


def check_permission(user_role: str, required_permission: str) -> bool:
    """
    Check if a user role has a specific permission

    Permission hierarchy:
    - manager: all permissions
    - supervisor: team management, work order approval
    - planner: work order scheduling, resource allocation
    - parts_manager: inventory management, vendor management
    - technician: work order completion, parts usage
    - requestor: work order creation only
    """
    role_permissions = {
        "manager": ["all"],
        "supervisor": [
            "view_all_work_orders",
            "approve_work_orders",
            "manage_team",
            "view_reports",
        ],
        "planner": [
            "schedule_work_orders",
            "assign_technicians",
            "view_resources",
            "view_reports",
        ],
        "parts_manager": [
            "manage_inventory",
            "manage_vendors",
            "approve_parts_requests",
            "view_inventory_reports",
        ],
        "technician": [
            "complete_work_orders",
            "use_parts",
            "view_assigned_work_orders",
            "update_status",
        ],
        "requestor": ["create_work_order_request", "view_own_requests"],
    }

    permissions = role_permissions.get(user_role, [])

    # Manager has all permissions
    if "all" in permissions:
        return True

    return required_permission in permissions
