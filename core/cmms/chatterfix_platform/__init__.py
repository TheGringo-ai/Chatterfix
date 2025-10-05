#!/usr/bin/env python3
"""
ChatterFix AI Development Platform
Plugin architecture and unified service framework
"""

__version__ = "1.0.0"
__author__ = "ChatterFix AI"
__description__ = "Modular AI development platform with CMMS integration"

# Import core modules for easy access
from .core import (
    PluginRegistry, ServiceDiscovery, SharedServices, 
    EventSystem, ConfigManager, plugin_registry, 
    service_discovery, shared_services, event_system, config_manager
)

__all__ = [
    'PluginRegistry',
    'ServiceDiscovery', 
    'SharedServices',
    'EventSystem',
    'ConfigManager',
    'plugin_registry',
    'service_discovery',
    'shared_services',
    'event_system',
    'config_manager'
]