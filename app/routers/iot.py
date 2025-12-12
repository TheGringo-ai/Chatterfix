"""
IoT Router for ChatterFix CMMS
Provides API endpoints for IoT sensor data collection and monitoring
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.iot_sensor_service import iot_sensor_service

router = APIRouter(prefix="/iot", tags=["iot"])


# Pydantic models for request validation


class SensorReading(BaseModel):
    sensor_id: str
    asset_id: int
    sensor_type: (
        str  # temperature, vibration, pressure, humidity, rpm, current, noise_level
    )
    value: float
    unit: Optional[str] = None
    timestamp: Optional[str] = None


class BatchSensorReadings(BaseModel):
    readings: List[SensorReading]


class ThresholdUpdate(BaseModel):
    warning: Optional[float] = None
    critical: Optional[float] = None
    unit: Optional[str] = None


# Sensor Data Collection Endpoints


@router.post("/sensors/data")
async def record_sensor_reading(reading: SensorReading):
    """
    Record a single sensor reading from an IoT device

    This endpoint accepts sensor data and:
    - Stores the reading in the database
    - Checks against configured thresholds
    - Creates alerts if thresholds are exceeded
    - Automatically creates work orders for critical alerts
    """
    try:
        result = iot_sensor_service.record_sensor_data(reading.model_dump())
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sensors/data/batch")
async def record_batch_readings(batch: BatchSensorReadings):
    """
    Record multiple sensor readings in batch

    Optimized for IoT gateways that aggregate data from multiple sensors
    """
    try:
        readings = [r.model_dump() for r in batch.readings]
        result = iot_sensor_service.record_batch_sensor_data(readings)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sensor Data Retrieval Endpoints


@router.get("/sensors/readings")
async def get_sensor_readings(
    asset_id: Optional[int] = None,
    sensor_type: Optional[str] = None,
    hours: int = Query(24, ge=1, le=720),
):
    """
    Get sensor readings with optional filters

    Parameters:
    - asset_id: Filter by specific asset
    - sensor_type: Filter by sensor type (temperature, vibration, etc.)
    - hours: Time range in hours (default: 24, max: 720/30 days)
    """
    try:
        readings = iot_sensor_service.get_sensor_readings(asset_id, sensor_type, hours)
        return JSONResponse(content={"count": len(readings), "readings": readings})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensors/asset/{asset_id}/summary")
async def get_asset_sensor_summary(asset_id: int):
    """
    Get comprehensive sensor summary for a specific asset

    Returns current readings, 24h averages, and status for all sensors
    """
    try:
        summary = iot_sensor_service.get_asset_sensor_summary(asset_id)
        return JSONResponse(content=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensors/asset/{asset_id}/insights")
async def get_predictive_insights(asset_id: int):
    """
    Get AI-powered predictive insights based on sensor data

    Analyzes sensor trends and provides:
    - Risk score (0-100)
    - Trend analysis for each sensor type
    - Maintenance recommendations
    """
    try:
        insights = iot_sensor_service.get_predictive_insights(asset_id)
        return JSONResponse(content=insights)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Alert Management Endpoints


@router.get("/sensors/alerts")
async def get_sensor_alerts(hours: int = Query(24, ge=1, le=720)):
    """
    Get recent sensor alerts

    Returns alerts triggered when sensor values exceed thresholds
    """
    try:
        alerts = iot_sensor_service.get_sensor_alerts(hours)
        return JSONResponse(content={"count": len(alerts), "alerts": alerts})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Threshold Configuration Endpoints


@router.get("/sensors/thresholds")
async def get_all_thresholds():
    """
    Get all configured sensor thresholds
    """
    return JSONResponse(content={"thresholds": iot_sensor_service.sensor_thresholds})


@router.get("/sensors/thresholds/{sensor_type}")
async def get_sensor_thresholds(sensor_type: str):
    """
    Get thresholds for a specific sensor type
    """
    if sensor_type not in iot_sensor_service.sensor_thresholds:
        raise HTTPException(
            status_code=404,
            detail=f"No thresholds configured for sensor type: {sensor_type}",
        )

    return JSONResponse(
        content={
            "sensor_type": sensor_type,
            "thresholds": iot_sensor_service.sensor_thresholds[sensor_type],
        }
    )


@router.put("/sensors/thresholds/{sensor_type}")
async def update_sensor_thresholds(sensor_type: str, thresholds: ThresholdUpdate):
    """
    Update thresholds for a sensor type

    Example:
    ```json
    {
        "warning": 85,
        "critical": 100,
        "unit": "°F"
    }
    ```
    """
    try:
        threshold_data = {
            k: v for k, v in thresholds.model_dump().items() if v is not None
        }
        result = iot_sensor_service.update_thresholds(sensor_type, threshold_data)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sensor Types and Documentation


@router.get("/sensors/types")
async def get_supported_sensor_types():
    """
    Get list of supported sensor types with their default thresholds
    """
    return JSONResponse(
        content={
            "sensor_types": list(iot_sensor_service.sensor_thresholds.keys()),
            "default_thresholds": iot_sensor_service.sensor_thresholds,
        }
    )


# Health Check for IoT Integration


@router.get("/health")
async def iot_health_check():
    """
    Health check endpoint for IoT integration
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "iot_sensor_service",
            "supported_sensor_types": len(iot_sensor_service.sensor_thresholds),
            "active_alerts": len(iot_sensor_service.active_alerts),
        }
    )


# WebSocket endpoint placeholder for real-time sensor data
# Note: Full WebSocket implementation would require additional setup


@router.get("/sensors/stream/info")
async def sensor_stream_info():
    """
    Information about real-time sensor data streaming

    For real-time sensor data, connect to the WebSocket endpoint at:
    ws://[host]/iot/sensors/stream
    """
    return JSONResponse(
        content={
            "websocket_endpoint": "/iot/sensors/stream",
            "protocol": "WebSocket",
            "message_format": {
                "subscribe": {
                    "type": "subscribe",
                    "asset_ids": [1, 2, 3],
                    "sensor_types": ["temperature", "vibration"],
                },
                "data_message": {
                    "type": "sensor_data",
                    "sensor_id": "SENSOR-001",
                    "asset_id": 1,
                    "sensor_type": "temperature",
                    "value": 75.5,
                    "unit": "°F",
                    "timestamp": "2025-01-01T12:00:00Z",
                },
            },
            "note": "Real-time streaming requires WebSocket connection",
        }
    )
