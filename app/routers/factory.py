"""
FactoryFix Router
The "Digital Foreman" - Real-time machine monitoring and production tracking

Module B of the Gringo Industrial OS:
- Machine Heartbeat Monitor (Green/Red dashboard)
- IoT Sensor Integration (Temperature, Vibration)
- Production Run Tracking
- Cross-module triggers (Machine Down -> ChatterFix Work Order)
"""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.auth import get_optional_current_user
from app.models.factory import (
    AlertSeverity,
    FactoryDashboard,
    HeartbeatStatus,
    Machine,
    MachineAlert,
    MachineStatus,
    ProductionRun,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/factory", tags=["FactoryFix"])


# ============ In-Memory Simulation Store ============
# In production, this would be Firestore + Redis for real-time

_machines: Dict[str, Machine] = {}
_production_runs: Dict[str, ProductionRun] = {}
_alerts: Dict[str, MachineAlert] = {}


def _init_demo_machines():
    """Initialize demo machines for the heartbeat dashboard"""
    if _machines:
        return

    demo_machines = [
        Machine(
            id="machine_cnc_1",
            organization_id="demo_org",
            name="CNC Mill #1",
            machine_type="CNC",
            location="Building A, Cell 1",
            plc_ip="192.168.1.101",
            status=MachineStatus.RUNNING,
            temperature_celsius=68.5,
            vibration_mm_s=2.1,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            cycle_count_today=523,
            uptime_percent_today=96.2,
        ),
        Machine(
            id="machine_cnc_2",
            organization_id="demo_org",
            name="CNC Mill #2",
            machine_type="CNC",
            location="Building A, Cell 2",
            plc_ip="192.168.1.102",
            status=MachineStatus.RUNNING,
            temperature_celsius=71.2,
            vibration_mm_s=2.8,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            cycle_count_today=489,
            uptime_percent_today=94.1,
        ),
        Machine(
            id="machine_cnc_3",
            organization_id="demo_org",
            name="CNC Mill #3",
            machine_type="CNC",
            location="Building A, Cell 3",
            plc_ip="192.168.1.103",
            status=MachineStatus.DOWN,
            temperature_celsius=45.0,
            vibration_mm_s=0.0,
            last_heartbeat=(datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
            cycle_count_today=312,
            uptime_percent_today=67.3,
        ),
        Machine(
            id="machine_press_1",
            organization_id="demo_org",
            name="Hydraulic Press #1",
            machine_type="Press",
            location="Building B, Bay 1",
            plc_ip="192.168.1.201",
            status=MachineStatus.RUNNING,
            temperature_celsius=82.1,
            temperature_threshold=85.0,
            vibration_mm_s=4.5,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            cycle_count_today=1247,
            uptime_percent_today=98.5,
        ),
        Machine(
            id="machine_press_2",
            organization_id="demo_org",
            name="Hydraulic Press #2",
            machine_type="Press",
            location="Building B, Bay 2",
            plc_ip="192.168.1.202",
            status=MachineStatus.MAINTENANCE,
            temperature_celsius=35.0,
            vibration_mm_s=0.0,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            cycle_count_today=0,
            uptime_percent_today=0.0,
        ),
        Machine(
            id="machine_conveyor_1",
            organization_id="demo_org",
            name="Main Conveyor Line",
            machine_type="Conveyor",
            location="Building A, Main Floor",
            plc_ip="192.168.1.50",
            status=MachineStatus.RUNNING,
            temperature_celsius=42.0,
            vibration_mm_s=1.2,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            cycle_count_today=0,
            uptime_percent_today=99.1,
        ),
        Machine(
            id="machine_robot_1",
            organization_id="demo_org",
            name="Welding Robot #1",
            machine_type="Robot",
            location="Building C, Weld Cell 1",
            plc_ip="192.168.1.301",
            status=MachineStatus.IDLE,
            temperature_celsius=55.0,
            vibration_mm_s=0.5,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            cycle_count_today=89,
            uptime_percent_today=45.0,
        ),
        Machine(
            id="machine_oven_1",
            organization_id="demo_org",
            name="Curing Oven #1",
            machine_type="Oven",
            location="Building D",
            plc_ip="192.168.1.401",
            status=MachineStatus.RUNNING,
            temperature_celsius=180.5,
            temperature_threshold=200.0,
            vibration_mm_s=0.1,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            cycle_count_today=12,
            uptime_percent_today=100.0,
        ),
    ]

    for m in demo_machines:
        _machines[m.id] = m


# Initialize on import
_init_demo_machines()


# ============ Heartbeat Dashboard ============

@router.get("/heartbeat", response_model=FactoryDashboard)
async def get_heartbeat_dashboard(
    current_user=Depends(get_optional_current_user),
):
    """
    The "Digital Foreman" Dashboard

    Shows all machines as Green (Running) or Red (Dead).
    One glance tells you the health of the entire factory floor.
    """
    _init_demo_machines()

    # Build heartbeat status for each machine
    heartbeats: List[HeartbeatStatus] = []
    now = datetime.now(timezone.utc)

    running = idle = down = maintenance = offline = 0
    total_production = 0
    total_rejects = 0
    critical_alerts = 0
    warning_alerts = 0

    for machine in _machines.values():
        # Calculate seconds since last heartbeat
        seconds_since = None
        if machine.last_heartbeat:
            try:
                last_hb = datetime.fromisoformat(machine.last_heartbeat.replace('Z', '+00:00'))
                seconds_since = int((now - last_hb).total_seconds())
            except:
                pass

        # Determine status color
        status_color = {
            MachineStatus.RUNNING: "green",
            MachineStatus.IDLE: "yellow",
            MachineStatus.DOWN: "red",
            MachineStatus.MAINTENANCE: "orange",
            MachineStatus.OFFLINE: "gray",
        }.get(machine.status, "gray")

        # Check for threshold alerts
        temp_alert = machine.temperature_celsius and machine.temperature_celsius > machine.temperature_threshold
        vib_alert = machine.vibration_mm_s and machine.vibration_mm_s > machine.vibration_threshold

        if temp_alert or vib_alert:
            critical_alerts += 1

        heartbeats.append(HeartbeatStatus(
            machine_id=machine.id,
            machine_name=machine.name,
            status=machine.status,
            status_color=status_color,
            last_heartbeat=machine.last_heartbeat,
            seconds_since_heartbeat=seconds_since,
            temperature=machine.temperature_celsius,
            temperature_alert=temp_alert,
            vibration=machine.vibration_mm_s,
            vibration_alert=vib_alert,
            current_run=machine.current_run_id,
        ))

        # Count statuses
        if machine.status == MachineStatus.RUNNING:
            running += 1
        elif machine.status == MachineStatus.IDLE:
            idle += 1
        elif machine.status == MachineStatus.DOWN:
            down += 1
        elif machine.status == MachineStatus.MAINTENANCE:
            maintenance += 1
        else:
            offline += 1

        total_production += machine.cycle_count_today

    # Calculate OEE (simplified)
    total_machines = len(_machines)
    availability = running / max(1, total_machines - maintenance)
    oee = availability * 0.95 * 0.98 * 100  # Availability * Performance * Quality

    return FactoryDashboard(
        total_machines=total_machines,
        machines_running=running,
        machines_idle=idle,
        machines_down=down,
        machines_maintenance=maintenance,
        machines_offline=offline,
        overall_oee_percent=round(oee, 1),
        total_production_today=total_production,
        total_rejects_today=total_rejects,
        yield_percent_today=99.2,
        active_critical_alerts=critical_alerts,
        active_warning_alerts=warning_alerts,
        machines=heartbeats,
    )


# ============ Machine CRUD ============

@router.get("/machines", response_model=List[Machine])
async def list_machines(
    status: Optional[str] = None,
    machine_type: Optional[str] = None,
    current_user=Depends(get_optional_current_user),
):
    """List all machines, optionally filtered by status or type"""
    _init_demo_machines()

    machines = list(_machines.values())

    if status:
        machines = [m for m in machines if m.status.value == status]
    if machine_type:
        machines = [m for m in machines if m.machine_type.lower() == machine_type.lower()]

    return machines


@router.get("/machines/{machine_id}", response_model=Machine)
async def get_machine(
    machine_id: str,
    current_user=Depends(get_optional_current_user),
):
    """Get machine details"""
    _init_demo_machines()

    if machine_id not in _machines:
        raise HTTPException(status_code=404, detail="Machine not found")

    return _machines[machine_id]


@router.post("/machines/{machine_id}/status")
async def update_machine_status(
    machine_id: str,
    status: MachineStatus,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_optional_current_user),
):
    """
    Update machine status.
    If status changes to DOWN, triggers ChatterFix work order.
    """
    _init_demo_machines()

    if machine_id not in _machines:
        raise HTTPException(status_code=404, detail="Machine not found")

    machine = _machines[machine_id]
    old_status = machine.status
    machine.status = status
    machine.updated_at = datetime.now(timezone.utc).isoformat()

    # Cross-module trigger: Machine Down -> Create Work Order
    if status == MachineStatus.DOWN and old_status != MachineStatus.DOWN:
        background_tasks.add_task(
            _trigger_maintenance_work_order,
            machine,
            "Machine went down - requires immediate attention"
        )

    return {"status": "updated", "old_status": old_status.value, "new_status": status.value}


# ============ IoT Ingestor ============

@router.post("/ingest")
async def ingest_sensor_data(
    machine_id: str,
    temperature: Optional[float] = None,
    vibration: Optional[float] = None,
    rpm: Optional[float] = None,
    power_kw: Optional[float] = None,
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_optional_current_user),
):
    """
    IoT Ingestor - Receive sensor data from PLCs/MQTT.

    In production, this would be called by an MQTT bridge or OPC-UA connector.
    Checks thresholds and triggers alerts/work orders if exceeded.
    """
    _init_demo_machines()

    if machine_id not in _machines:
        raise HTTPException(status_code=404, detail="Machine not found")

    machine = _machines[machine_id]
    alerts_generated = []

    # Update sensor values
    if temperature is not None:
        machine.temperature_celsius = temperature
        if temperature > machine.temperature_threshold:
            alert = await _create_alert(
                machine,
                "temperature",
                AlertSeverity.CRITICAL,
                f"Temperature exceeded: {temperature}°C > {machine.temperature_threshold}°C",
                temperature,
                machine.temperature_threshold
            )
            alerts_generated.append(alert)
            if background_tasks:
                background_tasks.add_task(_trigger_maintenance_work_order, machine, alert.message)

    if vibration is not None:
        machine.vibration_mm_s = vibration
        if vibration > machine.vibration_threshold:
            alert = await _create_alert(
                machine,
                "vibration",
                AlertSeverity.WARNING,
                f"Vibration high: {vibration} mm/s > {machine.vibration_threshold} mm/s",
                vibration,
                machine.vibration_threshold
            )
            alerts_generated.append(alert)

    if rpm is not None:
        machine.rpm = rpm

    if power_kw is not None:
        machine.power_kw = power_kw

    # Update heartbeat
    machine.last_heartbeat = datetime.now(timezone.utc).isoformat()
    if machine.status == MachineStatus.OFFLINE:
        machine.status = MachineStatus.RUNNING

    return {
        "status": "ingested",
        "machine_id": machine_id,
        "alerts_generated": len(alerts_generated),
        "alerts": [a.message for a in alerts_generated]
    }


@router.post("/simulate-iot")
async def simulate_iot_data(
    duration_seconds: int = Query(default=10, le=60),
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_optional_current_user),
):
    """
    Simulate IoT sensor data for demo purposes.
    Generates realistic temperature/vibration fluctuations.
    """
    _init_demo_machines()

    async def simulate():
        for _ in range(duration_seconds):
            for machine in _machines.values():
                if machine.status == MachineStatus.RUNNING:
                    # Simulate sensor fluctuations
                    machine.temperature_celsius = round(
                        machine.temperature_celsius + random.uniform(-0.5, 0.5), 1
                    )
                    machine.vibration_mm_s = round(
                        max(0, machine.vibration_mm_s + random.uniform(-0.2, 0.2)), 2
                    )
                    machine.last_heartbeat = datetime.now(timezone.utc).isoformat()
                    machine.cycle_count_today += random.randint(0, 2)
            await asyncio.sleep(1)

    if background_tasks:
        background_tasks.add_task(simulate)

    return {"status": "simulation_started", "duration_seconds": duration_seconds}


# ============ Production Runs ============

@router.post("/runs", response_model=ProductionRun)
async def create_production_run(
    machine_id: str,
    target_count: int,
    product_sku: Optional[str] = None,
    product_name: Optional[str] = None,
    current_user=Depends(get_optional_current_user),
):
    """Start a new production run on a machine"""
    _init_demo_machines()

    if machine_id not in _machines:
        raise HTTPException(status_code=404, detail="Machine not found")

    machine = _machines[machine_id]

    run = ProductionRun(
        id=f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        organization_id="demo_org",
        machine_id=machine_id,
        machine_name=machine.name,
        target_count=target_count,
        product_sku=product_sku,
        product_name=product_name,
        status="running",
        start_time=datetime.now(timezone.utc).isoformat(),
        operator_id=current_user.uid if current_user else None,
        operator_name=current_user.full_name if current_user else None,
    )

    _production_runs[run.id] = run
    machine.current_run_id = run.id

    return run


@router.post("/runs/{run_id}/count")
async def update_run_count(
    run_id: str,
    good: int = 0,
    reject: int = 0,
    rework: int = 0,
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_optional_current_user),
):
    """
    Update production counts.
    If reject count exceeds threshold, triggers QualityFix alert.
    """
    if run_id not in _production_runs:
        raise HTTPException(status_code=404, detail="Production run not found")

    run = _production_runs[run_id]
    run.actual_count += good + reject + rework
    run.reject_count += reject
    run.rework_count += rework

    # Cross-module trigger: >5 rejects -> QualityFix alert
    if run.reject_count > 5 and background_tasks:
        background_tasks.add_task(
            _trigger_quality_alert,
            run,
            f"High reject rate on {run.machine_name}: {run.reject_count} rejects"
        )

    return {
        "run_id": run_id,
        "actual_count": run.actual_count,
        "reject_count": run.reject_count,
        "yield_percent": run.yield_percent,
        "completion_percent": run.completion_percent
    }


@router.get("/runs", response_model=List[ProductionRun])
async def list_production_runs(
    status: Optional[str] = None,
    machine_id: Optional[str] = None,
    current_user=Depends(get_optional_current_user),
):
    """List production runs"""
    runs = list(_production_runs.values())

    if status:
        runs = [r for r in runs if r.status == status]
    if machine_id:
        runs = [r for r in runs if r.machine_id == machine_id]

    return runs


# ============ Alerts ============

@router.get("/alerts", response_model=List[MachineAlert])
async def list_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    current_user=Depends(get_optional_current_user),
):
    """List machine alerts"""
    alerts = list(_alerts.values())

    if severity:
        alerts = [a for a in alerts if a.severity.value == severity]
    if acknowledged is not None:
        alerts = [a for a in alerts if a.acknowledged == acknowledged]

    return sorted(alerts, key=lambda a: a.created_at, reverse=True)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user=Depends(get_optional_current_user),
):
    """Acknowledge an alert"""
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert = _alerts[alert_id]
    alert.acknowledged = True
    alert.acknowledged_by = current_user.uid if current_user else "system"
    alert.acknowledged_at = datetime.now(timezone.utc).isoformat()

    return {"status": "acknowledged"}


# ============ Cross-Module Integration ============

async def _create_alert(
    machine: Machine,
    alert_type: str,
    severity: AlertSeverity,
    message: str,
    sensor_value: float,
    threshold: float,
) -> MachineAlert:
    """Create and store a machine alert"""
    alert = MachineAlert(
        id=f"alert_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{alert_type}",
        organization_id=machine.organization_id,
        machine_id=machine.id,
        machine_name=machine.name,
        alert_type=alert_type,
        severity=severity,
        message=message,
        sensor_value=sensor_value,
        threshold_value=threshold,
    )
    _alerts[alert.id] = alert
    logger.warning(f"FACTORY ALERT: {message}")
    return alert


async def _trigger_maintenance_work_order(machine: Machine, reason: str):
    """
    Cross-module: FactoryFix -> ChatterFix
    Machine down triggers automatic work order creation
    """
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        work_order = {
            "title": f"[FACTORY] {machine.name} - {reason[:50]}",
            "description": f"Auto-generated from FactoryFix.\n\nMachine: {machine.name}\nType: {machine.machine_type}\nLocation: {machine.location}\n\nReason: {reason}",
            "priority": "Critical",
            "status": "Open",
            "type": "Emergency",
            "organization_id": machine.organization_id,
            "asset_id": machine.asset_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "factoryfix_auto",
            "source_machine_id": machine.id,
        }

        await db.create_document("work_orders", work_order)
        logger.info(f"ChatterFix work order created for {machine.name}")
    except Exception as e:
        logger.error(f"Failed to create maintenance work order: {e}")


async def _trigger_quality_alert(run: ProductionRun, reason: str):
    """
    Cross-module: FactoryFix -> QualityFix
    High reject rate triggers quality investigation
    """
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        nc_record = {
            "source_type": "production",
            "production_run_id": run.id,
            "machine_id": run.machine_id,
            "defect_type": "high_reject_rate",
            "description": reason,
            "severity": "major",
            "quantity_affected": run.reject_count,
            "product_sku": run.product_sku,
            "capa_required": True,
            "organization_id": run.organization_id,
            "reported_at": datetime.now(timezone.utc).isoformat(),
            "source": "factoryfix_auto",
        }

        await db.create_document("non_conformances", nc_record)
        logger.info(f"QualityFix NC created for high reject rate on {run.machine_name}")
    except Exception as e:
        logger.error(f"Failed to create quality NC: {e}")
