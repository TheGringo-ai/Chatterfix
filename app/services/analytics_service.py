"""
Advanced Analytics Service for ChatterFix CMMS
Provides KPIs, metrics, and reporting functionality including:
- MTTR (Mean Time To Repair)
- MTBF (Mean Time Between Failures)
- Asset Utilization
- Cost Tracking
- Compliance Analytics
- Predictive Insights
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.core.database import get_db_connection

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for advanced analytics and KPI calculations"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes cache

    def get_kpi_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of all KPIs for the dashboard"""
        try:
            return {
                "mttr": self.calculate_mttr(days),
                "mtbf": self.calculate_mtbf(days),
                "asset_utilization": self.calculate_asset_utilization(days),
                "cost_tracking": self.get_cost_tracking(days),
                "work_order_metrics": self.get_work_order_metrics(days),
                "compliance_metrics": self.get_compliance_metrics(days),
                "generated_at": datetime.now().isoformat(),
                "period_days": days,
            }
        except Exception as e:
            logger.error(f"Error calculating KPI summary: {e}")
            return self._get_default_kpi_summary(days)

    def calculate_mttr(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate Mean Time To Repair (MTTR)
        MTTR = Total Repair Time / Number of Repairs
        """
        conn = get_db_connection()
        try:
            # Get completed work orders with duration
            result = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_repairs,
                    AVG(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as avg_repair_time,
                    SUM(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as total_repair_time,
                    MIN(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as min_repair_time,
                    MAX(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as max_repair_time
                FROM work_orders
                WHERE status = 'Completed'
                AND actual_start IS NOT NULL
                AND actual_end IS NOT NULL
                AND DATE(actual_end) >= DATE('now', ?)
            """,
                (f"-{days} days",),
            ).fetchone()

            if result and result["total_repairs"] and result["total_repairs"] > 0:
                mttr_hours = result["avg_repair_time"] or 0
                return {
                    "value": round(mttr_hours, 2),
                    "unit": "hours",
                    "total_repairs": result["total_repairs"],
                    "total_repair_time": round(result["total_repair_time"] or 0, 2),
                    "min_repair_time": round(result["min_repair_time"] or 0, 2),
                    "max_repair_time": round(result["max_repair_time"] or 0, 2),
                    "trend": self._calculate_trend("mttr", mttr_hours, days),
                    "status": self._get_mttr_status(mttr_hours),
                }

            return self._get_default_mttr()

        finally:
            conn.close()

    def calculate_mtbf(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate Mean Time Between Failures (MTBF)
        MTBF = Total Operating Time / Number of Failures
        """
        conn = get_db_connection()
        try:
            # Get failure count from maintenance history
            failures = conn.execute(
                """
                SELECT 
                    COUNT(*) as failure_count,
                    SUM(downtime_hours) as total_downtime
                FROM maintenance_history
                WHERE maintenance_type IN ('Corrective', 'Emergency')
                AND DATE(created_date) >= DATE('now', ?)
            """,
                (f"-{days} days",),
            ).fetchone()

            # Get total assets for operating time calculation
            assets = conn.execute(
                """
                SELECT COUNT(*) as total_assets
                FROM assets
                WHERE status = 'Active'
            """
            ).fetchone()

            failure_count = failures["failure_count"] if failures else 0
            total_assets = assets["total_assets"] if assets else 1

            # Calculate total operating hours (assets * hours in period)
            total_operating_hours = total_assets * days * 24

            if failure_count > 0:
                mtbf_hours = total_operating_hours / failure_count
                return {
                    "value": round(mtbf_hours, 2),
                    "unit": "hours",
                    "failure_count": failure_count,
                    "total_operating_hours": total_operating_hours,
                    "total_downtime": round(failures["total_downtime"] or 0, 2),
                    "trend": self._calculate_trend("mtbf", mtbf_hours, days),
                    "status": self._get_mtbf_status(mtbf_hours),
                }

            return {
                "value": total_operating_hours,
                "unit": "hours",
                "failure_count": 0,
                "total_operating_hours": total_operating_hours,
                "total_downtime": 0,
                "trend": "stable",
                "status": "excellent",
                "message": "No failures recorded in this period",
            }

        finally:
            conn.close()

    def calculate_asset_utilization(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate asset utilization metrics
        """
        conn = get_db_connection()
        try:
            # Get asset status breakdown
            status_breakdown = conn.execute(
                """
                SELECT 
                    status,
                    COUNT(*) as count
                FROM assets
                GROUP BY status
            """
            ).fetchall()

            # Get utilization from maintenance history
            utilization = conn.execute(
                """
                SELECT 
                    a.id,
                    a.name,
                    COUNT(mh.id) as maintenance_events,
                    SUM(mh.downtime_hours) as total_downtime
                FROM assets a
                LEFT JOIN maintenance_history mh ON a.id = mh.asset_id
                    AND DATE(mh.created_date) >= DATE('now', ?)
                WHERE a.status = 'Active'
                GROUP BY a.id
            """,
                (f"-{days} days",),
            ).fetchall()

            total_assets = sum(s["count"] for s in status_breakdown)
            active_assets = next(
                (s["count"] for s in status_breakdown if s["status"] == "Active"), 0
            )

            # Calculate average utilization rate
            total_hours = days * 24
            total_uptime = 0
            asset_data = []

            for asset in utilization:
                downtime = asset["total_downtime"] or 0
                uptime = total_hours - downtime
                utilization_rate = (
                    (uptime / total_hours) * 100 if total_hours > 0 else 100
                )
                total_uptime += uptime
                asset_data.append(
                    {
                        "id": asset["id"],
                        "name": asset["name"],
                        "maintenance_events": asset["maintenance_events"],
                        "downtime_hours": round(downtime, 2),
                        "utilization_rate": round(utilization_rate, 2),
                    }
                )

            avg_utilization = (
                (total_uptime / (len(utilization) * total_hours)) * 100
                if utilization
                else 100
            )

            return {
                "average_utilization": round(avg_utilization, 2),
                "unit": "percent",
                "total_assets": total_assets,
                "active_assets": active_assets,
                "status_breakdown": {s["status"]: s["count"] for s in status_breakdown},
                "top_utilized": sorted(
                    asset_data, key=lambda x: x["utilization_rate"], reverse=True
                )[:5],
                "low_utilized": sorted(asset_data, key=lambda x: x["utilization_rate"])[
                    :5
                ],
                "trend": self._calculate_trend("utilization", avg_utilization, days),
                "status": self._get_utilization_status(avg_utilization),
            }

        finally:
            conn.close()

    def get_cost_tracking(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive cost tracking metrics
        """
        conn = get_db_connection()
        try:
            # Get maintenance costs
            costs = conn.execute(
                """
                SELECT 
                    SUM(labor_cost) as total_labor,
                    SUM(parts_cost) as total_parts,
                    SUM(total_cost) as total_cost,
                    COUNT(*) as maintenance_count,
                    AVG(total_cost) as avg_cost_per_event
                FROM maintenance_history
                WHERE DATE(created_date) >= DATE('now', ?)
            """,
                (f"-{days} days",),
            ).fetchone()

            # Get costs by maintenance type
            costs_by_type = conn.execute(
                """
                SELECT 
                    maintenance_type,
                    SUM(total_cost) as total_cost,
                    COUNT(*) as event_count
                FROM maintenance_history
                WHERE DATE(created_date) >= DATE('now', ?)
                GROUP BY maintenance_type
            """,
                (f"-{days} days",),
            ).fetchall()

            # Get top costly assets
            costly_assets = conn.execute(
                """
                SELECT 
                    a.name,
                    a.id,
                    SUM(mh.total_cost) as total_cost,
                    COUNT(mh.id) as maintenance_events
                FROM maintenance_history mh
                JOIN assets a ON mh.asset_id = a.id
                WHERE DATE(mh.created_date) >= DATE('now', ?)
                GROUP BY a.id
                ORDER BY total_cost DESC
                LIMIT 10
            """,
                (f"-{days} days",),
            ).fetchall()

            # Get daily cost trend
            daily_costs = conn.execute(
                """
                SELECT 
                    DATE(created_date) as date,
                    SUM(total_cost) as daily_cost
                FROM maintenance_history
                WHERE DATE(created_date) >= DATE('now', ?)
                GROUP BY DATE(created_date)
                ORDER BY date
            """,
                (f"-{days} days",),
            ).fetchall()

            total_cost = costs["total_cost"] if costs and costs["total_cost"] else 0

            return {
                "total_cost": round(total_cost, 2),
                "labor_cost": round(costs["total_labor"] or 0, 2) if costs else 0,
                "parts_cost": round(costs["total_parts"] or 0, 2) if costs else 0,
                "maintenance_count": costs["maintenance_count"] if costs else 0,
                "avg_cost_per_event": (
                    round(costs["avg_cost_per_event"] or 0, 2) if costs else 0
                ),
                "costs_by_type": {
                    c["maintenance_type"]: round(c["total_cost"] or 0, 2)
                    for c in costs_by_type
                },
                "top_costly_assets": [
                    {
                        "name": a["name"],
                        "id": a["id"],
                        "total_cost": round(a["total_cost"] or 0, 2),
                        "events": a["maintenance_events"],
                    }
                    for a in costly_assets
                ],
                "daily_trend": [
                    {"date": d["date"], "cost": round(d["daily_cost"] or 0, 2)}
                    for d in daily_costs
                ],
                "trend": self._calculate_trend("cost", total_cost, days),
                "currency": "USD",
            }

        finally:
            conn.close()

    def get_work_order_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive work order metrics
        """
        conn = get_db_connection()
        try:
            # Get work order status breakdown
            status_breakdown = conn.execute(
                """
                SELECT 
                    status,
                    COUNT(*) as count
                FROM work_orders
                WHERE DATE(created_date) >= DATE('now', ?)
                GROUP BY status
            """,
                (f"-{days} days",),
            ).fetchall()

            # Get priority breakdown
            priority_breakdown = conn.execute(
                """
                SELECT 
                    priority,
                    COUNT(*) as count
                FROM work_orders
                WHERE DATE(created_date) >= DATE('now', ?)
                GROUP BY priority
            """,
                (f"-{days} days",),
            ).fetchall()

            # Get overdue work orders
            overdue = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM work_orders
                WHERE status NOT IN ('Completed', 'Cancelled')
                AND due_date < DATE('now')
            """
            ).fetchone()

            # Get completion rate
            total_created = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM work_orders
                WHERE DATE(created_date) >= DATE('now', ?)
            """,
                (f"-{days} days",),
            ).fetchone()

            completed = next(
                (s["count"] for s in status_breakdown if s["status"] == "Completed"), 0
            )
            total = total_created["count"] if total_created else 0
            completion_rate = (completed / total * 100) if total > 0 else 0

            # Get daily trend
            daily_trend = conn.execute(
                """
                SELECT 
                    DATE(created_date) as date,
                    COUNT(*) as created,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
                FROM work_orders
                WHERE DATE(created_date) >= DATE('now', ?)
                GROUP BY DATE(created_date)
                ORDER BY date
            """,
                (f"-{days} days",),
            ).fetchall()

            return {
                "total_created": total,
                "completion_rate": round(completion_rate, 2),
                "overdue_count": overdue["count"] if overdue else 0,
                "status_breakdown": {s["status"]: s["count"] for s in status_breakdown},
                "priority_breakdown": {
                    p["priority"]: p["count"] for p in priority_breakdown
                },
                "daily_trend": [
                    {
                        "date": d["date"],
                        "created": d["created"],
                        "completed": d["completed"],
                    }
                    for d in daily_trend
                ],
                "trend": self._calculate_trend("work_orders", completion_rate, days),
                "status": (
                    "good"
                    if completion_rate >= 80
                    else "warning" if completion_rate >= 60 else "critical"
                ),
            }

        finally:
            conn.close()

    def get_compliance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get compliance and PM schedule adherence metrics
        """
        conn = get_db_connection()
        try:
            # Get PM completion rate
            pm_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_pm,
                    SUM(CASE WHEN DATE(actual_end) <= DATE(due_date) THEN 1 ELSE 0 END) as on_time
                FROM work_orders
                WHERE status = 'Completed'
                AND DATE(created_date) >= DATE('now', ?)
            """,
                (f"-{days} days",),
            ).fetchone()

            # Get training compliance
            training_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_assigned,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM user_training
            """
            ).fetchone()

            # Get certification status
            cert_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_certs,
                    SUM(CASE WHEN certification_expiry >= DATE('now') THEN 1 ELSE 0 END) as valid_certs,
                    SUM(CASE WHEN certification_expiry < DATE('now') THEN 1 ELSE 0 END) as expired_certs
                FROM user_skills
                WHERE certified = 1
            """
            ).fetchone()

            total_pm = pm_stats["total_pm"] if pm_stats else 0
            on_time_pm = pm_stats["on_time"] if pm_stats else 0
            pm_compliance = (on_time_pm / total_pm * 100) if total_pm > 0 else 100

            total_training = training_stats["total_assigned"] if training_stats else 0
            completed_training = training_stats["completed"] if training_stats else 0
            training_compliance = (
                (completed_training / total_training * 100)
                if total_training > 0
                else 100
            )

            return {
                "pm_compliance_rate": round(pm_compliance, 2),
                "total_pm_work_orders": total_pm,
                "on_time_completions": on_time_pm,
                "training_compliance_rate": round(training_compliance, 2),
                "total_training_assigned": total_training,
                "training_completed": completed_training,
                "certification_status": {
                    "total": cert_stats["total_certs"] if cert_stats else 0,
                    "valid": cert_stats["valid_certs"] if cert_stats else 0,
                    "expired": cert_stats["expired_certs"] if cert_stats else 0,
                },
                "overall_compliance": round(
                    (pm_compliance + training_compliance) / 2, 2
                ),
                "status": (
                    "good"
                    if pm_compliance >= 90
                    else "warning" if pm_compliance >= 70 else "critical"
                ),
            }

        finally:
            conn.close()

    def get_trend_data(
        self, metric: str, days: int = 30, interval: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get historical trend data for a specific metric
        """
        conn = get_db_connection()
        try:
            if metric == "mttr":
                return self._get_mttr_trend(conn, days)
            elif metric == "mtbf":
                return self._get_mtbf_trend(conn, days)
            elif metric == "cost":
                return self._get_cost_trend(conn, days)
            elif metric == "work_orders":
                return self._get_work_order_trend(conn, days)
            else:
                return []
        finally:
            conn.close()

    def _get_mttr_trend(self, conn, days: int) -> List[Dict[str, Any]]:
        """Get MTTR trend over time"""
        result = conn.execute(
            """
            SELECT 
                DATE(actual_end) as date,
                AVG(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as mttr
            FROM work_orders
            WHERE status = 'Completed'
            AND actual_start IS NOT NULL
            AND actual_end IS NOT NULL
            AND DATE(actual_end) >= DATE('now', ?)
            GROUP BY DATE(actual_end)
            ORDER BY date
        """,
            (f"-{days} days",),
        ).fetchall()

        return [{"date": r["date"], "value": round(r["mttr"] or 0, 2)} for r in result]

    def _get_mtbf_trend(self, conn, days: int) -> List[Dict[str, Any]]:
        """Get MTBF trend over time"""
        result = conn.execute(
            """
            SELECT 
                DATE(created_date) as date,
                COUNT(*) as failures
            FROM maintenance_history
            WHERE maintenance_type IN ('Corrective', 'Emergency')
            AND DATE(created_date) >= DATE('now', ?)
            GROUP BY DATE(created_date)
            ORDER BY date
        """,
            (f"-{days} days",),
        ).fetchall()

        # Calculate running MTBF
        assets_count = (
            conn.execute(
                "SELECT COUNT(*) FROM assets WHERE status = 'Active'"
            ).fetchone()[0]
            or 1
        )
        trend_data = []
        cumulative_failures = 0

        for i, r in enumerate(result):
            cumulative_failures += r["failures"]
            operating_hours = (i + 1) * 24 * assets_count
            mtbf = (
                operating_hours / cumulative_failures
                if cumulative_failures > 0
                else operating_hours
            )
            trend_data.append({"date": r["date"], "value": round(mtbf, 2)})

        return trend_data

    def _get_cost_trend(self, conn, days: int) -> List[Dict[str, Any]]:
        """Get cost trend over time"""
        result = conn.execute(
            """
            SELECT 
                DATE(created_date) as date,
                SUM(total_cost) as cost
            FROM maintenance_history
            WHERE DATE(created_date) >= DATE('now', ?)
            GROUP BY DATE(created_date)
            ORDER BY date
        """,
            (f"-{days} days",),
        ).fetchall()

        return [{"date": r["date"], "value": round(r["cost"] or 0, 2)} for r in result]

    def _get_work_order_trend(self, conn, days: int) -> List[Dict[str, Any]]:
        """Get work order completion trend over time"""
        result = conn.execute(
            """
            SELECT 
                DATE(created_date) as date,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM work_orders
            WHERE DATE(created_date) >= DATE('now', ?)
            GROUP BY DATE(created_date)
            ORDER BY date
        """,
            (f"-{days} days",),
        ).fetchall()

        return [
            {
                "date": r["date"],
                "total": r["total"],
                "completed": r["completed"],
                "completion_rate": round(
                    (r["completed"] / r["total"] * 100) if r["total"] > 0 else 0, 2
                ),
            }
            for r in result
        ]

    def _calculate_trend(self, metric: str, current_value: float, days: int) -> str:
        """
        Calculate trend direction compared to previous period
        Compares current period vs previous period of same length
        """
        conn = get_db_connection()
        try:
            # Get previous period value based on metric
            if metric == "mttr":
                prev_result = conn.execute(
                    """
                    SELECT AVG(CAST((julianday(actual_end) - julianday(actual_start)) * 24 AS REAL)) as value
                    FROM work_orders
                    WHERE status = 'Completed'
                    AND actual_start IS NOT NULL
                    AND actual_end IS NOT NULL
                    AND DATE(actual_end) >= DATE('now', ?)
                    AND DATE(actual_end) < DATE('now', ?)
                """,
                    (f"-{days * 2} days", f"-{days} days"),
                ).fetchone()

            elif metric == "mtbf":
                prev_result = conn.execute(
                    """
                    SELECT COUNT(*) as failure_count
                    FROM maintenance_history
                    WHERE maintenance_type IN ('Corrective', 'Emergency')
                    AND DATE(created_date) >= DATE('now', ?)
                    AND DATE(created_date) < DATE('now', ?)
                """,
                    (f"-{days * 2} days", f"-{days} days"),
                ).fetchone()

            elif metric == "cost":
                prev_result = conn.execute(
                    """
                    SELECT SUM(total_cost) as value
                    FROM maintenance_history
                    WHERE DATE(created_date) >= DATE('now', ?)
                    AND DATE(created_date) < DATE('now', ?)
                """,
                    (f"-{days * 2} days", f"-{days} days"),
                ).fetchone()

            elif metric == "utilization":
                # For utilization, use current vs previous downtime
                prev_result = conn.execute(
                    """
                    SELECT SUM(downtime_hours) as value
                    FROM maintenance_history
                    WHERE DATE(created_date) >= DATE('now', ?)
                    AND DATE(created_date) < DATE('now', ?)
                """,
                    (f"-{days * 2} days", f"-{days} days"),
                ).fetchone()

            else:
                return "stable"

            prev_value = (
                prev_result["value"] if prev_result and prev_result["value"] else 0
            )

            # Calculate change percentage
            if prev_value > 0:
                change_pct = ((current_value - prev_value) / prev_value) * 100
            elif current_value > 0:
                change_pct = 100  # New data, assume improving
            else:
                return "stable"

            # Determine trend based on metric type
            # For MTTR and cost, lower is better (decreasing = improving)
            # For MTBF and utilization, higher is better (increasing = improving)
            if metric in ["mttr", "cost"]:
                if change_pct < -10:
                    return "improving"
                elif change_pct > 10:
                    return "declining"
            elif metric in ["mtbf", "utilization"]:
                if change_pct > 10:
                    return "improving"
                elif change_pct < -10:
                    return "declining"

            return "stable"

        except Exception as e:
            logger.error(f"Error calculating trend for {metric}: {e}")
            return "stable"
        finally:
            conn.close()

    def _get_mttr_status(self, mttr_hours: float) -> str:
        """Get status based on MTTR value"""
        if mttr_hours <= 2:
            return "excellent"
        elif mttr_hours <= 4:
            return "good"
        elif mttr_hours <= 8:
            return "warning"
        return "critical"

    def _get_mtbf_status(self, mtbf_hours: float) -> str:
        """Get status based on MTBF value"""
        if mtbf_hours >= 720:  # 30 days
            return "excellent"
        elif mtbf_hours >= 168:  # 7 days
            return "good"
        elif mtbf_hours >= 72:  # 3 days
            return "warning"
        return "critical"

    def _get_utilization_status(self, utilization: float) -> str:
        """Get status based on utilization rate"""
        if utilization >= 95:
            return "excellent"
        elif utilization >= 85:
            return "good"
        elif utilization >= 70:
            return "warning"
        return "critical"

    def _get_default_mttr(self) -> Dict[str, Any]:
        """Return default MTTR data"""
        return {
            "value": 0,
            "unit": "hours",
            "total_repairs": 0,
            "total_repair_time": 0,
            "min_repair_time": 0,
            "max_repair_time": 0,
            "trend": "stable",
            "status": "excellent",
            "message": "No repair data available for this period",
        }

    def _get_default_kpi_summary(self, days: int) -> Dict[str, Any]:
        """Return default KPI summary when data is unavailable"""
        return {
            "mttr": self._get_default_mttr(),
            "mtbf": {"value": 0, "unit": "hours", "status": "unknown"},
            "asset_utilization": {"average_utilization": 0, "status": "unknown"},
            "cost_tracking": {"total_cost": 0, "currency": "USD"},
            "work_order_metrics": {"total_created": 0, "completion_rate": 0},
            "compliance_metrics": {"pm_compliance_rate": 0, "overall_compliance": 0},
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
        }


# Global analytics service instance
analytics_service = AnalyticsService()
