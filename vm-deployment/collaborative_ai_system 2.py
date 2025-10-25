#!/usr/bin/env python3
"""
Collaborative AI System for ChatterFix CMMS
Integrates ChatGPT, Claude, and Grok for enhanced problem-solving
Includes RAG system for persistent memory and knowledge base
"""

import asyncio
import json
import sqlite3
import requests
import os
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib

@dataclass
class AIResponse:
    """Standardized AI response format"""
    ai_model: str
    response: str
    confidence: float
    reasoning: str
    timestamp: str
    context_used: List[str]

@dataclass
class MemoryItem:
    """RAG memory item structure"""
    id: str
    content: str
    category: str
    timestamp: str
    relevance_score: float
    source: str
    embedding: Optional[List[float]] = None

class RAGMemorySystem:
    """Retrieval-Augmented Generation Memory System"""
    
    def __init__(self, db_path: str = "./data/ai_memory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the RAG memory database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Memory storage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                relevance_score REAL DEFAULT 1.0,
                source TEXT NOT NULL,
                embedding_hash TEXT,
                metadata TEXT
            )
        """)
        
        # Conversation history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ai_model TEXT,
                timestamp TEXT NOT NULL,
                context_ids TEXT
            )
        """)
        
        # Knowledge base table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                created_date TEXT NOT NULL,
                updated_date TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_memory(self, content: str, category: str, source: str, metadata: Dict = None) -> str:
        """Store a memory item in the RAG system"""
        memory_id = hashlib.md5(f"{content}{datetime.datetime.now()}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ai_memory (id, content, category, timestamp, source, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            memory_id,
            content,
            category,
            datetime.datetime.now().isoformat(),
            source,
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
        return memory_id
    
    def retrieve_relevant_memories(self, query: str, category: str = None, limit: int = 5) -> List[MemoryItem]:
        """Retrieve relevant memories based on query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build the SQL query based on whether category is specified
        if category is not None and category != "":
            # Category-based search
            sql = "SELECT * FROM ai_memory WHERE category = ? AND LOWER(content) LIKE ? ORDER BY relevance_score DESC LIMIT ?"
            search_term = f"%{query.lower()}%"
            params = [category, search_term, limit]
        else:
            # General search
            sql = "SELECT * FROM ai_memory WHERE LOWER(content) LIKE ? ORDER BY relevance_score DESC LIMIT ?"
            search_term = f"%{query.lower()}%"
            params = [search_term, limit]
        
        try:
            cursor.execute(sql, params)
            results = cursor.fetchall()
        except Exception as e:
            print(f"SQL Error: {e}")
            print(f"SQL: {sql}")
            print(f"Params: {params}")
            raise
        finally:
            conn.close()
        
        memories = []
        for row in results:
            memories.append(MemoryItem(
                id=row[0],
                content=row[1],
                category=row[2],
                timestamp=row[3],
                relevance_score=row[4],
                source=row[5]
            ))
        
        return memories

class CollaborativeAISystem:
    """Multi-AI collaboration system with RAG memory"""
    
    def __init__(self):
        self.memory = RAGMemorySystem()
        self.ai_models = {
            'chatgpt': self.call_chatgpt,
            'grok': self.call_grok,
            'claude': self.call_claude_via_api
        }
        
        # Load API keys from environment
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.grok_api_key = os.getenv('GROK_API_KEY', os.getenv('XAI_API_KEY'))
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
    
    async def call_chatgpt(self, prompt: str, context: List[str] = None) -> AIResponse:
        """Call ChatGPT API with context"""
        if not self.openai_api_key:
            return AIResponse("chatgpt", "ChatGPT API key not configured", 0.0, "No API key", datetime.datetime.now().isoformat(), [])
        
        # Enhanced prompt with context
        enhanced_prompt = self.build_contextual_prompt(prompt, context, "ChatGPT")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a CMMS and maintenance expert AI assistant working collaboratively with other AI systems."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", 
                                   headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Store interaction in memory
                self.memory.store_memory(
                    f"ChatGPT response to: {prompt[:100]}... Response: {content[:200]}...",
                    "chatgpt_interaction",
                    "chatgpt"
                )
                
                return AIResponse("chatgpt", content, 0.9, "OpenAI API response", datetime.datetime.now().isoformat(), context or [])
            else:
                return AIResponse("chatgpt", f"API error: {response.status_code}", 0.0, "API failure", datetime.datetime.now().isoformat(), [])
                
        except Exception as e:
            return AIResponse("chatgpt", f"Error: {str(e)}", 0.0, "Exception occurred", datetime.datetime.now().isoformat(), [])
    
    async def call_grok(self, prompt: str, context: List[str] = None) -> AIResponse:
        """Call Grok AI API with context"""
        if not self.grok_api_key:
            return AIResponse("grok", "Grok API key not configured", 0.0, "No API key", datetime.datetime.now().isoformat(), [])
        
        enhanced_prompt = self.build_contextual_prompt(prompt, context, "Grok")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.grok_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messages": [
                    {"role": "system", "content": "You are Grok, an AI with a rebellious streak and wit, working on CMMS and maintenance systems. Be helpful but maintain your unique personality."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0.7
            }
            
            response = requests.post("https://api.x.ai/v1/chat/completions", 
                                   headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Store interaction in memory
                self.memory.store_memory(
                    f"Grok response to: {prompt[:100]}... Response: {content[:200]}...",
                    "grok_interaction",
                    "grok"
                )
                
                return AIResponse("grok", content, 0.85, "Grok API response", datetime.datetime.now().isoformat(), context or [])
            else:
                return AIResponse("grok", f"API error: {response.status_code}", 0.0, "API failure", datetime.datetime.now().isoformat(), [])
                
        except Exception as e:
            return AIResponse("grok", f"Error: {str(e)}", 0.0, "Exception occurred", datetime.datetime.now().isoformat(), [])
    
    async def call_claude_via_api(self, prompt: str, context: List[str] = None) -> AIResponse:
        """Call Claude API (if available) with context"""
        # For now, return a placeholder since we're already running in Claude
        enhanced_prompt = self.build_contextual_prompt(prompt, context, "Claude")
        
        # Store the interaction
        self.memory.store_memory(
            f"Claude request: {prompt[:100]}...",
            "claude_interaction",
            "claude"
        )
        
        return AIResponse("claude", "Claude integration active (running locally)", 0.95, "Local Claude instance", datetime.datetime.now().isoformat(), context or [])
    
    def build_contextual_prompt(self, prompt: str, context: List[str], ai_model: str) -> str:
        """Build enhanced prompt with RAG context"""
        # Retrieve relevant memories
        relevant_memories = self.memory.retrieve_relevant_memories(prompt, limit=3)
        
        context_text = ""
        if relevant_memories:
            context_text = "\n\nRelevant context from memory:\n"
            for memory in relevant_memories:
                context_text += f"- {memory.content[:200]}...\n"
        
        if context:
            context_text += "\n\nAdditional context:\n" + "\n".join(context)
        
        enhanced_prompt = f"""
CMMS AI Collaboration Request for {ai_model}:

Query: {prompt}

{context_text}

Please provide a comprehensive response that:
1. Addresses the specific query
2. Incorporates relevant context
3. Suggests collaborative approaches with other AI systems
4. Identifies any knowledge gaps that need filling
"""
        
        return enhanced_prompt
    
    async def collaborative_query(self, prompt: str, models: List[str] = None) -> Dict[str, AIResponse]:
        """Query multiple AI models collaboratively"""
        if models is None:
            models = ['chatgpt', 'grok']  # Claude is already running locally
        
        # Get context from memory
        context = [mem.content for mem in self.memory.retrieve_relevant_memories(prompt, limit=2)]
        
        responses = {}
        tasks = []
        
        for model in models:
            if model in self.ai_models:
                task = self.ai_models[model](prompt, context)
                tasks.append((model, task))
        
        # Execute all queries concurrently
        for model, task in tasks:
            try:
                response = await task
                responses[model] = response
            except Exception as e:
                responses[model] = AIResponse(model, f"Error: {str(e)}", 0.0, "Exception", datetime.datetime.now().isoformat(), [])
        
        # Store the collaborative session
        session_summary = f"Collaborative query: {prompt[:100]}... Models: {', '.join(models)}"
        self.memory.store_memory(session_summary, "collaborative_session", "system")
        
        return responses
    
    def synthesize_responses(self, responses: Dict[str, AIResponse]) -> str:
        """Synthesize multiple AI responses into a comprehensive answer"""
        if not responses:
            return "No responses received from AI models."
        
        synthesis = "🤖 **Collaborative AI Analysis:**\n\n"
        
        for model, response in responses.items():
            if response.confidence > 0:
                synthesis += f"### {model.upper()} Response (Confidence: {response.confidence:.1%})\n"
                synthesis += f"{response.response}\n\n"
        
        # Add consensus or conflicting viewpoints analysis
        if len([r for r in responses.values() if r.confidence > 0.5]) > 1:
            synthesis += "### Collaborative Insights:\n"
            synthesis += "Multiple AI systems have provided input. Key themes:\n"
            synthesis += "- Cross-validated recommendations increase confidence\n"
            synthesis += "- Diverse AI perspectives provide comprehensive coverage\n"
            synthesis += "- Collaborative approach ensures robust solutions\n\n"
        
        # Store synthesis
        self.memory.store_memory(synthesis, "synthesis", "collaborative_system")
        
        return synthesis

class CMMSKnowledgeBase:
    """Specialized knowledge base for CMMS operations"""
    
    def __init__(self, memory_system: RAGMemorySystem):
        self.memory = memory_system
        self.init_cmms_knowledge()
    
    def init_cmms_knowledge(self):
        """Initialize CMMS-specific knowledge base"""
        knowledge_items = [
            {
                "title": "Preventive Maintenance Best Practices",
                "content": "Preventive maintenance should be scheduled based on manufacturer recommendations, usage patterns, and environmental conditions. Key practices include regular inspections, lubrication, filter changes, and calibration checks.",
                "category": "maintenance_procedures",
                "tags": "preventive,scheduling,best_practices"
            },
            {
                "title": "Work Order Priority Classification",
                "content": "Critical: Safety hazard or production stoppage. High: Significant impact on operations. Medium: Moderate impact, can wait 24-48 hours. Low: Minimal impact, routine maintenance.",
                "category": "work_order_management",
                "tags": "priority,classification,urgency"
            },
            {
                "title": "Inventory Optimization Strategies",
                "content": "Maintain 1.5-2x safety stock for critical parts. Use ABC analysis for inventory categorization. Implement just-in-time ordering for non-critical items. Track usage patterns for accurate forecasting.",
                "category": "inventory_management",
                "tags": "optimization,safety_stock,abc_analysis"
            },
            {
                "title": "Asset Performance Monitoring",
                "content": "Key metrics include MTBF (Mean Time Between Failures), MTTR (Mean Time To Repair), Overall Equipment Effectiveness (OEE), and maintenance cost per asset. Monitor trends to identify deteriorating performance.",
                "category": "asset_management",
                "tags": "kpi,performance,monitoring,metrics"
            },
            {
                "title": "Technician Skill Matrix",
                "content": "Maintain skills inventory including certifications, specializations, and experience levels. Match technician skills to work order requirements. Plan training for skill gaps and cross-training opportunities.",
                "category": "resource_management",
                "tags": "skills,training,resource_allocation"
            }
        ]
        
        for item in knowledge_items:
            self.memory.store_memory(
                f"Title: {item['title']}\nContent: {item['content']}\nTags: {item['tags']}",
                item['category'],
                "cmms_knowledge_base",
                {"title": item['title'], "tags": item['tags']}
            )

# Initialize the collaborative AI system
collaborative_ai = CollaborativeAISystem()
cmms_knowledge = CMMSKnowledgeBase(collaborative_ai.memory)

async def process_collaborative_query(query: str, models: List[str] = None) -> str:
    """Process a query using collaborative AI system"""
    responses = await collaborative_ai.collaborative_query(query, models)
    return collaborative_ai.synthesize_responses(responses)

if __name__ == "__main__":
    # Test the system
    async def test_system():
        query = "How should I prioritize maintenance work orders and optimize technician assignments?"
        result = await process_collaborative_query(query, ['chatgpt', 'grok'])
        print(result)
    
    asyncio.run(test_system())