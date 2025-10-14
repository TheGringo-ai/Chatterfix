#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Unified API Gateway
Dynamic routing, middleware pipeline, and plugin integration
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import time
import json
from urllib.parse import urlparse
import re

# Import platform core
from platform.core import (
    PluginRegistry, ServiceDiscovery, SharedServices, 
    EventSystem, ConfigManager, plugin_registry, 
    service_discovery, shared_services, event_system, config_manager
)

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
        self.cleanup_task = None
    
    async def is_allowed(self, client_id: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """Check if request is allowed based on rate limits"""
        now = time.time()
        window_start = now - window_seconds
        
        # Clean up old entries
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    async def cleanup_old_entries(self):
        """Background task to clean up old rate limit entries"""
        while True:
            try:
                now = time.time()
                # Remove entries older than 1 hour
                cutoff = now - 3600
                
                for client_id in list(self.requests.keys()):
                    self.requests[client_id] = [
                        req_time for req_time in self.requests[client_id]
                        if req_time > cutoff
                    ]
                    
                    if not self.requests[client_id]:
                        del self.requests[client_id]
                
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Rate limiter cleanup error: {e}")
                await asyncio.sleep(60)

class MiddlewarePipeline:
    """Configurable middleware pipeline"""
    
    def __init__(self):
        self.middleware: List[Callable] = []
        self.rate_limiter = RateLimiter()
    
    def add_middleware(self, middleware_func: Callable):
        """Add middleware to the pipeline"""
        self.middleware.append(middleware_func)
    
    async def process_request(self, request: Request) -> Optional[JSONResponse]:
        """Process request through middleware pipeline"""
        for middleware in self.middleware:
            try:
                result = await middleware(request)
                if result is not None:  # Middleware returned a response, stop processing
                    return result
            except Exception as e:
                logger.error(f"Middleware error: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error in middleware"}
                )
        return None
    
    async def rate_limit_middleware(self, request: Request) -> Optional[JSONResponse]:
        """Rate limiting middleware"""
        if not config_manager.get("api_gateway.rate_limiting", True):
            return None
        
        client_ip = request.client.host
        max_requests = config_manager.get("api_gateway.rate_limit_requests", 100)
        window = config_manager.get("api_gateway.rate_limit_window", 60)
        
        if not await self.rate_limiter.is_allowed(client_ip, max_requests, window):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": window
                }
            )
        return None
    
    async def logging_middleware(self, request: Request) -> Optional[JSONResponse]:
        """Request logging middleware"""
        start_time = time.time()
        
        # Log the request
        logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
        
        # Store timing info for later use
        request.state.start_time = start_time
        return None
    
    async def auth_middleware(self, request: Request) -> Optional[JSONResponse]:
        """Authentication middleware for protected routes"""
        # Skip auth for health checks and public routes
        public_routes = ["/health", "/", "/docs", "/openapi.json", "/platform/status"]
        
        if request.url.path in public_routes or request.url.path.startswith("/static"):
            return None
        
        # Check for API key in headers
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing authorization header"}
            )
        
        # Simple API key validation (enhance with real auth service)
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid authorization format"}
            )
        
        # Store user info for downstream use
        request.state.user = {"authenticated": True}
        return None

class RouteManager:
    """Dynamic route management for plugins"""
    
    def __init__(self):
        self.routes: Dict[str, Dict[str, Any]] = {}
        self.patterns: List[Dict[str, Any]] = []
    
    def register_route(self, pattern: str, service_name: str, plugin_name: str = None, 
                     methods: List[str] = None, middleware: List[str] = None):
        """Register a route pattern"""
        if methods is None:
            methods = ["GET", "POST", "PUT", "DELETE"]
        if middleware is None:
            middleware = []
        
        route_info = {
            "pattern": pattern,
            "service_name": service_name,
            "plugin_name": plugin_name,
            "methods": methods,
            "middleware": middleware,
            "compiled_pattern": re.compile(pattern.replace("{", "(?P<").replace("}", ">[^/]+)") + "$")
        }
        
        self.patterns.append(route_info)
        logger.info(f"Registered route: {pattern} -> {service_name}")
    
    def find_route(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """Find matching route for path and method"""
        for route_info in self.patterns:
            if method in route_info["methods"]:
                match = route_info["compiled_pattern"].match(path)
                if match:
                    route_info["path_params"] = match.groupdict()
                    return route_info
        return None
    
    def get_all_routes(self) -> List[Dict[str, Any]]:
        """Get all registered routes"""
        return self.patterns.copy()

class PlatformGateway:
    """Main platform gateway class"""
    
    def __init__(self):
        self.app = FastAPI(
            title="ChatterFix AI Development Platform Gateway",
            description="Unified API Gateway for ChatterFix platform and plugins",
            version="1.0.0"
        )
        
        self.middleware_pipeline = MiddlewarePipeline()
        self.route_manager = RouteManager()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup core routes
        self._setup_core_routes()
        
        # Register core service routes
        self._register_core_routes()
        
        # Setup main gateway middleware
        self._setup_gateway_middleware()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware and custom pipeline"""
        
        # CORS middleware
        if config_manager.get("api_gateway.cors_enabled", True):
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Trusted host middleware for production
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )
        
        # Add custom middleware to pipeline
        self.middleware_pipeline.add_middleware(self.middleware_pipeline.rate_limit_middleware)
        self.middleware_pipeline.add_middleware(self.middleware_pipeline.logging_middleware)
        self.middleware_pipeline.add_middleware(self.middleware_pipeline.auth_middleware)
    
    def _setup_core_routes(self):
        """Setup core platform routes"""
        
        @self.app.get("/health")
        async def gateway_health():
            """Gateway health check"""
            return {
                "status": "healthy",
                "gateway": "ChatterFix Platform Gateway",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/platform/status")
        async def platform_status():
            """Complete platform status"""
            plugin_status = plugin_registry.get_all_plugins_status()
            service_metrics = await service_discovery.get_service_metrics()
            shared_health = await shared_services.health_check()
            
            return {
                "platform": {
                    "name": config_manager.get("platform.name"),
                    "version": config_manager.get("platform.version"),
                    "uptime": time.time() - getattr(self, 'start_time', time.time())
                },
                "plugins": plugin_status,
                "services": service_metrics,
                "shared_services": shared_health,
                "routes": len(self.route_manager.get_all_routes()),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/platform/plugins")
        async def list_plugins():
            """List all registered plugins"""
            return plugin_registry.get_all_plugins_status()
        
        @self.app.post("/platform/plugins/{plugin_name}/start")
        async def start_plugin(plugin_name: str):
            """Start a specific plugin"""
            success = await plugin_registry.start_plugin(plugin_name)
            return {"success": success, "plugin": plugin_name}
        
        @self.app.post("/platform/plugins/{plugin_name}/stop")
        async def stop_plugin(plugin_name: str):
            """Stop a specific plugin"""
            success = await plugin_registry.stop_plugin(plugin_name)
            return {"success": success, "plugin": plugin_name}
        
        @self.app.post("/platform/plugins/{plugin_name}/reload")
        async def reload_plugin(plugin_name: str):
            """Reload a specific plugin"""
            success = await plugin_registry.reload_plugin(plugin_name)
            return {"success": success, "plugin": plugin_name}
        
        @self.app.get("/platform/routes")
        async def list_routes():
            """List all registered routes"""
            return {
                "routes": self.route_manager.get_all_routes(),
                "count": len(self.route_manager.get_all_routes())
            }
        
        @self.app.get("/platform/config")
        async def get_platform_config():
            """Get platform configuration"""
            return config_manager.config
        
        @self.app.get("/")
        async def root():
            """Root endpoint with platform info"""
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ChatterFix AI Development Platform</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { color: #2c3e50; }
                    .status { background: #ecf0f1; padding: 20px; border-radius: 5px; }
                    .link { color: #3498db; text-decoration: none; }
                </style>
            </head>
            <body>
                <h1 class="header">ChatterFix AI Development Platform</h1>
                <div class="status">
                    <h3>Platform Gateway Active</h3>
                    <p>Unified API Gateway for ChatterFix CMMS and plugins</p>
                    <ul>
                        <li><a href="/docs" class="link">API Documentation</a></li>
                        <li><a href="/platform/status" class="link">Platform Status</a></li>
                        <li><a href="/platform/plugins" class="link">Plugins</a></li>
                        <li><a href="/platform/routes" class="link">Routes</a></li>
                    </ul>
                </div>
            </body>
            </html>
            """)
    
    def _register_core_routes(self):
        """Register routes for core ChatterFix services"""
        
        # Backend service routes
        self.route_manager.register_route(
            r"/api/database/.*",
            "backend_unified",
            methods=["GET", "POST", "PUT", "DELETE"]
        )
        self.route_manager.register_route(
            r"/api/work-orders/.*",
            "backend_unified",
            methods=["GET", "POST", "PUT", "DELETE"]
        )
        self.route_manager.register_route(
            r"/api/assets/.*",
            "backend_unified",
            methods=["GET", "POST", "PUT", "DELETE"]
        )
        self.route_manager.register_route(
            r"/api/parts/.*",
            "backend_unified",
            methods=["GET", "POST", "PUT", "DELETE"]
        )
        self.route_manager.register_route(
            r"/api/users/.*",
            "backend_unified",
            methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        # AI service routes
        self.route_manager.register_route(
            r"/api/ai/.*",
            "ai_unified",
            methods=["GET", "POST"]
        )
        
        # UI Gateway legacy routes (for backward compatibility)
        self.route_manager.register_route(
            r"/work-orders/.*",
            "ui_gateway",
            methods=["GET", "POST", "PUT", "DELETE"]
        )
        
    async def _proxy_request(self, request: Request, target_service: str, 
                           target_path: str = None) -> JSONResponse:
        """Proxy request to target service"""
        
        # Get service URL
        service_url = await service_discovery.get_service_url(target_service)
        if not service_url:
            return JSONResponse(
                status_code=503,
                content={"error": f"Service {target_service} not available"}
            )
        
        # Use original path if target_path not specified
        if target_path is None:
            target_path = request.url.path
        
        # Build target URL
        target_url = f"{service_url}{target_path}"
        if request.url.query:
            target_url += f"?{request.url.query}"
        
        try:
            # Forward request
            if request.method == "GET":
                response = await self.client.get(target_url, headers=dict(request.headers))
            elif request.method == "POST":
                body = await request.body()
                response = await self.client.post(target_url, content=body, headers=dict(request.headers))
            elif request.method == "PUT":
                body = await request.body()
                response = await self.client.put(target_url, content=body, headers=dict(request.headers))
            elif request.method == "DELETE":
                response = await self.client.delete(target_url, headers=dict(request.headers))
            else:
                return JSONResponse(
                    status_code=405,
                    content={"error": f"Method {request.method} not allowed"}
                )
            
            # Return response
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text}
            )
            
        except Exception as e:
            logger.error(f"Proxy request failed: {e}")
            return JSONResponse(
                status_code=502,
                content={"error": "Bad gateway", "details": str(e)}
            )
    
    def _setup_gateway_middleware(self):
        """Setup the main gateway middleware"""
        
        @self.app.middleware("http")
        async def gateway_middleware(request: Request, call_next):
            """Main gateway middleware for routing and processing"""
            
            # Process through custom middleware pipeline
            middleware_response = await self.middleware_pipeline.process_request(request)
            if middleware_response:
                return middleware_response
            
            # Try to find matching route
            route_info = self.route_manager.find_route(request.url.path, request.method)
            
            if route_info:
                # Route found, proxy to service
                response = await self._proxy_request(
                    request, 
                    route_info["service_name"],
                    request.url.path
                )
                
                # Log response time
                if hasattr(request.state, 'start_time'):
                    duration = time.time() - request.state.start_time
                    logger.info(f"Response: {response.status_code} in {duration:.3f}s")
                
                return response
            
            # No route found, continue to FastAPI handlers
            response = await call_next(request)
            
            # Log response time for FastAPI routes
            if hasattr(request.state, 'start_time'):
                duration = time.time() - request.state.start_time
                logger.info(f"Response: {response.status_code} in {duration:.3f}s")
            
            return response
    
    async def startup(self):
        """Platform startup sequence"""
        self.start_time = time.time()
        
        logger.info("Starting ChatterFix AI Development Platform Gateway")
        
        # Start core services
        await service_discovery.start_monitoring()
        await event_system.start_processing()
        
        # Discover and start plugins
        plugins = await plugin_registry.discover_plugins()
        logger.info(f"Discovered {len(plugins)} plugins")
        
        # Register plugins
        for plugin in plugins:
            await plugin_registry.register_plugin(plugin)
        
        # Start enabled plugins
        start_results = await plugin_registry.start_all_plugins()
        successful_starts = sum(1 for success in start_results.values() if success)
        logger.info(f"Started {successful_starts}/{len(start_results)} plugins")
        
        # Register plugin routes
        await self._register_plugin_routes()
        
        # Start rate limiter cleanup
        asyncio.create_task(self.middleware_pipeline.rate_limiter.cleanup_old_entries())
        
        logger.info("Platform gateway startup complete")
    
    async def shutdown(self):
        """Platform shutdown sequence"""
        logger.info("Shutting down ChatterFix AI Development Platform Gateway")
        
        # Stop plugins
        for plugin_name in plugin_registry.get_running_plugins():
            await plugin_registry.stop_plugin(plugin_name)
        
        # Stop core services
        await event_system.stop_processing()
        await service_discovery.stop_monitoring()
        
        # Close HTTP client
        await self.client.aclose()
        
        logger.info("Platform gateway shutdown complete")
    
    async def _register_plugin_routes(self):
        """Register routes for all running plugins"""
        plugin_routes = plugin_registry.get_plugin_routes()
        
        for plugin_name, routes in plugin_routes.items():
            for route in routes:
                self.route_manager.register_route(
                    route,
                    plugin_name,
                    plugin_name=plugin_name
                )

# Create gateway instance
gateway = PlatformGateway()
app = gateway.app

# Add startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await gateway.startup()

@app.on_event("shutdown") 
async def shutdown_event():
    await gateway.shutdown()

if __name__ == "__main__":
    import uvicorn
    
    host = config_manager.get("api_gateway.host", "0.0.0.0")
    port = config_manager.get("api_gateway.port", 8000)
    
    uvicorn.run(app, host=host, port=port)