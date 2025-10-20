#!/usr/bin/env python3
"""
ChatterFix CMMS - Performance Optimization Module
Implements Redis caching, connection pooling, and async operations
"""

import redis.asyncio as redis
import asyncpg
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from contextlib import asynccontextmanager
import uvicorn
import os
import json
from typing import Optional, Dict, Any
import time
from datetime import datetime, timedelta

# Performance configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/cmms")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

class PerformanceOptimizer:
    """High-performance database and caching layer"""
    
    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.performance_metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0,
            "db_connections": 0
        }
    
    async def initialize(self):
        """Initialize Redis and PostgreSQL connections"""
        # Redis connection
        self.redis_client = await redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
        
        # PostgreSQL connection pool
        self.db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        print("✅ Performance optimization layer initialized")
    
    async def get_cached(self, key: str) -> Optional[Dict]:
        """Get data from Redis cache"""
        try:
            start_time = time.time()
            cached_data = await self.redis_client.get(key)
            
            if cached_data:
                self.performance_metrics["cache_hits"] += 1
                response_time = (time.time() - start_time) * 1000
                print(f"🎯 Cache HIT for '{key}' - {response_time:.2f}ms")
                return json.loads(cached_data)
            else:
                self.performance_metrics["cache_misses"] += 1
                print(f"❌ Cache MISS for '{key}'")
                return None
        except Exception as e:
            print(f"Cache error: {e}")
            return None
    
    async def set_cached(self, key: str, data: Dict, ttl: int = CACHE_TTL):
        """Set data in Redis cache"""
        try:
            await self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(data, default=str)
            )
            print(f"💾 Cached '{key}' for {ttl}s")
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def execute_query(self, query: str, *args) -> list:
        """Execute database query with connection pooling"""
        start_time = time.time()
        
        async with self.db_pool.acquire() as connection:
            self.performance_metrics["db_connections"] += 1
            result = await connection.fetch(query, *args)
            
            response_time = (time.time() - start_time) * 1000
            self.performance_metrics["avg_response_time"] = (
                self.performance_metrics["avg_response_time"] + response_time
            ) / 2
            
            print(f"🔍 DB Query executed in {response_time:.2f}ms")
            return [dict(row) for row in result]
    
    async def cached_work_orders(self) -> list:
        """Get work orders with caching"""
        cache_key = "work_orders:all"
        
        # Try cache first
        cached = await self.get_cached(cache_key)
        if cached:
            return cached
        
        # Fetch from database
        query = """
        SELECT id, title, description, status, priority, 
               created_at, technician, due_date
        FROM work_orders 
        ORDER BY created_at DESC 
        LIMIT 100
        """
        
        work_orders = await self.execute_query(query)
        
        # Cache the results
        await self.set_cached(cache_key, work_orders, ttl=180)  # 3 minutes
        
        return work_orders
    
    async def cached_assets(self, location_id: Optional[int] = None) -> list:
        """Get assets with caching"""
        cache_key = f"assets:location:{location_id or 'all'}"
        
        cached = await self.get_cached(cache_key)
        if cached:
            return cached
        
        if location_id:
            query = "SELECT * FROM assets WHERE location_id = $1"
            assets = await self.execute_query(query, location_id)
        else:
            query = "SELECT * FROM assets ORDER BY name"
            assets = await self.execute_query(query)
        
        await self.set_cached(cache_key, assets, ttl=600)  # 10 minutes
        return assets
    
    async def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                print(f"🗑️ Invalidated {len(keys)} cache entries")
        except Exception as e:
            print(f"Cache invalidation error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_total = self.performance_metrics["cache_hits"] + self.performance_metrics["cache_misses"]
        hit_rate = (self.performance_metrics["cache_hits"] / cache_total * 100) if cache_total > 0 else 0
        
        return {
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "avg_response_time": f"{self.performance_metrics['avg_response_time']:.2f}ms",
            "total_db_connections": self.performance_metrics["db_connections"],
            "status": "optimal" if hit_rate > 70 and self.performance_metrics["avg_response_time"] < 2000 else "needs_optimization"
        }

# Global optimizer instance
optimizer = PerformanceOptimizer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager"""
    # Startup
    await optimizer.initialize()
    
    # Initialize FastAPI Cache
    redis_client = await redis.from_url(REDIS_URL)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    
    yield
    
    # Shutdown
    if optimizer.redis_client:
        await optimizer.redis_client.close()
    if optimizer.db_pool:
        await optimizer.db_pool.close()

# Example FastAPI app with optimizations
app = FastAPI(
    title="ChatterFix CMMS - Optimized Services",
    description="High-performance CMMS with Redis caching and async PostgreSQL",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/work-orders/optimized")
async def get_optimized_work_orders():
    """Get work orders with caching optimization"""
    start_time = time.time()
    
    work_orders = await optimizer.cached_work_orders()
    
    response_time = (time.time() - start_time) * 1000
    
    return {
        "data": work_orders,
        "meta": {
            "count": len(work_orders),
            "response_time_ms": round(response_time, 2),
            "cached": response_time < 100  # Likely cached if under 100ms
        }
    }

@app.get("/api/assets/optimized")
async def get_optimized_assets(location_id: Optional[int] = None):
    """Get assets with caching optimization"""
    start_time = time.time()
    
    assets = await optimizer.cached_assets(location_id)
    
    response_time = (time.time() - start_time) * 1000
    
    return {
        "data": assets,
        "meta": {
            "count": len(assets),
            "response_time_ms": round(response_time, 2),
            "location_filter": location_id
        }
    }

@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get system performance metrics"""
    return optimizer.get_metrics()

@app.post("/api/performance/cache/invalidate")
async def invalidate_cache(pattern: str = "*"):
    """Invalidate cache entries"""
    await optimizer.invalidate_cache(pattern)
    return {"status": "Cache invalidated", "pattern": pattern}

@app.get("/health")
async def health_check():
    """Optimized health check"""
    return {
        "status": "healthy",
        "service": "performance-optimized-cmms",
        "timestamp": datetime.now().isoformat(),
        "optimizations": [
            "Redis caching layer",
            "PostgreSQL connection pooling", 
            "Async database operations",
            "Response time monitoring"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "performance_optimization:app",
        host="0.0.0.0",
        port=8090,
        workers=4,  # Multiple workers for concurrency
        reload=False,
        access_log=True
    )