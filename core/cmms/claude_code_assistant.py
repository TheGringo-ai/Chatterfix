#!/usr/bin/env python3
"""
ChatterFix CMMS - Claude Code Assistant Integration
Provides development assistance, code analysis, and technical support
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import httpx
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix Claude Code Assistant", version="1.0.0")

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

class ClaudeCodeRequest(BaseModel):
    query: str
    context: Optional[str] = "general"
    project_context: Optional[Dict[str, Any]] = None
    code_snippet: Optional[str] = None

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"
    analysis_type: str = "review"  # review, debug, optimize, explain

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "claude-code-assistant"}

@app.post("/ask")
async def ask_claude_code(request: ClaudeCodeRequest):
    """Ask Claude Code assistant for development help"""
    try:
        # Prepare the system prompt for Claude Code context
        system_prompt = f"""You are Claude Code, Anthropic's assistant specifically designed for software development tasks. 
        You are helping with the ChatterFix CMMS project - an AI-powered maintenance management system.
        
        Current context: {request.context}
        
        ChatterFix CMMS features:
        - FastAPI microservices architecture
        - PostgreSQL database
        - AI integration (Claude, Grok, OpenAI)
        - Work orders, assets, parts management
        - Real-time collaboration features
        
        Provide concise, actionable development guidance focused on the ChatterFix CMMS codebase."""

        # Add code snippet context if provided
        if request.code_snippet:
            system_prompt += f"\n\nCode snippet for analysis:\n```python\n{request.code_snippet}\n```"

        # Prepare the request to Anthropic API
        messages = [
            {
                "role": "user",
                "content": request.query
            }
        ]

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": messages
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=data,
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            return {
                "response": result["content"][0]["text"],
                "context": request.context,
                "assistant": "Claude Code",
                "timestamp": "now"
            }
        else:
            logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
            return {
                "response": "I'm currently experiencing connectivity issues. Please try again or contact the development team.",
                "context": request.context,
                "assistant": "Claude Code (Fallback)",
                "error": True
            }

    except Exception as e:
        logger.error(f"Claude Code assistant error: {str(e)}")
        return {
            "response": f"I encountered an error while processing your request. As your Claude Code assistant, I recommend checking the logs for details: {str(e)[:100]}...",
            "context": request.context,
            "assistant": "Claude Code (Error Handler)",
            "error": True
        }

@app.post("/analyze-code")
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code with Claude Code assistant"""
    try:
        analysis_prompts = {
            "review": "Please review this code for best practices, potential issues, and improvements:",
            "debug": "Please help debug this code and identify potential issues:",
            "optimize": "Please suggest optimizations for this code:",
            "explain": "Please explain what this code does and how it works:"
        }

        prompt = analysis_prompts.get(request.analysis_type, analysis_prompts["review"])
        
        system_prompt = f"""You are Claude Code, providing {request.analysis_type} analysis for ChatterFix CMMS.
        Focus on: FastAPI best practices, database efficiency, security, maintainability.
        Language: {request.language}"""

        messages = [
            {
                "role": "user", 
                "content": f"{prompt}\n\n```{request.language}\n{request.code}\n```"
            }
        ]

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": messages
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=data,
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            return {
                "analysis": result["content"][0]["text"],
                "analysis_type": request.analysis_type,
                "language": request.language,
                "assistant": "Claude Code"
            }
        else:
            return {
                "analysis": f"Analysis temporarily unavailable. Status: {response.status_code}",
                "analysis_type": request.analysis_type,
                "error": True
            }

    except Exception as e:
        logger.error(f"Code analysis error: {str(e)}")
        return {
            "analysis": f"Analysis error: {str(e)[:100]}...",
            "analysis_type": request.analysis_type,
            "error": True
        }

@app.get("/development-tips")
async def get_development_tips():
    """Get ChatterFix development tips from Claude Code"""
    tips = {
        "fastapi_best_practices": [
            "Use Pydantic models for request/response validation",
            "Implement proper error handling with HTTPException",
            "Use dependency injection for database connections",
            "Add proper logging throughout the application"
        ],
        "database_optimization": [
            "Use async database operations with asyncpg",
            "Implement connection pooling",
            "Add database indexes for frequently queried fields",
            "Use transactions for multi-table operations"
        ],
        "ai_integration": [
            "Implement proper API key rotation",
            "Add rate limiting for AI API calls",
            "Cache AI responses when appropriate",
            "Implement fallback responses for AI service outages"
        ],
        "security": [
            "Use environment variables for secrets",
            "Implement proper CORS settings",
            "Add authentication middleware",
            "Validate all input data"
        ]
    }
    
    return {
        "tips": tips,
        "assistant": "Claude Code",
        "context": "ChatterFix CMMS Development"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8009))
    uvicorn.run(app, host="0.0.0.0", port=port)