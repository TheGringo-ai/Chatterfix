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
    Verifies a Firebase ID token, then fetches the user's profile and permissions from Firestore.

    Args:
        token: The Firebase ID token (JWT) from the client.

    Returns:
        A User model instance if the token is valid and the user exists in Firestore, otherwise None.
    """
    if not firebase_admin._apps:
        logger.error("Firebase not initialized. Cannot verify token.")
        return None

    try:
        # Verify the token against the Firebase Auth service
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')

        # Fetch user profile from Firestore to get roles and permissions
        firestore_manager = get_firestore_manager()
        user_doc = await firestore_manager.get_document('users', uid)

        if not user_doc:
            logger.warning(f"User with UID '{uid}' authenticated but not found in Firestore.")
            # Optionally, you could create a user profile here on first login.
            # For now, we'll deny access if they don't have a profile.
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
            # Multi-tenant organization fields
            organization_id=user_doc.get("organization_id"),
            organization_name=user_doc.get("organization_name"),
        )

        if user.disabled:
            logger.warning(f"Authentication attempt for disabled user '{uid}'.")
            return None

        return user

    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID token provided.")
        return None
    except Exception as e:
        logger.error(f"An error occurred during token verification: {e}")
        return None


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
