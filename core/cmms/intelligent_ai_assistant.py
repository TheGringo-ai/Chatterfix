#!/usr/bin/env python3
"""
ChatterFix CMMS - Intelligent AI Assistant Service
Role-based AI with memory, learning, and comprehensive CMMS assistance
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
import sqlite3
import json
import os
import logging
import httpx
import uuid
import asyncio
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix Intelligent AI Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_FILE = os.getenv("DATABASE_FILE", "chatterfix_enterprise_v3.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# User Role Definitions
class UserRole(str, Enum):
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    TECHNICIAN = "technician"
    BUYER = "buyer"
    OPERATOR = "operator"
    ADMIN = "admin"

# Pydantic Models
class AIAssistantRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    user_role: Optional[UserRole] = UserRole.TECHNICIAN
    context: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None
    current_page: Optional[str] = None

class MemoryEntry(BaseModel):
    user_id: str
    interaction_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class LearningEntry(BaseModel):
    user_id: str
    pattern: str
    preference: str
    confidence: float = 0.5

# Database initialization for AI assistant
def init_ai_database():
    """Initialize AI assistant database tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # User interactions and memory
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_user_memory (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        interaction_type TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata TEXT DEFAULT '{}',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        relevance_score REAL DEFAULT 1.0
    )
    """)
    
    # Learning patterns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_learning_patterns (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        pattern_type TEXT NOT NULL,
        pattern_data TEXT NOT NULL,
        confidence REAL DEFAULT 0.5,
        usage_count INTEGER DEFAULT 1,
        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Conversation sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        context TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active BOOLEAN DEFAULT TRUE
    )
    """)
    
    # AI insights and analytics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_insights (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        insight_type TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_ai_database()

# Role-based AI configurations
ROLE_CONFIGURATIONS = {
    UserRole.MANAGER: {
        "name": "Executive Assistant",
        "personality": "Professional, analytical, strategic thinker focused on KPIs and team performance",
        "expertise": ["strategic planning", "team management", "budget analysis", "performance metrics", "reporting"],
        "default_actions": ["schedule optimization", "resource allocation", "cost analysis", "team productivity"],
        "ai_model_preference": "claude",  # Best for strategic thinking
    },
    UserRole.SUPERVISOR: {
        "name": "Operations Coordinator",
        "personality": "Organized, efficient, detail-oriented with focus on workflow optimization",
        "expertise": ["workflow management", "task coordination", "quality control", "team scheduling", "compliance"],
        "default_actions": ["work order prioritization", "schedule management", "quality assurance", "team coordination"],
        "ai_model_preference": "gpt4",  # Good for coordination tasks
    },
    UserRole.TECHNICIAN: {
        "name": "Technical Expert",
        "personality": "Practical, hands-on, solution-focused with deep technical knowledge",
        "expertise": ["equipment maintenance", "troubleshooting", "repair procedures", "safety protocols", "technical documentation"],
        "default_actions": ["diagnostic assistance", "procedure lookup", "safety checks", "part identification"],
        "ai_model_preference": "grok",  # Best for technical problem-solving
    },
    UserRole.BUYER: {
        "name": "Procurement Specialist",
        "personality": "Cost-conscious, vendor-savvy, detail-oriented with focus on value optimization",
        "expertise": ["vendor management", "cost optimization", "inventory planning", "contract negotiation", "supplier relationships"],
        "default_actions": ["vendor comparison", "cost analysis", "inventory forecasting", "purchase planning"],
        "ai_model_preference": "claude",  # Good for analysis and planning
    },
    UserRole.OPERATOR: {
        "name": "Operations Guide",
        "personality": "Safety-first, process-oriented, clear communicator focused on operational excellence",
        "expertise": ["operational procedures", "safety protocols", "equipment operation", "process optimization", "quality standards"],
        "default_actions": ["procedure guidance", "safety reminders", "operational tips", "process optimization"],
        "ai_model_preference": "gpt4",  # Good for clear instructions
    },
    UserRole.ADMIN: {
        "name": "System Administrator",
        "personality": "Technical, systematic, security-focused with broad system knowledge",
        "expertise": ["system administration", "user management", "security protocols", "data analysis", "system optimization"],
        "default_actions": ["system health checks", "user support", "security recommendations", "performance analysis"],
        "ai_model_preference": "claude",  # Best for comprehensive analysis
    }
}

async def get_user_memory(user_id: str, limit: int = 10) -> List[Dict]:
    """Retrieve user's interaction memory"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT interaction_type, content, metadata, timestamp, relevance_score
    FROM ai_user_memory 
    WHERE user_id = ? 
    ORDER BY relevance_score DESC, timestamp DESC 
    LIMIT ?
    """, (user_id, limit))
    
    memory = []
    for row in cursor.fetchall():
        memory.append({
            "type": row[0],
            "content": row[1],
            "metadata": json.loads(row[2] or "{}"),
            "timestamp": row[3],
            "relevance": row[4]
        })
    
    conn.close()
    return memory

async def store_interaction(user_id: str, interaction_type: str, content: str, metadata: Dict = None):
    """Store user interaction for memory and learning"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    interaction_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO ai_user_memory (id, user_id, interaction_type, content, metadata)
    VALUES (?, ?, ?, ?, ?)
    """, (interaction_id, user_id, interaction_type, content, json.dumps(metadata or {})))
    
    conn.commit()
    conn.close()

async def get_user_patterns(user_id: str) -> List[Dict]:
    """Get learned patterns for user"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT pattern_type, pattern_data, confidence, usage_count
    FROM ai_learning_patterns 
    WHERE user_id = ? AND confidence > 0.3
    ORDER BY confidence DESC, usage_count DESC
    """, (user_id,))
    
    patterns = []
    for row in cursor.fetchall():
        patterns.append({
            "type": row[0],
            "data": json.loads(row[1]),
            "confidence": row[2],
            "usage": row[3]
        })
    
    conn.close()
    return patterns

async def generate_role_based_response(request: AIAssistantRequest) -> Dict[str, Any]:
    """Generate AI response based on user role and context"""
    
    # Get role configuration
    role_config = ROLE_CONFIGURATIONS.get(request.user_role, ROLE_CONFIGURATIONS[UserRole.TECHNICIAN])
    
    # Retrieve user memory and patterns
    user_memory = await get_user_memory(request.user_id or "anonymous") if request.user_id else []
    user_patterns = await get_user_patterns(request.user_id or "anonymous") if request.user_id else []
    
    # Build context-aware prompt
    system_prompt = f"""You are {role_config['name']}, an AI assistant for ChatterFix CMMS.
    
    PERSONALITY: {role_config['personality']}
    
    EXPERTISE: {', '.join(role_config['expertise'])}
    
    USER ROLE: {request.user_role.value.title()}
    CURRENT PAGE: {request.current_page or 'dashboard'}
    
    RECENT INTERACTIONS:
    {chr(10).join([f"- {mem['type']}: {mem['content'][:100]}..." for mem in user_memory[:3]])}
    
    LEARNED PREFERENCES:
    {chr(10).join([f"- {pat['type']}: {pat['data']}" for pat in user_patterns[:3]])}
    
    CONTEXT: {json.dumps(request.context, indent=2)}
    
    Provide helpful, role-appropriate assistance for ChatterFix CMMS. Be concise but comprehensive.
    Focus on practical solutions and actionable insights."""
    
    # Call appropriate AI service based on role preference
    try:
        ai_model = role_config['ai_model_preference']
        
        if ai_model == "claude" and ANTHROPIC_API_KEY:
            response = await call_claude_api(system_prompt, request.message)
        elif ai_model == "grok" and XAI_API_KEY:
            response = await call_grok_api(system_prompt, request.message)
        else:  # Default to GPT-4
            response = await call_openai_api(system_prompt, request.message)
            
        # Store interaction for learning
        if request.user_id:
            await store_interaction(
                request.user_id,
                f"{request.user_role.value}_query",
                request.message,
                {"page": request.current_page, "ai_model": ai_model}
            )
        
        return {
            "response": response,
            "assistant_name": role_config['name'],
            "role": request.user_role.value,
            "ai_model": ai_model,
            "suggested_actions": role_config['default_actions'][:3],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI response generation error: {str(e)}")
        return {
            "response": f"I'm experiencing some technical difficulties right now. As your {role_config['name']}, I recommend checking the system status or trying again in a moment.",
            "assistant_name": role_config['name'],
            "role": request.user_role.value,
            "error": True
        }

async def call_claude_api(system_prompt: str, message: str) -> str:
    """Call Anthropic Claude API"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": [{"role": "user", "content": message}]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["content"][0]["text"]
    else:
        return "I'm having trouble accessing my advanced reasoning capabilities right now."

async def call_grok_api(system_prompt: str, message: str) -> str:
    """Call xAI Grok API"""
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "model": "grok-beta",
        "stream": False,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return "My technical problem-solving capabilities are temporarily unavailable."

async def call_openai_api(system_prompt: str, message: str) -> str:
    """Call OpenAI GPT-4 API"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4-turbo-preview",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "max_tokens": 1500,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return "I'm currently unable to provide my full assistance capabilities."

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "intelligent-ai-assistant",
        "roles_supported": list(UserRole),
        "ai_models": ["claude", "grok", "gpt4"]
    }

@app.post("/ask")
async def ask_ai_assistant(request: AIAssistantRequest):
    """Ask the intelligent AI assistant"""
    return await generate_role_based_response(request)

@app.get("/user/{user_id}/memory")
async def get_user_memory_endpoint(user_id: str, limit: int = 20):
    """Get user's interaction memory"""
    memory = await get_user_memory(user_id, limit)
    return {"user_id": user_id, "memory": memory, "count": len(memory)}

@app.get("/user/{user_id}/patterns")
async def get_user_patterns_endpoint(user_id: str):
    """Get user's learned patterns"""
    patterns = await get_user_patterns(user_id)
    return {"user_id": user_id, "patterns": patterns, "count": len(patterns)}

@app.get("/roles")
async def get_role_configurations():
    """Get all role configurations"""
    return {
        "roles": {
            role.value: {
                "name": config["name"],
                "expertise": config["expertise"],
                "default_actions": config["default_actions"]
            }
            for role, config in ROLE_CONFIGURATIONS.items()
        }
    }

@app.post("/insights/generate")
async def generate_insights(user_id: str, background_tasks: BackgroundTasks):
    """Generate AI insights for user"""
    background_tasks.add_task(generate_user_insights, user_id)
    return {"message": "Insights generation started", "user_id": user_id}

async def generate_user_insights(user_id: str):
    """Background task to generate insights"""
    # This would analyze user patterns and generate insights
    # Implementation would include data analysis and insight generation
    pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port)