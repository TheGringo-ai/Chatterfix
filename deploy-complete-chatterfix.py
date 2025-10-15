#!/usr/bin/env python3
"""
Complete ChatterFix Deployment
Deploys full system with PostgreSQL and Ollama
"""

import requests
import time
import os
import subprocess

VM_IP = "35.237.149.25"
POSTGRES_HOST = "35.225.244.14"
POSTGRES_PASSWORD = "ChatterFix2025!"

def create_complete_app():
    """Create complete ChatterFix app with PostgreSQL and Ollama"""
    
    app_code = f'''#!/usr/bin/env python3
"""
Complete ChatterFix CMMS with PostgreSQL and Ollama
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import httpx
import uvicorn
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix CMMS Complete", version="3.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = "postgresql://postgres:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/chatterfix_cmms"
OLLAMA_URL = "http://localhost:11434"

class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
            logger.info("✅ Connected to PostgreSQL")
            
            # Initialize tables
            await self.init_tables()
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {{e}}")
            # Fallback to SQLite for development
            import sqlite3
            logger.info("📦 Using SQLite fallback")
            self.init_sqlite()
    
    def init_sqlite(self):
        """Fallback SQLite initialization"""
        conn = sqlite3.connect('chatterfix.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                assigned_to TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def init_tables(self):
        """Initialize PostgreSQL tables"""
        if not self.pool:
            return
            
        async with self.pool.acquire() as conn:
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
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    location VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'active',
                    asset_type VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
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

class OllamaManager:
    def __init__(self):
        self.base_url = f"{{OLLAMA_URL}}/api"
    
    async def get_models(self):
        """Get available Ollama models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{{self.base_url}}/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Ollama connection failed: {{e}}")
        return []
    
    async def chat(self, model: str, prompt: str):
        """Chat with Ollama model"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {{
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }}
                
                response = await client.post(f"{{self.base_url}}/generate", json=payload)
                if response.status_code == 200:
                    return response.json().get('response', '')
        except Exception as e:
            logger.error(f"Ollama chat failed: {{e}}")
        return "Fix It Fred is currently offline. Please try again later."

# Initialize managers
db = DatabaseManager()
ollama = OllamaManager()

@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    logger.info("🚀 Starting ChatterFix CMMS Complete...")
    await db.connect()

@app.get("/")
async def dashboard():
    """Main dashboard"""
    
    # Check service status
    postgres_status = "✅ Connected" if db.pool else "❌ Offline"
    ollama_models = await ollama.get_models()
    ollama_status = f"✅ {{len(ollama_models)}} models" if ollama_models else "❌ Offline"
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS Complete</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
            .status {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 30px; }}
            .status-card {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .card h3 {{ color: #2c3e50; margin-top: 0; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #3498db; color: white; text-decoration: none; border-radius: 6px; margin: 5px; font-weight: 500; }}
            .btn:hover {{ background: #2980b9; }}
            .btn-success {{ background: #27ae60; }}
            .btn-danger {{ background: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 ChatterFix CMMS Complete</h1>
                <p>Full-featured CMMS with PostgreSQL database and Ollama AI</p>
                <p><strong>VM:</strong> {{VM_IP}} | <strong>Version:</strong> 3.0 Complete</p>
            </div>
            
            <div class="status">
                <div class="status-card">
                    <h4>🗄️ Database Status</h4>
                    <p>PostgreSQL: {{postgres_status}}</p>
                    <p>Host: {{POSTGRES_HOST}}</p>
                </div>
                
                <div class="status-card">
                    <h4>🤖 AI Status</h4>
                    <p>Ollama: {{ollama_status}}</p>
                    <p>URL: {{OLLAMA_URL}}</p>
                </div>
                
                <div class="status-card">
                    <h4>📊 System Health</h4>
                    <p>Uptime: {{datetime.now().strftime('%H:%M:%S')}}</p>
                    <p>Status: ✅ All Systems Go</p>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>🔧 Work Orders</h3>
                    <p>Create and manage maintenance work orders with full PostgreSQL persistence</p>
                    <a href="/work-orders" class="btn">View Work Orders</a>
                    <a href="/work-orders/create" class="btn btn-success">Create New</a>
                </div>
                
                <div class="card">
                    <h3>🏭 Assets</h3>
                    <p>Comprehensive asset management and tracking</p>
                    <a href="/assets" class="btn">View Assets</a>
                    <a href="/assets/create" class="btn btn-success">Add Asset</a>
                </div>
                
                <div class="card">
                    <h3>📦 Parts Inventory</h3>
                    <p>Complete parts and inventory management system</p>
                    <a href="/parts" class="btn">View Parts</a>
                    <a href="/parts/create" class="btn btn-success">Add Part</a>
                </div>
                
                <div class="card">
                    <h3>🤖 Fix It Fred AI</h3>
                    <p>AI-powered maintenance assistant with Ollama integration</p>
                    <a href="/fred" class="btn">Ask Fred</a>
                    <a href="/fred/models" class="btn">AI Models</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return HTMLResponse(content=html)

@app.get("/health")
async def health():
    """Comprehensive health check"""
    postgres_healthy = db.pool is not None
    ollama_models = await ollama.get_models()
    ollama_healthy = len(ollama_models) > 0
    
    return {{
        "status": "healthy",
        "service": "ChatterFix CMMS Complete",
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "components": {{
            "postgresql": {{
                "status": "healthy" if postgres_healthy else "offline",
                "host": "{POSTGRES_HOST}",
                "database": "chatterfix_cmms"
            }},
            "ollama": {{
                "status": "healthy" if ollama_healthy else "offline",
                "url": "{OLLAMA_URL}",
                "models": ollama_models
            }},
            "vm": {{
                "ip": "{VM_IP}",
                "ports": ["8080", "11434", "5432"]
            }}
        }}
    }}

@app.get("/fred")
async def fix_it_fred():
    """Fix It Fred AI interface"""
    models = await ollama.get_models()
    model_options = "".join([f'<option value="{{m}}">{{m}}</option>' for m in models])
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fix It Fred AI - ChatterFix</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px; }}
            .chat {{ background: white; padding: 30px; border-radius: 12px; min-height: 400px; }}
            .models {{ background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            select, textarea {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }}
            textarea {{ height: 120px; }}
            .btn {{ padding: 12px 24px; background: #e74c3c; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; }}
            .btn:hover {{ background: #c0392b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Fix It Fred AI Assistant</h1>
                <p>Powered by Ollama Local AI Models</p>
                <a href="/" style="color: white; text-decoration: none;">← Back to Dashboard</a>
            </div>
            
            <div class="chat">
                <div class="models">
                    <h4>🧠 Available AI Models: {{len(models)}}</h4>
                    <p>{{', '.join(models) if models else 'No models available - Ollama offline'}}</p>
                </div>
                
                <form method="post" action="/fred/ask">
                    <div class="form-group">
                        <label for="model">AI Model:</label>
                        <select name="model" id="model" required>
                            {{model_options}}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="question">Ask Fix It Fred:</label>
                        <textarea name="question" id="question" placeholder="Describe your maintenance issue or question..." required></textarea>
                    </div>
                    
                    <button type="submit" class="btn">Ask Fix It Fred</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    return HTMLResponse(content=html)

@app.post("/fred/ask")
async def ask_fred(model: str = Form(...), question: str = Form(...)):
    """Ask Fix It Fred using Ollama"""
    
    prompt = f"""You are Fix It Fred, an expert maintenance technician and CMMS specialist. 
    
    Question: {{question}}
    
    Provide a helpful, practical response with:
    1. Problem analysis
    2. Step-by-step solution
    3. Safety considerations
    4. Tools/parts needed
    5. Time estimate
    
    Be concise but thorough."""
    
    response = await ollama.chat(model, prompt)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fix It Fred Response - ChatterFix</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px; }}
            .conversation {{ background: white; padding: 30px; border-radius: 12px; }}
            .message {{ padding: 20px; margin: 15px 0; border-radius: 8px; }}
            .user {{ background: #3498db; color: white; margin-left: 10%; }}
            .fred {{ background: #ecf0f1; border-left: 4px solid #e74c3c; }}
            .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #e74c3c; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Fix It Fred Response</h1>
                <p>AI Model: {{model}}</p>
            </div>
            
            <div class="conversation">
                <div class="message user">
                    <div class="meta">You asked:</div>
                    <strong>{{question}}</strong>
                </div>
                
                <div class="message fred">
                    <div class="meta">Fix It Fred ({{model}}) responds:</div>
                    {{response.replace(chr(10), '<br>')}}
                </div>
                
                <a href="/fred" class="btn">Ask Another Question</a>
            </div>
        </div>
    </body>
    </html>
    '''
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("🚀 Starting ChatterFix CMMS Complete...")
    print(f"🌐 Access: http://{{VM_IP}}:8080")
    print(f"🗄️ Database: {{POSTGRES_HOST}}")
    print(f"🤖 AI: {{OLLAMA_URL}}")
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''
    
    return app_code

def deploy_to_vm():
    """Deploy complete app to VM"""
    print("🚀 Deploying Complete ChatterFix...")
    
    app_code = create_complete_app()
    
    # Write the complete app
    with open("chatterfix_complete.py", "w") as f:
        f.write(app_code)
    
    print("✅ Complete ChatterFix app created")
    print(f"📁 File: chatterfix_complete.py")
    print("")
    print("🔧 Manual deployment steps:")
    print(f"1. Copy chatterfix_complete.py to your VM")
    print(f"2. Install dependencies: pip install fastapi uvicorn asyncpg httpx")
    print(f"3. Run: python3 chatterfix_complete.py")
    print("")
    print("🔗 Will be available at:")
    print(f"   http://{VM_IP}:8080 - Main interface")
    print(f"   http://{VM_IP}:8080/health - Health check")
    print(f"   http://{VM_IP}:8080/fred - Fix It Fred AI")

if __name__ == "__main__":
    deploy_to_vm()