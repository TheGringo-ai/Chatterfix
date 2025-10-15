#!/usr/bin/env python3
"""
Simple ChatterFix CMMS - Standalone VM Version
No microservices, no complexity, just works
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

app = FastAPI(title="ChatterFix CMMS", version="2.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('chatterfix.db')
    cursor = conn.cursor()
    
    # Create tables
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            location TEXT,
            status TEXT DEFAULT 'active',
            asset_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.get("/")
async def dashboard():
    """Main dashboard"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .card h3 { color: #2c3e50; margin-top: 0; }
            .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 4px; margin: 5px; }
            .btn:hover { background: #2980b9; }
            .status { padding: 20px; background: #e8f5e8; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 ChatterFix CMMS</h1>
                <p>Maintenance Management System - Now Running on VM!</p>
            </div>
            
            <div class="status">
                <h3>✅ System Status: ONLINE</h3>
                <p>ChatterFix is running successfully on your VM at 35.237.149.25</p>
                <p>All core CMMS features are available below.</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>🔧 Work Orders</h3>
                    <p>Create and manage maintenance work orders</p>
                    <a href="/work-orders" class="btn">View Work Orders</a>
                    <a href="/work-orders/create" class="btn">Create New</a>
                </div>
                
                <div class="card">
                    <h3>🏭 Assets</h3>
                    <p>Manage equipment and assets</p>
                    <a href="/assets" class="btn">View Assets</a>
                    <a href="/assets/create" class="btn">Add Asset</a>
                </div>
                
                <div class="card">
                    <h3>📦 Parts Inventory</h3>
                    <p>Track spare parts and inventory</p>
                    <a href="/parts" class="btn">View Parts</a>
                    <a href="/parts/create" class="btn">Add Part</a>
                </div>
                
                <div class="card">
                    <h3>🤖 Fix It Fred</h3>
                    <p>AI-powered maintenance assistant</p>
                    <a href="/fred" class="btn">Ask Fred</a>
                    <a href="/fred/troubleshoot" class="btn">Troubleshoot</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "ChatterFix CMMS",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "message": "All systems operational on VM"
    }

# Work Orders endpoints
@app.get("/work-orders")
async def list_work_orders():
    """List all work orders"""
    conn = sqlite3.connect('chatterfix.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM work_orders ORDER BY created_at DESC')
    orders = cursor.fetchall()
    conn.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Work Orders - ChatterFix</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
            table { width: 100%; background: white; border-collapse: collapse; border-radius: 8px; overflow: hidden; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #34495e; color: white; }
            .btn { padding: 8px 16px; background: #3498db; color: white; text-decoration: none; border-radius: 4px; margin: 2px; }
            .status-open { background: #e74c3c; color: white; padding: 4px 8px; border-radius: 4px; }
            .status-in-progress { background: #f39c12; color: white; padding: 4px 8px; border-radius: 4px; }
            .status-completed { background: #27ae60; color: white; padding: 4px 8px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Work Orders</h1>
                <a href="/" class="btn">← Back to Dashboard</a>
                <a href="/work-orders/create" class="btn">+ Create New</a>
            </div>
            
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
    """
    
    for order in orders:
        status_class = f"status-{order[4].lower().replace(' ', '-')}"
        html += f"""
                    <tr>
                        <td>{order[0]}</td>
                        <td>{order[1]}</td>
                        <td>{order[3]}</td>
                        <td><span class="{status_class}">{order[4]}</span></td>
                        <td>{order[5] or 'Unassigned'}</td>
                        <td>{order[6]}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/work-orders/create")
async def create_work_order_form():
    """Work order creation form"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Create Work Order - ChatterFix</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
            .form { background: white; padding: 30px; border-radius: 8px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            textarea { height: 100px; }
            .btn { padding: 12px 24px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #219a52; }
            .btn-secondary { background: #95a5a6; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Create Work Order</h1>
                <a href="/work-orders" style="color: white;">← Back to Work Orders</a>
            </div>
            
            <form method="post" action="/work-orders/create" class="form">
                <div class="form-group">
                    <label for="title">Title:</label>
                    <input type="text" id="title" name="title" required>
                </div>
                
                <div class="form-group">
                    <label for="description">Description:</label>
                    <textarea id="description" name="description"></textarea>
                </div>
                
                <div class="form-group">
                    <label for="priority">Priority:</label>
                    <select id="priority" name="priority">
                        <option value="low">Low</option>
                        <option value="medium" selected>Medium</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="assigned_to">Assigned To:</label>
                    <input type="text" id="assigned_to" name="assigned_to">
                </div>
                
                <button type="submit" class="btn">Create Work Order</button>
                <a href="/work-orders" class="btn btn-secondary">Cancel</a>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/work-orders/create")
async def create_work_order(
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    assigned_to: str = Form("")
):
    """Create new work order"""
    conn = sqlite3.connect('chatterfix.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO work_orders (title, description, priority, assigned_to)
        VALUES (?, ?, ?, ?)
    ''', (title, description, priority, assigned_to or None))
    conn.commit()
    conn.close()
    
    return JSONResponse({"message": "Work order created successfully", "redirect": "/work-orders"})

# Fix It Fred endpoint
@app.get("/fred")
async def fix_it_fred():
    """Fix It Fred AI Assistant"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fix It Fred - ChatterFix</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { background: #e74c3c; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
            .chat { background: white; padding: 30px; border-radius: 8px; min-height: 400px; }
            .message { padding: 15px; margin: 10px 0; border-radius: 8px; }
            .user { background: #3498db; color: white; margin-left: 20%; }
            .fred { background: #ecf0f1; border-left: 4px solid #e74c3c; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Fix It Fred</h1>
                <p>Your AI Maintenance Assistant</p>
                <a href="/" style="color: white;">← Back to Dashboard</a>
            </div>
            
            <div class="chat">
                <div class="message fred">
                    <strong>Fix It Fred:</strong> Hello! I'm Fix It Fred, your AI maintenance assistant. 
                    I can help you troubleshoot equipment, provide maintenance guidance, and answer technical questions.
                    
                    <p><strong>Try asking me:</strong></p>
                    <ul>
                        <li>"My HVAC system is making a loud noise"</li>
                        <li>"How do I maintain a conveyor belt?"</li>
                        <li>"Troubleshoot boiler pressure issues"</li>
                    </ul>
                </div>
                
                <form method="post" action="/fred/ask" style="margin-top: 30px;">
                    <textarea name="question" placeholder="Ask Fix It Fred a question..." 
                             style="width: 100%; height: 100px; padding: 15px; border: 1px solid #ddd; border-radius: 4px;"></textarea>
                    <br><br>
                    <button type="submit" style="padding: 12px 24px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer;">Ask Fred</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/fred/ask")
async def ask_fred(question: str = Form(...)):
    """Ask Fix It Fred a question"""
    # Simple AI response (you can integrate with actual AI later)
    response = f"""
    Based on your question: "{question}"
    
    This is a placeholder response from Fix It Fred. In a full implementation, this would:
    1. Analyze your maintenance question using AI
    2. Provide specific troubleshooting steps
    3. Suggest safety precautions
    4. Recommend tools or parts needed
    
    For now, I recommend checking the equipment manual and following standard safety procedures.
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fix It Fred Response - ChatterFix</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .header {{ background: #e74c3c; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
            .chat {{ background: white; padding: 30px; border-radius: 8px; }}
            .message {{ padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .user {{ background: #3498db; color: white; margin-left: 20%; }}
            .fred {{ background: #ecf0f1; border-left: 4px solid #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Fix It Fred Response</h1>
                <a href="/fred" style="color: white;">← Ask Another Question</a>
            </div>
            
            <div class="chat">
                <div class="message user">
                    <strong>You:</strong> {question}
                </div>
                
                <div class="message fred">
                    <strong>Fix It Fred:</strong> {response}
                </div>
                
                <a href="/fred" style="padding: 12px 24px; background: #e74c3c; color: white; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 20px;">Ask Another Question</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("🚀 Starting ChatterFix CMMS...")
    print("🌐 Access at: http://35.237.149.25:8080")
    print("🩺 Health check: http://35.237.149.25:8080/health")
    uvicorn.run(app, host="0.0.0.0", port=8080)