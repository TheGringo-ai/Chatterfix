"""
Purchasing Dashboard Service - Procurement & Vendor Management
Provides data for purchase orders, vendor management, budget tracking, and spend analytics
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class PurchasingService:
    """Service for purchasing and procurement management"""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    async def get_purchase_orders(self, status: Optional[str] = None) -> List[Dict]:
        """Get purchase orders with optional status filter"""
        filters = []
        if status:
            filters.append({"field": "status", "operator": "==", "value": status})

        return await self.firestore_manager.get_collection(
            "purchase_orders", filters=filters, order_by="-requested_date"
        )

    async def get_pending_approvals(self) -> Dict:
        """Get purchase requests pending approval from Firestore"""
        try:
            filters = [{"field": "status", "operator": "==", "value": "pending"}]
            pending_requests = await self.firestore_manager.get_collection(
                "purchase_requests", filters=filters, order_by="-created_at"
            )
            return {
                "pending_count": len(pending_requests),
                "requests": pending_requests,
            }
        except Exception as e:
            logger.warning(f"Could not fetch pending approvals: {e}")
            return {"pending_count": 0, "requests": []}

    async def get_vendor_performance(self) -> List[Dict]:
        """Get vendor performance metrics from Firestore"""
        try:
            vendors = await self.firestore_manager.get_collection("vendors")
            # Calculate performance metrics per vendor from purchase orders
            performance = []
            for vendor in vendors:
                vendor_id = vendor.get("id", "")
                # Get completed orders for this vendor
                filters = [
                    {"field": "vendor_id", "operator": "==", "value": vendor_id},
                    {"field": "status", "operator": "==", "value": "completed"},
                ]
                orders = await self.firestore_manager.get_collection(
                    "purchase_orders", filters=filters
                )

                on_time_count = sum(
                    1 for o in orders if o.get("delivered_on_time", True)
                )
                total_orders = len(orders)

                performance.append(
                    {
                        "vendor_id": vendor_id,
                        "vendor_name": vendor.get("name", "Unknown"),
                        "total_orders": total_orders,
                        "on_time_delivery_rate": (
                            (on_time_count / total_orders * 100)
                            if total_orders > 0
                            else 100
                        ),
                        "average_lead_time_days": vendor.get("avg_lead_time", 7),
                        "quality_rating": vendor.get("quality_rating", 4.0),
                    }
                )
            return performance
        except Exception as e:
            logger.warning(f"Could not fetch vendor performance: {e}")
            return []

    async def get_budget_tracking(self) -> Dict:
        """Get budget tracking by category from Firestore"""
        try:
            # Get budget configuration
            budget_config = await self.firestore_manager.get_document(
                "settings", "budget_config"
            )
            monthly_budget = (
                budget_config.get("monthly_budget", 50000) if budget_config else 50000
            )

            # Calculate spent from purchase orders this month
            now = datetime.now(timezone.utc)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            orders = await self.firestore_manager.get_collection("purchase_orders")
            monthly_orders = [
                o
                for o in orders
                if o.get("created_at") and o.get("created_at") >= month_start
            ]

            total_spent = sum(o.get("total_amount", 0) for o in monthly_orders)

            # Group by category
            categories = {}
            for order in monthly_orders:
                cat = order.get("category", "General")
                categories[cat] = categories.get(cat, 0) + order.get("total_amount", 0)

            return {
                "monthly_budget": monthly_budget,
                "total_spent": total_spent,
                "remaining": monthly_budget - total_spent,
                "categories": [{"name": k, "spent": v} for k, v in categories.items()],
            }
        except Exception as e:
            logger.warning(f"Could not fetch budget tracking: {e}")
            return {
                "monthly_budget": 50000,
                "total_spent": 0,
                "remaining": 50000,
                "categories": [],
            }

    async def get_low_stock_alerts(self) -> List[Dict]:
        """Get low stock items needing reorder"""
        parts = await self.firestore_manager.get_collection("parts")
        low_stock_parts = [
            p for p in parts if p.get("current_stock", 0) <= p.get("minimum_stock", 0)
        ]
        return low_stock_parts

    async def get_price_trends(self) -> Dict:
        """Get price trends for common parts from Firestore"""
        try:
            # Get price history from Firestore
            price_history = await self.firestore_manager.get_collection(
                "price_history", order_by="-recorded_at", limit=100
            )

            # Group by part and calculate trends
            trends = {}
            for record in price_history:
                part_id = record.get("part_id", "")
                if part_id not in trends:
                    trends[part_id] = {
                        "part_id": part_id,
                        "part_name": record.get("part_name", "Unknown"),
                        "prices": [],
                    }
                trends[part_id]["prices"].append(
                    {
                        "price": record.get("price", 0),
                        "date": record.get("recorded_at"),
                    }
                )

            return {"trends": list(trends.values())}
        except Exception as e:
            logger.warning(f"Could not fetch price trends: {e}")
            return {"trends": []}

    async def get_contract_renewals(self) -> List[Dict]:
        """Get upcoming vendor contract renewals from Firestore"""
        try:
            contracts = await self.firestore_manager.get_collection(
                "contracts", order_by="expiry_date"
            )

            # Filter to contracts expiring in next 90 days
            now = datetime.now(timezone.utc)
            cutoff = now + timedelta(days=90)

            upcoming = []
            for contract in contracts:
                expiry = contract.get("expiry_date")
                if expiry and expiry <= cutoff:
                    upcoming.append(
                        {
                            "contract_id": contract.get("id", ""),
                            "vendor_name": contract.get("vendor_name", "Unknown"),
                            "expiry_date": (
                                expiry.strftime("%Y-%m-%d")
                                if hasattr(expiry, "strftime")
                                else str(expiry)
                            ),
                            "annual_value": contract.get("annual_value", 0),
                            "status": (
                                "expiring_soon"
                                if expiry <= now + timedelta(days=30)
                                else "upcoming"
                            ),
                        }
                    )
            return upcoming
        except Exception as e:
            logger.warning(f"Could not fetch contract renewals: {e}")
            return []

    async def get_spend_analytics(self, days: int = 30) -> Dict:
        """Get spend analytics for specified period from Firestore"""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            orders = await self.firestore_manager.get_collection("purchase_orders")

            recent_orders = [
                o
                for o in orders
                if o.get("created_at") and o.get("created_at") >= cutoff
            ]

            total_spend = sum(o.get("total_amount", 0) for o in recent_orders)

            return {
                "total_requests": len(recent_orders),
                "total_spend": total_spend,
                "average_order_value": (
                    total_spend / len(recent_orders) if recent_orders else 0
                ),
                "period_days": days,
            }
        except Exception as e:
            logger.warning(f"Could not fetch spend analytics: {e}")
            return {
                "total_requests": 0,
                "total_spend": 0,
                "average_order_value": 0,
                "period_days": days,
            }

    async def approve_purchase_request(self, request_id: str, approver_id: str) -> bool:
        """Approve a purchase request"""
        update_data = {
            "status": "approved",
            "approved_by": approver_id,
            "approved_date": datetime.now(timezone.utc),
        }
        return await self.firestore_manager.update_document(
            "purchase_requests", request_id, update_data
        )

    async def deny_purchase_request(
        self, request_id: str, reason: Optional[str] = None
    ) -> bool:
        """Deny a purchase request"""
        update_data = {"status": "denied", "denial_reason": reason}
        return await self.firestore_manager.update_document(
            "purchase_requests", request_id, update_data
        )

    # Other methods from the original service would be refactored here as well.
    # ...


# Global instance
purchasing_service = PurchasingService()
