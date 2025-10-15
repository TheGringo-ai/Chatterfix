#!/usr/bin/env python3
"""
Single-VM ChatterFix Backend
Unified backend service that runs alongside existing UI on different port
No conflicts with Ollama or existing services
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import sqlite3
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix Backend Unified", version="1.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for single VM
VM_IP = "35.237.149.25"
OLLAMA_INTERNAL_URL = "http://localhost:11434"  # Internal to VM
POSTGRES_HOST = "35.225.244.14"
POSTGRES_PASSWORD = "REDACTED_DB_PASSWORD"

# Pydantic models
class WorkOrder(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None

class Asset(BaseModel):
    name: str
    description: str = ""
    location: str = ""
    asset_type: str = ""
    status: str = "active"

class Part(BaseModel):
    name: str
    part_number: str
    description: str = ""
    category: str = ""
    quantity: int = 0
    min_stock: int = 0
    unit_cost: float = 0.0
    location: str = ""

class DatabaseManager:
    def __init__(self):
        self.db_path = "chatterfix_backend.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with all tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Work Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                assigned_to TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                location TEXT,
                asset_type TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Parts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                part_number TEXT UNIQUE,
                description TEXT,
                category TEXT,
                quantity INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                unit_cost REAL DEFAULT 0.0,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample data if tables are empty
        cursor.execute('SELECT COUNT(*) FROM work_orders')
        if cursor.fetchone()[0] == 0:
            sample_work_orders = [
                ('HVAC System Maintenance', 'Annual maintenance check for building HVAC system', 'high', 'open', 'John Smith'),
                ('Conveyor Belt Repair', 'Replace worn belt on production line 3', 'urgent', 'in-progress', 'Mike Johnson'),
                ('Pump Inspection', 'Monthly inspection of water pumps', 'medium', 'open', None),
                ('Electrical Panel Check', 'Safety inspection of main electrical panel', 'high', 'completed', 'Sarah Wilson'),
                ('Boiler Maintenance', 'Quarterly boiler inspection and cleaning', 'medium', 'open', 'Tom Brown')
            ]
            
            cursor.executemany('''
                INSERT INTO work_orders (title, description, priority, status, assigned_to)
                VALUES (?, ?, ?, ?, ?)
            ''', sample_work_orders)
        
        cursor.execute('SELECT COUNT(*) FROM assets')
        if cursor.fetchone()[0] == 0:
            sample_assets = [
                ('Main HVAC Unit', 'Central air conditioning system', 'Building A - Roof', 'HVAC', 'active'),
                ('Conveyor Belt #3', 'Production line conveyor system', 'Factory Floor - Line 3', 'Manufacturing', 'active'),
                ('Water Pump Station', 'Main water circulation pumps', 'Basement - Utility Room', 'Pumping', 'active'),
                ('Emergency Generator', 'Backup power generation unit', 'Outdoor - East Side', 'Power', 'active'),
                ('Boiler Unit #1', 'Primary heating boiler', 'Basement - Boiler Room', 'Heating', 'active')
            ]
            
            cursor.executemany('''
                INSERT INTO assets (name, description, location, asset_type, status)
                VALUES (?, ?, ?, ?, ?)
            ''', sample_assets)
        
        cursor.execute('SELECT COUNT(*) FROM parts')
        if cursor.fetchone()[0] == 0:
            sample_parts = [
                ('HVAC Filter', 'FLT-001', 'High-efficiency air filter', 'Filters', 25, 10, 45.99, 'Warehouse A-3'),
                ('Conveyor Belt', 'CBT-203', 'Heavy-duty rubber conveyor belt', 'Belts', 2, 1, 1250.00, 'Storage Room B'),
                ('Water Pump Seal', 'WPS-150', 'Rubber seal for water pumps', 'Seals', 15, 5, 89.50, 'Parts Cabinet 1'),
                ('Electrical Fuse', 'EF-30A', '30 Amp electrical fuse', 'Electrical', 50, 20, 12.75, 'Electrical Cabinet'),
                ('Boiler Gasket', 'BG-450', 'High-temperature boiler gasket', 'Gaskets', 8, 3, 156.99, 'Boiler Parts Storage')
            ]
            
            cursor.executemany('''
                INSERT INTO parts (name, part_number, description, category, quantity, min_stock, unit_cost, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_parts)
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized with sample data")

class OllamaClient:
    def __init__(self):
        self.base_url = f"{OLLAMA_INTERNAL_URL}/api"
    
    async def is_available(self):
        """Check if Ollama is available internally"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/tags")
                return response.status_code == 200
        except:
            return False
    
    async def get_models(self):
        """Get available models"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
        except:
            pass
        return []
    
    async def chat(self, model: str, prompt: str):
        """Chat with Ollama model"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = await client.post(f"{self.base_url}/generate", json=payload)
                if response.status_code == 200:
                    return response.json().get('response', '')
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
        return None

# Initialize services
db = DatabaseManager()
ollama = OllamaClient()

@app.get("/health")
async def health():
    """Backend health check"""
    ollama_available = await ollama.is_available()
    models = await ollama.get_models()
    
    return {
        "service": "ChatterFix Backend Unified",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "sqlite_ready",
        "ollama": {
            "available": ollama_available,
            "models": models
        },
        "features": ["work_orders", "assets", "parts", "ai_integration"]
    }

# Work Orders API
@app.get("/api/work-orders")
async def get_work_orders():
    """Get all work orders"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM work_orders ORDER BY created_at DESC')
    
    work_orders = []
    for row in cursor.fetchall():
        work_orders.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "priority": row[3],
            "status": row[4],
            "assigned_to": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        })
    
    conn.close()
    return {"work_orders": work_orders, "count": len(work_orders)}

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrder):
    """Create new work order"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO work_orders (title, description, priority, status, assigned_to)
        VALUES (?, ?, ?, ?, ?)
    ''', (work_order.title, work_order.description, work_order.priority, 
          work_order.status, work_order.assigned_to))
    
    work_order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": work_order_id, "message": "Work order created successfully"}

@app.get("/api/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get specific work order"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM work_orders WHERE id = ?', (work_order_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "priority": row[3],
        "status": row[4],
        "assigned_to": row[5],
        "created_at": row[6],
        "updated_at": row[7]
    }

# Assets API
@app.get("/api/assets")
async def get_assets():
    """Get all assets"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM assets ORDER BY created_at DESC')
    
    assets = []
    for row in cursor.fetchall():
        assets.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "location": row[3],
            "asset_type": row[4],
            "status": row[5],
            "created_at": row[6]
        })
    
    conn.close()
    return {"assets": assets, "count": len(assets)}

@app.post("/api/assets")
async def create_asset(asset: Asset):
    """Create new asset"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO assets (name, description, location, asset_type, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (asset.name, asset.description, asset.location, asset.asset_type, asset.status))
    
    asset_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": asset_id, "message": "Asset created successfully"}

# Parts API
@app.get("/api/parts")
async def get_parts():
    """Get all parts"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM parts ORDER BY created_at DESC')
    
    parts = []
    for row in cursor.fetchall():
        parts.append({
            "id": row[0],
            "name": row[1],
            "part_number": row[2],
            "description": row[3],
            "category": row[4],
            "quantity": row[5],
            "min_stock": row[6],
            "unit_cost": row[7],
            "location": row[8],
            "created_at": row[9]
        })
    
    conn.close()
    return {"parts": parts, "count": len(parts)}

@app.post("/api/parts")
async def create_part(part: Part):
    """Create new part"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO parts (name, part_number, description, category, quantity, min_stock, unit_cost, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (part.name, part.part_number, part.description, part.category, 
              part.quantity, part.min_stock, part.unit_cost, part.location))
        
        part_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": part_id, "message": "Part created successfully"}
    
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Part number already exists")

# AI Integration
@app.get("/api/ai/status")
async def ai_status():
    """AI service status"""
    ollama_available = await ollama.is_available()
    models = await ollama.get_models()
    
    return {
        "ai_available": ollama_available,
        "ollama_models": models,
        "ai_features": ["troubleshooting", "predictive_analysis", "recommendations"]
    }

@app.post("/api/ai/troubleshoot")
async def ai_troubleshoot(request: Dict[str, Any]):
    """AI troubleshooting endpoint"""
    equipment = request.get("equipment", "Unknown Equipment")
    issue = request.get("issue", "No issue description provided")
    
    # Check if Ollama is available
    if not await ollama.is_available():
        return {
            "success": False,
            "message": "AI service temporarily unavailable",
            "fallback_advice": f"For {equipment} issues: 1) Check power connections 2) Inspect for visible damage 3) Consult manual 4) Contact maintenance team"
        }
    
    models = await ollama.get_models()
    if not models:
        return {
            "success": False,
            "message": "AI models not available",
            "fallback_advice": f"For {equipment} issues: 1) Safety first - follow lockout/tagout 2) Visual inspection 3) Check system parameters"
        }
    
    # Use first available model
    model = models[0]
    prompt = f"""You are Fix It Fred, an expert maintenance technician.

Equipment: {equipment}
Issue: {issue}

Provide concise troubleshooting steps:
1. Immediate safety actions
2. Diagnostic steps (3-4 steps)
3. Common solutions
4. When to call for help

Keep response under 200 words."""
    
    response = await ollama.chat(model, prompt)
    
    if response:
        return {
            "success": True,
            "equipment": equipment,
            "issue": issue,
            "model_used": model,
            "troubleshooting_steps": response,
            "ai_powered": True
        }
    else:
        return {
            "success": False,
            "message": "AI processing failed",
            "fallback_advice": f"Standard troubleshooting for {equipment}: Check connections, inspect for damage, verify settings, test components systematically."
        }

if __name__ == "__main__":
    print("🚀 Starting ChatterFix Backend Unified...")
    print(f"🌐 Backend API: http://{VM_IP}:8081")
    print(f"🤖 Ollama Integration: {OLLAMA_INTERNAL_URL}")
    print("📋 Features: Work Orders, Assets, Parts, AI Integration")
    print("🔗 No conflicts - runs alongside existing UI on port 8080")
    
    # Run on port 8081 to avoid conflicts
    uvicorn.run(app, host="0.0.0.0", port=8081)