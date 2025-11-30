import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """Database adapter that can switch between SQLite and Firestore based on environment"""

    def __init__(self):
        self.use_firestore = os.getenv("USE_FIRESTORE", "true").lower() == "true"
        self.db_type = "firestore" if self.use_firestore else "sqlite"

        if self.use_firestore:
            from app.core.firestore_db import get_firestore_manager

            self.firestore_manager = get_firestore_manager()
            logger.info("🔥 Using Firestore database")
        else:
            from app.core.database import get_db_connection

            self.get_sqlite_connection = get_db_connection
            logger.info("📁 Using SQLite database")

    async def create_work_order(self, work_order_data: Dict[str, Any]) -> str:
        """Create a work order"""
        if self.use_firestore:
            return await self.firestore_manager.create_work_order(work_order_data)
        else:
            return self._create_sqlite_work_order(work_order_data)

    async def get_work_orders(
        self, status: str = None, assigned_to: str = None
    ) -> List[Dict[str, Any]]:
        """Get work orders"""
        if self.use_firestore:
            return await self.firestore_manager.get_work_orders(status, assigned_to)
        else:
            return self._get_sqlite_work_orders(status, assigned_to)

    async def create_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create an asset"""
        if self.use_firestore:
            return await self.firestore_manager.create_asset(asset_data)
        else:
            return self._create_sqlite_asset(asset_data)

    async def get_assets(
        self, status: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        """Get assets"""
        if self.use_firestore:
            return await self.firestore_manager.get_assets(status, location)
        else:
            return self._get_sqlite_assets(status, location)

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a user"""
        if self.use_firestore:
            return await self.firestore_manager.create_user(user_data)
        else:
            return self._create_sqlite_user(user_data)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        if self.use_firestore:
            return await self.firestore_manager.get_user_by_email(email)
        else:
            return self._get_sqlite_user_by_email(email)

    async def save_ai_interaction(self, user_message: str, ai_response: str) -> str:
        """Save AI interaction"""
        if self.use_firestore:
            return await self.firestore_manager.save_ai_interaction(
                user_message, ai_response
            )
        else:
            return self._save_sqlite_ai_interaction(user_message, ai_response)

    async def get_dashboard_data(self, user_id: str = None) -> Dict[str, Any]:
        """Get dashboard data"""
        if self.use_firestore:
            return await self.firestore_manager.get_dashboard_data(
                user_id or "anonymous"
            )
        else:
            return self._get_sqlite_dashboard_data(user_id)

    # SQLite implementation methods
    def _create_sqlite_work_order(self, work_order_data: Dict[str, Any]) -> str:
        """Create work order in SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO work_orders (title, description, status, priority, assigned_to, asset_id, due_date, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    work_order_data.get("title"),
                    work_order_data.get("description"),
                    work_order_data.get("status", "Open"),
                    work_order_data.get("priority", "Medium"),
                    work_order_data.get("assigned_to"),
                    work_order_data.get("asset_id"),
                    work_order_data.get("due_date"),
                    work_order_data.get("location"),
                ),
            )

            work_order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return str(work_order_id)
        except Exception as e:
            logger.error(f"Error creating SQLite work order: {e}")
            raise

    def _get_sqlite_work_orders(
        self, status: str = None, assigned_to: str = None
    ) -> List[Dict[str, Any]]:
        """Get work orders from SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM work_orders WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if assigned_to:
                query += " AND assigned_to = ?"
                params.append(assigned_to)

            query += " ORDER BY created_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            work_orders = []
            for row in rows:
                work_orders.append(
                    {
                        "id": str(row["id"]),
                        "title": row["title"],
                        "description": row["description"],
                        "status": row["status"],
                        "priority": row["priority"],
                        "assigned_to": row["assigned_to"],
                        "asset_id": row["asset_id"],
                        "created_date": row["created_date"],
                        "due_date": row["due_date"],
                        "location": row["location"],
                    }
                )

            conn.close()
            return work_orders
        except Exception as e:
            logger.error(f"Error getting SQLite work orders: {e}")
            return []

    def _create_sqlite_asset(self, asset_data: Dict[str, Any]) -> str:
        """Create asset in SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO assets (name, description, asset_tag, location, status, condition_rating)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    asset_data.get("name"),
                    asset_data.get("description"),
                    asset_data.get("asset_tag"),
                    asset_data.get("location"),
                    asset_data.get("status", "Active"),
                    asset_data.get("condition_rating", 5),
                ),
            )

            asset_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return str(asset_id)
        except Exception as e:
            logger.error(f"Error creating SQLite asset: {e}")
            raise

    def _get_sqlite_assets(
        self, status: str = None, location: str = None
    ) -> List[Dict[str, Any]]:
        """Get assets from SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM assets WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if location:
                query += " AND location = ?"
                params.append(location)

            query += " ORDER BY name"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            assets = []
            for row in rows:
                assets.append(
                    {
                        "id": str(row["id"]),
                        "name": row["name"],
                        "description": row["description"],
                        "asset_tag": row["asset_tag"],
                        "location": row["location"],
                        "status": row["status"],
                        "condition_rating": row["condition_rating"],
                        "image_url": row.get("image_url"),
                    }
                )

            conn.close()
            return assets
        except Exception as e:
            logger.error(f"Error getting SQLite assets: {e}")
            return []

    def _create_sqlite_user(self, user_data: Dict[str, Any]) -> str:
        """Create user in SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    user_data.get("username"),
                    user_data.get("email"),
                    user_data.get("password_hash"),
                    user_data.get("full_name"),
                    user_data.get("role", "technician"),
                ),
            )

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return str(user_id)
        except Exception as e:
            logger.error(f"Error creating SQLite user: {e}")
            raise

    def _get_sqlite_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()

            if row:
                user = {
                    "id": str(row["id"]),
                    "username": row["username"],
                    "email": row["email"],
                    "password_hash": row["password_hash"],
                    "full_name": row["full_name"],
                    "role": row["role"],
                }
                conn.close()
                return user

            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting SQLite user: {e}")
            return None

    def _save_sqlite_ai_interaction(self, user_message: str, ai_response: str) -> str:
        """Save AI interaction in SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO ai_interactions (user_message, ai_response)
                VALUES (?, ?)
            """,
                (user_message, ai_response),
            )

            interaction_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return str(interaction_id)
        except Exception as e:
            logger.error(f"Error saving SQLite AI interaction: {e}")
            raise

    def _get_sqlite_dashboard_data(self, user_id: str = None) -> Dict[str, Any]:
        """Get dashboard data from SQLite"""
        try:
            conn = self.get_sqlite_connection()
            cursor = conn.cursor()

            # Get recent work orders
            work_orders_query = (
                "SELECT * FROM work_orders ORDER BY created_date DESC LIMIT 10"
            )
            if user_id:
                work_orders_query = "SELECT * FROM work_orders WHERE assigned_to = ? ORDER BY created_date DESC LIMIT 10"
                cursor.execute(work_orders_query, (user_id,))
            else:
                cursor.execute(work_orders_query)

            work_orders = [dict(row) for row in cursor.fetchall()]

            # Get active assets
            cursor.execute("SELECT * FROM assets WHERE status = 'Active' LIMIT 5")
            assets = [dict(row) for row in cursor.fetchall()]

            # Get recent AI interactions
            cursor.execute(
                "SELECT * FROM ai_interactions ORDER BY timestamp DESC LIMIT 5"
            )
            ai_interactions = [dict(row) for row in cursor.fetchall()]

            conn.close()

            return {
                "work_orders": work_orders,
                "assets": assets,
                "ai_interactions": ai_interactions,
            }
        except Exception as e:
            logger.error(f"Error getting SQLite dashboard data: {e}")
            return {"work_orders": [], "assets": [], "ai_interactions": []}


# Global database adapter instance
db_adapter = DatabaseAdapter()


def get_db_adapter() -> DatabaseAdapter:
    """Get the global database adapter instance"""
    return db_adapter
