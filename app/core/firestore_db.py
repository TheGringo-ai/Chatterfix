import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast

from google.cloud import firestore  # type: ignore
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)

# Enforce Firestore availability

FIRESTORE_AVAILABLE = True


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

    async def get_asset_by_tag(self, asset_tag: str) -> Optional[Dict[str, Any]]:
        """Get asset by asset tag/barcode"""
        try:
            assets = await self.get_collection(
                "assets",
                limit=1,
                filters=[{"field": "asset_tag", "operator": "==", "value": asset_tag}],
            )
            return assets[0] if assets else None
        except Exception as e:
            logger.error(f"Error getting asset by tag: {e}")
            return None

    async def find_asset_by_identifier(
        self, identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Find asset by serial number, name, or other identifier"""
        try:
            # Try by serial number first
            assets = await self.get_collection(
                "assets",
                limit=1,
                filters=[
                    {"field": "serial_number", "operator": "==", "value": identifier}
                ],
            )
            if assets:
                return assets[0]

            # Try by name (partial match)
            assets = await self.get_collection(
                "assets",
                limit=10,
                filters=[{"field": "name", "operator": ">=", "value": identifier}],
            )
            # Filter for exact or close matches
            for asset in assets:
                if identifier.lower() in asset.get("name", "").lower():
                    return asset

            return None
        except Exception as e:
            logger.error(f"Error finding asset by identifier: {e}")
            return None

    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset by ID"""
        try:
            doc = await self.get_document("assets", str(asset_id))
            return doc
        except Exception as e:
            logger.error(f"Error getting asset: {e}")
            return None

    async def get_asset_work_orders(self, asset_id: str) -> List[Dict[str, Any]]:
        """Get work orders for an asset"""
        try:
            work_orders = await self.get_collection(
                "work_orders",
                order_by="-created_at",
                filters=[
                    {"field": "asset_id", "operator": "==", "value": str(asset_id)}
                ],
            )
            return work_orders
        except Exception as e:
            logger.error(f"Error getting asset work orders: {e}")
            return []

    async def get_asset_parts(self, asset_id: str) -> List[Dict[str, Any]]:
        """Get parts for an asset"""
        try:
            parts = await self.get_collection(
                "asset_parts",
                filters=[
                    {"field": "asset_id", "operator": "==", "value": str(asset_id)}
                ],
            )
            # Get detailed part information
            detailed_parts = []
            for asset_part in parts:
                part_id = asset_part.get("part_id")
                if part_id:
                    part_doc = await self.get_document("parts", part_id)
                    if part_doc:
                        part_doc.update(
                            {
                                "quantity_used": asset_part.get("quantity_used"),
                                "last_replaced": asset_part.get("last_replaced"),
                                "replacement_interval": asset_part.get(
                                    "replacement_interval"
                                ),
                            }
                        )
                        detailed_parts.append(part_doc)
            return detailed_parts
        except Exception as e:
            logger.error(f"Error getting asset parts: {e}")
            return []

    async def count_asset_work_orders(self, asset_id: str) -> int:
        """Count work orders for an asset"""
        try:
            work_orders = await self.get_asset_work_orders(asset_id)
            return len(work_orders)
        except Exception as e:
            logger.error(f"Error counting asset work orders: {e}")
            return 0

    async def count_asset_parts(self, asset_id: str) -> int:
        """Count parts for an asset"""
        try:
            parts = await self.get_asset_parts(asset_id)
            return len(parts)
        except Exception as e:
            logger.error(f"Error counting asset parts: {e}")
            return 0

    # Training-specific methods
    async def create_training_module(self, module_data: Dict[str, Any]) -> str:
        """Create a new training module"""
        return await self.create_document("training_modules", module_data)

    async def get_training_modules(
        self, skill_category: Optional[str] = None, asset_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get training modules with optional filtering"""
        filters = []
        if skill_category:
            filters.append(
                {"field": "skill_category", "operator": "==", "value": skill_category}
            )
        if asset_type:
            filters.append(
                {"field": "asset_type", "operator": "==", "value": asset_type}
            )

        return await self.get_collection(
            "training_modules",
            order_by="-created_at",
            filters=filters if filters else None,
        )

    async def create_user_training(self, training_data: Dict[str, Any]) -> str:
        """Create a new user training assignment"""
        return await self.create_document("user_training", training_data)

    async def get_user_training(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user training assignments"""
        filters = [{"field": "user_id", "operator": "==", "value": user_id}]
        if status:
            filters.append({"field": "status", "operator": "==", "value": status})

        return await self.get_collection("user_training", filters=filters)

    async def update_user_training_status(
        self, user_id: str, module_id: str, status: str, **kwargs
    ) -> bool:
        """Update user training status"""
        try:
            # Find the training record
            training_records = await self.get_collection(
                "user_training",
                filters=[
                    {"field": "user_id", "operator": "==", "value": user_id},
                    {
                        "field": "training_module_id",
                        "operator": "==",
                        "value": module_id,
                    },
                ],
                limit=1,
            )

            if not training_records:
                return False

            # Update the record
            update_data = {"status": status}
            update_data.update(kwargs)

            await self.update_document(
                "user_training", training_records[0]["id"], update_data
            )
            return True
        except Exception as e:
            logger.error(f"Error updating user training status: {e}")
            return False

    async def get_user_performance(
        self, user_id: str, period: str = "monthly"
    ) -> List[Dict[str, Any]]:
        """Get user performance metrics"""
        filters = [
            {"field": "user_id", "operator": "==", "value": user_id},
            {"field": "period", "operator": "==", "value": period},
        ]

        return await self.get_collection(
            "user_performance", order_by="-period_date", filters=filters
        )

    async def update_user_performance_metrics(
        self, user_id: str, period: str, period_date: str, metrics: Dict[str, Any]
    ) -> str:
        """Update or create user performance metrics"""
        try:
            # Check if record exists
            existing = await self.get_collection(
                "user_performance",
                filters=[
                    {"field": "user_id", "operator": "==", "value": user_id},
                    {"field": "period", "operator": "==", "value": period},
                    {"field": "period_date", "operator": "==", "value": period_date},
                ],
                limit=1,
            )

            if existing:
                # Update existing record
                await self.update_document(
                    "user_performance", existing[0]["id"], metrics
                )
                return existing[0]["id"]
            else:
                # Create new record
                performance_data = {
                    "user_id": user_id,
                    "period": period,
                    "period_date": period_date,
                    **metrics,
                }
                return await self.create_document("user_performance", performance_data)
        except Exception as e:
            logger.error(f"Error updating user performance metrics: {e}")
            raise


# Global Firestore manager instance
firestore_manager = FirestoreManager()


def get_firestore_manager() -> FirestoreManager:
    """Get the global Firestore manager instance"""
    return firestore_manager


class FirestoreSQLiteWrapper:
    """SQLite-compatible wrapper for Firestore operations"""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()
        self.last_query_result = None

    def execute(self, query: str, params=None):
        """Execute a SQL-like query (returns self for chaining)"""
        # For demo/development, we'll return mock data
        # In production, you'd implement proper SQL->Firestore translation
        logger.warning(f"SQLite-style query not fully implemented: {query[:50]}...")

        # Return mock data for common queries to keep the app functional
        if "SELECT" in query.upper():
            if "users" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "full_name": "Demo User",
                        "role": "technician",
                        "status": "available",
                    },
                    {
                        "id": 2,
                        "full_name": "Manager Demo",
                        "role": "manager",
                        "status": "available",
                    },
                ]
            elif "team_messages" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "sender_name": "Demo User",
                        "message": "Demo message",
                        "created_date": datetime.now(),
                    }
                ]
            elif "assets" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "name": "Demo Asset",
                        "status": "Active",
                        "criticality": "Medium",
                    }
                ]
            else:
                self.last_query_result = []
        else:
            # For INSERT, UPDATE, DELETE operations
            self.last_query_result = None

        return self

    def fetchall(self):
        """Fetch all results from last query"""
        return self.last_query_result or []

    def fetchone(self):
        """Fetch one result from last query"""
        if self.last_query_result and len(self.last_query_result) > 0:
            return self.last_query_result[0]
        return None

    def commit(self):
        """Commit transaction (no-op for demo)"""
        pass

    def close(self):
        """Close connection (no-op)"""
        pass

    @property
    def lastrowid(self):
        """Return last inserted row ID (mock)"""
        return 1


def get_db_connection():
    """Get a SQLite-compatible database connection for existing routers"""
    return FirestoreSQLiteWrapper()
