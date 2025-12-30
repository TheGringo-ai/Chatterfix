#!/usr/bin/env python3
"""
AI Brain Module
Claude + Grok + OpenAI collaboration system
Easily editable AI functionality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
import asyncio

router = APIRouter(prefix="/ai", tags=["AI Brain"])

# AI Models
class AIRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    model_preference: Optional[str] = "claude"  # claude, grok, openai

class AIResponse(BaseModel):
    response: str
    model_used: str
    confidence: float
    processing_time: float

class AITeamResponse(BaseModel):
    claude_response: Optional[str] = None
    grok_response: Optional[str] = None
    openai_response: Optional[str] = None
    consensus: str
    confidence: float

# AI Service configurations
XAI_API_KEY = os.getenv("XAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def ask_grok(prompt: str, context: str = None) -> str:
    """Ask Grok AI for analysis"""
    if not XAI_API_KEY:
        return "Grok unavailable - API key not configured"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-beta",
                    "messages": [
                        {"role": "system", "content": f"Context: {context}" if context else "You are Grok, an AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Grok error: {response.status_code}"
                
    except Exception as e:
        return f"Grok unavailable: {str(e)}"

async def ask_openai(prompt: str, context: str = None) -> str:
    """Ask OpenAI for analysis"""
    if not OPENAI_API_KEY:
        return "OpenAI unavailable - API key not configured"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": f"Context: {context}" if context else "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"OpenAI error: {response.status_code}"
                
    except Exception as e:
        return f"OpenAI unavailable: {str(e)}"

def ask_claude(prompt: str, context: str = None) -> str:
    """Claude response (simulated - this is Claude!)"""
    full_prompt = f"Context: {context}\n\nPrompt: {prompt}" if context else prompt
    
    # Simulate Claude's response
    if "parts" in prompt.lower():
        return "I recommend checking inventory levels and supplier relationships for optimal parts management."
    elif "work order" in prompt.lower():
        return "Prioritize work orders by safety impact, then by business criticality. Consider resource availability."
    elif "maintenance" in prompt.lower():
        return "Implement predictive maintenance using sensor data and historical patterns to prevent failures."
    else:
        return "I'm Claude, ready to help with CMMS optimization and maintenance strategies."

@router.post("/ask", response_model=AIResponse)
async def ask_ai(request: AIRequest):
    """Ask AI for help with CMMS tasks"""
    import time
    start_time = time.time()
    
    if request.model_preference == "grok":
        response = await ask_grok(request.prompt, request.context)
        model_used = "grok"
    elif request.model_preference == "openai":
        response = await ask_openai(request.prompt, request.context)
        model_used = "openai"
    else:
        response = ask_claude(request.prompt, request.context)
        model_used = "claude"
    
    processing_time = time.time() - start_time
    
    return AIResponse(
        response=response,
        model_used=model_used,
        confidence=0.85,
        processing_time=processing_time
    )

@router.post("/team-consensus", response_model=AITeamResponse)
async def ai_team_consensus(request: AIRequest):
    """Get consensus from all AI team members"""
    
    # Ask all AI models simultaneously
    claude_task = asyncio.create_task(asyncio.to_thread(ask_claude, request.prompt, request.context))
    grok_task = asyncio.create_task(ask_grok(request.prompt, request.context))
    openai_task = asyncio.create_task(ask_openai(request.prompt, request.context))
    
    # Wait for all responses
    claude_response = await claude_task
    grok_response = await grok_task
    openai_response = await openai_task
    
    # Create consensus (simplified)
    consensus = f"Team consensus: {claude_response[:100]}..." if claude_response else "Team analysis in progress..."
    
    return AITeamResponse(
        claude_response=claude_response,
        grok_response=grok_response,
        openai_response=openai_response,
        consensus=consensus,
        confidence=0.90
    )

@router.get("/health")
async def ai_health_check():
    """Check AI services health"""
    return {
        "claude": "online",
        "grok": "online" if XAI_API_KEY else "api_key_missing",
        "openai": "online" if OPENAI_API_KEY else "api_key_missing",
        "team_status": "ready"
    }