"""
Enhanced Autogen Framework for Multi-Model AI Team Collaboration
Coordinates Claude, ChatGPT, Gemini, Grok, and other AI models
WITH COMPREHENSIVE MEMORY SYSTEM INTEGRATION
Never repeat mistakes - Always learn and improve
"""
import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, AsyncGenerator, Any
from enum import Enum
from datetime import timedelta

# Import memory system components
from .memory_system import (
    get_memory_system, 
    get_mistake_prevention, 
    get_proactive_assistant,
    MistakeType, 
    OutcomeRating
)

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
    """
    Enhanced Orchestrates multi-agent collaboration using autogen principles
    WITH COMPREHENSIVE MEMORY SYSTEM INTEGRATION
    """
    
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.active_tasks: Dict[str, Dict] = {}
        
        # Initialize memory and learning systems
        self.memory_system = get_memory_system()
        self.mistake_prevention = get_mistake_prevention()
        self.proactive_assistant = get_proactive_assistant()
        
        # Performance tracking
        self.agent_performance_history = {}
        self.learning_enabled = True
        
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
                                       max_iterations: int = 3,
                                       project_context: str = "ChatterFix") -> CollaborationResult:
        """Execute a task using multiple AI agents in collaboration WITH MEMORY INTEGRATION"""
        
        start_time = time.time()
        collaboration_log = []
        agent_responses = []
        
        # STEP 1: PRE-EXECUTION ANALYSIS - Check for potential mistakes
        if self.learning_enabled:
            task_context = {
                "task_id": task_id,
                "prompt": prompt,
                "context": context,
                "project": project_context,
                "timestamp": time.time()
            }
            
            # Check for potential issues using proactive assistant
            proactive_guidance = await self.proactive_assistant.anticipate_issues(task_context)
            if proactive_guidance:
                collaboration_log.append(f"🛡️ PROACTIVE GUIDANCE: {proactive_guidance.get('type', 'unknown')}")
                
                if proactive_guidance.get('urgency') == 'high':
                    # Add prevention guidance to context
                    prevention_context = json.dumps(proactive_guidance, indent=2)
                    context = f"{context}\n\nIMPORTANT PREVENTION GUIDANCE:\n{prevention_context}"
                    collaboration_log.append("⚠️ High-urgency guidance integrated into task context")
            
            # Check for similar successful patterns
            historical_solutions = await self.memory_system.find_solution_patterns(prompt)
            if historical_solutions:
                collaboration_log.append(f"📚 Found {len(historical_solutions)} similar successful patterns")
                
                # Add best practices to context
                best_practices = []
                for solution in historical_solutions[:2]:  # Top 2 solutions
                    best_practices.extend(solution.best_practices)
                
                if best_practices:
                    practices_context = "\n".join(set(best_practices))
                    context = f"{context}\n\nBEST PRACTICES FROM PAST SUCCESSES:\n{practices_context}"
        
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
        
        # STEP 4: POST-EXECUTION LEARNING - Capture conversation and learn
        result = CollaborationResult(
            task_id=task_id,
            success=len(agent_responses) > 0,
            final_answer=final_answer,
            agent_responses=agent_responses,
            collaboration_log=collaboration_log,
            total_time=total_time,
            confidence_score=confidence_score
        )
        
        if self.learning_enabled:
            try:
                # Capture conversation for learning
                conversation_id = await self.memory_system.capture_conversation(
                    user_prompt=prompt,
                    ai_responses=[{
                        'model': resp.get('model_type', 'unknown'),
                        'agent': resp.get('agent', 'unknown'),
                        'response': resp.get('response', ''),
                        'confidence': confidence_score
                    } for resp in agent_responses],
                    context_data={
                        'task_id': task_id,
                        'collaboration_log': collaboration_log,
                        'total_time': total_time,
                        'success': result.success
                    },
                    project_context=project_context
                )
                
                collaboration_log.append(f"💾 Conversation captured: {conversation_id}")
                
                # If successful, capture as solution pattern
                if result.success and confidence_score > 0.7:
                    await self.memory_system.capture_solution(
                        problem_pattern=prompt,
                        solution_steps=[final_answer],
                        success_rate=confidence_score,
                        application=project_context,
                        performance_metrics={
                            'execution_time': total_time,
                            'agent_count': len(agent_responses),
                            'confidence': confidence_score
                        }
                    )
                    collaboration_log.append("✅ Success pattern captured for future learning")
                
                # Update agent performance tracking
                for resp in agent_responses:
                    agent_name = resp.get('agent', 'unknown')
                    if agent_name not in self.agent_performance_history:
                        self.agent_performance_history[agent_name] = {
                            'total_tasks': 0,
                            'successful_tasks': 0,
                            'average_confidence': 0.0
                        }
                    
                    perf = self.agent_performance_history[agent_name]
                    perf['total_tasks'] += 1
                    if result.success:
                        perf['successful_tasks'] += 1
                    perf['average_confidence'] = (perf['average_confidence'] + confidence_score) / perf['total_tasks']
                
            except Exception as e:
                logger.error(f"Failed to capture learning data: {e}")
                collaboration_log.append(f"⚠️ Learning capture failed: {str(e)}")
        
        return result
    
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
        """Get status of all registered agents WITH PERFORMANCE ANALYTICS"""
        return {
            "total_agents": len(self.agents),
            "learning_enabled": self.learning_enabled,
            "agents": [
                {
                    "name": agent.config.name,
                    "model_type": agent.config.model_type.value,
                    "model_name": agent.config.model_name,
                    "role": agent.config.role,
                    "enabled": agent.config.enabled,
                    "capabilities": agent.config.capabilities,
                    "performance": self.agent_performance_history.get(agent.config.name, {
                        "total_tasks": 0,
                        "successful_tasks": 0,
                        "average_confidence": 0.0,
                        "success_rate": 0.0
                    })
                }
                for agent in self.agents.values()
            ]
        }
    
    async def get_comprehensive_analytics(self, project_context: str = "ChatterFix") -> Dict[str, Any]:
        """Get comprehensive analytics about AI team performance and learning"""
        try:
            # Get memory system analytics
            development_patterns = await self.memory_system.analyze_development_patterns(project_context)
            
            # Get conversation history
            recent_conversations = await self.memory_system.get_conversation_history(
                project_context=project_context, 
                days_back=7
            )
            
            # Calculate agent performance metrics
            agent_analytics = {}
            for agent_name, perf in self.agent_performance_history.items():
                if perf['total_tasks'] > 0:
                    agent_analytics[agent_name] = {
                        **perf,
                        'success_rate': perf['successful_tasks'] / perf['total_tasks'],
                        'efficiency_score': perf['average_confidence'] * (perf['successful_tasks'] / perf['total_tasks'])
                    }
            
            # Learning progress metrics
            learning_metrics = {
                "total_conversations_captured": development_patterns.get("total_conversations", 0),
                "total_mistakes_identified": development_patterns.get("total_mistakes", 0),
                "total_solutions_captured": development_patterns.get("total_solutions", 0),
                "mistake_prevention_rate": 0,
                "learning_velocity": 0
            }
            
            if learning_metrics["total_mistakes_identified"] > 0 and learning_metrics["total_solutions_captured"] > 0:
                learning_metrics["mistake_prevention_rate"] = (
                    learning_metrics["total_solutions_captured"] / 
                    (learning_metrics["total_mistakes_identified"] + learning_metrics["total_solutions_captured"])
                )
            
            # Recent activity analysis
            recent_activity = {
                "conversations_this_week": len(recent_conversations),
                "average_confidence_this_week": 0,
                "most_active_models": {},
                "common_topics": []
            }
            
            if recent_conversations:
                total_confidence = 0
                model_counts = {}
                
                for conv in recent_conversations:
                    total_confidence += conv.outcome_rating.value
                    for model in conv.ai_models_involved:
                        model_counts[model] = model_counts.get(model, 0) + 1
                
                recent_activity["average_confidence_this_week"] = total_confidence / len(recent_conversations)
                recent_activity["most_active_models"] = dict(sorted(model_counts.items(), key=lambda x: x[1], reverse=True))
            
            return {
                "timestamp": time.time(),
                "project_context": project_context,
                "learning_enabled": self.learning_enabled,
                "development_patterns": development_patterns,
                "agent_analytics": agent_analytics,
                "learning_metrics": learning_metrics,
                "recent_activity": recent_activity,
                "ai_team_recommendations": development_patterns.get("recommendations", []),
                "overall_health_score": self._calculate_health_score(learning_metrics, agent_analytics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive analytics: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    def _calculate_health_score(self, learning_metrics: Dict, agent_analytics: Dict) -> float:
        """Calculate overall AI team health score (0.0 to 1.0)"""
        try:
            # Base score components
            mistake_prevention_score = learning_metrics.get("mistake_prevention_rate", 0) * 0.3
            
            # Agent performance score
            if agent_analytics:
                avg_success_rate = sum(perf.get('success_rate', 0) for perf in agent_analytics.values()) / len(agent_analytics)
                agent_performance_score = avg_success_rate * 0.4
            else:
                agent_performance_score = 0
            
            # Learning activity score
            total_learning_items = (
                learning_metrics.get("total_conversations_captured", 0) +
                learning_metrics.get("total_solutions_captured", 0)
            )
            learning_activity_score = min(total_learning_items / 100, 1.0) * 0.3  # Normalize to max 100 items
            
            overall_score = mistake_prevention_score + agent_performance_score + learning_activity_score
            return min(overall_score, 1.0)
            
        except Exception:
            return 0.5  # Neutral score if calculation fails
    
    async def capture_mistake_from_failure(self, 
                                         task_id: str, 
                                         error_details: Dict[str, Any],
                                         context: Dict[str, Any]) -> str:
        """Capture a mistake when a task fails"""
        try:
            mistake_type = MistakeType.CODE_ERROR  # Default, can be refined
            
            # Determine mistake type from error details
            if "security" in str(error_details).lower():
                mistake_type = MistakeType.SECURITY_VULNERABILITY
            elif "performance" in str(error_details).lower():
                mistake_type = MistakeType.PERFORMANCE_ISSUE
            elif "deploy" in str(error_details).lower():
                mistake_type = MistakeType.DEPLOYMENT_FAILURE
            elif "architecture" in str(error_details).lower():
                mistake_type = MistakeType.ARCHITECTURE_FLAW
            
            mistake_id = await self.memory_system.capture_mistake(
                mistake_type=mistake_type,
                description=f"Task {task_id} failed: {error_details.get('message', 'Unknown error')}",
                context={**context, "task_id": task_id, "error_details": error_details},
                how_detected="automatic_failure_detection",
                resolution_steps=[],  # To be filled when resolution is found
                impact_severity="medium"  # Default, can be refined
            )
            
            logger.warning(f"🚨 Mistake captured from failure: {mistake_id}")
            return mistake_id
            
        except Exception as e:
            logger.error(f"Failed to capture mistake from failure: {e}")
            return ""

# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> AutogenOrchestrator:
    """Get the global autogen orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AutogenOrchestrator()
        _orchestrator.setup_default_agents()
    return _orchestrator