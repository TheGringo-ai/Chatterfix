import os
import json
import logging
from typing import Dict, Optional, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import Firebase modules with error handling
try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    import pyrebase
    FIREBASE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Firebase modules not available: {e}")
    firebase_admin = None
    credentials = None
    auth = None
    firestore = None
    pyrebase = None
    FIREBASE_AVAILABLE = False

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
        # Check if Firebase modules are available
        if not FIREBASE_AVAILABLE:
            logger.info("🔥 Firebase modules not installed - running in local/SQLite mode")
            logger.info("   To enable Firebase, install: pip install firebase-admin pyrebase4")
            return

        # Check if Firebase is explicitly disabled
        if os.getenv("DISABLE_FIREBASE", "").lower() in ("true", "1", "yes"):
            logger.info(
                "🔥 Firebase disabled via DISABLE_FIREBASE environment variable"
            )
            return

        # Check if credentials are available
        google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        firebase_api_key = os.getenv("FIREBASE_API_KEY")

        # Skip initialization if no credentials are configured
        if not google_creds_path and not firebase_api_key:
            logger.info("🔥 Firebase not configured - running in local/SQLite mode")
            logger.info(
                "   To enable Firebase, set GOOGLE_APPLICATION_CREDENTIALS or FIREBASE_API_KEY"
            )
            return

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
                            "projectId": os.getenv(
                                "GOOGLE_CLOUD_PROJECT", "chatterfix-cmms"
                            ),
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
                    "authDomain": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'chatterfix-cmms')}.firebaseapp.com",
                    "projectId": os.getenv("GOOGLE_CLOUD_PROJECT", "chatterfix-cmms"),
                    "storageBucket": f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'chatterfix-cmms')}.appspot.com",
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
        """Verify Firebase ID token and return user data"""
        try:
            if not self.app:
                raise HTTPException(status_code=500, detail="Firebase not initialized")

            # Verify the token
            decoded_token = auth.verify_id_token(token)

            # Get user data from Firebase Auth
            user_record = auth.get_user(decoded_token["uid"])

            # Get or create user in Firestore
            user_data = await self.get_or_create_user(user_record)

            return {
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
                "verified": decoded_token.get("email_verified", False),
                "user_data": user_data,
            }

        except firebase_admin.auth.InvalidIdTokenError:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        except firebase_admin.auth.ExpiredIdTokenError:
            raise HTTPException(status_code=401, detail="Authentication token expired")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    async def get_or_create_user(self, user_record) -> Dict[str, Any]:
        """Get user from Firestore or create if doesn't exist"""
        try:
            user_ref = self.db.collection("users").document(user_record.uid)
            user_doc = user_ref.get()

            if user_doc.exists:
                return user_doc.to_dict()
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

    async def update_user_login(self, uid: str):
        """Update user's last login timestamp"""
        try:
            user_ref = self.db.collection("users").document(uid)
            user_ref.update({"last_login": firestore.SERVER_TIMESTAMP})
        except Exception as e:
            logger.error(f"Error updating user login: {e}")

    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user data by UID"""
        try:
            user_ref = self.db.collection("users").document(uid)
            user_doc = user_ref.get()

            if user_doc.exists:
                return user_doc.to_dict()
            return None

        except Exception as e:
            logger.error(f"Error getting user by UID: {e}")
            return None

    async def update_user_profile(self, uid: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            user_ref = self.db.collection("users").document(uid)
            user_ref.update({**profile_data, "updated_at": firestore.SERVER_TIMESTAMP})
            return True

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False


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
    except:
        return None


def get_firebase_auth_service() -> FirebaseAuthService:
    """Get the global Firebase auth service"""
    return firebase_auth_service
