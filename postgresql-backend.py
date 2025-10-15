#!/usr/bin/env python3
"""
ChatterFix PostgreSQL Backend
Enterprise-grade backend using PostgreSQL database
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import uvicorn
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix PostgreSQL Backend", version="2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL configuration
POSTGRES_HOST = "35.225.244.14"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "ChatterFix2025!"
POSTGRES_DB = "chatterfix_cmms"

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Pydantic models
class WorkOrderCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None

class AssetCreate(BaseModel):
    name: str
    description: str = ""
    location: str = ""
    asset_type: str = ""
    status: str = "active"

class PartCreate(BaseModel):
    name: str
    part_number: str
    description: str = ""
    category: str = ""
    quantity: int = 0
    min_stock: int = 0
    unit_cost: float = 0.0
    location: str = ""

# Database connection pool
pool = None

async def init_database():
    """Initialize database connection and tables"""
    global pool
    
    try:
        # Create connection pool
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        
        logger.info("✅ Connected to PostgreSQL")
        
        # Initialize tables
        await create_tables()
        await insert_sample_data()
        
        logger.info("✅ Database initialized with sample data")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def create_tables():
    """Create all necessary tables"""
    async with pool.acquire() as conn:
        # Work Orders table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS work_orders (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                priority VARCHAR(50) DEFAULT 'medium',
                status VARCHAR(50) DEFAULT 'open',
                assigned_to VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Assets table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                location VARCHAR(255),
                asset_type VARCHAR(100),
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Parts table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS parts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                part_number VARCHAR(100) UNIQUE,
                description TEXT,
                category VARCHAR(100),
                quantity INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                unit_cost DECIMAL(10,2) DEFAULT 0.0,
                location VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_priority ON work_orders(priority)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category)')

async def insert_sample_data():
    """Insert comprehensive sample data"""
    async with pool.acquire() as conn:
        # Check if data already exists
        count = await conn.fetchval('SELECT COUNT(*) FROM work_orders')
        if count > 0:
            return
        
        # Sample work orders
        work_orders = [
            ('HVAC Annual Maintenance', 'Complete annual maintenance for main HVAC system including filter replacement and performance check', 'high', 'open', 'John Smith'),
            ('Conveyor Belt Replacement', 'Replace worn conveyor belt on production line 3 - urgent repair needed', 'urgent', 'in-progress', 'Mike Johnson'),
            ('Water Pump Inspection', 'Monthly inspection of main water circulation pumps in basement utility room', 'medium', 'open', 'Sarah Wilson'),
            ('Emergency Generator Test', 'Quarterly test of 500kW emergency backup generator including load testing', 'medium', 'completed', 'Tom Brown'),
            ('Electrical Panel Safety Check', 'Annual safety inspection of main electrical distribution panel A1', 'high', 'open', 'Lisa Davis'),
            ('Boiler Maintenance', 'Quarterly boiler inspection, cleaning, and efficiency testing', 'medium', 'in-progress', 'John Smith'),
            ('Fire Alarm System Test', 'Monthly functionality test of building-wide fire detection and alarm system', 'high', 'completed', 'Mike Johnson'),
            ('Compressor Oil Change', 'Scheduled oil change for main pneumatic air compressor system', 'low', 'open', None),
            ('Roof Leak Repair', 'Emergency repair of roof leak above production area', 'urgent', 'open', 'Tom Brown'),
            ('Door Lock Maintenance', 'Quarterly maintenance of electronic door locks and access control system', 'low', 'completed', 'Sarah Wilson')
        ]
        
        for order in work_orders:
            await conn.execute('''
                INSERT INTO work_orders (title, description, priority, status, assigned_to)
                VALUES ($1, $2, $3, $4, $5)
            ''', *order)
        
        # Sample assets
        assets = [
            ('Main HVAC Unit', 'Central air conditioning and heating system - 50 ton capacity', 'Building A - Roof Level', 'HVAC', 'active'),
            ('Conveyor Belt #3', 'Heavy-duty production line conveyor system - 100ft length', 'Factory Floor - Line 3', 'Manufacturing', 'maintenance'),
            ('Water Pump Station', 'Dual centrifugal pump system for building water circulation', 'Basement - Utility Room', 'Pumping', 'active'),
            ('Emergency Generator', 'Caterpillar 500kW diesel backup power generation unit', 'Outdoor - East Side', 'Power', 'active'),
            ('Electrical Panel A1', 'Main 480V electrical distribution panel for building power', 'Basement - Electrical Room', 'Electrical', 'active'),
            ('Boiler Unit #1', 'Natural gas heating boiler - 2 million BTU capacity', 'Basement - Boiler Room', 'Heating', 'active'),
            ('Fire Alarm System', 'Honeywell building-wide fire detection and notification system', 'Throughout Building', 'Safety', 'active'),
            ('Air Compressor', 'Atlas Copco rotary screw air compressor - 125 HP', 'Basement - Compressor Room', 'Pneumatic', 'active'),
            ('Chiller Unit #2', 'York centrifugal chiller for process cooling - 200 ton', 'Roof Level - North Side', 'Cooling', 'active'),
            ('Loading Dock Door #1', 'Overhead sectional door with automatic opener', 'Loading Dock - Bay 1', 'Doors', 'active')
        ]
        
        for asset in assets:
            await conn.execute('''
                INSERT INTO assets (name, description, location, asset_type, status)
                VALUES ($1, $2, $3, $4, $5)
            ''', *asset)
        
        # Sample parts inventory
        parts = [
            ('HVAC Air Filter', 'AF-001', 'Pleated HEPA air filter 20x25x4 inch - 99.97% efficiency', 'Filters', 25, 10, 45.99, 'Warehouse A-3'),
            ('Conveyor Belt', 'CBT-203', 'Heavy-duty rubber conveyor belt 36" width x 100ft length', 'Belts', 2, 1, 1250.00, 'Storage Room B'),
            ('Water Pump Seal', 'WPS-150', 'Mechanical seal kit for centrifugal water pump repair', 'Seals', 15, 5, 89.50, 'Parts Cabinet 1'),
            ('Electrical Fuse 30A', 'EF-30A', '30 Amp time-delay electrical fuse - Class RK5', 'Electrical', 50, 20, 12.75, 'Electrical Cabinet'),
            ('Boiler Gasket Set', 'BG-450', 'High-temperature gasket set for boiler maintenance', 'Gaskets', 8, 3, 156.99, 'Boiler Parts Storage'),
            ('Generator Oil Filter', 'GOF-500', 'Engine oil filter for Caterpillar generator - OEM part', 'Filters', 6, 2, 78.25, 'Generator Storage'),
            ('Fire Alarm Battery', 'FAB-12V', '12V 7Ah sealed lead acid battery for fire alarm backup', 'Batteries', 20, 8, 34.50, 'Safety Equipment'),
            ('Compressor Oil', 'CO-SAE30', 'SAE 30 synthetic compressor oil - 5 gallon container', 'Lubricants', 12, 4, 125.00, 'Chemical Storage'),
            ('Chiller Refrigerant', 'R134A-30', 'R-134a refrigerant for chiller system - 30 lb cylinder', 'Refrigerants', 8, 3, 185.75, 'Refrigerant Storage'),
            ('Door Sensor', 'DS-MAG01', 'Magnetic door position sensor for loading dock doors', 'Sensors', 25, 10, 45.50, 'Electronics Cabinet')
        ]
        
        for part in parts:
            await conn.execute('''
                INSERT INTO parts (name, part_number, description, category, quantity, min_stock, unit_cost, location)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''', *part)

async def get_db():
    """Database dependency"""
    if not pool:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return pool

# API Endpoints

@app.get("/health")
async def health():
    """Comprehensive health check"""
    try:
        # Test database connectivity
        async with pool.acquire() as conn:
            db_version = await conn.fetchval('SELECT version()')
            
        return {
            "status": "healthy",
            "service": "ChatterFix PostgreSQL Backend",
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "type": "postgresql",
                "host": POSTGRES_HOST,
                "database": POSTGRES_DB,
                "status": "connected",
                "version": db_version.split()[1] if db_version else "unknown"
            },
            "features": [
                "work_orders_crud",
                "assets_management", 
                "parts_inventory",
                "postgresql_backend",
                "enterprise_ready"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ChatterFix PostgreSQL Backend",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Work Orders endpoints
@app.get("/api/work-orders")
async def get_work_orders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get work orders with optional filtering"""
    async with pool.acquire() as conn:
        query = "SELECT * FROM work_orders WHERE 1=1"
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)
        
        if priority:
            param_count += 1
            query += f" AND priority = ${param_count}"
            params.append(priority)
        
        if assigned_to:
            param_count += 1
            query += f" AND assigned_to = ${param_count}"
            params.append(assigned_to)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)
        
        if offset:
            param_count += 1
            query += f" OFFSET ${param_count}"
            params.append(offset)
        
        rows = await conn.fetch(query, *params)
        
        work_orders = []
        for row in rows:
            work_orders.append({
                "id": row['id'],
                "title": row['title'],
                "description": row['description'],
                "priority": row['priority'],
                "status": row['status'],
                "assigned_to": row['assigned_to'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
            })
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM work_orders WHERE 1=1"
        count_params = []
        count_param_count = 0
        
        if status:
            count_param_count += 1
            count_query += f" AND status = ${count_param_count}"
            count_params.append(status)
        
        if priority:
            count_param_count += 1
            count_query += f" AND priority = ${count_param_count}"
            count_params.append(priority)
        
        if assigned_to:
            count_param_count += 1
            count_query += f" AND assigned_to = ${count_param_count}"
            count_params.append(assigned_to)
        
        total_count = await conn.fetchval(count_query, *count_params)
        
        return {
            "work_orders": work_orders,
            "count": len(work_orders),
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "filters": {
                "status": status,
                "priority": priority, 
                "assigned_to": assigned_to
            }
        }

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrderCreate):
    """Create new work order"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            INSERT INTO work_orders (title, description, priority, status, assigned_to)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, created_at
        ''', work_order.title, work_order.description, work_order.priority, 
        work_order.status, work_order.assigned_to)
        
        return {
            "id": row['id'],
            "message": "Work order created successfully",
            "created_at": row['created_at'].isoformat(),
            "success": True
        }

@app.get("/api/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get specific work order"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM work_orders WHERE id = $1', work_order_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Work order not found")
        
        return {
            "id": row['id'],
            "title": row['title'],
            "description": row['description'],
            "priority": row['priority'],
            "status": row['status'],
            "assigned_to": row['assigned_to'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
        }

@app.put("/api/work-orders/{work_order_id}")
async def update_work_order(work_order_id: int, work_order: WorkOrderUpdate):
    """Update work order"""
    async with pool.acquire() as conn:
        # Build dynamic update query
        updates = []
        params = []
        param_count = 0
        
        if work_order.title is not None:
            param_count += 1
            updates.append(f"title = ${param_count}")
            params.append(work_order.title)
        
        if work_order.description is not None:
            param_count += 1
            updates.append(f"description = ${param_count}")
            params.append(work_order.description)
        
        if work_order.priority is not None:
            param_count += 1
            updates.append(f"priority = ${param_count}")
            params.append(work_order.priority)
        
        if work_order.status is not None:
            param_count += 1
            updates.append(f"status = ${param_count}")
            params.append(work_order.status)
        
        if work_order.assigned_to is not None:
            param_count += 1
            updates.append(f"assigned_to = ${param_count}")
            params.append(work_order.assigned_to)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        param_count += 1
        updates.append(f"updated_at = CURRENT_TIMESTAMP")
        params.append(work_order_id)
        
        query = f"UPDATE work_orders SET {', '.join(updates)} WHERE id = ${param_count} RETURNING updated_at"
        
        row = await conn.fetchrow(query, *params)
        
        if not row:
            raise HTTPException(status_code=404, detail="Work order not found")
        
        return {
            "message": "Work order updated successfully",
            "updated_at": row['updated_at'].isoformat(),
            "success": True
        }

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete work order"""
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM work_orders WHERE id = $1', work_order_id)
        
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Work order not found")
        
        return {
            "message": "Work order deleted successfully",
            "success": True
        }

# Assets endpoints
@app.get("/api/assets")
async def get_assets(
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get assets with optional filtering"""
    async with pool.acquire() as conn:
        query = "SELECT * FROM assets WHERE 1=1"
        params = []
        param_count = 0
        
        if asset_type:
            param_count += 1
            query += f" AND asset_type = ${param_count}"
            params.append(asset_type)
        
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)
        
        if location:
            param_count += 1
            query += f" AND location ILIKE ${param_count}"
            params.append(f"%{location}%")
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)
        
        if offset:
            param_count += 1
            query += f" OFFSET ${param_count}"
            params.append(offset)
        
        rows = await conn.fetch(query, *params)
        
        assets = []
        for row in rows:
            assets.append({
                "id": row['id'],
                "name": row['name'],
                "description": row['description'],
                "location": row['location'],
                "asset_type": row['asset_type'],
                "status": row['status'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
            })
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM assets WHERE 1=1"
        count_params = []
        count_param_count = 0
        
        if asset_type:
            count_param_count += 1
            count_query += f" AND asset_type = ${count_param_count}"
            count_params.append(asset_type)
        
        if status:
            count_param_count += 1
            count_query += f" AND status = ${count_param_count}"
            count_params.append(status)
        
        if location:
            count_param_count += 1
            count_query += f" AND location ILIKE ${count_param_count}"
            count_params.append(f"%{location}%")
        
        total_count = await conn.fetchval(count_query, *count_params)
        
        return {
            "assets": assets,
            "count": len(assets),
            "total": total_count,
            "offset": offset,
            "limit": limit
        }

@app.post("/api/assets")
async def create_asset(asset: AssetCreate):
    """Create new asset"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            INSERT INTO assets (name, description, location, asset_type, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, created_at
        ''', asset.name, asset.description, asset.location, asset.asset_type, asset.status)
        
        return {
            "id": row['id'],
            "message": "Asset created successfully",
            "created_at": row['created_at'].isoformat(),
            "success": True
        }

# Parts endpoints
@app.get("/api/parts")
async def get_parts(
    category: Optional[str] = None,
    low_stock: bool = False,
    location: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get parts with optional filtering"""
    async with pool.acquire() as conn:
        query = "SELECT * FROM parts WHERE 1=1"
        params = []
        param_count = 0
        
        if category:
            param_count += 1
            query += f" AND category = ${param_count}"
            params.append(category)
        
        if low_stock:
            query += " AND quantity <= min_stock"
        
        if location:
            param_count += 1
            query += f" AND location ILIKE ${param_count}"
            params.append(f"%{location}%")
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)
        
        if offset:
            param_count += 1
            query += f" OFFSET ${param_count}"
            params.append(offset)
        
        rows = await conn.fetch(query, *params)
        
        parts = []
        for row in rows:
            parts.append({
                "id": row['id'],
                "name": row['name'],
                "part_number": row['part_number'],
                "description": row['description'],
                "category": row['category'],
                "quantity": row['quantity'],
                "min_stock": row['min_stock'],
                "unit_cost": float(row['unit_cost']) if row['unit_cost'] else 0.0,
                "location": row['location'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                "low_stock": row['quantity'] <= row['min_stock']
            })
        
        return {
            "parts": parts,
            "count": len(parts),
            "filters": {
                "category": category,
                "low_stock": low_stock,
                "location": location
            }
        }

@app.post("/api/parts")
async def create_part(part: PartCreate):
    """Create new part"""
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow('''
                INSERT INTO parts (name, part_number, description, category, quantity, min_stock, unit_cost, location)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, created_at
            ''', part.name, part.part_number, part.description, part.category,
            part.quantity, part.min_stock, part.unit_cost, part.location)
            
            return {
                "id": row['id'],
                "message": "Part created successfully",
                "created_at": row['created_at'].isoformat(),
                "success": True
            }
            
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Part number already exists")

# Dashboard/Statistics endpoints
@app.get("/api/dashboard")
async def dashboard_stats():
    """Get dashboard statistics"""
    async with pool.acquire() as conn:
        # Work order statistics
        work_order_stats = await conn.fetch('''
            SELECT status, COUNT(*) as count
            FROM work_orders 
            GROUP BY status
        ''')
        
        # Asset statistics
        asset_stats = await conn.fetch('''
            SELECT asset_type, COUNT(*) as count
            FROM assets
            GROUP BY asset_type
        ''')
        
        # Parts statistics
        total_parts = await conn.fetchval('SELECT COUNT(*) FROM parts')
        low_stock_parts = await conn.fetchval('SELECT COUNT(*) FROM parts WHERE quantity <= min_stock')
        
        # Recent activity
        recent_work_orders = await conn.fetch('''
            SELECT id, title, status, created_at
            FROM work_orders
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        
        return {
            "work_orders": {
                "by_status": {row['status']: row['count'] for row in work_order_stats},
                "total": sum(row['count'] for row in work_order_stats)
            },
            "assets": {
                "by_type": {row['asset_type']: row['count'] for row in asset_stats},
                "total": sum(row['count'] for row in asset_stats)
            },
            "parts": {
                "total": total_parts,
                "low_stock": low_stock_parts
            },
            "recent_activity": [
                {
                    "id": row['id'],
                    "title": row['title'],
                    "status": row['status'],
                    "created_at": row['created_at'].isoformat()
                }
                for row in recent_work_orders
            ],
            "timestamp": datetime.now().isoformat()
        }

# Application lifecycle
@app.on_event("startup")
async def startup():
    """Initialize application"""
    logger.info("🚀 Starting ChatterFix PostgreSQL Backend...")
    await init_database()
    logger.info("✅ Application ready")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    if pool:
        await pool.close()
        logger.info("🔄 Database connections closed")

if __name__ == "__main__":
    print("🚀 ChatterFix PostgreSQL Backend")
    print("=" * 40)
    print(f"🗄️ Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print("🌐 Server: http://35.237.149.25:8081")
    print("📚 API Docs: http://35.237.149.25:8081/docs")
    print("✨ Features: Enterprise PostgreSQL backend with full CRUD")
    
    uvicorn.run(app, host="0.0.0.0", port=8081)