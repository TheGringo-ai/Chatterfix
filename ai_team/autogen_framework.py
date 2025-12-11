"""
Autogen Framework for Multi-Model AI Team Collaboration
Coordinates Claude, ChatGPT, Gemini, Grok, and other AI models
"""
import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, AsyncGenerator, Any
from enum import Enum

logger = logging.getLogger(__name__)

class ModelType(Enum):
    CLAUDE = "claude"
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    GROK = "grok"
    PERPLEXITY = "perplexity"
    LOCAL_LLM = "local_llm"

@dataclass
class AgentConfig:
    name: str
    model_type: ModelType
    role: str
    capabilities: List[str]
    model_name: Optional[str] = None  # Specific model name (e.g., "grok-3", "grok-code-fast-1")
    max_tokens: int = 4000
    temperature: float = 0.7
    enabled: bool = True

@dataclass
class CollaborationResult:
    task_id: str
    success: bool
    final_answer: str
    agent_responses: List[Dict[str, Any]]
    collaboration_log: List[str]
    total_time: float
    confidence_score: float

class AIAgent(ABC):
    """Abstract base class for AI agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.conversation_history = []
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate a response from this AI agent"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this agent is available"""
        pass

class ClaudeAgent(AIAgent):
    """Claude AI Agent using Anthropic API"""
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        try:
            import os
            import anthropic
            
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return f"[{self.config.name}] Error: ANTHROPIC_API_KEY not configured"
            
            client = anthropic.AsyncAnthropic(api_key=api_key)
            
            full_prompt = f"Context: {context}\n\nTask: {prompt}\n\nAs Claude AI, provide a thoughtful and analytical response:"
            
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=min(self.config.max_tokens, 4000),
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            content = response.content[0].text
            ai_response = f"[{self.config.name}] {content}"
            self.conversation_history.append({"prompt": prompt, "response": ai_response})
            return ai_response
            
        except Exception as e:
            logger.error(f"Claude agent error: {e}")
            return f"[{self.config.name}] Error: {str(e)}"
    
    async def is_available(self) -> bool:
        import os
        return bool(os.getenv('ANTHROPIC_API_KEY'))

class ChatGPTAgent(AIAgent):
    """ChatGPT AI Agent using OpenAI API"""
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        try:
            import os
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return f"[{self.config.name}] Error: OPENAI_API_KEY not configured"
            
            client = openai.AsyncOpenAI(api_key=api_key)
            
            messages = [
                {"role": "system", "content": "You are ChatGPT, a helpful AI assistant. Be comprehensive and practical."},
                {"role": "user", "content": f"Context: {context}\n\nTask: {prompt}"}
            ]
            
            response = await client.chat.completions.create(
                model="gpt-4o",  # Use latest GPT model
                messages=messages,
                max_tokens=min(self.config.max_tokens, 4000),
                temperature=self.config.temperature
            )
            
            content = response.choices[0].message.content
            ai_response = f"[{self.config.name}] {content}"
            self.conversation_history.append({"prompt": prompt, "response": ai_response})
            return ai_response
            
        except Exception as e:
            logger.error(f"ChatGPT agent error: {e}")
            return f"[{self.config.name}] Error: {str(e)}"
    
    async def is_available(self) -> bool:
        import os
        return bool(os.getenv('OPENAI_API_KEY'))

class GeminiAgent(AIAgent):
    """Gemini AI Agent using Google AI API"""
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        try:
            import os
            import google.generativeai as genai
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                return f"[{self.config.name}] Error: GEMINI_API_KEY not configured"
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            full_prompt = f"Context: {context}\n\nTask: {prompt}\n\nAs Gemini AI, provide an innovative and creative response:"
            
            response = await model.generate_content_async(full_prompt)
            content = response.text
            ai_response = f"[{self.config.name}] {content}"
            self.conversation_history.append({"prompt": prompt, "response": ai_response})
            return ai_response
            
        except Exception as e:
            logger.error(f"Gemini agent error: {e}")
            return f"[{self.config.name}] Error: {str(e)}"
    
    async def is_available(self) -> bool:
        import os
        return bool(os.getenv('GEMINI_API_KEY'))

class GrokAgent(AIAgent):
    """Grok AI Agent using xAI API"""
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        try:
            import os
            import requests
            
            api_key = os.getenv('XAI_API_KEY')
            if not api_key:
                return f"[{self.config.name}] Error: XAI_API_KEY not configured"
            
            # Use the specific model name from config, default to grok-3
            model_name = self.config.model_name or "grok-3"
            
            url = 'https://api.x.ai/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Customize system prompt based on the model
            if "code" in model_name.lower():
                system_prompt = "You are a coding specialist AI. Focus on clean, efficient code solutions."
            else:
                system_prompt = "You are a reasoning AI. Provide thoughtful analysis and insights."
            
            data = {
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Context: {context}\n\nTask: {prompt}"}
                ],
                'model': model_name,
                'stream': False,
                'temperature': self.config.temperature,
                'max_tokens': min(self.config.max_tokens, 4000)
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                ai_response = f"[{self.config.name}] {content}"
                self.conversation_history.append({"prompt": prompt, "response": ai_response})
                return ai_response
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(f"Grok agent error: {error_msg}")
                return f"[{self.config.name}] Error: {error_msg}"
            
        except Exception as e:
            logger.error(f"Grok agent error: {e}")
            return f"[{self.config.name}] Error: {str(e)}"
    
    async def is_available(self) -> bool:
        import os
        return bool(os.getenv('XAI_API_KEY'))

class AutogenOrchestrator:
    """Orchestrates multi-agent collaboration using autogen principles"""
    
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.active_tasks: Dict[str, Dict] = {}
        
    def register_agent(self, agent: AIAgent):
        """Register an AI agent with the orchestrator"""
        self.agents[agent.config.name] = agent
        logger.info(f"Registered agent: {agent.config.name} ({agent.config.model_type.value})")
    
    def setup_default_agents(self):
        """Setup default AI team with multiple models"""
        agents_config = [
            AgentConfig("claude-analyst", ModelType.CLAUDE, "Lead Analyst", ["analysis", "reasoning", "planning"]),
            AgentConfig("chatgpt-coder", ModelType.CHATGPT, "Senior Developer", ["coding", "debugging", "architecture"]),
            AgentConfig("gemini-creative", ModelType.GEMINI, "Creative Director", ["creativity", "design", "innovation"]),
            AgentConfig("grok-coder", ModelType.GROK, "Speed Coder", ["fast-coding", "optimization", "debugging"], "grok-code-fast-1"),
            AgentConfig("grok-reasoner", ModelType.GROK, "Strategic Thinker", ["reasoning", "analysis", "strategy"], "grok-3"),
        ]
        
        for config in agents_config:
            if config.model_type == ModelType.CLAUDE:
                agent = ClaudeAgent(config)
            elif config.model_type == ModelType.CHATGPT:
                agent = ChatGPTAgent(config)
            elif config.model_type == ModelType.GEMINI:
                agent = GeminiAgent(config)
            elif config.model_type == ModelType.GROK:
                agent = GrokAgent(config)
            else:
                continue
                
            self.register_agent(agent)
    
    async def execute_collaborative_task(self, 
                                       task_id: str,
                                       prompt: str, 
                                       context: str = "",
                                       required_agents: Optional[List[str]] = None,
                                       max_iterations: int = 3) -> CollaborationResult:
        """Execute a task using multiple AI agents in collaboration"""
        
        start_time = time.time()
        collaboration_log = []
        agent_responses = []
        
        # Determine which agents to use
        if required_agents:
            active_agents = [self.agents[name] for name in required_agents if name in self.agents]
        else:
            active_agents = [agent for agent in self.agents.values() if agent.config.enabled]
        
        collaboration_log.append(f"Starting collaboration with {len(active_agents)} agents")
        
        # Phase 1: Initial responses from all agents
        initial_responses = []
        for agent in active_agents:
            if await agent.is_available():
                response = await agent.generate_response(prompt, context)
                initial_responses.append({
                    "agent": agent.config.name,
                    "role": agent.config.role,
                    "response": response,
                    "model_type": agent.config.model_type.value
                })
                collaboration_log.append(f"{agent.config.name}: Generated initial response")
        
        agent_responses.extend(initial_responses)
        
        # Phase 2: Cross-agent review and refinement
        if len(initial_responses) > 1 and max_iterations > 1:
            collaboration_log.append("Starting cross-agent collaboration phase")
            
            # Create summary of all responses for review
            summary = "Previous responses from the team:\n"
            for resp in initial_responses:
                summary += f"\n{resp['agent']} ({resp['role']}): {resp['response'][:200]}...\n"
            
            refinement_prompt = f"Review the team responses and provide your refined analysis:\n{summary}\n\nOriginal task: {prompt}"
            
            refined_responses = []
            for agent in active_agents:
                if await agent.is_available():
                    response = await agent.generate_response(refinement_prompt, context)
                    refined_responses.append({
                        "agent": agent.config.name,
                        "role": agent.config.role,
                        "response": response,
                        "model_type": agent.config.model_type.value,
                        "phase": "refinement"
                    })
                    collaboration_log.append(f"{agent.config.name}: Provided refinement")
            
            agent_responses.extend(refined_responses)
        
        # Phase 3: Synthesis and final answer
        if len(agent_responses) > 0:
            synthesis_prompt = f"""
            Synthesize the following AI team responses into a final comprehensive answer:

            Task: {prompt}
            Context: {context}

            Team Responses:
            {chr(10).join([f"{resp['agent']}: {resp['response']}" for resp in agent_responses[-len(active_agents):]])}

            Provide a final synthesized answer that incorporates the best insights from the team:
            """
            
            # Use the lead agent (Claude) for synthesis
            claude_agent = next((agent for agent in active_agents if agent.config.model_type == ModelType.CLAUDE), active_agents[0])
            final_answer = await claude_agent.generate_response(synthesis_prompt, context)
            collaboration_log.append("Generated synthesized final answer")
        else:
            final_answer = "No responses generated from AI team"
        
        total_time = time.time() - start_time
        confidence_score = min(0.95, len(agent_responses) * 0.2)  # Simple confidence calculation
        
        collaboration_log.append(f"Collaboration completed in {total_time:.2f}s")
        
        return CollaborationResult(
            task_id=task_id,
            success=len(agent_responses) > 0,
            final_answer=final_answer,
            agent_responses=agent_responses,
            collaboration_log=collaboration_log,
            total_time=total_time,
            confidence_score=confidence_score
        )
    
    async def stream_collaboration(self, 
                                 task_id: str,
                                 prompt: str, 
                                 context: str = "") -> AsyncGenerator[Dict[str, Any], None]:
        """Stream collaborative responses as they come in"""
        
        active_agents = [agent for agent in self.agents.values() if agent.config.enabled]
        
        yield {
            "type": "start",
            "message": f"Starting collaboration with {len(active_agents)} agents",
            "agents": [agent.config.name for agent in active_agents]
        }
        
        # Stream responses from each agent
        for agent in active_agents:
            if await agent.is_available():
                yield {
                    "type": "agent_start",
                    "agent": agent.config.name,
                    "model_type": agent.config.model_type.value,
                    "message": f"{agent.config.name} is thinking..."
                }
                
                response = await agent.generate_response(prompt, context)
                
                yield {
                    "type": "agent_response",
                    "agent": agent.config.name,
                    "model_type": agent.config.model_type.value,
                    "response": response
                }
        
        yield {
            "type": "complete",
            "message": "Collaboration completed"
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        return {
            "total_agents": len(self.agents),
            "agents": [
                {
                    "name": agent.config.name,
                    "model_type": agent.config.model_type.value,
                    "model_name": agent.config.model_name,
                    "role": agent.config.role,
                    "enabled": agent.config.enabled,
                    "capabilities": agent.config.capabilities
                }
                for agent in self.agents.values()
            ]
        }

# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> AutogenOrchestrator:
    """Get the global autogen orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AutogenOrchestrator()
        _orchestrator.setup_default_agents()
    return _orchestrator