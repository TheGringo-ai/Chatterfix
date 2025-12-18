from typing import List, Optional, Dict, Any
from app.core.firestore_db import get_firestore_manager
from app.models.asset import Asset
from datetime import datetime, timezone


class AssetService:
    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    async def get_assets(self, limit: int = 50) -> List[Asset]:
        assets_data = await self.firestore_manager.get_collection(
            "assets", limit=limit, order_by="name"
        )
        return [Asset(**asset) for asset in assets_data]

    async def get_asset(self, asset_id: str) -> Optional[Asset]:
        asset_data = await self.firestore_manager.get_document("assets", asset_id)
        if asset_data:
            return Asset(**asset_data)
        return None

    async def create_asset(self, asset_data: Dict[str, Any]) -> str:
        asset_model = Asset(**asset_data)
        asset_model.created_at = datetime.now(timezone.utc)
        asset_dict = asset_model.dict(by_alias=True)
        return await self.firestore_manager.create_document("assets", asset_dict)

    async def update_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> bool:
        asset_data["updated_at"] = datetime.now(timezone.utc)
        return await self.firestore_manager.update_document(
            "assets", asset_id, asset_data
        )


asset_service = AssetService()
