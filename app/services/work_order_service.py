from typing import List, Optional, Dict, Any
from app.core.firestore_db import get_firestore_manager
from app.models.work_order import WorkOrder
from datetime import datetime, timezone
from app.utils.security import sanitize_html_input
import logging

logger = logging.getLogger(__name__)


class WorkOrderService:
    """
    Work Order Service with Multi-Tenant Support.
    All operations can be scoped to an organization for data isolation.
    """

    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    async def get_work_orders(
        self,
        limit: int = 50,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[WorkOrder]:
        """
        Get work orders with optional organization and user filtering.

        Args:
            limit: Maximum number of work orders to return
            organization_id: Filter by organization (for multi-tenant isolation)
            user_id: Filter by assigned user
        """
        filters = []

        # Multi-tenant isolation: filter by organization
        if organization_id:
            filters.append(
                {"field": "organization_id", "operator": "==", "value": organization_id}
            )

        # Optional: filter by assigned user
        if user_id:
            filters.append({"field": "assigned_to", "operator": "==", "value": user_id})

        work_orders_data = await self.firestore_manager.get_collection(
            "work_orders",
            limit=limit,
            order_by="-created_date" if not filters else None,  # Avoid composite index
            filters=filters if filters else None,
        )
        return [WorkOrder(**wo) for wo in work_orders_data]

    async def get_work_order(
        self, wo_id: str, organization_id: Optional[str] = None
    ) -> Optional[WorkOrder]:
        """
        Get a work order by ID with optional organization validation.

        Args:
            wo_id: Work order ID
            organization_id: If provided, validates the work order belongs to this org
        """
        wo_data = await self.firestore_manager.get_document("work_orders", wo_id)
        if wo_data:
            # Multi-tenant validation: ensure work order belongs to the user's org
            if organization_id and wo_data.get("organization_id") != organization_id:
                logger.warning(
                    f"Access denied: Work order {wo_id} does not belong to org {organization_id}"
                )
                return None
            return WorkOrder(**wo_data)
        return None

    async def create_work_order(
        self, wo_data: Dict[str, Any], organization_id: Optional[str] = None
    ) -> str:
        """
        Create a new work order with organization scoping.

        Args:
            wo_data: Work order data
            organization_id: Organization to associate with this work order
        """
        # Sanitize potentially unsafe HTML input for description
        if "description" in wo_data and isinstance(wo_data["description"], str):
            wo_data["description"] = sanitize_html_input(wo_data["description"])

        # Add organization_id for multi-tenant isolation
        if organization_id:
            wo_data["organization_id"] = organization_id

        wo_model = WorkOrder(**wo_data)
        wo_model.created_date = datetime.now(timezone.utc)
        wo_dict = wo_model.dict(by_alias=True)

        # Ensure organization_id is in the final dict
        if organization_id:
            wo_dict["organization_id"] = organization_id

        return await self.firestore_manager.create_document("work_orders", wo_dict)

    async def update_work_order(
        self,
        wo_id: str,
        wo_data: Dict[str, Any],
        organization_id: Optional[str] = None,
    ) -> bool:
        """
        Update a work order with organization validation.

        Args:
            wo_id: Work order ID
            wo_data: Data to update
            organization_id: If provided, validates the work order belongs to this org
        """
        # Validate access if organization_id is provided
        if organization_id:
            existing = await self.get_work_order(wo_id, organization_id)
            if not existing:
                logger.warning(
                    f"Update denied: Work order {wo_id} not found or doesn't belong to org {organization_id}"
                )
                return False

        # Sanitize potentially unsafe HTML input for description
        if "description" in wo_data and isinstance(wo_data["description"], str):
            wo_data["description"] = sanitize_html_input(wo_data["description"])

        wo_data["updated_at"] = datetime.now(timezone.utc)
        return await self.firestore_manager.update_document(
            "work_orders", wo_id, wo_data
        )

    async def delete_work_order(
        self, wo_id: str, organization_id: Optional[str] = None
    ) -> bool:
        """
        Delete a work order with organization validation.

        Args:
            wo_id: Work order ID
            organization_id: If provided, validates the work order belongs to this org
        """
        # Validate access if organization_id is provided
        if organization_id:
            existing = await self.get_work_order(wo_id, organization_id)
            if not existing:
                logger.warning(
                    f"Delete denied: Work order {wo_id} not found or doesn't belong to org {organization_id}"
                )
                return False

        return await self.firestore_manager.delete_document("work_orders", wo_id)


work_order_service = WorkOrderService()
