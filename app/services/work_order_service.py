from typing import List, Optional, Dict, Any
from app.core.firestore_db import get_firestore_manager
from app.models.work_order import WorkOrder
from datetime import datetime, timezone
from app.utils.security import sanitize_html_input

class WorkOrderService:
    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    async def get_work_orders(self, limit: int = 50) -> List[WorkOrder]:
        work_orders_data = await self.firestore_manager.get_collection("work_orders", limit=limit, order_by="-created_date")
        return [WorkOrder(**wo) for wo in work_orders_data]

    async def get_work_order(self, wo_id: str) -> Optional[WorkOrder]:
        wo_data = await self.firestore_manager.get_document("work_orders", wo_id)
        if wo_data:
            return WorkOrder(**wo_data)
        return None

    async def create_work_order(self, wo_data: Dict[str, Any]) -> str:
        # Sanitize potentially unsafe HTML input for description
        if 'description' in wo_data and isinstance(wo_data['description'], str):
            wo_data['description'] = sanitize_html_input(wo_data['description'])
            
        wo_model = WorkOrder(**wo_data)
        wo_model.created_date = datetime.now(timezone.utc)
        wo_dict = wo_model.dict(by_alias=True)
        return await self.firestore_manager.create_document("work_orders", wo_dict)

    async def update_work_order(self, wo_id: str, wo_data: Dict[str, Any]) -> bool:
        # Sanitize potentially unsafe HTML input for description
        if 'description' in wo_data and isinstance(wo_data['description'], str):
            wo_data['description'] = sanitize_html_input(wo_data['description'])
            
        wo_data["updated_at"] = datetime.now(timezone.utc)
        return await self.firestore_manager.update_document("work_orders", wo_id, wo_data)

work_order_service = WorkOrderService()
