#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Service Discovery
Dynamic service registration and discovery with health monitoring
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class ServiceEndpoint:
    """Service endpoint information"""
    name: str
    url: str
    port: int
    health_endpoint: str = "/health"
    version: str = "1.0.0"
    status: str = "unknown"  # healthy, unhealthy, unknown
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ServiceDiscovery:
    """Service discovery and health monitoring system"""
    
    def __init__(self, check_interval: int = 30):
        self.services: Dict[str, ServiceEndpoint] = {}
        self.check_interval = check_interval
        self.monitoring_task: Optional[asyncio.Task] = None
        self.client = httpx.AsyncClient(timeout=5.0)
        
        # Register core ChatterFix services
        self._register_core_services()
    
    def _register_core_services(self):
        """Register the core ChatterFix services"""
        core_services = [
            ServiceEndpoint(
                name="backend_unified",
                url="http://localhost:8088",
                port=8088,
                health_endpoint="/health",
                version="2.1.0",
                metadata={"service_type": "backend", "core": True}
            ),
            ServiceEndpoint(
                name="ai_unified", 
                url="http://localhost:8089",
                port=8089,
                health_endpoint="/health",
                version="2.1.0",
                metadata={"service_type": "ai", "core": True}
            ),
            ServiceEndpoint(
                name="ui_gateway",
                url="http://localhost:8090", 
                port=8090,
                health_endpoint="/health",
                version="2.1.0",
                metadata={"service_type": "gateway", "core": True}
            )
        ]
        
        for service in core_services:
            self.services[service.name] = service
            logger.info(f"Registered core service: {service.name} at {service.url}")
    
    async def register_service(self, service: ServiceEndpoint) -> bool:
        """Register a new service"""
        try:
            self.services[service.name] = service
            logger.info(f"Registered service: {service.name} at {service.url}")
            
            # Perform immediate health check
            await self._check_service_health(service.name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {service.name}: {e}")
            return False
    
    async def unregister_service(self, service_name: str) -> bool:
        """Unregister a service"""
        if service_name in self.services:
            service = self.services[service_name]
            
            # Don't allow unregistering core services
            if service.metadata.get("core", False):
                logger.warning(f"Cannot unregister core service: {service_name}")
                return False
                
            del self.services[service_name]
            logger.info(f"Unregistered service: {service_name}")
            return True
            
        return False
    
    async def discover_services(self, service_type: Optional[str] = None) -> List[ServiceEndpoint]:
        """Discover all services or services of a specific type"""
        services = list(self.services.values())
        
        if service_type:
            services = [
                s for s in services 
                if s.metadata.get("service_type") == service_type
            ]
            
        return services
    
    async def get_service(self, service_name: str) -> Optional[ServiceEndpoint]:
        """Get a specific service by name"""
        return self.services.get(service_name)
    
    async def get_healthy_services(self) -> List[ServiceEndpoint]:
        """Get all healthy services"""
        return [
            service for service in self.services.values()
            if service.status == "healthy"
        ]
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Get URL for a specific service"""
        service = self.services.get(service_name)
        return service.url if service and service.status == "healthy" else None
    
    async def load_balance_service(self, service_type: str) -> Optional[ServiceEndpoint]:
        """Simple round-robin load balancing for service type"""
        healthy_services = [
            s for s in self.services.values()
            if s.status == "healthy" and s.metadata.get("service_type") == service_type
        ]
        
        if not healthy_services:
            return None
            
        # Simple round-robin (could be enhanced with weighted balancing)
        import random
        return random.choice(healthy_services)
    
    async def start_monitoring(self):
        """Start the health monitoring background task"""
        if self.monitoring_task is None or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self._health_monitor_loop())
            logger.info("Started service health monitoring")
    
    async def stop_monitoring(self):
        """Stop the health monitoring"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped service health monitoring")
    
    async def _health_monitor_loop(self):
        """Background task for monitoring service health"""
        while True:
            try:
                tasks = [
                    self._check_service_health(name)
                    for name in self.services.keys()
                ]
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Health monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _check_service_health(self, service_name: str):
        """Check health of a specific service"""
        if service_name not in self.services:
            return
            
        service = self.services[service_name]
        start_time = datetime.now()
        
        try:
            health_url = f"{service.url}{service.health_endpoint}"
            response = await self.client.get(health_url)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                service.status = "healthy"
                service.response_time = response_time
                logger.debug(f"Service {service_name} is healthy ({response_time:.3f}s)")
            else:
                service.status = "unhealthy"
                logger.warning(f"Service {service_name} returned status {response.status_code}")
                
        except Exception as e:
            service.status = "unhealthy"
            service.response_time = None
            logger.warning(f"Service {service_name} health check failed: {e}")
            
        service.last_check = datetime.now()
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics"""
        total_services = len(self.services)
        healthy_services = len([s for s in self.services.values() if s.status == "healthy"])
        unhealthy_services = len([s for s in self.services.values() if s.status == "unhealthy"])
        
        avg_response_time = None
        response_times = [
            s.response_time for s in self.services.values() 
            if s.response_time is not None
        ]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "availability_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
            "average_response_time": avg_response_time,
            "last_updated": datetime.now().isoformat(),
            "services": {
                name: {
                    "status": service.status,
                    "last_check": service.last_check.isoformat() if service.last_check else None,
                    "response_time": service.response_time,
                    "url": service.url
                }
                for name, service in self.services.items()
            }
        }
    
    def export_service_registry(self) -> Dict[str, Any]:
        """Export current service registry for backup/restore"""
        return {
            "services": {
                name: asdict(service) 
                for name, service in self.services.items()
            },
            "exported_at": datetime.now().isoformat()
        }
    
    async def import_service_registry(self, registry_data: Dict[str, Any]) -> bool:
        """Import service registry from backup"""
        try:
            for name, service_data in registry_data.get("services", {}).items():
                # Convert datetime strings back to datetime objects
                if service_data.get("last_check"):
                    service_data["last_check"] = datetime.fromisoformat(service_data["last_check"])
                
                service = ServiceEndpoint(**service_data)
                self.services[name] = service
            
            logger.info(f"Imported {len(registry_data.get('services', {}))} services")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import service registry: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_monitoring()
        await self.client.aclose()

# Global service discovery instance  
service_discovery = ServiceDiscovery()