"""
Planner Dashboard Service - Maintenance Planning & Scheduling
Provides data for preventive maintenance scheduling, resource allocation, and capacity planning
"""

from datetime import datetime, timedelta
from typing import Dict, List

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection


class PlannerService:
    """Service for maintenance planning and scheduling"""

    def get_pm_schedule(self, days_ahead: int = 30) -> Dict:
        """Get preventive maintenance schedule for next N days"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get scheduled PM work orders
            end_date = datetime.now() + timedelta(days=days_ahead)

            scheduled_work = cur.execute(
                """
                SELECT
                    wo.id,
                    wo.title,
                    wo.due_date,
                    wo.priority,
                    wo.status,
                    wo.assigned_to,
                    a.name as asset_name,
                    a.category,
                    u.full_name as assigned_name
                FROM work_orders wo
                LEFT JOIN assets a ON wo.asset_id = a.id
                LEFT JOIN users u ON wo.assigned_to = u.id
                WHERE wo.due_date <= ?
                AND wo.status NOT IN ('completed', 'cancelled')
                ORDER BY wo.due_date ASC
            """,
                (end_date.strftime("%Y-%m-%d"),),
            ).fetchall()

            # Group by date
            schedule_by_date = {}
            for work in scheduled_work:
                date = work["due_date"]
                if date not in schedule_by_date:
                    schedule_by_date[date] = []
                schedule_by_date[date].append(dict(work))

            conn.close()

            return {
                "schedule": schedule_by_date,
                "total_scheduled": len(scheduled_work),
                "date_range": {
                    "start": datetime.now().strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
            }
        except (ImportError, OSError):
            # Return empty schedule if SQLite is not available
            return {
                "schedule": {},
                "total_scheduled": 0,
                "date_range": {
                    "start": datetime.now().strftime("%Y-%m-%d"),
                    "end": (datetime.now() + timedelta(days=days_ahead)).strftime(
                        "%Y-%m-%d"
                    ),
                },
            }

    def get_resource_capacity(self) -> Dict:
        """Get technician capacity and workload - Enhanced with Marcus Rodriguez test scenarios"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get all technicians
            technicians = cur.execute(
                """
                SELECT
                    u.id,
                    u.full_name,
                    u.username,
                    u.status,
                    COUNT(wo.id) as active_work_orders,
                    SUM(CASE WHEN wo.priority = 'urgent' THEN 1 ELSE 0 END) as urgent_count,
                    SUM(wo.estimated_duration) as total_hours
                FROM users u
                LEFT JOIN work_orders wo ON u.id = wo.assigned_to
                    AND wo.status NOT IN ('completed', 'cancelled')
                WHERE u.role = 'technician'
                GROUP BY u.id
            """
            ).fetchall()

            capacity_data = []
            for tech in technicians:
                total_hours = tech["total_hours"] or 0
                capacity_pct = min((total_hours / 40) * 100, 100)  # Assume 40 hour week

                capacity_data.append(
                    {
                        "id": tech["id"],
                        "name": tech["full_name"],
                        "status": tech["status"],
                        "active_work_orders": tech["active_work_orders"],
                        "urgent_count": tech["urgent_count"],
                        "total_hours": total_hours,
                        "capacity_percentage": round(capacity_pct, 1),
                        "available_hours": max(40 - total_hours, 0),
                    }
                )

            conn.close()

            return {
                "technicians": capacity_data,
                "total_technicians": len(capacity_data),
                "average_capacity": (
                    round(
                        sum(t["capacity_percentage"] for t in capacity_data)
                        / len(capacity_data),
                        1,
                    )
                    if capacity_data
                    else 0
                ),
            }
        except (ImportError, OSError):
            # Mock data for Marcus Rodriguez planner testing scenarios
            capacity_data = [
                {
                    "id": "tech_001",
                    "name": "Jake Anderson",
                    "status": "active",
                    "active_work_orders": 8,
                    "urgent_count": 3,
                    "total_hours": 52,  # OVERLOADED - Shows resource conflict!
                    "capacity_percentage": 130.0,  # 130% = RED ALERT
                    "available_hours": 0,
                },
                {
                    "id": "tech_002", 
                    "name": "Sarah Chen",
                    "status": "active",
                    "active_work_orders": 5,
                    "urgent_count": 1,
                    "total_hours": 36,
                    "capacity_percentage": 90.0,  # High but manageable
                    "available_hours": 4,
                },
                {
                    "id": "tech_003",
                    "name": "Mike Rodriguez",
                    "status": "active", 
                    "active_work_orders": 3,
                    "urgent_count": 0,
                    "total_hours": 24,
                    "capacity_percentage": 60.0,
                    "available_hours": 16,
                },
                {
                    "id": "tech_004",
                    "name": "Jennifer Wong",
                    "status": "on_leave",
                    "active_work_orders": 0,
                    "urgent_count": 0,
                    "total_hours": 0,
                    "capacity_percentage": 0.0,
                    "available_hours": 0,  # Unavailable
                },
            ]
            
            return {
                "technicians": capacity_data,
                "total_technicians": len(capacity_data),
                "average_capacity": 70.0,  # Average across active technicians
            }

    def get_work_order_backlog(self) -> Dict:
        """Get pending work order backlog"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            backlog = cur.execute(
                """
                SELECT
                    wo.id,
                    wo.title,
                    wo.priority,
                    wo.status,
                    wo.created_date,
                    wo.due_date,
                    wo.estimated_duration,
                    a.name as asset_name,
                    a.criticality,
                    CASE
                        WHEN wo.due_date < date('now') THEN 'overdue'
                        WHEN wo.due_date = date('now') THEN 'due_today'
                        WHEN wo.due_date <= date('now', '+7 days') THEN 'due_this_week'
                        ELSE 'future'
                    END as urgency
                FROM work_orders wo
                LEFT JOIN assets a ON wo.asset_id = a.id
                WHERE wo.status IN ('pending', 'on_hold')
                ORDER BY
                    CASE wo.priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                    END,
                    wo.due_date ASC
            """
            ).fetchall()

            # Categorize backlog
            by_priority = {"urgent": [], "high": [], "medium": [], "low": []}
            by_urgency = {
                "overdue": [],
                "due_today": [],
                "due_this_week": [],
                "future": [],
            }

            for work in backlog:
                work_dict = dict(work)
                by_priority[work["priority"]].append(work_dict)
                by_urgency[work["urgency"]].append(work_dict)

            conn.close()

            return {
                "total_backlog": len(backlog),
                "by_priority": {k: len(v) for k, v in by_priority.items()},
                "by_urgency": {k: len(v) for k, v in by_urgency.items()},
                "work_orders": [dict(w) for w in backlog],
                "overdue_count": len(by_urgency["overdue"]),
                "due_today_count": len(by_urgency["due_today"]),
            }
        except (ImportError, OSError):
            # Marcus Rodriguez Test Scenarios - Critical maintenance situations
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            mock_work_orders = [
                {
                    "id": "WO-001-URGENT",
                    "title": "Emergency Generator - Failure to Start", 
                    "priority": "urgent",
                    "status": "pending",
                    "created_date": yesterday,
                    "due_date": yesterday,  # OVERDUE!
                    "estimated_duration": 6,
                    "asset_name": "Backup Generator Unit #1",
                    "criticality": 5,
                    "urgency": "overdue"
                },
                {
                    "id": "WO-002-URGENT",
                    "title": "Fire Suppression System - Annual Inspection OVERDUE",
                    "priority": "urgent", 
                    "status": "pending",
                    "created_date": "2024-11-15",
                    "due_date": "2024-12-01",  # OVERDUE!
                    "estimated_duration": 4,
                    "asset_name": "Fire Suppression System", 
                    "criticality": 5,
                    "urgency": "overdue"
                },
                {
                    "id": "WO-003-HIGH",
                    "title": "HVAC Unit B-2 - Refrigerant Leak Repair",
                    "priority": "high",
                    "status": "pending",
                    "created_date": today,
                    "due_date": today,
                    "estimated_duration": 4,
                    "asset_name": "HVAC Unit B-2",
                    "criticality": 4,
                    "urgency": "due_today"
                },
                {
                    "id": "WO-004-HIGH", 
                    "title": "Production Line Conveyor - Belt Replacement",
                    "priority": "high",
                    "status": "pending",
                    "created_date": today,
                    "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "estimated_duration": 8,
                    "asset_name": "Conveyor Belt System A",
                    "criticality": 4,
                    "urgency": "due_this_week"
                },
                {
                    "id": "WO-005-MEDIUM",
                    "title": "Compressor - Quarterly Maintenance",
                    "priority": "medium",
                    "status": "pending", 
                    "created_date": today,
                    "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                    "estimated_duration": 3,
                    "asset_name": "Air Compressor #1",
                    "criticality": 3,
                    "urgency": "due_this_week"
                },
                {
                    "id": "WO-006-MEDIUM",
                    "title": "Forklift FL-005 - Safety Inspection",
                    "priority": "medium",
                    "status": "pending",
                    "created_date": today,
                    "due_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
                    "estimated_duration": 2,
                    "asset_name": "Forklift FL-005",
                    "criticality": 3, 
                    "urgency": "future"
                }
            ]
            
            return {
                "total_backlog": len(mock_work_orders),
                "by_priority": {"urgent": 2, "high": 2, "medium": 2, "low": 0},
                "by_urgency": {"overdue": 2, "due_today": 1, "due_this_week": 2, "future": 1},
                "work_orders": mock_work_orders,
                "overdue_count": 2,
                "due_today_count": 1,
            }

    def get_asset_pm_status(self) -> List[Dict]:
        """Get preventive maintenance status for all assets"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            assets = cur.execute(
                """
                SELECT
                    a.id,
                    a.name,
                    a.asset_id,
                    a.category,
                    a.criticality,
                    a.location,
                    COUNT(wo.id) as total_work_orders,
                    MAX(wo.completed_date) as last_maintenance,
                    MIN(CASE WHEN wo.status = 'pending' THEN wo.due_date END) as next_pm_date
                FROM assets a
                LEFT JOIN work_orders wo ON a.id = wo.asset_id
                GROUP BY a.id
                ORDER BY a.criticality DESC, next_pm_date ASC
            """
            ).fetchall()

            pm_status = []
            for asset in assets:
                last_maint = asset["last_maintenance"]
                next_pm = asset["next_pm_date"]

                # Calculate days since last maintenance
                days_since = None
                if last_maint:
                    last_date = datetime.strptime(last_maint, "%Y-%m-%d %H:%M:%S")
                    days_since = (datetime.now() - last_date).days

                # Calculate days until next PM
                days_until = None
                pm_status_text = "No PM scheduled"
                if next_pm:
                    next_date = datetime.strptime(next_pm, "%Y-%m-%d")
                    days_until = (next_date - datetime.now()).days

                    if days_until < 0:
                        pm_status_text = "Overdue"
                    elif days_until == 0:
                        pm_status_text = "Due today"
                    elif days_until <= 7:
                        pm_status_text = "Due this week"
                    else:
                        pm_status_text = f"Due in {days_until} days"

                pm_status.append(
                    {
                        "id": asset["id"],
                        "name": asset["name"],
                        "asset_id": asset["asset_id"],
                        "category": asset["category"],
                        "criticality": asset["criticality"],
                        "location": asset["location"],
                        "last_maintenance": last_maint,
                        "days_since_maintenance": days_since,
                        "next_pm_date": next_pm,
                        "days_until_pm": days_until,
                        "pm_status": pm_status_text,
                        "total_work_orders": asset["total_work_orders"],
                    }
                )

            conn.close()

            return pm_status
        except (ImportError, OSError):
            # Asset PM Status for Marcus Rodriguez testing
            return [
                {
                    "id": "asset_001",
                    "name": "Emergency Backup Generator",
                    "asset_id": "GEN-001",
                    "category": "Power Systems",
                    "criticality": 5,
                    "location": "Building A - Basement",
                    "last_maintenance": "2024-09-15 14:00:00",
                    "days_since_maintenance": 87,
                    "next_pm_date": "2024-12-01",  # OVERDUE!
                    "days_until_pm": -10,
                    "pm_status": "Overdue",
                    "total_work_orders": 12,
                },
                {
                    "id": "asset_002", 
                    "name": "Fire Suppression System",
                    "asset_id": "FIRE-001",
                    "category": "Safety Systems",
                    "criticality": 5,
                    "location": "Building A - Main Floor",
                    "last_maintenance": "2023-12-15 10:00:00", 
                    "days_since_maintenance": 362,
                    "next_pm_date": "2024-12-01", # CRITICALLY OVERDUE!
                    "days_until_pm": -10,
                    "pm_status": "Overdue",
                    "total_work_orders": 8,
                },
                {
                    "id": "asset_003",
                    "name": "HVAC Unit B-2", 
                    "asset_id": "HVAC-B2",
                    "category": "HVAC",
                    "criticality": 4,
                    "location": "Building B - Roof",
                    "last_maintenance": "2024-11-01 09:00:00",
                    "days_since_maintenance": 40,
                    "next_pm_date": "2024-12-12",
                    "days_until_pm": 0,
                    "pm_status": "Due today", 
                    "total_work_orders": 6,
                },
                {
                    "id": "asset_004",
                    "name": "Conveyor Belt System A",
                    "asset_id": "CONV-A001", 
                    "category": "Production Equipment",
                    "criticality": 4,
                    "location": "Production Floor",
                    "last_maintenance": "2024-11-20 16:00:00",
                    "days_since_maintenance": 21,
                    "next_pm_date": "2024-12-18",
                    "days_until_pm": 6,
                    "pm_status": "Due this week",
                    "total_work_orders": 15,
                },
                {
                    "id": "asset_005",
                    "name": "Air Compressor #1",
                    "asset_id": "COMP-001",
                    "category": "Compressed Air",
                    "criticality": 3,
                    "location": "Utility Room", 
                    "last_maintenance": "2024-10-15 11:00:00",
                    "days_since_maintenance": 57,
                    "next_pm_date": "2024-12-22",
                    "days_until_pm": 10,
                    "pm_status": "Due in 10 days",
                    "total_work_orders": 9,
                }
            ]

    def get_parts_availability(self) -> Dict:
        """Get parts availability for scheduled work"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get parts needed for upcoming work orders
            parts_needed = cur.execute(
                """
                SELECT
                    pr.id,
                    pr.part_name,
                    pr.quantity,
                    pr.status,
                    pr.priority,
                    pr.requested_date,
                    pr.expected_delivery,
                    wo.title as work_order_title,
                    wo.due_date as work_order_due,
                    u.full_name as requester
                FROM parts_requests pr
                LEFT JOIN work_orders wo ON pr.work_order_id = wo.id
                LEFT JOIN users u ON pr.requester_id = u.id
                WHERE pr.status IN ('pending', 'approved', 'ordered')
                AND wo.status NOT IN ('completed', 'cancelled')
                ORDER BY wo.due_date ASC
            """
            ).fetchall()

            # Check inventory levels
            low_stock = cur.execute(
                """
                SELECT
                    part_name,
                    quantity,
                    min_quantity,
                    location
                FROM parts_inventory
                WHERE quantity <= min_quantity
            """
            ).fetchall()

            conn.close()

            return {
                "parts_needed": [dict(p) for p in parts_needed],
                "total_pending": len(parts_needed),
                "low_stock_items": [dict(p) for p in low_stock],
                "low_stock_count": len(low_stock),
            }
        except (ImportError, OSError):
            return {
                "parts_needed": [],
                "total_pending": 0,
                "low_stock_items": [],
                "low_stock_count": 0,
            }

    def get_scheduling_conflicts(self) -> List[Dict]:
        """Detect scheduling conflicts (overlapping assignments)"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Find technicians with multiple work orders on same day
            conflicts = cur.execute(
                """
                SELECT
                    u.id as technician_id,
                    u.full_name as technician_name,
                    wo.due_date,
                    COUNT(wo.id) as work_order_count,
                    SUM(wo.estimated_duration) as total_hours,
                    GROUP_CONCAT(wo.title, ' | ') as work_orders
                FROM users u
                JOIN work_orders wo ON u.id = wo.assigned_to
                WHERE wo.status NOT IN ('completed', 'cancelled')
                AND wo.due_date IS NOT NULL
                GROUP BY u.id, wo.due_date
                HAVING work_order_count > 1 OR total_hours > 8
            """
            ).fetchall()

            conn.close()

            conflict_list = []
            for conflict in conflicts:
                conflict_type = (
                    "overload"
                    if conflict["total_hours"] > 8
                    else "multiple_assignments"
                )

                conflict_list.append(
                    {
                        "technician_id": conflict["technician_id"],
                        "technician_name": conflict["technician_name"],
                        "date": conflict["due_date"],
                        "work_order_count": conflict["work_order_count"],
                        "total_hours": conflict["total_hours"],
                        "conflict_type": conflict_type,
                        "work_orders": conflict["work_orders"].split(" | "),
                    }
                )

            return conflict_list
        except (ImportError, OSError):
            # Marcus Rodriguez Test Scenarios - Critical Scheduling Conflicts
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            return [
                {
                    "technician_id": "tech_001",
                    "technician_name": "Jake Anderson",
                    "date": today,
                    "work_order_count": 4,
                    "total_hours": 18,  # WAY OVERLOADED!
                    "conflict_type": "overload",
                    "work_orders": [
                        "Emergency Generator - Failure to Start",
                        "HVAC Unit B-2 - Refrigerant Leak Repair", 
                        "Fire Suppression System - Annual Inspection",
                        "Compressor - Quarterly Maintenance"
                    ]
                },
                {
                    "technician_id": "tech_001", 
                    "technician_name": "Jake Anderson",
                    "date": tomorrow,
                    "work_order_count": 3,
                    "total_hours": 12,
                    "conflict_type": "overload", 
                    "work_orders": [
                        "Production Line Conveyor - Belt Replacement",
                        "Forklift FL-005 - Safety Inspection",
                        "Water Pump #3 - Seal Replacement"
                    ]
                },
                {
                    "technician_id": "tech_002",
                    "technician_name": "Sarah Chen", 
                    "date": today,
                    "work_order_count": 2,
                    "total_hours": 9,
                    "conflict_type": "overload",
                    "work_orders": [
                        "Electrical Panel Maintenance",
                        "Motor Bearing Replacement"
                    ]
                }
            ]

    def get_compliance_tracking(self) -> Dict:
        """Track regulatory compliance for maintenance"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get critical assets requiring compliance
            compliance_assets = cur.execute(
                """
                SELECT
                    a.id,
                    a.name,
                    a.asset_id,
                    a.category,
                    COUNT(wo.id) as total_maintenance,
                    MAX(wo.completed_date) as last_inspection,
                    CASE
                        WHEN MAX(wo.completed_date) IS NULL THEN 'Never inspected'
                        WHEN julianday('now') - julianday(MAX(wo.completed_date)) > 90 THEN 'Overdue'
                        WHEN julianday('now') - julianday(MAX(wo.completed_date)) > 60 THEN 'Due soon'
                        ELSE 'Compliant'
                    END as compliance_status
                FROM assets a
                LEFT JOIN work_orders wo ON a.id = wo.asset_id AND wo.status = 'completed'
                WHERE a.criticality >= 4
                GROUP BY a.id
            """
            ).fetchall()

            # Categorize by compliance status
            by_status = {
                "compliant": [],
                "due_soon": [],
                "overdue": [],
                "never_inspected": [],
            }

            for asset in compliance_assets:
                status_key = asset["compliance_status"].lower().replace(" ", "_")
                by_status[status_key].append(dict(asset))

            conn.close()

            return {
                "total_critical_assets": len(compliance_assets),
                "compliant": len(by_status["compliant"]),
                "due_soon": len(by_status["due_soon"]),
                "overdue": len(by_status["overdue"]),
                "never_inspected": len(by_status["never_inspected"]),
                "assets_by_status": by_status,
            }
        except (ImportError, OSError):
            return {
                "total_critical_assets": 0,
                "compliant": 0,
                "due_soon": 0,
                "overdue": 0,
                "never_inspected": 0,
                "assets_by_status": {
                    "compliant": [],
                    "due_soon": [],
                    "overdue": [],
                    "never_inspected": [],
                },
            }


# Global instance
planner_service = PlannerService()
