"""
AI Orchestrator Module
Central routing and coordination system for multi-AI capabilities
Coordinates between Gemini, OpenAI, Grok, and other AI services
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from .gemini_service import GeminiService
from .openai_service import OpenAIService
from .voice_commands import process_voice_command

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """AI task types for intelligent routing"""

    PREDICTIVE = "predictive"
    DOCUMENTATION = "documentation"
    VISION = "vision"
    VOICE_COMMAND = "voice_command"
    ANALYSIS = "analysis"
    CREATIVE = "creative"


class AIModel(Enum):
    """Available AI models"""

    GEMINI = "gemini"
    OPENAI = "openai"
    GROK = "grok"
    AUTO = "auto"  # Let orchestrator decide


class AIOrchestrator:
    """
    Central AI coordination system for ChatterFix CMMS
    Routes requests to optimal AI models based on task type and complexity
    """

    def __init__(self):
        self.gemini_service = GeminiService()
        self.openai_service = OpenAIService()

        # Import config for API key checking
        try:
            from app.core.config import settings

            self.config = settings.get_ai_config()
        except Exception as e:
            logger.warning(f"⚠️ Config system not available: {e}")
            self.config = None

        # Performance tracking
        self.performance_metrics = {
            "gemini": {"calls": 0, "avg_time": 0, "success_rate": 100},
            "openai": {"calls": 0, "avg_time": 0, "success_rate": 100},
            "grok": {"calls": 0, "avg_time": 0, "success_rate": 100},
        }

        # Model preferences for different task types
        self.task_routing = {
            TaskType.PREDICTIVE: [AIModel.GEMINI, AIModel.OPENAI],
            TaskType.DOCUMENTATION: [AIModel.OPENAI, AIModel.GEMINI],
            TaskType.VISION: [AIModel.GEMINI],  # Gemini excels at vision
            TaskType.VOICE_COMMAND: [AIModel.GROK, AIModel.OPENAI, AIModel.GEMINI],
            TaskType.ANALYSIS: [AIModel.GEMINI, AIModel.OPENAI],
            TaskType.CREATIVE: [AIModel.OPENAI, AIModel.GEMINI],
        }

        logger.info("🤖 AI Orchestrator initialized - Multi-AI coordination ready")

    async def route_request(
        self,
        task_type: TaskType,
        input_data: Any,
        context: str = "",
        preferred_model: Optional[AIModel] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Route request to optimal AI model based on task type and context

        Args:
            task_type: Type of AI task to perform
            input_data: Input data (text, image, etc.)
            context: Additional context for the request
            preferred_model: Override automatic routing
            user_id: User ID for personalization

        Returns:
            Dict containing response and metadata
        """
        try:
            # Determine best model for this task
            selected_model = self._select_model(task_type, preferred_model)

            logger.info(f"🎯 Routing {task_type.value} task to {selected_model.value}")

            # Execute request with selected model
            start_time = time.time()
            result = await self._execute_request(
                selected_model, task_type, input_data, context, user_id
            )
            execution_time = time.time() - start_time

            # Update performance metrics
            self._update_metrics(selected_model.value, execution_time, True)

            return {
                "response": result,
                "model_used": selected_model.value,
                "execution_time": execution_time,
                "task_type": task_type.value,
                "success": True,
            }

        except Exception as e:
            logger.error(f"❌ AI routing failed for {task_type.value}: {e}")

            # Try fallback model
            fallback_result = await self._try_fallback(
                task_type, input_data, context, user_id, preferred_model
            )

            if fallback_result:
                return fallback_result

            return {
                "response": "AI services are temporarily unavailable. Please try again later.",
                "model_used": "none",
                "execution_time": 0,
                "task_type": task_type.value,
                "success": False,
                "error": str(e),
            }

    def _select_model(
        self, task_type: TaskType, preferred_model: Optional[AIModel] = None
    ) -> AIModel:
        """Select the best AI model for the given task"""

        if preferred_model and preferred_model != AIModel.AUTO:
            return preferred_model

        # Get preferred models for this task type
        preferred_models = self.task_routing.get(task_type, [AIModel.GEMINI])

        # Select based on availability and performance
        for model in preferred_models:
            if self._is_model_available(model):
                return model

        # Fallback to Gemini (most reliable)
        return AIModel.GEMINI

    def _is_model_available(self, model: AIModel) -> bool:
        """Check if a specific AI model is available and performing well"""
        try:
            if model == AIModel.GEMINI:
                return (
                    hasattr(self.gemini_service, "default_api_key")
                    and self.gemini_service.default_api_key
                )
            elif model == AIModel.OPENAI:
                return (
                    hasattr(self.openai_service, "default_api_key")
                    and self.openai_service.default_api_key
                )
            elif model == AIModel.GROK:
                # Check if Grok/XAI API key is configured
                return (
                    self.config
                    and self.config.grok_api_key
                    and len(self.config.grok_api_key) > 10
                )

            return False

        except Exception:
            return False

    async def _execute_request(
        self,
        model: AIModel,
        task_type: TaskType,
        input_data: Any,
        context: str,
        user_id: Optional[int] = None,
    ) -> str:
        """Execute the AI request with the selected model"""

        try:
            if model == AIModel.GEMINI:
                if task_type == TaskType.VISION and hasattr(input_data, "read"):
                    # Handle image input for vision tasks
                    return await self.gemini_service.analyze_image(
                        input_data, context, user_id=user_id
                    )
                else:
                    # Handle text input
                    return await self.gemini_service.generate_response(
                        str(input_data), context, user_id=user_id
                    )

            elif model == AIModel.OPENAI:
                return await self.openai_service.generate_response(
                    str(input_data), context, user_id=user_id
                )

            elif model == AIModel.GROK:
                # Handle Grok through voice command service for now
                if task_type == TaskType.VOICE_COMMAND:
                    result = await process_voice_command(str(input_data), user_id)
                    return result.get("response", "Grok processing completed")
                else:
                    # Use Grok for general text processing
                    import os

                    import httpx

                    xai_key = os.getenv("XAI_API_KEY")
                    if not xai_key:
                        raise ValueError("XAI_API_KEY not configured")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        headers = {
                            "Authorization": f"Bearer {xai_key}",
                            "Content-Type": "application/json",
                        }

                        payload = {
                            "model": "grok-4-latest",
                            "messages": [
                                {"role": "system", "content": f"Context: {context}"},
                                {"role": "user", "content": str(input_data)},
                            ],
                            "temperature": 0.3,
                            "max_tokens": 1000,
                        }

                        response = await client.post(
                            "https://api.x.ai/v1/chat/completions",
                            headers=headers,
                            json=payload,
                        )
                        response.raise_for_status()

                        data = response.json()
                        return data["choices"][0]["message"]["content"]

            else:
                raise ValueError(f"Unknown model: {model}")

        except Exception as e:
            logger.error(f"❌ {model.value} execution failed: {e}")
            raise

    async def _try_fallback(
        self,
        task_type: TaskType,
        input_data: Any,
        context: str,
        user_id: Optional[int],
        failed_model: Optional[AIModel] = None,
    ) -> Optional[Dict[str, Any]]:
        """Try fallback models when primary model fails"""

        # Get alternative models (excluding the failed one)
        preferred_models = self.task_routing.get(task_type, [AIModel.GEMINI])
        fallback_models = [m for m in preferred_models if m != failed_model]

        for fallback_model in fallback_models:
            if self._is_model_available(fallback_model):
                try:
                    logger.info(f"🔄 Trying fallback model: {fallback_model.value}")

                    start_time = time.time()
                    result = await self._execute_request(
                        fallback_model, task_type, input_data, context, user_id
                    )
                    execution_time = time.time() - start_time

                    self._update_metrics(fallback_model.value, execution_time, True)

                    return {
                        "response": result,
                        "model_used": fallback_model.value,
                        "execution_time": execution_time,
                        "task_type": task_type.value,
                        "success": True,
                        "fallback": True,
                    }

                except Exception as e:
                    logger.warning(
                        f"⚠️ Fallback model {fallback_model.value} also failed: {e}"
                    )
                    self._update_metrics(fallback_model.value, 0, False)
                    continue

        return None

    def _update_metrics(self, model: str, execution_time: float, success: bool):
        """Update performance metrics for AI models"""
        if model not in self.performance_metrics:
            self.performance_metrics[model] = {
                "calls": 0,
                "avg_time": 0,
                "success_rate": 100,
            }

        metrics = self.performance_metrics[model]
        metrics["calls"] += 1

        if success:
            # Update average execution time
            total_time = metrics["avg_time"] * (metrics["calls"] - 1) + execution_time
            metrics["avg_time"] = total_time / metrics["calls"]
        else:
            # Update success rate
            success_count = int(metrics["success_rate"] * (metrics["calls"] - 1) / 100)
            metrics["success_rate"] = (success_count / metrics["calls"]) * 100

    async def intelligent_response(
        self,
        message: str,
        context: str = "",
        complexity_level: str = "medium",
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Intelligent response generation with automatic task classification
        Used by predictive_engine.py and other advanced features
        """

        # Classify the task based on content
        task_type = self._classify_task(message, context)

        # Route to appropriate AI model
        return await self.route_request(
            task_type=task_type, input_data=message, context=context, user_id=user_id
        )

    def _classify_task(self, message: str, context: str = "") -> TaskType:
        """Classify the type of AI task based on input content"""

        message_lower = message.lower()
        context_lower = context.lower()

        # Vision-related keywords
        if any(
            keyword in message_lower
            for keyword in ["image", "photo", "visual", "camera", "picture", "scan"]
        ):
            return TaskType.VISION

        # Voice command keywords
        if any(
            keyword in context_lower
            for keyword in ["voice", "speech", "audio", "command"]
        ):
            return TaskType.VOICE_COMMAND

        # Predictive maintenance keywords
        if (
            any(
                keyword in message_lower
                for keyword in [
                    "predict",
                    "failure",
                    "maintenance",
                    "health",
                    "forecast",
                    "analysis",
                ]
            )
            or "predictive" in context_lower
        ):
            return TaskType.PREDICTIVE

        # Documentation keywords
        if any(
            keyword in message_lower
            for keyword in [
                "document",
                "report",
                "write",
                "create",
                "generate",
                "explain",
            ]
        ):
            return TaskType.DOCUMENTATION

        # Default to analysis for complex queries
        return TaskType.ANALYSIS

    async def multi_ai_consensus(
        self,
        task: str,
        context: str = "",
        models: Optional[List[AIModel]] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get consensus from multiple AI models for critical decisions
        Useful for high-stakes predictions or important analysis
        """

        if not models:
            models = [AIModel.GEMINI, AIModel.OPENAI]  # Default consensus models

        responses = {}
        tasks = []

        # Query all models simultaneously
        for model in models:
            if self._is_model_available(model):
                task_coroutine = self.route_request(
                    task_type=TaskType.ANALYSIS,
                    input_data=task,
                    context=context,
                    preferred_model=model,
                    user_id=user_id,
                )
                tasks.append((model, task_coroutine))

        # Execute all requests in parallel
        results = await asyncio.gather(
            *[task_coroutine for model, task_coroutine in tasks], return_exceptions=True
        )

        # Process results
        for (model, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ {model.value} consensus failed: {result}")
            else:
                responses[model.value] = result

        return {
            "consensus_responses": responses,
            "models_queried": len(tasks),
            "successful_responses": len(
                [r for r in results if not isinstance(r, Exception)]
            ),
            "task": task,
            "context": context,
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance metrics for all AI models"""
        return {
            "metrics": self.performance_metrics,
            "routing_preferences": {
                task.value: [model.value for model in models]
                for task, models in self.task_routing.items()
            },
            "total_requests": sum(
                m["calls"] for m in self.performance_metrics.values()
            ),
        }


# Global orchestrator instance
ai_orchestrator = AIOrchestrator()
