"""
Purchasing Dashboard Service - Procurement & Vendor Management
Provides data for purchase orders, vendor management, budget tracking, and spend analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection


class PurchasingService:
    """Service for purchasing and procurement management"""

    def get_purchase_orders(self, status: str = None) -> List[Dict]:
        """Get purchase orders with optional status filter"""
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT
                pr.id,
                pr.part_name,
                pr.quantity,
                pr.status,
                pr.priority,
                pr.requested_date,
                pr.expected_delivery,
                pr.approved_date,
                u.full_name as requester,
                wo.title as work_order_title
            FROM parts_requests pr
            LEFT JOIN users u ON pr.requester_id = u.id
            LEFT JOIN work_orders wo ON pr.work_order_id = wo.id
        """

        if status:
            query += f" WHERE pr.status = '{status}'"

        query += " ORDER BY pr.requested_date DESC"

        purchase_orders = cur.execute(query).fetchall()
        conn.close()

        return [dict(po) for po in purchase_orders]

    def get_pending_approvals(self) -> Dict:
        """Get purchase requests pending approval"""
        conn = get_db_connection()
        cur = conn.cursor()

        pending = cur.execute(
            """
            SELECT
                pr.id,
                pr.part_name,
                pr.quantity,
                pr.priority,
                pr.requested_date,
                u.full_name as requester,
                wo.title as work_order_title,
                wo.priority as work_order_priority
            FROM parts_requests pr
            LEFT JOIN users u ON pr.requester_id = u.id
            LEFT JOIN work_orders wo ON pr.work_order_id = wo.id
            WHERE pr.status = 'pending'
            ORDER BY
                CASE pr.priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                pr.requested_date ASC
        """
        ).fetchall()

        conn.close()

        return {"pending_count": len(pending), "requests": [dict(p) for p in pending]}

    def get_vendor_performance(self) -> List[Dict]:
        """Get vendor performance metrics (simulated - would need vendor table)"""
        # This is a placeholder - in production, you'd have a vendors table
        # For now, we'll return simulated data
        vendors = [
            {
                "id": 1,
                "name": "ABC Industrial Supply",
                "total_orders": 45,
                "on_time_delivery": 92,
                "quality_score": 4.5,
                "avg_delivery_days": 3,
                "total_spend": 125000,
            },
            {
                "id": 2,
                "name": "XYZ Parts Co",
                "total_orders": 32,
                "on_time_delivery": 88,
                "quality_score": 4.2,
                "avg_delivery_days": 5,
                "total_spend": 89000,
            },
            {
                "id": 3,
                "name": "Global Equipment",
                "total_orders": 28,
                "on_time_delivery": 95,
                "quality_score": 4.8,
                "avg_delivery_days": 2,
                "total_spend": 156000,
            },
        ]

        return vendors

    def get_budget_tracking(self) -> Dict:
        """Get budget tracking by category"""
        conn = get_db_connection()
        cur = conn.cursor()

        # Get parts spending (simulated pricing)
        parts_spending = cur.execute(
            """
            SELECT
                COUNT(*) as total_requests,
                SUM(quantity) as total_quantity
            FROM parts_requests
            WHERE status IN ('approved', 'ordered', 'delivered')
            AND requested_date >= date('now', '-30 days')
        """
        ).fetchone()

        conn.close()

        # Simulated budget data - in production, would come from budget table
        monthly_budget = 50000
        estimated_spend = (
            parts_spending["total_quantity"] or 0
        ) * 150  # Avg $150 per part

        categories = [
            {
                "category": "Parts & Materials",
                "budget": 30000,
                "spent": estimated_spend * 0.6,
                "remaining": 30000 - (estimated_spend * 0.6),
            },
            {
                "category": "Tools & Equipment",
                "budget": 10000,
                "spent": estimated_spend * 0.2,
                "remaining": 10000 - (estimated_spend * 0.2),
            },
            {
                "category": "Contractor Services",
                "budget": 10000,
                "spent": estimated_spend * 0.2,
                "remaining": 10000 - (estimated_spend * 0.2),
            },
        ]

        total_spent = sum(c["spent"] for c in categories)

        return {
            "monthly_budget": monthly_budget,
            "total_spent": total_spent,
            "remaining": monthly_budget - total_spent,
            "utilization_percentage": round((total_spent / monthly_budget) * 100, 1),
            "categories": categories,
        }

    def get_low_stock_alerts(self) -> List[Dict]:
        """Get low stock items needing reorder"""
        conn = get_db_connection()
        cur = conn.cursor()

        low_stock = cur.execute(
            """
            SELECT
                part_name,
                quantity,
                min_quantity,
                location,
                (min_quantity - quantity) as reorder_quantity
            FROM parts_inventory
            WHERE quantity <= min_quantity
            ORDER BY (min_quantity - quantity) DESC
        """
        ).fetchall()

        conn.close()

        return [dict(item) for item in low_stock]

    def get_price_trends(self) -> Dict:
        """Get price trends for common parts (simulated)"""
        # Simulated data - in production, would track historical pricing
        trends = [
            {
                "part_name": "Hydraulic Pump",
                "current_price": 450,
                "previous_price": 420,
                "change_percentage": 7.1,
                "trend": "up",
            },
            {
                "part_name": "Motor Bearing",
                "current_price": 85,
                "previous_price": 90,
                "change_percentage": -5.6,
                "trend": "down",
            },
            {
                "part_name": "Control Panel",
                "current_price": 1200,
                "previous_price": 1200,
                "change_percentage": 0,
                "trend": "stable",
            },
        ]

        return {"trends": trends}

    def get_contract_renewals(self) -> List[Dict]:
        """Get upcoming vendor contract renewals (simulated)"""
        # Simulated data - in production, would have contracts table
        renewals = [
            {
                "vendor": "ABC Industrial Supply",
                "contract_type": "Annual Parts Agreement",
                "renewal_date": "2025-03-15",
                "days_until_renewal": 114,
                "annual_value": 125000,
                "status": "upcoming",
            },
            {
                "vendor": "XYZ Parts Co",
                "contract_type": "Maintenance Contract",
                "renewal_date": "2025-02-01",
                "days_until_renewal": 72,
                "annual_value": 89000,
                "status": "upcoming",
            },
        ]

        return renewals

    def get_spend_analytics(self, days: int = 30) -> Dict:
        """Get spend analytics for specified period"""
        conn = get_db_connection()
        cur = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Get parts requests in period
        requests = cur.execute(
            """
            SELECT
                pr.id,
                pr.part_name,
                pr.quantity,
                pr.status,
                pr.requested_date,
                pr.priority
            FROM parts_requests pr
            WHERE pr.requested_date >= ?
            ORDER BY pr.requested_date DESC
        """,
            (start_date,),
        ).fetchall()

        conn.close()

        # Simulate pricing
        total_spend = 0
        by_priority = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        by_status = {}

        for req in requests:
            estimated_cost = req["quantity"] * 150  # Avg $150 per part
            total_spend += estimated_cost

            priority = req["priority"] or "low"
            by_priority[priority] += estimated_cost

            status = req["status"]
            by_status[status] = by_status.get(status, 0) + estimated_cost

        return {
            "period_days": days,
            "total_requests": len(requests),
            "total_spend": total_spend,
            "average_per_request": total_spend / len(requests) if requests else 0,
            "by_priority": by_priority,
            "by_status": by_status,
        }

    def approve_purchase_request(self, request_id: int, approver_id: int) -> bool:
        """Approve a purchase request"""
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                UPDATE parts_requests
                SET status = 'approved', approved_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (request_id,),
            )
            conn.commit()
            success = True
        except Exception as e:
            print(f"Error approving request: {e}")
            success = False
        finally:
            conn.close()

        return success

    def deny_purchase_request(self, request_id: int, reason: str = None) -> bool:
        """Deny a purchase request"""
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                UPDATE parts_requests
                SET status = 'denied'
                WHERE id = ?
            """,
                (request_id,),
            )
            conn.commit()
            success = True
        except Exception as e:
            print(f"Error denying request: {e}")
            success = False
        finally:
            conn.close()

        return success


# Global instance
purchasing_service = PurchasingService()
