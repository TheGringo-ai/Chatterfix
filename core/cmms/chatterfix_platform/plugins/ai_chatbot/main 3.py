#!/usr/bin/env python3
"""
AI Chatbot - AI Service
AI-powered chatbot for CMMS assistance
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import os
import sys
import json
from datetime import datetime

# Import ChatterFix platform services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from platform.core import shared_services, event_system, SystemEvents

logger = logging.getLogger(__name__)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    confidence: Optional[float] = None
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ConnectionManager:
    """WebSocket connection manager for real-time chat"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Create FastAPI app
app = FastAPI(
    title="AI Chatbot Service",
    description="AI-powered chatbot for CMMS assistance",
    version="1.0.0"
)

manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    """Service startup"""
    logger.info("Starting AI Chatbot Service")
    
    # Emit startup event
    await event_system.emit(
        SystemEvents.PLUGIN_STARTED,
        {"plugin_name": "ai_chatbot"},
        source="ai_chatbot"
    )

@app.on_event("shutdown")
async def shutdown():
    """Service shutdown"""
    logger.info("Shutting down AI Chatbot Service")
    
    # Emit shutdown event
    await event_system.emit(
        SystemEvents.PLUGIN_STOPPED,
        {"plugin_name": "ai_chatbot"},
        source="ai_chatbot"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Chatbot",
        "version": "1.0.0",
        "active_connections": len(manager.active_connections)
    }

@app.post("/api/ai_chatbot/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process chat message"""
    try:
        # Build context-aware prompt
        cmms_context = """
        You are a helpful AI assistant for ChatterFix CMMS (Computerized Maintenance Management System).
        You can help with:
        - Work order management
        - Asset maintenance
        - Parts inventory
        - Preventive maintenance scheduling
        - Equipment troubleshooting
        - Safety procedures
        
        Provide helpful, accurate, and actionable responses.
        """
        
        full_prompt = f"{cmms_context}\n\nUser: {message.message}\nAssistant:"
        
        # Use shared AI service
        result = await shared_services.ai.generate_text(
            prompt=full_prompt,
            provider="openai"
        )
        
        if result is None:
            raise HTTPException(status_code=500, detail="AI processing failed")
        
        # Generate suggestions based on context
        suggestions = []
        if "work order" in message.message.lower():
            suggestions = [
                "How do I create a work order?",
                "Show me pending work orders",
                "What's the priority system?"
            ]
        elif "asset" in message.message.lower():
            suggestions = [
                "How do I add a new asset?",
                "Show asset maintenance history",
                "What's the asset lifecycle?"
            ]
        elif "parts" in message.message.lower():
            suggestions = [
                "Check inventory levels",
                "How to order parts?",
                "Set reorder points"
            ]
        
        # Emit chat event
        await event_system.emit(
            SystemEvents.AI_ANALYSIS_COMPLETED,
            {
                "service": "ai_chatbot",
                "message_length": len(message.message),
                "response_length": len(result),
                "user_id": message.user_id
            },
            source="ai_chatbot"
        )
        
        return ChatResponse(
            response=result,
            confidence=0.85,
            suggestions=suggestions,
            metadata={
                "provider": "openai",
                "timestamp": datetime.now().isoformat(),
                "context": message.context
            }
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/ai_chatbot/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connected to AI Chatbot. How can I help you today?"
        }))
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message
            chat_message = ChatMessage(**message_data)
            response = await chat(chat_message)
            
            # Send response back
            await manager.send_personal_message(
                json.dumps({
                    "type": "response",
                    "response": response.response,
                    "suggestions": response.suggestions,
                    "metadata": response.metadata
                }),
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/ai_chatbot/status")
async def get_service_status():
    """Get service status and metrics"""
    return {
        "service": "AI Chatbot",
        "status": "running",
        "ai_provider": "openai",
        "active_connections": len(manager.active_connections),
        "features": [
            "Text chat",
            "WebSocket real-time chat",
            "CMMS context awareness",
            "Smart suggestions",
            "Event integration"
        ]
    }

@app.get("/api/ai_chatbot/suggestions/{category}")
async def get_suggestions(category: str):
    """Get predefined suggestions by category"""
    suggestions = {
        "work_orders": [
            "Create a new work order",
            "Show me all open work orders",
            "What's the priority classification?",
            "How do I assign a technician?",
            "Show completed work orders this week"
        ],
        "assets": [
            "Add a new asset to inventory",
            "Show asset maintenance schedule",
            "What's the depreciation rate?",
            "How do I update asset status?",
            "Show critical assets needing attention"
        ],
        "parts": [
            "Check current inventory levels",
            "How do I reorder parts?",
            "Set up automatic reorder points",
            "Show parts usage this month",
            "Find compatible parts for equipment"
        ],
        "maintenance": [
            "Schedule preventive maintenance",
            "Show overdue maintenance tasks",
            "How do I create a maintenance plan?",
            "What's the maintenance history?",
            "Show maintenance costs by asset"
        ]
    }
    
    return {
        "category": category,
        "suggestions": suggestions.get(category, []),
        "total": len(suggestions.get(category, []))
    }

# Plugin lifecycle functions
async def start():
    """Start the plugin"""
    logger.info("AI Chatbot plugin started")

async def stop():
    """Stop the plugin"""
    logger.info("AI Chatbot plugin stopped")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8100))
    uvicorn.run(app, host="0.0.0.0", port=port)