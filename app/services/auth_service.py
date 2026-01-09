"""
Authentication Service
Integrates with Firebase Authentication for token verification and retrieves user permissions from Firestore.
"""

import logging
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials

from app.core.firestore_db import get_firestore_manager
from app.models.user import User

logger = logging.getLogger(__name__)

# --- Firebase Initialization ---


def initialize_firebase_app():
    """
    Initializes the Firebase Admin SDK.
    It's safe to call this multiple times; it will only initialize once.
    """
    # Check if the app is already initialized
    if not firebase_admin._apps:
        try:
            # The SDK will automatically use the GOOGLE_APPLICATION_CREDENTIALS env var
            # if it's set and valid.
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")
            logger.error(
                "Please ensure the GOOGLE_APPLICATION_CREDENTIALS environment variable is set "
                "correctly to a valid service account JSON file."
            )


# Call initialization on module load
initialize_firebase_app()


# --- Core Authentication Functions ---


async def verify_id_token_and_get_user(token: str) -> Optional[User]:
    """
    Verifies a Firebase ID token or demo session token, then fetches the user's profile.

    Supports two authentication methods:
    1. Firebase ID token (JWT) - for regular authenticated users
    2. Demo session token - for one-click demo users

    Args:
        token: The Firebase ID token (JWT) or demo session token.

    Returns:
        A User model instance if the token is valid and the user exists in Firestore, otherwise None.
    """
    if not firebase_admin._apps:
        logger.error("Firebase not initialized. Cannot verify token.")
        return None

    firestore_manager = get_firestore_manager()

    # Try to verify as Firebase session cookie first, then ID token
    uid = None
    email = None

    try:
        # Try session cookie first (longer-lasting, created with create_session_cookie)
        decoded_token = auth.verify_session_cookie(token, check_revoked=True)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")
    except Exception:
        # Not a valid session cookie, try as ID token
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token["uid"]
            email = decoded_token.get("email")
        except Exception:
            # Neither worked - will fall through to demo session lookup below
            pass

    # If we got a valid Firebase user, fetch their profile
    if uid:
        # Fetch user profile from Firestore to get roles and permissions
        user_doc = await firestore_manager.get_document("users", uid)

        if not user_doc:
            logger.warning(
                f"User with UID '{uid}' authenticated but not found in Firestore."
            )
            return None

        # Get permissions based on the user's role
        role = user_doc.get("role", "technician")
        permissions = get_permissions_for_role(role)

        # Create a user model with multi-tenant organization data
        user = User(
            uid=uid,
            email=email,
            role=role,
            full_name=user_doc.get("full_name") or user_doc.get("display_name"),
            disabled=user_doc.get("disabled", False),
            permissions=permissions,
            organization_id=user_doc.get("organization_id"),
            organization_name=user_doc.get("organization_name"),
        )

        if user.disabled:
            logger.warning(f"Authentication attempt for disabled user '{uid}'.")
            return None

        return user

    # Not a valid Firebase token - try demo session lookup
    # Try to find a demo user by session token
    try:
        logger.debug(f"Attempting demo session lookup for token: {token[:20]}...")
        demo_user = await _get_demo_user_by_session_token(token, firestore_manager)
        if demo_user:
            logger.info(f"Demo user found: {demo_user.uid}")
            return demo_user
        else:
            logger.debug("No demo user found for token")
    except Exception as e:
        logger.warning(f"Demo session lookup failed: {e}")

    return None


async def _get_demo_user_by_session_token(token: str, firestore_manager) -> Optional[User]:
    """
    Look up a demo user by their session token.

    Args:
        token: The demo session token
        firestore_manager: Firestore manager instance

    Returns:
        User model if valid demo session, None otherwise
    """
    from datetime import datetime, timezone

    if not firestore_manager.db:
        return None

    # Query users by session_token where is_demo=True
    users_ref = firestore_manager.db.collection("users")
    query = users_ref.where("session_token", "==", token).where("is_demo", "==", True).limit(1)

    logger.debug(f"Querying Firestore for session_token: {token[:20]}...")
    docs = list(query.stream())
    logger.debug(f"Query returned {len(docs)} documents")
    if not docs:
        return None

    user_doc = docs[0].to_dict()
    uid = user_doc.get("uid")

    # Check session expiration
    expires_at = user_doc.get("session_expires_at")
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp_dt:
                logger.info(f"Demo session expired for user {uid}")
                return None
        except Exception:
            pass

    # Get permissions from stored list or default
    permissions = user_doc.get("permissions", [])
    if not permissions:
        permissions = get_permissions_for_role(user_doc.get("role", "technician"))

    # Create User model for demo user
    user = User(
        uid=uid,
        email=user_doc.get("email"),
        role=user_doc.get("role", "owner"),
        full_name=user_doc.get("full_name", "Demo User"),
        disabled=False,
        permissions=permissions,
        organization_id=user_doc.get("organization_id"),
        organization_name=user_doc.get("organization_name"),
    )

    # Add is_demo flag (may need to be added to User model)
    user.is_demo = True

    return user


# --- Permission Management ---


def get_permissions_for_role(role: str) -> list[str]:
    """
    Retrieves the list of permissions for a given user role.
    This defines the role-based access control (RBAC) for the application.
    """
    role_permissions = {
        "owner": ["all"],  # Organization owner has full access
        "manager": ["all"],
        "supervisor": [
            "view_all_work_orders",
            "approve_work_orders",
            "manage_team",
            "view_reports",
            "create_work_order_request",
            "update_status",
            "assign_technicians",
        ],
        "planner": [
            "schedule_work_orders",
            "assign_technicians",
            "view_resources",
            "view_reports",
            "create_work_order_request",
        ],
        "parts_manager": [
            "manage_inventory",
            "manage_vendors",
            "approve_parts_requests",
            "view_inventory_reports",
            "create_work_order_request",
        ],
        "technician": [
            "complete_work_orders",
            "use_parts",
            "view_assigned_work_orders",
            "update_status",
            "create_work_order_request",
        ],
        "requestor": ["create_work_order_request", "view_own_requests"],
    }
    return role_permissions.get(role, [])


def check_permission(user: User, required_permission: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: The User object.
        required_permission: The permission string to check for.

    Returns:
        True if the user has the permission, False otherwise.
    """
    if not user:
        return False

    # "manager" role has all permissions
    if "all" in user.permissions:
        return True

    return required_permission in user.permissions
