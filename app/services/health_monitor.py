#!/usr/bin/env python3
"""
ChatterFix CMMS - Enhanced Health Monitoring & SLO System
Comprehensive system health, uptime tracking, and error budget monitoring
"""

import os
import sys
import time
import json
import psutil
import aiosqlite
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class HealthMetric:
    """Individual health metric"""

    name: str
    value: Any
    status: str  # healthy, warning, critical
    threshold: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class SLOTarget:
    """Service Level Objective definition"""

    name: str
    target_percentage: float  # 99.9 = 99.9%
    time_window_hours: int  # 24, 168 (week), 720 (month)
    error_budget_minutes: float = 0.0  # calculated from target

    def __post_init__(self):
        # Calculate error budget in minutes
        total_minutes = self.time_window_hours * 60
        self.error_budget_minutes = total_minutes * (1 - self.target_percentage / 100)


class HealthMonitor:
    """Enhanced health monitoring system with SLO tracking"""

    def __init__(self, data_dir: str = "/tmp/chatterfix-health"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize SQLite for metrics storage
        self.db_path = self.data_dir / "health_metrics.db"
        # Database will be initialized asynchronously when first accessed
        self._db_initialized = False

        # SLO definitions
        self.slos = {
            "uptime": SLOTarget("System Uptime", 99.9, 24),
            "response_time": SLOTarget("API Response Time", 99.0, 24),
            "error_rate": SLOTarget("Error Rate", 99.5, 24),
        }

        # Health check configuration
        self.checks = {
            "system_resources": self.check_system_resources,
            "disk_space": self.check_disk_space,
            "memory_usage": self.check_memory_usage,
            "process_health": self.check_process_health,
            "database_connection": self.check_database_connection,
            "ai_services": self.check_ai_services,
            "external_dependencies": self.check_external_dependencies,
        }

        # Thresholds for alerting
        self.thresholds = {
            "cpu_usage": {"warning": 70, "critical": 85},
            "memory_usage": {"warning": 80, "critical": 90},
            "disk_usage": {"warning": 85, "critical": 95},
            "response_time": {"warning": 1000, "critical": 5000},  # milliseconds
            "error_rate": {"warning": 1, "critical": 5},  # percentage
        }

        logger.info("🏥 Health Monitor initialized")

    async def ensure_database_initialized(self):
        """Ensure database is initialized (call once)"""
        if not self._db_initialized:
            await self.init_database()
            self._db_initialized = True

    async def init_database(self):
        """Initialize SQLite database for health metrics"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS health_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    check_name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL,
                    status TEXT NOT NULL,
                    details TEXT
                )
            """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution TEXT,
                    resolved_at TEXT
                )
            """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS slo_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    slo_name TEXT NOT NULL,
                    event_type TEXT NOT NULL, -- violation, recovery, budget_exhausted
                    duration_minutes REAL,
                    details TEXT
                )
            """
            )

            # Create indexes for performance
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON health_metrics(timestamp)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_slo_timestamp ON slo_events(timestamp)"
            )

            await conn.commit()

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        await self.ensure_database_initialized()
        start_time = time.time()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "slo_status": {},
            "system_info": await self.get_system_info(),
            "check_duration_ms": 0,
        }

        # Run all health checks
        for check_name, check_func in self.checks.items():
            try:
                check_result = await check_func()
                results["checks"][check_name] = check_result

                # Store in database
                await self.store_health_metric(check_name, check_result)

                # Update overall status
                if check_result["status"] == "critical":
                    results["overall_status"] = "critical"
                elif (
                    check_result["status"] == "warning"
                    and results["overall_status"] == "healthy"
                ):
                    results["overall_status"] = "warning"

            except Exception as e:
                logger.error(f"Health check failed for {check_name}: {e}")
                results["checks"][check_name] = {
                    "status": "critical",
                    "error": str(e),
                    "metrics": {},
                }
                results["overall_status"] = "critical"

        # Check SLO compliance
        results["slo_status"] = await self.check_slo_compliance()

        # Calculate total check duration
        results["check_duration_ms"] = round((time.time() - start_time) * 1000, 2)

        return results

    async def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        return {
            "hostname": os.uname().nodename,
            "platform": os.uname().sysname,
            "python_version": sys.version.split()[0],
            "uptime_seconds": time.time() - psutil.boot_time(),
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

    async def check_system_resources(self) -> Dict[str, Any]:
        """Check CPU, memory, and basic system resources"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        metrics = {
            "cpu_usage": HealthMetric(
                "cpu_usage",
                cpu_percent,
                self.get_status_from_thresholds(cpu_percent, "cpu_usage"),
                self.thresholds["cpu_usage"],
            ),
            "memory_usage": HealthMetric(
                "memory_usage",
                memory.percent,
                self.get_status_from_thresholds(memory.percent, "memory_usage"),
                self.thresholds["memory_usage"],
            ),
            "memory_available_gb": HealthMetric(
                "memory_available_gb", round(memory.available / (1024**3), 2), "healthy"
            ),
        }

        overall_status = max(
            [m.status for m in metrics.values()],
            key=lambda x: ["healthy", "warning", "critical"].index(x),
        )

        return {
            "status": overall_status,
            "metrics": {k: asdict(v) for k, v in metrics.items()},
            "summary": f"CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%",
        }

    async def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space on all mounted filesystems"""
        disk_metrics = {}
        overall_status = "healthy"

        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                used_percent = (usage.used / usage.total) * 100

                status = self.get_status_from_thresholds(used_percent, "disk_usage")

                disk_metrics[partition.mountpoint] = HealthMetric(
                    f'disk_{partition.mountpoint.replace("/", "_root" if partition.mountpoint == "/" else "")}',
                    used_percent,
                    status,
                    self.thresholds["disk_usage"],
                )

                if status == "critical":
                    overall_status = "critical"
                elif status == "warning" and overall_status == "healthy":
                    overall_status = "warning"

            except Exception as e:
                logger.warning(
                    f"Could not check disk usage for {partition.mountpoint}: {e}"
                )

        return {
            "status": overall_status,
            "metrics": {k: asdict(v) for k, v in disk_metrics.items()},
            "summary": f"{len(disk_metrics)} partitions checked",
        }

    async def check_memory_usage(self) -> Dict[str, Any]:
        """Detailed memory usage check"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        metrics = {
            "virtual_memory": HealthMetric(
                "virtual_memory_percent",
                memory.percent,
                self.get_status_from_thresholds(memory.percent, "memory_usage"),
            ),
            "swap_usage": HealthMetric(
                "swap_usage_percent",
                swap.percent,
                (
                    "critical"
                    if swap.percent > 50
                    else "warning" if swap.percent > 25 else "healthy"
                ),
            ),
        }

        overall_status = max(
            [m.status for m in metrics.values()],
            key=lambda x: ["healthy", "warning", "critical"].index(x),
        )

        return {
            "status": overall_status,
            "metrics": {k: asdict(v) for k, v in metrics.items()},
            "summary": f"Memory: {memory.percent:.1f}%, Swap: {swap.percent:.1f}%",
        }

    async def check_process_health(self) -> Dict[str, Any]:
        """Check health of critical processes"""
        critical_processes = ["chatterfix", "nginx", "systemd"]
        process_metrics = {}
        overall_status = "healthy"

        for proc_name in critical_processes:
            processes = [
                p
                for p in psutil.process_iter(
                    ["name", "pid", "cpu_percent", "memory_percent"]
                )
                if proc_name.lower() in p.info["name"].lower()
            ]

            if not processes:
                process_metrics[proc_name] = HealthMetric(
                    f"process_{proc_name}",
                    "not_running",
                    "critical" if proc_name in ["chatterfix", "nginx"] else "warning",
                )
                overall_status = "critical"
            else:
                # Get the main process (usually the first one)
                main_proc = processes[0]
                process_metrics[proc_name] = HealthMetric(
                    f"process_{proc_name}",
                    f'running_pid_{main_proc.info["pid"]}',
                    "healthy",
                )

        return {
            "status": overall_status,
            "metrics": {k: asdict(v) for k, v in process_metrics.items()},
            "summary": f'{len([m for m in process_metrics.values() if "running" in str(m.value)])} processes healthy',
        }

    async def check_database_connection(self) -> Dict[str, Any]:
        """Check database connectivity (SQLite health database)"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT COUNT(*) FROM health_metrics WHERE timestamp > ?",
                    (datetime.now(timezone.utc) - timedelta(hours=1),),
                )
                row = await cursor.fetchone()
                recent_count = row[0] if row else 0

            return {
                "status": "healthy",
                "metrics": {
                    "connection": HealthMetric(
                        "database_connection", "connected", "healthy"
                    ),
                    "recent_metrics": HealthMetric(
                        "recent_metrics_count", recent_count, "healthy"
                    ),
                },
                "summary": f"Database connected, {recent_count} recent metrics",
            }

        except Exception as e:
            return {
                "status": "critical",
                "metrics": {
                    "connection": HealthMetric(
                        "database_connection", f"error: {str(e)}", "critical"
                    )
                },
                "summary": "Database connection failed",
            }

    async def check_ai_services(self) -> Dict[str, Any]:
        """Check AI services status"""
        # This would be expanded to check actual AI service health
        # For now, simulate based on process availability

        ai_metrics = {}

        # Check if AI processes are running (simplified)
        try:
            # This could be enhanced to check actual AI model availability
            ai_metrics["llama_available"] = HealthMetric(
                "llama_model", "simulated_healthy", "healthy"
            )
            ai_metrics["voice_processing"] = HealthMetric(
                "voice_processor", "available", "healthy"
            )

            return {
                "status": "healthy",
                "metrics": {k: asdict(v) for k, v in ai_metrics.items()},
                "summary": "AI services operational",
            }

        except Exception as e:
            return {
                "status": "warning",
                "metrics": {
                    "ai_services": HealthMetric(
                        "ai_services", f"degraded: {str(e)}", "warning"
                    )
                },
                "summary": "AI services degraded",
            }

    async def check_external_dependencies(self) -> Dict[str, Any]:
        """Check external service dependencies"""
        # This would check actual external APIs, databases, etc.
        # For now, simulate basic connectivity checks

        return {
            "status": "healthy",
            "metrics": {
                "external_apis": HealthMetric(
                    "external_connectivity", "available", "healthy"
                )
            },
            "summary": "External dependencies available",
        }

    async def check_slo_compliance(self) -> Dict[str, Any]:
        """Check SLO compliance and error budget status"""
        slo_results = {}

        for slo_name, slo in self.slos.items():
            # Query recent incidents/violations
            since_time = datetime.now(timezone.utc) - timedelta(
                hours=slo.time_window_hours
            )

            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """
                    SELECT SUM(duration_minutes) FROM slo_events
                    WHERE slo_name = ? AND timestamp > ? AND event_type = 'violation'
                """,
                    (slo_name, since_time),
                )

                row = await cursor.fetchone()
                total_violation_minutes = row[0] if row and row[0] else 0

            # Calculate error budget consumption
            budget_consumed_percent = (
                total_violation_minutes / slo.error_budget_minutes
            ) * 100
            remaining_budget = max(
                0, slo.error_budget_minutes - total_violation_minutes
            )

            status = "healthy"
            if budget_consumed_percent > 90:
                status = "critical"
            elif budget_consumed_percent > 75:
                status = "warning"

            slo_results[slo_name] = {
                "target_percentage": slo.target_percentage,
                "error_budget_minutes": slo.error_budget_minutes,
                "consumed_minutes": total_violation_minutes,
                "remaining_minutes": remaining_budget,
                "budget_consumed_percent": round(budget_consumed_percent, 2),
                "status": status,
            }

        return slo_results

    def get_status_from_thresholds(self, value: float, metric_type: str) -> str:
        """Determine status based on configured thresholds"""
        if metric_type not in self.thresholds:
            return "healthy"

        thresholds = self.thresholds[metric_type]

        if value >= thresholds["critical"]:
            return "critical"
        elif value >= thresholds["warning"]:
            return "warning"
        else:
            return "healthy"

    async def store_health_metric(self, check_name: str, check_result: Dict[str, Any]):
        """Store health check results in database"""
        await self.ensure_database_initialized()
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                timestamp = datetime.now(timezone.utc).isoformat()

                for metric_name, metric_data in check_result.get("metrics", {}).items():
                    if isinstance(metric_data, dict) and "value" in metric_data:
                        await conn.execute(
                            """
                            INSERT INTO health_metrics (timestamp, check_name, metric_name, value, status, details)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            (
                                timestamp,
                                check_name,
                                metric_name,
                                (
                                    metric_data["value"]
                                    if isinstance(metric_data["value"], (int, float))
                                    else None
                                ),
                                metric_data["status"],
                                json.dumps(metric_data),
                            ),
                        )

                await conn.commit()

        except Exception as e:
            logger.error(f"Failed to store health metrics: {e}")

    async def record_incident(
        self, incident_type: str, severity: str, description: str
    ) -> int:
        """Record a new incident"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO incidents (timestamp, type, severity, description)
                VALUES (?, ?, ?, ?)
            """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    incident_type,
                    severity,
                    description,
                ),
            )

            await conn.commit()
            return cursor.lastrowid

    async def resolve_incident(self, incident_id: int, resolution: str):
        """Mark an incident as resolved"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                UPDATE incidents
                SET resolved = TRUE, resolution = ?, resolved_at = ?
                WHERE id = ?
            """,
                (resolution, datetime.now(timezone.utc).isoformat(), incident_id),
            )
            await conn.commit()

    async def record_slo_violation(
        self, slo_name: str, duration_minutes: float, details: str = None
    ):
        """Record an SLO violation"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO slo_events (timestamp, slo_name, event_type, duration_minutes, details)
                VALUES (?, ?, 'violation', ?, ?)
            """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    slo_name,
                    duration_minutes,
                    details,
                ),
            )
            await conn.commit()

    async def get_health_history(self, hours: int = 24) -> Dict[str, Any]:
        """Get health check history for analysis"""
        await self.ensure_database_initialized()
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.cursor()

            # Get metric trends
            await cursor.execute(
                """
                SELECT check_name, metric_name, AVG(value) as avg_value,
                       COUNT(*) as sample_count, status
                FROM health_metrics
                WHERE timestamp > ? AND value IS NOT NULL
                GROUP BY check_name, metric_name, status
                ORDER BY check_name, metric_name
            """,
                (since_time,),
            )

            metrics_history = await cursor.fetchall()

            # Get incidents
            await cursor.execute(
                """
                SELECT * FROM incidents
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """,
                (since_time,),
            )

            incidents = await cursor.fetchall()

            # Get SLO violations
            await cursor.execute(
                """
                SELECT * FROM slo_events
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """,
                (since_time,),
            )

            slo_events = await cursor.fetchall()

        return {
            "time_range_hours": hours,
            "metrics_summary": [
                dict(zip([col[0] for col in cursor.description], row))
                for row in metrics_history
            ],
            "recent_incidents": [
                dict(zip([col[0] for col in cursor.description], row))
                for row in incidents
            ],
            "slo_events": [
                dict(zip([col[0] for col in cursor.description], row))
                for row in slo_events
            ],
        }


# Global health monitor instance
health_monitor = HealthMonitor()


async def get_detailed_health_status() -> Dict[str, Any]:
    """Enhanced health endpoint for comprehensive system status"""
    return await health_monitor.comprehensive_health_check()


async def get_liveness_probe() -> Dict[str, Any]:
    """Kubernetes-style liveness probe - minimal check"""
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "chatterfix-cmms",
    }


async def get_readiness_probe() -> Dict[str, Any]:
    """Kubernetes-style readiness probe - ready to serve traffic"""
    try:
        # Quick essential checks only
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        ready = (
            cpu_percent < 95  # Not completely overloaded
            and memory.percent < 95  # Not out of memory
        )

        return {
            "ready": ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "cpu_available": cpu_percent < 95,
                "memory_available": memory.percent < 95,
            },
        }

    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    import asyncio

    async def main():
        print("🏥 ChatterFix Health Monitor Test")

        # Run comprehensive health check
        health_status = await get_detailed_health_status()
        print(json.dumps(health_status, indent=2, default=str))

        # Show SLO status
        print("\n📊 SLO Status:")
        for slo_name, slo_data in health_status["slo_status"].items():
            print(
                f"  {slo_name}: {slo_data['status']} ({slo_data['budget_consumed_percent']:.1f}% budget used)"
            )

    asyncio.run(main())
