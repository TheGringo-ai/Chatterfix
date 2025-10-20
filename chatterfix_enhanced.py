#!/usr/bin/env python3
"""
ChatterFix CMMS - Enhanced with Complete Form Functionality
Includes all form submission endpoints for assets, work orders, parts management
"""
import os
import json
import sqlite3
import uvicorn
import requests
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatterFix CMMS - Enhanced",
    description="AI-Powered Maintenance Management System with Complete Forms",
    version="4.0.0"
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
def init_database():
    """Initialize SQLite database with all tables"""
    db_path = Path("data/chatterfix.db")
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            asset_id INTEGER,
            technician TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
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
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            part_number TEXT UNIQUE,
            quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 5,
            price REAL DEFAULT 0.0,
            location TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM work_orders")
    if cursor.fetchone()[0] == 0:
        sample_work_orders = [
            ("Pump Maintenance", "Regular maintenance check", "in_progress", "high", 1, "John Smith"),
            ("Filter Replacement", "Replace air filter", "assigned", "medium", 2, "Sarah Johnson"),
            ("Belt Inspection", "Check belt tension", "pending", "low", 3, "Mike Wilson")
        ]
        cursor.executemany(
            "INSERT INTO work_orders (title, description, status, priority, asset_id, technician) VALUES (?, ?, ?, ?, ?, ?)",
            sample_work_orders
        )
    
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
    
    cursor.execute("SELECT COUNT(*) FROM parts")
    if cursor.fetchone()[0] == 0:
        sample_parts = [
            ("Oil Filter", "OF-001", 15, 5, 25.99, "A1-01", "filters"),
            ("V-Belt", "VB-200", 3, 10, 45.00, "B2-05", "belts"),
            ("Bearing", "BR-150", 8, 5, 120.50, "C1-03", "bearings"),
            ("Air Filter", "AF-001", 22, 8, 18.75, "A1-02", "filters")
        ]
        cursor.executemany(
            "INSERT INTO parts (name, part_number, quantity, min_stock, price, location, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_parts
        )
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized successfully")

# Initialize database on startup
init_database()

def get_db():
    """Get database connection"""
    db_path = Path("data/chatterfix.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Data models
class WorkOrderCreate(BaseModel):
    title: str
    description: str
    asset_id: Optional[int] = None
    priority: str = "medium"
    technician: Optional[str] = None

class AssetCreate(BaseModel):
    name: str
    type: str
    location: str
    status: str = "operational"

class PartCreate(BaseModel):
    name: str
    part_number: str
    quantity: int
    min_stock: int = 5
    price: float = 0.0
    location: str
    category: str

# Fix It Fred AI Integration
async def get_ai_assistance(message: str, user_role: str = "technician", context: str = None):
    """Get AI assistance from Fix It Fred"""
    try:
        response = requests.post(
            "http://localhost:9000/chat",
            json={"message": message, "user_role": user_role, "context": context},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("response", "AI service unavailable")
    except:
        pass
    return "AI assistant temporarily unavailable"

# Page Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
    
    # Get dashboard stats
    cursor.execute("SELECT COUNT(*) FROM work_orders WHERE status != 'completed'")
    active_workorders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM assets")
    total_assets = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parts WHERE quantity > min_stock")
    parts_in_stock = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM work_orders ORDER BY created_at DESC LIMIT 5")
    recent_work_orders = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM assets ORDER BY health_score ASC LIMIT 5")
    critical_assets = [dict(row) for row in cursor.fetchall()]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_workorders": active_workorders,
        "total_assets": total_assets,
        "parts_in_stock": parts_in_stock,
        "recent_work_orders": recent_work_orders,
        "critical_assets": critical_assets,
        "system_health": 95
    })

@app.get("/work-orders", response_class=HTMLResponse)
async def work_orders(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT wo.*, a.name as asset_name 
        FROM work_orders wo 
        LEFT JOIN assets a ON wo.asset_id = a.id 
        ORDER BY wo.created_at DESC
    """)
    work_orders = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM assets ORDER BY name")
    assets = [dict(row) for row in cursor.fetchall()]
    
    return templates.TemplateResponse("work_orders.html", {
        "request": request,
        "work_orders": work_orders,
        "assets": assets
    })

@app.get("/assets", response_class=HTMLResponse)
async def assets(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM assets ORDER BY name")
    assets = [dict(row) for row in cursor.fetchall()]
    
    return templates.TemplateResponse("assets.html", {
        "request": request,
        "assets": assets
    })

@app.get("/parts", response_class=HTMLResponse)
async def parts(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM parts ORDER BY name")
    parts = [dict(row) for row in cursor.fetchall()]
    
    return templates.TemplateResponse("parts.html", {
        "request": request,
        "parts": parts
    })

@app.get("/technician", response_class=HTMLResponse)
async def technician(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM work_orders WHERE status IN ('assigned', 'in_progress') ORDER BY priority DESC, created_at")
    assigned_work_orders = [dict(row) for row in cursor.fetchall()]
    
    return templates.TemplateResponse("technician.html", {
        "request": request,
        "work_orders": assigned_work_orders
    })

@app.get("/manager", response_class=HTMLResponse)
async def manager(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
    
    # Get various manager stats
    cursor.execute("SELECT status, COUNT(*) as count FROM work_orders GROUP BY status")
    status_stats = dict(cursor.fetchall())
    
    cursor.execute("SELECT priority, COUNT(*) as count FROM work_orders WHERE status != 'completed' GROUP BY priority")
    priority_stats = dict(cursor.fetchall())
    
    return templates.TemplateResponse("manager.html", {
        "request": request,
        "status_stats": status_stats,
        "priority_stats": priority_stats
    })

# Form Submission Routes
@app.post("/work-orders/create")
async def create_work_order(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    asset_id: Optional[int] = Form(None),
    priority: str = Form("medium"),
    technician: Optional[str] = Form(None),
    db=Depends(get_db)
):
    """Create a new work order"""
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO work_orders (title, description, asset_id, priority, technician)
        VALUES (?, ?, ?, ?, ?)
    """, (title, description, asset_id, priority, technician))
    db.commit()
    
    logger.info(f"✅ Work order created: {title}")
    return RedirectResponse(url="/work-orders", status_code=303)

@app.post("/assets/create")
async def create_asset(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    location: str = Form(...),
    status: str = Form("operational"),
    db=Depends(get_db)
):
    """Create a new asset"""
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO assets (name, type, location, status)
        VALUES (?, ?, ?, ?)
    """, (name, type, location, status))
    db.commit()
    
    logger.info(f"✅ Asset created: {name}")
    return RedirectResponse(url="/assets", status_code=303)

@app.post("/parts/create")
async def create_part(
    request: Request,
    name: str = Form(...),
    part_number: str = Form(...),
    quantity: int = Form(...),
    min_stock: int = Form(5),
    price: float = Form(0.0),
    location: str = Form(...),
    category: str = Form(...),
    db=Depends(get_db)
):
    """Create a new part"""
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO parts (name, part_number, quantity, min_stock, price, location, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, part_number, quantity, min_stock, price, location, category))
        db.commit()
        logger.info(f"✅ Part created: {name}")
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Part number already exists")
    
    return RedirectResponse(url="/parts", status_code=303)

# API Routes
@app.post("/api/chat")
async def chat(request: Request, message: str = Form(...), user_role: str = Form("technician")):
    """Chat with Fix It Fred AI"""
    response = await get_ai_assistance(message, user_role)
    return JSONResponse({"response": response})

@app.get("/api/work-orders")
async def api_work_orders(db=Depends(get_db)):
    """Get all work orders"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM work_orders ORDER BY created_at DESC")
    return [dict(row) for row in cursor.fetchall()]

@app.get("/api/assets")
async def api_assets(db=Depends(get_db)):
    """Get all assets"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM assets ORDER BY name")
    return [dict(row) for row in cursor.fetchall()]

@app.get("/api/parts")
async def api_parts(db=Depends(get_db)):
    """Get all parts"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM parts ORDER BY name")
    return [dict(row) for row in cursor.fetchall()]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ChatterFix CMMS Enhanced", "version": "4.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)