"""
EventBus - The Nervous System of Gringo Industrial OS

Cross-module event system that enables:
- FactoryFix (Machine Down) -> ChatterFix (Work Order)
- QualityFix (High Rejects) -> FactoryFix (Stop Production)
- SafetyFix (Man Down) -> ChatterFix (Emergency Maintenance)

This is the glue that makes the "Trinity" work as one unified system.
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of cross-module events"""
    # FactoryFix Events
    MACHINE_DOWN = "machine_down"
    MACHINE_UP = "machine_up"
    TEMPERATURE_ALERT = "temperature_alert"
    VIBRATION_ALERT = "vibration_alert"
    PRODUCTION_STARTED = "production_started"
    PRODUCTION_COMPLETED = "production_completed"
    HIGH_REJECT_RATE = "high_reject_rate"

    # QualityFix Events
    INSPECTION_FAILED = "inspection_failed"
    NC_CREATED = "nc_created"
    CAPA_REQUIRED = "capa_required"
    CRITICAL_DEFECT = "critical_defect"

    # SafetyFix Events
    MAN_DOWN = "man_down"
    SAFETY_INCIDENT = "safety_incident"
    PPE_VIOLATION = "ppe_violation"
    ZONE_ENTRY = "zone_entry"

    # ChatterFix Events
    WORK_ORDER_CREATED = "work_order_created"
    WORK_ORDER_COMPLETED = "work_order_completed"
    ASSET_DOWN = "asset_down"
    PM_DUE = "pm_due"


class EventPriority(str, Enum):
    """Event priority levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Act within minutes
    NORMAL = "normal"      # Standard processing
    LOW = "low"            # Can wait


class IndustrialEvent(BaseModel):
    """
    A cross-module event in the Gringo Industrial OS
    """
    id: Optional[str] = None
    event_type: EventType
    priority: EventPriority = EventPriority.NORMAL

    # Source module
    source_module: str  # factoryfix, qualityfix, safetyfix, chatterfix
    source_id: Optional[str] = None  # machine_id, nc_id, incident_id, etc.

    # Event data
    title: str
    description: str
    data: Dict[str, Any] = {}

    # Metadata
    organization_id: str = "demo_org"
    user_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Processing status
    processed: bool = False
    processed_at: Optional[str] = None
    handlers_triggered: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "machine_down",
                "priority": "critical",
                "source_module": "factoryfix",
                "source_id": "machine_cnc_3",
                "title": "CNC Mill #3 went down",
                "description": "Machine stopped responding. Last temp: 92°C",
                "data": {"machine_id": "machine_cnc_3", "temperature": 92.0}
            }
        }


# Event handlers registry
_handlers: Dict[EventType, List[Callable]] = {}
_event_log: List[IndustrialEvent] = []


class EventBus:
    """
    The Nervous System - Pub/Sub event bus for cross-module communication

    Usage:
        # Subscribe to events
        @event_bus.subscribe(EventType.MACHINE_DOWN)
        async def handle_machine_down(event: IndustrialEvent):
            # Create work order in ChatterFix
            ...

        # Publish events
        await event_bus.publish(IndustrialEvent(
            event_type=EventType.MACHINE_DOWN,
            source_module="factoryfix",
            title="Machine stopped",
            ...
        ))
    """

    def __init__(self):
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.event_log: List[IndustrialEvent] = []
        self.max_log_size = 1000

    def subscribe(self, event_type: EventType):
        """Decorator to subscribe a handler to an event type"""
        def decorator(func: Callable):
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(func)
            logger.info(f"EventBus: Subscribed {func.__name__} to {event_type.value}")
            return func
        return decorator

    async def publish(self, event: IndustrialEvent):
        """Publish an event to all subscribers"""
        event.id = event.id or f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

        # Log event
        self.event_log.append(event)
        if len(self.event_log) > self.max_log_size:
            self.event_log = self.event_log[-self.max_log_size:]

        logger.info(f"EventBus: Publishing {event.event_type.value} from {event.source_module}")

        # Get handlers
        handlers = self.handlers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"EventBus: No handlers for {event.event_type.value}")
            return

        # Execute handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                event.handlers_triggered.append(handler.__name__)
            except Exception as e:
                logger.error(f"EventBus: Handler {handler.__name__} failed: {e}")

        event.processed = True
        event.processed_at = datetime.now(timezone.utc).isoformat()

    def get_recent_events(self, limit: int = 50, event_type: Optional[EventType] = None) -> List[IndustrialEvent]:
        """Get recent events from the log"""
        events = self.event_log

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]


# Global singleton
event_bus = EventBus()


# ============ Default Event Handlers (The Nervous System Wiring) ============

@event_bus.subscribe(EventType.MACHINE_DOWN)
async def handle_machine_down(event: IndustrialEvent):
    """
    FactoryFix -> ChatterFix
    Machine down triggers automatic work order
    """
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        work_order = {
            "title": f"[AUTO] {event.title}",
            "description": f"Auto-generated by Gringo Industrial OS.\n\n{event.description}\n\nSource: {event.source_module}\nEvent ID: {event.id}",
            "priority": "Critical" if event.priority == EventPriority.CRITICAL else "High",
            "status": "Open",
            "type": "Emergency",
            "organization_id": event.organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event.id,
            "source_module": event.source_module,
        }

        if event.data.get("machine_id"):
            work_order["source_machine_id"] = event.data["machine_id"]

        await db.create_document("work_orders", work_order)
        logger.info(f"EventBus: Created ChatterFix work order for {event.event_type.value}")

    except Exception as e:
        logger.error(f"EventBus: Failed to create work order: {e}")


@event_bus.subscribe(EventType.HIGH_REJECT_RATE)
async def handle_high_reject_rate(event: IndustrialEvent):
    """
    FactoryFix -> QualityFix
    High reject rate triggers quality investigation
    """
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        nc_record = {
            "source_type": "production_event",
            "source_event_id": event.id,
            "defect_type": "high_reject_rate",
            "description": event.description,
            "severity": "major",
            "organization_id": event.organization_id,
            "reported_at": datetime.now(timezone.utc).isoformat(),
            "capa_required": True,
            "production_run_id": event.data.get("run_id"),
            "machine_id": event.data.get("machine_id"),
        }

        await db.create_document("non_conformances", nc_record)
        logger.info(f"EventBus: Created QualityFix NC for {event.event_type.value}")

    except Exception as e:
        logger.error(f"EventBus: Failed to create NC: {e}")


@event_bus.subscribe(EventType.MAN_DOWN)
async def handle_man_down(event: IndustrialEvent):
    """
    SafetyFix -> ChatterFix
    Man down triggers emergency equipment check
    """
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        work_order = {
            "title": f"[SAFETY] Equipment Check - {event.title}",
            "description": f"SAFETY EVENT: Man down detected.\n\n{event.description}\n\nVerify all equipment in the area is safe:\n- Check ladder/scaffolding integrity\n- Inspect floor conditions\n- Review equipment guards\n\nEvent ID: {event.id}",
            "priority": "Critical",
            "status": "Open",
            "type": "Safety",
            "organization_id": event.organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event.id,
            "source_module": "safetyfix",
        }

        await db.create_document("work_orders", work_order)
        logger.info(f"EventBus: Created safety equipment check work order")

    except Exception as e:
        logger.error(f"EventBus: Failed to create safety work order: {e}")


@event_bus.subscribe(EventType.CRITICAL_DEFECT)
async def handle_critical_defect(event: IndustrialEvent):
    """
    QualityFix -> FactoryFix
    Critical defect triggers production stop alert
    """
    logger.warning(f"PRODUCTION ALERT: Critical defect detected - {event.description}")
    # In production: Send push notification, sound alarm, update production dashboard


@event_bus.subscribe(EventType.TEMPERATURE_ALERT)
async def handle_temperature_alert(event: IndustrialEvent):
    """
    FactoryFix -> ChatterFix
    Temperature threshold exceeded triggers PM work order
    """
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        work_order = {
            "title": f"[THERMAL] {event.title}",
            "description": f"Temperature threshold exceeded.\n\n{event.description}\n\nRecommended actions:\n- Check cooling system\n- Verify lubrication levels\n- Inspect filters\n\nEvent ID: {event.id}",
            "priority": "High",
            "status": "Open",
            "type": "Preventive",
            "organization_id": event.organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event.id,
        }

        await db.create_document("work_orders", work_order)
        logger.info(f"EventBus: Created thermal maintenance work order")

    except Exception as e:
        logger.error(f"EventBus: Failed to create thermal work order: {e}")


# ============ Helper Functions ============

async def emit_machine_down(machine_id: str, machine_name: str, reason: str, org_id: str = "demo_org"):
    """Helper to emit machine down event"""
    await event_bus.publish(IndustrialEvent(
        event_type=EventType.MACHINE_DOWN,
        priority=EventPriority.CRITICAL,
        source_module="factoryfix",
        source_id=machine_id,
        title=f"{machine_name} went down",
        description=reason,
        data={"machine_id": machine_id, "machine_name": machine_name},
        organization_id=org_id,
    ))


async def emit_high_rejects(run_id: str, machine_id: str, reject_count: int, org_id: str = "demo_org"):
    """Helper to emit high reject rate event"""
    await event_bus.publish(IndustrialEvent(
        event_type=EventType.HIGH_REJECT_RATE,
        priority=EventPriority.HIGH,
        source_module="factoryfix",
        source_id=run_id,
        title=f"High reject rate: {reject_count} rejects",
        description=f"Production run {run_id} has {reject_count} rejects. Quality investigation required.",
        data={"run_id": run_id, "machine_id": machine_id, "reject_count": reject_count},
        organization_id=org_id,
    ))


async def emit_man_down(user_id: str, user_name: str, location: str, org_id: str = "demo_org"):
    """Helper to emit man down event"""
    await event_bus.publish(IndustrialEvent(
        event_type=EventType.MAN_DOWN,
        priority=EventPriority.CRITICAL,
        source_module="safetyfix",
        source_id=user_id,
        title=f"Man down: {user_name}",
        description=f"Fall detected for {user_name} at {location}. Emergency response initiated.",
        data={"user_id": user_id, "user_name": user_name, "location": location},
        organization_id=org_id,
    ))


async def emit_temperature_alert(machine_id: str, machine_name: str, temp: float, threshold: float, org_id: str = "demo_org"):
    """Helper to emit temperature alert event"""
    await event_bus.publish(IndustrialEvent(
        event_type=EventType.TEMPERATURE_ALERT,
        priority=EventPriority.HIGH,
        source_module="factoryfix",
        source_id=machine_id,
        title=f"{machine_name} temperature alert",
        description=f"Temperature {temp}°C exceeded threshold {threshold}°C",
        data={"machine_id": machine_id, "temperature": temp, "threshold": threshold},
        organization_id=org_id,
    ))
