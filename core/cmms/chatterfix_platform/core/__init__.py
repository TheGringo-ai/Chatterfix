#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Core Infrastructure
Plugin registry, service discovery, and shared utilities
"""

from .plugin_registry import PluginRegistry
from .service_discovery import ServiceDiscovery
from .shared_services import SharedServices
from .event_system import EventSystem, SystemEvents
from .config_manager import ConfigManager

# Create global instances
plugin_registry = PluginRegistry()
service_discovery = ServiceDiscovery()
shared_services = SharedServices()
event_system = EventSystem()
config_manager = ConfigManager()

__all__ = [
    'PluginRegistry',
    'ServiceDiscovery', 
    'SharedServices',
    'EventSystem',
    'SystemEvents',
    'ConfigManager',
    'plugin_registry',
    'service_discovery',
    'shared_services',
    'event_system',
    'config_manager'
]