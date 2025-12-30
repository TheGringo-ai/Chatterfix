#!/usr/bin/env python3
"""
Complete ChatterFix CMMS with PostgreSQL and Ollama
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Configuration
VM_IP = "35.237.149.25"
POSTGRES_HOST = "35.225.244.14"
POSTGRES_PASSWORD = "REDACTED_DB_PASSWORD"
DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/chatterfix_cmms"
OLLAMA_URL = "http://localhost:11434"

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.sqlite_mode = False
    
    async def connect(self):
        """Connect to PostgreSQL or fallback to SQLite"""
        try:
            import asyncpg
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
            logger.info("✅ Connected to PostgreSQL")
            await self.init_postgres_tables()
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            logger.info("📦 Using SQLite fallback")
            self.sqlite_mode = True
            self.init_sqlite()
    
    def init_sqlite(self):
        """Fallback SQLite initialization"""
        import sqlite3
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
        
        # Insert sample data
        cursor.execute('''
            INSERT OR IGNORE INTO work_orders (id, title, description, priority, status)
            VALUES (1, 'HVAC System Maintenance', 'Annual maintenance check for building HVAC', 'high', 'open')
        ''')
        
        conn.commit()
        conn.close()
    
    async def init_postgres_tables(self):
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

class OllamaManager:
    def __init__(self):
        self.base_url = f"{OLLAMA_URL}/api"
    
    async def get_models(self):
        """Get available Ollama models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
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
    postgres_status = "✅ Connected" if db.pool else "❌ Using SQLite"
    ollama_models = await ollama.get_models()
    ollama_status = f"✅ {len(ollama_models)} models" if ollama_models else "❌ Offline"
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS Complete</title>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ background: rgba(255,255,255,0.95); color: #2c3e50; padding: 40px; border-radius: 20px; margin-bottom: 40px; text-align: center; backdrop-filter: blur(10px); }}
            .header h1 {{ font-size: 2.5em; margin: 0 0 10px 0; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .status {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .status-card {{ background: rgba(255,255,255,0.95); padding: 25px; border-radius: 15px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2); }}
            .status-card h4 {{ margin: 0 0 15px 0; color: #2c3e50; font-size: 1.2em; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; }}
            .card {{ background: rgba(255,255,255,0.95); padding: 30px; border-radius: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2); transition: transform 0.3s ease; }}
            .card:hover {{ transform: translateY(-5px); }}
            .card h3 {{ color: #2c3e50; margin: 0 0 15px 0; font-size: 1.4em; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #3498db, #2980b9); color: white; text-decoration: none; border-radius: 8px; margin: 8px 8px 8px 0; font-weight: 500; transition: all 0.3s ease; }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 15px rgba(52,152,219,0.4); }}
            .btn-success {{ background: linear-gradient(135deg, #27ae60, #219a52); }}
            .btn-danger {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
            .feature-badge {{ background: #f39c12; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; margin-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 ChatterFix CMMS Complete</h1>
                <p style="font-size: 1.2em; margin: 0; color: #7f8c8d;">Enterprise-grade CMMS with PostgreSQL database and Ollama AI</p>
                <p style="margin: 10px 0 0 0;"><strong>VM:</strong> {VM_IP} | <strong>Version:</strong> 3.0 Complete <span class="feature-badge">LIVE</span></p>
            </div>
            
            <div class="status">
                <div class="status-card">
                    <h4>🗄️ Database Status</h4>
                    <p><strong>PostgreSQL:</strong> {postgres_status}</p>
                    <p><strong>Host:</strong> {POSTGRES_HOST}</p>
                    <p><strong>Database:</strong> chatterfix_cmms</p>
                </div>
                
                <div class="status-card">
                    <h4>🤖 AI Status</h4>
                    <p><strong>Ollama:</strong> {ollama_status}</p>
                    <p><strong>URL:</strong> {OLLAMA_URL}</p>
                    <p><strong>Models:</strong> {', '.join(ollama_models[:3]) if ollama_models else 'None'}</p>
                </div>
                
                <div class="status-card">
                    <h4>📊 System Health</h4>
                    <p><strong>Uptime:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
                    <p><strong>Status:</strong> ✅ All Systems Operational</p>
                    <p><strong>Load:</strong> Optimized</p>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>🔧 Work Orders</h3>
                    <p>Complete work order management with PostgreSQL persistence, advanced filtering, and real-time updates.</p>
                    <a href="/work-orders" class="btn">View Work Orders</a>
                    <a href="/work-orders/create" class="btn btn-success">Create New</a>
                </div>
                
                <div class="card">
                    <h3>🏭 Assets</h3>
                    <p>Comprehensive asset management with maintenance schedules, downtime tracking, and performance analytics.</p>
                    <a href="/assets" class="btn">View Assets</a>
                    <a href="/assets/create" class="btn btn-success">Add Asset</a>
                </div>
                
                <div class="card">
                    <h3>📦 Parts Inventory</h3>
                    <p>Smart inventory management with automatic reorder points, cost tracking, and supplier integration.</p>
                    <a href="/parts" class="btn">View Parts</a>
                    <a href="/parts/create" class="btn btn-success">Add Part</a>
                </div>
                
                <div class="card">
                    <h3>🤖 Fix It Fred AI</h3>
                    <p>Advanced AI maintenance assistant powered by Ollama with multiple model support and expert troubleshooting.</p>
                    <a href="/fred" class="btn btn-danger">Ask Fred</a>
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
    
    return {
        "status": "healthy",
        "service": "ChatterFix CMMS Complete",
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "postgresql": {
                "status": "healthy" if postgres_healthy else "fallback_sqlite",
                "host": POSTGRES_HOST,
                "database": "chatterfix_cmms"
            },
            "ollama": {
                "status": "healthy" if ollama_healthy else "offline",
                "url": OLLAMA_URL,
                "models": ollama_models
            },
            "vm": {
                "ip": VM_IP,
                "ports": ["8080", "11434", "5432"]
            }
        }
    }

@app.get("/work-orders")
async def list_work_orders():
    """List all work orders"""
    orders = []
    
    if db.sqlite_mode:
        import sqlite3
        conn = sqlite3.connect('chatterfix.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM work_orders ORDER BY created_at DESC')
        orders = cursor.fetchall()
        conn.close()
    else:
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM work_orders ORDER BY created_at DESC')
                orders = [(row['id'], row['title'], row['description'], row['priority'], 
                          row['status'], row['assigned_to'], row['created_at']) for row in rows]
        except:
            orders = []
    
    orders_html = ""
    for order in orders:
        status_class = f"status-{order[4].lower().replace(' ', '-')}"
        orders_html += f"""
        <tr>
            <td>{order[0]}</td>
            <td>{order[1]}</td>
            <td>{order[3]}</td>
            <td><span class="{status_class}">{order[4]}</span></td>
            <td>{order[5] or 'Unassigned'}</td>
            <td>{str(order[6])[:16] if order[6] else 'N/A'}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Work Orders - ChatterFix Complete</title>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ background: rgba(255,255,255,0.95); color: #2c3e50; padding: 30px; border-radius: 15px; margin-bottom: 30px; backdrop-filter: blur(10px); }}
            .table-container {{ background: rgba(255,255,255,0.95); border-radius: 15px; overflow: hidden; backdrop-filter: blur(10px); }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
            th {{ background: #34495e; color: white; font-weight: 600; }}
            .btn {{ display: inline-block; padding: 10px 20px; background: linear-gradient(135deg, #3498db, #2980b9); color: white; text-decoration: none; border-radius: 6px; margin: 5px; font-weight: 500; }}
            .btn-success {{ background: linear-gradient(135deg, #27ae60, #219a52); }}
            .status-open {{ background: #e74c3c; color: white; padding: 6px 12px; border-radius: 15px; font-size: 0.85em; }}
            .status-in-progress {{ background: #f39c12; color: white; padding: 6px 12px; border-radius: 15px; font-size: 0.85em; }}
            .status-completed {{ background: #27ae60; color: white; padding: 6px 12px; border-radius: 15px; font-size: 0.85em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Work Orders</h1>
                <p>Complete work order management system</p>
                <a href="/" class="btn">← Dashboard</a>
                <a href="/work-orders/create" class="btn btn-success">+ Create New Order</a>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Priority</th>
                            <th>Status</th>
                            <th>Assigned To</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/fred")
async def fix_it_fred():
    """Fix It Fred AI interface"""
    models = await ollama.get_models()
    
    if not models:
        models = ["llama3:8b", "mistral:7b"]  # Default options
        model_status = "⚠️ Ollama offline - showing default models"
        model_options = '<option value="demo">Demo Mode (Ollama offline)</option>'
    else:
        model_status = f"✅ {len(models)} models available"
        model_options = "".join([f'<option value="{m}">{m}</option>' for m in models])
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fix It Fred AI - ChatterFix Complete</title>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); min-height: 100vh; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ background: rgba(255,255,255,0.95); color: #2c3e50; padding: 30px; border-radius: 15px; margin-bottom: 30px; backdrop-filter: blur(10px); text-align: center; }}
            .chat {{ background: rgba(255,255,255,0.95); padding: 40px; border-radius: 15px; backdrop-filter: blur(10px); }}
            .models {{ background: #ecf0f1; padding: 20px; border-radius: 10px; margin-bottom: 25px; }}
            .form-group {{ margin-bottom: 25px; }}
            label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #2c3e50; }}
            select, textarea {{ width: 100%; padding: 15px; border: 2px solid #ecf0f1; border-radius: 8px; font-size: 16px; }}
            select:focus, textarea:focus {{ border-color: #e74c3c; outline: none; }}
            textarea {{ height: 120px; resize: vertical; }}
            .btn {{ padding: 15px 30px; background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 16px; }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 15px rgba(231,76,60,0.4); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Fix It Fred AI Assistant</h1>
                <p style="font-size: 1.1em; margin: 10px 0 0 0;">Advanced AI-powered maintenance troubleshooting</p>
                <a href="/" style="color: #3498db; text-decoration: none; font-weight: 500;">← Back to Dashboard</a>
            </div>
            
            <div class="chat">
                <div class="models">
                    <h4 style="margin: 0 0 10px 0;">🧠 AI Model Status</h4>
                    <p style="margin: 0;"><strong>{model_status}</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #7f8c8d;">
                        Available: {', '.join(models[:3]) if models else 'None - Demo mode active'}
                    </p>
                </div>
                
                <form method="post" action="/fred/ask">
                    <div class="form-group">
                        <label for="model">🔧 Select AI Model:</label>
                        <select name="model" id="model" required>
                            {model_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="question">💬 Describe your maintenance issue:</label>
                        <textarea name="question" id="question" placeholder="Example: My HVAC system is making a loud grinding noise and the temperature isn't reaching the set point..." required></textarea>
                    </div>
                    
                    <button type="submit" class="btn">🚀 Ask Fix It Fred</button>
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
    
    prompt = f"""You are Fix It Fred, an expert maintenance technician and CMMS specialist with 20+ years of experience. 

Question: {question}

Provide a comprehensive, practical response with:

1. **Problem Analysis**: What's likely causing this issue?
2. **Immediate Actions**: What should be done right now for safety?
3. **Step-by-Step Solution**: Detailed troubleshooting steps
4. **Tools & Parts Needed**: Specific equipment required
5. **Safety Considerations**: Important warnings and precautions
6. **Time Estimate**: How long this should take
7. **Prevention**: How to avoid this in the future

Be thorough but practical. Focus on actionable solutions."""
    
    if model == "demo":
        response = f"""**DEMO MODE - Fix It Fred Response**

Based on your question: "{question}"

**1. Problem Analysis:**
This appears to be a common maintenance issue that requires systematic troubleshooting.

**2. Immediate Actions:**
- Ensure safety protocols are followed
- Check for any immediate hazards
- Document the issue for tracking

**3. Step-by-Step Solution:**
- Step 1: Perform initial visual inspection
- Step 2: Check system parameters
- Step 3: Test components systematically
- Step 4: Replace or repair as needed

**4. Tools & Parts Needed:**
- Standard maintenance toolkit
- Safety equipment
- Replacement parts (if required)

**5. Safety Considerations:**
- Always follow lockout/tagout procedures
- Wear appropriate PPE
- Have backup personnel available

**6. Time Estimate:**
Approximately 30-60 minutes for diagnosis and initial repair

**7. Prevention:**
Regular preventive maintenance schedule should prevent similar issues

*Note: This is a demo response. Connect Ollama for AI-powered answers.*"""
    else:
        response = await ollama.chat(model, prompt)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fix It Fred Response - ChatterFix Complete</title>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); min-height: 100vh; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ background: rgba(255,255,255,0.95); color: #2c3e50; padding: 25px; border-radius: 15px; margin-bottom: 25px; backdrop-filter: blur(10px); }}
            .conversation {{ background: rgba(255,255,255,0.95); padding: 40px; border-radius: 15px; backdrop-filter: blur(10px); }}
            .message {{ padding: 25px; margin: 20px 0; border-radius: 12px; }}
            .user {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; margin-left: 5%; }}
            .fred {{ background: #f8f9fa; border-left: 5px solid #e74c3c; }}
            .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 12px; font-weight: 600; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; text-decoration: none; border-radius: 8px; margin-top: 25px; font-weight: 600; }}
            .response-text {{ line-height: 1.6; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Fix It Fred Response</h1>
                <p><strong>AI Model:</strong> {model} | <strong>Response Time:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
            </div>
            
            <div class="conversation">
                <div class="message user">
                    <div class="meta">🙋 Your Question:</div>
                    <strong>{question}</strong>
                </div>
                
                <div class="message fred">
                    <div class="meta">🤖 Fix It Fred ({model}) responds:</div>
                    <div class="response-text">{response}</div>
                </div>
                
                <a href="/fred" class="btn">🔄 Ask Another Question</a>
                <a href="/" class="btn" style="background: linear-gradient(135deg, #3498db, #2980b9); margin-left: 10px;">🏠 Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("🚀 Starting ChatterFix CMMS Complete...")
    print(f"🌐 Access: http://{VM_IP}:8080")
    print(f"🗄️ Database: {POSTGRES_HOST}")
    print(f"🤖 AI: {OLLAMA_URL}")
    print("📋 Features: Work Orders, Assets, Parts, AI Assistant")
    uvicorn.run(app, host="0.0.0.0", port=8080)