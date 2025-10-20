#!/usr/bin/env python3
"""
Fix It Fred - Universal AI Assistant
====================================
Standalone AI assistant that can integrate into any application
- Multi-provider AI support (OpenAI, Anthropic, Google, xAI, Ollama)
- Universal API for easy integration
- Plugin system for custom applications
- Web interface for standalone use
- SDK for developers
"""

import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
import uvicorn
import logging
import hashlib
import time
import asyncio
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with enhanced metadata
app = FastAPI(
    title="Fix It Fred - Universal AI Assistant",
    description="Standalone AI assistant with multi-provider support and universal integration capabilities",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS for universal integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session configuration with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Enhanced caching system
response_cache = {}
cache_stats = defaultdict(int)
conversation_memory = defaultdict(list)
CACHE_TTL = 300  # 5 minutes
MAX_CONVERSATION_LENGTH = 20

# Universal AI Provider Configuration
AI_PROVIDERS = {
    "openai": {
        "name": "OpenAI GPT",
        "models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
        "default_model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
        "endpoint": "https://api.openai.com/v1/chat/completions"
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "default_model": "claude-3-5-sonnet-20241022",
        "api_key_env": "ANTHROPIC_API_KEY",
        "endpoint": "https://api.anthropic.com/v1/messages"
    },
    "google": {
        "name": "Google Gemini",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
        "default_model": "gemini-1.5-pro",
        "api_key_env": "GOOGLE_API_KEY",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models"
    },
    "xai": {
        "name": "xAI Grok",
        "models": ["grok-beta", "grok-vision-beta"],
        "default_model": "grok-beta",
        "api_key_env": "XAI_API_KEY",
        "endpoint": "https://api.x.ai/v1/chat/completions"
    },
    "ollama": {
        "name": "Local Ollama",
        "models": ["llama3.2", "qwen2.5", "codegemma"],
        "default_model": "llama3.2",
        "api_key_env": None,
        "endpoint": "http://localhost:11434/api/chat"
    }
}

# Pydantic Models for Universal API
class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None
    provider: Optional[str] = "anthropic"
    model: Optional[str] = None
    conversation_id: Optional[str] = None
    app_id: Optional[str] = None  # For app-specific integrations
    user_id: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

class IntegrationConfig(BaseModel):
    app_id: str
    app_name: str
    api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    allowed_providers: List[str] = ["anthropic", "openai"]
    default_provider: str = "anthropic"
    custom_instructions: Optional[str] = None

class PluginConfig(BaseModel):
    plugin_id: str
    plugin_name: str
    endpoints: List[str]
    capabilities: List[str]
    integration_type: str  # "webhook", "api", "embed"

# Storage for integrations and plugins
registered_integrations = {}
active_plugins = {}

# Utility functions
def get_cache_key(message: str, context: str = None, provider: str = None) -> str:
    cache_input = f"{message}|{context or ''}|{provider or ''}"
    return hashlib.md5(cache_input.encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[str]:
    if cache_key in response_cache:
        entry = response_cache[cache_key]
        if datetime.now() - entry['timestamp'] < timedelta(seconds=CACHE_TTL):
            cache_stats['hits'] += 1
            return entry['response']
        else:
            del response_cache[cache_key]
    cache_stats['misses'] += 1
    return None

def cache_response(cache_key: str, response: str):
    response_cache[cache_key] = {
        'response': response,
        'timestamp': datetime.now()
    }

def clean_old_cache():
    current_time = datetime.now()
    expired_keys = [
        key for key, entry in response_cache.items()
        if current_time - entry['timestamp'] > timedelta(seconds=CACHE_TTL)
    ]
    for key in expired_keys:
        del response_cache[key]

# AI Provider Functions
def call_anthropic(message: str, context: str = None, model: str = None) -> str:
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return "❌ Anthropic API key not configured"
    
    model = model or AI_PROVIDERS["anthropic"]["default_model"]
    
    headers = {
        'x-api-key': api_key,
        'content-type': 'application/json',
        'anthropic-version': '2023-06-01'
    }
    
    system_prompt = f"You are Fix It Fred, a helpful AI assistant. {context if context else ''}"
    
    data = {
        'model': model,
        'max_tokens': 2000,
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': message}]
    }
    
    try:
        response = session.post(
            AI_PROVIDERS["anthropic"]["endpoint"],
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()['content'][0]['text']
    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        return f"❌ Error calling Anthropic: {str(e)}"

def call_openai(message: str, context: str = None, model: str = None) -> str:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return "❌ OpenAI API key not configured"
    
    model = model or AI_PROVIDERS["openai"]["default_model"]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    system_message = f"You are Fix It Fred, a helpful AI assistant. {context if context else ''}"
    
    data = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': message}
        ],
        'max_tokens': 2000,
        'temperature': 0.7
    }
    
    try:
        response = session.post(
            AI_PROVIDERS["openai"]["endpoint"],
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"❌ Error calling OpenAI: {str(e)}"

def call_xai_grok(message: str, context: str = None, model: str = None) -> str:
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        return "❌ xAI API key not configured"
    
    model = model or AI_PROVIDERS["xai"]["default_model"]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    system_message = f"You are Fix It Fred, a helpful AI assistant with advanced problem-solving capabilities. {context if context else ''}"
    
    data = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': message}
        ],
        'max_tokens': 2000,
        'temperature': 0.7
    }
    
    try:
        response = session.post(
            AI_PROVIDERS["xai"]["endpoint"],
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"xAI Grok API error: {e}")
        return f"❌ Error calling xAI Grok: {str(e)}"

def call_google_gemini(message: str, context: str = None, model: str = None) -> str:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return "❌ Google API key not configured"
    
    model = model or AI_PROVIDERS["google"]["default_model"]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = f"You are Fix It Fred, a helpful AI assistant. {context if context else ''}\n\nUser: {message}"
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2000
        }
    }
    
    try:
        response = session.post(url, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logger.error(f"Google Gemini API error: {e}")
        return f"❌ Error calling Google Gemini: {str(e)}"

def call_ollama(message: str, context: str = None, model: str = None) -> str:
    model = model or AI_PROVIDERS["ollama"]["default_model"]
    
    url = "http://localhost:11434/api/chat"
    
    system_prompt = f"You are Fix It Fred, a helpful AI assistant. {context if context else ''}"
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "stream": False
    }
    
    try:
        response = session.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return f"❌ Error calling Ollama: {str(e)}"

# Universal API Endpoints

@app.get("/", response_class=HTMLResponse)
async def home():
    """Standalone web interface for Fix It Fred"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fix It Fred - Universal AI Assistant</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            .chat-container { height: 500px; overflow-y: auto; border: 1px solid #dee2e6; padding: 15px; margin-bottom: 15px; }
            .message { margin-bottom: 15px; }
            .user-message { text-align: right; }
            .ai-message { text-align: left; }
            .message-bubble { display: inline-block; padding: 10px 15px; border-radius: 18px; max-width: 70%; }
            .user-bubble { background-color: #007bff; color: white; }
            .ai-bubble { background-color: #f8f9fa; border: 1px solid #dee2e6; }
        </style>
    </head>
    <body>
        <div class="container-fluid py-4">
            <div class="row">
                <div class="col-12">
                    <h1 class="text-center mb-4">
                        <i class="fas fa-robot text-primary"></i> 
                        Fix It Fred - Universal AI Assistant
                    </h1>
                    <p class="text-center text-muted">Standalone AI assistant with multi-provider support</p>
                </div>
            </div>
            
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card shadow">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0"><i class="fas fa-comments"></i> Chat with Fix It Fred</h5>
                        </div>
                        <div class="card-body">
                            <div id="chatContainer" class="chat-container">
                                <div class="message ai-message">
                                    <div class="message-bubble ai-bubble">
                                        <strong>Fix It Fred:</strong> Hello! I'm your universal AI assistant. I can help with any questions or tasks. How can I assist you today?
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-3">
                                    <select id="providerSelect" class="form-select">
                                        <option value="anthropic">Anthropic Claude</option>
                                        <option value="openai">OpenAI GPT</option>
                                        <option value="xai">xAI Grok</option>
                                        <option value="google">Google Gemini</option>
                                        <option value="ollama">Local Ollama</option>
                                    </select>
                                </div>
                                <div class="col-md-9">
                                    <div class="input-group">
                                        <input type="text" id="messageInput" class="form-control" placeholder="Type your message..." onkeypress="if(event.key==='Enter') sendMessage()">
                                        <button class="btn btn-primary" onclick="sendMessage()">
                                            <i class="fas fa-paper-plane"></i> Send
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h6 class="mb-0"><i class="fas fa-plug"></i> Integration</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>API Endpoint:</strong><br>
                            <code>POST /api/universal/chat</code></p>
                            <p><strong>Documentation:</strong><br>
                            <a href="/docs" target="_blank">View API Docs</a></p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0"><i class="fas fa-cogs"></i> Providers</h6>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li><i class="fas fa-check text-success"></i> Anthropic Claude</li>
                                <li><i class="fas fa-check text-success"></i> OpenAI GPT</li>
                                <li><i class="fas fa-check text-success"></i> xAI Grok</li>
                                <li><i class="fas fa-check text-success"></i> Google Gemini</li>
                                <li><i class="fas fa-check text-success"></i> Local Ollama</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-warning text-dark">
                            <h6 class="mb-0"><i class="fas fa-code"></i> SDK</h6>
                        </div>
                        <div class="card-body">
                            <p>Easy integration with:</p>
                            <ul class="list-unstyled">
                                <li><i class="fab fa-js"></i> JavaScript</li>
                                <li><i class="fab fa-python"></i> Python</li>
                                <li><i class="fas fa-terminal"></i> cURL</li>
                                <li><i class="fas fa-plug"></i> Webhooks</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        async function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const providerSelect = document.getElementById('providerSelect');
            const chatContainer = document.getElementById('chatContainer');
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            chatContainer.innerHTML += `
                <div class="message user-message">
                    <div class="message-bubble user-bubble">
                        <strong>You:</strong> ${message}
                    </div>
                </div>
            `;
            
            messageInput.value = '';
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Show loading
            chatContainer.innerHTML += `
                <div class="message ai-message" id="loading">
                    <div class="message-bubble ai-bubble">
                        <strong>Fix It Fred:</strong> <i class="fas fa-spinner fa-spin"></i> Thinking...
                    </div>
                </div>
            `;
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            try {
                const response = await fetch('/api/universal/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        provider: providerSelect.value
                    })
                });
                
                const result = await response.json();
                
                // Remove loading
                document.getElementById('loading').remove();
                
                // Add AI response
                chatContainer.innerHTML += `
                    <div class="message ai-message">
                        <div class="message-bubble ai-bubble">
                            <strong>Fix It Fred (${providerSelect.value}):</strong> ${result.response}
                        </div>
                    </div>
                `;
                
            } catch (error) {
                document.getElementById('loading').remove();
                chatContainer.innerHTML += `
                    <div class="message ai-message">
                        <div class="message-bubble ai-bubble">
                            <strong>Fix It Fred:</strong> ❌ Error: ${error.message}
                        </div>
                    </div>
                `;
            }
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        </script>
    </body>
    </html>
    """)

@app.post("/api/universal/chat")
async def universal_chat(request: ChatMessage):
    """Universal chat endpoint for any application integration"""
    clean_old_cache()
    
    cache_key = get_cache_key(request.message, request.context, request.provider)
    cached_response = get_cached_response(cache_key)
    
    if cached_response:
        return {
            "success": True,
            "response": cached_response,
            "provider": request.provider,
            "model": request.model,
            "cached": True,
            "timestamp": datetime.now().isoformat()
        }
    
    # Route to appropriate AI provider
    provider_functions = {
        "anthropic": call_anthropic,
        "openai": call_openai,
        "xai": call_xai_grok,
        "google": call_google_gemini,
        "ollama": call_ollama
    }
    
    provider = request.provider or "anthropic"
    if provider not in provider_functions:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    try:
        response = provider_functions[provider](request.message, request.context, request.model)
        
        # Store conversation memory if conversation_id provided
        if request.conversation_id:
            conversation_memory[request.conversation_id].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat()
            })
            conversation_memory[request.conversation_id].append({
                "role": "assistant",
                "content": response,
                "provider": provider,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last MAX_CONVERSATION_LENGTH messages
            if len(conversation_memory[request.conversation_id]) > MAX_CONVERSATION_LENGTH:
                conversation_memory[request.conversation_id] = conversation_memory[request.conversation_id][-MAX_CONVERSATION_LENGTH:]
        
        cache_response(cache_key, response)
        
        return {
            "success": True,
            "response": response,
            "provider": provider,
            "model": request.model or AI_PROVIDERS[provider]["default_model"],
            "cached": False,
            "conversation_id": request.conversation_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in universal chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrations/register")
async def register_integration(config: IntegrationConfig):
    """Register a new application integration"""
    registered_integrations[config.app_id] = {
        "config": config.dict(),
        "registered_at": datetime.now().isoformat(),
        "usage_count": 0,
        "last_used": None
    }
    
    return {
        "success": True,
        "message": f"Integration registered for {config.app_name}",
        "app_id": config.app_id,
        "api_endpoint": f"/api/apps/{config.app_id}/chat"
    }

@app.post("/api/apps/{app_id}/chat")
async def app_specific_chat(app_id: str, request: ChatMessage):
    """App-specific chat endpoint with custom configurations"""
    if app_id not in registered_integrations:
        raise HTTPException(status_code=404, detail="Application not registered")
    
    integration = registered_integrations[app_id]
    config = integration["config"]
    
    # Apply app-specific configurations
    if request.provider not in config["allowed_providers"]:
        request.provider = config["default_provider"]
    
    # Add custom instructions to context
    if config["custom_instructions"]:
        request.context = f"{config['custom_instructions']}\n{request.context or ''}"
    
    # Update usage statistics
    integration["usage_count"] += 1
    integration["last_used"] = datetime.now().isoformat()
    
    # Set app_id for tracking
    request.app_id = app_id
    
    return await universal_chat(request)

@app.get("/api/providers")
async def get_providers():
    """Get all available AI providers"""
    return {
        "success": True,
        "providers": AI_PROVIDERS,
        "default_provider": "anthropic"
    }

@app.get("/api/integrations")
async def get_integrations():
    """Get all registered integrations"""
    return {
        "success": True,
        "integrations": registered_integrations,
        "total_integrations": len(registered_integrations)
    }

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    if conversation_id not in conversation_memory:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages": conversation_memory[conversation_id],
        "message_count": len(conversation_memory[conversation_id])
    }

@app.delete("/api/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    if conversation_id in conversation_memory:
        del conversation_memory[conversation_id]
    
    return {
        "success": True,
        "message": "Conversation cleared"
    }

@app.get("/api/stats")
async def get_stats():
    """Get usage statistics"""
    return {
        "success": True,
        "cache_stats": dict(cache_stats),
        "cache_size": len(response_cache),
        "active_conversations": len(conversation_memory),
        "registered_integrations": len(registered_integrations),
        "ai_providers": list(AI_PROVIDERS.keys()),
        "uptime": "Available",
        "version": "4.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fix It Fred Universal AI Assistant",
        "version": "4.0.0",
        "features": [
            "Multi-Provider AI Support",
            "Universal API Integration",
            "Conversation Memory",
            "App-Specific Configurations",
            "Standalone Web Interface",
            "SDK Support"
        ],
        "providers": list(AI_PROVIDERS.keys()),
        "timestamp": datetime.now().isoformat()
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🤖 Fix It Fred Universal AI Assistant starting up...")
    logger.info(f"📊 Available providers: {list(AI_PROVIDERS.keys())}")
    logger.info("🌐 Universal API ready for integrations")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    logger.info(f"🚀 Starting Fix It Fred Universal AI Assistant on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)