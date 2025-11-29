import logging
import asyncio
from typing import Optional
from .predictive_engine import PredictiveMaintenanceEngine
from .health_monitor import HealthMonitor
from .openai_service import openai_service

logger = logging.getLogger(__name__)

class ChatterFixAIClient:
    def __init__(self):
        logger.info("ChatterFix AI Assistant initialized")
        
        try:
            self.predictive_engine = PredictiveMaintenanceEngine()
            self.health_monitor = HealthMonitor()
            self.openai = openai_service
            logger.info("🤖 Advanced AI features initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize advanced features: {e}")
            self.predictive_engine = None
            self.health_monitor = None
            self.openai = None

    async def start(self):
        """Start background tasks"""
        if self.predictive_engine:
            await self.predictive_engine.start()
        # Health monitor start logic if needed

    async def process_message(self, message: str, context: str = "", user_id: int = None) -> str:
        """Process a user message and return an AI response"""
        if self.openai:
            return await self.openai.generate_response(message, context, user_id=user_id)
        return "AI features are currently unavailable."

# Global instance
chatterfix_ai = ChatterFixAIClient()
