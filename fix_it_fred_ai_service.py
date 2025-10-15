#!/usr/bin/env python3
"""
Fix It Fred AI Service - Multi-Provider AI Backend
Supports OpenAI, Anthropic Claude, Google Gemini, xAI Grok, and Local Ollama
"""
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging
import hashlib
import time
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure HTTP session with connection pooling and retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Simple response cache for improved performance
response_cache = {}
cache_stats = defaultdict(int)
CACHE_TTL = 300  # 5 minutes

def get_cache_key(message: str, context: str = None) -> str:
    """Generate cache key for message and context"""
    cache_input = f"{message}|{context or ''}"
    return hashlib.md5(cache_input.encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[str]:
    """Get cached response if still valid"""
    if cache_key in response_cache:
        cached_data, timestamp = response_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            cache_stats['hits'] += 1
            return cached_data
        else:
            del response_cache[cache_key]  # Clean expired entry
    cache_stats['misses'] += 1
    return None

def cache_response(cache_key: str, response: str):
    """Cache a response with timestamp"""
    response_cache[cache_key] = (response, time.time())

# Initialize FastAPI app
app = FastAPI(
    title="Fix It Fred AI Service",
    description="Multi-Provider AI Backend for ChatterFix CMMS",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_role: Optional[str] = "technician"
    context: Optional[str] = None
    provider: Optional[str] = "ollama"  # ollama, openai, anthropic, google, xai
    model: Optional[str] = "mistral:7b"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class AIProvider(BaseModel):
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: List[str] = []
    enabled: bool = False

class UserSettings(BaseModel):
    providers: Dict[str, AIProvider] = {}
    default_provider: str = "ollama"
    default_model: str = "mistral:7b"

# Global settings storage (in production, this would be a database)
user_settings = UserSettings(
    providers={
        "ollama": AIProvider(
            name="Ollama (Local)",
            base_url="http://localhost:11434",
            models=["mistral:7b", "llama3:8b"],
            enabled=True
        ),
        "openai": AIProvider(
            name="OpenAI GPT",
            base_url="https://api.openai.com/v1",
            models=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            enabled=False
        ),
        "anthropic": AIProvider(
            name="Anthropic Claude",
            base_url="https://api.anthropic.com",
            models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            enabled=False
        ),
        "google": AIProvider(
            name="Google Gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            models=["gemini-1.5-pro", "gemini-1.5-flash"],
            enabled=False
        ),
        "xai": AIProvider(
            name="xAI Grok",
            base_url="https://api.x.ai/v1",
            models=["grok-beta", "grok-vision-beta"],
            enabled=False
        )
    }
)

# Fix It Fred personality prompt - OPTIMIZED (reduced from 25 lines to 8 lines)
FIX_IT_FRED_SYSTEM_PROMPT = """
You are Fix It Fred, an expert CMMS maintenance assistant. Focus on:
- Parts management, work orders, asset maintenance
- Safety-first approach with actionable recommendations
- Cost-effective solutions and preventive measures
- Clear, concise responses with bullet points

Keep responses brief, practical, and professional.
"""

async def call_ollama(message: str, model: str = "mistral:7b", context: str = None) -> str:
    """Call local Ollama API with caching"""
    try:
        # Check cache first
        cache_key = get_cache_key(f"{model}:{message}", context)
        cached_response = get_cached_response(cache_key)
        if cached_response:
            logger.info(f"Cache hit for message: {message[:50]}...")
            return cached_response
            
        full_prompt = f"{FIX_IT_FRED_SYSTEM_PROMPT}\n\nContext: {context or 'CMMS Parts Management'}\n\nUser: {message}\n\nFix It Fred:"
        
        response = session.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stop": ["User:", "Human:"]
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            ai_response = response.json().get("response", "").strip()
            # Cache the response
            cache_response(cache_key, ai_response)
            return ai_response
        else:
            logger.error(f"Ollama error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ollama connection error: {e}")
        return None

async def call_openai(message: str, api_key: str, model: str = "gpt-3.5-turbo", context: str = None) -> str:
    """Call OpenAI API"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": FIX_IT_FRED_SYSTEM_PROMPT},
                {"role": "user", "content": f"Context: {context or 'CMMS Parts Management'}\n\n{message}"}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=90
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            logger.error(f"OpenAI error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"OpenAI connection error: {e}")
        return None

async def call_anthropic(message: str, api_key: str, model: str = "claude-3-sonnet-20240229", context: str = None) -> str:
    """Call Anthropic Claude API"""
    try:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": f"{FIX_IT_FRED_SYSTEM_PROMPT}\n\nContext: {context or 'CMMS Parts Management'}\n\n{message}"}
            ]
        }
        
        response = session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=90
        )
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"].strip()
        else:
            logger.error(f"Anthropic error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Anthropic connection error: {e}")
        return None

async def call_google(message: str, api_key: str, model: str = "gemini-1.5-pro-latest", context: str = None) -> str:
    """Call Google Gemini API"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        data = {
            "contents": [{
                "parts": [{
                    "text": f"{FIX_IT_FRED_SYSTEM_PROMPT}\n\nContext: {context or 'CMMS Parts Management'}\n\n{message}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000
            }
        }
        
        response = session.post(url, json=data, timeout=90)
        
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            logger.error(f"Google error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Google connection error: {e}")
        return None

async def call_xai(message: str, api_key: str, model: str = "grok-beta", context: str = None) -> str:
    """Call xAI Grok API"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": FIX_IT_FRED_SYSTEM_PROMPT},
                {"role": "user", "content": f"Context: {context or 'CMMS Parts Management'}\n\n{message}"}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = session.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=90
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            logger.error(f"xAI error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"xAI connection error: {e}")
        return None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint supporting multiple AI providers"""
    return await _handle_chat_request(request)

@app.post("/api/ai/chat")
async def ai_chat_endpoint(request: ChatRequest):
    """Alternative chat endpoint for compatibility"""
    return await _handle_chat_request(request)

async def _handle_chat_request(request: ChatRequest):
    try:
        provider = user_settings.providers.get(request.provider, user_settings.providers["ollama"])
        
        if not provider.enabled:
            # Fallback to Ollama if selected provider is not enabled
            provider = user_settings.providers["ollama"]
            request.provider = "ollama"
        
        response_text = None
        
        # Route to appropriate AI provider
        if request.provider == "ollama":
            response_text = await call_ollama(request.message, request.model, request.context)
        elif request.provider == "openai" and provider.api_key:
            response_text = await call_openai(request.message, provider.api_key, request.model, request.context)
        elif request.provider == "anthropic" and provider.api_key:
            response_text = await call_anthropic(request.message, provider.api_key, request.model, request.context)
        elif request.provider == "google" and provider.api_key:
            response_text = await call_google(request.message, provider.api_key, request.model, request.context)
        elif request.provider == "xai" and provider.api_key:
            response_text = await call_xai(request.message, provider.api_key, request.model, request.context)
        
        if response_text:
            return {
                "success": True,
                "response": response_text,
                "provider": request.provider,
                "model": request.model,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Enhanced fallback response with useful CMMS tips
            fallback_tips = [
                "💡 Schedule preventive maintenance for high-priority assets",
                "📦 Review parts inventory for low stock alerts", 
                "⚠️ Check work order completion rates and bottlenecks",
                "🔧 Ensure technicians have required parts before starting jobs"
            ]
            import random
            tip = random.choice(fallback_tips)
            
            return {
                "success": True,
                "response": f"I'm Fix It Fred, your AI maintenance assistant! {tip}\n\nI'm currently optimizing my connection to provide better responses. Please try again in a moment.",
                "provider": "fallback",
                "model": "local", 
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/providers")
async def get_providers():
    """Get available AI providers and their status"""
    return {
        "providers": {
            name: {
                "name": provider.name,
                "enabled": provider.enabled,
                "models": provider.models,
                "has_api_key": bool(provider.api_key)
            }
            for name, provider in user_settings.providers.items()
        },
        "default_provider": user_settings.default_provider
    }

@app.post("/api/providers/{provider_name}/configure")
async def configure_provider(provider_name: str, api_key: str = Form(None)):
    """Configure AI provider with API key"""
    if provider_name not in user_settings.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = user_settings.providers[provider_name]
    if api_key:
        provider.api_key = api_key
        provider.enabled = True
    else:
        provider.enabled = False
    
    return {
        "success": True,
        "message": f"Provider {provider_name} configured successfully",
        "enabled": provider.enabled
    }

@app.get("/api/models/{provider_name}")
async def get_provider_models(provider_name: str):
    """Get available models for a provider"""
    if provider_name not in user_settings.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = user_settings.providers[provider_name]
    
    # For Ollama, fetch models dynamically
    if provider_name == "ollama":
        try:
            response = session.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                provider.models = [model["name"] for model in models_data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
    
    return {
        "provider": provider_name,
        "models": provider.models,
        "enabled": provider.enabled
    }

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics"""
    total_requests = cache_stats['hits'] + cache_stats['misses']
    hit_rate = (cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "cache_hits": cache_stats['hits'],
        "cache_misses": cache_stats['misses'],
        "total_requests": total_requests,
        "hit_rate_percent": round(hit_rate, 2),
        "cache_size": len(response_cache),
        "cache_ttl_seconds": CACHE_TTL
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Ollama status
    ollama_status = "unknown"
    try:
        response = session.get("http://localhost:11434/api/tags", timeout=2)
        ollama_status = "running" if response.status_code == 200 else "error"
    except:
        ollama_status = "offline"
    
    return {
        "status": "healthy",
        "service": "Fix It Fred AI Service",
        "providers": {
            name: provider.enabled for name, provider in user_settings.providers.items()
        },
        "ollama_status": ollama_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9001))  # Default to 9001 to avoid conflicts
    print(f"🤖 Starting Fix It Fred AI Service on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)