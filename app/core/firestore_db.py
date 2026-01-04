import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast

from google.cloud import firestore  # type: ignore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds

logger = logging.getLogger(__name__)

# Enforce Firestore availability

FIRESTORE_AVAILABLE = True


def convert_firestore_timestamps(data: Any) -> Any:
    """
    Convert Firestore DatetimeWithNanoseconds objects to JSON-serializable datetime strings
    """
    if isinstance(data, dict):
        return {key: convert_firestore_timestamps(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_firestore_timestamps(item) for item in data]
    elif isinstance(data, DatetimeWithNanoseconds):
        return data.isoformat()
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


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
            if service_account_path:
                # Convert relative path to absolute path
                if not os.path.isabs(service_account_path):
                    service_account_path = os.path.join(
                        os.getcwd(), service_account_path
                    )

                if os.path.exists(service_account_path):
                    self.db = firestore.Client.from_service_account_json(
                        service_account_path
                    )
                    logger.info(
                        f"✅ Firestore client initialized with credentials: {service_account_path}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Credentials file not found: {service_account_path}"
                    )
                    # Try default credentials for GCP deployment
                    self.db = firestore.Client()
                    logger.info(
                        "✅ Firestore client initialized with default credentials"
                    )
            else:
                # For GCP deployment with default credentials
                self.db = firestore.Client()
                logger.info("✅ Firestore client initialized with default credentials")
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
                # Use provided document ID
                final_doc_id = doc_id
            else:
                # Generate a unique document ID using UUID
                final_doc_id = uuid.uuid4().hex

            # Use set() which overwrites if exists - more reliable than add()
            doc_ref = self.db.collection(collection).document(final_doc_id)
            doc_ref.set(data)
            logger.info(f"Created document {final_doc_id} in {collection}")
            return final_doc_id
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
                # Convert Firestore timestamps to JSON-serializable format
                return convert_firestore_timestamps(data)
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
                # Convert Firestore timestamps to JSON-serializable format
                results.append(convert_firestore_timestamps(data))

            return results
        except Exception as e:
            error_str = str(e)
            # Handle missing index gracefully - return empty list with warning
            if "requires an index" in error_str.lower():
                logger.warning(f"Missing Firestore index for {collection} query - returning empty results")
                return []
            logger.error(f"Error getting collection {collection}: {e}")
            raise

    # ==========================================
    # ORGANIZATION-SCOPED METHODS (Multi-Tenant)
    # ==========================================

    async def create_org_document(
        self,
        collection: str,
        data: Dict[str, Any],
        organization_id: str,
        doc_id: Optional[str] = None,
    ) -> str:
        """Create a document scoped to an organization"""
        data["organization_id"] = organization_id
        return await self.create_document(collection, data, doc_id)

    async def get_org_collection(
        self,
        collection: str,
        organization_id: str,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        additional_filters: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Get documents from a collection filtered by organization_id"""
        filters = [
            {"field": "organization_id", "operator": "==", "value": organization_id}
        ]
        if additional_filters:
            filters.extend(additional_filters)
        return await self.get_collection(
            collection, limit=limit, order_by=order_by, filters=filters
        )

    async def get_org_document(
        self, collection: str, doc_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a document and verify it belongs to the organization"""
        doc = await self.get_document(collection, doc_id)
        if doc and doc.get("organization_id") == organization_id:
            return doc
        return None

    async def update_org_document(
        self, collection: str, doc_id: str, data: Dict[str, Any], organization_id: str
    ) -> bool:
        """Update a document only if it belongs to the organization"""
        # Verify ownership first
        doc = await self.get_document(collection, doc_id)
        if not doc or doc.get("organization_id") != organization_id:
            logger.warning(
                f"Attempted to update doc {doc_id} not belonging to org {organization_id}"
            )
            return False
        return await self.update_document(collection, doc_id, data)

    async def delete_org_document(
        self, collection: str, doc_id: str, organization_id: str
    ) -> bool:
        """Delete a document only if it belongs to the organization"""
        # Verify ownership first
        doc = await self.get_document(collection, doc_id)
        if not doc or doc.get("organization_id") != organization_id:
            logger.warning(
                f"Attempted to delete doc {doc_id} not belonging to org {organization_id}"
            )
            return False
        return await self.delete_document(collection, doc_id)

    # ==========================================
    # CMMS-SPECIFIC ORGANIZATION-SCOPED METHODS
    # ==========================================

    async def create_org_work_order(
        self, work_order_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Create a work order for an organization"""
        return await self.create_org_document(
            "work_orders", work_order_data, organization_id
        )

    async def get_org_work_orders(
        self,
        organization_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get work orders for an organization"""
        additional_filters = []
        if status:
            additional_filters.append(
                {"field": "status", "operator": "==", "value": status}
            )
        if assigned_to:
            additional_filters.append(
                {"field": "assigned_to", "operator": "==", "value": assigned_to}
            )
        return await self.get_org_collection(
            "work_orders",
            organization_id,
            limit=limit,
            additional_filters=additional_filters if additional_filters else None,
        )

    async def create_org_asset(
        self, asset_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Create an asset for an organization"""
        return await self.create_org_document("assets", asset_data, organization_id)

    async def get_org_assets(
        self,
        organization_id: str,
        status: Optional[str] = None,
        location: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get assets for an organization"""
        additional_filters = []
        if status:
            additional_filters.append(
                {"field": "status", "operator": "==", "value": status}
            )
        if location:
            additional_filters.append(
                {"field": "location", "operator": "==", "value": location}
            )
        return await self.get_org_collection(
            "assets",
            organization_id,
            order_by="name",
            limit=limit,
            additional_filters=additional_filters if additional_filters else None,
        )

    async def create_org_part(
        self, part_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Create a part/inventory item for an organization"""
        return await self.create_org_document("parts", part_data, organization_id)

    async def get_org_parts(
        self,
        organization_id: str,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get parts for an organization"""
        additional_filters = []
        if category:
            additional_filters.append(
                {"field": "category", "operator": "==", "value": category}
            )
        return await self.get_org_collection(
            "parts",
            organization_id,
            order_by="name",
            limit=limit,
            additional_filters=additional_filters if additional_filters else None,
        )

    async def create_org_vendor(
        self, vendor_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Create a vendor for an organization"""
        return await self.create_org_document("vendors", vendor_data, organization_id)

    async def get_org_vendors(
        self, organization_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get vendors for an organization"""
        return await self.get_org_collection(
            "vendors", organization_id, order_by="name", limit=limit
        )

    async def get_org_asset(
        self, asset_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single asset by ID with organization verification.

        Returns None if asset doesn't exist or belongs to different org.
        """
        return await self.get_org_document("assets", asset_id, organization_id)

    async def get_org_asset_by_tag(
        self, asset_tag: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get asset by asset tag/barcode within organization scope."""
        try:
            assets = await self.get_org_collection(
                "assets",
                organization_id,
                limit=1,
                additional_filters=[
                    {"field": "asset_tag", "operator": "==", "value": asset_tag}
                ],
            )
            return assets[0] if assets else None
        except Exception as e:
            logger.error(f"Error getting org asset by tag: {e}")
            return None

    async def get_org_asset_work_orders(
        self, asset_id: str, organization_id: str
    ) -> List[Dict[str, Any]]:
        """Get work orders for an asset within organization scope."""
        try:
            return await self.get_org_collection(
                "work_orders",
                organization_id,
                order_by="-created_at",
                additional_filters=[
                    {"field": "asset_id", "operator": "==", "value": str(asset_id)}
                ],
            )
        except Exception as e:
            logger.error(f"Error getting org asset work orders: {e}")
            return []

    async def get_org_work_order(
        self, work_order_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single work order by ID with organization verification.

        Returns None if work order doesn't exist or belongs to different org.
        """
        return await self.get_org_document("work_orders", work_order_id, organization_id)

    async def update_org_work_order(
        self, work_order_id: str, data: Dict[str, Any], organization_id: str
    ) -> bool:
        """Update a work order with organization verification."""
        return await self.update_org_document(
            "work_orders", work_order_id, data, organization_id
        )

    async def delete_org_work_order(
        self, work_order_id: str, organization_id: str
    ) -> bool:
        """Delete a work order with organization verification."""
        return await self.delete_org_document("work_orders", work_order_id, organization_id)

    async def get_org_dashboard_data(
        self, organization_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Get dashboard data for an organization"""
        try:
            # Get recent work orders for this organization
            work_orders = await self.get_org_work_orders(organization_id, limit=10)

            # Get active assets for this organization
            assets = await self.get_org_assets(
                organization_id, status="Active", limit=5
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
            logger.error(f"Error getting org dashboard data: {e}")
            return {"work_orders": [], "assets": [], "ai_interactions": []}

    # ==========================================
    # PM AUTOMATION METHODS (Preventive Maintenance)
    # ==========================================

    # --- PM Templates ---

    async def create_pm_template(
        self,
        template_data: Dict[str, Any],
        organization_id: Optional[str] = None,
    ) -> str:
        """
        Create a PM template. If organization_id is None, creates a global template.
        Global templates are available to all organizations.
        """
        if organization_id:
            template_data["organization_id"] = organization_id
        else:
            template_data["organization_id"] = None  # Global template
        return await self.create_document("pm_templates", template_data)

    async def get_pm_templates(
        self,
        organization_id: str,
        maintenance_type: Optional[str] = None,
        include_global: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get PM templates for an organization.
        Includes global templates (organization_id=null) if include_global=True.
        """
        templates = []

        # Get org-specific templates
        org_filters = [
            {"field": "organization_id", "operator": "==", "value": organization_id}
        ]
        if maintenance_type:
            org_filters.append(
                {"field": "maintenance_type", "operator": "==", "value": maintenance_type}
            )
        org_templates = await self.get_collection(
            "pm_templates", filters=org_filters, order_by="name"
        )
        templates.extend(org_templates)

        # Get global templates
        if include_global:
            global_filters = [
                {"field": "organization_id", "operator": "==", "value": None}
            ]
            if maintenance_type:
                global_filters.append(
                    {"field": "maintenance_type", "operator": "==", "value": maintenance_type}
                )
            global_templates = await self.get_collection(
                "pm_templates", filters=global_filters, order_by="name"
            )
            templates.extend(global_templates)

        return templates

    async def get_pm_template(
        self, template_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific PM template (org-specific or global)"""
        template = await self.get_document("pm_templates", template_id)
        if not template:
            return None
        # Allow access if it's the org's template or a global template
        if template.get("organization_id") in [organization_id, None]:
            return template
        return None

    async def update_pm_template(
        self, template_id: str, data: Dict[str, Any], organization_id: str
    ) -> bool:
        """Update a PM template (only org-specific templates can be updated)"""
        template = await self.get_document("pm_templates", template_id)
        if not template:
            return False
        # Only allow updating org-specific templates, not global ones
        if template.get("organization_id") != organization_id:
            logger.warning(
                f"Cannot update template {template_id} - not owned by org {organization_id}"
            )
            return False
        return await self.update_document("pm_templates", template_id, data)

    async def delete_pm_template(self, template_id: str, organization_id: str) -> bool:
        """Delete a PM template (only org-specific templates can be deleted)"""
        template = await self.get_document("pm_templates", template_id)
        if not template:
            return False
        if template.get("organization_id") != organization_id:
            logger.warning(
                f"Cannot delete template {template_id} - not owned by org {organization_id}"
            )
            return False
        return await self.delete_document("pm_templates", template_id)

    # --- PM Schedule Rules ---

    async def create_pm_schedule_rule(
        self, rule_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Create a PM schedule rule for an organization"""
        return await self.create_org_document("pm_schedule_rules", rule_data, organization_id)

    async def get_pm_schedule_rules(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        schedule_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get PM schedule rules for an organization with optional filters"""
        additional_filters = []
        if asset_id:
            additional_filters.append(
                {"field": "asset_id", "operator": "==", "value": asset_id}
            )
        if is_active is not None:
            additional_filters.append(
                {"field": "is_active", "operator": "==", "value": is_active}
            )
        if schedule_type:
            additional_filters.append(
                {"field": "schedule_type", "operator": "==", "value": schedule_type}
            )
        return await self.get_org_collection(
            "pm_schedule_rules",
            organization_id,
            order_by="next_due",
            additional_filters=additional_filters if additional_filters else None,
        )

    async def get_pm_schedule_rule(
        self, rule_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific PM schedule rule"""
        return await self.get_org_document("pm_schedule_rules", rule_id, organization_id)

    async def update_pm_schedule_rule(
        self, rule_id: str, data: Dict[str, Any], organization_id: str
    ) -> bool:
        """Update a PM schedule rule"""
        return await self.update_org_document(
            "pm_schedule_rules", rule_id, data, organization_id
        )

    async def delete_pm_schedule_rule(self, rule_id: str, organization_id: str) -> bool:
        """Delete a PM schedule rule"""
        return await self.delete_org_document("pm_schedule_rules", rule_id, organization_id)

    async def get_due_pm_rules(
        self, organization_id: str, due_before: datetime
    ) -> List[Dict[str, Any]]:
        """Get PM rules that are due before a specific date"""
        return await self.get_org_collection(
            "pm_schedule_rules",
            organization_id,
            additional_filters=[
                {"field": "is_active", "operator": "==", "value": True},
                {"field": "next_due", "operator": "<=", "value": due_before},
            ],
            order_by="next_due",
        )

    # --- Asset Meters ---

    async def create_asset_meter(
        self, meter_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Create an asset meter for tracking usage/conditions"""
        return await self.create_org_document("asset_meters", meter_data, organization_id)

    async def get_asset_meters(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        meter_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get asset meters for an organization"""
        additional_filters = []
        if asset_id:
            additional_filters.append(
                {"field": "asset_id", "operator": "==", "value": asset_id}
            )
        if meter_type:
            additional_filters.append(
                {"field": "meter_type", "operator": "==", "value": meter_type}
            )
        return await self.get_org_collection(
            "asset_meters",
            organization_id,
            additional_filters=additional_filters if additional_filters else None,
        )

    async def get_asset_meter(
        self, meter_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific asset meter"""
        return await self.get_org_document("asset_meters", meter_id, organization_id)

    async def update_asset_meter(
        self, meter_id: str, data: Dict[str, Any], organization_id: str
    ) -> bool:
        """Update an asset meter (e.g., update current_value)"""
        return await self.update_org_document("asset_meters", meter_id, data, organization_id)

    async def update_meter_reading(
        self,
        meter_id: str,
        new_value: float,
        organization_id: str,
        reading_source: str = "manual",
    ) -> Dict[str, Any]:
        """
        Update a meter reading and return the updated meter with threshold status.
        reading_source: 'manual', 'iot', 'api'
        """
        meter = await self.get_asset_meter(meter_id, organization_id)
        if not meter:
            raise ValueError(f"Meter {meter_id} not found")

        old_value = meter.get("current_value", 0)
        update_data = {
            "current_value": new_value,
            "last_reading_date": datetime.now(timezone.utc),
            "last_reading_source": reading_source,
            "previous_value": old_value,
        }

        await self.update_asset_meter(meter_id, update_data, organization_id)

        # Check thresholds
        threshold_warning = meter.get("threshold_warning")
        threshold_critical = meter.get("threshold_critical")
        threshold_status = "normal"

        if threshold_critical and new_value >= threshold_critical:
            threshold_status = "critical"
        elif threshold_warning and new_value >= threshold_warning:
            threshold_status = "warning"

        return {
            "meter_id": meter_id,
            "asset_id": meter.get("asset_id"),
            "meter_type": meter.get("meter_type"),
            "old_value": old_value,
            "new_value": new_value,
            "unit": meter.get("unit"),
            "threshold_status": threshold_status,
            "threshold_warning": threshold_warning,
            "threshold_critical": threshold_critical,
        }

    async def delete_asset_meter(self, meter_id: str, organization_id: str) -> bool:
        """Delete an asset meter"""
        return await self.delete_org_document("asset_meters", meter_id, organization_id)

    async def get_meters_exceeding_threshold(
        self, organization_id: str, threshold_type: str = "warning"
    ) -> List[Dict[str, Any]]:
        """
        Get meters that have exceeded their warning or critical threshold.
        This requires fetching all meters and filtering in code since Firestore
        doesn't support comparing two fields directly.
        """
        meters = await self.get_asset_meters(organization_id)
        exceeding = []

        for meter in meters:
            current = meter.get("current_value", 0)
            if threshold_type == "critical":
                threshold = meter.get("threshold_critical")
            else:
                threshold = meter.get("threshold_warning")

            if threshold and current >= threshold:
                meter["threshold_exceeded"] = threshold_type
                exceeding.append(meter)

        return exceeding

    # --- PM Generated Orders (Tracking) ---

    async def create_pm_generated_order(
        self, order_data: Dict[str, Any], organization_id: str
    ) -> str:
        """Create a record of a PM-generated work order"""
        return await self.create_org_document(
            "pm_generated_orders", order_data, organization_id
        )

    async def get_pm_generated_orders(
        self,
        organization_id: str,
        status: Optional[str] = None,
        rule_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get PM generated order records"""
        additional_filters = []
        if status:
            additional_filters.append(
                {"field": "status", "operator": "==", "value": status}
            )
        if rule_id:
            additional_filters.append(
                {"field": "rule_id", "operator": "==", "value": rule_id}
            )
        if asset_id:
            additional_filters.append(
                {"field": "asset_id", "operator": "==", "value": asset_id}
            )
        return await self.get_org_collection(
            "pm_generated_orders",
            organization_id,
            limit=limit,
            order_by="-generated_date",
            additional_filters=additional_filters if additional_filters else None,
        )

    async def update_pm_generated_order(
        self, order_id: str, data: Dict[str, Any], organization_id: str
    ) -> bool:
        """Update a PM generated order record (e.g., mark as deferred)"""
        return await self.update_org_document(
            "pm_generated_orders", order_id, data, organization_id
        )

    async def link_pm_order_to_work_order(
        self, pm_order_id: str, work_order_id: str, organization_id: str
    ) -> bool:
        """Link a PM generated order to an actual work order"""
        return await self.update_pm_generated_order(
            pm_order_id,
            {"work_order_id": work_order_id, "status": "work_order_created"},
            organization_id,
        )

    async def get_pm_order_by_idempotency_key(
        self, idempotency_key: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a PM order already exists with the given idempotency key.

        Idempotency keys follow the format: {organization_id}_{rule_id}_{YYYYMMDD}
        This prevents duplicate work orders from being created for the same rule on the same day.

        Returns the existing PM order if found, None otherwise.
        """
        try:
            results = await self.get_org_collection(
                "pm_generated_orders",
                organization_id,
                limit=1,
                additional_filters=[
                    {"field": "idempotency_key", "operator": "==", "value": idempotency_key}
                ],
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error checking idempotency key {idempotency_key}: {e}")
            return None

    # --- PM Dashboard/Analytics Methods ---

    async def get_pm_overview(
        self, organization_id: str, days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Get a comprehensive PM overview for the organization"""
        try:
            # Get active schedule rules
            active_rules = await self.get_pm_schedule_rules(
                organization_id, is_active=True
            )

            # Get due rules (next 30 days by default)
            due_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
            due_rules = await self.get_due_pm_rules(organization_id, due_date)

            # Get meters exceeding thresholds
            warning_meters = await self.get_meters_exceeding_threshold(
                organization_id, "warning"
            )
            critical_meters = await self.get_meters_exceeding_threshold(
                organization_id, "critical"
            )

            # Get recent PM generated orders
            recent_pm_orders = await self.get_pm_generated_orders(
                organization_id, limit=10
            )

            # Get templates
            templates = await self.get_pm_templates(organization_id)

            # Calculate stats
            overdue_count = sum(
                1
                for rule in due_rules
                if rule.get("next_due")
                and datetime.fromisoformat(rule["next_due"].replace("Z", "+00:00"))
                < datetime.now(timezone.utc)
            )

            return {
                "summary": {
                    "total_active_rules": len(active_rules),
                    "rules_due_soon": len(due_rules),
                    "overdue_count": overdue_count,
                    "meters_warning": len(warning_meters),
                    "meters_critical": len(critical_meters),
                    "total_templates": len(templates),
                },
                "due_rules": due_rules[:10],  # Top 10 due soonest
                "critical_meters": critical_meters,
                "warning_meters": warning_meters[:5],  # Top 5 warnings
                "recent_pm_orders": recent_pm_orders,
            }
        except Exception as e:
            logger.error(f"Error getting PM overview: {e}")
            return {
                "summary": {
                    "total_active_rules": 0,
                    "rules_due_soon": 0,
                    "overdue_count": 0,
                    "meters_warning": 0,
                    "meters_critical": 0,
                    "total_templates": 0,
                },
                "due_rules": [],
                "critical_meters": [],
                "warning_meters": [],
                "recent_pm_orders": [],
            }

    # ==========================================
    # LEGACY CMMS METHODS - DEPRECATED
    # ==========================================
    # WARNING: These methods do NOT enforce organization isolation!
    # They are kept for backward compatibility but should NOT be used
    # in production code. Use the org-scoped versions instead:
    #   - create_org_work_order() instead of create_work_order()
    #   - get_org_work_orders() instead of get_work_orders()
    #   - get_org_assets() instead of get_assets()
    #   - get_org_dashboard_data() instead of get_dashboard_data()
    # ==========================================

    async def create_work_order(self, work_order_data: Dict[str, Any]) -> str:
        """DEPRECATED: Use create_org_work_order() for multi-tenant safety"""
        logger.warning(
            "DEPRECATED: create_work_order() called - use create_org_work_order() instead for multi-tenant safety"
        )
        return await self.create_document("work_orders", work_order_data)

    async def get_work_orders(
        self, status: Optional[str] = None, assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """DEPRECATED: Use get_org_work_orders() for multi-tenant safety - Returns ALL work orders without org filtering!"""
        logger.warning(
            "DEPRECATED: get_work_orders() called - use get_org_work_orders() instead for multi-tenant safety"
        )
        # Simplified query to avoid composite index requirement
        # Apply single filter only to avoid index conflicts
        filters = []
        if status and not assigned_to:
            filters.append({"field": "status", "operator": "==", "value": status})
        elif assigned_to and not status:
            filters.append(
                {"field": "assigned_to", "operator": "==", "value": assigned_to}
            )
        # If both filters are requested, only use status to avoid composite index requirement

        return await self.get_collection(
            "work_orders",
            order_by=(
                "-created_at" if not filters else None
            ),  # Remove ordering when filtering to avoid index issues
            filters=filters if filters else None,
        )

    async def create_asset(self, asset_data: Dict[str, Any]) -> str:
        """DEPRECATED: Use create_org_asset() for multi-tenant safety"""
        logger.warning(
            "DEPRECATED: create_asset() called - use create_org_asset() instead for multi-tenant safety"
        )
        return await self.create_document("assets", asset_data)

    async def get_assets(
        self, status: Optional[str] = None, location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """DEPRECATED: Use get_org_assets() for multi-tenant safety - Returns ALL assets without org filtering!"""
        logger.warning(
            "DEPRECATED: get_assets() called - use get_org_assets() instead for multi-tenant safety"
        )
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
        """DEPRECATED: Use get_org_dashboard_data() for multi-tenant safety - Returns ALL data without org filtering!"""
        logger.warning(
            "DEPRECATED: get_dashboard_data() called - use get_org_dashboard_data() instead for multi-tenant safety"
        )
        try:
            # Get recent work orders (simplified query to avoid index issues)
            work_orders = await self.get_collection(
                "work_orders",
                limit=10,
                # Removed filters to avoid composite index requirement
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
        # For demo/development, we'll return comprehensive mock data
        # In production, you'd implement proper SQL->Firestore translation
        logger.warning(f"SQLite-style query not fully implemented: {query[:50]}...")

        # Return mock data for common queries to keep the app functional
        if "SELECT" in query.upper():
            # Resource capacity query (technicians with work load)
            if "users" in query.lower() and "total_hours" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "full_name": "John Smith",
                        "username": "jsmith",
                        "status": "available",
                        "role": "technician",
                        "active_work_orders": 3,
                        "urgent_count": 1,
                        "total_hours": 15.5,
                    },
                    {
                        "id": 2,
                        "full_name": "Sarah Johnson",
                        "username": "sjohnson",
                        "status": "available",
                        "role": "technician",
                        "active_work_orders": 2,
                        "urgent_count": 0,
                        "total_hours": 8.0,
                    },
                    {
                        "id": 3,
                        "full_name": "Mike Davis",
                        "username": "mdavis",
                        "status": "on_job",
                        "role": "technician",
                        "active_work_orders": 4,
                        "urgent_count": 2,
                        "total_hours": 22.0,
                    },
                ]
            # Work order backlog query
            elif "work_orders" in query.lower() and "priority" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "title": "Fix HVAC System - Building A",
                        "priority": "high",
                        "status": "pending",
                        "created_date": (datetime.now() - timedelta(days=2)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "due_date": (datetime.now() + timedelta(days=5)).strftime(
                            "%Y-%m-%d"
                        ),
                        "estimated_duration": 4.0,
                        "asset_name": "HVAC-001",
                        "asset_id": 1,
                        "criticality": 4,
                        "urgency": "due_this_week",
                    },
                    {
                        "id": 2,
                        "title": "Inspect Fire Suppression System",
                        "priority": "urgent",
                        "status": "pending",
                        "created_date": (datetime.now() - timedelta(days=5)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "due_date": datetime.now().strftime("%Y-%m-%d"),
                        "estimated_duration": 2.0,
                        "asset_name": "FIRE-SUPP-001",
                        "asset_id": 2,
                        "criticality": 5,
                        "urgency": "due_today",
                    },
                    {
                        "id": 3,
                        "title": "Replace Air Filters",
                        "priority": "medium",
                        "status": "pending",
                        "created_date": (datetime.now() - timedelta(days=1)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "due_date": (datetime.now() + timedelta(days=10)).strftime(
                            "%Y-%m-%d"
                        ),
                        "estimated_duration": 1.5,
                        "asset_name": "HVAC-002",
                        "asset_id": 3,
                        "criticality": 2,
                        "urgency": "future",
                    },
                ]
            # Asset PM status query
            elif "assets" in query.lower() and "last_maintenance" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "name": "HVAC Unit - Building A",
                        "asset_id": "HVAC-001",
                        "category": "HVAC",
                        "criticality": 4,
                        "location": "Building A - Roof",
                        "total_work_orders": 5,
                        "last_maintenance": (
                            datetime.now() - timedelta(days=45)
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "next_pm_date": (datetime.now() + timedelta(days=15)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                    {
                        "id": 2,
                        "name": "Fire Suppression System",
                        "asset_id": "FIRE-SUPP-001",
                        "category": "Safety",
                        "criticality": 5,
                        "location": "Building A - Ground Floor",
                        "total_work_orders": 3,
                        "last_maintenance": (
                            datetime.now() - timedelta(days=150)
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "next_pm_date": datetime.now().strftime("%Y-%m-%d"),
                    },
                ]
            # Scheduling conflicts query
            elif (
                "users" in query.lower()
                and "work_orders" in query.lower()
                and "total_hours" in query.lower()
            ):
                self.last_query_result = [
                    {
                        "technician_id": 3,
                        "technician_name": "Mike Davis",
                        "due_date": datetime.now().strftime("%Y-%m-%d"),
                        "work_order_count": 3,
                        "total_hours": 10.5,
                        "work_orders": "Fix Elevator | Inspect Boiler | Replace Pump",
                    }
                ]
            # Parts requests/availability query
            elif (
                "parts_requests" in query.lower() or "parts_inventory" in query.lower()
            ):
                if "parts_requests" in query.lower():
                    self.last_query_result = [
                        {
                            "id": 1,
                            "part_name": "HVAC Filter",
                            "quantity": 4,
                            "status": "pending",
                            "priority": "high",
                            "requested_date": (
                                datetime.now() - timedelta(days=2)
                            ).strftime("%Y-%m-%d"),
                            "expected_delivery": (
                                datetime.now() + timedelta(days=3)
                            ).strftime("%Y-%m-%d"),
                            "work_order_title": "Replace Air Filters",
                            "work_order_due": (
                                datetime.now() + timedelta(days=10)
                            ).strftime("%Y-%m-%d"),
                            "requester": "John Smith",
                        }
                    ]
                else:
                    self.last_query_result = [
                        {
                            "part_name": "Emergency Valve",
                            "quantity": 2,
                            "min_quantity": 5,
                            "location": "Warehouse A",
                        }
                    ]
            # Generic users query
            elif "users" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "full_name": "John Smith",
                        "username": "jsmith",
                        "role": "technician",
                        "status": "available",
                    },
                    {
                        "id": 2,
                        "full_name": "Sarah Johnson",
                        "username": "sjohnson",
                        "role": "technician",
                        "status": "available",
                    },
                    {
                        "id": 3,
                        "full_name": "Mike Davis",
                        "username": "mdavis",
                        "role": "manager",
                        "status": "available",
                    },
                ]
            # Team messages query
            elif "team_messages" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "sender_name": "John Smith",
                        "message": "HVAC unit in Building A needs urgent attention",
                        "created_date": datetime.now(),
                    }
                ]
            # Generic assets query
            elif "assets" in query.lower():
                self.last_query_result = [
                    {
                        "id": 1,
                        "name": "HVAC Unit - Building A",
                        "asset_id": "HVAC-001",
                        "status": "Active",
                        "criticality": 4,
                        "category": "HVAC",
                        "location": "Building A - Roof",
                    },
                    {
                        "id": 2,
                        "name": "Fire Suppression System",
                        "asset_id": "FIRE-SUPP-001",
                        "status": "Active",
                        "criticality": 5,
                        "category": "Safety",
                        "location": "Building A - Ground Floor",
                    },
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

    def close(self):
        """Close connection (no-op)"""

    def cursor(self):
        """Return a cursor (returns self for SQLite compatibility)"""
        return self

    @property
    def lastrowid(self):
        """Return last inserted row ID (mock)"""
        return 1


def get_db_connection():
    """Get a SQLite-compatible database connection for existing routers"""
    return FirestoreSQLiteWrapper()
