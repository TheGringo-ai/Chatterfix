"""
ChatterFix IoT Advanced Module - Sensor Management
Universal sensor integration and data collection framework
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Third-party imports for sensor protocols
try:
    from pymodbus.client.sync import ModbusTcpClient

    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False

try:
    import paho.mqtt.client as mqtt

    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

from .licensing import require_iot_license, validate_sensor_count

logger = logging.getLogger(__name__)


class SensorType(Enum):
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    FLOW = "flow"
    ELECTRICAL = "electrical"
    ENVIRONMENTAL = "environmental"
    MECHANICAL = "mechanical"


class SensorProtocol(Enum):
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    MQTT = "mqtt"
    HTTP_API = "http_api"
    SERIAL = "serial"
    OPC_UA = "opc_ua"


class SensorStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class SensorReading:
    """Individual sensor reading with metadata"""

    sensor_id: str
    value: float
    unit: str
    timestamp: datetime
    quality: float = 1.0  # 0.0 to 1.0 quality score
    alert_level: str = "normal"  # normal, warning, critical
    raw_data: Optional[Dict] = None


@dataclass
class SensorConfig:
    """Sensor configuration definition"""

    sensor_id: str
    name: str
    sensor_type: SensorType
    protocol: SensorProtocol
    connection_params: Dict[str, Any]
    data_mapping: Dict[str, Any]
    sampling_interval: int = 60  # seconds
    alert_thresholds: Dict[str, float] = None
    asset_id: Optional[str] = None
    location: Optional[str] = None
    enabled: bool = True


@dataclass
class SensorDevice:
    """Physical sensor device representation"""

    config: SensorConfig
    status: SensorStatus = SensorStatus.OFFLINE
    last_reading: Optional[SensorReading] = None
    last_seen: Optional[datetime] = None
    connection_errors: int = 0
    total_readings: int = 0


class SensorManager:
    """Universal sensor management and data collection"""

    def __init__(self):
        self.sensors: Dict[str, SensorDevice] = {}
        self.data_collectors: Dict[str, Any] = {}
        self.is_running = False
        self.collection_tasks = {}

    @require_iot_license
    async def add_sensor(
        self, customer_id: str, sensor_config: SensorConfig
    ) -> Dict[str, Any]:
        """Add a new sensor to the system"""

        # Validate sensor count limits
        current_count = len(self.sensors)
        validation = await validate_sensor_count(customer_id, current_count + 1)

        if not validation["valid"]:
            return {
                "success": False,
                "error": "Sensor limit exceeded",
                "message": validation["message"],
                "upgrade_required": validation.get("upgrade_required", False),
            }

        # Create sensor device
        device = SensorDevice(config=sensor_config)
        self.sensors[sensor_config.sensor_id] = device

        # Initialize data collector based on protocol
        try:
            collector = await self._create_data_collector(sensor_config)
            self.data_collectors[sensor_config.sensor_id] = collector

            # Start data collection
            if sensor_config.enabled:
                await self._start_sensor_collection(sensor_config.sensor_id)

            logger.info(f"Sensor {sensor_config.sensor_id} added successfully")

            return {
                "success": True,
                "sensor_id": sensor_config.sensor_id,
                "message": f"Sensor {sensor_config.name} added and monitoring started",
                "status": device.status.value,
            }

        except Exception as e:
            logger.error(f"Failed to add sensor {sensor_config.sensor_id}: {e}")

            # Cleanup on failure
            if sensor_config.sensor_id in self.sensors:
                del self.sensors[sensor_config.sensor_id]

            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to configure sensor {sensor_config.name}",
            }

    async def _create_data_collector(self, config: SensorConfig):
        """Create appropriate data collector for sensor protocol"""

        if config.protocol == SensorProtocol.MODBUS_TCP:
            return await self._create_modbus_collector(config)
        elif config.protocol == SensorProtocol.MQTT:
            return await self._create_mqtt_collector(config)
        elif config.protocol == SensorProtocol.HTTP_API:
            return await self._create_http_collector(config)
        else:
            raise ValueError(f"Unsupported protocol: {config.protocol}")

    async def _create_modbus_collector(self, config: SensorConfig):
        """Create Modbus TCP/RTU data collector"""

        if not MODBUS_AVAILABLE:
            raise ImportError("Modbus library not available - install pymodbus")

        connection_params = config.connection_params

        class ModbusCollector:
            def __init__(self, host, port, slave_id, registers):
                self.host = host
                self.port = port
                self.slave_id = slave_id
                self.registers = registers
                self.client = None

            async def connect(self):
                self.client = ModbusTcpClient(self.host, port=self.port)
                return self.client.connect()

            async def read_data(self) -> List[float]:
                if not self.client or not self.client.is_socket_open():
                    await self.connect()

                values = []
                for register in self.registers:
                    try:
                        result = self.client.read_holding_registers(
                            register["address"], 1, unit=self.slave_id
                        )
                        if result.isError():
                            logger.error(f"Modbus read error: {result}")
                            values.append(None)
                        else:
                            # Apply scaling if configured
                            raw_value = result.registers[0]
                            scaled_value = raw_value * register.get(
                                "scale", 1.0
                            ) + register.get("offset", 0.0)
                            values.append(scaled_value)
                    except Exception as e:
                        logger.error(f"Modbus register read error: {e}")
                        values.append(None)

                return values

        collector = ModbusCollector(
            host=connection_params["host"],
            port=connection_params.get("port", 502),
            slave_id=connection_params.get("slave_id", 1),
            registers=config.data_mapping.get("registers", []),
        )

        # Test connection
        if await collector.connect():
            logger.info(f"Modbus collector connected for sensor {config.sensor_id}")
        else:
            raise ConnectionError(
                f"Failed to connect to Modbus device at {connection_params['host']}"
            )

        return collector

    async def _create_mqtt_collector(self, config: SensorConfig):
        """Create MQTT data collector"""

        if not MQTT_AVAILABLE:
            raise ImportError("MQTT library not available - install paho-mqtt")

        connection_params = config.connection_params

        class MQTTCollector:
            def __init__(self, broker, port, topic, username=None, password=None):
                self.broker = broker
                self.port = port
                self.topic = topic
                self.client = mqtt.Client()
                self.latest_data = None
                self.connected = False

                if username and password:
                    self.client.username_pw_set(username, password)

                self.client.on_connect = self._on_connect
                self.client.on_message = self._on_message
                self.client.on_disconnect = self._on_disconnect

            def _on_connect(self, client, userdata, flags, rc):
                self.connected = rc == 0
                if self.connected:
                    client.subscribe(self.topic)
                    logger.info(f"MQTT connected and subscribed to {self.topic}")
                else:
                    logger.error(f"MQTT connection failed with code {rc}")

            def _on_message(self, client, userdata, msg):
                try:
                    payload = json.loads(msg.payload.decode())
                    self.latest_data = payload
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode MQTT message: {e}")

            def _on_disconnect(self, client, userdata, rc):
                self.connected = False
                logger.warning(f"MQTT disconnected with code {rc}")

            async def connect(self):
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()

                # Wait for connection
                for _ in range(50):  # 5 second timeout
                    if self.connected:
                        return True
                    await asyncio.sleep(0.1)

                return False

            async def read_data(self) -> Dict:
                return self.latest_data

        collector = MQTTCollector(
            broker=connection_params["broker"],
            port=connection_params.get("port", 1883),
            topic=connection_params["topic"],
            username=connection_params.get("username"),
            password=connection_params.get("password"),
        )

        # Test connection
        if await collector.connect():
            logger.info(f"MQTT collector connected for sensor {config.sensor_id}")
        else:
            raise ConnectionError(
                f"Failed to connect to MQTT broker at {connection_params['broker']}"
            )

        return collector

    async def _create_http_collector(self, config: SensorConfig):
        """Create HTTP API data collector"""

        import httpx

        connection_params = config.connection_params

        class HTTPCollector:
            def __init__(self, url, headers=None, auth=None):
                self.url = url
                self.headers = headers or {}
                self.auth = auth

            async def read_data(self) -> Dict:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        self.url, headers=self.headers, auth=self.auth, timeout=10.0
                    )
                    response.raise_for_status()
                    return response.json()

        return HTTPCollector(
            url=connection_params["url"],
            headers=connection_params.get("headers"),
            auth=connection_params.get("auth"),
        )

    async def _start_sensor_collection(self, sensor_id: str):
        """Start data collection task for sensor"""

        if sensor_id in self.collection_tasks:
            # Stop existing task
            self.collection_tasks[sensor_id].cancel()

        # Start new collection task
        task = asyncio.create_task(self._sensor_collection_loop(sensor_id))
        self.collection_tasks[sensor_id] = task

        # Update sensor status
        self.sensors[sensor_id].status = SensorStatus.ONLINE

    async def _sensor_collection_loop(self, sensor_id: str):
        """Main data collection loop for a sensor"""

        device = self.sensors[sensor_id]
        collector = self.data_collectors[sensor_id]

        logger.info(f"Starting data collection for sensor {sensor_id}")

        while device.config.enabled:
            try:
                # Collect data from sensor
                raw_data = await collector.read_data()

                if raw_data is not None:
                    # Process and store reading
                    reading = await self._process_sensor_reading(sensor_id, raw_data)

                    if reading:
                        device.last_reading = reading
                        device.last_seen = datetime.now()
                        device.total_readings += 1
                        device.connection_errors = 0
                        device.status = SensorStatus.ONLINE

                        # Store reading in database
                        await self._store_sensor_reading(reading)

                        # Check for alerts
                        await self._check_sensor_alerts(device, reading)

                # Wait for next sampling interval
                await asyncio.sleep(device.config.sampling_interval)

            except Exception as e:
                logger.error(f"Sensor {sensor_id} collection error: {e}")
                device.connection_errors += 1

                if device.connection_errors >= 3:
                    device.status = SensorStatus.ERROR
                    logger.warning(
                        f"Sensor {sensor_id} marked as ERROR after {device.connection_errors} failures"
                    )

                # Wait before retry (exponential backoff)
                retry_delay = min(300, 30 * (2 ** (device.connection_errors - 1)))
                await asyncio.sleep(retry_delay)

    async def _process_sensor_reading(
        self, sensor_id: str, raw_data: Any
    ) -> Optional[SensorReading]:
        """Process raw sensor data into structured reading"""

        device = self.sensors[sensor_id]
        config = device.config

        try:
            # Extract value based on data mapping
            if isinstance(raw_data, (list, tuple)):
                # Modbus-style array data
                value = raw_data[0] if raw_data else None
            elif isinstance(raw_data, dict):
                # JSON/MQTT style data
                value_key = config.data_mapping.get("value_field", "value")
                value = raw_data.get(value_key)
            else:
                # Direct numeric value
                value = float(raw_data)

            if value is None:
                return None

            # Apply calibration if configured
            calibration = config.data_mapping.get("calibration", {})
            if calibration:
                scale = calibration.get("scale", 1.0)
                offset = calibration.get("offset", 0.0)
                value = value * scale + offset

            # Determine alert level
            alert_level = "normal"
            thresholds = config.alert_thresholds or {}

            if "critical_high" in thresholds and value >= thresholds["critical_high"]:
                alert_level = "critical"
            elif "critical_low" in thresholds and value <= thresholds["critical_low"]:
                alert_level = "critical"
            elif "warning_high" in thresholds and value >= thresholds["warning_high"]:
                alert_level = "warning"
            elif "warning_low" in thresholds and value <= thresholds["warning_low"]:
                alert_level = "warning"

            # Create reading
            reading = SensorReading(
                sensor_id=sensor_id,
                value=value,
                unit=config.data_mapping.get("unit", "units"),
                timestamp=datetime.now(),
                quality=1.0,  # TODO: Implement quality assessment
                alert_level=alert_level,
                raw_data=raw_data if isinstance(raw_data, dict) else None,
            )

            return reading

        except Exception as e:
            logger.error(f"Failed to process sensor data for {sensor_id}: {e}")
            return None

    async def _store_sensor_reading(self, reading: SensorReading):
        """Store sensor reading in database"""
        # TODO: Implement time-series database storage (InfluxDB, TimescaleDB)
        logger.debug(
            f"Storing reading: {reading.sensor_id} = {reading.value} {reading.unit}"
        )

    async def _check_sensor_alerts(self, device: SensorDevice, reading: SensorReading):
        """Check sensor reading for alert conditions"""

        if reading.alert_level in ["warning", "critical"]:
            alert_message = f"Sensor {device.config.name}: {reading.value} {reading.unit} - {reading.alert_level.upper()} level"

            # TODO: Integrate with ChatterFix voice system
            # voice_alert = f"Alert: {device.config.name} reading {reading.value} {reading.unit} is at {reading.alert_level} level"

            logger.warning(f"SENSOR ALERT: {alert_message}")

            # TODO: Send notifications via configured channels
            # await self._send_alert_notifications(device, reading, alert_message)

    @require_iot_license
    async def get_sensor_status(
        self, customer_id: str, sensor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get status of one or all sensors"""

        if sensor_id:
            if sensor_id in self.sensors:
                device = self.sensors[sensor_id]
                return {
                    "sensor_id": sensor_id,
                    "name": device.config.name,
                    "status": device.status.value,
                    "last_reading": (
                        asdict(device.last_reading) if device.last_reading else None
                    ),
                    "last_seen": (
                        device.last_seen.isoformat() if device.last_seen else None
                    ),
                    "total_readings": device.total_readings,
                    "connection_errors": device.connection_errors,
                }
            else:
                return {"error": f"Sensor {sensor_id} not found"}
        else:
            # Return status of all sensors
            sensors_status = []
            for device in self.sensors.values():
                sensors_status.append(
                    {
                        "sensor_id": device.config.sensor_id,
                        "name": device.config.name,
                        "type": device.config.sensor_type.value,
                        "status": device.status.value,
                        "last_reading": (
                            device.last_reading.value if device.last_reading else None
                        ),
                        "last_seen": (
                            device.last_seen.isoformat() if device.last_seen else None
                        ),
                        "alert_level": (
                            device.last_reading.alert_level
                            if device.last_reading
                            else "unknown"
                        ),
                    }
                )

            return {
                "total_sensors": len(self.sensors),
                "online_sensors": len(
                    [
                        s
                        for s in self.sensors.values()
                        if s.status == SensorStatus.ONLINE
                    ]
                ),
                "sensors": sensors_status,
            }

    @require_iot_license
    async def get_sensor_data(
        self, customer_id: str, sensor_id: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Get historical sensor data"""

        # TODO: Implement time-series data retrieval
        # For now, return current reading
        if sensor_id in self.sensors:
            device = self.sensors[sensor_id]
            if device.last_reading:
                return {
                    "sensor_id": sensor_id,
                    "data_points": 1,
                    "readings": [asdict(device.last_reading)],
                    "summary": {
                        "current_value": device.last_reading.value,
                        "unit": device.last_reading.unit,
                        "alert_level": device.last_reading.alert_level,
                    },
                }

        return {"error": f"No data available for sensor {sensor_id}"}

    async def remove_sensor(self, customer_id: str, sensor_id: str) -> Dict[str, Any]:
        """Remove a sensor from the system"""

        if sensor_id not in self.sensors:
            return {"success": False, "error": f"Sensor {sensor_id} not found"}

        try:
            # Stop collection task
            if sensor_id in self.collection_tasks:
                self.collection_tasks[sensor_id].cancel()
                del self.collection_tasks[sensor_id]

            # Remove data collector
            if sensor_id in self.data_collectors:
                del self.data_collectors[sensor_id]

            # Remove sensor
            sensor_name = self.sensors[sensor_id].config.name
            del self.sensors[sensor_id]

            logger.info(f"Sensor {sensor_id} removed successfully")

            return {
                "success": True,
                "message": f"Sensor {sensor_name} removed successfully",
            }

        except Exception as e:
            logger.error(f"Failed to remove sensor {sensor_id}: {e}")
            return {"success": False, "error": str(e)}


# Global sensor manager instance
sensor_manager = SensorManager()
