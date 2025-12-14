"""
HTTP-based AI Orchestrator for AI Team Service
Replaces gRPC-based autogen framework with HTTP REST API
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
import sys
import os

from app.ai_team.autogen_framework import (
    AutogenOrchestrator as BaseOrchestrator,
    CollaborationResult,
    AgentConfig,
    ModelType
)

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """HTTP-based AI orchestrator wrapping the existing autogen framework"""
    
    def __init__(self):
        self.base_orchestrator = BaseOrchestrator()
        self.active_tasks: Dict[str, Dict] = {}
        self.task_counter = 0
        
    async def initialize(self):
        """Initialize the AI orchestrator"""
        try:
            # Setup default agents (Claude, ChatGPT, Gemini, Grok)
            self.base_orchestrator.setup_default_agents()
            logger.info("✅ AI Orchestrator initialized with default agents")
            
            # Log available agents
            available_agents = []
            for agent_name, agent in self.base_orchestrator.agents.items():
                is_available = await agent.is_available()
                available_agents.append(f"{agent_name}: {'✅' if is_available else '❌'}")
            
            logger.info(f"📊 Agent availability: {', '.join(available_agents)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI orchestrator: {e}")
            raise
    
    @property
    def agents(self):
        """Get agents dictionary for compatibility"""
        return self.base_orchestrator.agents
    
    async def execute_collaborative_task(
        self,
        prompt: str,
        context: str = "",
        required_agents: Optional[List[str]] = None,
        max_iterations: int = 3,
        project_context: str = "ChatterFix",
        stream_response: bool = False,
        fast_mode: bool = False
    ) -> CollaborationResult:
        """
        Execute collaborative task using the AI team

        Args:
            prompt: Task prompt
            context: Additional context
            required_agents: Specific agents to use
            max_iterations: Max collaboration rounds
            project_context: Project name
            stream_response: Enable streaming (not yet implemented)
            fast_mode: Skip refinement for ~50% faster response
        """

        # Generate unique task ID
        self.task_counter += 1
        task_id = f"task-{int(time.time())}-{self.task_counter}"

        mode_indicator = "⚡ FAST" if fast_mode else "🔄 FULL"
        logger.info(f"🚀 Starting {mode_indicator} collaborative task {task_id}")
        logger.info(f"📝 Prompt: {prompt[:100]}...")

        try:
            # Store task in active tasks
            self.active_tasks[task_id] = {
                "prompt": prompt,
                "context": context,
                "status": "running",
                "start_time": time.time(),
                "fast_mode": fast_mode
            }

            # Execute the collaborative task
            result = await self.base_orchestrator.execute_collaborative_task(
                task_id=task_id,
                prompt=prompt,
                context=context,
                required_agents=required_agents,
                max_iterations=max_iterations,
                project_context=project_context,
                fast_mode=fast_mode
            )
            
            # Update task status
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["end_time"] = time.time()
            self.active_tasks[task_id]["result"] = result
            
            logger.info(f"✅ Completed task {task_id} in {result.total_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}")
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)
            raise
    
    async def stream_collaborative_task(
        self,
        prompt: str,
        context: str = "",
        required_agents: Optional[List[str]] = None,
        max_iterations: int = 3,
        project_context: str = "ChatterFix"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream collaborative task responses in real-time"""
        
        task_id = f"stream-{int(time.time())}-{self.task_counter}"
        self.task_counter += 1
        
        try:
            yield {"type": "task_started", "task_id": task_id, "timestamp": time.time()}
            
            # Execute task with streaming
            result = await self.execute_collaborative_task(
                prompt=prompt,
                context=context,
                required_agents=required_agents,
                max_iterations=max_iterations,
                project_context=project_context
            )
            
            # Stream agent responses
            for response in result.agent_responses:
                yield {
                    "type": "agent_response",
                    "agent": response.get("agent", "unknown"),
                    "role": response.get("role", "assistant"),
                    "response": response.get("response", ""),
                    "model_type": response.get("model_type", "unknown"),
                    "timestamp": time.time()
                }
                
                # Add small delay for streaming effect
                await asyncio.sleep(0.1)
            
            # Stream final result
            yield {
                "type": "task_completed",
                "task_id": task_id,
                "final_answer": result.final_answer,
                "collaboration_log": result.collaboration_log,
                "total_time": result.total_time,
                "confidence_score": result.confidence_score,
                "timestamp": time.time()
            }
            
        except Exception as e:
            yield {
                "type": "task_failed",
                "task_id": task_id,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task"""
        return self.active_tasks.get(task_id)
    
    async def get_active_tasks(self) -> List[Dict]:
        """Get all active tasks"""
        return list(self.active_tasks.values())
    
    async def get_agent_analytics(self) -> Dict[str, Any]:
        """Get analytics about agent performance"""
        try:
            analytics = {
                "total_agents": len(self.base_orchestrator.agents),
                "available_agents": 0,
                "agent_details": [],
                "performance_history": getattr(self.base_orchestrator, 'agent_performance_history', {}),
                "total_tasks_completed": len([t for t in self.active_tasks.values() if t.get("status") == "completed"]),
                "total_tasks_failed": len([t for t in self.active_tasks.values() if t.get("status") == "failed"]),
                "timestamp": time.time()
            }
            
            for agent_name, agent in self.base_orchestrator.agents.items():
                is_available = await agent.is_available()
                if is_available:
                    analytics["available_agents"] += 1
                
                analytics["agent_details"].append({
                    "name": agent_name,
                    "model_type": agent.config.model_type.value,
                    "role": agent.config.role,
                    "capabilities": agent.config.capabilities,
                    "available": is_available,
                    "conversation_history_length": len(agent.conversation_history)
                })
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting agent analytics: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            health = {
                "status": "healthy",
                "agents": {},
                "active_tasks": len(self.active_tasks),
                "memory_system": "available",  # Simplified check
                "timestamp": time.time()
            }
            
            # Check each agent
            for agent_name, agent in self.base_orchestrator.agents.items():
                try:
                    is_available = await agent.is_available()
                    health["agents"][agent_name] = "healthy" if is_available else "unavailable"
                except Exception as e:
                    health["agents"][agent_name] = f"error: {str(e)}"
            
            # Overall status
            healthy_agents = sum(1 for status in health["agents"].values() if status == "healthy")
            if healthy_agents == 0:
                health["status"] = "unhealthy"
            elif healthy_agents < len(self.base_orchestrator.agents):
                health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }