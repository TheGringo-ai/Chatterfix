import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for advanced analytics and KPI calculations"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes cache

    async def get_kpi_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of all KPIs for the dashboard"""
        try:
            mttr, mtbf, asset_utilization, cost_tracking, work_order_metrics, compliance_metrics = await asyncio.gather(
                self.calculate_mttr(days),
                self.calculate_mtbf(days),
                self.calculate_asset_utilization(days),
                self.get_cost_tracking(days),
                self.get_work_order_metrics(days),
                self.get_compliance_metrics(days),
            )
            return {
                "mttr": mttr,
                "mtbf": mtbf,
                "asset_utilization": asset_utilization,
                "cost_tracking": cost_tracking,
                "work_order_metrics": work_order_metrics,
                "compliance_metrics": compliance_metrics,
                "generated_at": datetime.now().isoformat(),
                "period_days": days,
            }
        except Exception as e:
            logger.error(f"Error calculating KPI summary: {e}")
            return self._get_default_kpi_summary(days)

    async def calculate_mttr(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate Mean Time To Repair (MTTR) - Firestore compatible
        MTTR = Total Repair Time / Number of Repairs
        """
        try:
            firestore_manager = get_firestore_manager()
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            completed_wos = await firestore_manager.get_collection(
                "work_orders",
                filters=[
                    {"field": "status", "operator": "==", "value": "Completed"},
                    {"field": "completed_date", "operator": ">=", "value": start_date}
                ]
            )

            repair_times = []
            for wo in completed_wos:
                if wo.get("actual_start") and wo.get("actual_end"):
                    start = datetime.fromisoformat(wo["actual_start"])
                    end = datetime.fromisoformat(wo["actual_end"])
                    repair_times.append((end - start).total_seconds() / 3600) # in hours

            if repair_times:
                total_repairs = len(repair_times)
                avg_repair_time = sum(repair_times) / total_repairs
                return {
                    "value": round(avg_repair_time, 2), "unit": "hours",
                    "total_repairs": total_repairs,
                    "total_repair_time": round(sum(repair_times), 2),
                    "min_repair_time": round(min(repair_times), 2),
                    "max_repair_time": round(max(repair_times), 2),
                    "trend": "stable", # Trend calculation needs historical data
                    "status": self._get_mttr_status(avg_repair_time),
                }

            return self._get_default_mttr()
        except Exception as e:
            logger.error(f"Error in calculate_mttr: {e}")
            return self._get_default_mttr()

    async def calculate_mtbf(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate Mean Time Between Failures (MTBF)
        MTBF = Total Operating Time / Number of Failures
        """
        try:
            firestore_manager = get_firestore_manager()
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            failures, assets = await asyncio.gather(
                firestore_manager.get_collection(
                    "maintenance_history",
                    filters=[
                        {"field": "maintenance_type", "operator": "in", "value": ["Corrective", "Emergency"]},
                        {"field": "created_date", "operator": ">=", "value": start_date}
                    ]
                ),
                firestore_manager.get_collection("assets", filters=[{"field": "status", "operator": "==", "value": "Active"}])
            )

            failure_count = len(failures)
            total_assets = len(assets)
            total_operating_hours = total_assets * days * 24
            total_downtime = sum(f.get("downtime_hours", 0) for f in failures)

            if failure_count > 0:
                mtbf_hours = total_operating_hours / failure_count
                return {
                    "value": round(mtbf_hours, 2), "unit": "hours",
                    "failure_count": failure_count,
                    "total_operating_hours": total_operating_hours,
                    "total_downtime": round(total_downtime, 2),
                    "trend": "stable", # Trend calculation needs historical data
                    "status": self._get_mtbf_status(mtbf_hours),
                }

            return {
                "value": total_operating_hours, "unit": "hours", "failure_count": 0,
                "total_operating_hours": total_operating_hours, "total_downtime": 0,
                "trend": "stable", "status": "excellent",
                "message": "No failures recorded in this period",
            }
        except Exception as e:
            logger.error(f"Error in calculate_mtbf: {e}")
            return {
                "value": 0, "unit": "hours", "failure_count": 0,
                "total_operating_hours": 0, "total_downtime": 0,
                "trend": "stable", "status": "unknown",
                "message": "Analytics unavailable",
            }

    def _get_utilization_status(self, utilization: float) -> str:
        """Get status based on utilization rate"""
        if utilization >= 95: return "excellent"
        elif utilization >= 85: return "good"
        elif utilization >= 70: return "warning"
        return "critical"

    async def calculate_asset_utilization(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate asset utilization metrics
        """
        try:
            firestore_manager = get_firestore_manager()
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            assets, history = await asyncio.gather(
                firestore_manager.get_collection("assets"),
                firestore_manager.get_collection("maintenance_history", filters=[{"field": "created_date", "operator": ">=", "value": start_date}])
            )

            status_breakdown = {}
            for asset in assets:
                status = asset.get("status", "Unknown")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            total_assets = len(assets)
            active_assets = status_breakdown.get("Active", 0)
            
            total_hours = days * 24
            asset_data = []
            total_uptime = 0

            # This is inefficient and should be done with better queries or data modeling in a real app
            active_asset_ids = {a["id"] for a in assets if a.get("status") == "Active"}
            for asset_id in active_asset_ids:
                asset_name = next((a["name"] for a in assets if a["id"] == asset_id), "Unknown")
                downtime = sum(h.get("downtime_hours", 0) for h in history if h.get("asset_id") == asset_id)
                events = len([h for h in history if h.get("asset_id") == asset_id])
                uptime = total_hours - downtime
                utilization_rate = (uptime / total_hours) * 100 if total_hours > 0 else 100
                total_uptime += uptime
                asset_data.append({
                    "id": asset_id, "name": asset_name, "maintenance_events": events,
                    "downtime_hours": round(downtime, 2), "utilization_rate": round(utilization_rate, 2),
                })

            avg_utilization = (total_uptime / (active_assets * total_hours)) * 100 if active_assets > 0 and total_hours > 0 else 100

            return {
                "average_utilization": round(avg_utilization, 2), "unit": "percent",
                "total_assets": total_assets, "active_assets": active_assets,
                "status_breakdown": status_breakdown,
                "top_utilized": sorted(asset_data, key=lambda x: x["utilization_rate"], reverse=True)[:5],
                "low_utilized": sorted(asset_data, key=lambda x: x["utilization_rate"])[:5],
                "trend": "stable", # Trend calculation needs historical data
                "status": self._get_utilization_status(avg_utilization),
            }
        except Exception as e:
            logger.error(f"Error in calculate_asset_utilization: {e}")
            return {
                "average_utilization": 0, "unit": "percent", "total_assets": 0,
                "active_assets": 0, "status_breakdown": {},
                "top_utilized": [], "low_utilized": [],
                "trend": "stable", "status": "unknown",
            }


    async def get_cost_tracking(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive cost tracking metrics
        """
        try:
            firestore_manager = get_firestore_manager()
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            history = await firestore_manager.get_collection(
                "maintenance_history",
                filters=[{"field": "created_date", "operator": ">=", "value": start_date}]
            )

            if not history:
                return {"total_cost": 0, "labor_cost": 0, "parts_cost": 0, "maintenance_count": 0, "avg_cost_per_event": 0, "costs_by_type": {}, "top_costly_assets": [], "daily_trend": [], "trend": "stable", "currency": "USD"}

            total_cost = sum(h.get("total_cost", 0) for h in history)
            labor_cost = sum(h.get("labor_cost", 0) for h in history)
            parts_cost = sum(h.get("parts_cost", 0) for h in history)
            maintenance_count = len(history)
            avg_cost_per_event = total_cost / maintenance_count if maintenance_count > 0 else 0

            costs_by_type = {}
            for h in history:
                m_type = h.get("maintenance_type", "Unknown")
                costs_by_type[m_type] = costs_by_type.get(m_type, 0) + h.get("total_cost", 0)

            costly_assets_agg = {}
            for h in history:
                asset_id = h.get("asset_id")
                if asset_id:
                    if asset_id not in costly_assets_agg:
                        costly_assets_agg[asset_id] = {"total_cost": 0, "events": 0, "name": h.get("asset_name", asset_id)}
                    costly_assets_agg[asset_id]["total_cost"] += h.get("total_cost", 0)
                    costly_assets_agg[asset_id]["events"] += 1
            
            top_costly_assets = sorted(costly_assets_agg.items(), key=lambda item: item[1]["total_cost"], reverse=True)[:10]


            daily_trend_agg = {}
            for h in history:
                date_str = h.get("created_date", "").split("T")[0]
                if date_str:
                    daily_trend_agg[date_str] = daily_trend_agg.get(date_str, 0) + h.get("total_cost", 0)
            
            daily_trend = [{"date": d, "cost": round(c, 2)} for d, c in sorted(daily_trend_agg.items())]


            return {
                "total_cost": round(total_cost, 2),
                "labor_cost": round(labor_cost, 2),
                "parts_cost": round(parts_cost, 2),
                "maintenance_count": maintenance_count,
                "avg_cost_per_event": round(avg_cost_per_event, 2),
                "costs_by_type": {k: round(v, 2) for k, v in costs_by_type.items()},
                "top_costly_assets": [{"id": k, **v} for k,v in top_costly_assets],
                "daily_trend": daily_trend,
                "trend": "stable", # Trend calculation needs historical data
                "currency": "USD",
            }
        except Exception as e:
            logger.error(f"Error in get_cost_tracking: {e}")
            return {"total_cost": 0, "labor_cost": 0, "parts_cost": 0, "maintenance_count": 0, "avg_cost_per_event": 0, "costs_by_type": {}, "top_costly_assets": [], "daily_trend": [], "trend": "stable", "currency": "USD"}


    async def get_work_order_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive work order metrics
        """
        try:
            firestore_manager = get_firestore_manager()
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            work_orders = await firestore_manager.get_collection(
                "work_orders",
                filters=[{"field": "created_date", "operator": ">=", "value": start_date.isoformat()}]
            )

            if not work_orders:
                return {"total_created": 0, "completion_rate": 0, "overdue_count": 0, "status_breakdown": {}, "priority_breakdown": {}, "daily_trend": [], "trend": "stable", "status": "unknown"}

            status_breakdown = {}
            priority_breakdown = {}
            daily_trend_agg = {}
            overdue_count = 0
            
            for wo in work_orders:
                status = wo.get("status", "Unknown")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                priority = wo.get("priority", "Unknown")
                priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1

                due_date_str = wo.get("due_date")
                if due_date_str and status not in ["Completed", "Cancelled"]:
                    due_date = datetime.fromisoformat(due_date_str)
                    if due_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                        overdue_count += 1
                
                date_str = wo.get("created_date", "").split("T")[0]
                if date_str:
                    if date_str not in daily_trend_agg:
                        daily_trend_agg[date_str] = {"created": 0, "completed": 0}
                    daily_trend_agg[date_str]["created"] += 1
                    if status == "Completed":
                        daily_trend_agg[date_str]["completed"] += 1

            total_created = len(work_orders)
            completed = status_breakdown.get("Completed", 0)
            completion_rate = (completed / total_created * 100) if total_created > 0 else 0
            
            daily_trend = [{"date": d, **v} for d, v in sorted(daily_trend_agg.items())]

            return {
                "total_created": total_created,
                "completion_rate": round(completion_rate, 2),
                "overdue_count": overdue_count,
                "status_breakdown": status_breakdown,
                "priority_breakdown": priority_breakdown,
                "daily_trend": daily_trend,
                "trend": "stable",
                "status": "good" if completion_rate >= 80 else "warning" if completion_rate >= 60 else "critical",
            }
        except Exception as e:
            logger.error(f"Error in get_work_order_metrics: {e}")
            return {"total_created": 0, "completion_rate": 0, "overdue_count": 0, "status_breakdown": {}, "priority_breakdown": {}, "daily_trend": [], "trend": "stable", "status": "unknown"}


    async def get_compliance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get compliance and PM schedule adherence metrics
        """
        try:
            firestore_manager = get_firestore_manager()
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            completed_wos, user_training, user_skills = await asyncio.gather(
                firestore_manager.get_collection("work_orders", filters=[
                    {"field": "status", "operator": "==", "value": "Completed"},
                    {"field": "created_date", "operator": ">=", "value": start_date.isoformat()}
                ]),
                firestore_manager.get_collection("user_training"),
                firestore_manager.get_collection("user_skills") # Assuming a user_skills collection exists
            )

            total_pm = len([wo for wo in completed_wos if wo.get("work_order_type") == "Preventive"])
            on_time_pm = 0
            for wo in completed_wos:
                if wo.get("work_order_type") == "Preventive" and wo.get("due_date") and wo.get("completed_date"):
                    due_date = datetime.fromisoformat(wo["due_date"])
                    completed_date = datetime.fromisoformat(wo["completed_date"])
                    if completed_date <= due_date:
                        on_time_pm += 1
            
            pm_compliance = (on_time_pm / total_pm * 100) if total_pm > 0 else 100

            total_training = len(user_training)
            completed_training = len([t for t in user_training if t.get("status") == "completed"])
            training_compliance = (completed_training / total_training * 100) if total_training > 0 else 100

            total_certs = len([s for s in user_skills if s.get("certified")])
            valid_certs = 0
            expired_certs = 0
            for skill in user_skills:
                if skill.get("certified") and skill.get("certification_expiry"):
                    expiry_date = datetime.fromisoformat(skill["certification_expiry"])
                    if expiry_date.replace(tzinfo=timezone.utc) >= datetime.now(timezone.utc):
                        valid_certs += 1
                    else:
                        expired_certs += 1

            return {
                "pm_compliance_rate": round(pm_compliance, 2),
                "total_pm_work_orders": total_pm,
                "on_time_completions": on_time_pm,
                "training_compliance_rate": round(training_compliance, 2),
                "total_training_assigned": total_training,
                "training_completed": completed_training,
                "certification_status": {
                    "total": total_certs, "valid": valid_certs, "expired": expired_certs
                },
                "overall_compliance": round((pm_compliance + training_compliance) / 2, 2),
                "status": "good" if pm_compliance >= 90 else "warning" if pm_compliance >= 70 else "critical",
            }

        except Exception as e:
            logger.error(f"Error in get_compliance_metrics: {e}")
            return {"pm_compliance_rate": 0, "total_pm_work_orders": 0, "on_time_completions": 0, "training_compliance_rate": 0, "total_training_assigned": 0, "training_completed": 0, "certification_status": {"total": 0, "valid": 0, "expired": 0,}, "overall_compliance": 0, "status": "unknown"}


    async def get_trend_data(self, metric: str, days: int = 30, interval: str = "day") -> List[Dict[str, Any]]:
        """
        Get historical trend data for a specific metric
        """
        firestore_manager = get_firestore_manager()
        if metric == "mttr":
            return await self._get_mttr_trend(firestore_manager, days)
        elif metric == "mtbf":
            return await self._get_mtbf_trend(firestore_manager, days)
        elif metric == "cost":
            return await self._get_cost_trend(firestore_manager, days)
        elif metric == "work_orders":
            return await self._get_work_order_trend(firestore_manager, days)
        return []

    async def _get_mttr_trend(self, firestore_manager, days: int) -> List[Dict[str, Any]]:
        """Get MTTR trend over time"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        completed_wos = await firestore_manager.get_collection(
            "work_orders",
            filters=[
                {"field": "status", "operator": "==", "value": "Completed"},
                {"field": "completed_date", "operator": ">=", "value": start_date}
            ]
        )
        # This is a simplified trend. A real implementation would group by day.
        return [{"date": wo.get("completed_date", "").split("T")[0], "value": wo.get("actual_hours", 0)} for wo in completed_wos]

    async def _get_mtbf_trend(self, firestore_manager, days: int) -> List[Dict[str, Any]]:
        """Get MTBF trend over time"""
        # This is complex to calculate as a trend, so returning mock data for now.
        return []

    async def _get_cost_trend(self, firestore_manager, days: int) -> List[Dict[str, Any]]:
        """Get cost trend over time"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        history = await firestore_manager.get_collection(
            "maintenance_history",
            filters=[{"field": "created_date", "operator": ">=", "value": start_date}]
        )
        daily_costs = {}
        for h in history:
            date_str = h.get("created_date", "").split("T")[0]
            if date_str:
                daily_costs[date_str] = daily_costs.get(date_str, 0) + h.get("total_cost", 0)
        return [{"date": d, "value": round(c, 2)} for d, c in sorted(daily_costs.items())]

    async def _get_work_order_trend(self, firestore_manager, days: int) -> List[Dict[str, Any]]:
        """Get work order completion trend over time"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        work_orders = await firestore_manager.get_collection(
            "work_orders",
            filters=[{"field": "created_date", "operator": ">=", "value": start_date.isoformat()}]
        )
        daily_agg = {}
        for wo in work_orders:
            date_str = wo.get("created_date", "").split("T")[0]
            if date_str:
                if date_str not in daily_agg:
                    daily_agg[date_str] = {"created": 0, "completed": 0}
                daily_agg[date_str]["created"] += 1
                if wo.get("status") == "Completed":
                    daily_agg[date_str]["completed"] += 1
        return [{"date": d, **v} for d, v in sorted(daily_agg.items())]

    async def _calculate_trend(self, metric: str, current_value: float, days: int) -> str:
        """
        Calculate trend direction compared to previous period
        (NEEDS REFACTORING TO FIRESTORE)
        """
        # This logic needs to be updated to fetch previous period data from Firestore
        return "stable"
    
    def _get_mttr_status(self, mttr_hours: float) -> str:
        """Get status based on MTTR value"""
        if mttr_hours <= 2: return "excellent"
        elif mttr_hours <= 4: return "good"
        elif mttr_hours <= 8: return "warning"
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
        if utilization >= 95: return "excellent"
        elif utilization >= 85: return "good"
        elif utilization >= 70: return "warning"
        return "critical"

    # ... other private helpers
    def _get_default_mttr(self) -> Dict[str, Any]:
        """Return default MTTR data"""
        return {
            "value": 0, "unit": "hours", "total_repairs": 0, "total_repair_time": 0,
            "min_repair_time": 0, "max_repair_time": 0, "trend": "stable",
            "status": "excellent", "message": "No repair data available for this period",
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
