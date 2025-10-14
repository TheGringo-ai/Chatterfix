#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Plugin Registry
Manages plugin discovery, loading, and lifecycle
"""

import os
import json
import logging
import importlib
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PluginMetadata:
    """Plugin metadata structure"""
    name: str
    version: str
    description: str
    author: str
    app_type: str  # ai_service, web_app, api, microservice
    dependencies: List[str]
    routes: List[str]
    permissions: List[str]
    enabled: bool = True
    auto_start: bool = True
    port: Optional[int] = None
    health_endpoint: str = "/health"
    config_schema: Optional[Dict] = None
    created_at: str = ""
    updated_at: str = ""

@dataclass
class PluginInstance:
    """Runtime plugin instance"""
    metadata: PluginMetadata
    module: Any
    app: Any = None
    status: str = "stopped"  # stopped, starting, running, error
    error_message: str = ""
    last_heartbeat: Optional[datetime] = None

class PluginRegistry:
    """Central registry for all ChatterFix platform plugins"""
    
    def __init__(self, plugins_dir: str = "platform/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.registry: Dict[str, PluginInstance] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.middleware_stack: List[Callable] = []
        
        # Ensure plugins directory exists
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
    async def discover_plugins(self) -> List[PluginMetadata]:
        """Discover all plugins in the plugins directory"""
        plugins = []
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                manifest_path = plugin_dir / "plugin.json"
                
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest_data = json.load(f)
                            
                        metadata = PluginMetadata(**manifest_data)
                        plugins.append(metadata)
                        logger.info(f"Discovered plugin: {metadata.name} v{metadata.version}")
                        
                    except Exception as e:
                        logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")
                        
        return plugins
    
    async def register_plugin(self, metadata: PluginMetadata) -> bool:
        """Register a plugin with the registry"""
        try:
            # Load the plugin module
            plugin_path = self.plugins_dir / metadata.name
            spec = importlib.util.spec_from_file_location(
                f"plugin_{metadata.name}", 
                plugin_path / "main.py"
            )
            
            if spec is None:
                raise Exception(f"Could not load plugin spec for {metadata.name}")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create plugin instance
            instance = PluginInstance(
                metadata=metadata,
                module=module,
                status="stopped"
            )
            
            self.registry[metadata.name] = instance
            logger.info(f"Registered plugin: {metadata.name}")
            
            # Execute plugin hooks
            await self._execute_hook("plugin_registered", metadata.name, instance)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {metadata.name}: {e}")
            return False
    
    async def start_plugin(self, plugin_name: str) -> bool:
        """Start a specific plugin"""
        if plugin_name not in self.registry:
            logger.error(f"Plugin {plugin_name} not found in registry")
            return False
            
        instance = self.registry[plugin_name]
        
        try:
            instance.status = "starting"
            
            # Call plugin's start method if it exists
            if hasattr(instance.module, 'start'):
                await instance.module.start()
            
            # Initialize FastAPI app if plugin has one
            if hasattr(instance.module, 'app'):
                instance.app = instance.module.app
                
            instance.status = "running"
            instance.last_heartbeat = datetime.now()
            
            logger.info(f"Started plugin: {plugin_name}")
            await self._execute_hook("plugin_started", plugin_name, instance)
            
            return True
            
        except Exception as e:
            instance.status = "error"
            instance.error_message = str(e)
            logger.error(f"Failed to start plugin {plugin_name}: {e}")
            return False
    
    async def stop_plugin(self, plugin_name: str) -> bool:
        """Stop a specific plugin"""
        if plugin_name not in self.registry:
            return False
            
        instance = self.registry[plugin_name]
        
        try:
            # Call plugin's stop method if it exists
            if hasattr(instance.module, 'stop'):
                await instance.module.stop()
                
            instance.status = "stopped"
            instance.app = None
            
            logger.info(f"Stopped plugin: {plugin_name}")
            await self._execute_hook("plugin_stopped", plugin_name, instance)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop plugin {plugin_name}: {e}")
            return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin (stop, unregister, discover, register, start)"""
        if plugin_name in self.registry:
            await self.stop_plugin(plugin_name)
            del self.registry[plugin_name]
            
        # Rediscover and register
        plugins = await self.discover_plugins()
        for plugin in plugins:
            if plugin.name == plugin_name:
                if await self.register_plugin(plugin):
                    return await self.start_plugin(plugin_name)
                    
        return False
    
    async def start_all_plugins(self) -> Dict[str, bool]:
        """Start all enabled plugins"""
        results = {}
        
        # Sort by dependencies (simple topological sort)
        sorted_plugins = self._sort_by_dependencies()
        
        for plugin_name in sorted_plugins:
            instance = self.registry[plugin_name]
            if instance.metadata.enabled and instance.metadata.auto_start:
                results[plugin_name] = await self.start_plugin(plugin_name)
                
        return results
    
    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a plugin"""
        if plugin_name not in self.registry:
            return None
            
        instance = self.registry[plugin_name]
        return {
            "name": plugin_name,
            "status": instance.status,
            "error_message": instance.error_message,
            "last_heartbeat": instance.last_heartbeat.isoformat() if instance.last_heartbeat else None,
            "metadata": asdict(instance.metadata)
        }
    
    def get_all_plugins_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered plugins"""
        return {
            name: self.get_plugin_status(name) 
            for name in self.registry.keys()
        }
    
    def get_running_plugins(self) -> List[str]:
        """Get list of currently running plugin names"""
        return [
            name for name, instance in self.registry.items()
            if instance.status == "running"
        ]
    
    def get_plugin_routes(self) -> Dict[str, List[str]]:
        """Get all routes exposed by running plugins"""
        routes = {}
        for name, instance in self.registry.items():
            if instance.status == "running" and instance.metadata.routes:
                routes[name] = instance.metadata.routes
        return routes
    
    def register_hook(self, event: str, callback: Callable):
        """Register a hook for plugin events"""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(callback)
    
    async def _execute_hook(self, event: str, *args, **kwargs):
        """Execute all hooks for an event"""
        if event in self.hooks:
            for callback in self.hooks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(*args, **kwargs)
                    else:
                        callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Hook execution failed for {event}: {e}")
    
    def _sort_by_dependencies(self) -> List[str]:
        """Simple topological sort based on plugin dependencies"""
        sorted_list = []
        visited = set()
        temp_visited = set()
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                # Circular dependency detected
                logger.warning(f"Circular dependency detected involving {plugin_name}")
                return
                
            if plugin_name in visited:
                return
                
            temp_visited.add(plugin_name)
            
            if plugin_name in self.registry:
                for dep in self.registry[plugin_name].metadata.dependencies:
                    if dep in self.registry:
                        visit(dep)
                        
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            sorted_list.append(plugin_name)
        
        for plugin_name in self.registry.keys():
            visit(plugin_name)
            
        return sorted_list

# Global plugin registry instance
plugin_registry = PluginRegistry()