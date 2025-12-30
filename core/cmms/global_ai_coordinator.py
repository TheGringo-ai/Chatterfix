#!/usr/bin/env python3
"""
ChatterFix CMMS - Global AI Team Coordinator
Multi-AI system using web APIs for global deployment - Grok, OpenAI, Claude, Gemini
Ready to rock the entire planet! 🚀🌍
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
import json
import os
import logging
import httpx
import uuid
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix Global AI Team", version="3.0.0", description="🌍 Global AI deployment ready!")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global API Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY", "your-xai-key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-key") 
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-key")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "your-google-key")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")  # Only local option

# AI Provider Configuration for Global Deployment
class AIProvider:
    def __init__(self, name: str, enabled: bool = True, api_type: str = "web"):
        self.name = name
        self.enabled = enabled
        self.api_type = api_type  # "web" or "local"
        self.api_key = None

# Global AI Team Setup - Web APIs Only (except Ollama)
GLOBAL_AI_PROVIDERS = {
    "grok": AIProvider("Grok (xAI)", enabled=True, api_type="web"),
    "openai": AIProvider("OpenAI GPT-4", enabled=True, api_type="web"),
    "claude": AIProvider("Claude (Anthropic)", enabled=True, api_type="web"),
    "gemini": AIProvider("Google Gemini", enabled=True, api_type="web"),
    "ollama": AIProvider("Ollama (Local)", enabled=True, api_type="local"),  # Only local option
}

# Request Models
class AIRequest(BaseModel):
    message: str
    context: Optional[str] = ""
    preferred_provider: Optional[str] = "grok"
    use_memory: Optional[bool] = True
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class APIKeyConfig(BaseModel):
    provider: str
    api_key: str
    user_id: Optional[str] = None

# Global Web API Functions
async def call_xai_grok_api(message: str, context: str = "") -> Dict[str, Any]:
    """Call xAI Grok API - Primary Global AI"""
    try:
        if not XAI_API_KEY or XAI_API_KEY == "your-xai-key":
            return {"error": "XAI_API_KEY not configured", "success": False}
            
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": f"You are Grok, the most advanced AI for ChatterFix CMMS. Context: {context}"},
                {"role": "user", "content": message}
            ],
            "max_tokens": 2000,
            "temperature": 0.8,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=45.0
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                return {
                    "response": ai_response,
                    "provider": "grok-xai",
                    "model": "grok-beta",
                    "success": True,
                    "global_deployment": True
                }
            else:
                return {"error": f"xAI API error: {response.status_code}", "success": False}
                
    except Exception as e:
        logger.error(f"xAI Grok API error: {e}")
        return {"error": str(e), "success": False}

async def call_openai_api(message: str, context: str = "") -> Dict[str, Any]:
    """Call OpenAI GPT-4 API"""
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-key":
            return {"error": "OPENAI_API_KEY not configured", "success": False}
            
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4-turbo-preview",
            "messages": [
                {"role": "system", "content": f"You are an advanced AI assistant for ChatterFix CMMS. Context: {context}"},
                {"role": "user", "content": message}
            ],
            "max_tokens": 2000,
            "temperature": 0.8
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=45.0
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                return {
                    "response": ai_response,
                    "provider": "openai",
                    "model": "gpt-4-turbo-preview",
                    "success": True,
                    "global_deployment": True
                }
            else:
                return {"error": f"OpenAI API error: {response.status_code}", "success": False}
                
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {"error": str(e), "success": False}

async def call_claude_api(message: str, context: str = "") -> Dict[str, Any]:
    """Call Anthropic Claude API"""
    try:
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-anthropic-key":
            return {"error": "ANTHROPIC_API_KEY not configured", "success": False}
            
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2000,
            "messages": [
                {"role": "user", "content": f"Context: {context}\n\nUser: {message}"}
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=45.0
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["content"][0]["text"]
                return {
                    "response": ai_response,
                    "provider": "claude",
                    "model": "claude-3-sonnet",
                    "success": True,
                    "global_deployment": True
                }
            else:
                return {"error": f"Claude API error: {response.status_code}", "success": False}
                
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return {"error": str(e), "success": False}

async def call_gemini_api(message: str, context: str = "") -> Dict[str, Any]:
    """Call Google Gemini API"""
    try:
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your-google-key":
            return {"error": "GOOGLE_API_KEY not configured", "success": False}
            
        prompt = f"Context: {context}\n\nUser: {message}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 2000
                    }
                },
                timeout=45.0
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "response": ai_response,
                    "provider": "gemini",
                    "model": "gemini-pro",
                    "success": True,
                    "global_deployment": True
                }
            else:
                return {"error": f"Gemini API error: {response.status_code}", "success": False}
                
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return {"error": str(e), "success": False}

async def call_ollama_api(message: str, context: str = "", model: str = "llama2") -> Dict[str, Any]:
    """Call local Ollama API - Only local option allowed"""
    try:
        data = {
            "model": model,
            "prompt": f"Context: {context}\n\nUser: {message}",
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_ENDPOINT}/api/generate",
                json=data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                return {
                    "response": ai_response,
                    "provider": "ollama",
                    "model": model,
                    "success": True,
                    "local_deployment": True
                }
            else:
                return {"error": f"Ollama API error: {response.status_code}", "success": False}
                
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return {"error": str(e), "success": False}

async def get_ai_response(request: AIRequest) -> Dict[str, Any]:
    """Get AI response using global web APIs with fallback chain"""
    
    # Priority order for global deployment
    provider_chain = [
        request.preferred_provider or "grok",
        "grok", "openai", "claude", "gemini", "ollama"
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    provider_chain = [p for p in provider_chain if not (p in seen or seen.add(p))]
    
    last_error = None
    
    for provider in provider_chain:
        try:
            logger.info(f"🌍 Trying global provider: {provider}")
            
            if provider == "grok":
                result = await call_xai_grok_api(request.message, request.context)
            elif provider == "openai":
                result = await call_openai_api(request.message, request.context)
            elif provider == "claude":
                result = await call_claude_api(request.message, request.context)
            elif provider == "gemini":
                result = await call_gemini_api(request.message, request.context)
            elif provider == "ollama":
                result = await call_ollama_api(request.message, request.context)
            else:
                continue
                
            if result.get("success"):
                logger.info(f"✅ Success with {provider}")
                return {
                    **result,
                    "timestamp": datetime.now().isoformat(),
                    "request_id": str(uuid.uuid4()),
                    "global_ai_deployment": True
                }
            else:
                last_error = result.get("error", f"Unknown error with {provider}")
                logger.warning(f"❌ {provider} failed: {last_error}")
                
        except Exception as e:
            last_error = str(e)
            logger.error(f"❌ {provider} exception: {e}")
            continue
    
    # All providers failed
    return {
        "response": "🌍 Global AI system temporarily unavailable. All providers failed.",
        "error": last_error,
        "provider": "fallback",
        "success": False,
        "global_deployment": True,
        "timestamp": datetime.now().isoformat()
    }

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "ChatterFix Global AI Team Coordinator",
        "status": "🚀 Ready to rock the entire planet!",
        "version": "3.0.0",
        "deployment": "global",
        "providers": {
            "primary": "Grok (xAI)",
            "available": ["Grok", "OpenAI GPT-4", "Claude", "Gemini", "Ollama (local)"],
            "api_types": "Web APIs (global deployment ready)"
        },
        "capabilities": ["multi-ai", "global_deployment", "web_apis", "fallback_chain"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Global AI Team Coordinator",
        "deployment": "🌍 Global Ready",
        "timestamp": datetime.now().isoformat(),
        "providers_available": len([p for p in GLOBAL_AI_PROVIDERS.values() if p.enabled])
    }

@app.post("/ai-team/ask")
async def ask_ai_team(request: AIRequest):
    """Ask the global AI team"""
    logger.info(f"🌍 Global AI request: {request.message[:100]}...")
    
    result = await get_ai_response(request)
    
    # Store in memory if requested
    if request.use_memory and result.get("success"):
        try:
            memory_data = {
                "user_message": request.message,
                "ai_response": result["response"],
                "context": {
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "provider": result.get("provider"),
                    "global_deployment": True
                }
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8014/memory/conversation",
                    json=memory_data,
                    timeout=5.0
                )
        except Exception as e:
            logger.warning(f"Memory storage failed: {e}")
    
    return result

@app.get("/ai-team/providers")
async def get_providers():
    """Get available AI providers"""
    providers = {}
    for key, provider in GLOBAL_AI_PROVIDERS.items():
        providers[key] = {
            "name": provider.name,
            "enabled": provider.enabled,
            "type": provider.api_type,
            "global_ready": provider.api_type == "web"
        }
    
    return {
        "providers": providers,
        "primary": "grok",
        "deployment": "global",
        "total_count": len(providers)
    }

@app.post("/ai-team/configure-api-key")
async def configure_api_key(config: APIKeyConfig):
    """Configure API key for provider (for user enhancement)"""
    if config.provider in GLOBAL_AI_PROVIDERS:
        # In production, store user-specific API keys securely
        logger.info(f"API key configured for {config.provider}")
        return {
            "success": True,
            "message": f"API key configured for {config.provider}",
            "global_deployment": True
        }
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8015))
    print(f"🌍🚀 Starting ChatterFix Global AI Team Coordinator on port {port}")
    print(f"Ready to rock the entire planet!")
    uvicorn.run(app, host="0.0.0.0", port=port)