"""
Intelligent Task Routing System for AI Team Collaboration
Automatically selects the best agents for different task types
with ML-powered classification and routing algorithms
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Classification of different task types"""
    CODING = "coding"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    OPTIMIZATION = "optimization"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    UI_UX = "ui_ux"


@dataclass
class TaskClassification:
    """Result of task classification"""
    primary_type: TaskType
    secondary_types: List[TaskType]
    confidence_score: float
    complexity_level: str  # low, medium, high
    estimated_duration: str  # quick, medium, long
    required_capabilities: List[str]


@dataclass
class AgentScore:
    """Scoring result for an agent"""
    agent_name: str
    score: float
    reasoning: str
    capability_match: float
    performance_history: float
    workload_factor: float


class IntelligentTaskRouter:
    """Advanced task routing system with ML-powered agent selection"""

    def __init__(self):
        # Task classification patterns using regex and keywords
        self.classification_patterns = {
            TaskType.CODING: {
                "keywords": ["code", "implement", "function", "class", "method", "api", "endpoint", "script"],
                "patterns": [
                    r'\b(write|create|implement|code|build|develop)\s+(a\s+)?(function|class|method|api|script|component)',
                    r'\b(fix|debug|correct)\s+(the\s+)?(code|bug|error|issue)',
                    r'\b(add|create|implement)\s+(feature|functionality)',
                ],
                "negative_keywords": ["analyze", "explain", "research", "design only"]
            },
            TaskType.ANALYSIS: {
                "keywords": ["analyze", "examine", "investigate", "review", "assess", "evaluate", "study"],
                "patterns": [
                    r'\b(analyze|examine|investigate|review|assess|evaluate)\s+',
                    r'\bwhat\s+(is|are|does)\b',
                    r'\bhow\s+(does|can|should)\b',
                    r'\bwhy\s+(does|is|are)\b',
                ],
                "negative_keywords": ["implement", "code", "create", "build"]
            },
            TaskType.CREATIVE: {
                "keywords": ["design", "creative", "ui", "ux", "interface", "user experience", "mockup", "prototype"],
                "patterns": [
                    r'\b(design|create|build)\s+(ui|ux|interface|mockup|prototype)',
                    r'\buser\s+(experience|interface)',
                    r'\b(improve|enhance)\s+(design|ui|ux)',
                ],
                "negative_keywords": ["backend", "database", "api only"]
            },
            TaskType.DEBUGGING: {
                "keywords": ["debug", "fix", "error", "bug", "issue", "problem", "troubleshoot"],
                "patterns": [
                    r'\b(fix|debug|resolve|solve|troubleshoot)\s+',
                    r'\b(error|bug|issue|problem)\b',
                    r'\bnot\s+working\b',
                    r'\bfailing\b',
                ],
                "negative_keywords": ["new feature", "enhancement"]
            },
            TaskType.ARCHITECTURE: {
                "keywords": ["architecture", "structure", "design", "pattern", "framework", "system design"],
                "patterns": [
                    r'\b(architecture|structure|design)\s+(pattern|framework|system)',
                    r'\bsystem\s+design\b',
                    r'\bhow\s+to\s+structure\b',
                ],
                "negative_keywords": ["specific implementation"]
            },
            TaskType.OPTIMIZATION: {
                "keywords": ["optimize", "performance", "improve", "enhance", "faster", "efficient"],
                "patterns": [
                    r'\b(optimize|improve|enhance)\s+(performance|speed|efficiency)',
                    r'\bmake\s+(faster|more\s+efficient|better)',
                    r'\bperformance\s+(issue|problem|optimization)',
                ],
                "negative_keywords": ["new feature", "create"]
            },
            TaskType.SECURITY: {
                "keywords": ["security", "authentication", "authorization", "encrypt", "secure", "vulnerability"],
                "patterns": [
                    r'\b(security|authentication|authorization|encryption)\b',
                    r'\bsecure\s+',
                    r'\bvulnerability\b',
                ],
                "negative_keywords": []
            },
            TaskType.TESTING: {
                "keywords": ["test", "testing", "unit test", "integration", "validate"],
                "patterns": [
                    r'\b(test|testing|validate)\s+',
                    r'\bunit\s+test\b',
                    r'\bintegration\s+test\b',
                ],
                "negative_keywords": []
            }
        }

        # Agent capabilities mapping
        self.agent_capabilities = {
            "claude-analyst": {
                "strengths": [TaskType.ANALYSIS, TaskType.ARCHITECTURE, TaskType.RESEARCH],
                "capabilities": ["analysis", "reasoning", "planning", "architecture", "research"],
                "performance_weight": 1.2,  # Higher weight for primary tasks
            },
            "chatgpt-coder": {
                "strengths": [TaskType.CODING, TaskType.DEBUGGING, TaskType.TESTING],
                "capabilities": ["coding", "debugging", "architecture", "testing"],
                "performance_weight": 1.1,
            },
            "gemini-creative": {
                "strengths": [TaskType.CREATIVE, TaskType.UI_UX, TaskType.DOCUMENTATION],
                "capabilities": ["creativity", "design", "innovation", "ui_ux"],
                "performance_weight": 1.0,
            },
            "grok-coder": {
                "strengths": [TaskType.CODING, TaskType.OPTIMIZATION, TaskType.DEBUGGING],
                "capabilities": ["fast-coding", "optimization", "debugging"],
                "performance_weight": 1.3,  # Fastest coder
            },
            "grok-reasoner": {
                "strengths": [TaskType.ANALYSIS, TaskType.ARCHITECTURE, TaskType.RESEARCH],
                "capabilities": ["reasoning", "analysis", "strategy"],
                "performance_weight": 1.1,
            },
        }

        # Performance tracking for adaptive weighting
        self.agent_performance_history = {}
        self.task_routing_history = []

    async def classify_task(self, task_prompt: str, context: str = "") -> TaskClassification:
        """Classify a task using ML-powered analysis"""
        try:
            task_text = f"{task_prompt} {context}".lower()
            
            # Score each task type
            type_scores = {}
            for task_type, config in self.classification_patterns.items():
                score = self._calculate_type_score(task_text, config)
                type_scores[task_type] = score

            # Determine primary and secondary types
            sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
            
            primary_type = sorted_types[0][0]
            primary_score = sorted_types[0][1]
            
            # Get secondary types (score > 0.3 and within 0.5 of primary)
            secondary_types = [
                task_type for task_type, score in sorted_types[1:4]
                if score > 0.3 and (primary_score - score) < 0.5
            ]

            # Determine complexity and duration
            complexity_level = self._assess_complexity(task_text)
            estimated_duration = self._estimate_duration(task_text, complexity_level)
            required_capabilities = self._extract_required_capabilities(task_text, primary_type, secondary_types)

            classification = TaskClassification(
                primary_type=primary_type,
                secondary_types=secondary_types,
                confidence_score=min(primary_score, 1.0),
                complexity_level=complexity_level,
                estimated_duration=estimated_duration,
                required_capabilities=required_capabilities
            )

            logger.info(f"📊 Task classified as {primary_type.value} (confidence: {primary_score:.2f})")
            return classification

        except Exception as e:
            logger.error(f"Failed to classify task: {e}")
            # Return default classification
            return TaskClassification(
                primary_type=TaskType.ANALYSIS,
                secondary_types=[],
                confidence_score=0.5,
                complexity_level="medium",
                estimated_duration="medium",
                required_capabilities=["analysis"]
            )

    async def route_task(self, task_classification: TaskClassification, available_agents: List[str], 
                        performance_history: Dict = None) -> List[str]:
        """Route task to optimal agents based on classification and performance"""
        try:
            agent_scores = []
            
            for agent_name in available_agents:
                if agent_name not in self.agent_capabilities:
                    continue
                
                score = await self._score_agent_for_task(
                    agent_name, task_classification, performance_history or {}
                )
                agent_scores.append(score)

            # Sort by total score
            agent_scores.sort(key=lambda x: x.score, reverse=True)

            # Select optimal team
            selected_agents = self._select_optimal_team(agent_scores, task_classification)
            
            # Log routing decision
            self._log_routing_decision(task_classification, agent_scores, selected_agents)
            
            return selected_agents

        except Exception as e:
            logger.error(f"Failed to route task: {e}")
            # Fallback to all available agents
            return available_agents

    def _calculate_type_score(self, task_text: str, config: Dict) -> float:
        """Calculate score for a task type based on keywords and patterns"""
        score = 0.0
        
        # Keyword matching
        keyword_matches = sum(1 for keyword in config["keywords"] if keyword in task_text)
        if keyword_matches > 0:
            score += min(keyword_matches * 0.2, 0.6)  # Max 0.6 from keywords
        
        # Pattern matching
        pattern_matches = sum(1 for pattern in config["patterns"] if re.search(pattern, task_text))
        if pattern_matches > 0:
            score += min(pattern_matches * 0.3, 0.4)  # Max 0.4 from patterns
        
        # Negative keyword penalty
        negative_matches = sum(1 for neg_keyword in config["negative_keywords"] if neg_keyword in task_text)
        score -= negative_matches * 0.3
        
        return max(score, 0.0)

    def _assess_complexity(self, task_text: str) -> str:
        """Assess task complexity based on text analysis"""
        complexity_indicators = {
            "high": ["complex", "advanced", "comprehensive", "full system", "entire", "complete", "sophisticated"],
            "medium": ["moderate", "standard", "typical", "regular", "normal"],
            "low": ["simple", "basic", "quick", "small", "minor", "easy"]
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in task_text for indicator in indicators):
                return level
        
        # Default based on length and technical terms
        technical_terms = ["api", "database", "architecture", "framework", "integration", "deployment"]
        tech_count = sum(1 for term in technical_terms if term in task_text)
        
        if len(task_text.split()) > 30 and tech_count > 3:
            return "high"
        elif len(task_text.split()) > 15 and tech_count > 1:
            return "medium"
        else:
            return "low"

    def _estimate_duration(self, task_text: str, complexity: str) -> str:
        """Estimate task duration"""
        duration_indicators = {
            "quick": ["quick", "fast", "immediate", "simple", "small"],
            "long": ["comprehensive", "complete", "full", "entire", "complex"]
        }
        
        for duration, indicators in duration_indicators.items():
            if any(indicator in task_text for indicator in indicators):
                return duration
        
        # Default based on complexity
        if complexity == "high":
            return "long"
        elif complexity == "low":
            return "quick"
        else:
            return "medium"

    def _extract_required_capabilities(self, task_text: str, primary_type: TaskType, 
                                     secondary_types: List[TaskType]) -> List[str]:
        """Extract required capabilities from task"""
        capabilities = set()
        
        # Add capabilities based on task types
        type_to_capabilities = {
            TaskType.CODING: ["coding", "programming", "implementation"],
            TaskType.ANALYSIS: ["analysis", "reasoning", "investigation"],
            TaskType.CREATIVE: ["creativity", "design", "innovation"],
            TaskType.DEBUGGING: ["debugging", "troubleshooting", "problem-solving"],
            TaskType.ARCHITECTURE: ["architecture", "system-design", "planning"],
            TaskType.OPTIMIZATION: ["optimization", "performance", "efficiency"],
            TaskType.SECURITY: ["security", "authentication", "encryption"],
            TaskType.TESTING: ["testing", "validation", "quality-assurance"]
        }
        
        capabilities.update(type_to_capabilities.get(primary_type, []))
        for secondary_type in secondary_types:
            capabilities.update(type_to_capabilities.get(secondary_type, []))
        
        # Add specific capabilities from text
        if "api" in task_text:
            capabilities.add("api-development")
        if "database" in task_text:
            capabilities.add("database")
        if "ui" in task_text or "interface" in task_text:
            capabilities.add("ui-development")
        if "deployment" in task_text:
            capabilities.add("deployment")
        
        return list(capabilities)

    async def _score_agent_for_task(self, agent_name: str, classification: TaskClassification, 
                                  performance_history: Dict) -> AgentScore:
        """Score an agent for a specific task"""
        agent_config = self.agent_capabilities[agent_name]
        
        # Capability match score (0.0 - 1.0)
        capability_score = self._calculate_capability_match(agent_config, classification)
        
        # Performance history score (0.0 - 1.0)
        performance_score = self._calculate_performance_score(agent_name, performance_history, classification)
        
        # Workload factor (0.5 - 1.0, lower means agent is busy)
        workload_score = self._calculate_workload_factor(agent_name)
        
        # Weighted total score
        total_score = (
            capability_score * 0.5 +
            performance_score * 0.3 +
            workload_score * 0.2
        ) * agent_config["performance_weight"]
        
        reasoning = f"Cap:{capability_score:.2f} Perf:{performance_score:.2f} Load:{workload_score:.2f}"
        
        return AgentScore(
            agent_name=agent_name,
            score=total_score,
            reasoning=reasoning,
            capability_match=capability_score,
            performance_history=performance_score,
            workload_factor=workload_score
        )

    def _calculate_capability_match(self, agent_config: Dict, classification: TaskClassification) -> float:
        """Calculate how well agent capabilities match task requirements"""
        score = 0.0
        
        # Primary task type match
        if classification.primary_type in agent_config["strengths"]:
            score += 0.6  # Strong match for primary task
        
        # Secondary task type match
        for secondary_type in classification.secondary_types:
            if secondary_type in agent_config["strengths"]:
                score += 0.2  # Bonus for secondary matches
        
        # Capability match
        required_caps = set(classification.required_capabilities)
        agent_caps = set(agent_config["capabilities"])
        
        if required_caps:
            cap_match_ratio = len(required_caps & agent_caps) / len(required_caps)
            score += cap_match_ratio * 0.4
        
        return min(score, 1.0)

    def _calculate_performance_score(self, agent_name: str, performance_history: Dict, 
                                   classification: TaskClassification) -> float:
        """Calculate agent performance score based on historical data"""
        if agent_name not in performance_history:
            return 0.7  # Default score for new agents
        
        agent_perf = performance_history[agent_name]
        
        # Base performance metrics
        success_rate = agent_perf.get("successful_tasks", 0) / max(agent_perf.get("total_tasks", 1), 1)
        avg_confidence = agent_perf.get("average_confidence", 0.5)
        
        # Task-type specific performance (if available)
        task_type_perf = agent_perf.get("task_type_performance", {})
        type_specific_score = task_type_perf.get(classification.primary_type.value, success_rate)
        
        # Weighted score
        performance_score = (
            success_rate * 0.4 +
            avg_confidence * 0.3 +
            type_specific_score * 0.3
        )
        
        return min(performance_score, 1.0)

    def _calculate_workload_factor(self, agent_name: str) -> float:
        """Calculate current workload factor for agent (simplified)"""
        # In a real implementation, this would check current active tasks
        # For now, return a default good score
        return 0.9

    def _select_optimal_team(self, agent_scores: List[AgentScore], classification: TaskClassification) -> List[str]:
        """Select optimal team of agents based on scores and task requirements"""
        if not agent_scores:
            return []
        
        selected = []
        
        # Always select the top agent
        selected.append(agent_scores[0].agent_name)
        
        # Determine team size based on task complexity
        max_team_size = {
            "low": 2,
            "medium": 3,
            "high": 4
        }.get(classification.complexity_level, 3)
        
        # Add additional agents if they have good scores
        for agent_score in agent_scores[1:max_team_size]:
            if agent_score.score > 0.5:  # Only add if reasonably capable
                selected.append(agent_score.agent_name)
        
        # Ensure we have at least 2 agents for collaboration
        if len(selected) < 2 and len(agent_scores) > 1:
            selected.append(agent_scores[1].agent_name)
        
        return selected

    def _log_routing_decision(self, classification: TaskClassification, agent_scores: List[AgentScore], 
                            selected: List[str]):
        """Log the routing decision for learning and debugging"""
        decision_log = {
            "task_type": classification.primary_type.value,
            "complexity": classification.complexity_level,
            "confidence": classification.confidence_score,
            "agent_scores": {score.agent_name: score.score for score in agent_scores},
            "selected_agents": selected
        }
        
        self.task_routing_history.append(decision_log)
        
        logger.info(f"🎯 Route: {classification.primary_type.value} -> {selected}")
        for score in agent_scores[:3]:  # Log top 3
            logger.info(f"   {score.agent_name}: {score.score:.2f} ({score.reasoning})")

    async def update_performance_feedback(self, task_id: str, agent_name: str, 
                                        task_type: TaskType, success: bool, confidence: float):
        """Update agent performance based on task feedback"""
        try:
            if agent_name not in self.agent_performance_history:
                self.agent_performance_history[agent_name] = {
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "average_confidence": 0.0,
                    "task_type_performance": {}
                }
            
            perf = self.agent_performance_history[agent_name]
            perf["total_tasks"] += 1
            
            if success:
                perf["successful_tasks"] += 1
            
            # Update average confidence
            perf["average_confidence"] = (
                (perf["average_confidence"] * (perf["total_tasks"] - 1) + confidence) / 
                perf["total_tasks"]
            )
            
            # Update task-type specific performance
            task_type_key = task_type.value
            if task_type_key not in perf["task_type_performance"]:
                perf["task_type_performance"][task_type_key] = 0.0
            
            # Simple moving average for task-type performance
            current_type_perf = perf["task_type_performance"][task_type_key]
            perf["task_type_performance"][task_type_key] = (
                (current_type_perf * 0.8) + (confidence * 0.2)
            ) if success else (current_type_perf * 0.9)
            
            logger.info(f"📈 Updated performance for {agent_name}: {perf}")
            
        except Exception as e:
            logger.error(f"Failed to update performance feedback: {e}")

    def get_routing_analytics(self) -> Dict:
        """Get analytics about task routing performance"""
        try:
            if not self.task_routing_history:
                return {"message": "No routing history available"}
            
            # Analyze routing patterns
            task_type_counts = {}
            complexity_distribution = {}
            agent_selection_frequency = {}
            
            for decision in self.task_routing_history:
                # Task type distribution
                task_type = decision["task_type"]
                task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
                
                # Complexity distribution
                complexity = decision["complexity"]
                complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
                
                # Agent selection frequency
                for agent in decision["selected_agents"]:
                    agent_selection_frequency[agent] = agent_selection_frequency.get(agent, 0) + 1
            
            analytics = {
                "total_routings": len(self.task_routing_history),
                "task_type_distribution": task_type_counts,
                "complexity_distribution": complexity_distribution,
                "agent_selection_frequency": agent_selection_frequency,
                "agent_performance_history": self.agent_performance_history,
                "routing_effectiveness": self._calculate_routing_effectiveness()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get routing analytics: {e}")
            return {"error": str(e)}

    def _calculate_routing_effectiveness(self) -> Dict:
        """Calculate effectiveness metrics for routing decisions"""
        if not self.agent_performance_history:
            return {"average_success_rate": 0.0, "average_confidence": 0.0}
        
        total_tasks = sum(perf.get("total_tasks", 0) for perf in self.agent_performance_history.values())
        total_successful = sum(perf.get("successful_tasks", 0) for perf in self.agent_performance_history.values())
        total_confidence = sum(
            perf.get("average_confidence", 0) * perf.get("total_tasks", 0) 
            for perf in self.agent_performance_history.values()
        )
        
        return {
            "average_success_rate": total_successful / max(total_tasks, 1),
            "average_confidence": total_confidence / max(total_tasks, 1),
            "total_tasks_routed": total_tasks
        }


# Global router instance
_task_router = None

def get_task_router() -> IntelligentTaskRouter:
    """Get the global task router instance"""
    global _task_router
    if _task_router is None:
        _task_router = IntelligentTaskRouter()
    return _task_router