import logging
import os
from typing import Any, Dict, Optional, cast

# Import Firebase modules
import firebase_admin
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials, firestore

FIREBASE_ADMIN_AVAILABLE = True

try:
    import pyrebase

    PYREBASE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Pyrebase not available: {e}")
    pyrebase = None
    PYREBASE_AVAILABLE = False

# Backward compatibility flag
FIREBASE_AVAILABLE = True

logger = logging.getLogger(__name__)


class FirebaseAuthService:
    def __init__(self):
        self.app = None
        self.auth_client = None
        self.db = None
        self._initialized = False
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK and client SDK"""
        # Check if Firebase is explicitly disabled
        if os.getenv("DISABLE_FIREBASE", "").lower() in ("true", "1", "yes"):
            logger.warning(
                "🔥 Firebase disabled via DISABLE_FIREBASE environment variable. This is not recommended for production."
            )
            return

        # Check if credentials are available
        google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        firebase_api_key = os.getenv("FIREBASE_API_KEY")

        # Fail if no credentials are configured
        if not google_creds_path and not firebase_api_key:
            logger.warning(
                "⚠️ No explicit credentials found. Attempting to use Google Cloud Default Credentials..."
            )
            # raise ValueError("Firebase credentials missing. Cannot start application without Firebase.")

        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = None

                # Try to load credentials from file path
                if google_creds_path and os.path.exists(google_creds_path):
                    cred = credentials.Certificate(google_creds_path)
                    logger.info(f"🔥 Using credentials from: {google_creds_path}")
                else:
                    # Try Application Default Credentials (for Cloud Run, GKE, etc.)
                    try:
                        cred = credentials.ApplicationDefault()
                        logger.info("🔥 Using Application Default Credentials")
                    except Exception as adc_error:
                        logger.warning(
                            f"🔥 Application Default Credentials not available: {adc_error}"
                        )
                        return

                if cred:
                    self.app = firebase_admin.initialize_app(
                        cred,
                        {
                            "projectId": os.getenv("GOOGLE_CLOUD_PROJECT", "fredfix"),
                        },
                    )
            else:
                self.app = firebase_admin.get_app()

            # Initialize Firestore client
            if self.app:
                try:
                    self.db = firestore.client()
                except Exception as fs_error:
                    logger.warning(f"🔥 Firestore not available: {fs_error}")

            # Initialize Pyrebase for client-side auth (optional, for frontend)
            if firebase_api_key:
                firebase_config = {
                    "apiKey": firebase_api_key,
                    "authDomain": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'fredfix')}.firebaseapp.com",
                    "projectId": os.getenv("GOOGLE_CLOUD_PROJECT", "fredfix"),
                    "storageBucket": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'fredfix')}.appspot.com",
                    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
                    "appId": os.getenv("FIREBASE_APP_ID", ""),
                    "databaseURL": "",
                }

                try:
                    firebase = pyrebase.initialize_app(firebase_config)
                    self.auth_client = firebase.auth()
                except Exception as pyrebase_error:
                    logger.warning(
                        f"🔥 Pyrebase initialization failed: {pyrebase_error}"
                    )

            self._initialized = True
            logger.info("🔥 Firebase Authentication initialized successfully")

        except Exception as e:
            logger.warning(f"🔥 Firebase initialization skipped: {e}")
            logger.info("   Application will use SQLite authentication instead")
            self.app = None
            self.auth_client = None
            self.db = None

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user data with organization info"""
        try:
            if not self.app:
                raise HTTPException(status_code=500, detail="Firebase not initialized")

            # Verify the token
            decoded_token = auth.verify_id_token(token)

            # Get user data from Firebase Auth
            user_record = auth.get_user(decoded_token["uid"])

            # Get or create user in Firestore
            user_data = await self.get_or_create_user(user_record)

            # Extract organization info for multi-tenant support
            organization_id = user_data.get("organization_id")
            organization_name = None
            company_data = user_data.get("company", {})

            if company_data:
                organization_name = company_data.get("name")
                # Use company name as organization_id if not explicitly set
                if not organization_id and organization_name:
                    organization_id = organization_name.lower().replace(" ", "_")

            return {
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
                "verified": decoded_token.get("email_verified", False),
                "user_data": user_data,
                # Multi-tenant fields
                "organization_id": organization_id,
                "organization_name": organization_name,
            }

        except firebase_admin.auth.InvalidIdTokenError:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        except firebase_admin.auth.ExpiredIdTokenError:
            raise HTTPException(status_code=401, detail="Authentication token expired")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    async def get_or_create_user(self, user_record: Any) -> Dict[str, Any]:
        """Get user from Firestore or create if doesn't exist"""
        try:
            if not self.db:
                raise Exception("Firestore not initialized")
            user_ref = self.db.collection("users").document(user_record.uid)
            user_doc = user_ref.get()

            if user_doc.exists:
                return cast(Dict[str, Any], user_doc.to_dict())
            else:
                # Create new user record
                user_data = {
                    "uid": user_record.uid,
                    "email": user_record.email,
                    "display_name": user_record.display_name or user_record.email,
                    "email_verified": user_record.email_verified,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "last_login": firestore.SERVER_TIMESTAMP,
                    "role": "technician",  # Default role
                    "status": "active",
                    "profile": {
                        "avatar_url": user_record.photo_url,
                        "phone": user_record.phone_number,
                    },
                }

                user_ref.set(user_data)
                logger.info(f"Created new user: {user_record.email}")
                return user_data

        except Exception as e:
            logger.error(f"Error getting/creating user: {e}")
            raise HTTPException(status_code=500, detail="User creation failed")

    async def update_user_login(self, uid: str) -> None:
        """Update user's last login timestamp"""
        try:
            if not self.db:
                return
            user_ref = self.db.collection("users").document(uid)
            user_ref.update({"last_login": firestore.SERVER_TIMESTAMP})
        except Exception as e:
            logger.error(f"Error updating user login: {e}")

    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user data by UID"""
        try:
            if not self.db:
                return None
            user_ref = self.db.collection("users").document(uid)
            user_doc = user_ref.get()

            if user_doc.exists:
                return cast(Dict[str, Any], user_doc.to_dict())
            return None

        except Exception as e:
            logger.error(f"Error getting user by UID: {e}")
            return None

    async def update_user_profile(self, uid: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            if not self.db:
                return False
            user_ref = self.db.collection("users").document(uid)
            user_ref.update({**profile_data, "updated_at": firestore.SERVER_TIMESTAMP})
            return True

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False

    async def sign_in_with_email_password(
        self, email: str, password: str
    ) -> Dict[str, Any]:
        """Sign in with email and password using Pyrebase"""
        if not self.auth_client:
            raise Exception(
                "Client-side authentication not available (Pyrebase init failed)"
            )

        try:
            user = self.auth_client.sign_in_with_email_and_password(email, password)
            return user
        except Exception as e:
            logger.error(f"Firebase sign-in failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid credentials")

    async def create_user_with_email_password(
        self, email: str, password: str, display_name: Optional[str] = None
    ) -> Any:
        """Create a new Firebase user with email and password"""
        if not self.is_available:
            raise Exception("Firebase not available")

        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False,
            )
            logger.info(f"Created Firebase user: {email}")
            return user_record
        except Exception as e:
            logger.error(f"Error creating Firebase user: {e}")
            raise Exception(f"Failed to create user: {str(e)}")

    async def create_custom_token(self, uid: str) -> str:
        """Create a custom token for user authentication"""
        if not self.is_available:
            raise Exception("Firebase not available")

        try:
            custom_token = auth.create_custom_token(uid)
            # Convert bytes to string if needed
            if isinstance(custom_token, bytes):
                return custom_token.decode("utf-8")
            return cast(str, custom_token)
        except Exception as e:
            logger.error(f"Error creating custom token: {e}")
            raise Exception(f"Failed to create session token: {str(e)}")

    async def send_password_reset_email(self, email: str) -> bool:
        """Generate password reset link for user

        Note: Firebase Admin SDK generates a link but doesn't send emails directly.
        For production, you would integrate with an email service to send the link.
        """
        if not self.is_available:
            raise Exception("Firebase not available")

        try:
            # Generate password reset link
            link = auth.generate_password_reset_link(email)
            logger.info(f"Password reset link generated for {email}")
            # In production, you would send this link via email
            # For now, just log that it was generated
            return True
        except auth.UserNotFoundError:
            # Don't reveal if user exists
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error generating password reset link: {e}")
            raise Exception(f"Failed to generate password reset: {str(e)}")

    @property
    def is_available(self) -> bool:
        """Check if Firebase is properly initialized"""
        return self._initialized and self.app is not None and FIREBASE_AVAILABLE


# Global Firebase auth service
firebase_auth_service = FirebaseAuthService()

# FastAPI dependency for authentication
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    try:
        # Extract token from Authorization header
        token = credentials.credentials

        # Verify token and get user data
        user_data = await firebase_auth_service.verify_token(token)

        # Update last login
        await firebase_auth_service.update_user_login(user_data["uid"])

        return user_data

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication required")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[Dict[str, Any]]:
    """FastAPI dependency for optional authentication"""
    if not credentials:
        return None

    try:
        return await firebase_auth_service.verify_token(credentials.credentials)
    except Exception:
        return None


def get_firebase_auth_service() -> FirebaseAuthService:
    """Get the global Firebase auth service"""
    return firebase_auth_service
