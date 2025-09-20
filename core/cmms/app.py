#!/usr/bin/env python3
"""
ChatterFix CMMS - Complete AI-Enhanced Maintenance Management System
Main Application with LLaMA Integration
"""

import logging
import sqlite3
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
# Import unified styles, fallback to inline if not available
try:
    from unified_cmms_system import get_unified_styles
except ImportError:
    from typing import Literal

    def get_unified_styles() -> Literal["""
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #5a6fd8; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        """]:
        return """
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #5a6fd8; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        """

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ChatterFix CMMS", version="2.0.0")

# Database setup
DATABASE_PATH = "cmms.db"


def init_database():
    """Initialize the CMMS database with all required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'medium',
            assigned_to TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            ai_analysis TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            status TEXT DEFAULT 'operational',
            last_maintenance TIMESTAMP,
            next_maintenance TIMESTAMP,
            ai_health_score REAL DEFAULT 0.0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            context_type TEXT
        )
    """)

    conn.commit()
    conn.close()


class LLaMAClient:
    """Client for interacting with LLaMA via Ollama"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama3.1:8b"

    async def query(self, prompt: str, context: str = "") -> str:
        """Query LLaMA with maintenance-specific context"""
        try:
            # Enhanced prompt for CMMS context
            system_prompt = """You are an AI assistant for ChatterFix CMMS (Computerized Maintenance Management System). 
            You help technicians with:
            - Troubleshooting equipment issues
            - Maintenance scheduling and procedures
            - Work order prioritization
            - Parts identification and sourcing
            - Safety protocols and compliance
            
            Provide practical, actionable advice focused on maintenance and operations."""

            full_prompt = f"{system_prompt}\n\nContext: {context}\n\nUser Question: {prompt}"

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": full_prompt, "stream": False},
                timeout=30,
            )

            if response.status_code == 200:
                return response.json().get("response", "No response from AI")
            else:
                logger.error(f"LLaMA API error: {response.status_code}")
                return "AI assistant temporarily unavailable. Please try again."

        except requests.exceptions.RequestException as e:
            logger.error(f"LLaMA connection error: {e}")
            return "AI assistant offline. Check Ollama service status."


# Initialize LLaMA client
llama_client = LLaMAClient()


# Initialize database and LLaMA client on import
init_database()
logger.info("ChatterFix CMMS initialized successfully")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main CMMS dashboard with AI assistant"""
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS - AI-Enhanced Maintenance</title>
    <style>
        {get_unified_styles()}
        
        /* AI Assistant Styling */
        #ai-assistant {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }}
        
        #ai-toggle {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }}
        
        #ai-toggle:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 30px rgba(0,0,0,0.4);
        }}
        
        #ai-chat {{
            display: none;
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 350px;
            height: 400px;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
        }}
        
        .ai-header {{
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0;
            font-weight: bold;
        }}
        
        .ai-messages {{
            flex: 1;
            padding: 15px;
            overflow-y: auto;
        }}
        
        .ai-input-area {{
            padding: 15px;
            border-top: 1px solid rgba(0,0,0,0.1);
        }}
        
        .ai-input {{
            width: 100%;
            padding: 10px;
            border: 1px solid rgba(0,0,0,0.2);
            border-radius: 20px;
            outline: none;
        }}
        
        .message {{
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 10px;
            max-width: 80%;
        }}
        
        .user-message {{
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }}
        
        .ai-message {{
            background: rgba(0,0,0,0.1);
            color: #333;
        }}
        
        /* Dashboard Cards */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}
        
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        
        .status-operational {{ background: #4CAF50; }}
        .status-maintenance {{ background: #FF9800; }}
        .status-critical {{ background: #F44336; }}
    </style>
</head>
<body>
    <div class="cmms-header">
        <h1>🔧 ChatterFix CMMS</h1>
        <p>AI-Enhanced Maintenance Management System</p>
    </div>

    <div class="container">
        <div class="dashboard-grid">
            <div class="cmms-card">
                <h3>📋 Work Orders</h3>
                <div id="work-orders-summary">
                    <p>Loading work orders...</p>
                </div>
                <button onclick="location.href='/work-orders'" class="btn btn-primary">Manage Work Orders</button>
            </div>

            <div class="cmms-card">
                <h3>🏭 Assets</h3>
                <div id="assets-summary">
                    <p>Loading assets...</p>
                </div>
                <button onclick="location.href='/assets'" class="btn btn-primary">Manage Assets</button>
            </div>

            <div class="cmms-card">
                <h3>🤖 AI Assistant</h3>
                <p>Get instant help with maintenance tasks, troubleshooting, and operational guidance.</p>
                <button onclick="toggleAIChat()" class="btn btn-primary">Open AI Assistant</button>
            </div>

            <div class="cmms-card">
                <h3>📊 Analytics</h3>
                <p>View maintenance metrics, performance trends, and predictive insights.</p>
                <button onclick="location.href='/analytics'" class="btn btn-primary">View Analytics</button>
            </div>
        </div>
    </div>

    <!-- AI Assistant -->
    <div id="ai-assistant">
        <button id="ai-toggle" onclick="toggleAIChat()">🤖</button>
        <div id="ai-chat">
            <div class="ai-header">
                ChatterFix AI Assistant
                <button style="float: right; background: none; border: none; color: white; cursor: pointer;" onclick="toggleAIChat()">×</button>
            </div>
            <div class="ai-messages" id="ai-messages">
                <div class="message ai-message">
                    Hello! I'm your ChatterFix AI assistant. I can help you with maintenance tasks, troubleshooting, work order management, and more. How can I assist you today?
                </div>
            </div>
            <div class="ai-input-area">
                <input type="text" class="ai-input" id="ai-input" placeholder="Ask me about maintenance..." onkeypress="handleAIInput(event)">
            </div>
        </div>
    </div>

    <script>
        let aiChatVisible = false;

        function toggleAIChat() {{
            const aiChat = document.getElementById('ai-chat');
            aiChatVisible = !aiChatVisible;
            aiChat.style.display = aiChatVisible ? 'flex' : 'none';
            
            if (aiChatVisible) {{
                document.getElementById('ai-input').focus();
            }}
        }}

        async function handleAIInput(event) {{
            if (event.key === 'Enter') {{
                const input = document.getElementById('ai-input');
                const query = input.value.trim();
                
                if (!query) return;
                
                // Add user message
                addMessage(query, 'user');
                input.value = '';
                
                // Add thinking indicator
                const thinkingDiv = addMessage('🤔 Thinking...', 'ai');
                
                try {{
                    const response = await fetch('/api/ai/query', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ query: query }})
                    }});
                    
                    const data = await response.json();
                    
                    // Remove thinking indicator
                    thinkingDiv.remove();
                    
                    // Add AI response
                    addMessage(data.response, 'ai');
                    
                }} catch (error) {{
                    thinkingDiv.remove();
                    addMessage('Sorry, I encountered an error. Please try again.', 'ai');
                }}
            }}
        }}

        function addMessage(text, sender) {{
            const messagesDiv = document.getElementById('ai-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{sender}}-message`;
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            return messageDiv;
        }}

        // Load dashboard data
        async function loadDashboardData() {{
            try {{
                // Load work orders summary
                const workOrdersResponse = await fetch('/api/work-orders/summary');
                const workOrdersData = await workOrdersResponse.json();
                document.getElementById('work-orders-summary').innerHTML = `
                    <p><span class="status-indicator status-critical"></span>Critical: ${{workOrdersData.critical || 0}}</p>
                    <p><span class="status-indicator status-maintenance"></span>In Progress: ${{workOrdersData.in_progress || 0}}</p>
                    <p><span class="status-indicator status-operational"></span>Completed: ${{workOrdersData.completed || 0}}</p>
                `;
                
                // Load assets summary
                const assetsResponse = await fetch('/api/assets/summary');
                const assetsData = await assetsResponse.json();
                document.getElementById('assets-summary').innerHTML = `
                    <p><span class="status-indicator status-operational"></span>Operational: ${{assetsData.operational || 0}}</p>
                    <p><span class="status-indicator status-maintenance"></span>Maintenance: ${{assetsData.maintenance || 0}}</p>
                    <p><span class="status-indicator status-critical"></span>Critical: ${{assetsData.critical || 0}}</p>
                `;
                
            }} catch (error) {{
                console.error('Failed to load dashboard data:', error);
            }}
        }}

        // Load data when page loads
        document.addEventListener('DOMContentLoaded', loadDashboardData);
    </script>
</body>
</html>
    """)


@app.post("/api/ai/query")
async def ai_query(request: Request):
    """Handle AI assistant queries"""
    try:
        data = await request.json()
        query = data.get("query", "")

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Get context from recent work orders and assets
        context = await get_maintenance_context()

        # Query LLaMA
        response = await llama_client.query(query, context)

        # Store interaction
        store_ai_interaction(query, response)

        return JSONResponse({"response": response, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        logger.error(f"AI query error: {e}")
        return JSONResponse(
            {"response": "I'm having trouble processing your request. Please try again."},
            status_code=500,
        )


async def get_maintenance_context() -> str:
    """Get relevant maintenance context for AI queries"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get recent work orders
        cursor.execute("""
            SELECT title, description, status, priority 
            FROM work_orders 
            WHERE created_at > datetime('now', '-7 days')
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        work_orders = cursor.fetchall()

        # Get critical assets
        cursor.execute("""
            SELECT name, type, status, location 
            FROM assets 
            WHERE status != 'operational' 
            ORDER BY last_maintenance DESC 
            LIMIT 5
        """)
        assets = cursor.fetchall()

        conn.close()

        context = "Recent maintenance context:\n"
        if work_orders:
            context += "Recent Work Orders:\n"
            for wo in work_orders:
                context += f"- {wo[0]} ({wo[2]}, {wo[3]} priority): {wo[1]}\n"

        if assets:
            context += "\nAssets requiring attention:\n"
            for asset in assets:
                context += f"- {asset[0]} ({asset[1]}) at {asset[3]}: {asset[2]}\n"

        return context

    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return ""


def store_ai_interaction(query: str, response: str):
    """Store AI interaction in database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ai_interactions (query, response) VALUES (?, ?)",
            (query, response),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error storing AI interaction: {e}")


@app.get("/api/work-orders/summary")
async def work_orders_summary():
    """Get work orders summary for dashboard"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT status, COUNT(*) FROM work_orders GROUP BY status")
        results = cursor.fetchall()

        summary = {}
        for status, count in results:
            if status in ["critical", "high"]:
                summary["critical"] = summary.get("critical", 0) + count
            elif status in ["in_progress", "assigned"]:
                summary["in_progress"] = summary.get("in_progress", 0) + count
            elif status == "completed":
                summary["completed"] = count

        conn.close()
        return summary

    except Exception as e:
        logger.error(f"Error getting work orders summary: {e}")
        return {"critical": 0, "in_progress": 0, "completed": 0}


@app.get("/api/assets/summary")
async def assets_summary():
    """Get assets summary for dashboard"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT status, COUNT(*) FROM assets GROUP BY status")
        results = cursor.fetchall()

        summary = {}
        for status, count in results:
            summary[status] = count

        conn.close()
        return summary

    except Exception as e:
        logger.error(f"Error getting assets summary: {e}")
        return {"operational": 0, "maintenance": 0, "critical": 0}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = sqlite3.connect(DATABASE_PATH)
        conn.close()

        # Test LLaMA connection
        llama_status = "unknown"
        try:
            response = requests.get(f"{llama_client.base_url}/api/version", timeout=5)
            llama_status = "online" if response.status_code == 200 else "offline"
        except:
            llama_status = "offline"

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "llama": llama_status,
            "version": "2.0.0",
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)