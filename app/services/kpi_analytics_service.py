"""
KPI Analytics Service for ChatterFix CMMS
Provides enterprise-grade maintenance analytics and insights.

Key Metrics:
- MTTR (Mean Time To Repair)
- MTBF (Mean Time Between Failures)
- Work Order Completion Rates
- PM Compliance Rate
- Downtime Analysis
- Cost Analysis
- Technician Performance
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class KPIAnalyticsService:
    """Service for calculating maintenance KPIs and analytics."""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    async def get_comprehensive_kpis(
        self,
        organization_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get all KPIs for an organization in a single call.
        """
        try:
            # Fetch all required data
            work_orders = await self._get_work_orders(organization_id, days)
            assets = await self._get_assets(organization_id)
            maintenance_history = await self._get_maintenance_history(organization_id, days)
            pm_schedules = await self._get_pm_schedules(organization_id)

            # Calculate all KPIs
            return {
                "period_days": days,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "work_order_metrics": await self._calculate_work_order_metrics(work_orders),
                "mttr": await self._calculate_mttr(work_orders),
                "mtbf": await self._calculate_mtbf(work_orders, assets),
                "pm_compliance": await self._calculate_pm_compliance(work_orders, pm_schedules),
                "downtime_analysis": await self._calculate_downtime(maintenance_history, assets),
                "cost_analysis": await self._calculate_costs(work_orders, maintenance_history),
                "technician_performance": await self._calculate_technician_performance(work_orders),
                "asset_reliability": await self._calculate_asset_reliability(work_orders, assets),
                "trend_data": await self._calculate_trends(work_orders, days),
            }
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {"error": str(e)}

    async def _get_work_orders(self, organization_id: str, days: int) -> List[Dict]:
        """Fetch work orders for the period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        all_wos = await self.firestore_manager.get_collection(
            "work_orders",
            filters=[{"field": "organization_id", "operator": "==", "value": organization_id}]
        )

        # Filter by date and convert timestamps
        filtered = []
        for wo in all_wos:
            created = wo.get("created_at")
            if created:
                if hasattr(created, 'timestamp'):
                    created_dt = created
                elif isinstance(created, str):
                    try:
                        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    except:
                        continue
                else:
                    continue

                if created_dt.replace(tzinfo=timezone.utc) >= cutoff:
                    wo['_created_dt'] = created_dt
                    filtered.append(wo)

        return filtered

    async def _get_assets(self, organization_id: str) -> List[Dict]:
        """Fetch all assets."""
        return await self.firestore_manager.get_collection(
            "assets",
            filters=[{"field": "organization_id", "operator": "==", "value": organization_id}]
        )

    async def _get_maintenance_history(self, organization_id: str, days: int) -> List[Dict]:
        """Fetch maintenance history."""
        try:
            return await self.firestore_manager.get_collection(
                "maintenance_history",
                filters=[{"field": "organization_id", "operator": "==", "value": organization_id}],
                limit=500
            )
        except:
            return []

    async def _get_pm_schedules(self, organization_id: str) -> List[Dict]:
        """Fetch PM schedules."""
        try:
            return await self.firestore_manager.get_collection(
                "pm_schedules",
                filters=[{"field": "organization_id", "operator": "==", "value": organization_id}]
            )
        except:
            return []

    async def _calculate_work_order_metrics(self, work_orders: List[Dict]) -> Dict[str, Any]:
        """Calculate work order statistics."""
        total = len(work_orders)
        if total == 0:
            return {
                "total": 0,
                "open": 0,
                "in_progress": 0,
                "completed": 0,
                "overdue": 0,
                "completion_rate": 0,
                "by_priority": {},
                "by_type": {},
            }

        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        type_counts = defaultdict(int)
        overdue = 0
        now = datetime.now(timezone.utc)

        for wo in work_orders:
            status = wo.get("status", "Unknown")
            priority = wo.get("priority", "Medium")
            wo_type = wo.get("work_order_type", "General")

            status_counts[status] += 1
            priority_counts[priority] += 1
            type_counts[wo_type] += 1

            # Check if overdue
            due_date = wo.get("due_date") or wo.get("scheduled_date")
            if due_date and status not in ["Completed", "Cancelled"]:
                if isinstance(due_date, str):
                    try:
                        due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        if due_dt < now:
                            overdue += 1
                    except:
                        pass

        completed = status_counts.get("Completed", 0)
        completion_rate = round((completed / total) * 100, 1) if total > 0 else 0

        return {
            "total": total,
            "open": status_counts.get("Open", 0),
            "in_progress": status_counts.get("In Progress", 0),
            "completed": completed,
            "on_hold": status_counts.get("On Hold", 0),
            "cancelled": status_counts.get("Cancelled", 0),
            "overdue": overdue,
            "completion_rate": completion_rate,
            "by_priority": dict(priority_counts),
            "by_type": dict(type_counts),
        }

    async def _calculate_mttr(self, work_orders: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Mean Time To Repair (MTTR).
        MTTR = Total repair time / Number of repairs
        """
        completed_wos = [wo for wo in work_orders if wo.get("status") == "Completed"]

        if not completed_wos:
            return {
                "overall_hours": 0,
                "overall_formatted": "N/A",
                "by_priority": {},
                "by_asset": {},
                "trend": "stable",
            }

        repair_times = []
        by_priority = defaultdict(list)
        by_asset = defaultdict(list)

        for wo in completed_wos:
            created = wo.get("_created_dt") or wo.get("created_at")
            completed = wo.get("completed_at")

            if created and completed:
                try:
                    if isinstance(created, str):
                        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    else:
                        created_dt = created

                    if isinstance(completed, str):
                        completed_dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                    else:
                        completed_dt = completed

                    # Ensure both have timezone
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)
                    if completed_dt.tzinfo is None:
                        completed_dt = completed_dt.replace(tzinfo=timezone.utc)

                    hours = (completed_dt - created_dt).total_seconds() / 3600

                    if 0 < hours < 720:  # Reasonable range (0 to 30 days)
                        repair_times.append(hours)
                        by_priority[wo.get("priority", "Medium")].append(hours)

                        asset_id = wo.get("asset_id")
                        if asset_id:
                            by_asset[asset_id].append(hours)
                except Exception as e:
                    logger.debug(f"Error calculating MTTR for WO: {e}")

        if not repair_times:
            return {
                "overall_hours": 0,
                "overall_formatted": "N/A",
                "by_priority": {},
                "by_asset": {},
                "trend": "stable",
            }

        avg_hours = sum(repair_times) / len(repair_times)

        # Format nicely
        if avg_hours < 1:
            formatted = f"{int(avg_hours * 60)} minutes"
        elif avg_hours < 24:
            formatted = f"{avg_hours:.1f} hours"
        else:
            formatted = f"{avg_hours / 24:.1f} days"

        # Calculate by priority
        priority_mttr = {}
        for priority, times in by_priority.items():
            if times:
                avg = sum(times) / len(times)
                priority_mttr[priority] = round(avg, 1)

        # Top 5 slowest assets
        asset_mttr = {}
        for asset_id, times in sorted(by_asset.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, reverse=True)[:5]:
            if times:
                asset_mttr[asset_id] = round(sum(times) / len(times), 1)

        return {
            "overall_hours": round(avg_hours, 2),
            "overall_formatted": formatted,
            "sample_size": len(repair_times),
            "by_priority": priority_mttr,
            "slowest_assets": asset_mttr,
            "trend": "stable",
        }

    async def _calculate_mtbf(self, work_orders: List[Dict], assets: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Mean Time Between Failures (MTBF).
        MTBF = Total operating time / Number of failures
        """
        # Group failures by asset
        failures_by_asset = defaultdict(list)

        failure_types = ["Corrective", "Emergency", "Breakdown"]
        for wo in work_orders:
            wo_type = wo.get("work_order_type", "")
            if wo_type in failure_types or "failure" in wo.get("title", "").lower():
                asset_id = wo.get("asset_id")
                if asset_id:
                    created = wo.get("_created_dt") or wo.get("created_at")
                    if created:
                        failures_by_asset[asset_id].append(created)

        if not failures_by_asset:
            return {
                "overall_days": 0,
                "overall_formatted": "No failures recorded",
                "by_asset": {},
                "most_reliable": [],
                "least_reliable": [],
            }

        # Calculate MTBF per asset
        asset_mtbf = {}
        asset_map = {a.get("id"): a.get("name", "Unknown") for a in assets}

        for asset_id, failure_dates in failures_by_asset.items():
            if len(failure_dates) >= 2:
                # Sort dates and calculate intervals
                sorted_dates = sorted(failure_dates)
                intervals = []
                for i in range(1, len(sorted_dates)):
                    prev = sorted_dates[i-1]
                    curr = sorted_dates[i]

                    if isinstance(prev, str):
                        prev = datetime.fromisoformat(prev.replace('Z', '+00:00'))
                    if isinstance(curr, str):
                        curr = datetime.fromisoformat(curr.replace('Z', '+00:00'))

                    days = (curr - prev).days
                    if days > 0:
                        intervals.append(days)

                if intervals:
                    avg_days = sum(intervals) / len(intervals)
                    asset_name = asset_map.get(asset_id, asset_id[:8])
                    asset_mtbf[asset_name] = round(avg_days, 1)

        if not asset_mtbf:
            return {
                "overall_days": 0,
                "overall_formatted": "Insufficient data",
                "by_asset": {},
                "most_reliable": [],
                "least_reliable": [],
            }

        # Overall average
        overall_avg = sum(asset_mtbf.values()) / len(asset_mtbf)

        # Sort for most/least reliable
        sorted_assets = sorted(asset_mtbf.items(), key=lambda x: x[1], reverse=True)

        return {
            "overall_days": round(overall_avg, 1),
            "overall_formatted": f"{overall_avg:.0f} days between failures",
            "assets_analyzed": len(asset_mtbf),
            "by_asset": asset_mtbf,
            "most_reliable": sorted_assets[:3],
            "least_reliable": sorted_assets[-3:] if len(sorted_assets) >= 3 else sorted_assets,
        }

    async def _calculate_pm_compliance(self, work_orders: List[Dict], pm_schedules: List[Dict]) -> Dict[str, Any]:
        """
        Calculate PM Compliance Rate.
        % of preventive maintenance tasks completed on time.
        """
        pm_work_orders = [wo for wo in work_orders if wo.get("work_order_type") == "Preventive"]

        if not pm_work_orders:
            return {
                "compliance_rate": 0,
                "total_pm": 0,
                "completed_on_time": 0,
                "completed_late": 0,
                "missed": 0,
                "status": "No PM data",
            }

        completed_on_time = 0
        completed_late = 0
        missed = 0
        now = datetime.now(timezone.utc)

        for wo in pm_work_orders:
            status = wo.get("status")
            due_date = wo.get("due_date") or wo.get("scheduled_date")
            completed_at = wo.get("completed_at")

            if status == "Completed":
                if due_date and completed_at:
                    try:
                        if isinstance(due_date, str):
                            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        else:
                            due_dt = due_date

                        if isinstance(completed_at, str):
                            completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        else:
                            completed_dt = completed_at

                        if completed_dt <= due_dt:
                            completed_on_time += 1
                        else:
                            completed_late += 1
                    except:
                        completed_on_time += 1  # Assume on time if can't parse
                else:
                    completed_on_time += 1
            elif status not in ["Completed", "Cancelled"]:
                if due_date:
                    try:
                        if isinstance(due_date, str):
                            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        else:
                            due_dt = due_date

                        if due_dt < now:
                            missed += 1
                    except:
                        pass

        total = len(pm_work_orders)
        compliance_rate = round((completed_on_time / total) * 100, 1) if total > 0 else 0

        # Determine status
        if compliance_rate >= 90:
            status = "Excellent"
        elif compliance_rate >= 75:
            status = "Good"
        elif compliance_rate >= 50:
            status = "Needs Improvement"
        else:
            status = "Critical"

        return {
            "compliance_rate": compliance_rate,
            "total_pm": total,
            "completed_on_time": completed_on_time,
            "completed_late": completed_late,
            "missed": missed,
            "pending": total - completed_on_time - completed_late - missed,
            "status": status,
        }

    async def _calculate_downtime(self, maintenance_history: List[Dict], assets: List[Dict]) -> Dict[str, Any]:
        """Calculate downtime analytics."""
        if not maintenance_history:
            return {
                "total_hours": 0,
                "by_asset": {},
                "by_category": {},
                "avg_per_incident": 0,
            }

        total_downtime = 0
        by_asset = defaultdict(float)
        by_category = defaultdict(float)
        incidents = 0
        asset_map = {a.get("id"): a.get("name", "Unknown") for a in assets}

        for record in maintenance_history:
            downtime = record.get("downtime_hours", 0) or 0
            if downtime > 0:
                total_downtime += downtime
                incidents += 1

                asset_id = record.get("asset_id")
                if asset_id:
                    asset_name = asset_map.get(asset_id, asset_id[:8])
                    by_asset[asset_name] += downtime

                category = record.get("maintenance_type", "Other")
                by_category[category] += downtime

        return {
            "total_hours": round(total_downtime, 1),
            "incidents": incidents,
            "avg_per_incident": round(total_downtime / incidents, 1) if incidents > 0 else 0,
            "by_asset": dict(sorted(by_asset.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_category": dict(by_category),
        }

    async def _calculate_costs(self, work_orders: List[Dict], maintenance_history: List[Dict]) -> Dict[str, Any]:
        """Calculate cost analytics."""
        total_labor = 0
        total_parts = 0
        by_type = defaultdict(float)
        by_asset = defaultdict(float)

        for wo in work_orders:
            labor_hours = wo.get("labor_hours", 0) or 0
            labor_rate = 50  # Default hourly rate
            labor_cost = labor_hours * labor_rate
            total_labor += labor_cost

            # Parts costs from work order
            parts_used = wo.get("parts_used", [])
            for part in parts_used:
                part_cost = part.get("cost", 0) or 0
                total_parts += part_cost

            wo_type = wo.get("work_order_type", "General")
            by_type[wo_type] += labor_cost

            asset_id = wo.get("asset_id")
            if asset_id:
                by_asset[asset_id] += labor_cost

        # Also check maintenance history for costs
        for record in maintenance_history:
            labor = record.get("labor_cost", 0) or 0
            parts = record.get("parts_cost", 0) or 0
            total_labor += labor
            total_parts += parts

        total_cost = total_labor + total_parts

        return {
            "total_cost": round(total_cost, 2),
            "labor_cost": round(total_labor, 2),
            "parts_cost": round(total_parts, 2),
            "labor_percentage": round((total_labor / total_cost) * 100, 1) if total_cost > 0 else 0,
            "parts_percentage": round((total_parts / total_cost) * 100, 1) if total_cost > 0 else 0,
            "by_type": dict(by_type),
            "avg_per_wo": round(total_cost / len(work_orders), 2) if work_orders else 0,
        }

    async def _calculate_technician_performance(self, work_orders: List[Dict]) -> Dict[str, Any]:
        """Calculate technician performance metrics."""
        tech_stats = defaultdict(lambda: {
            "completed": 0,
            "total_assigned": 0,
            "total_hours": 0,
            "on_time": 0,
        })

        for wo in work_orders:
            tech_id = wo.get("assigned_to_uid") or wo.get("assigned_to")
            if not tech_id:
                continue

            tech_name = wo.get("assigned_to_name", tech_id)

            tech_stats[tech_name]["total_assigned"] += 1

            if wo.get("status") == "Completed":
                tech_stats[tech_name]["completed"] += 1
                tech_stats[tech_name]["total_hours"] += wo.get("labor_hours", 0) or 0

                # Check if on time
                due_date = wo.get("due_date")
                completed_at = wo.get("completed_at")
                if due_date and completed_at:
                    try:
                        if isinstance(due_date, str):
                            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                        else:
                            due_dt = due_date
                        if isinstance(completed_at, str):
                            completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        else:
                            completed_dt = completed_at

                        if completed_dt <= due_dt:
                            tech_stats[tech_name]["on_time"] += 1
                    except:
                        pass

        # Calculate metrics per technician
        technicians = []
        for name, stats in tech_stats.items():
            completion_rate = round((stats["completed"] / stats["total_assigned"]) * 100, 1) if stats["total_assigned"] > 0 else 0
            avg_hours = round(stats["total_hours"] / stats["completed"], 1) if stats["completed"] > 0 else 0
            on_time_rate = round((stats["on_time"] / stats["completed"]) * 100, 1) if stats["completed"] > 0 else 0

            technicians.append({
                "name": name,
                "jobs_completed": stats["completed"],
                "jobs_assigned": stats["total_assigned"],
                "completion_rate": completion_rate,
                "avg_hours_per_job": avg_hours,
                "on_time_rate": on_time_rate,
                "total_hours": round(stats["total_hours"], 1),
            })

        # Sort by jobs completed
        technicians.sort(key=lambda x: x["jobs_completed"], reverse=True)

        return {
            "technician_count": len(technicians),
            "technicians": technicians[:10],  # Top 10
            "top_performer": technicians[0] if technicians else None,
        }

    async def _calculate_asset_reliability(self, work_orders: List[Dict], assets: List[Dict]) -> Dict[str, Any]:
        """Calculate asset reliability scores."""
        asset_failures = defaultdict(int)
        asset_map = {a.get("id"): a for a in assets}

        failure_types = ["Corrective", "Emergency", "Breakdown"]
        for wo in work_orders:
            wo_type = wo.get("work_order_type", "")
            if wo_type in failure_types:
                asset_id = wo.get("asset_id")
                if asset_id:
                    asset_failures[asset_id] += 1

        # Score each asset
        reliability_scores = []
        for asset in assets:
            asset_id = asset.get("id")
            failures = asset_failures.get(asset_id, 0)

            # Higher failures = lower reliability
            if failures == 0:
                score = 100
            elif failures <= 2:
                score = 85
            elif failures <= 5:
                score = 70
            elif failures <= 10:
                score = 50
            else:
                score = 30

            reliability_scores.append({
                "asset_id": asset_id,
                "asset_name": asset.get("name", "Unknown"),
                "location": asset.get("location", ""),
                "failures": failures,
                "reliability_score": score,
                "criticality": asset.get("criticality", "Medium"),
            })

        # Sort by reliability (worst first for attention)
        reliability_scores.sort(key=lambda x: x["reliability_score"])

        avg_score = sum(a["reliability_score"] for a in reliability_scores) / len(reliability_scores) if reliability_scores else 0

        return {
            "average_reliability": round(avg_score, 1),
            "assets_analyzed": len(reliability_scores),
            "critical_assets": [a for a in reliability_scores if a["reliability_score"] < 50][:5],
            "at_risk_assets": [a for a in reliability_scores if 50 <= a["reliability_score"] < 70][:5],
            "healthy_assets": len([a for a in reliability_scores if a["reliability_score"] >= 85]),
        }

    async def _calculate_trends(self, work_orders: List[Dict], days: int) -> Dict[str, Any]:
        """Calculate trend data for charts."""
        # Group by week
        weekly_data = defaultdict(lambda: {"created": 0, "completed": 0})

        for wo in work_orders:
            created = wo.get("_created_dt")
            if created:
                if isinstance(created, str):
                    try:
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    except:
                        continue

                # Get week start (Monday)
                week_start = created - timedelta(days=created.weekday())
                week_key = week_start.strftime("%Y-%m-%d")

                weekly_data[week_key]["created"] += 1

                if wo.get("status") == "Completed":
                    weekly_data[week_key]["completed"] += 1

        # Sort by date
        sorted_weeks = sorted(weekly_data.items())

        return {
            "weekly_created": [{"week": k, "count": v["created"]} for k, v in sorted_weeks],
            "weekly_completed": [{"week": k, "count": v["completed"]} for k, v in sorted_weeks],
        }


# Singleton instance
kpi_analytics_service = KPIAnalyticsService()


async def get_kpi_dashboard(organization_id: str, days: int = 30) -> Dict[str, Any]:
    """Convenience function to get full KPI dashboard."""
    return await kpi_analytics_service.get_comprehensive_kpis(organization_id, days)
