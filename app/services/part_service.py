from typing import List, Optional, Dict, Any
from app.core.firestore_db import get_firestore_manager
from app.models.part import Part
from datetime import datetime, timezone


class PartService:
    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    async def get_parts(self, limit: int = 50) -> List[Part]:
        parts_data = await self.firestore_manager.get_collection(
            "parts", limit=limit, order_by="name"
        )
        return [Part(**part) for part in parts_data]

    async def get_part(self, part_id: str) -> Optional[Part]:
        part_data = await self.firestore_manager.get_document("parts", part_id)
        if part_data:
            return Part(**part_data)
        return None

    async def create_part(self, part_data: Dict[str, Any]) -> str:
        part_model = Part(**part_data)
        part_model.created_at = datetime.now(timezone.utc)
        part_dict = part_model.dict(by_alias=True)
        return await self.firestore_manager.create_document("parts", part_dict)

    async def update_part_stock(self, part_id: str, quantity_change: int) -> bool:
        part = await self.get_part(part_id)
        if not part:
            return False

        new_stock = part.current_stock + quantity_change
        if new_stock < 0:
            return False  # Or raise an error

        return await self.firestore_manager.update_document(
            "parts", part_id, {"current_stock": new_stock}
        )


part_service = PartService()
