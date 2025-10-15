#!/usr/bin/env python3
"""
ChatterFix AI Brain Service - Cloud Compatible
Multi-Provider AI Backend for ChatterFix CMMS (Cloud Run Compatible)
"""
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
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
    title="ChatterFix AI Brain Service",
    description="Multi-Provider AI Backend for ChatterFix CMMS",
    version="2.0.0"
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
    provider: Optional[str] = "openai"  # Default to OpenAI for cloud
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

# ChatterFix CMMS AI personality prompt
CHATTERFIX_AI_SYSTEM_PROMPT = """
You are the ChatterFix AI assistant, an expert CMMS maintenance assistant. Focus on:
- Work orders, parts management, asset maintenance
- Safety-first approach with actionable recommendations
- Cost-effective solutions and preventive measures
- Clear, concise responses with bullet points

Keep responses brief, practical, and professional. Always prioritize safety and efficiency.
"""

async def call_openai(message: str, model: str = "gpt-3.5-turbo", context: str = None) -> str:
    """Call OpenAI API with environment API key"""
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found in environment")
            return None
            
        # Check cache first
        cache_key = get_cache_key(f"openai:{model}:{message}", context)
        cached_response = get_cached_response(cache_key)
        if cached_response:
            logger.info(f"Cache hit for OpenAI message: {message[:50]}...")
            return cached_response
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": CHATTERFIX_AI_SYSTEM_PROMPT},
                {"role": "user", "content": f"Context: {context or 'ChatterFix CMMS'}\n\n{message}"}
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
            ai_response = response.json()["choices"][0]["message"]["content"].strip()
            # Cache the response
            cache_response(cache_key, ai_response)
            return ai_response
        else:
            logger.error(f"OpenAI error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"OpenAI connection error: {e}")
        return None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for ChatterFix"""
    try:
        response_text = None
        
        # Try OpenAI first
        if os.environ.get("OPENAI_API_KEY"):
            response_text = await call_openai(request.message, request.model, request.context)
        
        if response_text:
            return {
                "success": True,
                "response": response_text,
                "provider": "openai",
                "model": request.model,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Enhanced fallback response with useful CMMS tips
            fallback_tips = [
                "💡 Schedule preventive maintenance for high-priority assets",
                "📦 Review parts inventory for low stock alerts", 
                "⚠️ Check work order completion rates and bottlenecks",
                "🔧 Ensure technicians have required parts before starting jobs",
                "📋 Update asset maintenance logs regularly",
                "🔍 Perform routine safety inspections"
            ]
            import random
            tip = random.choice(fallback_tips)
            
            return {
                "success": True,
                "response": f"Hi! I'm your ChatterFix AI assistant. {tip}\n\nI can help with work orders, asset management, parts inventory, and maintenance planning. What can I help you with?",
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

@app.get("/api/assets/{asset_id}/ai-insights")
async def get_asset_insights(asset_id: str):
    """Get AI insights for a specific asset"""
    try:
        # Generate contextual insights based on asset ID
        insights = [
            f"Recommended maintenance schedule for asset {asset_id}",
            "Check for wear patterns in critical components",
            "Monitor vibration levels and temperature",
            "Verify lubrication and filter status"
        ]
        
        return {
            "success": True,
            "asset_id": asset_id,
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Asset insights error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ChatterFix AI Brain Service",
        "version": "2.0.0",
        "providers": {
            "openai": bool(os.environ.get("OPENAI_API_KEY"))
        },
        "timestamp": datetime.now().isoformat()
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🤖 Starting ChatterFix AI Brain Service on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
