#!/usr/bin/env python3
"""
ChatterFix CMMS - Clean Modular Main Application
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sqlite3
import datetime
import os
from typing import Optional, List

# Initialize FastAPI app
app = FastAPI(title="ChatterFix CMMS", version="4.0.0")

# Database configuration
DATABASE_PATH = "data/cmms.db"

class WorkOrder(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    status: str = "open"
    priority: str = "medium"
    asset_id: Optional[int] = None
    technician: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class Asset(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    location: str
    status: str = "operational"
    health_score: Optional[int] = 100
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PartInventory(BaseModel):
    id: Optional[int] = None
    name: str
    part_number: str
    quantity: int
    min_stock: int
    price: float
    location: str
    category: str

def init_database():
    """Initialize SQLite database with tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Work Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'medium',
            asset_id INTEGER,
            technician TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            status TEXT DEFAULT 'operational',
            health_score INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Parts inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            part_number TEXT UNIQUE,
            quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            price REAL DEFAULT 0.0,
            location TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        sample_assets = [
            ("Pump #1", "Pump", "Building A", "operational", 85),
            ("HVAC Unit A", "HVAC", "Building B", "operational", 92),
            ("Conveyor #3", "Conveyor", "Warehouse", "maintenance", 78)
        ]
        cursor.executemany(
            "INSERT INTO assets (name, type, location, status, health_score) VALUES (?, ?, ?, ?, ?)",
            sample_assets
        )
    
    cursor.execute("SELECT COUNT(*) FROM work_orders")
    if cursor.fetchone()[0] == 0:
        sample_work_orders = [
            ("Pump Maintenance", "Regular maintenance check", "in_progress", "high", 1, "John Smith"),
            ("Filter Replacement", "Replace air filter in HVAC", "open", "medium", 2, "Jane Doe"),
            ("Belt Inspection", "Inspect conveyor belt", "completed", "low", 3, "Bob Wilson")
        ]
        cursor.executemany(
            "INSERT INTO work_orders (title, description, status, priority, asset_id, technician) VALUES (?, ?, ?, ?, ?, ?)",
            sample_work_orders
        )
    
    cursor.execute("SELECT COUNT(*) FROM parts")
    if cursor.fetchone()[0] == 0:
        sample_parts = [
            ("Motor Oil", "OIL-001", 15, 5, 25.99, "A1-01", "lubricants"),
            ("Belt Drive", "BELT-002", 8, 3, 45.50, "A1-03", "mechanical"),
            ("Hydraulic Fluid", "HYD-003", 12, 4, 35.75, "A2-01", "fluids"),
            ("Air Filter", "AF-001", 22, 8, 18.75, "A1-02", "filters")
        ]
        cursor.executemany(
            "INSERT INTO parts (name, part_number, quantity, min_stock, price, location, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_parts
        )
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ChatterFix CMMS Enhanced", "version": "4.0.0"}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #032B44; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stat-number { font-size: 2rem; font-weight: bold; color: #032B44; }
            .stat-label { color: #666; margin-top: 5px; }
            .content { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .panel h3 { margin-top: 0; color: #032B44; }
            .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
            .btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 ChatterFix CMMS</h1>
                <p>AI-Enhanced Maintenance Management System</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="work-orders-count">-</div>
                    <div class="stat-label">Active Work Orders</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="assets-count">-</div>
                    <div class="stat-label">Assets Monitored</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="parts-count">-</div>
                    <div class="stat-label">Parts in Inventory</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">98%</div>
                    <div class="stat-label">System Uptime</div>
                </div>
            </div>
            
            <div class="content">
                <div class="panel">
                    <h3>Recent Work Orders</h3>
                    <div id="recent-work-orders">Loading...</div>
                    <a href="/work-orders" class="btn">View All Work Orders</a>
                </div>
                
                <div class="panel">
                    <h3>Asset Status</h3>
                    <div id="asset-status">Loading...</div>
                    <a href="/assets" class="btn">View All Assets</a>
                </div>
            </div>
        </div>
        
        <script>
            // Load dashboard data
            fetch('/api/work-orders').then(r => r.json()).then(data => {
                document.getElementById('work-orders-count').textContent = data.length;
                const recent = data.slice(0, 3).map(wo => 
                    `<div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        <strong>${wo.title}</strong><br>
                        <small>Status: ${wo.status} | Priority: ${wo.priority}</small>
                    </div>`
                ).join('');
                document.getElementById('recent-work-orders').innerHTML = recent || 'No work orders';
            });
            
            fetch('/api/assets').then(r => r.json()).then(data => {
                document.getElementById('assets-count').textContent = data.length;
                const status = data.slice(0, 3).map(asset => 
                    `<div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        <strong>${asset.name}</strong><br>
                        <small>Status: ${asset.status} | Health: ${asset.health_score}%</small>
                    </div>`
                ).join('');
                document.getElementById('asset-status').innerHTML = status || 'No assets';
            });
            
            fetch('/api/parts').then(r => r.json()).then(data => {
                document.getElementById('parts-count').textContent = data.length;
            });
        </script>
    </body>
    </html>
    """

# API Routes
@app.get("/api/work-orders")
async def get_work_orders():
    """Get all work orders"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM work_orders ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'title', 'description', 'status', 'priority', 'asset_id', 'technician', 'created_at', 'updated_at']
    return [dict(zip(columns, row)) for row in rows]

@app.get("/api/assets")
async def get_assets():
    """Get all assets"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'name', 'type', 'location', 'status', 'health_score', 'created_at', 'updated_at']
    return [dict(zip(columns, row)) for row in rows]

@app.get("/api/parts")
async def get_parts():
    """Get all parts"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parts ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'name', 'part_number', 'quantity', 'min_stock', 'price', 'location', 'category', 'created_at', 'updated_at']
    return [dict(zip(columns, row)) for row in rows]

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrder):
    """Create new work order"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO work_orders (title, description, status, priority, asset_id, technician)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (work_order.title, work_order.description, work_order.status, 
          work_order.priority, work_order.asset_id, work_order.technician))
    
    work_order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": work_order_id, "message": "Work order created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)