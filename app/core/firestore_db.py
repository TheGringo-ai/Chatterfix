import os
import logging
from typing import Dict, List, Optional, Any, cast
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    from google.cloud import firestore  # type: ignore
    from google.cloud.firestore_v1.base_query import FieldFilter
    FIRESTORE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ google-cloud-firestore not available. Firestore features will be disabled.")
    FIRESTORE_AVAILABLE = False
    firestore = None
    FieldFilter = None


class FirestoreDB:
    def __init__(self):
        self.db = None
        if FIRESTORE_AVAILABLE:
            self._initialize_client()
        else:
            logger.error("❌ Firestore client cannot be initialized: module not found")

    def _initialize_client(self):
        """Initialize Firestore client"""
        try:
            # For local development with service account
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if service_account_path and os.path.exists(service_account_path):
                self.db = firestore.Client.from_service_account_json(
                    service_account_path
                )
            else:
                # For GCP deployment with default credentials
                self.db = firestore.Client()
            logger.info("✅ Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore: {e}")
            self.db = None

    def get_client(self):
        """Get Firestore client"""
        if not self.db and FIRESTORE_AVAILABLE:
            self._initialize_client()
        return self.db


# Global Firestore instance
firestore_db = FirestoreDB()


class FirestoreManager:
    """Firestore database manager with CMMS-specific methods"""

    def __init__(self):
        self.db = firestore_db.get_client()

    async def create_document(
        self, collection: str, data: Dict[str, Any], doc_id: Optional[str] = None
    ) -> str:
        """Create a new document"""
        try:
            if not self.db:
                raise Exception("Firestore not initialized")

            # Add timestamp
            data["created_at"] = datetime.now(timezone.utc)
            data["updated_at"] = datetime.now(timezone.utc)

            if doc_id:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.set(data)
                return doc_id
            else:
                doc_ref = self.db.collection(collection).add(data)[1]
                return cast(str, doc_ref.id)
        except Exception as e:
            logger.error(f"Error creating document in {collection}: {e}")
            raise

    async def get_document(
        self, collection: str, doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        try:
            if not self.db:
                raise Exception("Firestore not initialized")

            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()

            if doc.exists:
                data = cast(Dict[str, Any], doc.to_dict())
                data["id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting document {doc_id} from {collection}: {e}")
            raise

    async def update_document(
        self, collection: str, doc_id: str, data: Dict[str, Any]
    ) -> bool:
        """Update a document"""
        try:
            if not self.db:
                raise Exception("Firestore not initialized")

            data["updated_at"] = datetime.now(timezone.utc)
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            logger.error(f"Error updating document {doc_id} in {collection}: {e}")
            raise

    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document"""
        try:
            if not self.db:
                raise Exception("Firestore not initialized")

            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id} from {collection}: {e}")
            raise

    async def get_collection(
        self,
        collection: str,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Get documents from a collection with optional filtering and ordering"""
        try:
            if not self.db:
                raise Exception("Firestore not initialized")

            query = self.db.collection(collection)

            # Apply filters
            if filters:
                for filter_item in filters:
                    query = query.where(
                        filter=FieldFilter(
                            filter_item["field"],
                            filter_item["operator"],
                            filter_item["value"],
                        )
                    )

            # Apply ordering
            if order_by:
                direction = (
                    firestore.Query.DESCENDING
                    if order_by.startswith("-")
                    else firestore.Query.ASCENDING
                )
                field = order_by.lstrip("-")
                query = query.order_by(field, direction=direction)

            # Apply limit
            if limit:
                query = query.limit(limit)

            docs = query.stream()
            results = []

            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            return results
        except Exception as e:
            logger.error(f"Error getting collection {collection}: {e}")
            raise

    # CMMS-specific methods
    async def create_work_order(self, work_order_data: Dict[str, Any]) -> str:
        """Create a new work order"""
        return await self.create_document("work_orders", work_order_data)

    async def get_work_orders(
        self, status: Optional[str] = None, assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get work orders with optional filtering"""
        filters = []
        if status:
            filters.append({"field": "status", "operator": "==", "value": status})
        if assigned_to:
            filters.append(
                {"field": "assigned_to", "operator": "==", "value": assigned_to}
            )

        return await self.get_collection(
            "work_orders", order_by="-created_at", filters=filters
        )

    async def create_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create a new asset"""
        return await self.create_document("assets", asset_data)

    async def get_assets(
        self, status: Optional[str] = None, location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get assets with optional filtering"""
        filters = []
        if status:
            filters.append({"field": "status", "operator": "==", "value": status})
        if location:
            filters.append({"field": "location", "operator": "==", "value": location})

        return await self.get_collection("assets", order_by="name", filters=filters)

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        return await self.create_document("users", user_data)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        users = await self.get_collection(
            "users", filters=[{"field": "email", "operator": "==", "value": email}]
        )
        return users[0] if users else None

    async def save_ai_interaction(self, user_message: str, ai_response: str) -> str:
        """Save AI interaction"""
        interaction_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": datetime.now(timezone.utc),
        }
        return await self.create_document("ai_interactions", interaction_data)

    async def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard data for a user"""
        try:
            # Get recent work orders
            work_orders = await self.get_collection(
                "work_orders",
                limit=10,
                order_by="-created_at",
                filters=[{"field": "assigned_to", "operator": "==", "value": user_id}],
            )

            # Get active assets
            assets = await self.get_collection(
                "assets",
                limit=5,
                filters=[{"field": "status", "operator": "==", "value": "Active"}],
            )

            # Get recent AI interactions
            ai_interactions = await self.get_collection(
                "ai_interactions", limit=5, order_by="-timestamp"
            )

            return {
                "work_orders": work_orders,
                "assets": assets,
                "ai_interactions": ai_interactions,
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"work_orders": [], "assets": [], "ai_interactions": []}


# Global Firestore manager instance
firestore_manager = FirestoreManager()


def get_firestore_manager() -> FirestoreManager:
    """Get the global Firestore manager instance"""
    return firestore_manager
