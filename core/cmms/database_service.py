#!/usr/bin/env python3
"""
ChatterFix CMMS - Database Microservice
A dedicated FastAPI service for all database operations using SimpleDatabaseManager.

This service provides:
- RESTful API for all database operations
- Health checks and monitoring
- Optimized for Cloud Run deployment
- Clean separation from main application
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
import logging
import os
import json
from datetime import datetime
from contextlib import asynccontextmanager

# Import the database utilities
from database_utils import get_db_connection, execute_query, check_database_health, is_postgresql

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class HealthResponse(BaseModel):
    status: str
    database_type: str
    connection: bool
    tables: int
    errors: List[str] = []
    timestamp: str

class QueryRequest(BaseModel):
    query: str
    params: Union[List, Dict] = Field(default_factory=list)
    fetch: Optional[str] = "one"  # 'one', 'all', 'many', or None

class QueryResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    affected_rows: Optional[int] = None

class WorkOrder(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None
    asset_id: Optional[int] = None

class Asset(BaseModel):
    name: str
    description: str
    location: str
    status: str = "active"
    asset_type: str

class User(BaseModel):
    username: str
    email: str
    full_name: str
    role: str = "user"

# Database initialization context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    logger.info("Starting Database Microservice...")
    
    # Initialize database tables if they don't exist
    try:
        await initialize_database_schema()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    logger.info("Database Microservice shutting down...")

# Create FastAPI app
app = FastAPI(
    title="ChatterFix CMMS Database Service",
    description="Dedicated database microservice for ChatterFix CMMS",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_database_schema():
    """Initialize database schema with essential tables"""
    
    # Common schema for both PostgreSQL and SQLite
    schema_queries = [
        # Users table
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            role VARCHAR(50) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Assets table
        """
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            asset_type VARCHAR(100),
            location VARCHAR(255),
            status VARCHAR(50) DEFAULT 'active',
            purchase_date DATE,
            warranty_expiry DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Work orders table
        """
        CREATE TABLE IF NOT EXISTS work_orders (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            priority VARCHAR(20) DEFAULT 'medium',
            status VARCHAR(50) DEFAULT 'open',
            assigned_to INTEGER REFERENCES users(id),
            asset_id INTEGER REFERENCES assets(id),
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            completed_at TIMESTAMP
        )
        """,
        
        # Parts table
        """
        CREATE TABLE IF NOT EXISTS parts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            part_number VARCHAR(100) UNIQUE,
            quantity INTEGER DEFAULT 0,
            unit_cost DECIMAL(10,2),
            supplier VARCHAR(255),
            location VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Work order parts junction table
        """
        CREATE TABLE IF NOT EXISTS work_order_parts (
            id SERIAL PRIMARY KEY,
            work_order_id INTEGER REFERENCES work_orders(id),
            part_id INTEGER REFERENCES parts(id),
            quantity_used INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    # Execute schema creation
    for query in schema_queries:
        try:
            # Adapt query for SQLite if needed
            adapted_query = query
            if db.config.db_type.value == "sqlite":
                adapted_query = query.replace("SERIAL", "INTEGER").replace("REFERENCES", "-- REFERENCES")
            
            db.execute_query(adapted_query, fetch=None)
            logger.info(f"Schema query executed successfully")
        except Exception as e:
            logger.warning(f"Schema query failed (may already exist): {e}")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Database health check endpoint"""
    try:
        health = check_database_health()
        return HealthResponse(
            status=health["status"],
            database_type=health["database_type"],
            connection=health["connection"],
            tables=health["tables"],
            errors=health["errors"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            database_type="unknown",
            connection=False,
            tables=0,
            errors=[str(e)],
            timestamp=datetime.now().isoformat()
        )

# Generic query endpoint
@app.post("/api/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a generic database query"""
    try:
        result = db.execute_query(
            request.query, 
            tuple(request.params) if isinstance(request.params, list) else request.params,
            request.fetch
        )
        
        return QueryResponse(
            success=True,
            data=result,
            affected_rows=result if request.fetch is None else None
        )
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")

# Work Orders endpoints
@app.get("/api/work-orders", response_model=List[Dict])
async def get_work_orders(limit: int = 100, offset: int = 0):
    """Get all work orders with optional pagination"""
    try:
        query = """
        SELECT wo.*, u.username as assigned_username, a.name as asset_name 
        FROM work_orders wo 
        LEFT JOIN users u ON wo.assigned_to = u.id 
        LEFT JOIN assets a ON wo.asset_id = a.id 
        ORDER BY wo.created_date DESC 
        LIMIT ? OFFSET ?
        """
        
        if db.config.db_type.value == "postgresql":
            query = query.replace("LIMIT ? OFFSET ?", "LIMIT %s OFFSET %s")
            
        results = db.execute_query(query, (limit, offset), fetch='all')
        return [dict(row) for row in results] if results else []
    except Exception as e:
        logger.error(f"Failed to get work orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/{work_order_id}", response_model=Dict)
async def get_work_order(work_order_id: int):
    """Get a specific work order by ID"""
    try:
        query = """
        SELECT wo.*, u.username as assigned_username, a.name as asset_name 
        FROM work_orders wo 
        LEFT JOIN users u ON wo.assigned_to = u.id 
        LEFT JOIN assets a ON wo.asset_id = a.id 
        WHERE wo.id = ?
        """
        
        if db.config.db_type.value == "postgresql":
            query = query.replace("?", "%s")
            
        result = db.execute_query(query, (work_order_id,), fetch='one')
        if not result:
            raise HTTPException(status_code=404, detail="Work order not found")
        return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get work order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders", response_model=Dict)
async def create_work_order(work_order: WorkOrder):
    """Create a new work order"""
    try:
        query = """
        INSERT INTO work_orders (title, description, priority, status, assigned_to, asset_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        if db.config.db_type.value == "postgresql":
            query = query.replace("?", "%s") + " RETURNING id"
            
        params = (
            work_order.title,
            work_order.description,
            work_order.priority,
            work_order.status,
            work_order.assigned_to,
            work_order.asset_id
        )
        
        if db.config.db_type.value == "postgresql":
            result = db.execute_query(query, params, fetch='one')
            work_order_id = result[0] if result else None
        else:
            db.execute_query(query, params, fetch=None)
            work_order_id = db.execute_query("SELECT last_insert_rowid()", fetch='one')[0]
        
        return {"id": work_order_id, "message": "Work order created successfully"}
    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Assets endpoints
@app.get("/api/assets", response_model=List[Dict])
async def get_assets(limit: int = 100, offset: int = 0):
    """Get all assets with optional pagination"""
    try:
        query = "SELECT * FROM assets ORDER BY created_date DESC LIMIT ? OFFSET ?"
        
        if db.config.db_type.value == "postgresql":
            query = query.replace("LIMIT ? OFFSET ?", "LIMIT %s OFFSET %s")
            
        results = db.execute_query(query, (limit, offset), fetch='all')
        return [dict(row) for row in results] if results else []
    except Exception as e:
        logger.error(f"Failed to get assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets", response_model=Dict)
async def create_asset(asset: Asset):
    """Create a new asset"""
    try:
        query = """
        INSERT INTO assets (name, description, asset_type, location, status)
        VALUES (?, ?, ?, ?, ?)
        """
        
        if db.config.db_type.value == "postgresql":
            query = query.replace("?", "%s") + " RETURNING id"
            
        params = (asset.name, asset.description, asset.asset_type, asset.location, asset.status)
        
        if db.config.db_type.value == "postgresql":
            result = db.execute_query(query, params, fetch='one')
            asset_id = result[0] if result else None
        else:
            db.execute_query(query, params, fetch=None)
            asset_id = db.execute_query("SELECT last_insert_rowid()", fetch='one')[0]
        
        return {"id": asset_id, "message": "Asset created successfully"}
    except Exception as e:
        logger.error(f"Failed to create asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Users endpoints
@app.get("/api/users", response_model=List[Dict])
async def get_users():
    """Get all users (excluding password hashes)"""
    try:
        query = "SELECT id, username, email, full_name, role, created_date, is_active FROM users ORDER BY created_date DESC"
        results = db.execute_query(query, fetch='all')
        return [dict(row) for row in results] if results else []
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}", response_model=Dict)
async def get_user(user_id: int):
    """Get a specific user by ID"""
    try:
        query = "SELECT id, username, email, full_name, role, created_date, is_active FROM users WHERE id = ?"
        
        if db.config.db_type.value == "postgresql":
            query = query.replace("?", "%s")
            
        result = db.execute_query(query, (user_id,), fetch='one')
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Parts endpoints
@app.get("/api/parts", response_model=List[Dict])
async def get_parts(limit: int = 100, offset: int = 0):
    """Get all parts with optional pagination"""
    try:
        query = "SELECT * FROM parts ORDER BY created_date DESC LIMIT ? OFFSET ?"
        
        if db.config.db_type.value == "postgresql":
            query = query.replace("LIMIT ? OFFSET ?", "LIMIT %s OFFSET %s")
            
        results = db.execute_query(query, (limit, offset), fetch='all')
        return [dict(row) for row in results] if results else []
    except Exception as e:
        logger.error(f"Failed to get parts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoints
@app.get("/api/stats/overview", response_model=Dict)
async def get_overview_stats():
    """Get overview statistics"""
    try:
        stats = {}
        
        # Count tables
        tables = ["work_orders", "assets", "users", "parts"]
        for table in tables:
            try:
                count_query = f"SELECT COUNT(*) FROM {table}"
                result = db.execute_query(count_query, fetch='one')
                stats[f"{table}_count"] = result[0] if result else 0
            except Exception as e:
                logger.warning(f"Failed to count {table}: {e}")
                stats[f"{table}_count"] = 0
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get overview stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)