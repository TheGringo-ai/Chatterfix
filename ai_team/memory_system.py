"""
Advanced Memory System for AI Development Platform
Captures all conversations, code changes, mistakes, and solutions
Never repeat a mistake twice - Comprehensive learning system
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)


class MistakeType(Enum):
    CODE_ERROR = "code_error"
    ARCHITECTURE_FLAW = "architecture_flaw"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"
    DEPLOYMENT_FAILURE = "deployment_failure"
    LOGIC_ERROR = "logic_error"
    INTEGRATION_ISSUE = "integration_issue"
    USER_EXPERIENCE_PROBLEM = "user_experience_problem"


class OutcomeRating(Enum):
    EXCELLENT = 5
    GOOD = 4
    SATISFACTORY = 3
    POOR = 2
    FAILURE = 1


@dataclass
class ConversationRecord:
    conversation_id: str
    timestamp: datetime
    ai_models_involved: List[str]
    user_prompt: str
    ai_responses: List[Dict[str, Any]]
    context_data: Dict[str, Any]
    project_context: str
    outcome_rating: OutcomeRating
    lessons_learned: List[str]
    mistakes_identified: List[Dict[str, Any]]
    solution_patterns: List[Dict[str, Any]]


@dataclass
class CodeChangeRecord:
    change_id: str
    timestamp: datetime
    files_modified: List[str]
    change_description: str
    ai_reasoning: str
    before_after_diff: str
    test_results: Dict[str, Any]
    performance_impact: Dict[str, Any]
    bug_fixes_applied: List[str]
    architectural_decisions: List[Dict[str, Any]]


@dataclass
class MistakePattern:
    mistake_id: str
    mistake_type: MistakeType
    description: str
    when_occurred: datetime
    context: Dict[str, Any]
    how_detected: str
    resolution_steps: List[str]
    prevention_strategy: str
    related_conversations: List[str]
    impact_severity: str
    tags: List[str]


@dataclass
class SolutionKnowledge:
    solution_id: str
    problem_pattern: str
    solution_steps: List[str]
    success_rate: float
    applications_used_in: List[str]
    performance_metrics: Dict[str, Any]
    best_practices: List[str]
    contraindications: List[str]


class ComprehensiveMemorySystem:
    """Advanced memory system that captures all development activities and learns from them"""

    def __init__(self):
        self.db = self._initialize_firestore()
        self.conversation_collection = "ai_conversations"
        self.code_changes_collection = "code_changes"
        self.mistake_patterns_collection = "mistake_patterns"
        self.solution_knowledge_collection = "solution_knowledge_base"

    def _initialize_firestore(self):
        """Initialize Firestore database connection"""
        try:
            # Check if Firebase is already initialized
            try:
                firebase_admin.get_app()
            except ValueError:
                # Initialize Firebase if not already done
                cred_path = os.getenv(
                    "GOOGLE_APPLICATION_CREDENTIALS", "secrets/firebase-admin.json"
                )
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    logger.warning(
                        "Firebase credentials not found, using default credentials"
                    )
                    firebase_admin.initialize_app()

            return firestore.client()
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            raise

    def generate_id(self, content: str) -> str:
        """Generate a unique ID based on content hash"""
        return hashlib.sha256(f"{content}{time.time()}".encode()).hexdigest()[:16]

    async def capture_conversation(
        self,
        user_prompt: str,
        ai_responses: List[Dict[str, Any]],
        context_data: Dict[str, Any],
        project_context: str = "ChatterFix",
    ) -> str:
        """Capture a complete conversation with AI models"""
        try:
            conversation_id = self.generate_id(user_prompt)

            # Extract AI models involved
            ai_models = [resp.get("model", "unknown") for resp in ai_responses]

            conversation = ConversationRecord(
                conversation_id=conversation_id,
                timestamp=datetime.now(timezone.utc),
                ai_models_involved=ai_models,
                user_prompt=user_prompt,
                ai_responses=ai_responses,
                context_data=context_data,
                project_context=project_context,
                outcome_rating=OutcomeRating.SATISFACTORY,  # Default, can be updated
                lessons_learned=[],
                mistakes_identified=[],
                solution_patterns=[],
            )

            # Store in Firestore
            doc_ref = self.db.collection(self.conversation_collection).document(
                conversation_id
            )
            doc_ref.set(asdict(conversation))

            logger.info(f"📝 Captured conversation {conversation_id}")
            return conversation_id

        except Exception as e:
            logger.error(f"Failed to capture conversation: {e}")
            return ""

    async def capture_code_change(
        self,
        files_modified: List[str],
        change_description: str,
        ai_reasoning: str,
        before_after_diff: str,
        test_results: Optional[Dict] = None,
        performance_impact: Optional[Dict] = None,
    ) -> str:
        """Capture a code change with full context"""
        try:
            change_id = self.generate_id(change_description)

            code_change = CodeChangeRecord(
                change_id=change_id,
                timestamp=datetime.now(timezone.utc),
                files_modified=files_modified,
                change_description=change_description,
                ai_reasoning=ai_reasoning,
                before_after_diff=before_after_diff,
                test_results=test_results or {},
                performance_impact=performance_impact or {},
                bug_fixes_applied=[],
                architectural_decisions=[],
            )

            # Store in Firestore
            doc_ref = self.db.collection(self.code_changes_collection).document(
                change_id
            )
            doc_ref.set(asdict(code_change))

            logger.info(f"🔧 Captured code change {change_id}")
            return change_id

        except Exception as e:
            logger.error(f"Failed to capture code change: {e}")
            return ""

    async def capture_mistake(
        self,
        mistake_type: MistakeType,
        description: str,
        context: Dict[str, Any],
        how_detected: str,
        resolution_steps: List[str],
        impact_severity: str = "medium",
    ) -> str:
        """Capture a mistake pattern to prevent future occurrences"""
        try:
            mistake_id = self.generate_id(description)

            mistake = MistakePattern(
                mistake_id=mistake_id,
                mistake_type=mistake_type,
                description=description,
                when_occurred=datetime.now(timezone.utc),
                context=context,
                how_detected=how_detected,
                resolution_steps=resolution_steps,
                prevention_strategy="",  # To be filled by AI analysis
                related_conversations=[],
                impact_severity=impact_severity,
                tags=[],
            )

            # Store in Firestore
            doc_ref = self.db.collection(self.mistake_patterns_collection).document(
                mistake_id
            )
            doc_ref.set(asdict(mistake))

            logger.warning(f"❌ Captured mistake pattern {mistake_id}: {description}")

            # Generate prevention strategy using AI team
            await self._generate_prevention_strategy(mistake_id, mistake)

            return mistake_id

        except Exception as e:
            logger.error(f"Failed to capture mistake: {e}")
            return ""

    async def capture_solution(
        self,
        problem_pattern: str,
        solution_steps: List[str],
        success_rate: float,
        application: str,
        performance_metrics: Optional[Dict] = None,
    ) -> str:
        """Capture a successful solution pattern"""
        try:
            solution_id = self.generate_id(problem_pattern)

            solution = SolutionKnowledge(
                solution_id=solution_id,
                problem_pattern=problem_pattern,
                solution_steps=solution_steps,
                success_rate=success_rate,
                applications_used_in=[application],
                performance_metrics=performance_metrics or {},
                best_practices=[],
                contraindications=[],
            )

            # Store in Firestore
            doc_ref = self.db.collection(self.solution_knowledge_collection).document(
                solution_id
            )
            doc_ref.set(asdict(solution))

            logger.info(f"✅ Captured solution pattern {solution_id}")
            return solution_id

        except Exception as e:
            logger.error(f"Failed to capture solution: {e}")
            return ""

    async def find_similar_mistakes(
        self, context: Dict[str, Any]
    ) -> List[MistakePattern]:
        """Find similar mistakes that might be repeating"""
        try:
            # Search by similar context or tags
            mistakes_ref = self.db.collection(self.mistake_patterns_collection)

            # Basic search - can be enhanced with vector similarity
            docs = mistakes_ref.limit(50).stream()

            similar_mistakes = []
            for doc in docs:
                mistake_data = doc.to_dict()
                # Simple similarity check - can be enhanced with ML
                if self._is_context_similar(context, mistake_data.get("context", {})):
                    similar_mistakes.append(MistakePattern(**mistake_data))

            return similar_mistakes

        except Exception as e:
            logger.error(f"Failed to find similar mistakes: {e}")
            return []

    async def find_solution_patterns(
        self, problem_description: str
    ) -> List[SolutionKnowledge]:
        """Find solution patterns for similar problems"""
        try:
            solutions_ref = self.db.collection(self.solution_knowledge_collection)

            # Search for solutions with similar problem patterns
            docs = solutions_ref.limit(20).stream()

            matching_solutions = []
            for doc in docs:
                solution_data = doc.to_dict()
                # Simple text matching - can be enhanced with semantic search
                if self._is_problem_similar(
                    problem_description, solution_data.get("problem_pattern", "")
                ):
                    matching_solutions.append(SolutionKnowledge(**solution_data))

            # Sort by success rate
            matching_solutions.sort(key=lambda x: x.success_rate, reverse=True)

            return matching_solutions

        except Exception as e:
            logger.error(f"Failed to find solution patterns: {e}")
            return []

    async def get_conversation_history(
        self, project_context: str = None, ai_model: str = None, days_back: int = 30
    ) -> List[ConversationRecord]:
        """Get conversation history with optional filters"""
        try:
            conversations_ref = self.db.collection(self.conversation_collection)

            # Apply filters
            query = conversations_ref

            if project_context:
                query = query.where("project_context", "==", project_context)

            # Time filter
            from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            query = query.where("timestamp", ">=", from_date)

            # Order by timestamp
            query = query.order_by("timestamp", direction=firestore.Query.DESCENDING)

            docs = query.limit(100).stream()

            conversations = []
            for doc in docs:
                conv_data = doc.to_dict()
                # Filter by AI model if specified
                if ai_model and ai_model not in conv_data.get("ai_models_involved", []):
                    continue

                conversations.append(ConversationRecord(**conv_data))

            return conversations

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def analyze_development_patterns(
        self, application: str = "ChatterFix"
    ) -> Dict[str, Any]:
        """Analyze patterns across all captured data for an application"""
        try:
            analysis = {
                "total_conversations": 0,
                "total_code_changes": 0,
                "total_mistakes": 0,
                "total_solutions": 0,
                "common_mistake_types": {},
                "successful_solution_patterns": [],
                "ai_model_performance": {},
                "learning_trends": {},
                "recommendations": [],
            }

            # Analyze conversations
            conversations = await self.get_conversation_history(
                project_context=application
            )
            analysis["total_conversations"] = len(conversations)

            # Analyze AI model performance
            for conv in conversations:
                for model in conv.ai_models_involved:
                    if model not in analysis["ai_model_performance"]:
                        analysis["ai_model_performance"][model] = {
                            "total_interactions": 0,
                            "average_rating": 0,
                            "success_count": 0,
                        }

                    perf = analysis["ai_model_performance"][model]
                    perf["total_interactions"] += 1
                    perf["average_rating"] = (
                        perf["average_rating"] + conv.outcome_rating.value
                    ) / perf["total_interactions"]

                    if conv.outcome_rating.value >= 4:
                        perf["success_count"] += 1

            # Analyze mistakes
            mistakes_ref = self.db.collection(self.mistake_patterns_collection)
            mistakes_docs = mistakes_ref.limit(100).stream()

            for doc in mistakes_docs:
                mistake_data = doc.to_dict()
                analysis["total_mistakes"] += 1

                mistake_type = mistake_data.get("mistake_type", "unknown")
                if mistake_type not in analysis["common_mistake_types"]:
                    analysis["common_mistake_types"][mistake_type] = 0
                analysis["common_mistake_types"][mistake_type] += 1

            # Generate recommendations
            analysis["recommendations"] = await self._generate_recommendations(analysis)

            logger.info(f"📊 Generated development pattern analysis for {application}")
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze development patterns: {e}")
            return {}

    def _is_context_similar(self, context1: Dict, context2: Dict) -> bool:
        """Check if two contexts are similar (simple implementation)"""
        # Simple similarity check - can be enhanced with ML
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return False

        similarity_score = 0
        for key in common_keys:
            if (
                str(context1[key]).lower() in str(context2[key]).lower()
                or str(context2[key]).lower() in str(context1[key]).lower()
            ):
                similarity_score += 1

        return similarity_score >= len(common_keys) * 0.5

    def _is_problem_similar(self, problem1: str, problem2: str) -> bool:
        """Check if two problems are similar (simple implementation)"""
        # Simple text similarity - can be enhanced with semantic analysis
        words1 = set(problem1.lower().split())
        words2 = set(problem2.lower().split())

        common_words = words1 & words2
        total_words = words1 | words2

        if not total_words:
            return False

        similarity = len(common_words) / len(total_words)
        return similarity > 0.3

    async def _generate_prevention_strategy(
        self, mistake_id: str, mistake: MistakePattern
    ):
        """Generate prevention strategy using AI team"""
        try:
            from .autogen_framework import get_orchestrator

            orchestrator = get_orchestrator()

            prompt = f"""
            A mistake has been detected and needs a prevention strategy:
            
            Type: {mistake.mistake_type.value}
            Description: {mistake.description}
            Context: {json.dumps(mistake.context, indent=2)}
            How detected: {mistake.how_detected}
            Resolution steps: {json.dumps(mistake.resolution_steps, indent=2)}
            
            Generate a comprehensive prevention strategy that includes:
            1. Code patterns to avoid
            2. Best practices to follow
            3. Automated checks to implement
            4. Warning signs to watch for
            
            Focus on preventing this exact type of mistake from occurring again.
            """

            result = await orchestrator.execute_collaborative_task(
                task_id=f"prevention_{mistake_id}",
                prompt=prompt,
                context="Mistake prevention analysis",
            )

            if result.success:
                # Update the mistake record with prevention strategy
                doc_ref = self.db.collection(self.mistake_patterns_collection).document(
                    mistake_id
                )
                doc_ref.update({"prevention_strategy": result.final_answer})

                logger.info(f"🛡️ Generated prevention strategy for mistake {mistake_id}")

        except Exception as e:
            logger.error(f"Failed to generate prevention strategy: {e}")

    async def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate development recommendations based on analysis"""
        recommendations = []

        # Check mistake patterns
        if analysis["common_mistake_types"]:
            top_mistake = max(
                analysis["common_mistake_types"].items(), key=lambda x: x[1]
            )
            recommendations.append(
                f"Focus on preventing {top_mistake[0]} mistakes - they account for {top_mistake[1]} occurrences"
            )

        # Check AI model performance
        if analysis["ai_model_performance"]:
            best_model = max(
                analysis["ai_model_performance"].items(),
                key=lambda x: x[1].get("average_rating", 0),
            )
            recommendations.append(
                f"Consider using {best_model[0]} more often - it has the highest success rate"
            )

        # General recommendations
        if analysis["total_mistakes"] > analysis["total_solutions"]:
            recommendations.append(
                "Capture more successful solution patterns to build knowledge base"
            )

        return recommendations


# Global memory system instance
_memory_system = None


def get_memory_system() -> ComprehensiveMemorySystem:
    """Get the global memory system instance"""
    global _memory_system
    if _memory_system is None:
        _memory_system = ComprehensiveMemorySystem()
    return _memory_system


class MistakePrevention:
    """Advanced mistake prevention system"""

    def __init__(self):
        self.memory_system = get_memory_system()
        self.risk_threshold = 0.7

    async def analyze_current_action(
        self, action_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze current development action for potential mistakes"""
        try:
            similar_mistakes = await self.memory_system.find_similar_mistakes(
                action_context
            )

            if similar_mistakes:
                risk_assessment = await self._assess_risk(
                    action_context, similar_mistakes
                )

                if risk_assessment["risk_level"] >= self.risk_threshold:
                    return await self._generate_prevention_guidance(
                        similar_mistakes, action_context
                    )

            return None

        except Exception as e:
            logger.error(f"Failed to analyze current action: {e}")
            return None

    async def _assess_risk(
        self, action_context: Dict, similar_mistakes: List[MistakePattern]
    ) -> Dict[str, Any]:
        """Assess risk level of current action"""
        total_risk = 0
        high_severity_count = 0

        for mistake in similar_mistakes:
            if (
                mistake.impact_severity == "high"
                or mistake.impact_severity == "critical"
            ):
                high_severity_count += 1
                total_risk += 0.8
            elif mistake.impact_severity == "medium":
                total_risk += 0.5
            else:
                total_risk += 0.3

        average_risk = total_risk / len(similar_mistakes) if similar_mistakes else 0

        return {
            "risk_level": min(average_risk, 1.0),
            "similar_mistake_count": len(similar_mistakes),
            "high_severity_count": high_severity_count,
            "recommendation": (
                "high_caution"
                if average_risk > 0.7
                else "moderate_caution" if average_risk > 0.4 else "low_risk"
            ),
        }

    async def _generate_prevention_guidance(
        self, similar_mistakes: List[MistakePattern], action_context: Dict
    ) -> Dict[str, Any]:
        """Generate prevention guidance based on similar mistakes"""
        guidance = {
            "warning_level": "HIGH",
            "message": f"⚠️ DETECTED {len(similar_mistakes)} SIMILAR PAST MISTAKES",
            "prevention_steps": [],
            "alternative_approaches": [],
            "risk_factors": [],
            "similar_mistakes": [],
        }

        for mistake in similar_mistakes[:3]:  # Top 3 most relevant
            guidance["similar_mistakes"].append(
                {
                    "description": mistake.description,
                    "when_occurred": mistake.when_occurred.isoformat(),
                    "resolution_steps": mistake.resolution_steps,
                    "prevention_strategy": mistake.prevention_strategy,
                }
            )

            guidance["prevention_steps"].extend(mistake.resolution_steps)

            if mistake.prevention_strategy:
                guidance["alternative_approaches"].append(mistake.prevention_strategy)

        return guidance


class ProactiveDevelopmentAssistant:
    """Proactive development assistant that anticipates issues and suggests improvements"""

    def __init__(self):
        self.memory_system = get_memory_system()
        self.mistake_prevention = MistakePrevention()

    async def anticipate_issues(
        self, development_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Anticipate issues before they happen based on historical patterns"""
        try:
            # Check for potential mistake patterns
            prevention_guidance = await self.mistake_prevention.analyze_current_action(
                development_context
            )

            if prevention_guidance:
                return {
                    "type": "mistake_prevention",
                    "urgency": "high",
                    "guidance": prevention_guidance,
                }

            # Check for optimization opportunities
            optimization_suggestions = await self._suggest_optimizations(
                development_context
            )

            if optimization_suggestions:
                return {
                    "type": "optimization",
                    "urgency": "medium",
                    "suggestions": optimization_suggestions,
                }

            return None

        except Exception as e:
            logger.error(f"Failed to anticipate issues: {e}")
            return None

    async def _suggest_optimizations(
        self, development_context: Dict[str, Any]
    ) -> Optional[List[str]]:
        """Suggest optimizations based on past successful patterns"""
        try:
            # Find successful solution patterns
            context_description = json.dumps(development_context)
            solution_patterns = await self.memory_system.find_solution_patterns(
                context_description
            )

            suggestions = []
            for pattern in solution_patterns[:3]:  # Top 3 solutions
                if pattern.success_rate > 0.8:  # Only high-success patterns
                    suggestions.extend(pattern.best_practices)

            return list(set(suggestions)) if suggestions else None

        except Exception as e:
            logger.error(f"Failed to suggest optimizations: {e}")
            return None


# Global instances
_mistake_prevention = None
_proactive_assistant = None


def get_mistake_prevention() -> MistakePrevention:
    """Get the global mistake prevention instance"""
    global _mistake_prevention
    if _mistake_prevention is None:
        _mistake_prevention = MistakePrevention()
    return _mistake_prevention


def get_proactive_assistant() -> ProactiveDevelopmentAssistant:
    """Get the global proactive development assistant"""
    global _proactive_assistant
    if _proactive_assistant is None:
        _proactive_assistant = ProactiveDevelopmentAssistant()
    return _proactive_assistant
