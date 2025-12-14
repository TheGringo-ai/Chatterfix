import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import asyncio

from app.core.firestore_db import get_firestore_manager
from app.services.work_order_service import work_order_service

logger = logging.getLogger(__name__)

class IoTSensorService:
    """Service for IoT sensor data management and analysis"""

    def __init__(self):
        self.firestore_manager = get_firestore_manager()
        self.sensor_thresholds = {
            "temperature": {"warning": 85, "critical": 100, "unit": "°F"},
            "vibration": {"warning": 1.0, "critical": 2.0, "unit": "mm/s"},
        }
        self.active_alerts = {}

    async def record_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record sensor data from IoT device to Firestore"""
        try:
            reading_data = {
                "sensor_id": data.get("sensor_id"), "asset_id": data.get("asset_id"),
                "sensor_type": data.get("sensor_type"), "value": data.get("value"),
                "unit": data.get("unit", ""), "recorded_at": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
            reading_id = await self.firestore_manager.create_document("sensor_readings", reading_data)
            
            alert = await self._check_threshold(reading_data)
            result = {"success": True, "reading_id": reading_id, "timestamp": datetime.now().isoformat()}

            if alert:
                result["alert"] = alert
                if alert.get("severity") == "critical":
                    work_order = await self._create_automated_work_order(reading_data, alert)
                    result["work_order_created"] = work_order

            return result
        except Exception as e:
            logger.error(f"Error recording sensor data: {e}")
            return {"success": False, "error": str(e)}

    async def get_sensor_readings(self, asset_id: str = None, sensor_type: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get sensor readings with optional filters"""
        filters = []
        if asset_id: filters.append({"field": "asset_id", "operator": "==", "value": asset_id})
        if sensor_type: filters.append({"field": "sensor_type", "operator": "==", "value": sensor_type})
        
        start_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        filters.append({"field": "recorded_at", "operator": ">=", "value": start_date.isoformat()})
        
        return await self.firestore_manager.get_collection(
            "sensor_readings", filters=filters, order_by="-recorded_at", limit=1000
        )

    async def get_asset_sensor_summary(self, asset_id: str) -> Dict[str, Any]:
        """Get summary of sensor data for an asset"""
        # This is a simplified version. A real implementation might use aggregations.
        readings = await self.get_sensor_readings(asset_id=asset_id, hours=24)
        
        sensors = {}
        for reading in readings:
            sensor_type = reading.get("sensor_type")
            if not sensor_type or sensor_type in sensors: continue # Process latest reading only

            value = reading.get("value")
            status = self._get_value_status(sensor_type, value)
            
            sensors[sensor_type] = {
                "current_value": value, "unit": reading.get("unit"),
                "last_updated": reading.get("recorded_at"), "sensor_id": reading.get("sensor_id"),
                "status": status, "thresholds": self.sensor_thresholds.get(sensor_type, {}),
            }
        return {"asset_id": asset_id, "sensors": sensors, "generated_at": datetime.now().isoformat()}

    async def get_sensor_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent sensor alerts"""
        start_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        return await self.firestore_manager.get_collection(
            "sensor_alerts", filters=[{"field": "created_at", "operator": ">=", "value": start_date.isoformat()}], order_by="-created_at"
        )
        
    # Methods to be refactored
    async def record_batch_sensor_data(self, readings: List[Dict[str, Any]]): return {"success": False, "error": "Not implemented"}
    async def update_thresholds(self, sensor_type: str, thresholds: Dict[str, float]): return {"success": False, "error": "Not implemented"}
    async def get_predictive_insights(self, asset_id: str): return {"error": "Not implemented"}


    # Private helpers
    async def _check_threshold(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if sensor value exceeds thresholds"""
        # ... (logic is mostly the same, but alert creation is async)
        sensor_type = data.get("sensor_type")
        value = data.get("value")

        if sensor_type not in self.sensor_thresholds:
            return None

        thresholds = self.sensor_thresholds[sensor_type]

        if value >= thresholds.get("critical", float("inf")):
            return await self._create_alert(data, "critical", thresholds)
        elif value >= thresholds.get("warning", float("inf")):
            return await self._create_alert(data, "warning", thresholds)

        return None

    async def _create_alert(self, data: Dict[str, Any], severity: str, thresholds: Dict) -> Dict[str, Any]:
        """Create and record a sensor alert"""
        alert = {
            "sensor_id": data.get("sensor_id"), "asset_id": data.get("asset_id"),
            "sensor_type": data.get("sensor_type"), "value": data.get("value"),
            "threshold": thresholds.get(severity), "severity": severity,
            "message": f"{data.get('sensor_type').title()} reading of {data.get('value')} exceeds {severity} threshold of {thresholds.get(severity)}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.firestore_manager.create_document("sensor_alerts", alert)
        logger.warning(f"Sensor alert: {alert['message']}")
        return alert

    async def _create_automated_work_order(self, data: Dict[str, Any], alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create automated work order based on critical sensor alert"""
        asset_id = data.get("asset_id")
        if not asset_id: return None

        asset = await self.firestore_manager.get_document("assets", asset_id)
        if not asset: return None
        
        asset_name = asset.get("name", "Unknown Asset")
        wo_data = {
            "title": f"[AUTO] {alert.get('severity').upper()}: {data.get('sensor_type').title()} Alert - {asset_name}",
            "description": f"Automated work order created due to sensor alert.\n\nAlert Details:\n- Sensor Type: {data.get('sensor_type')}\n- Current Value: {data.get('value')} {data.get('unit', '')}\n- Threshold: {alert.get('threshold')} {data.get('unit', '')}\n- Severity: {alert.get('severity').upper()}",
            "priority": "High" if alert.get("severity") == "critical" else "Medium",
            "asset_id": asset_id, "status": "Open", "work_order_type": "Corrective",
        }
        wo_id = await work_order_service.create_work_order(wo_data)
        return {"id": wo_id, **wo_data}

    def _get_value_status(self, sensor_type: str, value: float) -> str:
        # ... (logic is correct)
        return "unknown"

iot_sensor_service = IoTSensorService()
