#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Event System
Enables inter-app communication and event-driven architecture
"""

import asyncio
import logging
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from enum import Enum

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Event:
    """Event structure for the platform"""
    name: str
    data: Dict[str, Any]
    source: str
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EventHandler:
    """Event handler wrapper"""
    
    def __init__(self, callback: Callable, priority: int = 0, once: bool = False):
        self.callback = callback
        self.priority = priority  # Higher priority handlers run first
        self.once = once
        self.executed = False

class EventSystem:
    """Event-driven communication system for platform plugins"""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.event_history: List[Event] = []
        self.max_history = 1000
        
    def subscribe(self, event_name: str, callback: Callable, priority: int = 0, once: bool = False):
        """Subscribe to an event"""
        if event_name not in self.handlers:
            self.handlers[event_name] = []
            
        handler = EventHandler(callback, priority, once)
        self.handlers[event_name].append(handler)
        
        # Sort handlers by priority (highest first)
        self.handlers[event_name].sort(key=lambda h: h.priority, reverse=True)
        
        logger.debug(f"Subscribed to event '{event_name}' with priority {priority}")
        
    def unsubscribe(self, event_name: str, callback: Callable):
        """Unsubscribe from an event"""
        if event_name in self.handlers:
            self.handlers[event_name] = [
                h for h in self.handlers[event_name] 
                if h.callback != callback
            ]
            
            if not self.handlers[event_name]:
                del self.handlers[event_name]
                
        logger.debug(f"Unsubscribed from event '{event_name}'")
    
    async def emit(self, event_name: str, data: Dict[str, Any] = None, 
                   source: str = "unknown", priority: EventPriority = EventPriority.NORMAL,
                   correlation_id: Optional[str] = None):
        """Emit an event"""
        if data is None:
            data = {}
            
        event = Event(
            name=event_name,
            data=data,
            source=source,
            priority=priority,
            correlation_id=correlation_id
        )
        
        # Add to event queue for processing
        await self.event_queue.put(event)
        
        # Add to history
        self._add_to_history(event)
        
        logger.debug(f"Emitted event '{event_name}' from '{source}'")
    
    async def emit_sync(self, event_name: str, data: Dict[str, Any] = None,
                       source: str = "unknown", priority: EventPriority = EventPriority.NORMAL,
                       correlation_id: Optional[str] = None):
        """Emit an event synchronously (blocks until all handlers complete)"""
        if data is None:
            data = {}
            
        event = Event(
            name=event_name,
            data=data,
            source=source,
            priority=priority,
            correlation_id=correlation_id
        )
        
        await self._process_event(event)
        self._add_to_history(event)
        
        logger.debug(f"Emitted synchronous event '{event_name}' from '{source}'")
    
    async def start_processing(self):
        """Start the event processing background task"""
        if self.processing_task is None or self.processing_task.done():
            self.processing_task = asyncio.create_task(self._event_processor())
            logger.info("Started event processing")
    
    async def stop_processing(self):
        """Stop the event processing"""
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped event processing")
    
    async def _event_processor(self):
        """Background task for processing events"""
        while True:
            try:
                # Process events in priority order
                events_to_process = []
                
                # Collect events from queue
                while not self.event_queue.empty():
                    event = await self.event_queue.get()
                    events_to_process.append(event)
                
                # Sort by priority (critical first)
                events_to_process.sort(key=lambda e: e.priority.value, reverse=True)
                
                # Process events
                for event in events_to_process:
                    await self._process_event(event)
                
                # Wait for new events if none are pending
                if not events_to_process:
                    event = await self.event_queue.get()
                    await self._process_event(event)
                    
            except asyncio.CancelledError:
                logger.info("Event processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        if event.name not in self.handlers:
            logger.debug(f"No handlers for event '{event.name}'")
            return
            
        handlers_to_remove = []
        
        for handler in self.handlers[event.name]:
            try:
                # Skip if this is a 'once' handler that has already executed
                if handler.once and handler.executed:
                    handlers_to_remove.append(handler)
                    continue
                
                # Execute handler
                if asyncio.iscoroutinefunction(handler.callback):
                    await handler.callback(event)
                else:
                    handler.callback(event)
                
                # Mark as executed for 'once' handlers
                if handler.once:
                    handler.executed = True
                    handlers_to_remove.append(handler)
                    
            except Exception as e:
                logger.error(f"Error executing handler for event '{event.name}': {e}")
        
        # Remove 'once' handlers that have executed
        for handler in handlers_to_remove:
            if handler in self.handlers[event.name]:
                self.handlers[event.name].remove(handler)
        
        logger.debug(f"Processed event '{event.name}' with {len(self.handlers[event.name])} handlers")
    
    def _add_to_history(self, event: Event):
        """Add event to history with size limit"""
        self.event_history.append(event)
        
        # Maintain maximum history size
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
    
    def get_event_history(self, event_name: Optional[str] = None, 
                         source: Optional[str] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history with optional filtering"""
        events = self.event_history
        
        # Filter by event name
        if event_name:
            events = [e for e in events if e.name == event_name]
        
        # Filter by source
        if source:
            events = [e for e in events if e.source == source]
        
        # Limit results
        events = events[-limit:]
        
        # Convert to serializable format
        return [
            {
                "name": e.name,
                "data": e.data,
                "source": e.source,
                "priority": e.priority.name,
                "timestamp": e.timestamp.isoformat(),
                "correlation_id": e.correlation_id
            }
            for e in events
        ]
    
    def get_active_handlers(self) -> Dict[str, int]:
        """Get count of active handlers for each event"""
        return {
            event_name: len(handlers)
            for event_name, handlers in self.handlers.items()
        }
    
    def clear_handlers(self, event_name: Optional[str] = None):
        """Clear all handlers for an event or all events"""
        if event_name:
            if event_name in self.handlers:
                del self.handlers[event_name]
                logger.info(f"Cleared handlers for event '{event_name}'")
        else:
            self.handlers.clear()
            logger.info("Cleared all event handlers")
    
    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()
        logger.info("Cleared event history")

# Pre-defined system events for the ChatterFix platform
class SystemEvents:
    """Standard system events"""
    PLUGIN_REGISTERED = "system.plugin.registered"
    PLUGIN_STARTED = "system.plugin.started"
    PLUGIN_STOPPED = "system.plugin.stopped"
    PLUGIN_ERROR = "system.plugin.error"
    
    SERVICE_HEALTHY = "system.service.healthy"
    SERVICE_UNHEALTHY = "system.service.unhealthy"
    SERVICE_REGISTERED = "system.service.registered"
    SERVICE_UNREGISTERED = "system.service.unregistered"
    
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    
    WORK_ORDER_CREATED = "cmms.work_order.created"
    WORK_ORDER_UPDATED = "cmms.work_order.updated"
    WORK_ORDER_COMPLETED = "cmms.work_order.completed"
    
    ASSET_CREATED = "cmms.asset.created"
    ASSET_UPDATED = "cmms.asset.updated"
    ASSET_MAINTENANCE_DUE = "cmms.asset.maintenance_due"
    
    AI_ANALYSIS_COMPLETED = "ai.analysis.completed"
    AI_PREDICTION_GENERATED = "ai.prediction.generated"

# Global event system instance
event_system = EventSystem()