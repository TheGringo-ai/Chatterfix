"""
FactoryFix Models
The "Digital Foreman" - Real-time machine monitoring and production tracking

Module B of the Gringo Industrial OS Trinity:
- ChatterFix (Maintenance)
- FactoryFix (Production) <- THIS
- QualityFix (QMS)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class MachineStatus(str, Enum):
    """Machine operational status - the Heartbeat"""
    RUNNING = "running"       # Green - All systems go
    IDLE = "idle"             # Yellow - Powered but not producing
    DOWN = "down"             # Red - Broken, needs maintenance
    MAINTENANCE = "maintenance"  # Orange - Scheduled maintenance
    OFFLINE = "offline"       # Gray - No signal/powered off


class AlertSeverity(str, Enum):
    """Alert severity for machine events"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Machine(BaseModel):
    """
    Factory machine with IoT sensor integration
    The "Digital Heartbeat" of the production floor
    """
    id: Optional[str] = None
    organization_id: str

    # Identity
    name: str = Field(..., description="Machine name (e.g., 'CNC Mill #3')")
    machine_type: str = Field(..., description="Type (e.g., 'CNC', 'Press', 'Conveyor')")
    location: Optional[str] = None
    asset_id: Optional[str] = None  # Link to ChatterFix Asset

    # Network/PLC Connection
    plc_ip: Optional[str] = Field(None, description="PLC IP address for data collection")
    plc_port: int = 502  # Modbus default
    protocol: str = "modbus"  # modbus, opcua, mqtt

    # Status (Updated by IoT Ingestor)
    status: MachineStatus = MachineStatus.OFFLINE
    last_heartbeat: Optional[str] = None
    heartbeat_interval_seconds: int = 30  # Expected heartbeat frequency

    # Sensor Data (Real-time from PLC)
    temperature_celsius: Optional[float] = None
    temperature_threshold: float = 85.0  # Alert if exceeded

    vibration_mm_s: Optional[float] = None  # mm/s RMS
    vibration_threshold: float = 10.0  # Alert if exceeded

    power_kw: Optional[float] = None
    rpm: Optional[float] = None

    # Production Metrics
    current_run_id: Optional[str] = None
    cycle_count_today: int = 0
    uptime_percent_today: float = 100.0

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "CNC Mill #3",
                "machine_type": "CNC",
                "location": "Building A, Cell 7",
                "plc_ip": "192.168.1.103",
                "status": "running",
                "temperature_celsius": 72.5,
                "vibration_mm_s": 3.2,
                "cycle_count_today": 847,
                "uptime_percent_today": 94.5
            }
        }


class ProductionRun(BaseModel):
    """
    A production run/batch on a machine
    Tracks target vs actual output with reject counts
    """
    id: Optional[str] = None
    organization_id: str

    # Links
    machine_id: str
    machine_name: Optional[str] = None
    work_order_id: Optional[str] = None  # Link to ChatterFix work order
    product_sku: Optional[str] = None
    product_name: Optional[str] = None

    # Targets
    target_count: int = Field(..., ge=0)
    target_cycle_time_seconds: Optional[float] = None

    # Actuals (Updated in real-time)
    actual_count: int = Field(default=0, ge=0)
    reject_count: int = Field(default=0, ge=0)
    rework_count: int = Field(default=0, ge=0)

    # Quality Metrics
    @property
    def good_count(self) -> int:
        return self.actual_count - self.reject_count - self.rework_count

    @property
    def yield_percent(self) -> float:
        if self.actual_count == 0:
            return 100.0
        return round((self.good_count / self.actual_count) * 100, 2)

    @property
    def completion_percent(self) -> float:
        if self.target_count == 0:
            return 100.0
        return round((self.actual_count / self.target_count) * 100, 2)

    # Timing
    status: str = "pending"  # pending, running, paused, completed, cancelled
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    pause_time_minutes: float = 0.0  # Total pause duration

    # Operator
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "machine_cnc_3",
                "product_sku": "BRACKET-A100",
                "product_name": "Steel Bracket Assembly",
                "target_count": 500,
                "actual_count": 423,
                "reject_count": 7,
                "status": "running",
                "start_time": "2024-12-20T08:00:00Z"
            }
        }


class MachineAlert(BaseModel):
    """
    Alert generated by machine sensor thresholds
    Triggers cross-module actions (work orders, production stops)
    """
    id: Optional[str] = None
    organization_id: str

    machine_id: str
    machine_name: Optional[str] = None

    alert_type: str  # temperature, vibration, downtime, quality
    severity: AlertSeverity

    message: str
    sensor_value: Optional[float] = None
    threshold_value: Optional[float] = None

    # Cross-module triggers
    triggered_work_order_id: Optional[str] = None  # ChatterFix integration
    triggered_production_stop: bool = False  # Stop the line

    # Status
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[str] = None

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "machine_cnc_3",
                "machine_name": "CNC Mill #3",
                "alert_type": "temperature",
                "severity": "critical",
                "message": "Temperature exceeded threshold: 92°C > 85°C",
                "sensor_value": 92.0,
                "threshold_value": 85.0,
                "triggered_work_order_id": "wo_emergency_123"
            }
        }


class HeartbeatStatus(BaseModel):
    """
    Simple Green/Red status for the Heartbeat Monitor dashboard
    "Is the machine alive?"
    """
    machine_id: str
    machine_name: str
    status: MachineStatus
    status_color: str  # green, yellow, red, orange, gray
    last_heartbeat: Optional[str] = None
    seconds_since_heartbeat: Optional[int] = None

    # Key metrics for quick view
    temperature: Optional[float] = None
    temperature_alert: bool = False
    vibration: Optional[float] = None
    vibration_alert: bool = False

    # Production info
    current_run: Optional[str] = None
    run_progress_percent: Optional[float] = None


class FactoryDashboard(BaseModel):
    """
    Factory floor overview - the "Digital Foreman" view
    """
    total_machines: int = 0
    machines_running: int = 0
    machines_idle: int = 0
    machines_down: int = 0
    machines_maintenance: int = 0
    machines_offline: int = 0

    # Overall Equipment Effectiveness (OEE)
    overall_oee_percent: float = 0.0

    # Production totals
    total_production_today: int = 0
    total_rejects_today: int = 0
    yield_percent_today: float = 100.0

    # Alerts
    active_critical_alerts: int = 0
    active_warning_alerts: int = 0

    # Machine list with heartbeat status
    machines: List[HeartbeatStatus] = []

    class Config:
        json_schema_extra = {
            "example": {
                "total_machines": 12,
                "machines_running": 9,
                "machines_idle": 1,
                "machines_down": 1,
                "machines_maintenance": 1,
                "overall_oee_percent": 78.5,
                "total_production_today": 4523,
                "total_rejects_today": 34,
                "active_critical_alerts": 1
            }
        }
