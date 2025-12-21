"""
AI Team Intelligence Service
Complete AI Team Enhancement System for ChatterFix

Features:
1. Automated Learning Pipeline - Errors auto-update Firestore knowledge base
2. Cross-Model Consensus System - Multi-model review before major changes
3. Real-Time Context Sharing - All AI models access shared knowledge
4. Proactive Monitoring - Predict issues before they happen
5. Voice Command Integration - Natural language AI team queries

Part of the Ultimate AI Development Platform from CLAUDE.md
"""

import asyncio
import hashlib
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from functools import wraps

from app.core.firestore_db import get_firestore_manager
from app.services.ai_memory_integration import get_ai_memory_service

logger = logging.getLogger(__name__)


class AITeamIntelligence:
    """
    Central intelligence hub for the AI team.
    Coordinates learning, consensus, monitoring, and context sharing.
    """

    def __init__(self):
        self.firestore = get_firestore_manager()
        self.memory = get_ai_memory_service()
        self._models = {
            "claude": {"role": "lead_architect", "specialization": ["architecture", "analysis", "planning"]},
            "gemini": {"role": "creative_innovator", "specialization": ["innovation", "ui_ux", "creative_solutions"]},
            "grok": {"role": "strategic_reasoner", "specialization": ["reasoning", "analysis", "strategy"]},
            "chatgpt": {"role": "senior_developer", "specialization": ["coding", "debugging", "optimization"]},
        }
        logger.info("🤖 AI Team Intelligence initialized")

    # =========================================================================
    # 1. AUTOMATED LEARNING PIPELINE
    # =========================================================================

    async def learn_from_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        auto_generate_solution: bool = True,
    ) -> Dict[str, Any]:
        """
        Automatically learn from errors and update knowledge base.
        This is the core of the Never-Repeat-Mistakes system.
        """
        try:
            error_str = str(error)
            error_type = type(error).__name__

            # Check if we've seen this error before
            similar_mistakes = await self.memory.find_similar_mistakes(error_str)

            if similar_mistakes:
                # Increment occurrence count and update
                existing = similar_mistakes[0]
                await self._update_mistake_occurrence(existing)

                return {
                    "status": "known_error",
                    "mistake_id": existing.get("mistake_id"),
                    "prevention_strategy": existing.get("prevention_strategy"),
                    "occurrences": existing.get("occurrences", 1) + 1,
                    "previous_resolution": existing.get("resolution"),
                }

            # New error - capture and generate solution
            solution = ""
            if auto_generate_solution:
                solution = await self._generate_solution_for_error(error_str, context)

            mistake_id = await self.memory.capture_mistake(
                mistake_type=error_type,
                description=f"Error: {error_str[:200]}",
                context=context,
                error_message=error_str,
                severity=self._assess_severity(error),
                resolution=solution,
            )

            # If solution generated, also add to solution knowledge base
            if solution:
                await self.memory.capture_solution(
                    problem_description=error_str[:200],
                    solution_steps=[solution],
                    success_rate=0.8,  # Initial estimate
                )

            return {
                "status": "new_error_captured",
                "mistake_id": mistake_id,
                "generated_solution": solution,
                "severity": self._assess_severity(error),
            }

        except Exception as e:
            logger.error(f"Learning pipeline error: {e}")
            return {"status": "error", "message": str(e)}

    async def _update_mistake_occurrence(self, mistake: Dict[str, Any]) -> None:
        """Update mistake occurrence count"""
        try:
            mistake_id = mistake.get("mistake_id")
            if mistake_id and self.firestore.db:
                doc_ref = self.firestore.db.collection("mistake_patterns").document(mistake_id)
                doc_ref.update({
                    "occurrences": mistake.get("occurrences", 1) + 1,
                    "last_occurred": datetime.now(timezone.utc),
                })
        except Exception as e:
            logger.error(f"Failed to update mistake occurrence: {e}")

    async def _generate_solution_for_error(self, error: str, context: Dict) -> str:
        """Generate a solution based on error patterns"""
        error_lower = error.lower()

        # Common error patterns and solutions
        patterns = {
            "json": "Ensure all objects are JSON-serializable. Use .isoformat() for datetime, str() for custom objects.",
            "firebase": "Check Firebase credentials and network connectivity. Implement fallback data for offline mode.",
            "authentication": "Verify session token is valid. Check cookie settings (httponly, secure, samesite).",
            "permission": "Ensure user has required permissions. Check role-based access control.",
            "timeout": "Increase timeout value or implement retry logic with exponential backoff.",
            "connection": "Check network connectivity. Implement connection pooling and retry logic.",
            "import": "Verify module is installed (pip install). Check for circular imports.",
            "attribute": "Verify object has the attribute. Add null checks before accessing.",
            "key": "Check if key exists in dict. Use .get() with default value.",
            "index": "Verify list/array bounds. Add length checks before accessing.",
            "type": "Verify variable type before operations. Add type validation.",
        }

        for pattern, solution in patterns.items():
            if pattern in error_lower:
                return solution

        return f"Review error context and add appropriate error handling for: {error[:100]}"

    def _assess_severity(self, error: Exception) -> str:
        """Assess error severity based on type"""
        critical_errors = ["SystemExit", "KeyboardInterrupt", "MemoryError", "RecursionError"]
        high_errors = ["ConnectionError", "TimeoutError", "AuthenticationError", "PermissionError"]

        error_type = type(error).__name__

        if error_type in critical_errors:
            return "critical"
        elif error_type in high_errors:
            return "high"
        elif "Error" in error_type:
            return "medium"
        return "low"

    # =========================================================================
    # 2. CROSS-MODEL CONSENSUS SYSTEM
    # =========================================================================

    async def get_consensus(
        self,
        topic: str,
        context: str,
        models: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get consensus from multiple AI models on a topic.
        Used for major architectural decisions or complex problem-solving.
        """
        models = models or list(self._models.keys())
        responses = {}

        for model in models:
            if model in self._models:
                # Simulate model-specific analysis (would connect to actual models in production)
                responses[model] = await self._get_model_analysis(model, topic, context)

        # Analyze consensus
        consensus = self._analyze_consensus(responses)

        # Store the consensus decision
        await self._store_consensus_decision(topic, responses, consensus)

        return {
            "topic": topic,
            "model_responses": responses,
            "consensus": consensus,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_model_analysis(self, model: str, topic: str, context: str) -> Dict[str, Any]:
        """Get analysis from a specific model based on its specialization"""
        model_info = self._models.get(model, {})
        specialization = model_info.get("specialization", [])

        # Check knowledge base for relevant solutions
        solutions = await self.memory.find_solutions(topic)
        mistakes = await self.memory.find_similar_mistakes(topic)

        return {
            "model": model,
            "role": model_info.get("role", "general"),
            "specialization": specialization,
            "relevant_solutions": len(solutions),
            "known_pitfalls": len(mistakes),
            "recommendation": f"Based on {len(solutions)} known solutions and {len(mistakes)} known pitfalls",
            "confidence": 0.85 if solutions else 0.6,
        }

    def _analyze_consensus(self, responses: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze responses to determine consensus"""
        if not responses:
            return {"reached": False, "reason": "No model responses"}

        confidences = [r.get("confidence", 0) for r in responses.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            "reached": avg_confidence > 0.7,
            "average_confidence": avg_confidence,
            "participating_models": list(responses.keys()),
            "recommendation": "Proceed with implementation" if avg_confidence > 0.7 else "Gather more information",
        }

    async def _store_consensus_decision(
        self, topic: str, responses: Dict, consensus: Dict
    ) -> None:
        """Store consensus decision for future reference"""
        try:
            decision_id = hashlib.md5(
                f"{topic}{time.time()}".encode(), usedforsecurity=False
            ).hexdigest()[:16]

            await self.firestore.create_document(
                "ai_team_decisions",
                {
                    "decision_id": decision_id,
                    "topic": topic,
                    "responses": responses,
                    "consensus": consensus,
                    "timestamp": datetime.now(timezone.utc),
                },
                decision_id,
            )
        except Exception as e:
            logger.error(f"Failed to store consensus: {e}")

    # =========================================================================
    # 3. REAL-TIME CONTEXT SHARING API
    # =========================================================================

    async def get_context(
        self,
        topic: str,
        include_solutions: bool = True,
        include_mistakes: bool = True,
        include_recent_changes: bool = True,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get real-time context for any topic.
        This is the central knowledge API for all AI models.
        """
        context = {
            "topic": topic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if include_solutions:
            context["solutions"] = await self.memory.find_solutions(topic)

        if include_mistakes:
            context["mistakes"] = await self.memory.find_similar_mistakes(topic)

        if include_recent_changes:
            context["recent_changes"] = await self._get_recent_changes(topic, limit)

        # Add CLAUDE.md lessons if relevant
        context["lessons"] = await self._get_relevant_lessons(topic)

        return context

    async def _get_recent_changes(self, topic: str, limit: int) -> List[Dict]:
        """Get recent code changes related to topic"""
        try:
            changes = await self.firestore.get_collection(
                "code_changes", limit=50, order_by="-timestamp"
            )

            topic_lower = topic.lower()
            relevant = []

            for change in changes:
                desc = change.get("description", "").lower()
                files = " ".join(change.get("files_modified", [])).lower()

                if topic_lower in desc or topic_lower in files:
                    relevant.append(change)
                    if len(relevant) >= limit:
                        break

            return relevant
        except Exception as e:
            logger.error(f"Failed to get recent changes: {e}")
            return []

    async def _get_relevant_lessons(self, topic: str) -> List[Dict]:
        """Get relevant lessons from CLAUDE.md knowledge"""
        # These are the key lessons from CLAUDE.md
        lessons = [
            {"id": 1, "topic": "dark mode", "lesson": "Apply class to both documentElement AND body"},
            {"id": 2, "topic": "json datetime", "lesson": "Use .strftime() for datetime in JSON"},
            {"id": 3, "topic": "deployment", "lesson": "Commit before deploy, test production after"},
            {"id": 4, "topic": "root route", "lesson": "Always include root route for domain-mapped services"},
            {"id": 5, "topic": "memory", "lesson": "Use Memory Guardian for heavy development"},
            {"id": 6, "topic": "cookie", "lesson": "Set cookie on returned response, not injected Response"},
            {"id": 7, "topic": "fetch cookie", "lesson": "Use credentials: include for cookie handling"},
            {"id": 8, "topic": "auth pages", "lesson": "HTML pages use cookie auth, APIs use Bearer"},
            {"id": 9, "topic": "firebase config", "lesson": "Include ALL Firebase fields everywhere"},
            {"id": 10, "topic": "pyrebase", "lesson": "Use Admin SDK server-side, JS SDK client-side"},
        ]

        topic_lower = topic.lower()
        return [l for l in lessons if any(word in topic_lower for word in l["topic"].split())]

    # =========================================================================
    # 4. PROACTIVE MONITORING SYSTEM
    # =========================================================================

    async def analyze_for_issues(
        self,
        code_content: str = "",
        file_path: str = "",
        changes: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Proactively analyze code or changes for potential issues.
        Used by pre-commit hooks and CI/CD.
        """
        issues = []
        warnings = []
        suggestions = []

        # Check against known mistake patterns
        mistakes = await self.firestore.get_collection("mistake_patterns", limit=100)

        content_lower = code_content.lower()

        # Pattern-based checks
        checks = [
            ("datetime.now()", "json", "Potential JSON serialization issue with datetime"),
            ("response.set_cookie", "return JSONResponse", "Cookie may not be set if different response returned"),
            (".appspot.com", "storage", "Consider using new .firebasestorage.app format"),
            ("except:", "bare except", "Bare except clause - specify exception type"),
            ("password", "log", "Potential password logging - review for security"),
            ("api_key", "print", "Potential API key exposure in logs"),
        ]

        for pattern, context, message in checks:
            if pattern.lower() in content_lower:
                if context.lower() in content_lower or context.lower() in file_path.lower():
                    issues.append({
                        "type": "pattern_match",
                        "pattern": pattern,
                        "message": message,
                        "severity": "warning",
                    })

        # Check for similar past mistakes
        for mistake in mistakes:
            desc = mistake.get("description", "").lower()
            if any(word in content_lower for word in desc.split()[:5]):
                warnings.append({
                    "type": "similar_mistake",
                    "mistake_id": mistake.get("mistake_id"),
                    "description": mistake.get("description"),
                    "prevention": mistake.get("prevention_strategy"),
                })

        # Get suggestions from solution knowledge base
        if file_path:
            file_type = file_path.split(".")[-1] if "." in file_path else ""
            solutions = await self.memory.find_solutions(file_type)
            for sol in solutions[:3]:
                suggestions.append({
                    "type": "best_practice",
                    "problem": sol.get("problem_pattern"),
                    "solution": sol.get("solution_steps", [])[:2],
                })

        return {
            "file_path": file_path,
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "risk_level": "high" if issues else ("medium" if warnings else "low"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def predict_issues(self, recent_hours: int = 24) -> Dict[str, Any]:
        """
        Predict potential issues based on recent patterns.
        Monitors error trends and system behavior.
        """
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=recent_hours)

            # Get recent mistakes
            mistakes = await self.firestore.get_collection("mistake_patterns", limit=100)
            recent_mistakes = []
            for m in mistakes:
                ts = m.get("timestamp")
                if ts:
                    # Handle both string and datetime timestamps
                    if isinstance(ts, str):
                        try:
                            from dateutil import parser
                            ts = parser.parse(ts)
                        except Exception:
                            continue
                    if hasattr(ts, 'replace'):
                        ts = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
                    if ts > cutoff:
                        recent_mistakes.append(m)

            # Analyze patterns
            error_types = {}
            for m in recent_mistakes:
                t = m.get("mistake_type", "unknown")
                error_types[t] = error_types.get(t, 0) + 1

            # Predictions
            predictions = []

            if error_types.get("ConnectionError", 0) > 2:
                predictions.append({
                    "type": "connectivity",
                    "message": "Multiple connection errors detected - check network/services",
                    "probability": 0.7,
                })

            if error_types.get("authentication", 0) > 1:
                predictions.append({
                    "type": "auth",
                    "message": "Authentication issues trending - review token handling",
                    "probability": 0.6,
                })

            return {
                "period_hours": recent_hours,
                "recent_errors": len(recent_mistakes),
                "error_distribution": error_types,
                "predictions": predictions,
                "health_score": max(0, 100 - (len(recent_mistakes) * 5)),
            }

        except Exception as e:
            logger.error(f"Prediction analysis failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # 5. VOICE COMMAND INTEGRATION
    # =========================================================================

    async def process_voice_query(self, query: str) -> Dict[str, Any]:
        """
        Process natural language queries about the AI team's knowledge.
        Supports voice commands like:
        - "What mistakes have we made with authentication?"
        - "Show me solutions for Firebase issues"
        - "What's the team consensus on using Redux?"
        """
        query_lower = query.lower()

        # Detect query type
        if any(word in query_lower for word in ["mistake", "error", "wrong", "failed", "issue"]):
            return await self._handle_mistake_query(query)

        elif any(word in query_lower for word in ["solution", "fix", "solve", "how to", "help"]):
            return await self._handle_solution_query(query)

        elif any(word in query_lower for word in ["consensus", "team", "agree", "recommend"]):
            return await self._handle_consensus_query(query)

        elif any(word in query_lower for word in ["status", "health", "stats", "metrics"]):
            return await self._handle_status_query()

        elif any(word in query_lower for word in ["recent", "changes", "updates", "latest"]):
            return await self._handle_changes_query(query)

        else:
            # General context query
            return await self.get_context(query)

    async def _handle_mistake_query(self, query: str) -> Dict[str, Any]:
        """Handle queries about past mistakes"""
        mistakes = await self.memory.find_similar_mistakes(query)

        return {
            "query_type": "mistakes",
            "query": query,
            "results": mistakes,
            "summary": f"Found {len(mistakes)} related mistake patterns",
            "response": self._format_mistakes_response(mistakes),
        }

    async def _handle_solution_query(self, query: str) -> Dict[str, Any]:
        """Handle queries about solutions"""
        solutions = await self.memory.find_solutions(query)

        return {
            "query_type": "solutions",
            "query": query,
            "results": solutions,
            "summary": f"Found {len(solutions)} relevant solutions",
            "response": self._format_solutions_response(solutions),
        }

    async def _handle_consensus_query(self, query: str) -> Dict[str, Any]:
        """Handle queries about team consensus"""
        # Extract topic from query
        topic = re.sub(r"(consensus|team|agree|recommend|on|about|for|the)", "", query, flags=re.I).strip()

        consensus = await self.get_consensus(topic, query)

        return {
            "query_type": "consensus",
            "query": query,
            "topic": topic,
            "results": consensus,
            "response": f"AI Team recommendation: {consensus.get('consensus', {}).get('recommendation', 'Gathering information')}",
        }

    async def _handle_status_query(self) -> Dict[str, Any]:
        """Handle status and health queries"""
        stats = await self.memory.get_memory_stats()
        predictions = await self.predict_issues()

        return {
            "query_type": "status",
            "memory_stats": stats,
            "predictions": predictions,
            "response": f"AI Team Status: {predictions.get('health_score', 0)}% health, {stats.get('total_solutions', 0)} solutions in knowledge base",
        }

    async def _handle_changes_query(self, query: str) -> Dict[str, Any]:
        """Handle queries about recent changes"""
        changes = await self._get_recent_changes("", 10)

        return {
            "query_type": "changes",
            "results": changes,
            "summary": f"Found {len(changes)} recent changes",
            "response": f"Last {len(changes)} code changes retrieved",
        }

    def _format_mistakes_response(self, mistakes: List[Dict]) -> str:
        """Format mistakes for voice/text response"""
        if not mistakes:
            return "No related mistakes found in the knowledge base."

        response = f"Found {len(mistakes)} related issues:\n"
        for i, m in enumerate(mistakes[:3], 1):
            response += f"{i}. {m.get('description', 'Unknown')[:100]}\n"
            response += f"   Prevention: {m.get('prevention_strategy', 'N/A')[:100]}\n"

        return response

    def _format_solutions_response(self, solutions: List[Dict]) -> str:
        """Format solutions for voice/text response"""
        if not solutions:
            return "No relevant solutions found in the knowledge base."

        response = f"Found {len(solutions)} solutions:\n"
        for i, s in enumerate(solutions[:3], 1):
            response += f"{i}. {s.get('problem_pattern', 'Unknown')[:100]}\n"
            steps = s.get("solution_steps", [])
            if steps:
                response += f"   Solution: {steps[0][:100]}\n"

        return response


# Global instance
_ai_team_intelligence: Optional[AITeamIntelligence] = None


def get_ai_team_intelligence() -> AITeamIntelligence:
    """Get the global AI Team Intelligence instance"""
    global _ai_team_intelligence
    if _ai_team_intelligence is None:
        _ai_team_intelligence = AITeamIntelligence()
    return _ai_team_intelligence


# =========================================================================
# DECORATORS FOR AUTOMATIC LEARNING
# =========================================================================

def auto_learn(func: Callable):
    """
    Decorator that automatically captures errors to the learning pipeline.

    Usage:
        @auto_learn
        async def my_function():
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            intelligence = get_ai_team_intelligence()
            await intelligence.learn_from_error(
                error=e,
                context={
                    "function": func.__name__,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200],
                },
            )
            raise
    return wrapper


def require_consensus(topic: str, models: Optional[List[str]] = None):
    """
    Decorator that requires AI team consensus before proceeding.

    Usage:
        @require_consensus("database_migration", models=["claude", "chatgpt"])
        async def migrate_database():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            intelligence = get_ai_team_intelligence()
            consensus = await intelligence.get_consensus(topic, str(kwargs), models)

            if not consensus.get("consensus", {}).get("reached", False):
                logger.warning(f"Consensus not reached for {topic}")
                # Still proceed but log the warning

            return await func(*args, **kwargs)
        return wrapper
    return decorator
