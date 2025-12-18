"""
Smart AI Router - Routes requests to the best AI model or team
Optimizes for speed on simple tasks, uses full AI team for complex tasks

Enhanced with:
- Response caching with TTL
- Confidence scoring for routing decisions
- Circuit breaker pattern for resilience
- Semantic complexity analysis
- Analytics tracking
"""

import asyncio
import hashlib
import logging
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.ai_team_http_client import (
    execute_ai_team_task,
    check_ai_team_health,
)

# Lazy import to avoid circular dependencies
_gemini_service = None
_openai_service = None
_ai_config = None


def _get_gemini_service():
    """Lazy load Gemini service"""
    global _gemini_service
    if _gemini_service is None:
        try:
            from app.services.gemini_service import gemini_service

            _gemini_service = gemini_service
        except Exception as e:
            logging.getLogger(__name__).warning(f"Gemini service not available: {e}")
            _gemini_service = False
    return _gemini_service if _gemini_service else None


def _get_openai_service():
    """Lazy load OpenAI service as fallback"""
    global _openai_service
    if _openai_service is None:
        try:
            from app.services.openai_service import openai_service

            _openai_service = openai_service
        except Exception as e:
            logging.getLogger(__name__).warning(f"OpenAI service not available: {e}")
            _openai_service = False
    return _openai_service if _openai_service else None


def _get_ai_config():
    """Lazy load AI configuration"""
    global _ai_config
    if _ai_config is None:
        try:
            from app.core.config import get_settings

            _ai_config = get_settings().ai
        except Exception as e:
            logging.getLogger(__name__).warning(f"Config not available: {e}")
            _ai_config = False
    return _ai_config if _ai_config else None


logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    SIMPLE = "simple"  # Quick response, single model
    MODERATE = "moderate"  # Single specialist model
    COMPLEX = "complex"  # Full AI team collaboration


@dataclass
class ComplexityResult:
    """Result of complexity analysis with confidence score"""

    complexity: TaskComplexity
    confidence: float  # 0.0 to 1.0
    reasoning: str
    keyword_matches: List[str] = field(default_factory=list)
    semantic_signals: Dict[str, float] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Cached response with metadata"""

    response: str
    model_used: str
    complexity: str
    timestamp: float
    hit_count: int = 0


class CircuitBreaker:
    """Circuit breaker for service resilience"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open

    def record_success(self):
        """Record a successful call"""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"🔴 Circuit breaker OPEN after {self.failure_count} failures"
            )

    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                logger.info("🟡 Circuit breaker HALF-OPEN, testing...")
                return True
            return False

        # half-open - allow one test request
        return True


class ResponseCache:
    """LRU cache for AI responses with TTL"""

    def __init__(self, max_size: int = 100, ttl: float = 300.0):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _generate_key(self, message: str, context: str, context_type: str) -> str:
        """Generate cache key from request parameters (not used for security)"""
        content = f"{message}:{context[:100]}:{context_type}"
        # usedforsecurity=False because this is only for cache key generation, not cryptographic security
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def get(
        self, message: str, context: str, context_type: str
    ) -> Optional[CacheEntry]:
        """Get cached response if valid"""
        key = self._generate_key(message, context, context_type)

        if key in self.cache:
            entry = self.cache[key]
            # Check TTL
            if time.time() - entry.timestamp < self.ttl:
                entry.hit_count += 1
                self.hits += 1
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                logger.info(f"📦 Cache HIT (key={key[:8]}..., hits={entry.hit_count})")
                return entry
            else:
                # Expired
                del self.cache[key]

        self.misses += 1
        return None

    def set(
        self,
        message: str,
        context: str,
        context_type: str,
        response: str,
        model_used: str,
        complexity: str,
    ):
        """Cache a response"""
        key = self._generate_key(message, context, context_type)

        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[key] = CacheEntry(
            response=response,
            model_used=model_used,
            complexity=complexity,
            timestamp=time.time(),
        )
        logger.debug(f"📦 Cache SET (key={key[:8]}...)")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }


class RoutingAnalytics:
    """Track routing decisions for optimization"""

    def __init__(self):
        self.decisions: List[Dict] = []
        self.max_history = 1000

    def record(
        self,
        message: str,
        complexity: str,
        model_used: str,
        response_time: float,
        confidence: float,
        success: bool,
    ):
        """Record a routing decision"""
        self.decisions.append(
            {
                "timestamp": time.time(),
                "message_length": len(message),
                "complexity": complexity,
                "model_used": model_used,
                "response_time": response_time,
                "confidence": confidence,
                "success": success,
            }
        )

        # Keep history bounded
        if len(self.decisions) > self.max_history:
            self.decisions = self.decisions[-self.max_history :]

    def get_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        if not self.decisions:
            return {"total_requests": 0}

        by_complexity = {}
        by_model = {}
        total_time = 0
        success_count = 0

        for d in self.decisions:
            # By complexity
            c = d["complexity"]
            if c not in by_complexity:
                by_complexity[c] = 0
            by_complexity[c] += 1

            # By model
            m = d["model_used"]
            if m not in by_model:
                by_model[m] = 0
            by_model[m] += 1

            total_time += d["response_time"]
            if d["success"]:
                success_count += 1

        return {
            "total_requests": len(self.decisions),
            "by_complexity": by_complexity,
            "by_model": by_model,
            "avg_response_time": f"{total_time / len(self.decisions):.2f}s",
            "success_rate": f"{success_count / len(self.decisions) * 100:.1f}%",
        }


class DemoResponseGenerator:
    """Generate helpful demo responses when no AI services are configured"""

    DEMO_RESPONSES = {
        "greeting": """👋 Hello! I'm ChatterFix AI Assistant running in **demo mode**.

To unlock full AI capabilities, configure one or more of these API keys in your .env file:
- `GEMINI_API_KEY` - Google Gemini (recommended, fastest)
- `OPENAI_API_KEY` - OpenAI GPT-4
- `XAI_API_KEY` - xAI Grok
- `ANTHROPIC_API_KEY` - Anthropic Claude

I can still help you navigate the CMMS system and provide basic guidance!""",
        "work_order": """📋 **Work Order Assistance (Demo Mode)**

To create or manage work orders, I would typically:
1. Analyze your equipment issue
2. Suggest priority level based on symptoms
3. Recommend required parts from inventory
4. Assign to the best available technician

*Configure an AI API key to enable intelligent work order assistance.*""",
        "troubleshooting": """🔧 **Troubleshooting Guide (Demo Mode)**

For equipment troubleshooting, I would normally:
1. Analyze symptoms and error codes
2. Check maintenance history for patterns
3. Provide step-by-step diagnostic procedures
4. Suggest corrective actions with safety considerations

*Enable AI services for intelligent diagnostics and root cause analysis.*""",
        "inventory": """📦 **Inventory Management (Demo Mode)**

I can help with:
- Part lookups and availability checks
- Reorder recommendations
- Stock level monitoring
- Vendor comparison

*Full AI capabilities require an API key configuration.*""",
        "default": """🤖 **ChatterFix AI (Demo Mode)**

I'm currently running without AI services configured. Here's what you can still do:

✅ **Available Features:**
- Navigate dashboards and reports
- View work orders, assets, and inventory
- Access training modules
- Use voice commands for basic operations

🔑 **To Enable Full AI:**
Add one of these to your .env file:
- `GEMINI_API_KEY` (recommended)
- `OPENAI_API_KEY`
- `XAI_API_KEY`
- `ANTHROPIC_API_KEY`

How can I help you navigate ChatterFix today?""",
    }

    @classmethod
    def get_response(cls, message: str, context_type: str = "general") -> str:
        """Generate appropriate demo response based on message content"""
        message_lower = message.lower()

        # Check for greetings
        if any(
            word in message_lower for word in ["hello", "hi", "hey", "help", "start"]
        ):
            return cls.DEMO_RESPONSES["greeting"]

        # Check for work order related
        if any(
            word in message_lower
            for word in ["work order", "ticket", "task", "job", "repair"]
        ):
            return cls.DEMO_RESPONSES["work_order"]

        # Check for troubleshooting
        if any(
            word in message_lower
            for word in [
                "troubleshoot",
                "diagnose",
                "fix",
                "error",
                "problem",
                "issue",
                "broken",
            ]
        ):
            return cls.DEMO_RESPONSES["troubleshooting"]

        # Check for inventory
        if any(
            word in message_lower
            for word in ["part", "inventory", "stock", "order", "supplier"]
        ):
            return cls.DEMO_RESPONSES["inventory"]

        # Context-based responses
        context_map = {
            "equipment_diagnosis": "troubleshooting",
            "troubleshooting": "troubleshooting",
            "work_order": "work_order",
            "inventory": "inventory",
        }

        if context_type in context_map:
            return cls.DEMO_RESPONSES[context_map[context_type]]

        return cls.DEMO_RESPONSES["default"]


class AIRouter:
    """
    Smart router that determines the best AI approach for each request.

    - SIMPLE tasks: Use fast single model (Gemini) for < 2 second response
    - MODERATE tasks: Use specialist from AI team
    - COMPLEX tasks: Use full AI team collaboration

    Gracefully handles missing API keys by routing to available services or demo mode.
    """

    # Keywords indicating complex tasks requiring team collaboration
    COMPLEX_KEYWORDS = [
        "analyze",
        "diagnose",
        "troubleshoot",
        "investigate",
        "design",
        "architect",
        "plan",
        "strategy",
        "multiple",
        "several",
        "compare",
        "comprehensive",
        "emergency",
        "critical",
        "urgent",
        "safety",
        "root cause",
        "failure analysis",
        "predictive",
        "optimization",
        "improve",
        "enhance",
        "workflow",
        "process",
        "procedure",
        "training",
        "documentation",
        "manual",
    ]

    # Keywords indicating simple tasks
    SIMPLE_KEYWORDS = [
        "hello",
        "hi",
        "hey",
        "thanks",
        "thank you",
        "what is",
        "where is",
        "how do i",
        "show me",
        "status",
        "check",
        "list",
        "get",
        "yes",
        "no",
        "ok",
        "okay",
        "sure",
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

    # Semantic patterns for deeper analysis
    QUESTION_PATTERNS = [
        r"^(what|where|when|who|why|how)\s",
        r"\?$",
        r"^(can you|could you|will you|would you)",
        r"^(is|are|do|does|did|has|have|was|were)\s",
    ]

    MULTI_STEP_PATTERNS = [
        r"(first|then|after|before|next|finally)",
        r"(step\s*\d+|1\.|2\.|3\.)",
        r"(and\s+also|in addition|furthermore|moreover)",
        r"(multiple|several|various|different)",
    ]

    TECHNICAL_PATTERNS = [
        r"(error|exception|failure|fault|malfunction)",
        r"(pressure|temperature|voltage|current|rpm|flow)",
        r"(vibration|noise|leak|wear|corrosion)",
        r"(calibrat|align|adjust|tighten|lubricate)",
    ]

    def __init__(self):
        self.ai_team_available = False
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds

        # Enhanced features
        self.cache = ResponseCache(max_size=100, ttl=300.0)  # 5 min TTL
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60.0
        )
        self.analytics = RoutingAnalytics()
        self.in_flight_requests: Dict[str, asyncio.Event] = {}

        logger.info(
            "🧠 Smart AI Router initialized with caching, circuit breaker, and analytics"
        )

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

    def _detect_complexity(
        self, message: str, context: str = "", context_type: str = ""
    ) -> TaskComplexity:
        """Detect the complexity of a task based on message content (simple return)"""
        result = self._analyze_complexity(message, context, context_type)
        return result.complexity

    def _analyze_complexity(
        self, message: str, context: str = "", context_type: str = ""
    ) -> ComplexityResult:
        """
        Enhanced complexity analysis with confidence scoring and semantic patterns.

        Returns ComplexityResult with:
        - complexity: TaskComplexity enum
        - confidence: 0.0 to 1.0 confidence score
        - reasoning: Human-readable explanation
        - keyword_matches: List of matched keywords
        - semantic_signals: Dict of semantic pattern matches
        """
        message_lower = message.lower()
        context_lower = context.lower() if context else ""
        combined = f"{message_lower} {context_lower}"

        keyword_matches = []
        semantic_signals = {}

        # Emergency/critical always gets full team (high confidence)
        emergency_words = [
            "emergency",
            "critical",
            "urgent",
            "safety hazard",
            "danger",
            "immediately",
        ]
        emergency_matches = [w for w in emergency_words if w in combined]
        if context_type == "emergency" or emergency_matches:
            logger.info("🚨 Emergency detected - using full AI team")
            return ComplexityResult(
                complexity=TaskComplexity.COMPLEX,
                confidence=0.98,
                reasoning=f"Emergency keywords detected: {emergency_matches}",
                keyword_matches=emergency_matches,
                semantic_signals={"emergency": 1.0},
            )

        # Check for simple greetings/acknowledgments (high confidence for simple)
        word_count = len(message.split())
        simple_matches = [w for w in self.SIMPLE_KEYWORDS if w in message_lower]
        if word_count <= 5 and simple_matches:
            return ComplexityResult(
                complexity=TaskComplexity.SIMPLE,
                confidence=0.95,
                reasoning=f"Short message with simple keywords: {simple_matches}",
                keyword_matches=simple_matches,
                semantic_signals={"greeting": 1.0},
            )

        # === Semantic Pattern Analysis ===

        # Question complexity
        question_score = 0
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                question_score += 0.2
        semantic_signals["question"] = min(question_score, 1.0)

        # Multi-step task detection
        multistep_score = 0
        for pattern in self.MULTI_STEP_PATTERNS:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            if matches:
                multistep_score += len(matches) * 0.3
        semantic_signals["multi_step"] = min(multistep_score, 1.0)

        # Technical content detection
        technical_score = 0
        for pattern in self.TECHNICAL_PATTERNS:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            if matches:
                technical_score += len(matches) * 0.25
                keyword_matches.extend(matches)
        semantic_signals["technical"] = min(technical_score, 1.0)

        # === Keyword Analysis ===

        # Count complex keywords
        complex_matches = [kw for kw in self.COMPLEX_KEYWORDS if kw in combined]
        keyword_matches.extend(complex_matches)
        complex_count = len(complex_matches)

        # === Structural Analysis ===

        sentence_count = len([s for s in re.split(r"[.!?]", message) if s.strip()])
        semantic_signals["sentence_count"] = min(sentence_count / 5, 1.0)
        semantic_signals["word_count"] = min(word_count / 50, 1.0)

        # === Complexity Scoring ===

        complexity_score = 0.0

        # Keyword contribution (0-3 points)
        complexity_score += min(complex_count * 0.6, 3.0)

        # Semantic pattern contribution (0-3 points)
        complexity_score += semantic_signals.get("multi_step", 0) * 1.5
        complexity_score += semantic_signals.get("technical", 0) * 1.5

        # Length contribution (0-2 points)
        complexity_score += semantic_signals.get("sentence_count", 0) * 1.0
        complexity_score += semantic_signals.get("word_count", 0) * 1.0

        # Context type boost
        high_complexity_contexts = [
            "equipment_diagnosis",
            "troubleshooting",
            "failure_analysis",
            "root_cause",
        ]
        moderate_complexity_contexts = ["work_order", "inventory", "documentation"]

        if context_type in high_complexity_contexts:
            complexity_score += 2.5
            semantic_signals["context_boost"] = 0.8
        elif context_type in moderate_complexity_contexts:
            complexity_score += 1.0
            semantic_signals["context_boost"] = 0.4

        # === Determine Complexity Level and Confidence ===

        if complexity_score >= 5.0:
            complexity = TaskComplexity.COMPLEX
            # Confidence based on how far above threshold
            confidence = min(0.7 + (complexity_score - 5.0) * 0.05, 0.95)
            reasoning = f"High complexity score ({complexity_score:.1f}): {len(keyword_matches)} keywords, multi-step={semantic_signals.get('multi_step', 0):.1f}"
        elif complexity_score >= 2.0:
            complexity = TaskComplexity.MODERATE
            # Confidence based on how centered in range
            distance_from_boundaries = min(
                complexity_score - 2.0, 5.0 - complexity_score
            )
            confidence = 0.6 + distance_from_boundaries * 0.1
            reasoning = f"Moderate complexity score ({complexity_score:.1f}): {len(keyword_matches)} keywords"
        else:
            complexity = TaskComplexity.SIMPLE
            # Higher confidence for very low scores
            confidence = min(0.8 + (2.0 - complexity_score) * 0.1, 0.95)
            reasoning = f"Low complexity score ({complexity_score:.1f}): simple request"

        logger.debug(
            f"📊 Complexity analysis: {complexity.value} (confidence={confidence:.2f})"
        )

        return ComplexityResult(
            complexity=complexity,
            confidence=confidence,
            reasoning=reasoning,
            keyword_matches=keyword_matches,
            semantic_signals=semantic_signals,
        )

    def _get_specialist_agents(self, context_type: str) -> Optional[List[str]]:
        """Get recommended specialist agents for a context type"""
        return self.SPECIALIST_CONTEXTS.get(context_type)

    async def route_request(
        self,
        message: str,
        context: str = "",
        context_type: str = "general",
        user_id: Optional[int] = None,
        force_team: bool = False,
        use_cache: bool = True,
        fast_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate AI model(s)

        Args:
            message: User's message
            context: Additional context
            context_type: Type of request (equipment_diagnosis, troubleshooting, etc.)
            user_id: User ID for personalization
            force_team: Force use of full AI team
            use_cache: Whether to use response caching (default True)
            fast_mode: Skip AI team refinement for ~50% faster responses

        Returns:
            Response dict with 'response', 'model_used', 'complexity', 'confidence', etc.
        """
        start_time = time.time()

        # === Check Cache First (if not forcing team) ===
        if use_cache and not force_team:
            cached = self.cache.get(message, context, context_type)
            if cached:
                elapsed_time = time.time() - start_time
                return {
                    "success": True,
                    "response": cached.response,
                    "model_used": f"{cached.model_used} (cached)",
                    "complexity": cached.complexity,
                    "response_time": f"{elapsed_time:.3f}s",
                    "cached": True,
                    "cache_hits": cached.hit_count,
                }

        # === Analyze Complexity with Confidence ===
        if force_team:
            complexity_result = ComplexityResult(
                complexity=TaskComplexity.COMPLEX,
                confidence=1.0,
                reasoning="Forced team collaboration",
            )
        else:
            complexity_result = self._analyze_complexity(message, context, context_type)

        complexity = complexity_result.complexity
        confidence = complexity_result.confidence

        logger.info(
            f"📊 Task complexity: {complexity.value} (confidence={confidence:.2f}) for: {message[:50]}..."
        )

        # === Check Circuit Breaker ===
        if (
            complexity != TaskComplexity.SIMPLE
            and not self.circuit_breaker.can_execute()
        ):
            logger.warning("🔴 Circuit breaker OPEN - using fallback")
            response = await self._route_to_gemini(
                message, f"[FALLBACK MODE]\n{context}", user_id
            )
            elapsed_time = time.time() - start_time
            return {
                "success": True,
                "response": response,
                "model_used": "gemini-2.0-flash (circuit-breaker)",
                "complexity": complexity.value,
                "confidence": confidence,
                "response_time": f"{elapsed_time:.2f}s",
                "circuit_breaker": "open",
            }

        # === Check AI Team Availability ===
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
                    response = await self._route_to_specialists(
                        message, context, specialists
                    )
                    model_used = f"specialists: {', '.join(specialists)}"
                else:
                    response = await self._route_to_gemini(message, context, user_id)
                    model_used = "gemini-2.0-flash"

            else:  # COMPLEX
                # Use full AI team collaboration
                if team_available:
                    response = await self._route_to_team(
                        message, context, context_type, fast_mode=fast_mode
                    )
                    model_used = "full-ai-team" + (" (fast)" if fast_mode else "")
                else:
                    # Fallback to Gemini with enhanced prompt
                    enhanced_context = (
                        f"[COMPLEX TASK - Provide thorough analysis]\n{context}"
                    )
                    response = await self._route_to_gemini(
                        message, enhanced_context, user_id
                    )
                    model_used = "gemini-2.0-flash (fallback)"

            elapsed_time = time.time() - start_time

            # Record success with circuit breaker
            if complexity != TaskComplexity.SIMPLE:
                self.circuit_breaker.record_success()

            # Cache the response (don't cache team responses due to variability)
            if use_cache and model_used.startswith("gemini"):
                self.cache.set(
                    message,
                    context,
                    context_type,
                    response,
                    model_used,
                    complexity.value,
                )

            # Record analytics
            self.analytics.record(
                message=message,
                complexity=complexity.value,
                model_used=model_used,
                response_time=elapsed_time,
                confidence=confidence,
                success=True,
            )

            return {
                "success": True,
                "response": response,
                "model_used": model_used,
                "complexity": complexity.value,
                "confidence": confidence,
                "reasoning": complexity_result.reasoning,
                "response_time": f"{elapsed_time:.2f}s",
                "team_available": team_available,
            }

        except Exception as e:
            logger.error(f"❌ AI routing error: {e}")

            # Record failure with circuit breaker
            if complexity != TaskComplexity.SIMPLE:
                self.circuit_breaker.record_failure()

            # Ultimate fallback to Gemini
            try:
                response = await self._route_to_gemini(message, context, user_id)
                elapsed_time = time.time() - start_time

                # Record recovered request
                self.analytics.record(
                    message=message,
                    complexity=complexity.value,
                    model_used="gemini-2.0-flash (error fallback)",
                    response_time=elapsed_time,
                    confidence=confidence,
                    success=True,
                )

                return {
                    "success": True,
                    "response": response,
                    "model_used": "gemini-2.0-flash (error fallback)",
                    "complexity": complexity.value,
                    "confidence": confidence,
                    "error_recovered": True,
                }
            except Exception as fallback_error:
                elapsed_time = time.time() - start_time
                logger.warning(
                    f"All AI services failed, using demo mode: {fallback_error}"
                )

                # Use demo mode as ultimate fallback - never error out to user
                demo_response = DemoResponseGenerator.get_response(
                    message, context_type
                )

                # Record as partial success (demo mode worked)
                self.analytics.record(
                    message=message,
                    complexity=complexity.value,
                    model_used="demo-mode",
                    response_time=elapsed_time,
                    confidence=0.5,
                    success=True,
                )

                return {
                    "success": True,  # Demo mode is still a valid response
                    "response": demo_response,
                    "model_used": "demo-mode",
                    "complexity": complexity.value,
                    "confidence": 0.5,
                    "demo_mode": True,
                    "note": "No AI services available - running in demo mode",
                }

    def get_router_stats(self) -> Dict[str, Any]:
        """Get router statistics including cache, circuit breaker, and analytics"""
        # Get AI service availability
        ai_config = _get_ai_config()
        ai_status = (
            ai_config.get_ai_status_summary()
            if ai_config
            else {
                "any_available": False,
                "primary_service": None,
                "available_services": [],
            }
        )

        return {
            "cache": self.cache.get_stats(),
            "circuit_breaker": {
                "state": self.circuit_breaker.state,
                "failure_count": self.circuit_breaker.failure_count,
            },
            "analytics": self.analytics.get_summary(),
            "ai_team_available": self.ai_team_available,
            "ai_services": ai_status,
            "demo_mode": not ai_status.get("any_available", False),
        }

    def is_demo_mode(self) -> bool:
        """Check if running in demo mode (no AI services configured)"""
        ai_config = _get_ai_config()
        if ai_config:
            return not ai_config.has_any_ai_service()
        return True  # If config unavailable, assume demo mode

    async def _route_to_gemini(
        self, message: str, context: str, user_id: Optional[int]
    ) -> str:
        """Route to best available AI service (Gemini preferred, with fallbacks)"""

        # Add CMMS context for better responses
        cmms_context = """You are ChatterFix AI, an intelligent CMMS assistant for industrial maintenance technicians.
You help with work orders, equipment diagnosis, inventory management, and troubleshooting.
Be concise, professional, and action-oriented. Prioritize safety.

""" + (
            context or ""
        )

        # Try Gemini first (fastest)
        gemini = _get_gemini_service()
        if gemini:
            try:
                # Check if Gemini has a valid API key
                if (
                    hasattr(gemini, "using_service_account")
                    and gemini.using_service_account
                ):
                    logger.info("⚡ Routing to Gemini (service account)")
                    return await gemini.generate_response(
                        message, cmms_context, user_id
                    )
                elif hasattr(gemini, "default_api_key") and gemini.default_api_key:
                    logger.info("⚡ Routing to Gemini (API key)")
                    return await gemini.generate_response(
                        message, cmms_context, user_id
                    )
            except Exception as e:
                logger.warning(f"Gemini failed, trying fallback: {e}")

        # Try OpenAI as fallback
        openai = _get_openai_service()
        if openai:
            try:
                if hasattr(openai, "default_api_key") and openai.default_api_key:
                    logger.info("⚡ Routing to OpenAI (fallback)")
                    return await openai.generate_response(
                        message, cmms_context, user_id
                    )
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}")

        # No AI service available - return demo response
        logger.info("🎭 No AI service available - using demo mode")
        return DemoResponseGenerator.get_response(message, "general")

    async def _route_to_specialists(
        self, message: str, context: str, specialists: List[str]
    ) -> str:
        """Route to specific specialist agents - uses FAST MODE for quick responses"""
        logger.info(f"🎯 Routing to specialists (fast mode): {specialists}")

        result = await execute_ai_team_task(
            prompt=message,
            context=f"ChatterFix CMMS Context:\n{context}",
            required_agents=specialists,
            max_iterations=2,  # Quick specialist response
            project_context="ChatterFix",
            fast_mode=True,  # Skip refinement for faster specialist responses
        )

        if result.get("success"):
            return result.get("final_result", "Specialist analysis complete.")
        else:
            # Fallback
            return await self._route_to_gemini(message, context, None)

    async def _route_to_team(
        self, message: str, context: str, context_type: str, fast_mode: bool = False
    ) -> str:
        """
        Route to full AI team for complex collaborative task

        Args:
            message: User message
            context: Additional context
            context_type: Type of task
            fast_mode: If True, skip refinement for faster response (~50% faster)
        """
        mode = "⚡ FAST" if fast_mode else "🔄 FULL"
        logger.info(f"🤖 Routing to {mode} AI TEAM for complex task")

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
            max_iterations=2 if fast_mode else 3,  # Fewer iterations in fast mode
            project_context="ChatterFix",
            fast_mode=fast_mode,
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
    force_team: bool = False,
    fast_mode: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to get smart AI response

    Args:
        message: User message
        context: Additional context
        context_type: Type of request
        user_id: User ID
        force_team: Force full AI team collaboration
        fast_mode: Skip refinement for faster response (~50% faster)
    """
    return await ai_router.route_request(
        message=message,
        context=context,
        context_type=context_type,
        user_id=user_id,
        force_team=force_team,
        fast_mode=fast_mode,
    )
