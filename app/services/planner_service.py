"""
Planner Dashboard Service - Maintenance Planning & Scheduling
Provides data for preventive maintenance scheduling, resource allocation, and capacity planning
"""

from datetime import datetime, timedelta
from typing import Dict, List


class PlannerService:
    """Service for maintenance planning and scheduling with realistic demo data"""

    def get_pm_schedule(self, days_ahead: int = 30) -> Dict:
        """Get preventive maintenance schedule for next N days"""
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)

        # Generate realistic PM schedule
        schedule_by_date = {}
        pm_tasks = [
            {"asset": "HVAC Unit B-2", "type": "Quarterly Service", "duration": 4},
            {"asset": "Air Compressor #1", "type": "Monthly Check", "duration": 2},
            {"asset": "Conveyor Belt A", "type": "Weekly Inspection", "duration": 1},
            {
                "asset": "Fire Suppression System",
                "type": "Annual Inspection",
                "duration": 6,
            },
            {"asset": "Emergency Generator", "type": "Load Test", "duration": 3},
        ]

        for i, task in enumerate(pm_tasks):
            date = (today + timedelta(days=i * 3)).strftime("%Y-%m-%d")
            if date not in schedule_by_date:
                schedule_by_date[date] = []
            schedule_by_date[date].append(
                {
                    "id": f"pm_{i+1}",
                    "asset_name": task["asset"],
                    "pm_type": task["type"],
                    "estimated_duration": task["duration"],
                    "priority": "High" if i < 2 else "Medium",
                }
            )

        return {
            "schedule": schedule_by_date,
            "total_scheduled": len(pm_tasks),
            "date_range": {
                "start": today.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            },
        }

    def get_resource_capacity(self) -> Dict:
        """Get technician capacity and workload"""
        technicians = [
            {
                "id": "tech_001",
                "name": "Jake Anderson",
                "status": "active",
                "active_work_orders": 8,
                "total_hours": 52,
                "capacity_percentage": 130,
                "available_hours": -12,
                "urgent_count": 3,
                "specialization": "Electrical",
            },
            {
                "id": "tech_002",
                "name": "Sarah Chen",
                "status": "active",
                "active_work_orders": 5,
                "total_hours": 36,
                "capacity_percentage": 90,
                "available_hours": 4,
                "urgent_count": 1,
                "specialization": "HVAC",
            },
            {
                "id": "tech_003",
                "name": "Mike Rodriguez",
                "status": "active",
                "active_work_orders": 3,
                "total_hours": 24,
                "capacity_percentage": 60,
                "available_hours": 16,
                "urgent_count": 0,
                "specialization": "Mechanical",
            },
            {
                "id": "tech_004",
                "name": "Jennifer Wong",
                "status": "on_leave",
                "active_work_orders": 0,
                "total_hours": 0,
                "capacity_percentage": 0,
                "available_hours": 0,
                "urgent_count": 0,
                "specialization": "General",
            },
        ]

        active_techs = [t for t in technicians if t["status"] == "active"]
        avg_capacity = (
            sum(t["capacity_percentage"] for t in active_techs) / len(active_techs)
            if active_techs
            else 0
        )

        return {
            "technicians": technicians,
            "total_technicians": len(technicians),
            "active_technicians": len(active_techs),
            "average_capacity": round(avg_capacity, 1),
        }

    def get_work_order_backlog(self) -> Dict:
        """Get pending work order backlog"""
        today = datetime.now()

        work_orders = [
            {
                "id": "wo_001",
                "title": "Emergency Generator - Failure to Start",
                "asset_name": "Emergency Generator",
                "priority": "Critical",
                "status": "pending",
                "due_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "estimated_duration": 6,
                "assigned_to": "tech_001",
            },
            {
                "id": "wo_002",
                "title": "Fire Suppression System - Annual Inspection Overdue",
                "asset_name": "Fire Suppression System",
                "priority": "Critical",
                "status": "pending",
                "due_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                "estimated_duration": 4,
                "assigned_to": None,
            },
            {
                "id": "wo_003",
                "title": "HVAC Unit B-2 - Refrigerant Leak",
                "asset_name": "HVAC Unit B-2",
                "priority": "High",
                "status": "in_progress",
                "due_date": today.strftime("%Y-%m-%d"),
                "estimated_duration": 4,
                "assigned_to": "tech_002",
            },
            {
                "id": "wo_004",
                "title": "Conveyor Belt A - Belt Tension Adjustment",
                "asset_name": "Conveyor Belt A",
                "priority": "Medium",
                "status": "pending",
                "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "estimated_duration": 2,
                "assigned_to": "tech_003",
            },
            {
                "id": "wo_005",
                "title": "Air Compressor #1 - Oil Change",
                "asset_name": "Air Compressor #1",
                "priority": "Medium",
                "status": "pending",
                "due_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
                "estimated_duration": 1,
                "assigned_to": "tech_003",
            },
            {
                "id": "wo_006",
                "title": "Water Pump #3 - Seal Replacement",
                "asset_name": "Water Pump #3",
                "priority": "Low",
                "status": "pending",
                "due_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                "estimated_duration": 3,
                "assigned_to": None,
            },
        ]

        # Calculate statistics
        overdue = [
            wo for wo in work_orders if wo["due_date"] < today.strftime("%Y-%m-%d")
        ]
        due_today = [
            wo for wo in work_orders if wo["due_date"] == today.strftime("%Y-%m-%d")
        ]

        by_priority = {}
        for wo in work_orders:
            priority = wo["priority"].lower()
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return {
            "work_orders": work_orders,
            "total_backlog": len(work_orders),
            "overdue_count": len(overdue),
            "due_today_count": len(due_today),
            "by_priority": by_priority,
        }

    def get_asset_pm_status(self) -> List[Dict]:
        """Get preventive maintenance status for all assets"""
        today = datetime.now()

        assets = [
            {
                "asset_id": "ASSET_001",
                "name": "Emergency Generator",
                "location": "Building A - Utility Room",
                "criticality": 5,
                "pm_status": "Overdue",
                "last_pm_date": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
                "next_pm_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                "pm_interval_days": 30,
            },
            {
                "asset_id": "ASSET_002",
                "name": "Fire Suppression System",
                "location": "Building A - All Floors",
                "criticality": 5,
                "pm_status": "Overdue",
                "last_pm_date": (today - timedelta(days=380)).strftime("%Y-%m-%d"),
                "next_pm_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
                "pm_interval_days": 365,
            },
            {
                "asset_id": "ASSET_003",
                "name": "HVAC Unit B-2",
                "location": "Building B - Roof",
                "criticality": 4,
                "pm_status": "Due today",
                "last_pm_date": (today - timedelta(days=90)).strftime("%Y-%m-%d"),
                "next_pm_date": today.strftime("%Y-%m-%d"),
                "pm_interval_days": 90,
            },
            {
                "asset_id": "ASSET_004",
                "name": "Air Compressor #1",
                "location": "Building A - Mechanical Room",
                "criticality": 3,
                "pm_status": "Due this week",
                "last_pm_date": (today - timedelta(days=28)).strftime("%Y-%m-%d"),
                "next_pm_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "pm_interval_days": 30,
            },
            {
                "asset_id": "ASSET_005",
                "name": "Conveyor Belt A",
                "location": "Production Floor - Line 1",
                "criticality": 4,
                "pm_status": "Compliant",
                "last_pm_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                "next_pm_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "pm_interval_days": 7,
            },
            {
                "asset_id": "ASSET_006",
                "name": "Water Pump #3",
                "location": "Building A - Basement",
                "criticality": 3,
                "pm_status": "Compliant",
                "last_pm_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                "next_pm_date": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
                "pm_interval_days": 14,
            },
        ]

        return assets

    def get_parts_availability(self) -> Dict:
        """Get parts availability for scheduled work"""
        parts_needed = [
            {
                "part_id": "PART_001",
                "part_name": "Generator Control Module",
                "work_order_id": "wo_001",
                "work_order_title": "Emergency Generator Repair",
                "quantity": 1,
                "status": "On Order",
                "expected_delivery": "2024-12-16",
            },
            {
                "part_id": "PART_002",
                "part_name": "R410A Refrigerant (5 lbs)",
                "work_order_id": "wo_003",
                "work_order_title": "HVAC Unit B-2 Leak Repair",
                "quantity": 2,
                "status": "In Stock",
                "expected_delivery": None,
            },
            {
                "part_id": "PART_003",
                "part_name": "Conveyor Belt V-Belt",
                "work_order_id": "wo_004",
                "work_order_title": "Conveyor Belt Adjustment",
                "quantity": 1,
                "status": "In Stock",
                "expected_delivery": None,
            },
        ]

        low_stock_items = [
            {
                "part_id": "PART_004",
                "part_name": "Air Filter - Industrial",
                "quantity": 2,
                "min_quantity": 5,
                "reorder_point": 5,
            },
            {
                "part_id": "PART_005",
                "part_name": "Hydraulic Oil (1 Gal)",
                "quantity": 3,
                "min_quantity": 10,
                "reorder_point": 10,
            },
            {
                "part_id": "PART_006",
                "part_name": "Generator Fuel Filter",
                "quantity": 0,
                "min_quantity": 2,
                "reorder_point": 2,
            },
        ]

        return {
            "parts_needed": parts_needed,
            "total_pending": len(
                [p for p in parts_needed if p["status"] != "In Stock"]
            ),
            "low_stock_items": low_stock_items,
            "low_stock_count": len(low_stock_items),
        }

    def get_scheduling_conflicts(self) -> List[Dict]:
        """Detect scheduling conflicts"""
        today = datetime.now()

        conflicts = [
            {
                "conflict_id": "CONF_001",
                "technician_id": "tech_001",
                "technician_name": "Jake Anderson",
                "date": today.strftime("%Y-%m-%d"),
                "conflict_type": "Overload",
                "work_order_count": 4,
                "total_hours": 18,
                "severity": "High",
                "description": "Technician assigned 18 hours of work for an 8-hour shift",
            },
            {
                "conflict_id": "CONF_002",
                "technician_id": "tech_001",
                "technician_name": "Jake Anderson",
                "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                "conflict_type": "Overload",
                "work_order_count": 3,
                "total_hours": 14,
                "severity": "High",
                "description": "Technician assigned 14 hours of work for an 8-hour shift",
            },
            {
                "conflict_id": "CONF_003",
                "technician_id": "tech_002",
                "technician_name": "Sarah Chen",
                "date": today.strftime("%Y-%m-%d"),
                "conflict_type": "Skills Gap",
                "work_order_count": 1,
                "total_hours": 6,
                "severity": "Medium",
                "description": "Work order requires electrical certification that technician does not have",
            },
        ]

        return conflicts

    def get_compliance_tracking(self) -> Dict:
        """Track regulatory compliance for maintenance"""
        assets = self.get_asset_pm_status()

        compliant = len([a for a in assets if a["pm_status"] == "Compliant"])
        due_soon = len(
            [a for a in assets if a["pm_status"] in ["Due today", "Due this week"]]
        )
        overdue = len([a for a in assets if a["pm_status"] == "Overdue"])

        return {
            "total_critical_assets": len(assets),
            "compliant": compliant,
            "due_soon": due_soon,
            "overdue": overdue,
            "never_inspected": 0,
            "compliance_rate": (
                round((compliant / len(assets)) * 100, 1) if assets else 0
            ),
            "assets_by_status": {
                "compliant": compliant,
                "due_soon": due_soon,
                "overdue": overdue,
            },
        }


# Global instance
planner_service = PlannerService()
