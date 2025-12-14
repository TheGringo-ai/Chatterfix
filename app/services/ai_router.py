"""
Smart AI Router - Routes requests to the best AI model or team
Optimizes for speed on simple tasks, uses full AI team for complex tasks
"""

import logging
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.ai_team_http_client import (
    execute_ai_team_task,
    check_ai_team_health,
    get_ai_team_client,
)
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    SIMPLE = "simple"           # Quick response, single model
    MODERATE = "moderate"       # Single specialist model
    COMPLEX = "complex"         # Full AI team collaboration


class AIRouter:
    """
    Smart router that determines the best AI approach for each request.

    - SIMPLE tasks: Use fast single model (Gemini) for < 2 second response
    - MODERATE tasks: Use specialist from AI team
    - COMPLEX tasks: Use full AI team collaboration
    """

    # Keywords indicating complex tasks requiring team collaboration
    COMPLEX_KEYWORDS = [
        "analyze", "diagnose", "troubleshoot", "investigate",
        "design", "architect", "plan", "strategy",
        "multiple", "several", "compare", "comprehensive",
        "emergency", "critical", "urgent", "safety",
        "root cause", "failure analysis", "predictive",
        "optimization", "improve", "enhance",
        "workflow", "process", "procedure",
        "training", "documentation", "manual"
    ]

    # Keywords indicating simple tasks
    SIMPLE_KEYWORDS = [
        "hello", "hi", "hey", "thanks", "thank you",
        "what is", "where is", "how do i", "show me",
        "status", "check", "list", "get",
        "yes", "no", "ok", "okay", "sure"
    ]

    # Context types that require specific handling
    SPECIALIST_CONTEXTS = {
        "equipment_diagnosis": ["gemini-analyst", "grok-reasoner"],
        "part_recognition": ["gemini-creative", "gemini-analyst"],
        "troubleshooting": ["grok-reasoner", "gpt4-analyst"],
        "work_order": ["grok-coder", "chatgpt-coder"],
        "inventory": ["grok-coder"],
        "documentation": ["gemini-analyst", "gpt4-analyst"],
        "training": ["gemini-creative", "gpt4-analyst"],
        "emergency": None,  # Always use full team
    }

    def __init__(self):
        self.ai_team_available = False
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
        logger.info("🧠 Smart AI Router initialized")

    async def _check_ai_team_availability(self) -> bool:
        """Check if AI team service is available (with caching)"""
        current_time = time.time()

        if current_time - self.last_health_check > self.health_check_interval:
            self.ai_team_available = await check_ai_team_health()
            self.last_health_check = current_time

            if self.ai_team_available:
                logger.info("✅ AI Team service is available")
            else:
                logger.warning("⚠️ AI Team service unavailable, using fallback")

        return self.ai_team_available

    def _detect_complexity(self, message: str, context: str = "", context_type: str = "") -> TaskComplexity:
        """Detect the complexity of a task based on message content"""
        message_lower = message.lower()
        context_lower = context.lower() if context else ""
        combined = f"{message_lower} {context_lower}"

        # Emergency/critical always gets full team
        if context_type == "emergency" or any(word in combined for word in ["emergency", "critical", "urgent", "safety hazard"]):
            logger.info("🚨 Emergency detected - using full AI team")
            return TaskComplexity.COMPLEX

        # Check for simple greetings/acknowledgments
        if len(message.split()) <= 5 and any(word in message_lower for word in self.SIMPLE_KEYWORDS):
            return TaskComplexity.SIMPLE

        # Count complex keywords
        complex_count = sum(1 for keyword in self.COMPLEX_KEYWORDS if keyword in combined)

        # Long messages with multiple sentences are likely complex
        sentence_count = len(re.split(r'[.!?]', message))
        word_count = len(message.split())

        # Complexity scoring
        complexity_score = 0
        complexity_score += complex_count * 2
        complexity_score += sentence_count - 1
        complexity_score += word_count // 20

        # Equipment diagnosis, troubleshooting always at least moderate
        if context_type in ["equipment_diagnosis", "troubleshooting", "failure_analysis"]:
            complexity_score += 3

        if complexity_score >= 5:
            return TaskComplexity.COMPLEX
        elif complexity_score >= 2:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    def _get_specialist_agents(self, context_type: str) -> Optional[List[str]]:
        """Get recommended specialist agents for a context type"""
        return self.SPECIALIST_CONTEXTS.get(context_type)

    async def route_request(
        self,
        message: str,
        context: str = "",
        context_type: str = "general",
        user_id: Optional[int] = None,
        force_team: bool = False
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate AI model(s)

        Args:
            message: User's message
            context: Additional context
            context_type: Type of request (equipment_diagnosis, troubleshooting, etc.)
            user_id: User ID for personalization
            force_team: Force use of full AI team

        Returns:
            Response dict with 'response', 'model_used', 'complexity', etc.
        """
        start_time = time.time()

        # Detect complexity
        complexity = TaskComplexity.COMPLEX if force_team else self._detect_complexity(message, context, context_type)

        logger.info(f"📊 Task complexity: {complexity.value} for: {message[:50]}...")

        # Check AI team availability
        team_available = await self._check_ai_team_availability()

        try:
            if complexity == TaskComplexity.SIMPLE or not team_available:
                # Use fast single model (Gemini)
                response = await self._route_to_gemini(message, context, user_id)
                model_used = "gemini-2.0-flash"

            elif complexity == TaskComplexity.MODERATE:
                # Use specialist agent(s)
                specialists = self._get_specialist_agents(context_type)

                if specialists and team_available:
                    response = await self._route_to_specialists(message, context, specialists)
                    model_used = f"specialists: {', '.join(specialists)}"
                else:
                    response = await self._route_to_gemini(message, context, user_id)
                    model_used = "gemini-2.0-flash"

            else:  # COMPLEX
                # Use full AI team collaboration
                if team_available:
                    response = await self._route_to_team(message, context, context_type)
                    model_used = "full-ai-team"
                else:
                    # Fallback to Gemini with enhanced prompt
                    enhanced_context = f"[COMPLEX TASK - Provide thorough analysis]\n{context}"
                    response = await self._route_to_gemini(message, enhanced_context, user_id)
                    model_used = "gemini-2.0-flash (fallback)"

            elapsed_time = time.time() - start_time

            return {
                "success": True,
                "response": response,
                "model_used": model_used,
                "complexity": complexity.value,
                "response_time": f"{elapsed_time:.2f}s",
                "team_available": team_available
            }

        except Exception as e:
            logger.error(f"❌ AI routing error: {e}")

            # Ultimate fallback to Gemini
            try:
                response = await self._route_to_gemini(message, context, user_id)
                return {
                    "success": True,
                    "response": response,
                    "model_used": "gemini-2.0-flash (error fallback)",
                    "complexity": complexity.value,
                    "error_recovered": True
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "response": f"I'm having trouble processing your request. Error: {str(e)}",
                    "model_used": "none",
                    "complexity": complexity.value,
                    "error": str(fallback_error)
                }

    async def _route_to_gemini(self, message: str, context: str, user_id: Optional[int]) -> str:
        """Route to Gemini for fast single-model response"""
        logger.info("⚡ Routing to Gemini for fast response")

        # Add CMMS context for better responses
        cmms_context = """You are ChatterFix AI, an intelligent CMMS assistant for industrial maintenance technicians.
You help with work orders, equipment diagnosis, inventory management, and troubleshooting.
Be concise, professional, and action-oriented. Prioritize safety.

""" + (context or "")

        return await gemini_service.generate_response(message, cmms_context, user_id)

    async def _route_to_specialists(self, message: str, context: str, specialists: List[str]) -> str:
        """Route to specific specialist agents"""
        logger.info(f"🎯 Routing to specialists: {specialists}")

        result = await execute_ai_team_task(
            prompt=message,
            context=f"ChatterFix CMMS Context:\n{context}",
            required_agents=specialists,
            max_iterations=2,  # Quick specialist response
            project_context="ChatterFix"
        )

        if result.get("success"):
            return result.get("final_result", "Specialist analysis complete.")
        else:
            # Fallback
            return await self._route_to_gemini(message, context, None)

    async def _route_to_team(self, message: str, context: str, context_type: str) -> str:
        """Route to full AI team for complex collaborative task"""
        logger.info("🤖 Routing to FULL AI TEAM for complex task")

        enhanced_prompt = f"""
[ChatterFix CMMS - Complex Task Analysis Required]

Task Type: {context_type}
User Request: {message}

Context:
{context}

Please provide a comprehensive response with:
1. Analysis of the situation
2. Recommended actions
3. Safety considerations
4. Next steps

Collaborate as a team to provide the best possible guidance.
"""

        result = await execute_ai_team_task(
            prompt=enhanced_prompt,
            context=context,
            required_agents=None,  # Use all available agents
            max_iterations=3,  # Allow thorough collaboration
            project_context="ChatterFix"
        )

        if result.get("success"):
            response = result.get("final_result", "")

            # Add collaboration summary if available
            summary = result.get("collaboration_summary", "")
            if summary and summary not in response:
                response = f"{response}\n\n---\n*AI Team Collaboration: {summary}*"

            return response
        else:
            return result.get("final_result", "AI team analysis complete.")


# Global instance
ai_router = AIRouter()


async def smart_ai_response(
    message: str,
    context: str = "",
    context_type: str = "general",
    user_id: Optional[int] = None,
    force_team: bool = False
) -> Dict[str, Any]:
    """Convenience function to get smart AI response"""
    return await ai_router.route_request(
        message=message,
        context=context,
        context_type=context_type,
        user_id=user_id,
        force_team=force_team
    )
