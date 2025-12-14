"""
ChatterFix IoT Advanced Module - API Endpoints
Premium sensor integration and analytics endpoints
"""

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import IoT Advanced Module components
try:
    from app.modules.iot_advanced.licensing import (
        require_iot_license, 
        require_enterprise_license,
        get_license_status,
        validate_sensor_count
    )
    from app.modules.iot_advanced.sensor_manager import (
        sensor_manager,
        SensorConfig,
        SensorType,
        SensorProtocol
    )
    IOT_AVAILABLE = True
except ImportError:
    IOT_AVAILABLE = False

from app.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/iot", tags=["IoT Advanced Module"])

# Request/Response Models
class SensorConfigRequest(BaseModel):
    name: str
    sensor_type: str
    protocol: str
    connection_params: Dict[str, Any]
    data_mapping: Dict[str, Any]
    sampling_interval: int = 60
    alert_thresholds: Optional[Dict[str, float]] = None
    asset_id: Optional[str] = None
    location: Optional[str] = None

# Premium Feature Check Endpoint
@router.get("/license-status")
async def check_license_status(current_user: User = Depends(get_current_active_user)):
    """Check IoT Advanced Module license status"""
    if not IOT_AVAILABLE:
        return JSONResponse({
            "tier": "core",
            "iot_available": False,
            "message": "IoT Advanced Module not installed",
            "upgrade_url": "https://chatterfix.com/upgrade/iot-advanced"
        })
    
    customer_id = getattr(current_user, "customer_id", "demo_customer_1")
    license_info = await get_license_status(customer_id)
    return JSONResponse(license_info)

# Sensor Management Endpoints
@router.post("/sensors")
async def add_sensor(
    config: SensorConfigRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Add a new IoT sensor to monitoring system"""
    if not IOT_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "IoT Advanced Module Required",
            "message": "This feature requires ChatterFix IoT Advanced Module",
            "upgrade_info": {
                "tier_required": "iot_advanced",
                "pricing": "$199/month + $25/sensor",
                "contact_sales": "sales@chatterfix.com"
            }
        })
    
    customer_id = getattr(current_user, "customer_id", "demo_customer_1")
    
    try:
        # Convert request to sensor config
        sensor_config = SensorConfig(
            sensor_id=f"{config.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=config.name,
            sensor_type=SensorType(config.sensor_type),
            protocol=SensorProtocol(config.protocol),
            connection_params=config.connection_params,
            data_mapping=config.data_mapping,
            sampling_interval=config.sampling_interval,
            alert_thresholds=config.alert_thresholds,
            asset_id=config.asset_id,
            location=config.location
        )
        
        result = await sensor_manager.add_sensor(customer_id, sensor_config)
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Failed to add sensor: {str(e)}"
        })

@router.get("/sensors")
async def list_sensors(current_user: User = Depends(get_current_active_user)):
    """List all configured IoT sensors"""
    if not IOT_AVAILABLE:
        return JSONResponse({
            "error": "IoT Advanced Module Required",
            "sensors": [],
            "total_sensors": 0,
            "upgrade_required": True
        })
    
    customer_id = getattr(current_user, "customer_id", "demo_customer_1")
    
    # Apply IoT license check
    @require_iot_license
    async def _get_sensors():
        return await sensor_manager.get_sensor_status(customer_id)
    
    result = await _get_sensors()
    return JSONResponse(result)

@router.get("/dashboard/overview")
async def get_dashboard_overview(current_user: User = Depends(get_current_active_user)):
    """Get IoT dashboard overview with key metrics"""
    if not IOT_AVAILABLE:
        return JSONResponse({
            "overview": {
                "total_sensors": 0,
                "online_sensors": 0,
                "offline_sensors": 0,
                "active_alerts": 0,
                "upgrade_required": True
            },
            "message": "IoT Advanced Module required for sensor monitoring",
            "upgrade_url": "https://chatterfix.com/upgrade/iot-advanced"
        })
    
    customer_id = getattr(current_user, "customer_id", "demo_customer_1")
    
    @require_iot_license
    async def _get_overview():
        sensor_status = await sensor_manager.get_sensor_status(customer_id)
        
        total_sensors = sensor_status.get("total_sensors", 0)
        online_sensors = sensor_status.get("online_sensors", 0)
        
        alerts = []
        if "sensors" in sensor_status:
            for sensor in sensor_status["sensors"]:
                if sensor.get("alert_level") in ["warning", "critical"]:
                    alerts.append({
                        "sensor_id": sensor["sensor_id"],
                        "name": sensor["name"],
                        "level": sensor["alert_level"],
                        "value": sensor.get("last_reading")
                    })
        
        return {
            "overview": {
                "total_sensors": total_sensors,
                "online_sensors": online_sensors,
                "offline_sensors": total_sensors - online_sensors,
                "active_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a["level"] == "critical"]),
                "warning_alerts": len([a for a in alerts if a["level"] == "warning"])
            },
            "alerts": alerts[:10],
            "system_health": "good" if online_sensors == total_sensors else "warning" if online_sensors > 0 else "critical"
        }
    
    result = await _get_overview()
    return JSONResponse(result)

# Voice Integration with IoT
@router.post("/voice-sensor-query")
async def process_voice_sensor_query(
    voice_text: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """Process voice queries about sensor data"""
    if not IOT_AVAILABLE:
        return JSONResponse({
            "voice_query": voice_text,
            "voice_response": "IoT sensor monitoring requires ChatterFix IoT Advanced Module. Contact sales@chatterfix.com for upgrade information.",
            "iot_enhanced": False,
            "upgrade_required": True
        })
    
    customer_id = getattr(current_user, "customer_id", "demo_customer_1")
    voice_lower = voice_text.lower()
    
    @require_iot_license 
    async def _process_voice_query():
        # Parse sensor-related voice commands
        if "temperature" in voice_lower:
            sensor_status = await sensor_manager.get_sensor_status(customer_id)
            temp_sensors = [s for s in sensor_status.get("sensors", []) if s.get("type") == "temperature"]
            
            if temp_sensors:
                responses = []
                for sensor in temp_sensors[:3]:
                    if sensor.get("last_reading"):
                        responses.append(f"{sensor['name']}: {sensor['last_reading']} degrees")
                
                voice_response = f"Temperature readings: {', '.join(responses)}" if responses else "No recent temperature readings available"
            else:
                voice_response = "No temperature sensors configured"
        
        elif "pressure" in voice_lower:
            sensor_status = await sensor_manager.get_sensor_status(customer_id)
            pressure_sensors = [s for s in sensor_status.get("sensors", []) if s.get("type") == "pressure"]
            
            if pressure_sensors:
                responses = []
                for sensor in pressure_sensors[:3]:
                    if sensor.get("last_reading"):
                        responses.append(f"{sensor['name']}: {sensor['last_reading']} PSI")
                
                voice_response = f"Pressure readings: {', '.join(responses)}" if responses else "No recent pressure readings available"
            else:
                voice_response = "No pressure sensors configured"
        
        elif "alert" in voice_lower or "alarm" in voice_lower:
            overview = await get_dashboard_overview(current_user)
            voice_response = "Checking sensor alerts for you..."
        
        else:
            voice_response = "I can help you check temperature, pressure, vibration, or current alerts. What would you like to know?"
        
        return {
            "voice_query": voice_text,
            "voice_response": voice_response,
            "iot_enhanced": True,
            "command_recognized": True
        }
    
    result = await _process_voice_query()
    return JSONResponse(result)

# Sensor Configuration Templates
@router.get("/templates/sensor-configs")
async def get_sensor_config_templates():
    """Get pre-built sensor configuration templates"""
    return JSONResponse({
        "templates": [
            {
                "name": "Modbus Temperature Sensor",
                "type": "temperature",
                "protocol": "modbus_tcp",
                "description": "Standard Modbus TCP temperature sensor with RTD input",
                "connection_params": {
                    "host": "192.168.1.100",
                    "port": 502,
                    "slave_id": 1
                },
                "data_mapping": {
                    "registers": [
                        {
                            "address": 40001,
                            "scale": 0.1,
                            "offset": 0.0
                        }
                    ],
                    "unit": "°C"
                },
                "alert_thresholds": {
                    "warning_high": 80.0,
                    "critical_high": 95.0
                }
            },
            {
                "name": "MQTT Pressure Sensor",
                "type": "pressure",
                "protocol": "mqtt", 
                "description": "Wireless pressure sensor via MQTT broker",
                "connection_params": {
                    "broker": "iot.company.com",
                    "port": 1883,
                    "topic": "sensors/pressure/+",
                    "username": "sensor_user"
                },
                "data_mapping": {
                    "value_field": "pressure",
                    "unit": "PSI"
                },
                "alert_thresholds": {
                    "warning_high": 150.0,
                    "critical_high": 175.0
                }
            }
        ],
        "iot_available": IOT_AVAILABLE,
        "upgrade_required": not IOT_AVAILABLE
    })

# Upgrade Information
@router.get("/upgrade-info")
async def get_iot_upgrade_info(current_user: User = Depends(get_current_active_user)):
    """Get IoT Advanced Module upgrade information"""
    if IOT_AVAILABLE:
        customer_id = getattr(current_user, "customer_id", "demo_customer_1")
        license_info = await get_license_status(customer_id)
        current_tier = license_info.get("tier", "core")
    else:
        current_tier = "core"
    
    return JSONResponse({
        "current_tier": current_tier,
        "iot_available": IOT_AVAILABLE,
        "iot_features": [
            "Real-time sensor monitoring",
            "Predictive maintenance analytics",
            "Advanced alert system", 
            "Voice-integrated sensor queries",
            "Custom dashboard builder",
            "Historical trend analysis",
            "MQTT, Modbus, HTTP API support",
            "Unlimited sensors (with Enterprise)"
        ],
        "pricing": {
            "iot_advanced": "$199/month + $25/sensor",
            "enterprise": "$299/technician/month (includes IoT)"
        },
        "upgrade_benefits": {
            "productivity_increase": "40%",
            "downtime_reduction": "60%", 
            "maintenance_cost_savings": "30%",
            "failure_prediction_accuracy": "85%"
        },
        "contact_info": {
            "sales_email": "sales@chatterfix.com",
            "demo_url": "https://chatterfix.com/iot-demo",
            "upgrade_url": "https://chatterfix.com/upgrade"
        }
    })