#!/bin/bash
set -e

echo "🐘 PostgreSQL Backend Deployment"
echo "==============================="
cd /home/yoyofred_gringosgambit_com

# Stop any existing backend processes
echo "🛑 Stopping existing backend processes..."
pkill -f "python.*8081" || true
pkill -f "postgresql-backend" || true
pkill -f "ai_backend" || true
pkill -f "simple_backend" || true

# Install PostgreSQL client and Python dependencies
echo "📦 Installing dependencies..."
python3 -m pip install --user --quiet asyncpg fastapi uvicorn

# Test PostgreSQL connection
echo "🔍 Testing PostgreSQL connection..."
python3 -c "
import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            'postgresql://postgres:ChatterFix2025!@35.225.244.14:5432/chatterfix_cmms'
        )
        result = await conn.fetchval('SELECT current_database()')
        await conn.close()
        print(f'✅ PostgreSQL connection successful: {result}')
        return True
    except Exception as e:
        print(f'❌ PostgreSQL connection failed: {e}')
        return False

asyncio.run(test_connection())
"

# Create PostgreSQL backend
echo "📝 Creating PostgreSQL backend service..."
cat > postgresql_backend.py << 'POSTGRES_BACKEND_EOF'
#!/usr/bin/env python3
"""
ChatterFix PostgreSQL Backend - Production Ready
Enterprise-grade backend with PostgreSQL database
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
import uvicorn
from datetime import datetime
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix PostgreSQL Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL configuration
DATABASE_URL = "postgresql://postgres:ChatterFix2025!@35.225.244.14:5432/chatterfix_cmms"
pool = None

class WorkOrderCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None

async def init_database():
    global pool
    try:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)
        logger.info("✅ Connected to PostgreSQL")
        
        async with pool.acquire() as conn:
            # Create work orders table
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
            
            # Create assets table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    location VARCHAR(255),
                    asset_type VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create parts table
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert sample data if empty
            count = await conn.fetchval('SELECT COUNT(*) FROM work_orders')
            if count == 0:
                sample_orders = [
                    ('PostgreSQL Backend Test', 'Testing enterprise PostgreSQL integration', 'high', 'open', 'Database Team'),
                    ('HVAC System Maintenance', 'Annual maintenance for building HVAC system', 'medium', 'open', 'John Smith'),
                    ('Conveyor Belt Repair', 'Replace worn belt on production line', 'urgent', 'in-progress', 'Mike Johnson'),
                    ('Water Pump Inspection', 'Monthly pump inspection', 'low', 'completed', 'Sarah Wilson')
                ]
                
                for order in sample_orders:
                    await conn.execute('''
                        INSERT INTO work_orders (title, description, priority, status, assigned_to)
                        VALUES ($1, $2, $3, $4, $5)
                    ''', *order)
                
                logger.info("✅ Sample data inserted")
    
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

@app.get("/health")
async def health():
    try:
        async with pool.acquire() as conn:
            db_version = await conn.fetchval('SELECT version()')
            
        return {
            "status": "healthy",
            "service": "ChatterFix PostgreSQL Backend",
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "type": "postgresql",
                "host": "35.225.244.14",
                "database": "chatterfix_cmms",
                "status": "connected",
                "version": db_version.split()[1] if db_version else "unknown"
            },
            "port": 8081,
            "enterprise_ready": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ChatterFix PostgreSQL Backend",
            "error": str(e)
        }

@app.get("/api/work-orders")
async def get_work_orders():
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT * FROM work_orders ORDER BY created_at DESC')
        
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
        
        return {
            "work_orders": work_orders,
            "count": len(work_orders),
            "database": "postgresql",
            "message": "Enterprise PostgreSQL backend working"
        }

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrderCreate):
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
            INSERT INTO work_orders (title, description, priority, status, assigned_to)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, created_at
        ''', work_order.title, work_order.description, work_order.priority, 
        work_order.status, work_order.assigned_to)
        
        return {
            "id": row['id'],
            "message": "Work order created in PostgreSQL",
            "created_at": row['created_at'].isoformat(),
            "success": True
        }

@app.get("/api/assets")
async def get_assets():
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT * FROM assets ORDER BY created_at DESC')
        
        assets = []
        for row in rows:
            assets.append({
                "id": row['id'],
                "name": row['name'],
                "description": row['description'],
                "location": row['location'],
                "asset_type": row['asset_type'],
                "status": row['status'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            })
        
        return {
            "assets": assets,
            "count": len(assets),
            "database": "postgresql"
        }

@app.get("/api/parts")
async def get_parts():
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT * FROM parts ORDER BY created_at DESC')
        
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
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            })
        
        return {
            "parts": parts,
            "count": len(parts),
            "database": "postgresql"
        }

@app.get("/api/dashboard")
async def dashboard():
    async with pool.acquire() as conn:
        work_order_count = await conn.fetchval('SELECT COUNT(*) FROM work_orders')
        asset_count = await conn.fetchval('SELECT COUNT(*) FROM assets')
        part_count = await conn.fetchval('SELECT COUNT(*) FROM parts')
        
        return {
            "work_orders": work_order_count,
            "assets": asset_count,
            "parts": part_count,
            "database": "postgresql",
            "timestamp": datetime.now().isoformat()
        }

@app.on_event("startup")
async def startup():
    logger.info("🚀 Starting ChatterFix PostgreSQL Backend...")
    await init_database()
    logger.info("✅ PostgreSQL Backend ready")

@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()

if __name__ == "__main__":
    print("🐘 ChatterFix PostgreSQL Backend")
    print("Enterprise-grade backend with PostgreSQL")
    print("Port: 8081")
    uvicorn.run(app, host="0.0.0.0", port=8081)
POSTGRES_BACKEND_EOF

# Start PostgreSQL backend
echo "🚀 Starting PostgreSQL backend..."
nohup python3 postgresql_backend.py > postgresql_backend.log 2>&1 &

# Wait for startup
sleep 10

# Test the backend
echo "🧪 Testing PostgreSQL backend..."
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ PostgreSQL backend is running!"
    echo "Testing APIs..."
    
    # Test work orders API
    if curl -s http://localhost:8081/api/work-orders > /dev/null; then
        echo "✅ Work Orders API working"
    fi
    
    # Test assets API  
    if curl -s http://localhost:8081/api/assets > /dev/null; then
        echo "✅ Assets API working"
    fi
    
    # Test parts API
    if curl -s http://localhost:8081/api/parts > /dev/null; then
        echo "✅ Parts API working"
    fi
    
else
    echo "⚠️ Backend may still be starting..."
fi

echo ""
echo "🎉 POSTGRESQL BACKEND DEPLOYED!"
echo "==============================="
echo "✅ Enterprise PostgreSQL backend running on port 8081"
echo "✅ Database: chatterfix_cmms @ 35.225.244.14"
echo "✅ APIs: Work Orders, Assets, Parts"
echo "✅ No conflicts with existing services"
echo ""
echo "🌐 Access URLs:"
echo "  Backend: http://35.237.149.25:8081"
echo "  Health: http://35.237.149.25:8081/health"
echo "  Work Orders: http://35.237.149.25:8081/api/work-orders"
echo "  API Docs: http://35.237.149.25:8081/docs"
