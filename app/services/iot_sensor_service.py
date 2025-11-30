"""
IoT Sensor Integration Service for ChatterFix CMMS
Handles sensor data collection, threshold monitoring, and automated work order creation
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.core.database import get_db_connection

logger = logging.getLogger(__name__)


class IoTSensorService:
    """Service for IoT sensor data management and analysis"""

    def __init__(self):
        self.sensor_thresholds = {
            "temperature": {"warning": 85, "critical": 100, "unit": "°F"},
            "vibration": {"warning": 1.0, "critical": 2.0, "unit": "mm/s"},
            "pressure": {"warning": 150, "critical": 200, "unit": "psi"},
            "humidity": {"warning": 70, "critical": 85, "unit": "%"},
            "rpm": {"warning": 3500, "critical": 4000, "unit": "RPM"},
            "current": {"warning": 15, "critical": 20, "unit": "A"},
            "noise_level": {"warning": 85, "critical": 100, "unit": "dB"},
        }
        self.active_alerts = {}

    def record_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record sensor data from IoT device
        Expected data format:
        {
            "sensor_id": "SENSOR-001",
            "asset_id": 1,
            "sensor_type": "temperature",
            "value": 75.5,
            "unit": "°F",
            "timestamp": "2025-01-01T12:00:00Z"
        }
        """
        conn = get_db_connection()
        try:
            # Ensure sensor_readings table exists
            self._ensure_sensor_table(conn)

            # Insert sensor reading
            cursor = conn.execute(
                """
                INSERT INTO sensor_readings
                (sensor_id, asset_id, sensor_type, value, unit, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    data.get("sensor_id"),
                    data.get("asset_id"),
                    data.get("sensor_type"),
                    data.get("value"),
                    data.get("unit", ""),
                    data.get("timestamp", datetime.now().isoformat()),
                ),
            )
            conn.commit()

            reading_id = cursor.lastrowid

            # Check thresholds and create alerts if needed
            alert = self._check_threshold(data)

            # Update asset metrics
            self._update_asset_metrics(conn, data)

            result = {
                "success": True,
                "reading_id": reading_id,
                "sensor_id": data.get("sensor_id"),
                "value": data.get("value"),
                "timestamp": datetime.now().isoformat(),
            }

            if alert:
                result["alert"] = alert
                # Trigger automated work order if critical
                if alert.get("severity") == "critical":
                    work_order = self._create_automated_work_order(conn, data, alert)
                    result["work_order_created"] = work_order

            return result

        except Exception as e:
            logger.error(f"Error recording sensor data: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def record_batch_sensor_data(
        self, readings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Record multiple sensor readings in batch"""
        results = {
            "success": True,
            "total": len(readings),
            "recorded": 0,
            "alerts": [],
            "work_orders_created": [],
        }

        for reading in readings:
            result = self.record_sensor_data(reading)
            if result.get("success"):
                results["recorded"] += 1
                if result.get("alert"):
                    results["alerts"].append(result["alert"])
                if result.get("work_order_created"):
                    results["work_orders_created"].append(result["work_order_created"])

        return results

    def get_sensor_readings(
        self, asset_id: int = None, sensor_type: str = None, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get sensor readings with optional filters"""
        conn = get_db_connection()
        try:
            self._ensure_sensor_table(conn)

            query = """
                SELECT sr.*, a.name as asset_name
                FROM sensor_readings sr
                LEFT JOIN assets a ON sr.asset_id = a.id
                WHERE sr.recorded_at >= datetime('now', ?)
            """
            params = [f"-{hours} hours"]

            if asset_id:
                query += " AND sr.asset_id = ?"
                params.append(asset_id)

            if sensor_type:
                query += " AND sr.sensor_type = ?"
                params.append(sensor_type)

            query += " ORDER BY sr.recorded_at DESC LIMIT 1000"

            readings = conn.execute(query, params).fetchall()
            return [dict(r) for r in readings]

        finally:
            conn.close()

    def get_asset_sensor_summary(self, asset_id: int) -> Dict[str, Any]:
        """Get summary of sensor data for an asset"""
        conn = get_db_connection()
        try:
            self._ensure_sensor_table(conn)

            # Get latest readings by sensor type
            latest = conn.execute(
                """
                SELECT sensor_type, value, unit, recorded_at, sensor_id
                FROM sensor_readings
                WHERE asset_id = ?
                AND recorded_at = (
                    SELECT MAX(recorded_at)
                    FROM sensor_readings sr2
                    WHERE sr2.asset_id = sensor_readings.asset_id
                    AND sr2.sensor_type = sensor_readings.sensor_type
                )
            """,
                (asset_id,),
            ).fetchall()

            # Get averages for last 24 hours
            averages = conn.execute(
                """
                SELECT
                    sensor_type,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(*) as reading_count
                FROM sensor_readings
                WHERE asset_id = ?
                AND recorded_at >= datetime('now', '-24 hours')
                GROUP BY sensor_type
            """,
                (asset_id,),
            ).fetchall()

            # Check current status for each sensor type
            sensors = {}
            for reading in latest:
                sensor_type = reading["sensor_type"]
                value = reading["value"]
                status = self._get_value_status(sensor_type, value)

                avg_data = next(
                    (a for a in averages if a["sensor_type"] == sensor_type), None
                )

                sensors[sensor_type] = {
                    "current_value": value,
                    "unit": reading["unit"],
                    "last_updated": reading["recorded_at"],
                    "sensor_id": reading["sensor_id"],
                    "status": status,
                    "average_24h": (
                        round(avg_data["avg_value"], 2) if avg_data else None
                    ),
                    "min_24h": round(avg_data["min_value"], 2) if avg_data else None,
                    "max_24h": round(avg_data["max_value"], 2) if avg_data else None,
                    "reading_count_24h": avg_data["reading_count"] if avg_data else 0,
                    "thresholds": self.sensor_thresholds.get(sensor_type, {}),
                }

            return {
                "asset_id": asset_id,
                "sensors": sensors,
                "generated_at": datetime.now().isoformat(),
            }

        finally:
            conn.close()

    def get_sensor_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent sensor alerts"""
        conn = get_db_connection()
        try:
            self._ensure_sensor_table(conn)

            alerts = conn.execute(
                """
                SELECT sa.*, a.name as asset_name
                FROM sensor_alerts sa
                LEFT JOIN assets a ON sa.asset_id = a.id
                WHERE sa.created_at >= datetime('now', ?)
                ORDER BY sa.created_at DESC
            """,
                (f"-{hours} hours",),
            ).fetchall()

            return [dict(a) for a in alerts]

        finally:
            conn.close()

    def update_thresholds(
        self, sensor_type: str, thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """Update thresholds for a sensor type"""
        if sensor_type not in self.sensor_thresholds:
            self.sensor_thresholds[sensor_type] = {}

        self.sensor_thresholds[sensor_type].update(thresholds)

        return {
            "success": True,
            "sensor_type": sensor_type,
            "thresholds": self.sensor_thresholds[sensor_type],
        }

    def get_predictive_insights(self, asset_id: int) -> Dict[str, Any]:
        """
        Get AI-powered predictive insights based on sensor data trends
        """
        conn = get_db_connection()
        try:
            self._ensure_sensor_table(conn)

            # Get sensor history for the asset (last 7 days)
            history = conn.execute(
                """
                SELECT
                    sensor_type,
                    value,
                    recorded_at
                FROM sensor_readings
                WHERE asset_id = ?
                AND recorded_at >= datetime('now', '-7 days')
                ORDER BY sensor_type, recorded_at
            """,
                (asset_id,),
            ).fetchall()

            if not history:
                return {
                    "asset_id": asset_id,
                    "insights": [],
                    "risk_score": 0,
                    "message": "Insufficient sensor data for analysis",
                }

            # Group by sensor type and analyze trends
            sensor_data = {}
            for reading in history:
                sensor_type = reading["sensor_type"]
                if sensor_type not in sensor_data:
                    sensor_data[sensor_type] = []
                sensor_data[sensor_type].append(
                    {"value": reading["value"], "timestamp": reading["recorded_at"]}
                )

            insights = []
            total_risk = 0

            for sensor_type, readings in sensor_data.items():
                if len(readings) >= 5:
                    analysis = self._analyze_sensor_trend(sensor_type, readings)
                    if analysis:
                        insights.append(analysis)
                        total_risk += analysis.get("risk_contribution", 0)

            # Calculate overall risk score (0-100)
            risk_score = min(100, total_risk)

            # Determine recommended actions
            recommendations = self._generate_recommendations(insights, risk_score)

            return {
                "asset_id": asset_id,
                "insights": insights,
                "risk_score": round(risk_score, 2),
                "risk_level": self._get_risk_level(risk_score),
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
            }

        finally:
            conn.close()

    def _analyze_sensor_trend(
        self, sensor_type: str, readings: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Analyze trend for a specific sensor type"""
        values = [r["value"] for r in readings]

        if len(values) < 5:
            return None

        # Calculate basic statistics
        avg_value = sum(values) / len(values)
        recent_avg = sum(values[-10:]) / min(10, len(values))
        older_avg = sum(values[:10]) / min(10, len(values))

        # Calculate trend direction
        trend = "stable"
        change_percent = 0

        if older_avg > 0:
            change_percent = ((recent_avg - older_avg) / older_avg) * 100
            if change_percent > 10:
                trend = "increasing"
            elif change_percent < -10:
                trend = "decreasing"

        # Get threshold info
        thresholds = self.sensor_thresholds.get(sensor_type, {})
        warning_threshold = thresholds.get("warning", float("inf"))
        critical_threshold = thresholds.get("critical", float("inf"))

        # Calculate risk contribution
        risk_contribution = 0
        current_value = values[-1]

        if current_value >= critical_threshold:
            risk_contribution = 40
        elif current_value >= warning_threshold:
            risk_contribution = 20
        elif trend == "increasing" and current_value >= warning_threshold * 0.8:
            risk_contribution = 15

        # Add trend risk
        if trend == "increasing" and change_percent > 20:
            risk_contribution += 10

        # Predict days to threshold
        days_to_warning = None
        if trend == "increasing" and change_percent > 0:
            daily_change = (recent_avg - older_avg) / 7  # Assuming 7 days of data
            if daily_change > 0:
                remaining = warning_threshold - current_value
                days_to_warning = max(0, int(remaining / daily_change))

        return {
            "sensor_type": sensor_type,
            "current_value": round(current_value, 2),
            "average_value": round(avg_value, 2),
            "trend": trend,
            "change_percent": round(change_percent, 2),
            "status": self._get_value_status(sensor_type, current_value),
            "risk_contribution": risk_contribution,
            "days_to_warning_threshold": days_to_warning,
            "thresholds": thresholds,
            "unit": thresholds.get("unit", ""),
        }

    def _generate_recommendations(
        self, insights: List[Dict], risk_score: float
    ) -> List[str]:
        """Generate maintenance recommendations based on sensor insights"""
        recommendations = []

        if risk_score >= 70:
            recommendations.append(
                "🚨 URGENT: Schedule immediate inspection - high risk of failure detected"
            )
        elif risk_score >= 50:
            recommendations.append("⚠️ Schedule maintenance within 1-2 days")
        elif risk_score >= 30:
            recommendations.append("📋 Plan preventive maintenance within 1 week")

        for insight in insights:
            sensor_type = insight.get("sensor_type", "")
            status = insight.get("status", "")
            trend = insight.get("trend", "")
            days_to_warning = insight.get("days_to_warning_threshold")

            if status == "critical":
                recommendations.append(
                    f"🔴 {sensor_type.title()}: Critical level - immediate action required"
                )
            elif status == "warning":
                recommendations.append(
                    f"🟡 {sensor_type.title()}: Warning level - monitor closely"
                )
            elif (
                trend == "increasing"
                and days_to_warning is not None
                and days_to_warning <= 7
            ):
                recommendations.append(
                    f"📈 {sensor_type.title()}: Rising trend - expected to reach warning in ~{days_to_warning} days"
                )

        if not recommendations:
            recommendations.append("✅ All sensors within normal parameters")

        return recommendations

    def _check_threshold(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if sensor value exceeds thresholds"""
        sensor_type = data.get("sensor_type")
        value = data.get("value")

        if sensor_type not in self.sensor_thresholds:
            return None

        thresholds = self.sensor_thresholds[sensor_type]

        if value >= thresholds.get("critical", float("inf")):
            return self._create_alert(data, "critical", thresholds)
        elif value >= thresholds.get("warning", float("inf")):
            return self._create_alert(data, "warning", thresholds)

        return None

    def _create_alert(
        self, data: Dict[str, Any], severity: str, thresholds: Dict
    ) -> Dict[str, Any]:
        """Create and record a sensor alert"""
        conn = get_db_connection()
        try:
            self._ensure_sensor_table(conn)

            alert = {
                "sensor_id": data.get("sensor_id"),
                "asset_id": data.get("asset_id"),
                "sensor_type": data.get("sensor_type"),
                "value": data.get("value"),
                "threshold": thresholds.get(severity),
                "severity": severity,
                "message": f"{data.get('sensor_type').title()} reading of {data.get('value')} exceeds {severity} threshold of {thresholds.get(severity)}",
                "created_at": datetime.now().isoformat(),
            }

            conn.execute(
                """
                INSERT INTO sensor_alerts
                (sensor_id, asset_id, sensor_type, value, threshold_value, severity, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert["sensor_id"],
                    alert["asset_id"],
                    alert["sensor_type"],
                    alert["value"],
                    alert["threshold"],
                    alert["severity"],
                    alert["message"],
                ),
            )
            conn.commit()

            logger.warning(f"Sensor alert: {alert['message']}")
            return alert

        finally:
            conn.close()

    def _create_automated_work_order(
        self, conn, data: Dict[str, Any], alert: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create automated work order based on critical sensor alert"""
        # Validate input data
        asset_id = data.get("asset_id")
        if not asset_id:
            logger.error("Cannot create automated work order: missing asset_id")
            return None

        severity = alert.get("severity", "").lower()
        if severity not in ["warning", "critical"]:
            logger.error(f"Invalid alert severity: {severity}")
            return None

        try:
            # Get asset name and validate asset exists
            asset = conn.execute(
                "SELECT id, name FROM assets WHERE id = ?", (asset_id,)
            ).fetchone()

            if not asset:
                logger.error(
                    f"Asset {asset_id} not found - cannot create automated work order"
                )
                return None

            asset_name = asset["name"]

            work_order = {
                "title": f"[AUTO] {alert.get('severity').upper()}: {data.get('sensor_type').title()} Alert - {asset_name}",
                "description": f"""Automated work order created due to sensor alert.

Alert Details:
- Sensor Type: {data.get('sensor_type')}
- Current Value: {data.get('value')} {data.get('unit', '')}
- Threshold: {alert.get('threshold')} {data.get('unit', '')}
- Severity: {alert.get('severity').upper()}
- Sensor ID: {data.get('sensor_id')}

Recommended Action: Inspect equipment immediately and address the {data.get('sensor_type')} issue.

This work order was automatically generated by the IoT monitoring system.""",
                "priority": "High" if alert.get("severity") == "critical" else "Medium",
                "asset_id": data.get("asset_id"),
                "status": "Open",
            }

            cursor = conn.execute(
                """
                INSERT INTO work_orders (title, description, priority, asset_id, status)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    work_order["title"],
                    work_order["description"],
                    work_order["priority"],
                    work_order["asset_id"],
                    work_order["status"],
                ),
            )
            conn.commit()

            work_order["id"] = cursor.lastrowid

            logger.info(
                f"Automated work order created: #{work_order['id']} - {work_order['title']}"
            )

            return work_order

        except Exception as e:
            logger.error(f"Error creating automated work order: {e}")
            return None

    def _update_asset_metrics(self, conn, data: Dict[str, Any]):
        """Update asset_metrics table with sensor reading"""
        try:
            conn.execute(
                """
                INSERT INTO asset_metrics (asset_id, metric_type, value, unit)
                VALUES (?, ?, ?, ?)
            """,
                (
                    data.get("asset_id"),
                    data.get("sensor_type"),
                    data.get("value"),
                    data.get("unit", ""),
                ),
            )
            conn.commit()
        except Exception as e:
            logger.debug(f"Could not update asset metrics: {e}")

    def _get_value_status(self, sensor_type: str, value: float) -> str:
        """Get status label based on sensor value"""
        if sensor_type not in self.sensor_thresholds:
            return "unknown"

        thresholds = self.sensor_thresholds[sensor_type]

        if value >= thresholds.get("critical", float("inf")):
            return "critical"
        elif value >= thresholds.get("warning", float("inf")):
            return "warning"
        return "normal"

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level label"""
        if risk_score >= 70:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 30:
            return "medium"
        return "low"

    def _ensure_sensor_table(self, conn):
        """Ensure sensor-related tables exist"""
        # Sensor readings table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                asset_id INTEGER,
                sensor_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            )
        """
        )

        # Sensor alerts table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                asset_id INTEGER,
                sensor_type TEXT NOT NULL,
                value REAL NOT NULL,
                threshold_value REAL,
                severity TEXT NOT NULL,
                message TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                work_order_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(asset_id) REFERENCES assets(id),
                FOREIGN KEY(work_order_id) REFERENCES work_orders(id)
            )
        """
        )

        # Create index for performance
        try:
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sensor_readings_asset
                ON sensor_readings(asset_id, sensor_type, recorded_at)
            """
            )
        except:
            pass

        conn.commit()


# Global IoT sensor service instance
iot_sensor_service = IoTSensorService()
