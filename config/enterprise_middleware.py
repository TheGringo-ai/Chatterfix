"""
Enterprise FastAPI Middleware Template
Standard middleware for all ChatterFix services
"""
import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

class EnterpriseMiddleware(BaseHTTPMiddleware):
    """Enterprise middleware for timeout and monitoring"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Request timeout
        request_timeout = int(os.environ.get("REQUEST_TIMEOUT_MS", "10000")) / 1000
        
        try:
            response = await call_next(request)
            
            # Add performance headers
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Service-Version"] = "7.0.0"
            
            # Log slow requests
            if process_time > 2.0:
                logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {request.url} after {process_time:.2f}s - {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": str(time.time())}
            )

def setup_enterprise_middleware(app: FastAPI, service_name: str):
    """Setup standard enterprise middleware for all services"""
    
    # CORS Configuration
    cors_origins = os.environ.get("CORS_ORIGINS", "https://chatterfix-unified-gateway-650169261019.us-central1.run.app").split(",")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        max_age=3600
    )
    
    # Trusted Host Middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.run.app", "chatterfix.com", "localhost", "127.0.0.1"]
    )
    
    # Enterprise custom middleware
    app.add_middleware(EnterpriseMiddleware)
    
    # Standard health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": service_name,
            "version": "7.0.0",
            "timestamp": time.time()
        }

def create_enterprise_db_engine(database_url: str):
    """Create database engine with enterprise connection pooling"""
    
    return create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=int(os.environ.get("DB_POOL_SIZE", "10")),
        max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "20")),
        pool_recycle=int(os.environ.get("DB_POOL_RECYCLE", "180")),
        pool_pre_ping=True,
        pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "30")),
        connect_args={
            "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT_S", "5")),
            "options": f"-c statement_timeout={os.environ.get('DB_QUERY_TIMEOUT_S', '20')}s"
        },
        echo=False
    )

# Security headers for production
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}