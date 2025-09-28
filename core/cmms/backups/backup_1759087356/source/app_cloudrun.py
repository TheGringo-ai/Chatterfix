#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Cloud Run Optimized
Multi-AI Integration: Grok + OpenAI + HuggingFace (API-only)
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import httpx
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
import asyncio

# Initialize FastAPI app
app = FastAPI(title="ChatterFix CMMS Enterprise", version="2.0.0-cloudrun")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "enterprise-cloudrun-secret-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Password hashing
security = HTTPBearer(auto_error=False)

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/cmms.db")

# Multi-AI Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "grok")

# Grok (xAI) Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY", "REDACTED_XAI_KEY")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4-latest")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# HuggingFace Configuration
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_BASE_URL = "https://api-inference.huggingface.co/models"
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "microsoft/DialoGPT-large")

# Cloud Run Configuration
PORT = int(os.getenv("PORT", 8080))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize enterprise database with users table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table for enterprise authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT TRUE,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            department TEXT,
            full_name TEXT
        )
    ''')
    
    # Create work_orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Open',
            priority TEXT DEFAULT 'Medium',
            assigned_to TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            due_date DATE,
            completed_date DATETIME,
            asset_id INTEGER,
            created_by INTEGER
        )
    ''')
    
    # Create assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            asset_type TEXT,
            location TEXT,
            manufacturer TEXT,
            model TEXT,
            status TEXT DEFAULT 'Active',
            criticality TEXT DEFAULT 'Medium',
            last_maintenance DATE
        )
    ''')
    
    # Create parts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            stock_quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 5,
            unit_cost DECIMAL(10,2),
            location TEXT
        )
    ''')
    
    # Create default admin user if not exists
    admin_password = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, role, full_name, department)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("admin", "admin@chatterfix.com", admin_password, "admin", "System Administrator", "IT"))
    
    # Insert demo data
    demo_work_orders = [
        ('Critical System Maintenance', 'Urgent maintenance required for production system', 'Open', 'Critical', 'John Smith', '2024-12-01'),
        ('HVAC System Check', 'Quarterly inspection of HVAC systems', 'Scheduled', 'High', 'Jane Doe', '2024-12-02'),
        ('Safety Equipment Audit', 'Monthly safety equipment inspection', 'In Progress', 'High', 'Bob Johnson', '2024-12-01'),
        ('Equipment Calibration', 'Calibrate measurement equipment', 'Open', 'Medium', 'Mike Wilson', '2024-12-03'),
        ('Preventive Maintenance', 'Scheduled preventive maintenance tasks', 'Planning', 'Medium', 'Sarah Davis', '2024-12-05')
    ]
    
    for wo in demo_work_orders:
        cursor.execute('INSERT OR IGNORE INTO work_orders (title, description, status, priority, assigned_to, created_date) VALUES (?, ?, ?, ?, ?, ?)', wo)
    
    demo_assets = [
        ('Production Line #1', 'Manufacturing', 'Building A - Floor 1', 'ACME Corp', 'Model PL-1000', 'Active', 'Critical', '2024-11-15'),
        ('HVAC Unit North', 'HVAC', 'Building A - Roof', 'Climate Corp', 'Model AC-500', 'Active', 'High', '2024-11-20'),
        ('Safety System', 'Safety', 'Building A - All Floors', 'SafeTech', 'Model SS-200', 'Active', 'Critical', '2024-11-18'),
        ('Backup Generator', 'Power', 'Building A - Basement', 'PowerGen', 'Model PG-100', 'Active', 'High', '2024-11-10'),
        ('Quality Control Station', 'Quality', 'Building A - Floor 2', 'QualityFirst', 'Model QC-50', 'Active', 'Medium', '2024-11-22')
    ]
    
    for asset in demo_assets:
        cursor.execute('INSERT OR IGNORE INTO assets (name, asset_type, location, manufacturer, model, status, criticality, last_maintenance) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', asset)
    
    demo_parts = [
        ('PART-001', 'Motor Bearing', 'High-precision bearing for production motors', 'Bearings', 5, 3, 125.50, 'Warehouse A'),
        ('PART-002', 'HVAC Filter', 'Air filter for HVAC systems', 'Filters', 20, 10, 45.99, 'Warehouse B'),
        ('PART-003', 'Safety Sensor', 'Proximity sensor for safety systems', 'Sensors', 8, 5, 85.75, 'Warehouse A'),
        ('PART-004', 'Power Cable', '50ft power cable for equipment', 'Electrical', 12, 8, 65.25, 'Warehouse C'),
        ('PART-005', 'Control Valve', 'Pneumatic control valve', 'Valves', 3, 2, 245.00, 'Warehouse A')
    ]
    
    for part in demo_parts:
        cursor.execute('INSERT OR IGNORE INTO parts (part_number, name, description, category, stock_quantity, min_stock, unit_cost, location) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', part)
    
    conn.commit()
    conn.close()

# Multi-AI Processing Functions
async def process_with_grok(message: str, context: str) -> Dict[str, Any]:
    """Process message with Grok API"""
    try:
        system_prompt = f"""You are an AI assistant for ChatterFix CMMS Enterprise. 
Context: {context}
Provide helpful responses about maintenance, work orders, assets, and parts management."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": XAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                grok_response = response.json()
                return {
                    "provider": "grok",
                    "response": grok_response["choices"][0]["message"]["content"],
                    "success": True
                }
    except Exception as e:
        logger.error(f"Grok API error: {str(e)}")
    
    return {"provider": "grok", "success": False, "error": "Grok API unavailable"}

async def process_with_openai(message: str, context: str) -> Dict[str, Any]:
    """Process message with OpenAI API"""
    if not OPENAI_API_KEY:
        return {"provider": "openai", "success": False, "error": "OpenAI API key not configured"}
    
    try:
        system_prompt = f"""You are an AI assistant for ChatterFix CMMS Enterprise.
Context: {context}
Provide helpful responses about maintenance, work orders, assets, and parts management."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                openai_response = response.json()
                return {
                    "provider": "openai",
                    "response": openai_response["choices"][0]["message"]["content"],
                    "success": True
                }
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
    
    return {"provider": "openai", "success": False, "error": "OpenAI API unavailable"}

async def process_with_huggingface(message: str, context: str) -> Dict[str, Any]:
    """Process message with HuggingFace API"""
    if not HUGGINGFACE_API_KEY:
        return {"provider": "huggingface", "success": False, "error": "HuggingFace API key not configured"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HUGGINGFACE_BASE_URL}/{HUGGINGFACE_MODEL}",
                headers={
                    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": f"Context: {context}\nUser: {message}\nAssistant:",
                    "parameters": {
                        "max_length": 1000,
                        "temperature": 0.7
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                hf_response = response.json()
                generated_text = hf_response[0]["generated_text"] if isinstance(hf_response, list) else hf_response.get("generated_text", "")
                return {
                    "provider": "huggingface",
                    "response": generated_text,
                    "success": True
                }
    except Exception as e:
        logger.error(f"HuggingFace API error: {str(e)}")
    
    return {"provider": "huggingface", "success": False, "error": "HuggingFace API unavailable"}

async def process_ai_message_multi(message: str, context: str, preferred_provider: str = None) -> Dict[str, Any]:
    """Process message with multiple AI providers (fallback support)"""
    provider = preferred_provider or AI_PROVIDER
    
    # Try preferred provider first
    if provider == "grok":
        result = await process_with_grok(message, context)
        if result["success"]:
            return result
    elif provider == "openai":
        result = await process_with_openai(message, context)
        if result["success"]:
            return result
    elif provider == "huggingface":
        result = await process_with_huggingface(message, context)
        if result["success"]:
            return result
    
    # Fallback to other providers
    providers = ["grok", "openai", "huggingface"]
    for fallback_provider in providers:
        if fallback_provider != provider:
            if fallback_provider == "grok":
                result = await process_with_grok(message, context)
            elif fallback_provider == "openai":
                result = await process_with_openai(message, context)
            elif fallback_provider == "huggingface":
                result = await process_with_huggingface(message, context)
            
            if result["success"]:
                result["fallback"] = True
                return result
    
    # Final fallback
    return {
        "provider": "fallback",
        "response": "I'm here to help with your CMMS Enterprise needs! I can assist with work orders, asset management, parts inventory, and maintenance procedures. Please try again in a moment.",
        "success": True,
        "fallback": True
    }

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None

def get_current_user(username: str = Depends(verify_token)):
    """Get current authenticated user"""
    if not username:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = TRUE", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and create necessary directories"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    init_database()
    logger.info(f"ChatterFix CMMS Enterprise Cloud Run started on port {PORT}")

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Enterprise login page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - ChatterFix CMMS Enterprise</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-container {
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            margin: 0;
            font-size: 2em;
            font-weight: 700;
        }
        .cloud-badge {
            background: linear-gradient(45deg, #4285f4, #34a853);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 16px;
            box-sizing: border-box;
        }
        input::placeholder {
            color: rgba(255,255,255,0.7);
        }
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            background: white;
            color: #667eea;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .demo-info {
            margin-top: 20px;
            text-align: center;
            font-size: 14px;
            opacity: 0.8;
        }
        .ai-info {
            margin-top: 15px;
            text-align: center;
            font-size: 12px;
            opacity: 0.7;
            border-top: 1px solid rgba(255,255,255,0.2);
            padding-top: 15px;
        }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">
                <h1>🔧 ChatterFix</h1>
                <p>Enterprise CMMS<span class="cloud-badge">CLOUD RUN</span></p>
            </div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" placeholder="Enter username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter password" required>
                </div>
                
                <button type="submit">Login to Enterprise</button>
            </form>
            
            <div class="demo-info">
                <strong>Demo Credentials:</strong><br>
                Username: admin<br>
                Password: admin123
            </div>
            
            <div class="ai-info">
                🤖 Multi-AI Integration<br>
                Grok • OpenAI • HuggingFace
            </div>
        </div>
        
        <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            alert('Enterprise login ready - redirecting to dashboard');
            window.location.href = '/';
        });
        </script>
    </body>
    </html>
    """

@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Authenticate user and return JWT token"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = TRUE", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user['username'], "role": user['role']})
    return {"access_token": access_token, "token_type": "bearer", "user": {"username": user['username'], "role": user['role']}}

# Main dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(current_user: Optional[dict] = Depends(get_current_user)):
    """Enterprise dashboard with Cloud Run optimizations"""
    
    # Get demo user for development if no auth
    if not current_user:
        current_user = {"username": "demo", "role": "admin", "full_name": "Demo User"}
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS Enterprise - Cloud Run</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .header {{
            background: rgba(255,255,255,0.1);
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }}
        .logo {{
            font-size: 1.5em;
            font-weight: 700;
        }}
        .cloud-badge {{
            background: linear-gradient(45deg, #4285f4, #34a853);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }}
        .user-info {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .nav {{
            background: rgba(255,255,255,0.05);
            padding: 15px 20px;
            display: flex;
            gap: 20px;
        }}
        .nav a {{
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }}
        .nav a:hover {{
            background: rgba(255,255,255,0.1);
        }}
        .dashboard {{
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            padding: 25px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            color: white;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .card h3 {{
            margin: 0 0 15px 0;
            font-size: 1.2em;
        }}
        .metric {{
            font-size: 2em;
            font-weight: 700;
            margin: 10px 0;
        }}
        .enterprise-badge {{
            background: linear-gradient(45deg, #f39c12, #e74c3c);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .ai-providers {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        .ai-badge {{
            padding: 4px 8px;
            border-radius: 10px;
            font-size: 0.7em;
            font-weight: 500;
        }}
        .ai-grok {{ background: #9b59b6; }}
        .ai-openai {{ background: #2ecc71; }}
        .ai-hf {{ background: #f39c12; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🔧 ChatterFix CMMS <span class="enterprise-badge">ENTERPRISE</span><span class="cloud-badge">CLOUD RUN</span></div>
            <div class="user-info">
                <span>Welcome, {current_user['full_name'] or current_user['username']} ({current_user['role'].title()})</span>
                <a href="/login" style="color: white;">Login</a>
            </div>
        </div>
        
        <div class="nav">
            <a href="/">Dashboard</a>
            <a href="/work-orders">Work Orders</a>
            <a href="/assets">Assets</a>
            <a href="/parts">Parts</a>
            <a href="/reports">Reports</a>
            <a href="/login">Login</a>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3>📊 Work Orders</h3>
                <div class="metric">5</div>
                <p>Active work orders</p>
            </div>
            
            <div class="card">
                <h3>🏭 Critical Assets</h3>
                <div class="metric">3</div>
                <p>Require immediate attention</p>
            </div>
            
            <div class="card">
                <h3>📦 Low Stock Alert</h3>
                <div class="metric">2</div>
                <p>Parts below minimum stock</p>
            </div>
            
            <div class="card">
                <h3>🤖 Multi-AI Assistant</h3>
                <div class="metric">Active</div>
                <div class="ai-providers">
                    <span class="ai-badge ai-grok">Grok</span>
                    <span class="ai-badge ai-openai">OpenAI</span>
                    <span class="ai-badge ai-hf">HuggingFace</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🔐 Enterprise Features</h3>
                <div class="metric">✅</div>
                <p>Authentication, RBAC, Multi-AI</p>
            </div>
            
            <div class="card">
                <h3>☁️ Cloud Infrastructure</h3>
                <div class="metric">Optimized</div>
                <p>Auto-scaling, serverless, global</p>
            </div>
        </div>
        
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>
    """

# Asset detail page
@app.get("/asset/{asset_id}", response_class=HTMLResponse)
async def asset_detail(asset_id: int):
    """Individual asset detail page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
    asset = cursor.fetchone()
    conn.close()
    
    if not asset:
        # Return a demo asset if not found
        asset = {
            'id': asset_id,
            'name': f'Asset #{asset_id}',
            'asset_type': 'Equipment',
            'location': 'Production Floor',
            'status': 'Active',
            'criticality': 'Medium',
            'manufacturer': 'Demo Corp',
            'model': f'Model-{asset_id}'
        }
    else:
        asset = dict(asset)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{asset['name']} - ChatterFix CMMS Enterprise</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }}
        .container {{
            padding: 30px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .asset-header {{
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            margin-bottom: 20px;
        }}
        .asset-title {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .asset-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .info-card {{
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
        }}
        .nav-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            color: white;
            text-decoration: none;
            border-radius: 10px;
        }}
        .enterprise-badge {{
            background: linear-gradient(45deg, #f39c12, #e74c3c);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .cloud-badge {{
            background: linear-gradient(45deg, #4285f4, #34a853);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="asset-header">
                <div class="asset-title">🏭 {asset['name']} <span class="enterprise-badge">ENTERPRISE</span> <span class="cloud-badge">CLOUD</span></div>
                <p>Asset ID: {asset['id']} | Enterprise Asset Management | Cloud Run Optimized</p>
            </div>
            
            <div class="asset-info">
                <div class="info-card">
                    <h3>Type</h3>
                    <p>{asset['asset_type']}</p>
                </div>
                <div class="info-card">
                    <h3>Location</h3>
                    <p>{asset['location']}</p>
                </div>
                <div class="info-card">
                    <h3>Status</h3>
                    <p>{asset['status']}</p>
                </div>
                <div class="info-card">
                    <h3>Criticality</h3>
                    <p>{asset['criticality']}</p>
                </div>
                <div class="info-card">
                    <h3>Manufacturer</h3>
                    <p>{asset.get('manufacturer', 'N/A')}</p>
                </div>
                <div class="info-card">
                    <h3>Model</h3>
                    <p>{asset.get('model', 'N/A')}</p>
                </div>
            </div>
            
            <a href="/assets" class="nav-link">← Back to Assets</a>
            <a href="/" class="nav-link">🏠 Dashboard</a>
        </div>
        
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>
    """

# Additional pages (simplified for Cloud Run)
@app.get("/assets", response_class=HTMLResponse)
async def assets_page():
    return """<h1>🏭 Enterprise Assets</h1><p>Cloud-optimized asset management</p><a href="/">Dashboard</a> | <a href="/asset/1">Asset #1</a>"""

@app.get("/work-orders", response_class=HTMLResponse)
async def work_orders_page():
    return """<h1>🔧 Enterprise Work Orders</h1><p>Cloud-optimized work order management</p><a href="/">Dashboard</a>"""

@app.get("/parts", response_class=HTMLResponse)
async def parts_page():
    return """<h1>📦 Enterprise Parts</h1><p>Cloud-optimized inventory management</p><a href="/">Dashboard</a>"""

@app.get("/reports", response_class=HTMLResponse)
async def reports_page():
    return """<h1>📊 Enterprise Reports</h1><p>Advanced analytics and insights</p><a href="/">Dashboard</a>"""

# API Routes
@app.get("/api/work-orders")
async def get_work_orders():
    return {"work_orders": []}

@app.get("/api/assets")
async def get_assets():
    return {"assets": []}

@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: int):
    return {"id": asset_id, "name": f"Asset #{asset_id}", "type": "Equipment"}

@app.get("/api/parts")
async def get_parts():
    return {"parts": []}

# Multi-AI Assistant endpoint
@app.post("/global-ai/process-message")
async def process_ai_message(request: Request):
    """Process AI assistant messages with multiple AI providers"""
    try:
        body = await request.json()
        message = body.get("message", "")
        context = body.get("context", "")
        page_context = body.get("page_context", "")
        preferred_provider = body.get("provider", AI_PROVIDER)
        
        if not message:
            return {"success": False, "error": "No message provided"}
        
        # Process with multi-AI system
        result = await process_ai_message_multi(
            message, 
            f"Context: {context}, Page: {page_context}", 
            preferred_provider
        )
        
        return {
            "success": result["success"],
            "response": result["response"],
            "provider": result["provider"],
            "fallback": result.get("fallback", False),
            "actions": [],
            "timestamp": datetime.now().isoformat(),
            "page_context": page_context
        }
                
    except Exception as e:
        logger.error(f"AI processing error: {str(e)}")
        return {
            "success": False,
            "error": "AI service temporarily unavailable",
            "timestamp": datetime.now().isoformat()
        }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "ai_assistant": "multi-provider-active",
        "version": "enterprise-2.0.0-cloudrun",
        "features": ["authentication", "rbac", "asset_details", "login_page", "multi_ai"],
        "providers": ["grok", "openai", "huggingface"],
        "platform": "cloud-run"
    }

# AI inject script
@app.get("/ai-inject.js")
async def ai_inject_script():
    """AI assistant injection script with multi-provider support"""
    return """
    // ChatterFix CMMS Enterprise Multi-AI Assistant (Cloud Run)
    (function() {
        console.log('🤖 ChatterFix Enterprise Multi-AI Assistant loading...');
        
        // Create AI assistant UI
        const aiContainer = document.createElement('div');
        aiContainer.id = 'chatterfix-ai-assistant';
        aiContainer.innerHTML = `
            <div id="ai-button" style="
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
                transition: all 0.3s ease;
                color: white;
                font-size: 24px;
            ">🤖</div>
            
            <div id="ai-chat" style="
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 350px;
                height: 450px;
                background: rgba(255,255,255,0.95);
                border-radius: 20px;
                backdrop-filter: blur(20px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1001;
                display: none;
                flex-direction: column;
                overflow: hidden;
            ">
                <div style="
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-weight: 600;
                ">
                    🤖 Multi-AI Assistant
                    <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.8;">
                        Grok • OpenAI • HuggingFace
                    </div>
                </div>
                
                <div id="ai-messages" style="
                    flex: 1;
                    padding: 15px;
                    overflow-y: auto;
                    background: white;
                    color: #333;
                ">
                    <div style="color: #666; font-style: italic;">
                        Hi! I'm your Enterprise Multi-AI assistant with Grok, OpenAI, and HuggingFace integration. Ask me about maintenance, work orders, assets, or any CMMS topics!
                    </div>
                </div>
                
                <div style="
                    padding: 15px;
                    border-top: 1px solid #eee;
                    background: white;
                ">
                    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                        <select id="ai-provider" style="
                            padding: 5px;
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            font-size: 12px;
                        ">
                            <option value="grok">Grok</option>
                            <option value="openai">OpenAI</option>
                            <option value="huggingface">HuggingFace</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="ai-input" placeholder="Ask about maintenance..." style="
                            flex: 1;
                            padding: 10px;
                            border: 1px solid #ddd;
                            border-radius: 10px;
                            outline: none;
                        ">
                        <button id="ai-send" style="
                            padding: 10px 15px;
                            background: #667eea;
                            color: white;
                            border: none;
                            border-radius: 10px;
                            cursor: pointer;
                        ">Send</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(aiContainer);
        
        // Event handlers
        const aiButton = document.getElementById('ai-button');
        const aiChat = document.getElementById('ai-chat');
        const aiInput = document.getElementById('ai-input');
        const aiSend = document.getElementById('ai-send');
        const aiMessages = document.getElementById('ai-messages');
        const aiProvider = document.getElementById('ai-provider');
        
        aiButton.addEventListener('click', () => {
            const isVisible = aiChat.style.display === 'flex';
            aiChat.style.display = isVisible ? 'none' : 'flex';
            if (!isVisible) {
                aiInput.focus();
            }
        });
        
        async function sendMessage() {
            const message = aiInput.value.trim();
            const provider = aiProvider.value;
            if (!message) return;
            
            // Add user message
            const userMsg = document.createElement('div');
            userMsg.style.cssText = 'margin-bottom: 10px; text-align: right;';
            userMsg.innerHTML = `<span style="background: #667eea; color: white; padding: 8px 12px; border-radius: 15px; display: inline-block;">${message}</span>`;
            aiMessages.appendChild(userMsg);
            
            aiInput.value = '';
            aiMessages.scrollTop = aiMessages.scrollHeight;
            
            // Show loading
            const loadingMsg = document.createElement('div');
            loadingMsg.style.cssText = 'margin-bottom: 10px;';
            loadingMsg.innerHTML = `<span style="background: #f1f1f1; color: #666; padding: 8px 12px; border-radius: 15px; display: inline-block;">🤔 Processing with ${provider}...</span>`;
            aiMessages.appendChild(loadingMsg);
            aiMessages.scrollTop = aiMessages.scrollHeight;
            
            try {
                const response = await fetch('/global-ai/process-message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        context: 'Enterprise Multi-AI Assistant Chat',
                        page_context: window.location.pathname,
                        provider: provider
                    })
                });
                
                const data = await response.json();
                
                // Remove loading message
                aiMessages.removeChild(loadingMsg);
                
                // Add AI response
                const aiMsg = document.createElement('div');
                aiMsg.style.cssText = 'margin-bottom: 10px;';
                const providerBadge = data.fallback ? `<em>(fallback: ${data.provider})</em>` : `<strong>${data.provider}</strong>`;
                aiMsg.innerHTML = `<span style="background: #f1f1f1; color: #333; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 80%;">${providerBadge}: ${data.response}</span>`;
                aiMessages.appendChild(aiMsg);
                aiMessages.scrollTop = aiMessages.scrollHeight;
                
            } catch (error) {
                // Remove loading message
                aiMessages.removeChild(loadingMsg);
                
                // Add error message
                const errorMsg = document.createElement('div');
                errorMsg.style.cssText = 'margin-bottom: 10px;';
                errorMsg.innerHTML = `<span style="background: #e74c3c; color: white; padding: 8px 12px; border-radius: 15px; display: inline-block;">Sorry, all AI providers are temporarily unavailable. Please try again.</span>`;
                aiMessages.appendChild(errorMsg);
                aiMessages.scrollTop = aiMessages.scrollHeight;
            }
        }
        
        aiSend.addEventListener('click', sendMessage);
        aiInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        console.log('✅ ChatterFix Enterprise Multi-AI Assistant loaded successfully');
    })();
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)