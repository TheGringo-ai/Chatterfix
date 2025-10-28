#!/usr/bin/env python3
"""
Example Application with AI Team Integration
Demonstrates how to add Claude + Grok collaboration to any app

This example shows:
1. How to integrate the AI team into your existing app
2. Real-time AI collaboration features
3. Task management with AI assistance
4. Chatbot functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
from typing import Optional, Dict, Any
from ai_team_integration import AITeamIntegration, AITeamChatbot, ask_ai_team, solve_problem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize your app
app = FastAPI(
    title="AI Team Integration Example",
    description="Example app showing Claude + Grok collaboration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI team (you can pass API keys here or use environment variables)
ai_team = AITeamIntegration()
chatbot = AITeamChatbot()

# Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ProblemRequest(BaseModel):
    problem: str
    context: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    title: str
    description: str
    priority: str = "medium"

@app.get("/", response_class=HTMLResponse)
async def demo_dashboard():
    """Demo dashboard showing AI team integration"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Team Integration Demo</title>
        <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 3rem; }
        .demo-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; }
        .demo-card { 
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 2rem; border: 1px solid rgba(255,255,255,0.2);
        }
        .demo-card h3 { margin-bottom: 1rem; color: #00f5ff; }
        .input-group { margin-bottom: 1rem; }
        .input-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        .input-group input, .input-group textarea { 
            width: 100%; padding: 0.75rem; border-radius: 8px; border: none;
            background: rgba(255,255,255,0.9); color: #333;
        }
        .btn { 
            background: linear-gradient(45deg, #00f5ff, #ff6b6b); border: none; 
            padding: 0.75rem 1.5rem; border-radius: 8px; color: white; 
            font-weight: 600; cursor: pointer; transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .response-area { 
            margin-top: 1rem; padding: 1rem; background: rgba(0,0,0,0.3); 
            border-radius: 8px; min-height: 150px; overflow-y: auto;
        }
        .ai-response { margin-bottom: 1rem; padding: 0.75rem; background: rgba(255,255,255,0.1); border-radius: 8px; }
        .ai-name { font-weight: 600; color: #00f5ff; margin-bottom: 0.5rem; }
        .confidence { font-size: 0.8rem; opacity: 0.8; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Team Integration Demo</h1>
                <p>Experience Claude + Grok collaboration in your apps</p>
            </div>
            
            <div class="demo-grid">
                <!-- Chat with AI Team -->
                <div class="demo-card">
                    <h3>💬 Chat with AI Team</h3>
                    <div class="input-group">
                        <label>Ask the AI team anything:</label>
                        <input type="text" id="chatInput" placeholder="How do I optimize my database queries?">
                    </div>
                    <button class="btn" onclick="chatWithAITeam()">Chat with AI Team</button>
                    <div id="chatResponse" class="response-area">AI team responses will appear here...</div>
                </div>
                
                <!-- Solve Complex Problems -->
                <div class="demo-card">
                    <h3>🧠 Problem Solving</h3>
                    <div class="input-group">
                        <label>Describe your problem:</label>
                        <textarea id="problemInput" rows="3" placeholder="I need to build a scalable microservices architecture..."></textarea>
                    </div>
                    <button class="btn" onclick="solveProblem()">Solve with AI Team</button>
                    <div id="problemResponse" class="response-area">AI team solutions will appear here...</div>
                </div>
                
                <!-- Ask AI Team -->
                <div class="demo-card">
                    <h3>❓ Quick AI Consultation</h3>
                    <div class="input-group">
                        <label>Quick question:</label>
                        <input type="text" id="quickInput" placeholder="What's the best Python web framework?">
                    </div>
                    <button class="btn" onclick="askAITeam()">Ask AI Team</button>
                    <div id="quickResponse" class="response-area">Quick AI responses will appear here...</div>
                </div>
                
                <!-- AI Team Status -->
                <div class="demo-card">
                    <h3>📊 AI Team Status</h3>
                    <button class="btn" onclick="getAIStatus()">Check AI Team Status</button>
                    <div id="statusResponse" class="response-area">AI team status will appear here...</div>
                </div>
            </div>
        </div>
        
        <script>
        async function chatWithAITeam() {
            const input = document.getElementById('chatInput');
            const response = document.getElementById('chatResponse');
            
            if (!input.value.trim()) return;
            
            response.innerHTML = '<div>🤖 AI team is thinking...</div>';
            
            try {
                const result = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: input.value})
                });
                
                const data = await result.json();
                
                response.innerHTML = `
                    <div class="ai-response">
                        <div class="ai-name">Best Response (${data.ai_provider})</div>
                        <div>${data.response}</div>
                        <div class="confidence">Confidence: ${(data.confidence * 100).toFixed(1)}%</div>
                    </div>
                    ${data.suggestions ? `<div><strong>Suggestions:</strong> ${data.suggestions.join(', ')}</div>` : ''}
                `;
            } catch (error) {
                response.innerHTML = `<div style="color: #ff6b6b;">Error: ${error.message}</div>`;
            }
            
            input.value = '';
        }
        
        async function solveProblem() {
            const input = document.getElementById('problemInput');
            const response = document.getElementById('problemResponse');
            
            if (!input.value.trim()) return;
            
            response.innerHTML = '<div>🧠 AI team is analyzing and solving...</div>';
            
            try {
                const result = await fetch('/api/solve', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({problem: input.value})
                });
                
                const data = await result.json();
                
                response.innerHTML = `
                    <div class="ai-response">
                        <div class="ai-name">Solution (Confidence: ${(data.confidence_score * 100).toFixed(1)}%)</div>
                        <div><strong>Analysis:</strong> ${data.analysis.best_response.content.substring(0, 200)}...</div>
                        <div><strong>Solution:</strong> ${data.solution.best_response.content.substring(0, 200)}...</div>
                        <div><strong>Recommendations:</strong> ${data.recommendations.slice(0, 3).join(', ')}</div>
                    </div>
                `;
            } catch (error) {
                response.innerHTML = `<div style="color: #ff6b6b;">Error: ${error.message}</div>`;
            }
            
            input.value = '';
        }
        
        async function askAITeam() {
            const input = document.getElementById('quickInput');
            const response = document.getElementById('quickResponse');
            
            if (!input.value.trim()) return;
            
            response.innerHTML = '<div>⚡ Getting quick AI insights...</div>';
            
            try {
                const result = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: input.value})
                });
                
                const data = await result.json();
                let html = '';
                
                for (const [aiName, aiData] of Object.entries(data.responses)) {
                    html += `
                        <div class="ai-response">
                            <div class="ai-name">${aiName.toUpperCase()}</div>
                            <div>${aiData.content.substring(0, 150)}...</div>
                            <div class="confidence">Confidence: ${(aiData.confidence * 100).toFixed(1)}%</div>
                        </div>
                    `;
                }
                
                response.innerHTML = html;
            } catch (error) {
                response.innerHTML = `<div style="color: #ff6b6b;">Error: ${error.message}</div>`;
            }
            
            input.value = '';
        }
        
        async function getAIStatus() {
            const response = document.getElementById('statusResponse');
            response.innerHTML = '<div>📊 Checking AI team status...</div>';
            
            try {
                const result = await fetch('/api/status');
                const data = await result.json();
                
                response.innerHTML = `
                    <div class="ai-response">
                        <div class="ai-name">AI Team Status</div>
                        <div><strong>Available AIs:</strong> ${data.available_providers.join(', ')}</div>
                        <div><strong>Active Tasks:</strong> ${data.active_tasks}</div>
                        <div><strong>Completed Tasks:</strong> ${data.completed_tasks}</div>
                        <div><strong>Conversation History:</strong> ${data.conversation_history_length} interactions</div>
                    </div>
                `;
            } catch (error) {
                response.innerHTML = `<div style="color: #ff6b6b;">Error: ${error.message}</div>`;
            }
        }
        
        // Allow Enter key to submit
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') chatWithAITeam();
        });
        document.getElementById('quickInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') askAITeam();
        });
        </script>
    </body>
    </html>
    """

@app.post("/api/chat")
async def chat_with_ai_team(message: ChatMessage):
    """Chat endpoint that uses AI team collaboration"""
    try:
        response = await chatbot.chat(message.message)
        return response
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/solve")
async def solve_with_ai_team(request: ProblemRequest):
    """Problem solving endpoint using AI team"""
    try:
        solution = await ai_team.solve_with_ai_team(request.problem, request.context)
        return solution
    except Exception as e:
        logger.error(f"Problem solving error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask")
async def ask_ai_team_endpoint(message: ChatMessage):
    """Quick ask endpoint for AI team consultation"""
    try:
        responses = await ai_team.collaborate_with_ai_team(message.message)
        return {
            "responses": {k: {
                "content": v.content,
                "confidence": v.confidence,
                "suggestions": v.suggestions
            } for k, v in responses.items()}
        }
    except Exception as e:
        logger.error(f"Ask AI team error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_ai_team_status():
    """Get current AI team status"""
    try:
        return ai_team.get_ai_team_status()
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Team Integration Example",
        "version": "1.0.0",
        "ai_team_available": len(ai_team.get_available_providers()) > 0,
        "available_ai_providers": [p.value for p in ai_team.get_available_providers()]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Team Integration Example App")
    print("🤖 Claude + Grok + Multi-AI Collaboration Ready")
    print("🌐 Visit http://localhost:8000 to try the demo")
    uvicorn.run(app, host="0.0.0.0", port=8000)