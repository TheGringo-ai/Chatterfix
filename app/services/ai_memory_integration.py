"""
AI Memory Integration Service
Captures all AI interactions, mistakes, and solutions to Firestore
Part of the Never-Repeat-Mistakes system from CLAUDE.md
"""

import hashlib
import logging
import time
import traceback
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


class AIMemoryService:
    """
    Centralized AI Memory Service that captures:
    - All AI conversations and interactions
    - Mistake patterns for prevention
    - Successful solutions for reuse
    - Code changes and their outcomes
    """

    def __init__(self):
        self.firestore = get_firestore_manager()
        self._session_id = self._generate_session_id()
        logger.info(f"🧠 AI Memory Service initialized - Session: {self._session_id}")

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return hashlib.md5(f"{time.time()}".encode(), usedforsecurity=False).hexdigest()[:12]

    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content"""
        return hashlib.md5(f"{content}{time.time()}".encode(), usedforsecurity=False).hexdigest()[:16]

    async def capture_interaction(
        self,
        user_message: str,
        ai_response: str,
        model: str = "unknown",
        context: str = "",
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Capture an AI interaction to memory"""
        try:
            interaction_id = self._generate_id(user_message)

            interaction_data = {
                "interaction_id": interaction_id,
                "session_id": self._session_id,
                "user_message": user_message,
                "ai_response": ai_response,
                "model": model,
                "context": context,
                "success": success,
                "timestamp": datetime.now(timezone.utc),
                "application": "ChatterFix",
                "metadata": metadata or {},
            }

            await self.firestore.create_document(
                "ai_conversations", interaction_data, interaction_id
            )

            logger.info(f"🧠 Captured interaction: {interaction_id}")
            return interaction_id

        except Exception as e:
            logger.error(f"Failed to capture interaction: {e}")
            return ""

    async def capture_mistake(
        self,
        mistake_type: str,
        description: str,
        context: Dict[str, Any],
        error_message: str = "",
        stack_trace: str = "",
        severity: str = "medium",
        resolution: str = "",
    ) -> str:
        """Capture a mistake pattern to prevent future occurrences"""
        try:
            mistake_id = self._generate_id(description)

            # Generate prevention strategy
            prevention_strategy = self._generate_prevention_strategy(
                mistake_type, description, error_message
            )

            mistake_data = {
                "mistake_id": mistake_id,
                "mistake_type": mistake_type,
                "description": description,
                "context": context,
                "error_message": error_message,
                "stack_trace": stack_trace[:2000] if stack_trace else "",  # Limit size
                "severity": severity,
                "prevention_strategy": prevention_strategy,
                "resolution": resolution,
                "occurrences": 1,
                "timestamp": datetime.now(timezone.utc),
                "application": "ChatterFix",
                "resolved": bool(resolution),
            }

            await self.firestore.create_document(
                "mistake_patterns", mistake_data, mistake_id
            )

            logger.warning(f"🚨 Captured mistake pattern: {mistake_id} - {description[:50]}")
            return mistake_id

        except Exception as e:
            logger.error(f"Failed to capture mistake: {e}")
            return ""

    async def capture_solution(
        self,
        problem_description: str,
        solution_steps: List[str],
        code_template: str = "",
        success_rate: float = 1.0,
        performance_impact: str = "",
    ) -> str:
        """Capture a successful solution pattern"""
        try:
            solution_id = self._generate_id(problem_description)

            solution_data = {
                "solution_id": solution_id,
                "problem_pattern": problem_description,
                "solution_steps": solution_steps,
                "code_template": code_template,
                "success_rate": success_rate,
                "performance_impact": performance_impact,
                "applications_used": ["ChatterFix"],
                "timestamp": datetime.now(timezone.utc),
                "verified": True,
            }

            await self.firestore.create_document(
                "solution_knowledge_base", solution_data, solution_id
            )

            logger.info(f"💡 Captured solution: {solution_id}")
            return solution_id

        except Exception as e:
            logger.error(f"Failed to capture solution: {e}")
            return ""

    async def capture_code_change(
        self,
        files_modified: List[str],
        description: str,
        ai_reasoning: str = "",
        diff: str = "",
        test_results: Optional[Dict] = None,
    ) -> str:
        """Capture a code change with context"""
        try:
            change_id = self._generate_id(description)

            change_data = {
                "change_id": change_id,
                "files_modified": files_modified,
                "description": description,
                "ai_reasoning": ai_reasoning,
                "diff": diff[:5000] if diff else "",  # Limit size
                "test_results": test_results or {},
                "timestamp": datetime.now(timezone.utc),
                "application": "ChatterFix",
                "session_id": self._session_id,
            }

            await self.firestore.create_document(
                "code_changes", change_data, change_id
            )

            logger.info(f"📝 Captured code change: {change_id}")
            return change_id

        except Exception as e:
            logger.error(f"Failed to capture code change: {e}")
            return ""

    async def find_similar_mistakes(self, context: str) -> List[Dict]:
        """Find similar mistakes from history to prevent repetition"""
        try:
            mistakes = await self.firestore.get_collection(
                "mistake_patterns",
                limit=20,
                order_by="-timestamp"
            )

            # Simple keyword matching (can be enhanced with ML)
            context_lower = context.lower()
            similar = []

            for mistake in mistakes:
                desc = mistake.get("description", "").lower()
                error_msg = mistake.get("error_message", "").lower()

                # Check for keyword overlap
                if any(word in context_lower for word in desc.split()[:10]):
                    similar.append(mistake)
                elif any(word in context_lower for word in error_msg.split()[:5]):
                    similar.append(mistake)

            return similar[:5]  # Return top 5 matches

        except Exception as e:
            logger.error(f"Failed to find similar mistakes: {e}")
            return []

    async def find_solutions(self, problem: str) -> List[Dict]:
        """Find relevant solutions from knowledge base"""
        try:
            solutions = await self.firestore.get_collection(
                "solution_knowledge_base",
                limit=20,
                order_by="-timestamp"
            )

            problem_lower = problem.lower()
            matching = []

            for solution in solutions:
                pattern = solution.get("problem_pattern", "").lower()

                if any(word in problem_lower for word in pattern.split()[:10]):
                    matching.append(solution)

            # Sort by success rate
            matching.sort(key=lambda x: x.get("success_rate", 0), reverse=True)
            return matching[:5]

        except Exception as e:
            logger.error(f"Failed to find solutions: {e}")
            return []

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the AI memory system"""
        try:
            conversations = await self.firestore.get_collection("ai_conversations", limit=1000)
            mistakes = await self.firestore.get_collection("mistake_patterns", limit=1000)
            solutions = await self.firestore.get_collection("solution_knowledge_base", limit=1000)
            code_changes = await self.firestore.get_collection("code_changes", limit=1000)

            return {
                "total_conversations": len(conversations),
                "total_mistakes": len(mistakes),
                "total_solutions": len(solutions),
                "total_code_changes": len(code_changes),
                "session_id": self._session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}

    def _generate_prevention_strategy(
        self, mistake_type: str, description: str, error_message: str
    ) -> str:
        """Generate a prevention strategy based on the mistake"""
        strategies = {
            "json_serialization": "Always use .strftime() for datetime objects before JSON responses",
            "deployment": "Commit all changes before deployment; test production immediately after",
            "theme_toggle": "Apply dark-mode class to both documentElement AND body",
            "firebase": "Add proper fallback data for Firebase connection failures",
            "api_error": "Add proper error handling and validation for API endpoints",
            "authentication": "Verify user session and permissions before protected operations",
            "database": "Use parameterized queries and proper connection handling",
        }

        # Check for known patterns
        desc_lower = description.lower()
        error_lower = error_message.lower()

        if "datetime" in desc_lower or "json" in error_lower:
            return strategies["json_serialization"]
        elif "deploy" in desc_lower:
            return strategies["deployment"]
        elif "theme" in desc_lower or "dark" in desc_lower:
            return strategies["theme_toggle"]
        elif "firebase" in desc_lower or "firestore" in error_lower:
            return strategies["firebase"]
        elif "api" in mistake_type.lower():
            return strategies["api_error"]
        elif "auth" in desc_lower:
            return strategies["authentication"]
        elif "database" in desc_lower or "query" in desc_lower:
            return strategies["database"]

        return f"Review and add validation for: {description[:100]}"


# Global instance
_ai_memory_service: Optional[AIMemoryService] = None


def get_ai_memory_service() -> AIMemoryService:
    """Get the global AI memory service instance"""
    global _ai_memory_service
    if _ai_memory_service is None:
        _ai_memory_service = AIMemoryService()
    return _ai_memory_service


def with_memory_capture(model: str = "unknown"):
    """
    Decorator to automatically capture AI interactions to memory

    Usage:
        @with_memory_capture(model="gemini")
        async def generate_response(message: str) -> str:
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            memory = get_ai_memory_service()

            # Extract message from args/kwargs
            message = kwargs.get("message") or kwargs.get("prompt") or (args[0] if args else "")
            context = kwargs.get("context", "")

            try:
                result = await func(*args, **kwargs)

                # Capture successful interaction
                await memory.capture_interaction(
                    user_message=str(message)[:1000],
                    ai_response=str(result)[:2000] if result else "",
                    model=model,
                    context=str(context)[:500],
                    success=True,
                )

                return result

            except Exception as e:
                # Capture the mistake
                await memory.capture_mistake(
                    mistake_type="ai_error",
                    description=f"AI function {func.__name__} failed",
                    context={"message": str(message)[:500], "function": func.__name__},
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    severity="medium",
                )
                raise

        return wrapper
    return decorator


def capture_error(mistake_type: str = "runtime_error", severity: str = "medium"):
    """
    Decorator to capture errors as mistake patterns

    Usage:
        @capture_error(mistake_type="api_error", severity="high")
        async def api_endpoint():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                memory = get_ai_memory_service()
                await memory.capture_mistake(
                    mistake_type=mistake_type,
                    description=f"Error in {func.__name__}: {str(e)}",
                    context={"function": func.__name__, "args": str(args)[:200]},
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    severity=severity,
                )
                raise

        return wrapper
    return decorator
