#!/usr/bin/env python3
"""
ChatterFix CMMS - Complete Backend Service
Integrated Work Orders, Assets, and Parts Management
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from functools import wraps
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix CMMS Service",
    description="Complete Computerized Maintenance Management System",
    version="6B.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration with connection pooling
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "chatterfix_cmms"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "connect_timeout": 10,
    "keepalives_idle": 600,
    "keepalives_interval": 30,
    "keepalives_count": 3
}

# Connection pool configuration
POOL_MIN_CONN = int(os.getenv("DB_POOL_MIN", "5"))
POOL_MAX_CONN = int(os.getenv("DB_POOL_MAX", "20"))

# Initialize connection pool
connection_pool = None

def initialize_connection_pool():
    """Initialize database connection pool"""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            POOL_MIN_CONN,
            POOL_MAX_CONN,
            **DATABASE_CONFIG
        )
        logger.info(f"✅ Database connection pool initialized: {POOL_MIN_CONN}-{POOL_MAX_CONN} connections")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize connection pool: {e}")
        return False

def get_db_connection():
    """Get database connection from pool with enhanced error handling"""
    global connection_pool
    
    # Initialize pool if not available
    if connection_pool is None:
        if not initialize_connection_pool():
            return None
    
    try:
        conn = connection_pool.getconn()
        if conn:
            return conn
    except Exception as e:
        logger.error(f"Failed to get connection from pool: {e}")
        
    # Fallback to direct connection
    try:
        config = DATABASE_CONFIG.copy()
        conn = psycopg2.connect(**config)
        logger.warning("Using fallback direct connection")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def return_db_connection(conn):
    """Return connection to pool"""
    global connection_pool
    try:
        if connection_pool and conn:
            connection_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Failed to return connection to pool: {e}")

# Redis Cache Setup
redis_client = None

def initialize_redis():
    """Initialize Redis client for caching"""
    global redis_client
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        # Test connection
        redis_client.ping()
        logger.info("✅ Redis cache connected")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Redis not available, caching disabled: {e}")
        redis_client = None
        return False

def cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from parameters"""
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)

def cached_query(ttl: int = 300):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)
            
            # Generate cache key
            key = cache_key(func.__name__, **kwargs)
            
            try:
                # Try to get from cache
                cached_result = redis_client.get(key)
                if cached_result:
                    logger.debug(f"Cache hit for {key}")
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            try:
                redis_client.setex(key, ttl, json.dumps(result, default=str))
                logger.debug(f"Cached result for {key}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        return wrapper
    return decorator

def init_database():
    """Initialize database with sample data if empty"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if tables exist, create basic tables if not
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'open',
                priority VARCHAR(50) DEFAULT 'medium',
                asset_id INTEGER,
                assigned_to VARCHAR(255),
                created_by VARCHAR(255) DEFAULT 'system',
                estimated_hours NUMERIC(6,2),
                actual_hours NUMERIC(6,2),
                due_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                asset_type VARCHAR(100) DEFAULT 'equipment',
                manufacturer VARCHAR(255),
                model VARCHAR(255),
                serial_number VARCHAR(255),
                location VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                purchase_date DATE,
                warranty_expiry DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                part_number VARCHAR(255) UNIQUE,
                category VARCHAR(100) DEFAULT 'general',
                quantity_on_hand INTEGER DEFAULT 0,
                minimum_stock_level INTEGER DEFAULT 5,
                unit_cost NUMERIC(10,2) DEFAULT 0.00,
                supplier VARCHAR(255),
                location VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Add sample data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM assets")
        if cursor.fetchone()[0] == 0:
            sample_assets = [
                ("HVAC Unit #1", "Main building air conditioning system", "HVAC", "Carrier", "30XA-025", "AC001", "Building A - Roof", "active"),
                ("Boiler #1", "Primary heating boiler", "Heating", "Viessmann", "Vitocrossal 300", "BL001", "Basement", "active"),
                ("Generator #1", "Emergency backup generator", "Electrical", "Caterpillar", "C7.1", "GN001", "Outdoor - North", "active"),
                ("Elevator #1", "Main passenger elevator", "Mechanical", "Otis", "Gen2", "EL001", "Building A - Core", "active"),
                ("Fire Pump", "Main fire suppression pump", "Safety", "Grundfos", "CR 64-2", "FP001", "Basement", "active")
            ]
            
            cursor.executemany("""
                INSERT INTO assets (name, description, asset_type, manufacturer, model, serial_number, location, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_assets)
        
        cursor.execute("SELECT COUNT(*) FROM parts")
        if cursor.fetchone()[0] == 0:
            sample_parts = [
                ("Air Filter", "HVAC system air filter", "FILT-001", "Filters", 25, 10, 15.50, "FilterCorp", "Warehouse A1"),
                ("Belt Drive", "V-belt for HVAC units", "BELT-002", "Mechanical", 8, 5, 45.00, "PowerTrans", "Warehouse B2"),
                ("Bearing", "Ball bearing 6204", "BEAR-003", "Mechanical", 15, 10, 12.75, "SKF", "Warehouse B1"),
                ("Motor Oil", "Synthetic motor oil", "OIL-004", "Fluids", 12, 5, 8.25, "Mobil", "Chemical Storage"),
                ("Light Bulb", "LED bulb 60W equivalent", "BULB-005", "Electrical", 50, 20, 12.00, "Phillips", "Electrical Room")
            ]
            
            cursor.executemany("""
                INSERT INTO parts (name, description, part_number, category, quantity_on_hand, minimum_stock_level, unit_cost, supplier, location)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_parts)
        
        cursor.execute("SELECT COUNT(*) FROM work_orders")
        if cursor.fetchone()[0] == 0:
            sample_work_orders = [
                ("HVAC Maintenance", "Monthly preventive maintenance", "in_progress", "medium", 1, "John Smith", 4.0),
                ("Replace Air Filter", "Replace dirty air filter in Unit #1", "open", "low", 1, "Mike Johnson", 1.0),
                ("Boiler Inspection", "Annual boiler safety inspection", "open", "high", 2, "Sarah Wilson", 8.0),
                ("Generator Test", "Monthly generator load test", "completed", "medium", 3, "Tom Davis", 2.0),
                ("Elevator Service", "Quarterly elevator maintenance", "open", "high", 4, "John Smith", 6.0)
            ]
            
            for title, desc, status, priority, asset_id, assigned_to, est_hours in sample_work_orders:
                due_date = datetime.now() + timedelta(days=7)
                cursor.execute("""
                    INSERT INTO work_orders (title, description, status, priority, asset_id, assigned_to, estimated_hours, due_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (title, desc, status, priority, asset_id, assigned_to, est_hours, due_date))
        
        conn.commit()
        cursor.close()
        return_db_connection(conn)
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if 'conn' in locals():
            return_db_connection(conn)

# Pydantic Models
class WorkOrder(BaseModel):
    title: str
    description: Optional[str] = ""
    status: Optional[str] = "open"
    priority: Optional[str] = "medium"
    asset_id: Optional[int] = None
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = None
    due_date: Optional[str] = None

class Asset(BaseModel):
    name: str
    description: Optional[str] = ""
    asset_type: Optional[str] = "equipment"
    manufacturer: Optional[str] = ""
    model: Optional[str] = ""
    serial_number: Optional[str] = ""
    location: Optional[str] = ""
    status: Optional[str] = "active"
    purchase_date: Optional[str] = None
    warranty_expiry: Optional[str] = None

class Part(BaseModel):
    name: str
    description: Optional[str] = ""
    part_number: Optional[str] = ""
    category: Optional[str] = "general"
    quantity_on_hand: Optional[int] = 0
    minimum_stock_level: Optional[int] = 5
    unit_cost: Optional[float] = 0.00
    supplier: Optional[str] = ""
    location: Optional[str] = ""

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cmms", "version": "6B.1.0"}

# Demo data for when database is not available
DEMO_WORK_ORDERS = [
    {"id": 1, "title": "HVAC Maintenance", "description": "Monthly preventive maintenance", "status": "in_progress", "priority": "medium", "asset_id": 1, "asset_name": "HVAC Unit #1", "assigned_to": "John Smith", "created_at": "2025-10-21T10:00:00"},
    {"id": 2, "title": "Replace Air Filter", "description": "Replace dirty air filter", "status": "open", "priority": "low", "asset_id": 1, "asset_name": "HVAC Unit #1", "assigned_to": "Mike Johnson", "created_at": "2025-10-21T09:30:00"},
    {"id": 3, "title": "Boiler Inspection", "description": "Annual safety inspection", "status": "open", "priority": "high", "asset_id": 2, "asset_name": "Boiler #1", "assigned_to": "Sarah Wilson", "created_at": "2025-10-21T08:00:00"},
    {"id": 4, "title": "Generator Test", "description": "Monthly load test", "status": "completed", "priority": "medium", "asset_id": 3, "asset_name": "Generator #1", "assigned_to": "Tom Davis", "created_at": "2025-10-20T14:00:00"},
    {"id": 5, "title": "Elevator Service", "description": "Quarterly maintenance", "status": "open", "priority": "high", "asset_id": 4, "asset_name": "Elevator #1", "assigned_to": "John Smith", "created_at": "2025-10-20T11:00:00"}
]

DEMO_ASSETS = [
    {"id": 1, "name": "HVAC Unit #1", "description": "Main building air conditioning", "asset_type": "HVAC", "manufacturer": "Carrier", "model": "30XA-025", "serial_number": "AC001", "location": "Building A - Roof", "status": "active", "created_at": "2025-01-01T00:00:00"},
    {"id": 2, "name": "Boiler #1", "description": "Primary heating boiler", "asset_type": "Heating", "manufacturer": "Viessmann", "model": "Vitocrossal 300", "serial_number": "BL001", "location": "Basement", "status": "active", "created_at": "2025-01-01T00:00:00"},
    {"id": 3, "name": "Generator #1", "description": "Emergency backup generator", "asset_type": "Electrical", "manufacturer": "Caterpillar", "model": "C7.1", "serial_number": "GN001", "location": "Outdoor - North", "status": "active", "created_at": "2025-01-01T00:00:00"},
    {"id": 4, "name": "Elevator #1", "description": "Main passenger elevator", "asset_type": "Mechanical", "manufacturer": "Otis", "model": "Gen2", "serial_number": "EL001", "location": "Building A - Core", "status": "active", "created_at": "2025-01-01T00:00:00"},
    {"id": 5, "name": "Fire Pump", "description": "Main fire suppression pump", "asset_type": "Safety", "manufacturer": "Grundfos", "model": "CR 64-2", "serial_number": "FP001", "location": "Basement", "status": "active", "created_at": "2025-01-01T00:00:00"}
]

DEMO_PARTS = [
    {"id": 1, "name": "Air Filter", "description": "HVAC system air filter", "part_number": "FILT-001", "category": "Filters", "quantity_on_hand": 25, "minimum_stock_level": 10, "unit_cost": 15.50, "supplier": "FilterCorp", "location": "Warehouse A1", "created_at": "2025-01-01T00:00:00"},
    {"id": 2, "name": "Belt Drive", "description": "V-belt for HVAC units", "part_number": "BELT-002", "category": "Mechanical", "quantity_on_hand": 8, "minimum_stock_level": 5, "unit_cost": 45.00, "supplier": "PowerTrans", "location": "Warehouse B2", "created_at": "2025-01-01T00:00:00"},
    {"id": 3, "name": "Bearing", "description": "Ball bearing 6204", "part_number": "BEAR-003", "category": "Mechanical", "quantity_on_hand": 3, "minimum_stock_level": 10, "unit_cost": 12.75, "supplier": "SKF", "location": "Warehouse B1", "created_at": "2025-01-01T00:00:00"},
    {"id": 4, "name": "Motor Oil", "description": "Synthetic motor oil", "part_number": "OIL-004", "category": "Fluids", "quantity_on_hand": 12, "minimum_stock_level": 5, "unit_cost": 8.25, "supplier": "Mobil", "location": "Chemical Storage", "created_at": "2025-01-01T00:00:00"},
    {"id": 5, "name": "Light Bulb", "description": "LED bulb 60W equivalent", "part_number": "BULB-005", "category": "Electrical", "quantity_on_hand": 50, "minimum_stock_level": 20, "unit_cost": 12.00, "supplier": "Phillips", "location": "Electrical Room", "created_at": "2025-01-01T00:00:00"}
]

# Work Orders API with caching
@app.get("/api/work-orders")
@cached_query(ttl=60)  # Cache for 1 minute
async def get_work_orders(status: Optional[str] = None, limit: int = Query(50, le=100)):
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT wo.*, a.name as asset_name 
                FROM work_orders wo 
                LEFT JOIN assets a ON wo.asset_id = a.id
            """
            params = []
            
            if status:
                query += " WHERE wo.status = %s"
                params.append(status)
            
            query += " ORDER BY wo.created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            work_orders = cursor.fetchall()
            
            cursor.close()
            return_db_connection(conn)
            
            return {"work_orders": [dict(wo) for wo in work_orders], "count": len(work_orders)}
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return_db_connection(conn)
            # Fall through to demo data
    
    # Use demo data when database is not available
    filtered_orders = DEMO_WORK_ORDERS
    if status:
        filtered_orders = [wo for wo in DEMO_WORK_ORDERS if wo["status"] == status]
    
    return {"work_orders": filtered_orders[:limit], "count": len(filtered_orders)}

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrder):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        INSERT INTO work_orders (title, description, status, priority, asset_id, assigned_to, estimated_hours, due_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (
        work_order.title,
        work_order.description,
        work_order.status,
        work_order.priority,
        work_order.asset_id,
        work_order.assigned_to,
        work_order.estimated_hours,
        work_order.due_date
    ))
    
    new_work_order = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "work_order": dict(new_work_order)}

@app.get("/api/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT wo.*, a.name as asset_name 
        FROM work_orders wo 
        LEFT JOIN assets a ON wo.asset_id = a.id
        WHERE wo.id = %s
    """, (work_order_id,))
    
    work_order = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return {"work_order": dict(work_order)}

@app.put("/api/work-orders/{work_order_id}")
async def update_work_order(work_order_id: int, updates: dict):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Build dynamic update query
    set_clauses = []
    values = []
    
    for key, value in updates.items():
        if key in ['title', 'description', 'status', 'priority', 'assigned_to', 'estimated_hours', 'actual_hours']:
            set_clauses.append(f"{key} = %s")
            values.append(value)
    
    if not set_clauses:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    values.append(work_order_id)
    
    query = f"UPDATE work_orders SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
    
    cursor.execute(query, values)
    updated_work_order = cursor.fetchone()
    
    if not updated_work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "work_order": dict(updated_work_order)}

# Assets API with caching
@app.get("/api/assets")
@cached_query(ttl=300)  # Cache for 5 minutes (heavy query)
async def get_assets(status: Optional[str] = None, asset_type: Optional[str] = None, limit: int = Query(50, le=100)):
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM assets"
            params = []
            conditions = []
            
            if status:
                conditions.append("status = %s")
                params.append(status)
            
            if asset_type:
                conditions.append("asset_type = %s")
                params.append(asset_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            assets = cursor.fetchall()
            
            cursor.close()
            return_db_connection(conn)
            
            return {"assets": [dict(asset) for asset in assets], "count": len(assets)}
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return_db_connection(conn)
    
    # Use demo data when database is not available
    filtered_assets = DEMO_ASSETS
    if status:
        filtered_assets = [asset for asset in DEMO_ASSETS if asset["status"] == status]
    if asset_type:
        filtered_assets = [asset for asset in filtered_assets if asset["asset_type"] == asset_type]
    
    return {"assets": filtered_assets[:limit], "count": len(filtered_assets)}

@app.post("/api/assets")
async def create_asset(asset: Asset):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        INSERT INTO assets (name, description, asset_type, manufacturer, model, serial_number, location, status, purchase_date, warranty_expiry)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (
        asset.name,
        asset.description,
        asset.asset_type,
        asset.manufacturer,
        asset.model,
        asset.serial_number,
        asset.location,
        asset.status,
        asset.purchase_date,
        asset.warranty_expiry
    ))
    
    new_asset = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "asset": dict(new_asset)}

@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM assets WHERE id = %s", (asset_id,))
    asset = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return {"asset": dict(asset)}

# Parts API
@app.get("/api/parts")
async def get_parts(category: Optional[str] = None, low_stock: bool = False, limit: int = Query(50, le=100)):
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM parts"
            params = []
            conditions = []
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            if low_stock:
                conditions.append("quantity_on_hand <= minimum_stock_level")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            parts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {"parts": [dict(part) for part in parts], "count": len(parts)}
        except Exception as e:
            logger.error(f"Database query failed: {e}")
    
    # Use demo data when database is not available
    filtered_parts = DEMO_PARTS
    if category:
        filtered_parts = [part for part in DEMO_PARTS if part["category"] == category]
    if low_stock:
        filtered_parts = [part for part in filtered_parts if part["quantity_on_hand"] <= part["minimum_stock_level"]]
    
    return {"parts": filtered_parts[:limit], "count": len(filtered_parts)}

@app.post("/api/parts")
async def create_part(part: Part):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        INSERT INTO parts (name, description, part_number, category, quantity_on_hand, minimum_stock_level, unit_cost, supplier, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (
        part.name,
        part.description,
        part.part_number,
        part.category,
        part.quantity_on_hand,
        part.minimum_stock_level,
        part.unit_cost,
        part.supplier,
        part.location
    ))
    
    new_part = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "part": dict(new_part)}

@app.get("/api/parts/{part_id}")
async def get_part(part_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM parts WHERE id = %s", (part_id,))
    part = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    return {"part": dict(part)}

@app.put("/api/parts/{part_id}/stock")
async def update_part_stock(part_id: int, adjustment: dict):
    """Update part stock levels"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    quantity = adjustment.get("quantity", 0)
    operation = adjustment.get("operation", "add")  # add, subtract, set
    
    if operation == "set":
        cursor.execute("""
            UPDATE parts SET quantity_on_hand = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s RETURNING *
        """, (quantity, part_id))
    elif operation == "add":
        cursor.execute("""
            UPDATE parts SET quantity_on_hand = quantity_on_hand + %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s RETURNING *
        """, (quantity, part_id))
    elif operation == "subtract":
        cursor.execute("""
            UPDATE parts SET quantity_on_hand = GREATEST(0, quantity_on_hand - %s), updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s RETURNING *
        """, (quantity, part_id))
    
    updated_part = cursor.fetchone()
    
    if not updated_part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "part": dict(updated_part)}

# Dashboard / Stats endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get CMMS dashboard statistics"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Work order stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_work_orders,
            COUNT(*) FILTER (WHERE status = 'open') as open_work_orders,
            COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_work_orders,
            COUNT(*) FILTER (WHERE status = 'completed') as completed_work_orders,
            COUNT(*) FILTER (WHERE priority = 'high') as high_priority_work_orders
        FROM work_orders
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
    """)
    work_order_stats = cursor.fetchone()
    
    # Asset stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_assets,
            COUNT(*) FILTER (WHERE status = 'active') as active_assets,
            COUNT(*) FILTER (WHERE status = 'inactive') as inactive_assets,
            COUNT(DISTINCT asset_type) as asset_types
        FROM assets
    """)
    asset_stats = cursor.fetchone()
    
    # Parts stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_parts,
            COUNT(*) FILTER (WHERE quantity_on_hand <= minimum_stock_level) as low_stock_parts,
            SUM(quantity_on_hand * unit_cost) as total_inventory_value
        FROM parts
    """)
    parts_stats = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return {
        "work_orders": dict(work_order_stats),
        "assets": dict(asset_stats),
        "parts": dict(parts_stats),
        "generated_at": datetime.now().isoformat()
    }

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting CMMS service with optimizations...")
    
    # Initialize connection pool
    logger.info("🔧 Initializing database connection pool...")
    pool_initialized = initialize_connection_pool()
    
    # Initialize Redis cache
    logger.info("🔧 Initializing Redis cache...")
    cache_initialized = initialize_redis()
    
    # Test database connection and initialize
    try:
        conn = get_db_connection()
        if conn:
            logger.info("✅ Database connected successfully")
            return_db_connection(conn)
            init_database()
        else:
            logger.warning("❌ Database connection failed - using demo data")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.info("📊 Service running with demo data fallback")
    
    # Log optimization status
    optimizations = []
    if pool_initialized:
        optimizations.append("Connection Pooling")
    if cache_initialized:
        optimizations.append("Redis Caching")
    
    logger.info(f"✅ CMMS service startup complete with optimizations: {', '.join(optimizations) if optimizations else 'None'}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("🔄 Shutting down CMMS service...")
    
    # Close connection pool
    global connection_pool
    if connection_pool:
        try:
            connection_pool.closeall()
            logger.info("✅ Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")
    
    # Close Redis connection
    global redis_client
    if redis_client:
        try:
            redis_client.close()
            logger.info("✅ Redis cache connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    logger.info("✅ CMMS service shutdown complete")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)