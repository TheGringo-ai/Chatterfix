#!/usr/bin/env python3
"""
ChatterFix CMMS - Lightweight Microservices Gateway
Replaces the monolithic 9000+ line app.py with a clean routing gateway
"""
import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatterFix CMMS Gateway",
    description="Lightweight gateway routing to microservices",
    version="2.0.0"
)

# Microservices configuration
SERVICES = {
    "database": "http://localhost:8001",
    "work_orders": "http://localhost:8002", 
    "assets": "http://localhost:8003",
    "parts": "http://localhost:8004",
    "ai_brain": "http://localhost:9000",
    "fix_it_fred": "http://localhost:8081"  # AI chat backend running on 8081
}

# Request models
class ChatRequest(BaseModel):
    message: str
    equipment: Optional[str] = "ChatterFix CMMS Platform"

# Landing page with WORKING chat widget
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Clean landing page with Fix It Fred chat integration"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS - AI-Powered Maintenance Management</title>
    <style>
        :root {
            --primary-blue: #006fee;
            --success-green: #00c851;
            --text-dark: #1a202c;
            --bg-light: #f8f9fa;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: var(--text-dark); }
        .hero { background: linear-gradient(135deg, var(--primary-blue), var(--success-green)); color: white; padding: 4rem 2rem; text-align: center; }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
        .hero p { font-size: 1.2rem; max-width: 600px; margin: 0 auto; }
        .chat-bubble { position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; background: var(--primary-blue); border-radius: 50%; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .chat-bubble:hover { transform: scale(1.1); }
        .chat-icon { color: white; font-size: 24px; }
        .chat-window { position: fixed; bottom: 90px; right: 20px; width: 350px; height: 500px; background: white; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); display: none; z-index: 1001; flex-direction: column; }
        .chat-header { background: var(--primary-blue); color: white; padding: 1rem; border-radius: 12px 12px 0 0; font-weight: 600; }
        .chat-messages { flex: 1; padding: 1rem; overflow-y: auto; }
        .chat-input { padding: 1rem; border-top: 1px solid #eee; }
        .chat-input input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }
        .message { margin-bottom: 1rem; }
        .user-message { text-align: right; }
        .bot-message { text-align: left; }
        .message-content { display: inline-block; padding: 8px 12px; border-radius: 8px; max-width: 80%; }
        .user-message .message-content { background: var(--primary-blue); color: white; }
        .bot-message .message-content { background: #f1f3f5; color: var(--text-dark); }
    </style>
</head>
<body>
    <div class="hero">
        <h1>ChatterFix CMMS</h1>
        <p>AI-Powered Maintenance Management System with Real-Time Chat Support</p>
    </div>

    <!-- Chat Bubble -->
    <div class="chat-bubble" onclick="toggleChat()">
        <div class="chat-icon">💬</div>
    </div>

    <!-- Chat Window -->
    <div class="chat-window" id="chatWindow">
        <div class="chat-header">
            Fix It Fred - AI Assistant
            <span style="float: right; cursor: pointer;" onclick="toggleChat()">×</span>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                <div class="message-content">
                    Hi! I'm Fix It Fred, your AI maintenance assistant. How can I help you with ChatterFix CMMS today?
                </div>
            </div>
        </div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Ask about equipment, maintenance, or CMMS features..." onkeypress="handleKeyPress(event)">
        </div>
    </div>

    <script>
        function toggleChat() {
            const chatWindow = document.getElementById('chatWindow');
            chatWindow.style.display = chatWindow.style.display === 'flex' ? 'none' : 'flex';
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;

            // Add user message
            addMessage(message, 'user');
            input.value = '';

            try {
                // Send to Fix It Fred API
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.response, 'bot');
                } else {
                    addMessage('I apologize, but I\'m having trouble connecting. Please try again.', 'bot');
                }
            } catch (error) {
                addMessage('Connection error. Please try again later.', 'bot');
            }
        }

        function addMessage(content, type) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
"""

# Chat API - Routes to Fix It Fred
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint that routes to Fix It Fred"""
    try:
        # Route to AI Chat Backend (Fix It Fred)
        fred_response = requests.post(
            "http://localhost:8081/api/ai/chat",
            json={
                "message": request.message,
                "context": "ChatterFix CMMS user inquiry"
            },
            timeout=30
        )
        
        if fred_response.status_code == 200:
            data = fred_response.json()
            # Handle different response formats from AI chat backend
            response_text = data.get('response') or data.get('data', {}).get('response') or str(data)
            return {
                "success": True,
                "response": response_text
            }
        
        return {"success": False, "error": "Fix It Fred unavailable"}
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"success": False, "error": str(e)}

# Microservices proxy endpoints
@app.api_route("/api/work-orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_work_orders(request: Request, path: str):
    """Proxy to work orders microservice"""
    return await proxy_request(request, "work_orders", path)

@app.api_route("/api/assets/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]) 
async def proxy_assets(request: Request, path: str):
    """Proxy to assets microservice"""
    return await proxy_request(request, "assets", path)

@app.api_route("/api/parts/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_parts(request: Request, path: str):
    """Proxy to parts microservice"""
    return await proxy_request(request, "parts", path)

@app.api_route("/api/database/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_database(request: Request, path: str):
    """Proxy to database microservice"""
    return await proxy_request(request, "database", path)

async def proxy_request(request: Request, service: str, path: str):
    """Generic proxy function for microservices"""
    try:
        service_url = SERVICES.get(service)
        if not service_url:
            raise HTTPException(status_code=404, detail=f"Service {service} not found")
        
        # Forward request to microservice
        url = f"{service_url}/{path}"
        
        if request.method == "GET":
            response = requests.get(url, params=dict(request.query_params))
        else:
            body = await request.body()
            headers = {"Content-Type": request.headers.get("content-type", "application/json")}
            response = requests.request(request.method, url, data=body, headers=headers)
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {}
        )
        
    except Exception as e:
        logger.error(f"Proxy error for {service}/{path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    service_status = {}
    for name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            service_status[name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            service_status[name] = "unreachable"
    
    return {
        "status": "healthy",
        "gateway": "ChatterFix Lightweight Gateway",
        "version": "2.0.0",
        "services": service_status
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)