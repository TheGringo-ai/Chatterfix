import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """Database adapter for Firestore (SQLite support removed)"""

    def __init__(self):
        self.db_type = "firestore"

        # Import Firestore manager directly - fail if not available
        from app.core.firestore_db import get_firestore_manager, FIRESTORE_AVAILABLE

        if not FIRESTORE_AVAILABLE:
            raise ImportError(
                "Firestore module not available. Cannot initialize database."
            )

        self.firestore_manager = get_firestore_manager()
        logger.info("🔥 Using Firestore database")

    async def create_work_order(self, work_order_data: Dict[str, Any]) -> str:
        """Create a work order"""
        if self.firestore_manager:
            return await self.firestore_manager.create_work_order(work_order_data)
        raise NotImplementedError("Firestore not available")

    async def get_work_orders(
        self, status: Optional[str] = None, assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get work orders"""
        if self.firestore_manager:
            return await self.firestore_manager.get_work_orders(status, assigned_to)
        return []

    async def create_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create an asset"""
        if self.firestore_manager:
            return await self.firestore_manager.create_asset(asset_data)
        raise NotImplementedError("Firestore not available")

    async def get_assets(
        self, status: Optional[str] = None, location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get assets"""
        if self.firestore_manager:
            return await self.firestore_manager.get_assets(status, location)
        return []

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a user"""
        if self.firestore_manager:
            return await self.firestore_manager.create_user(user_data)
        raise NotImplementedError("Firestore not available")

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        if self.firestore_manager:
            return await self.firestore_manager.get_user_by_email(email)
        return None

    async def save_ai_interaction(self, user_message: str, ai_response: str) -> str:
        """Save AI interaction"""
        if self.firestore_manager:
            return await self.firestore_manager.save_ai_interaction(
                user_message, ai_response
            )
        raise NotImplementedError("Firestore not available")

    async def get_dashboard_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get dashboard data"""
        if self.firestore_manager:
            return await self.firestore_manager.get_dashboard_data(
                user_id or "anonymous"
            )
        return {"work_orders": [], "assets": [], "ai_interactions": []}

    async def get_asset_by_tag(self, asset_tag: str) -> Optional[Dict[str, Any]]:
        """Get asset by asset tag/barcode"""
        if self.firestore_manager:
            return await self.firestore_manager.get_asset_by_tag(asset_tag)
        return None

    async def find_asset_by_identifier(
        self, identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Find asset by serial number, name, or other identifier"""
        if self.firestore_manager:
            return await self.firestore_manager.find_asset_by_identifier(identifier)
        return None

    async def get_asset(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """Get asset by ID"""
        if self.firestore_manager:
            return await self.firestore_manager.get_asset(asset_id)
        return None

    async def get_asset_work_orders(self, asset_id: int) -> List[Dict[str, Any]]:
        """Get work orders for an asset"""
        if self.firestore_manager:
            return await self.firestore_manager.get_asset_work_orders(asset_id)
        return []

    async def get_asset_parts(self, asset_id: int) -> List[Dict[str, Any]]:
        """Get parts for an asset"""
        if self.firestore_manager:
            return await self.firestore_manager.get_asset_parts(asset_id)
        return []

    async def count_asset_work_orders(self, asset_id: int) -> int:
        """Count work orders for an asset"""
        if self.firestore_manager:
            return await self.firestore_manager.count_asset_work_orders(asset_id)
        return 0

    async def count_asset_parts(self, asset_id: int) -> int:
        """Count parts for an asset"""
        if self.firestore_manager:
            return await self.firestore_manager.count_asset_parts(asset_id)
        return 0

    # Training methods
    async def create_training_module(self, module_data: Dict[str, Any]) -> str:
        """Create a training module"""
        if self.firestore_manager:
            return await self.firestore_manager.create_training_module(module_data)
        raise NotImplementedError("Firestore not available")

    async def get_training_modules(
        self, skill_category: Optional[str] = None, asset_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get training modules"""
        if self.firestore_manager:
            filters = []
            if skill_category:
                filters.append(
                    {
                        "field": "skill_category",
                        "operator": "==",
                        "value": skill_category,
                    }
                )
            if asset_type:
                filters.append(
                    {"field": "asset_type", "operator": "==", "value": asset_type}
                )

            return await self.firestore_manager.get_collection(
                "training_modules",
                order_by="-created_at",
                filters=filters if filters else None,
            )
        return []

    async def get_training_module(self, module_id: str) -> Optional[Dict[str, Any]]:
        """Get a training module by ID"""
        if self.firestore_manager:
            return await self.firestore_manager.get_document(
                "training_modules", module_id
            )
        return None

    async def create_user_training(self, training_data: Dict[str, Any]) -> str:
        """Create user training assignment"""
        if self.firestore_manager:
            return await self.firestore_manager.create_user_training(training_data)
        raise NotImplementedError("Firestore not available")

    async def get_user_training(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user training assignments"""
        if self.firestore_manager:
            return await self.firestore_manager.get_user_training(user_id)
        return []

    async def update_user_training(
        self, training_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update user training record"""
        if self.firestore_manager:
            return await self.firestore_manager.update_document(
                "user_training", training_id, update_data
            )
        return False


# Global database adapter instance
db_adapter = DatabaseAdapter()


def get_db_adapter() -> DatabaseAdapter:
    """Get the global database adapter instance"""
    return db_adapter
