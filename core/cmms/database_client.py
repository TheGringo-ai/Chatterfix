#!/usr/bin/env python3
"""
ChatterFix CMMS - Database Client
HTTP client for communicating with the database microservice.

This module provides a clean interface for the main application to interact
with the database service without direct database connections.
"""

import httpx
import logging
import os
import asyncio
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class DatabaseClientConfig:
    """Configuration for database client"""
    base_url: str
    timeout: float = 30.0
    retries: int = 3
    retry_delay: float = 1.0

class DatabaseClientError(Exception):
    """Custom exception for database client errors"""
    pass

class DatabaseClient:
    """
    HTTP client for communicating with the database microservice.
    
    Provides the same interface as the direct database manager but routes
    calls through HTTP to the database service.
    """
    
    def __init__(self, config: Optional[DatabaseClientConfig] = None):
        """Initialize the database client"""
        self.config = config or self._auto_detect_config()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
        logger.info(f"Database client initialized for {self.config.base_url}")
    
    def _auto_detect_config(self) -> DatabaseClientConfig:
        """Auto-detect database service configuration"""
        # Check for database service URL in environment
        db_service_url = os.getenv("DATABASE_SERVICE_URL")
        
        if not db_service_url:
            # Default to local service for development
            db_service_url = "http://localhost:8081"  # Different port from main app
            
        return DatabaseClientConfig(base_url=db_service_url)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database service health"""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise DatabaseClientError(f"Health check failed: {e}")
    
    async def execute_query(self, 
                           query: str, 
                           params: Union[tuple, list, dict] = (), 
                           fetch: Optional[str] = 'one') -> Any:
        """
        Execute a query via the database service.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: 'one', 'all', 'many', or None
            
        Returns:
            Query result
        """
        try:
            request_data = {
                "query": query,
                "params": list(params) if isinstance(params, tuple) else params,
                "fetch": fetch
            }
            
            response = await self.client.post("/api/query", json=request_data)
            response.raise_for_status()
            result = response.json()
            
            if not result["success"]:
                raise DatabaseClientError(result.get("error", "Query failed"))
            
            return result["data"]
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during query: {e}")
            raise DatabaseClientError(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseClientError(f"Query failed: {e}")
    
    # Work Orders methods
    async def get_work_orders(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get work orders from database service"""
        try:
            response = await self.client.get(f"/api/work-orders?limit={limit}&offset={offset}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get work orders: {e}")
            raise DatabaseClientError(f"Failed to get work orders: {e}")
    
    async def get_work_order(self, work_order_id: int) -> Dict:
        """Get a specific work order"""
        try:
            response = await self.client.get(f"/api/work-orders/{work_order_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise DatabaseClientError(f"Failed to get work order: {e}")
        except Exception as e:
            logger.error(f"Failed to get work order {work_order_id}: {e}")
            raise DatabaseClientError(f"Failed to get work order: {e}")
    
    async def create_work_order(self, work_order_data: Dict) -> Dict:
        """Create a new work order"""
        try:
            response = await self.client.post("/api/work-orders", json=work_order_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create work order: {e}")
            raise DatabaseClientError(f"Failed to create work order: {e}")
    
    # Assets methods
    async def get_assets(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get assets from database service"""
        try:
            response = await self.client.get(f"/api/assets?limit={limit}&offset={offset}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get assets: {e}")
            raise DatabaseClientError(f"Failed to get assets: {e}")
    
    async def create_asset(self, asset_data: Dict) -> Dict:
        """Create a new asset"""
        try:
            response = await self.client.post("/api/assets", json=asset_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create asset: {e}")
            raise DatabaseClientError(f"Failed to create asset: {e}")
    
    # Users methods
    async def get_users(self) -> List[Dict]:
        """Get users from database service"""
        try:
            response = await self.client.get("/api/users")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise DatabaseClientError(f"Failed to get users: {e}")
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get a specific user"""
        try:
            response = await self.client.get(f"/api/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise DatabaseClientError(f"Failed to get user: {e}")
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise DatabaseClientError(f"Failed to get user: {e}")
    
    # Parts methods
    async def get_parts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get parts from database service"""
        try:
            response = await self.client.get(f"/api/parts?limit={limit}&offset={offset}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get parts: {e}")
            raise DatabaseClientError(f"Failed to get parts: {e}")
    
    # Statistics methods
    async def get_overview_stats(self) -> Dict:
        """Get overview statistics"""
        try:
            response = await self.client.get("/api/stats/overview")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get overview stats: {e}")
            raise DatabaseClientError(f"Failed to get overview stats: {e}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Synchronous wrapper for backward compatibility
class SyncDatabaseClient:
    """Synchronous wrapper for the async database client"""
    
    def __init__(self, config: Optional[DatabaseClientConfig] = None):
        self.async_client = DatabaseClient(config)
    
    def _run_async(self, coro):
        """Run an async function synchronously"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task and wait for it
                import asyncio
                task = asyncio.create_task(coro)
                # Use a new thread to run the coroutine
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(coro)
    
    def health_check(self) -> Dict[str, Any]:
        return self._run_async(self.async_client.health_check())
    
    def execute_query(self, query: str, params=(), fetch='one') -> Any:
        return self._run_async(self.async_client.execute_query(query, params, fetch))
    
    def get_work_orders(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._run_async(self.async_client.get_work_orders(limit, offset))
    
    def get_work_order(self, work_order_id: int) -> Optional[Dict]:
        return self._run_async(self.async_client.get_work_order(work_order_id))
    
    def create_work_order(self, work_order_data: Dict) -> Dict:
        return self._run_async(self.async_client.create_work_order(work_order_data))
    
    def get_assets(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._run_async(self.async_client.get_assets(limit, offset))
    
    def create_asset(self, asset_data: Dict) -> Dict:
        return self._run_async(self.async_client.create_asset(asset_data))
    
    def get_users(self) -> List[Dict]:
        return self._run_async(self.async_client.get_users())
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        return self._run_async(self.async_client.get_user(user_id))
    
    def get_parts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._run_async(self.async_client.get_parts(limit, offset))
    
    def get_overview_stats(self) -> Dict:
        return self._run_async(self.async_client.get_overview_stats())

# Global client instance for backward compatibility
db_client = SyncDatabaseClient()

# Convenience functions
def get_database_client() -> SyncDatabaseClient:
    """Get the global database client instance"""
    return db_client

def check_database_health() -> Dict[str, Any]:
    """Check database health via the client"""
    return db_client.health_check()