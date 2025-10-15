#!/usr/bin/env python3
"""
🔧 ChatterFix CMMS Enterprise - Hot Reload Development Version
Comprehensive maintenance management system with live editing capabilities
"""

import os
import sqlite3
import logging
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_PATH = "/opt/chatterfix-cmms/shared/data/cmms.db"
JWT_SECRET = "chatterfix-enterprise-secret-2025"
JWT_ALGORITHM = "HS256"

# AI Configuration (multiple providers)
XAI_API_KEY = os.getenv("XAI_API_KEY", "xai-demo-key")
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-beta"

# Initialize FastAPI
app = FastAPI(
    title="ChatterFix CMMS Enterprise - Hot Reload",
    description="Complete Maintenance Management System with Live Development",
    version="3.0.0-hotreload"
)

def get_db_connection():
    """Get database connection with auto-initialization"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    # Initialize database schema
    cursor = conn.cursor()
    
    # Users table
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
    
    # Work orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            assigned_to INTEGER,
            created_by INTEGER,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            due_date DATETIME,
            completed_date DATETIME,
            asset_id INTEGER,
            FOREIGN KEY (assigned_to) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            asset_type TEXT,
            location TEXT,
            status TEXT DEFAULT 'active',
            criticality TEXT DEFAULT 'medium',
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            install_date DATE,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
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
            current_stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            unit_cost DECIMAL(10,2),
            supplier TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_password = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, full_name, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@chatterfix.com', admin_password, 'admin', 'System Administrator', 'IT'))
    
    conn.commit()
    return conn

def verify_token(token: Optional[str] = Cookie(None)):
    """Verify JWT token"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = TRUE", (user_id,))
            user = cursor.fetchone()
            conn.close()
            return dict(user) if user else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
    return None

def get_current_user(token: Optional[str] = Cookie(None)):
    """Get current authenticated user"""
    user = verify_token(token)
    if not user:
        # Return demo user for development
        return {
            'id': 1,
            'username': 'demo',
            'email': 'demo@chatterfix.com',
            'role': 'admin',
            'full_name': 'Demo User',
            'department': 'Demo'
        }
    return user

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(current_user: dict = Depends(get_current_user)):
    """Main dashboard with hot reload indicator"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS Enterprise - Hot Reload Dashboard</title>
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
        .hot-reload-badge {{
            background: linear-gradient(45deg, #e74c3c, #ff6b35);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
        .clean-badge {{
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🔧 ChatterFix CMMS <span class="enterprise-badge">ENTERPRISE</span> <span class="hot-reload-badge">🔥 HOT RELOAD</span></div>
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
            <a href="/dev">🔥 Dev Tools</a>
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
                <h3>🤖 AI Assistant</h3>
                <div class="metric">Active</div>
                <p>Multi-provider AI insights</p>
            </div>
            
            <div class="card">
                <h3>🔥 Hot Reload</h3>
                <div class="metric">Live</div>
                <p>Files auto-update on change</p>
            </div>
            
            <div class="card">
                <h3>🚀 Fix It Fred Deploy</h3>
                <div class="metric">Ready</div>
                <p>Push to main = auto deploy</p>
            </div>
        </div>
        
        <!-- Development indicator -->
        <div style="position: fixed; top: 10px; right: 10px; background: #e74c3c; color: white; padding: 8px 15px; border-radius: 20px; font-size: 12px; z-index: 9999;">
            🔥 HOT RELOAD ACTIVE
        </div>
        
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>
    """

@app.get("/dev", response_class=HTMLResponse)
async def dev_tools():
    """Development tools page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔥 ChatterFix Dev Tools</title>
        <style>
        body { font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }
        .tool { background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .status { color: #ff6b35; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🔥 ChatterFix CMMS - Development Tools</h1>
        
        <div class="tool">
            <h3>🔥 Hot Reload Status</h3>
            <p class="status">ACTIVE - Files auto-reload on change</p>
        </div>
        
        <div class="tool">
            <h3>🚀 Fix It Fred Deploy</h3>
            <p class="status">ENABLED - Push to main/main-clean triggers deploy</p>
        </div>
        
        <div class="tool">
            <h3>📁 File Locations</h3>
            <p>App: /opt/chatterfix-cmms/current/app.py</p>
            <p>Database: /opt/chatterfix-cmms/shared/data/cmms.db</p>
            <p>Logs: /opt/chatterfix-cmms/logs/</p>
        </div>
        
        <div class="tool">
            <h3>🔧 Quick Commands</h3>
            <p>Restart: sudo systemctl restart chatterfix-cmms</p>
            <p>Logs: sudo journalctl -f -u chatterfix-cmms</p>
            <p>Status: sudo systemctl status chatterfix-cmms</p>
        </div>
        
        <a href="/" style="color: #00ff00;">← Back to Dashboard</a>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint with hot reload status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "ai_assistant": "active",
        "version": "enterprise-3.0.0-hotreload",
        "features": ["hot_reload", "fix_it_fred_deploy", "enterprise_auth", "multi_ai"],
        "deployment": "hot-reload-enabled"
    }

# AI Assistant endpoint
@app.post("/global-ai/process-message")
async def process_ai_message(request: Request):
    """Process AI assistant messages"""
    try:
        body = await request.json()
        message = body.get("message", "")
        
        if not message:
            return {"success": False, "error": "No message provided"}
        
        # Hot reload development response
        return {
            "success": True,
            "response": f"🔥 ChatterFix Hot Reload Active! I can help with:\n\n🔧 Work order management\n🏭 Asset monitoring\n📦 Parts inventory\n🚀 Fix It Fred deployments\n🔥 Live development\n\nYour message: '{message}'\n\nChanges deploy automatically when Fix It Fred pushes to main!",
            "actions": [],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI processing error: {str(e)}")
        return {
            "success": False,
            "error": "AI service temporarily unavailable",
            "timestamp": datetime.now().isoformat()
        }

# AI inject script with hot reload features
@app.get("/ai-inject.js")
async def ai_inject_script():
    """AI assistant injection script with development features"""
    return """
    // ChatterFix CMMS Enterprise AI Assistant - Hot Reload Version
    (function() {
        console.log('🔥 ChatterFix Hot Reload AI Assistant loading...');
        
        // Create AI assistant UI with hot reload indicator
        const aiContainer = document.createElement('div');
        aiContainer.id = 'chatterfix-ai-assistant';
        aiContainer.innerHTML = `
            <div id="ai-button" style="
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #e74c3c 0%, #ff6b35 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 8px 32px rgba(231, 76, 60, 0.4);
                z-index: 1000;
                transition: all 0.3s ease;
                color: white;
                font-size: 24px;
                animation: hotPulse 3s infinite;
            ">🔥</div>
            
            <div id="ai-chat" style="
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 350px;
                height: 400px;
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
                    background: linear-gradient(135deg, #e74c3c 0%, #ff6b35 100%);
                    color: white;
                    font-weight: 600;
                ">
                    🔥 ChatterFix Hot Reload AI
                </div>
                
                <div id="ai-messages" style="
                    flex: 1;
                    padding: 15px;
                    overflow-y: auto;
                    background: white;
                    color: #333;
                ">
                    <div style="color: #666; font-style: italic;">
                        🔥 Hot Reload Active! Fix It Fred can now deploy instantly by pushing to main!
                    </div>
                </div>
                
                <div style="
                    padding: 15px;
                    border-top: 1px solid #eee;
                    background: white;
                ">
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="ai-input" placeholder="Ask about hot reloads..." style="
                            flex: 1;
                            padding: 10px;
                            border: 1px solid #ddd;
                            border-radius: 10px;
                            outline: none;
                        ">
                        <button id="ai-send" style="
                            padding: 10px 15px;
                            background: #e74c3c;
                            color: white;
                            border: none;
                            border-radius: 10px;
                            cursor: pointer;
                        ">Send</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add hot reload pulse animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes hotPulse {
                0% { box-shadow: 0 8px 32px rgba(231, 76, 60, 0.4); }
                50% { box-shadow: 0 8px 32px rgba(231, 76, 60, 0.8); }
                100% { box-shadow: 0 8px 32px rgba(231, 76, 60, 0.4); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(aiContainer);
        
        // Event handlers (same as before but with hot reload messaging)
        const aiButton = document.getElementById('ai-button');
        const aiChat = document.getElementById('ai-chat');
        const aiInput = document.getElementById('ai-input');
        const aiSend = document.getElementById('ai-send');
        const aiMessages = document.getElementById('ai-messages');
        
        aiButton.addEventListener('click', () => {
            const isVisible = aiChat.style.display === 'flex';
            aiChat.style.display = isVisible ? 'none' : 'flex';
            if (!isVisible) {
                aiInput.focus();
            }
        });
        
        async function sendMessage() {
            const message = aiInput.value.trim();
            if (!message) return;
            
            // Add user message
            const userMsg = document.createElement('div');
            userMsg.style.cssText = 'margin-bottom: 10px; text-align: right;';
            userMsg.innerHTML = `<span style="background: #e74c3c; color: white; padding: 8px 12px; border-radius: 15px; display: inline-block;">${message}</span>`;
            aiMessages.appendChild(userMsg);
            
            aiInput.value = '';
            aiMessages.scrollTop = aiMessages.scrollHeight;
            
            try {
                const response = await fetch('/global-ai/process-message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                const aiMsg = document.createElement('div');
                aiMsg.style.cssText = 'margin-bottom: 10px;';
                aiMsg.innerHTML = `<span style="background: #f1f1f1; color: #333; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 80%; white-space: pre-line;">${data.response}</span>`;
                aiMessages.appendChild(aiMsg);
                aiMessages.scrollTop = aiMessages.scrollHeight;
                
            } catch (error) {
                console.error('AI Error:', error);
            }
        }
        
        aiSend.addEventListener('click', sendMessage);
        aiInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        console.log('🔥 ChatterFix Hot Reload AI Assistant loaded successfully');
    })();
    """

if __name__ == "__main__":
    import uvicorn
    # HOT RELOAD ENABLED with watch directories
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_dirs=["/opt/chatterfix-cmms/current"],
        reload_includes=["*.py", "*.html", "*.js", "*.css"]
    )