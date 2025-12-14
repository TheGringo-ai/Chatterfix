"""
Purchasing Dashboard Service - Procurement & Vendor Management
Provides data for purchase orders, vendor management, budget tracking, and spend analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List

from app.core.db_adapter import get_db_adapter
from app.core.firestore_db import get_db_connection


class PurchasingService:
    """Service for purchasing and procurement management"""

    def __init__(self):
        self.db = get_db_adapter()

    async def get_purchase_orders(self, status: str = None) -> List[Dict]:
        """Get purchase orders with optional status filter"""
        # Use Firestore to get purchase orders
        # This would be implemented in the db_adapter with proper Firestore queries
        if hasattr(self.db, "get_purchase_orders"):
            return await self.db.get_purchase_orders(status)

        # Return mock data for demo purposes until Firestore collection is set up
        mock_orders = [
            {
                "id": "po_001",
                "part_name": "Industrial Bearing Set",
                "quantity": 10,
                "status": status or "pending",
                "priority": "high",
                "requested_date": (datetime.now() - timedelta(days=2)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "expected_delivery": (datetime.now() + timedelta(days=7)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "requester": "Mike Johnson",
                "work_order_title": "Conveyor Belt Maintenance",
            },
            {
                "id": "po_002",
                "part_name": "Hydraulic Pump Seals",
                "quantity": 5,
                "status": status or "approved",
                "priority": "medium",
                "requested_date": (datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "expected_delivery": (datetime.now() + timedelta(days=5)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "requester": "Sarah Chen",
                "work_order_title": "Press Hydraulic System Repair",
            },
        ]

        return (
            mock_orders
            if not status
            else [o for o in mock_orders if o["status"] == status]
        )

    async def get_pending_approvals(self) -> Dict:
        """Get purchase requests pending approval"""
        # Use Firestore to get pending approvals
        if hasattr(self.db, "get_pending_purchase_approvals"):
            return await self.db.get_pending_purchase_approvals()

        # Mock data for demo purposes
        pending_requests = [
            {
                "id": "pr_001",
                "part_name": "Motor Coupling",
                "quantity": 2,
                "priority": "urgent",
                "requested_date": (datetime.now() - timedelta(hours=6)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "requester": "Alex Rodriguez",
                "work_order_title": "Assembly Line Motor Failure",
                "work_order_priority": "critical",
            },
            {
                "id": "pr_002",
                "part_name": "Filter Cartridge Set",
                "quantity": 12,
                "priority": "medium",
                "requested_date": (datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "requester": "Mike Johnson",
                "work_order_title": "HVAC System Maintenance",
                "work_order_priority": "medium",
            },
        ]

        return {"pending_count": len(pending_requests), "requests": pending_requests}

    async def get_vendor_performance(self) -> List[Dict]:
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

    async def get_budget_tracking(self) -> Dict:
        """Get budget tracking by category"""
        # Use Firestore to get budget data
        if hasattr(self.db, "get_purchase_budget_data"):
            return await self.db.get_purchase_budget_data()

        # Mock budget data for demo purposes
        monthly_budget = 50000
        estimated_spend = 32500  # Simulated current month spending

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

    async def get_low_stock_alerts(self) -> List[Dict]:
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

    async def get_price_trends(self) -> Dict:
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

    async def get_contract_renewals(self) -> List[Dict]:
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

    async def get_spend_analytics(self, days: int = 30) -> Dict:
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

    async def approve_purchase_request(self, request_id: int, approver_id: int) -> bool:
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

    async def deny_purchase_request(self, request_id: int, reason: str = None) -> bool:
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

    # =========================================================================
    # PURCHASER DASHBOARD SERVICE METHODS
    # =========================================================================

    async def get_kpi_summary(self) -> Dict:
        """Get KPI summary for purchaser dashboard"""
        # Mock data - will integrate with Firestore
        return {
            "mtd_spend": 47250.00,
            "mtd_spend_change": 12.5,
            "open_pos": 23,
            "open_pos_change": -8.0,
            "alerts": 7,
            "alerts_change": 3,
            "avg_vendor_rating": 4.2,
            "avg_vendor_rating_change": 0.3,
            "budget_total": 75000.00,
            "budget_remaining": 27750.00,
            "on_time_delivery_rate": 94.5,
            "cost_savings_ytd": 15230.00,
        }

    async def get_po_pipeline_counts(self) -> Dict:
        """Get PO counts by pipeline stage"""
        # Mock data - will integrate with Firestore
        return {
            "draft": 5,
            "pending": 8,
            "approved": 6,
            "shipped": 3,
            "received": 12,
            "total": 34,
        }

    async def get_pending_actions(self) -> List[Dict]:
        """Get list of pending actions for purchaser"""
        # Mock data - will integrate with Firestore
        return [
            {
                "id": "action_001",
                "type": "approval",
                "title": "PO #2024-0847 requires approval",
                "description": "Industrial Bearing Set - Qty: 10",
                "priority": "high",
                "created_at": (datetime.now() - timedelta(hours=2)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "amount": 1250.00,
            },
            {
                "id": "action_002",
                "type": "reorder",
                "title": "Low Stock Alert: Hydraulic Seals",
                "description": "Current: 3, Min: 10 - Reorder suggested",
                "priority": "medium",
                "created_at": (datetime.now() - timedelta(hours=5)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "amount": 450.00,
            },
            {
                "id": "action_003",
                "type": "invoice",
                "title": "Invoice #INV-9823 pending review",
                "description": "Vendor: ABC Industrial - Amount: $3,450",
                "priority": "medium",
                "created_at": (datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "amount": 3450.00,
            },
            {
                "id": "action_004",
                "type": "contract",
                "title": "Contract renewal due: XYZ Supplies",
                "description": "Annual contract expires in 15 days",
                "priority": "low",
                "created_at": (datetime.now() - timedelta(days=3)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "due_date": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
                "amount": 25000.00,
            },
        ]

    async def get_top_vendors(self, limit: int = 5) -> List[Dict]:
        """Get top performing vendors with metrics"""
        # Mock data - will integrate with Firestore
        vendors = [
            {
                "id": "vendor_001",
                "name": "ABC Industrial Supply",
                "rating": 4.8,
                "on_time_rate": 98.5,
                "quality_score": 96,
                "total_orders": 145,
                "total_spend": 125000.00,
                "avg_lead_time": 3.2,
                "categories": ["Bearings", "Seals", "Motors"],
            },
            {
                "id": "vendor_002",
                "name": "FastParts Inc",
                "rating": 4.5,
                "on_time_rate": 95.0,
                "quality_score": 94,
                "total_orders": 98,
                "total_spend": 87500.00,
                "avg_lead_time": 2.8,
                "categories": ["Electronics", "Sensors", "Controls"],
            },
            {
                "id": "vendor_003",
                "name": "Premium Hydraulics",
                "rating": 4.6,
                "on_time_rate": 97.2,
                "quality_score": 98,
                "total_orders": 67,
                "total_spend": 54200.00,
                "avg_lead_time": 4.1,
                "categories": ["Hydraulics", "Pumps", "Valves"],
            },
            {
                "id": "vendor_004",
                "name": "Industrial Tools Co",
                "rating": 4.3,
                "on_time_rate": 92.0,
                "quality_score": 91,
                "total_orders": 52,
                "total_spend": 38900.00,
                "avg_lead_time": 3.5,
                "categories": ["Tools", "Safety Equipment"],
            },
            {
                "id": "vendor_005",
                "name": "Global Parts Network",
                "rating": 4.1,
                "on_time_rate": 89.5,
                "quality_score": 88,
                "total_orders": 34,
                "total_spend": 29100.00,
                "avg_lead_time": 5.2,
                "categories": ["General Parts", "Fasteners"],
            },
        ]
        return vendors[:limit]

    async def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent purchasing activity feed"""
        # Mock data - will integrate with Firestore
        activities = [
            {
                "id": "act_001",
                "type": "po_created",
                "icon": "bi-file-earmark-plus",
                "color": "primary",
                "title": "PO #2024-0851 created",
                "description": "10x Industrial Bearings from ABC Industrial",
                "user": "John Smith",
                "timestamp": (datetime.now() - timedelta(minutes=15)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "amount": 1250.00,
            },
            {
                "id": "act_002",
                "type": "po_approved",
                "icon": "bi-check-circle",
                "color": "success",
                "title": "PO #2024-0848 approved",
                "description": "Approved by Manager - Ready to ship",
                "user": "Sarah Chen",
                "timestamp": (datetime.now() - timedelta(hours=1)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "amount": 3450.00,
            },
            {
                "id": "act_003",
                "type": "shipment_received",
                "icon": "bi-box-seam",
                "color": "info",
                "title": "Shipment received",
                "description": "PO #2024-0842 - 25 items received and verified",
                "user": "Mike Johnson",
                "timestamp": (datetime.now() - timedelta(hours=3)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "amount": 2890.00,
            },
            {
                "id": "act_004",
                "type": "invoice_paid",
                "icon": "bi-credit-card",
                "color": "success",
                "title": "Invoice #INV-9820 paid",
                "description": "Payment processed to FastParts Inc",
                "user": "System",
                "timestamp": (datetime.now() - timedelta(hours=5)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "amount": 5670.00,
            },
            {
                "id": "act_005",
                "type": "vendor_added",
                "icon": "bi-building-add",
                "color": "primary",
                "title": "New vendor added",
                "description": "Precision Motors LLC added to approved vendors",
                "user": "John Smith",
                "timestamp": (datetime.now() - timedelta(hours=8)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "amount": None,
            },
            {
                "id": "act_006",
                "type": "alert",
                "icon": "bi-exclamation-triangle",
                "color": "warning",
                "title": "Low stock alert triggered",
                "description": "Hydraulic Seals below minimum threshold",
                "user": "System",
                "timestamp": (datetime.now() - timedelta(hours=12)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "amount": None,
            },
            {
                "id": "act_007",
                "type": "po_shipped",
                "icon": "bi-truck",
                "color": "info",
                "title": "PO #2024-0845 shipped",
                "description": "Tracking #: 1Z999AA10123456784",
                "user": "ABC Industrial",
                "timestamp": (datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "amount": 4200.00,
            },
        ]
        return activities[:limit]


# Global instance
purchasing_service = PurchasingService()
