#!/usr/bin/env python3
"""
Simple AI Brain Service for ChatterFix
Fixed version for quick deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix AI Brain", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    context: str = "general"

class ChatResponse(BaseModel):
    response: str
    provider: str = "mock"
    context: str

@app.get("/")
def root():
    return {"message": "ChatterFix AI Brain Service", "status": "operational"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ai-brain"}

@app.get("/api/health")
def api_health():
    return {"status": "healthy", "service": "ai-brain", "timestamp": "2025-10-23"}

@app.post("/api/ai/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Basic chat endpoint with mock AI responses"""
    try:
        # Mock AI responses for different contexts
        responses = {
            "maintenance": f"For maintenance issue: '{request.message}' - I recommend checking the equipment manual and performing routine diagnostics.",
            "technical": f"Technical analysis: '{request.message}' - This appears to be a system-level issue. Please check connections and power supply.",
            "test": "AI BRAIN WORKING - Service is operational and responding correctly.",
            "general": f"I understand you're asking about: '{request.message}'. Let me help you with that."
        }
        
        response_text = responses.get(request.context, responses["general"])
        
        return ChatResponse(
            response=response_text,
            provider="chatterfix-mock-ai",
            context=request.context
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/providers")
def get_providers():
    """List available AI providers"""
    return {
        "providers": ["chatterfix-mock-ai"],
        "default": "chatterfix-mock-ai",
        "status": "operational"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)