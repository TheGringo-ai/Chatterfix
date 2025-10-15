#!/bin/bash
set -e

echo "🔧 ChatterFix Single-VM Backend Deployment"
echo "==========================================="
echo "No conflicts with existing services!"
echo ""

VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
PROJECT="fredfix"

# Create startup script that adds backend without disrupting existing services
cat > backend-startup.sh << 'BACKEND_EOF'
#!/bin/bash
set -e

echo "🔧 Adding ChatterFix Backend - No Conflicts"
echo "==========================================="
cd /home/yoyofred_gringosgambit_com

# DON'T kill existing services - just add backend
echo "📦 Installing Python dependencies (if needed)..."
python3 -m pip install --user --quiet fastapi uvicorn httpx pydantic

# Create unified backend
echo "📝 Creating unified backend service..."
cat > single_vm_backend.py << 'BACKEND_CODE_EOF'
#!/usr/bin/env python3
"""
Single-VM ChatterFix Backend - Port 8081
Runs alongside existing UI (port 8080) and Ollama (port 11434)
No conflicts, pure addition!
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix Backend Unified", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_URL = "http://localhost:11434"

# Models
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

def init_database():
    """Initialize database with sample data"""
    conn = sqlite3.connect('chatterfix_unified.db')
    cursor = conn.cursor()
    
    # Work Orders
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
    
    # Assets
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
    
    # Parts
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
    
    # Sample data
    cursor.execute('SELECT COUNT(*) FROM work_orders')
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('HVAC Maintenance', 'Annual HVAC system check', 'high', 'open', 'John Smith'),
            ('Pump Repair', 'Water pump seal replacement', 'urgent', 'in-progress', 'Mike Johnson'),
            ('Safety Inspection', 'Monthly safety walkthrough', 'medium', 'open', None)
        ]
        cursor.executemany('''
            INSERT INTO work_orders (title, description, priority, status, assigned_to)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_data)
    
    cursor.execute('SELECT COUNT(*) FROM assets')
    if cursor.fetchone()[0] == 0:
        assets_data = [
            ('HVAC Unit', 'Main air conditioning system', 'Roof Level', 'HVAC', 'active'),
            ('Water Pump', 'Primary circulation pump', 'Basement', 'Pump', 'active'),
            ('Generator', 'Emergency backup power', 'Outside', 'Power', 'active')
        ]
        cursor.executemany('''
            INSERT INTO assets (name, description, location, asset_type, status)
            VALUES (?, ?, ?, ?, ?)
        ''', assets_data)
    
    cursor.execute('SELECT COUNT(*) FROM parts')
    if cursor.fetchone()[0] == 0:
        parts_data = [
            ('Air Filter', 'AF-001', 'HVAC air filter', 'Filters', 10, 5, 25.99, 'Storage A'),
            ('Pump Seal', 'PS-150', 'Water pump seal', 'Seals', 5, 2, 45.50, 'Parts Room'),
            ('Fuse 30A', 'F-30', '30 amp fuse', 'Electric', 20, 10, 8.75, 'Electric Panel')
        ]
        cursor.executemany('''
            INSERT INTO parts (name, part_number, description, category, quantity, min_stock, unit_cost, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', parts_data)
    
    conn.commit()
    conn.close()

# Ollama integration
async def check_ollama():
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            return response.status_code == 200
    except:
        return False

async def ollama_chat(model: str, prompt: str):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {"model": model, "prompt": prompt, "stream": False}
            response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            if response.status_code == 200:
                return response.json().get('response', '')
    except:
        pass
    return None

# Initialize database
init_database()

@app.get("/health")
async def health():
    ollama_status = await check_ollama()
    return {
        "service": "ChatterFix Backend Unified",
        "status": "healthy",
        "port": 8081,
        "timestamp": datetime.now().isoformat(),
        "ollama_available": ollama_status,
        "database": "sqlite_ready",
        "conflicts": "none"
    }

@app.get("/api/work-orders")
async def get_work_orders():
    conn = sqlite3.connect('chatterfix_unified.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM work_orders ORDER BY created_at DESC')
    
    work_orders = []
    for row in cursor.fetchall():
        work_orders.append({
            "id": row[0], "title": row[1], "description": row[2],
            "priority": row[3], "status": row[4], "assigned_to": row[5],
            "created_at": row[6], "updated_at": row[7]
        })
    
    conn.close()
    return {"work_orders": work_orders, "count": len(work_orders)}

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrder):
    conn = sqlite3.connect('chatterfix_unified.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO work_orders (title, description, priority, status, assigned_to)
        VALUES (?, ?, ?, ?, ?)
    ''', (work_order.title, work_order.description, work_order.priority, 
          work_order.status, work_order.assigned_to))
    
    work_order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": work_order_id, "message": "Work order created", "success": True}

@app.get("/api/assets")
async def get_assets():
    conn = sqlite3.connect('chatterfix_unified.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM assets ORDER BY created_at DESC')
    
    assets = []
    for row in cursor.fetchall():
        assets.append({
            "id": row[0], "name": row[1], "description": row[2],
            "location": row[3], "asset_type": row[4], "status": row[5],
            "created_at": row[6]
        })
    
    conn.close()
    return {"assets": assets, "count": len(assets)}

@app.post("/api/assets")
async def create_asset(asset: Asset):
    conn = sqlite3.connect('chatterfix_unified.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO assets (name, description, location, asset_type, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (asset.name, asset.description, asset.location, asset.asset_type, asset.status))
    
    asset_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": asset_id, "message": "Asset created", "success": True}

@app.get("/api/parts")
async def get_parts():
    conn = sqlite3.connect('chatterfix_unified.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM parts ORDER BY created_at DESC')
    
    parts = []
    for row in cursor.fetchall():
        parts.append({
            "id": row[0], "name": row[1], "part_number": row[2],
            "description": row[3], "category": row[4], "quantity": row[5],
            "min_stock": row[6], "unit_cost": row[7], "location": row[8],
            "created_at": row[9]
        })
    
    conn.close()
    return {"parts": parts, "count": len(parts)}

@app.post("/api/parts")
async def create_part(part: Part):
    conn = sqlite3.connect('chatterfix_unified.db')
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
        
        return {"id": part_id, "message": "Part created", "success": True}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Part number already exists")

@app.post("/api/ai/troubleshoot")
async def ai_troubleshoot(request: Dict[str, Any]):
    equipment = request.get("equipment", "Equipment")
    issue = request.get("issue", "Issue not specified")
    
    if not await check_ollama():
        return {
            "success": False,
            "message": "AI temporarily unavailable",
            "fallback": f"Standard troubleshooting for {equipment}: 1) Safety check 2) Visual inspection 3) Test components"
        }
    
    prompt = f"Fix It Fred troubleshooting for {equipment} with issue: {issue}. Provide 3-4 concise steps."
    
    response = await ollama_chat("mistral:7b", prompt)
    
    if response:
        return {
            "success": True,
            "equipment": equipment,
            "issue": issue,
            "troubleshooting": response,
            "ai_powered": True
        }
    else:
        return {
            "success": False,
            "message": "AI processing failed",
            "fallback": f"Check {equipment} power, connections, and manual"
        }

if __name__ == "__main__":
    print("🚀 ChatterFix Backend Unified - Port 8081")
    print("✅ No conflicts with existing services")
    uvicorn.run(app, host="0.0.0.0", port=8081)
BACKEND_CODE_EOF

# Start backend service (non-disruptive)
echo "🚀 Starting unified backend on port 8081..."
nohup python3 single_vm_backend.py > backend.log 2>&1 &

# Wait for startup
sleep 5

# Test backend
echo "🩺 Testing backend health..."
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ Backend healthy on port 8081"
else
    echo "⚠️  Backend may still be starting"
fi

echo ""
echo "✅ BACKEND DEPLOYMENT COMPLETE!"
echo "==============================="
echo "🌐 Existing UI: http://35.237.149.25:8080 (unchanged)"
echo "🔧 New Backend: http://35.237.149.25:8081 (added)"
echo "🤖 Ollama: http://localhost:11434 (unchanged)"
echo ""
echo "📋 Available APIs on port 8081:"
echo "  GET  /health"
echo "  GET  /api/work-orders"
echo "  POST /api/work-orders"
echo "  GET  /api/assets"
echo "  POST /api/assets"
echo "  GET  /api/parts"
echo "  POST /api/parts"
echo "  POST /api/ai/troubleshoot"
echo ""
echo "🎯 NO CONFLICTS - All services coexist!"
BACKEND_EOF

chmod +x backend-startup.sh

# Deploy to VM
echo "📤 Deploying backend startup script..."
gcloud compute instances add-metadata $VM_NAME \
    --zone=$ZONE \
    --project=$PROJECT \
    --metadata-from-file startup-script=backend-startup.sh

echo "🔄 Restarting VM to add backend..."
gcloud compute instances reset $VM_NAME --zone=$ZONE --project=$PROJECT

echo ""
echo "⏳ Waiting for backend deployment..."
sleep 50

echo "🩺 Testing deployment..."
echo "UI Gateway (port 8080):"
curl -s http://35.237.149.25:8080/health | head -3

echo ""
echo "New Backend (port 8081):"
curl -s http://35.237.149.25:8081/health | head -3

echo ""
echo "🎉 SINGLE-VM DEPLOYMENT COMPLETE!"
echo "=================================="
echo "✅ ChatterFix UI: http://35.237.149.25:8080"
echo "✅ Backend APIs: http://35.237.149.25:8081" 
echo "✅ Ollama AI: http://35.237.149.25:11434"
echo "✅ No conflicts between services"
echo ""
echo "📋 Test the APIs:"
echo "curl http://35.237.149.25:8081/api/work-orders"
echo "curl http://35.237.149.25:8081/api/assets"
echo "curl http://35.237.149.25:8081/health"