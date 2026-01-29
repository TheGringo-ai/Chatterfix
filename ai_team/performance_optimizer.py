"""
Advanced Performance Optimization System for AI Team Collaboration
Implements intelligent caching, agent warm-up, response quality scoring,
and adaptive performance optimizations for the autogen framework
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import pickle
import os

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Different caching strategies"""
    EXACT_MATCH = "exact_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    PATTERN_MATCH = "pattern_match"
    HYBRID = "hybrid"


class QualityDimension(Enum):
    """Quality assessment dimensions"""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    INNOVATION = "innovation"
    PRACTICALITY = "practicality"
    EFFICIENCY = "efficiency"


@dataclass
class CachedResponse:
    """Cached AI response with metadata"""
    cache_key: str
    response: str
    agent_name: str
    model_type: str
    timestamp: datetime
    quality_score: float
    usage_count: int = 0
    context_hash: str = ""
    tags: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityAssessment:
    """Quality assessment result"""
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    reasoning: str
    improvement_suggestions: List[str]
    confidence: float


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    response_time: float
    cache_hit_rate: float
    quality_score: float
    agent_efficiency: float
    memory_usage: float
    concurrent_tasks: int
    timestamp: datetime


@dataclass
class AgentWarmupState:
    """Agent warm-up state tracking"""
    agent_name: str
    last_used: datetime
    warmup_level: float  # 0.0 to 1.0
    avg_response_time: float
    recent_tasks: List[str]
    is_warmed_up: bool = False


class AdvancedResponseCache:
    """Advanced caching system with multiple strategies"""

    def __init__(self, cache_dir: str = "/tmp/ai_team_cache"):
        self.cache_dir = cache_dir
        self.memory_cache = {}  # In-memory cache for hot data
        self.cache_strategy = CacheStrategy.HYBRID
        self.max_memory_cache_size = 1000
        self.cache_hit_stats = {"hits": 0, "misses": 0}
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

    def generate_cache_key(self, prompt: str, context: str, agent_name: str, 
                          strategy: CacheStrategy = None) -> str:
        """Generate cache key based on strategy"""
        strategy = strategy or self.cache_strategy
        
        if strategy == CacheStrategy.EXACT_MATCH:
            # Exact string match
            content = f"{prompt}_{context}_{agent_name}".strip()
        
        elif strategy == CacheStrategy.SEMANTIC_SIMILARITY:
            # Normalize for semantic similarity
            content = self._normalize_for_similarity(prompt, context, agent_name)
        
        elif strategy == CacheStrategy.PATTERN_MATCH:
            # Extract patterns and key elements
            content = self._extract_patterns(prompt, context, agent_name)
        
        else:  # HYBRID
            # Combine multiple approaches
            exact = f"{prompt}_{context}_{agent_name}".strip()
            semantic = self._normalize_for_similarity(prompt, context, agent_name)
            pattern = self._extract_patterns(prompt, context, agent_name)
            content = f"{exact}|{semantic}|{pattern}"
        
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _normalize_for_similarity(self, prompt: str, context: str, agent_name: str) -> str:
        """Normalize text for semantic similarity matching"""
        # Remove non-essential words and normalize
        import re
        
        combined = f"{prompt} {context}".lower()
        # Remove punctuation and extra whitespace
        combined = re.sub(r'[^\w\s]', ' ', combined)
        combined = re.sub(r'\s+', ' ', combined).strip()
        
        # Remove common stop words that don't affect meaning
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        words = [w for w in combined.split() if w not in stop_words]
        
        return f"{' '.join(sorted(words))}_{agent_name}"

    def _extract_patterns(self, prompt: str, context: str, agent_name: str) -> str:
        """Extract key patterns from prompt for pattern matching"""
        import re
        
        combined = f"{prompt} {context}".lower()
        
        # Extract key patterns
        patterns = []
        
        # Technical terms
        tech_terms = re.findall(r'\b(?:api|database|function|class|method|component|system|framework|library)\b', combined)
        patterns.extend(tech_terms)
        
        # Action words
        actions = re.findall(r'\b(?:create|build|implement|fix|debug|analyze|design|optimize|test|deploy)\b', combined)
        patterns.extend(actions)
        
        # Domain-specific terms
        domains = re.findall(r'\b(?:frontend|backend|ui|ux|security|performance|authentication)\b', combined)
        patterns.extend(domains)
        
        return f"{' '.join(sorted(set(patterns)))}_{agent_name}"

    async def get_cached_response(self, cache_key: str) -> Optional[CachedResponse]:
        """Retrieve cached response"""
        try:
            # Check memory cache first
            if cache_key in self.memory_cache:
                cached = self.memory_cache[cache_key]
                cached.usage_count += 1
                self.cache_hit_stats["hits"] += 1
                logger.info(f"💾 Cache HIT (memory): {cache_key[:8]}")
                return cached
            
            # Check disk cache
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                    cached.usage_count += 1
                    
                    # Promote to memory cache
                    self._promote_to_memory_cache(cache_key, cached)
                    
                    self.cache_hit_stats["hits"] += 1
                    logger.info(f"💾 Cache HIT (disk): {cache_key[:8]}")
                    return cached
            
            self.cache_hit_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")
            return None

    async def store_cached_response(self, cache_key: str, response: str, agent_name: str,
                                  model_type: str, quality_score: float, 
                                  context_hash: str = "", tags: List[str] = None) -> bool:
        """Store response in cache"""
        try:
            cached_response = CachedResponse(
                cache_key=cache_key,
                response=response,
                agent_name=agent_name,
                model_type=model_type,
                timestamp=datetime.now(timezone.utc),
                quality_score=quality_score,
                context_hash=context_hash,
                tags=tags or [],
                performance_metrics={}
            )
            
            # Store in memory cache
            self._add_to_memory_cache(cache_key, cached_response)
            
            # Store in disk cache
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_response, f)
            
            logger.info(f"💾 Cached response: {cache_key[:8]} (quality: {quality_score:.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing cached response: {e}")
            return False

    def _add_to_memory_cache(self, cache_key: str, cached_response: CachedResponse):
        """Add to memory cache with LRU eviction"""
        # Remove oldest items if cache is full
        if len(self.memory_cache) >= self.max_memory_cache_size:
            # Remove 20% of oldest items
            items_to_remove = len(self.memory_cache) // 5
            oldest_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].timestamp
            )[:items_to_remove]
            
            for key, _ in oldest_items:
                del self.memory_cache[key]
        
        self.memory_cache[cache_key] = cached_response

    def _promote_to_memory_cache(self, cache_key: str, cached_response: CachedResponse):
        """Promote frequently used items to memory cache"""
        if cached_response.usage_count > 2:  # Promote if used more than twice
            self._add_to_memory_cache(cache_key, cached_response)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hit_stats["hits"] + self.cache_hit_stats["misses"]
        hit_rate = self.cache_hit_stats["hits"] / max(total_requests, 1)
        
        return {
            "hit_rate": hit_rate,
            "total_hits": self.cache_hit_stats["hits"],
            "total_misses": self.cache_hit_stats["misses"],
            "memory_cache_size": len(self.memory_cache),
            "cache_strategy": self.cache_strategy.value,
            "cache_effectiveness": hit_rate * 100
        }

    async def cleanup_expired_cache(self, max_age_hours: int = 24):
        """Clean up expired cache entries"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            
            # Clean memory cache
            expired_keys = [
                key for key, cached in self.memory_cache.items()
                if cached.timestamp < cutoff_time
            ]
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Clean disk cache
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'rb') as f:
                            cached = pickle.load(f)
                            if cached.timestamp < cutoff_time:
                                os.remove(filepath)
                    except Exception:
                        # Remove corrupted files
                        os.remove(filepath)
            
            logger.info(f"🧹 Cache cleanup completed, removed {len(expired_keys)} expired entries")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")


class ResponseQualityAssessor:
    """Advanced quality assessment for AI responses"""

    def __init__(self):
        self.quality_patterns = {
            QualityDimension.ACCURACY: {
                "positive_indicators": ["correct", "accurate", "precise", "verified", "validated"],
                "negative_indicators": ["incorrect", "wrong", "inaccurate", "false", "error"],
                "structure_indicators": ["step by step", "detailed explanation", "specific examples"]
            },
            QualityDimension.COMPLETENESS: {
                "positive_indicators": ["comprehensive", "complete", "thorough", "detailed", "full"],
                "negative_indicators": ["incomplete", "partial", "missing", "vague", "unclear"],
                "length_threshold": 100  # Minimum response length
            },
            QualityDimension.RELEVANCE: {
                "context_match_threshold": 0.7,
                "topic_coherence": True,
                "off_topic_indicators": ["unrelated", "off topic", "not relevant"]
            },
            QualityDimension.CLARITY: {
                "positive_indicators": ["clear", "simple", "understandable", "explained well"],
                "negative_indicators": ["confusing", "unclear", "complicated", "hard to understand"],
                "structure_score": True
            },
            QualityDimension.INNOVATION: {
                "creative_indicators": ["innovative", "creative", "novel", "unique", "original"],
                "standard_indicators": ["standard", "typical", "common", "usual"],
                "improvement_suggestions": True
            },
            QualityDimension.PRACTICALITY: {
                "actionable_indicators": ["practical", "actionable", "implementable", "usable"],
                "theoretical_indicators": ["theoretical", "abstract", "conceptual only"],
                "code_examples": True
            }
        }

    async def assess_quality(self, response: str, original_prompt: str, 
                           context: str = "", agent_name: str = "") -> QualityAssessment:
        """Comprehensive quality assessment of AI response"""
        try:
            dimension_scores = {}
            improvement_suggestions = []
            
            # Assess each quality dimension
            for dimension in QualityDimension:
                score, suggestions = await self._assess_dimension(
                    dimension, response, original_prompt, context
                )
                dimension_scores[dimension] = score
                improvement_suggestions.extend(suggestions)
            
            # Calculate overall score with weighted dimensions
            weights = {
                QualityDimension.ACCURACY: 0.25,
                QualityDimension.COMPLETENESS: 0.20,
                QualityDimension.RELEVANCE: 0.20,
                QualityDimension.CLARITY: 0.15,
                QualityDimension.PRACTICALITY: 0.15,
                QualityDimension.INNOVATION: 0.05
            }
            
            overall_score = sum(
                dimension_scores[dim] * weights.get(dim, 0.1)
                for dim in dimension_scores
            )
            
            # Generate reasoning
            reasoning = self._generate_quality_reasoning(dimension_scores, agent_name)
            
            # Calculate confidence based on consistency of scores
            score_variance = self._calculate_score_variance(list(dimension_scores.values()))
            confidence = max(0.5, 1.0 - score_variance)
            
            return QualityAssessment(
                overall_score=min(overall_score, 1.0),
                dimension_scores=dimension_scores,
                reasoning=reasoning,
                improvement_suggestions=list(set(improvement_suggestions)),
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing response quality: {e}")
            return QualityAssessment(
                overall_score=0.5,
                dimension_scores={dim: 0.5 for dim in QualityDimension},
                reasoning=f"Quality assessment failed: {str(e)}",
                improvement_suggestions=[],
                confidence=0.5
            )

    async def _assess_dimension(self, dimension: QualityDimension, response: str,
                              prompt: str, context: str) -> Tuple[float, List[str]]:
        """Assess a specific quality dimension"""
        patterns = self.quality_patterns.get(dimension, {})
        score = 0.5  # Default score
        suggestions = []
        
        response_lower = response.lower()
        
        if dimension == QualityDimension.ACCURACY:
            score = self._assess_accuracy(response_lower, patterns)
            if score < 0.6:
                suggestions.append("Verify accuracy of claims and provide sources")
        
        elif dimension == QualityDimension.COMPLETENESS:
            score = self._assess_completeness(response, patterns)
            if score < 0.6:
                suggestions.append("Provide more detailed explanation and examples")
        
        elif dimension == QualityDimension.RELEVANCE:
            score = self._assess_relevance(response_lower, prompt.lower(), patterns)
            if score < 0.6:
                suggestions.append("Focus more on the specific question asked")
        
        elif dimension == QualityDimension.CLARITY:
            score = self._assess_clarity(response, patterns)
            if score < 0.6:
                suggestions.append("Improve structure and use clearer language")
        
        elif dimension == QualityDimension.INNOVATION:
            score = self._assess_innovation(response_lower, patterns)
            if score < 0.4:
                suggestions.append("Consider more creative or innovative approaches")
        
        elif dimension == QualityDimension.PRACTICALITY:
            score = self._assess_practicality(response, patterns)
            if score < 0.6:
                suggestions.append("Provide more actionable steps and practical examples")
        
        return score, suggestions

    def _assess_accuracy(self, response: str, patterns: Dict) -> float:
        """Assess response accuracy"""
        positive_count = sum(1 for indicator in patterns["positive_indicators"] if indicator in response)
        negative_count = sum(1 for indicator in patterns["negative_indicators"] if indicator in response)
        structure_count = sum(1 for indicator in patterns["structure_indicators"] if indicator in response)
        
        score = 0.5 + (positive_count * 0.1) + (structure_count * 0.1) - (negative_count * 0.2)
        return max(0.0, min(1.0, score))

    def _assess_completeness(self, response: str, patterns: Dict) -> float:
        """Assess response completeness"""
        # Length factor
        length_score = min(len(response) / patterns.get("length_threshold", 100), 1.0) * 0.4
        
        # Content indicators
        positive_count = sum(1 for indicator in patterns["positive_indicators"] if indicator in response.lower())
        negative_count = sum(1 for indicator in patterns["negative_indicators"] if indicator in response.lower())
        
        content_score = 0.3 + (positive_count * 0.1) - (negative_count * 0.15)
        
        return max(0.0, min(1.0, length_score + content_score))

    def _assess_relevance(self, response: str, prompt: str, patterns: Dict) -> float:
        """Assess response relevance to prompt"""
        # Simple word overlap
        response_words = set(response.split())
        prompt_words = set(prompt.split())
        
        if prompt_words:
            overlap_ratio = len(response_words & prompt_words) / len(prompt_words)
        else:
            overlap_ratio = 0.5
        
        # Off-topic penalty
        off_topic_count = sum(1 for indicator in patterns["off_topic_indicators"] if indicator in response)
        
        score = overlap_ratio - (off_topic_count * 0.2)
        return max(0.0, min(1.0, score))

    def _assess_clarity(self, response: str, patterns: Dict) -> float:
        """Assess response clarity"""
        response_lower = response.lower()
        
        positive_count = sum(1 for indicator in patterns["positive_indicators"] if indicator in response_lower)
        negative_count = sum(1 for indicator in patterns["negative_indicators"] if indicator in response_lower)
        
        # Structure assessment (simplified)
        has_structure = any(marker in response for marker in ["1.", "2.", "3.", "•", "-", "Step"])
        structure_bonus = 0.2 if has_structure else 0
        
        score = 0.5 + (positive_count * 0.1) - (negative_count * 0.15) + structure_bonus
        return max(0.0, min(1.0, score))

    def _assess_innovation(self, response: str, patterns: Dict) -> float:
        """Assess response innovation"""
        creative_count = sum(1 for indicator in patterns["creative_indicators"] if indicator in response)
        standard_count = sum(1 for indicator in patterns["standard_indicators"] if indicator in response)
        
        # Look for novel combinations or unique approaches
        has_unique_approach = any(phrase in response for phrase in [
            "new approach", "alternative method", "innovative solution", "creative way"
        ])
        
        innovation_bonus = 0.3 if has_unique_approach else 0
        score = 0.3 + (creative_count * 0.15) - (standard_count * 0.1) + innovation_bonus
        
        return max(0.0, min(1.0, score))

    def _assess_practicality(self, response: str, patterns: Dict) -> float:
        """Assess response practicality"""
        response_lower = response.lower()
        
        actionable_count = sum(1 for indicator in patterns["actionable_indicators"] if indicator in response_lower)
        theoretical_count = sum(1 for indicator in patterns["theoretical_indicators"] if indicator in response_lower)
        
        # Check for code examples or specific steps
        has_code = any(marker in response for marker in ["```", "code", "function", "class", "def "])
        has_steps = any(marker in response for marker in ["step 1", "first", "then", "next", "finally"])
        
        practical_bonus = 0.2 * (int(has_code) + int(has_steps))
        score = 0.4 + (actionable_count * 0.1) - (theoretical_count * 0.1) + practical_bonus
        
        return max(0.0, min(1.0, score))

    def _calculate_score_variance(self, scores: List[float]) -> float:
        """Calculate variance in scores to determine confidence"""
        if len(scores) < 2:
            return 0.0
        
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        return variance

    def _generate_quality_reasoning(self, dimension_scores: Dict, agent_name: str) -> str:
        """Generate human-readable reasoning for quality assessment"""
        reasoning_parts = []
        
        # Identify strengths
        strong_dimensions = [dim for dim, score in dimension_scores.items() if score > 0.7]
        if strong_dimensions:
            strengths = ", ".join(dim.value for dim in strong_dimensions)
            reasoning_parts.append(f"Strong in: {strengths}")
        
        # Identify weaknesses
        weak_dimensions = [dim for dim, score in dimension_scores.items() if score < 0.5]
        if weak_dimensions:
            weaknesses = ", ".join(dim.value for dim in weak_dimensions)
            reasoning_parts.append(f"Needs improvement: {weaknesses}")
        
        # Agent-specific notes
        if agent_name:
            reasoning_parts.append(f"Agent: {agent_name}")
        
        return " | ".join(reasoning_parts) if reasoning_parts else "Balanced performance across dimensions"


class AgentWarmupManager:
    """Manages agent warm-up for faster response times"""

    def __init__(self):
        self.warmup_states: Dict[str, AgentWarmupState] = {}
        self.warmup_threshold = 300  # 5 minutes
        self.warmup_tasks = ["Hello", "Ready for tasks", "Status check"]

    async def ensure_agent_warmup(self, agent_name: str) -> bool:
        """Ensure agent is warmed up and ready"""
        try:
            current_time = datetime.now(timezone.utc)
            
            if agent_name not in self.warmup_states:
                self.warmup_states[agent_name] = AgentWarmupState(
                    agent_name=agent_name,
                    last_used=current_time,
                    warmup_level=0.0,
                    avg_response_time=0.0,
                    recent_tasks=[]
                )
            
            warmup_state = self.warmup_states[agent_name]
            
            # Check if warmup is needed
            time_since_last_use = (current_time - warmup_state.last_used).total_seconds()
            
            if time_since_last_use > self.warmup_threshold or warmup_state.warmup_level < 0.5:
                logger.info(f"🔥 Warming up agent: {agent_name}")
                await self._perform_warmup(agent_name)
            
            warmup_state.last_used = current_time
            return warmup_state.is_warmed_up
            
        except Exception as e:
            logger.error(f"Error during agent warmup: {e}")
            return False

    async def _perform_warmup(self, agent_name: str):
        """Perform actual warmup for agent"""
        try:
            from .autogen_framework import get_orchestrator
            
            orchestrator = get_orchestrator()
            
            if agent_name in orchestrator.agents:
                agent = orchestrator.agents[agent_name]
                
                # Quick warmup task
                start_time = time.time()
                response = await agent.generate_response("System warmup check", "")
                warmup_time = time.time() - start_time
                
                # Update warmup state
                warmup_state = self.warmup_states[agent_name]
                warmup_state.warmup_level = 1.0
                warmup_state.avg_response_time = warmup_time
                warmup_state.is_warmed_up = True
                
                logger.info(f"✅ Agent {agent_name} warmed up in {warmup_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error performing warmup for {agent_name}: {e}")

    def get_warmup_status(self) -> Dict[str, Any]:
        """Get current warmup status for all agents"""
        return {
            agent_name: {
                "is_warmed_up": state.is_warmed_up,
                "warmup_level": state.warmup_level,
                "avg_response_time": state.avg_response_time,
                "last_used": state.last_used.isoformat(),
                "time_since_last_use": (datetime.now(timezone.utc) - state.last_used).total_seconds()
            }
            for agent_name, state in self.warmup_states.items()
        }


class PerformanceOptimizer:
    """Main performance optimization coordinator"""

    def __init__(self):
        self.response_cache = AdvancedResponseCache()
        self.quality_assessor = ResponseQualityAssessor()
        self.warmup_manager = AgentWarmupManager()
        self.performance_history = []
        
    async def optimize_request(self, prompt: str, context: str, agent_name: str,
                             model_type: str) -> Tuple[Optional[str], bool, Dict]:
        """Optimize a request using all available techniques"""
        start_time = time.time()
        optimization_info = {"cache_used": False, "warmup_performed": False, "quality_score": 0.0}
        
        # 1. Check cache first
        cache_key = self.response_cache.generate_cache_key(prompt, context, agent_name)
        cached_response = await self.response_cache.get_cached_response(cache_key)
        
        if cached_response and cached_response.quality_score > 0.6:
            optimization_info["cache_used"] = True
            optimization_info["quality_score"] = cached_response.quality_score
            
            # Update usage metrics
            self._record_performance(time.time() - start_time, True, cached_response.quality_score)
            
            return cached_response.response, True, optimization_info
        
        # 2. Ensure agent warmup
        warmup_success = await self.warmup_manager.ensure_agent_warmup(agent_name)
        optimization_info["warmup_performed"] = not warmup_success
        
        return None, False, optimization_info

    async def post_process_response(self, response: str, prompt: str, context: str,
                                  agent_name: str, model_type: str) -> Tuple[str, float, Dict]:
        """Post-process response with quality assessment and caching"""
        try:
            # Assess quality
            quality_assessment = await self.quality_assessor.assess_quality(
                response, prompt, context, agent_name
            )
            
            # Cache if quality is good enough
            if quality_assessment.overall_score > 0.5:
                cache_key = self.response_cache.generate_cache_key(prompt, context, agent_name)
                context_hash = hashlib.md5(context.encode(), usedforsecurity=False).hexdigest()[:8]
                
                await self.response_cache.store_cached_response(
                    cache_key, response, agent_name, model_type,
                    quality_assessment.overall_score, context_hash,
                    tags=["auto-cached"]
                )
            
            # Record performance
            self._record_performance(0.0, False, quality_assessment.overall_score)
            
            return response, quality_assessment.overall_score, {
                "quality_assessment": quality_assessment,
                "cached": quality_assessment.overall_score > 0.5
            }
            
        except Exception as e:
            logger.error(f"Error in post-processing: {e}")
            return response, 0.5, {"error": str(e)}

    def _record_performance(self, response_time: float, cache_used: bool, quality_score: float):
        """Record performance metrics"""
        cache_stats = self.response_cache.get_cache_stats()
        
        metrics = PerformanceMetrics(
            response_time=response_time,
            cache_hit_rate=cache_stats["hit_rate"],
            quality_score=quality_score,
            agent_efficiency=1.0 - (response_time / 30.0),  # Normalize to 30s max
            memory_usage=0.0,  # Could be implemented
            concurrent_tasks=1,  # Could be tracked
            timestamp=datetime.now(timezone.utc)
        )
        
        self.performance_history.append(metrics)
        
        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-800:]

    async def get_optimization_analytics(self) -> Dict[str, Any]:
        """Get comprehensive optimization analytics"""
        try:
            cache_stats = self.response_cache.get_cache_stats()
            warmup_status = self.warmup_manager.get_warmup_status()
            
            # Performance trends
            if self.performance_history:
                recent_metrics = self.performance_history[-10:]
                avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
                avg_quality = sum(m.quality_score for m in recent_metrics) / len(recent_metrics)
            else:
                avg_response_time = 0.0
                avg_quality = 0.0
            
            return {
                "cache_performance": cache_stats,
                "warmup_status": warmup_status,
                "performance_trends": {
                    "avg_response_time": avg_response_time,
                    "avg_quality_score": avg_quality,
                    "total_requests": len(self.performance_history)
                },
                "optimization_effectiveness": self._calculate_optimization_effectiveness(),
                "recommendations": self._generate_optimization_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimization analytics: {e}")
            return {"error": str(e)}

    def _calculate_optimization_effectiveness(self) -> Dict[str, float]:
        """Calculate optimization effectiveness metrics"""
        cache_stats = self.response_cache.get_cache_stats()
        
        # Calculate time saved from caching (estimated)
        estimated_time_saved = cache_stats["total_hits"] * 5.0  # Assume 5s saved per hit
        
        # Calculate quality improvement (simplified)
        if self.performance_history:
            recent_quality = sum(m.quality_score for m in self.performance_history[-10:]) / min(10, len(self.performance_history))
        else:
            recent_quality = 0.5
        
        return {
            "cache_effectiveness": cache_stats["hit_rate"],
            "time_saved_seconds": estimated_time_saved,
            "quality_improvement": max(0, recent_quality - 0.5),
            "overall_efficiency": cache_stats["hit_rate"] * recent_quality
        }

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        cache_stats = self.response_cache.get_cache_stats()
        
        if cache_stats["hit_rate"] < 0.3:
            recommendations.append("Improve cache strategy - hit rate is low")
        
        if self.performance_history:
            avg_quality = sum(m.quality_score for m in self.performance_history[-10:]) / min(10, len(self.performance_history))
            if avg_quality < 0.6:
                recommendations.append("Focus on improving response quality")
        
        # Check warmup effectiveness
        warmup_status = self.warmup_manager.get_warmup_status()
        cold_agents = [name for name, status in warmup_status.items() if not status["is_warmed_up"]]
        if cold_agents:
            recommendations.append(f"Warm up cold agents: {', '.join(cold_agents)}")
        
        if not recommendations:
            recommendations.append("Performance optimization is working well")
        
        return recommendations


# Global optimizer instance
_performance_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer