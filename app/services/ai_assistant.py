"""
ChatterFix AI Assistant - Main AI interface
Uses Smart AI Router to leverage the full AI team when needed
"""

import logging

from .gemini_service import gemini_service
from .health_monitor import HealthMonitor
from .predictive_engine import PredictiveMaintenanceEngine

logger = logging.getLogger(__name__)

# Import AI Router (lazy to avoid circular imports)
_ai_router = None


def _get_ai_router():
    """Lazy load AI router to avoid circular imports"""
    global _ai_router
    if _ai_router is None:
        try:
            from .ai_router import ai_router
            _ai_router = ai_router
            logger.info("🧠 Smart AI Router loaded")
        except ImportError as e:
            logger.warning(f"AI Router not available: {e}")
            _ai_router = False
    return _ai_router if _ai_router else None


class ChatterFixAIClient:
    """
    Main AI client for ChatterFix CMMS

    Uses smart routing to:
    - Simple queries: Fast Gemini response (< 2 seconds)
    - Complex tasks: Full AI team collaboration (6 models)
    """

    def __init__(self):
        logger.info("ChatterFix AI Assistant initialized")

        try:
            self.predictive_engine = PredictiveMaintenanceEngine()
            self.health_monitor = HealthMonitor()
            self.gemini = gemini_service
            logger.info("🤖 Advanced AI features initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize advanced features: {e}")
            self.predictive_engine = None
            self.health_monitor = None
            self.gemini = None

    async def start(self):
        """Start background tasks"""
        if self.predictive_engine:
            await self.predictive_engine.start()

    async def process_message(
        self,
        message: str,
        context: str = "",
        user_id: int = None,
        context_type: str = "general",
        force_team: bool = False
    ) -> str:
        """
        Process a user message and return an AI response

        Uses smart routing to determine best AI approach:
        - Simple: Fast single model (Gemini)
        - Moderate: Specialist agents
        - Complex: Full AI team

        Args:
            message: User's message
            context: Additional context
            user_id: User ID for personalization
            context_type: Type of request for routing
            force_team: Force full AI team collaboration

        Returns:
            AI response string
        """
        router = _get_ai_router()

        if router:
            # Use smart AI router for optimal model selection
            result = await router.route_request(
                message=message,
                context=context,
                context_type=context_type,
                user_id=user_id,
                force_team=force_team
            )

            if result.get("success"):
                logger.info(f"✅ AI response via {result.get('model_used')} ({result.get('complexity')}) in {result.get('response_time', 'N/A')}")
                return result.get("response", "")
            else:
                logger.warning(f"⚠️ AI router failed, using fallback")

        # Fallback to direct Gemini if router unavailable
        if self.gemini:
            return await self.gemini.generate_response(
                message, context, user_id=user_id
            )

        return "AI features are currently unavailable."

    async def process_with_team(
        self,
        message: str,
        context: str = "",
        user_id: int = None,
        context_type: str = "general"
    ) -> dict:
        """
        Force full AI team processing and return detailed result

        Returns full response dict with model info, complexity, etc.
        """
        router = _get_ai_router()

        if router:
            return await router.route_request(
                message=message,
                context=context,
                context_type=context_type,
                user_id=user_id,
                force_team=True
            )

        # Fallback
        if self.gemini:
            response = await self.gemini.generate_response(
                message, context, user_id=user_id
            )
            return {
                "success": True,
                "response": response,
                "model_used": "gemini-2.0-flash (fallback)",
                "complexity": "unknown"
            }

        return {
            "success": False,
            "response": "AI features are currently unavailable.",
            "model_used": "none"
        }

    async def diagnose_equipment(
        self,
        description: str,
        equipment_type: str = "",
        symptoms: str = "",
        user_id: int = None
    ) -> dict:
        """
        Equipment diagnosis - always uses AI team for thorough analysis

        Returns detailed diagnosis with multiple AI perspectives
        """
        context = f"""
Equipment Type: {equipment_type or 'Unknown'}
Symptoms/Issues: {symptoms}
"""
        return await self.process_with_team(
            message=description,
            context=context,
            user_id=user_id,
            context_type="equipment_diagnosis"
        )

    async def troubleshoot(
        self,
        issue: str,
        asset_info: str = "",
        user_id: int = None
    ) -> dict:
        """
        Troubleshooting - uses AI team for complex issues

        Returns step-by-step troubleshooting guidance
        """
        return await self.process_with_team(
            message=issue,
            context=f"Asset: {asset_info}",
            user_id=user_id,
            context_type="troubleshooting"
        )


# Global instance
chatterfix_ai = ChatterFixAIClient()
