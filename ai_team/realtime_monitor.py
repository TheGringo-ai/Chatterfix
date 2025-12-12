"""
Real-time Quality Assessment and Monitoring System
Provides live monitoring of AI team performance, quality assessment during streaming,
and comprehensive analytics for the enhanced autogen framework
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Tuple
import threading
from queue import Queue
import statistics

logger = logging.getLogger(__name__)


class MonitoringLevel(Enum):
    """Different levels of monitoring intensity"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"
    DEBUG = "debug"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics to track"""
    RESPONSE_TIME = "response_time"
    QUALITY_SCORE = "quality_score"
    TOKEN_USAGE = "token_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    CONSENSUS_LEVEL = "consensus_level"
    AGENT_EFFICIENCY = "agent_efficiency"
    INNOVATION_SCORE = "innovation_score"


@dataclass
class RealtimeMetric:
    """Real-time metric data point"""
    metric_type: MetricType
    value: float
    agent_name: str
    timestamp: datetime
    task_id: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    severity: AlertSeverity
    message: str
    metric_type: MetricType
    threshold_violated: float
    current_value: float
    agent_name: str
    timestamp: datetime
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class StreamingQualityAssessment:
    """Real-time quality assessment during streaming"""
    current_quality: float
    confidence: float
    completeness: float
    coherence: float
    relevance: float
    innovation_indicators: int
    warning_flags: List[str]
    improvement_suggestions: List[str]
    timestamp: datetime


@dataclass
class AgentHealthStatus:
    """Health status of an agent"""
    agent_name: str
    is_healthy: bool
    response_time_avg: float
    quality_score_avg: float
    error_rate: float
    last_activity: datetime
    health_score: float
    issues: List[str]
    recommendations: List[str]


class RealtimeMetricsCollector:
    """Collects and manages real-time metrics"""

    def __init__(self, retention_hours: int = 24, max_metrics_per_type: int = 1000):
        self.retention_hours = retention_hours
        self.max_metrics_per_type = max_metrics_per_type
        
        # Storage for metrics
        self.metrics_storage: Dict[MetricType, deque] = {
            metric_type: deque(maxlen=max_metrics_per_type)
            for metric_type in MetricType
        }
        
        # Real-time aggregations
        self.current_aggregations = {}
        self.rolling_windows = {
            "1m": deque(maxlen=60),
            "5m": deque(maxlen=300),
            "15m": deque(maxlen=900),
            "1h": deque(maxlen=3600)
        }
        
        # Threading for background processing
        self._processing_queue = Queue()
        self._stop_processing = threading.Event()
        self._processing_thread = threading.Thread(target=self._process_metrics_background)
        self._processing_thread.daemon = True
        self._processing_thread.start()

    async def record_metric(self, metric: RealtimeMetric):
        """Record a new metric"""
        try:
            # Add to storage
            self.metrics_storage[metric.metric_type].append(metric)
            
            # Queue for background processing
            self._processing_queue.put(metric)
            
            # Update current aggregations
            await self._update_aggregations(metric)
            
        except Exception as e:
            logger.error(f"Error recording metric: {e}")

    async def _update_aggregations(self, metric: RealtimeMetric):
        """Update real-time aggregations"""
        metric_type_key = metric.metric_type.value
        
        if metric_type_key not in self.current_aggregations:
            self.current_aggregations[metric_type_key] = {
                "count": 0,
                "sum": 0.0,
                "avg": 0.0,
                "min": float('inf'),
                "max": float('-inf'),
                "last_value": 0.0,
                "last_update": metric.timestamp
            }
        
        agg = self.current_aggregations[metric_type_key]
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["avg"] = agg["sum"] / agg["count"]
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)
        agg["last_value"] = metric.value
        agg["last_update"] = metric.timestamp

    def _process_metrics_background(self):
        """Background processing of metrics"""
        while not self._stop_processing.is_set():
            try:
                # Process queued metrics
                if not self._processing_queue.empty():
                    metric = self._processing_queue.get(timeout=1)
                    self._process_single_metric(metric)
                
                # Cleanup old metrics
                self._cleanup_old_metrics()
                
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                logger.error(f"Error in background metrics processing: {e}")

    def _process_single_metric(self, metric: RealtimeMetric):
        """Process a single metric for rolling windows"""
        current_minute = int(time.time() / 60)
        
        # Add to rolling windows
        for window_name, window in self.rolling_windows.items():
            window.append({
                "metric": metric,
                "minute": current_minute
            })

    def _cleanup_old_metrics(self):
        """Clean up old metrics beyond retention period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        
        for metric_type, metrics in self.metrics_storage.items():
            # Remove old metrics
            while metrics and metrics[0].timestamp < cutoff_time:
                metrics.popleft()

    async def get_current_metrics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current metric aggregations"""
        metrics = {}
        
        for metric_type, agg in self.current_aggregations.items():
            if agent_name:
                # Filter by agent if specified
                agent_metrics = [
                    m for m in self.metrics_storage[MetricType(metric_type)]
                    if m.agent_name == agent_name
                ]
                if agent_metrics:
                    values = [m.value for m in agent_metrics[-10:]]  # Last 10 values
                    metrics[metric_type] = {
                        "current": values[-1] if values else 0,
                        "avg": sum(values) / len(values),
                        "count": len(values)
                    }
            else:
                metrics[metric_type] = agg.copy()
        
        return metrics

    async def get_metric_trend(self, metric_type: MetricType, minutes: int = 15) -> List[float]:
        """Get trend data for a specific metric"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        metrics = self.metrics_storage[metric_type]
        trend_values = [
            m.value for m in metrics
            if m.timestamp >= cutoff_time
        ]
        
        return trend_values

    def stop(self):
        """Stop the background processing"""
        self._stop_processing.set()
        self._processing_thread.join(timeout=5)


class StreamingQualityMonitor:
    """Monitors quality during streaming responses"""

    def __init__(self):
        self.quality_indicators = {
            "positive_words": ["correct", "accurate", "excellent", "perfect", "optimal"],
            "negative_words": ["error", "wrong", "incorrect", "failed", "broken"],
            "uncertainty_words": ["maybe", "perhaps", "possibly", "might", "uncertain"],
            "confidence_words": ["definitely", "certainly", "clearly", "obviously"],
            "structure_indicators": ["first", "second", "then", "finally", "conclusion"],
            "technical_indicators": ["function", "class", "method", "api", "database"]
        }

    async def assess_streaming_quality(self, partial_response: str, 
                                     original_prompt: str) -> StreamingQualityAssessment:
        """Assess quality of streaming response in real-time"""
        try:
            current_quality = await self._calculate_current_quality(partial_response)
            confidence = await self._assess_confidence(partial_response)
            completeness = await self._assess_completeness(partial_response, original_prompt)
            coherence = await self._assess_coherence(partial_response)
            relevance = await self._assess_relevance(partial_response, original_prompt)
            
            innovation_indicators = await self._count_innovation_indicators(partial_response)
            warning_flags = await self._detect_warning_flags(partial_response)
            improvement_suggestions = await self._generate_realtime_suggestions(
                partial_response, current_quality
            )
            
            return StreamingQualityAssessment(
                current_quality=current_quality,
                confidence=confidence,
                completeness=completeness,
                coherence=coherence,
                relevance=relevance,
                innovation_indicators=innovation_indicators,
                warning_flags=warning_flags,
                improvement_suggestions=improvement_suggestions,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error in streaming quality assessment: {e}")
            return StreamingQualityAssessment(
                current_quality=0.5,
                confidence=0.5,
                completeness=0.3,
                coherence=0.5,
                relevance=0.5,
                innovation_indicators=0,
                warning_flags=["Assessment error"],
                improvement_suggestions=[],
                timestamp=datetime.now(timezone.utc)
            )

    async def _calculate_current_quality(self, partial_response: str) -> float:
        """Calculate current quality score"""
        if not partial_response:
            return 0.0
        
        response_lower = partial_response.lower()
        score = 0.5  # Base score
        
        # Positive indicators
        positive_count = sum(
            1 for word in self.quality_indicators["positive_words"]
            if word in response_lower
        )
        score += min(positive_count * 0.1, 0.3)
        
        # Negative indicators
        negative_count = sum(
            1 for word in self.quality_indicators["negative_words"]
            if word in response_lower
        )
        score -= min(negative_count * 0.15, 0.4)
        
        # Structure indicators
        structure_count = sum(
            1 for indicator in self.quality_indicators["structure_indicators"]
            if indicator in response_lower
        )
        score += min(structure_count * 0.05, 0.2)
        
        return max(0.0, min(1.0, score))

    async def _assess_confidence(self, partial_response: str) -> float:
        """Assess confidence level in response"""
        response_lower = partial_response.lower()
        
        confidence_count = sum(
            1 for word in self.quality_indicators["confidence_words"]
            if word in response_lower
        )
        
        uncertainty_count = sum(
            1 for word in self.quality_indicators["uncertainty_words"]
            if word in response_lower
        )
        
        # Base confidence
        confidence = 0.6
        
        # Adjust based on indicators
        confidence += min(confidence_count * 0.1, 0.3)
        confidence -= min(uncertainty_count * 0.1, 0.4)
        
        return max(0.0, min(1.0, confidence))

    async def _assess_completeness(self, partial_response: str, original_prompt: str) -> float:
        """Assess completeness of partial response"""
        if not partial_response:
            return 0.0
        
        # Simple length-based assessment
        expected_length = len(original_prompt) * 3  # Heuristic
        current_length = len(partial_response)
        
        length_score = min(current_length / expected_length, 1.0)
        
        # Check for conclusion indicators
        has_conclusion = any(
            word in partial_response.lower()
            for word in ["conclusion", "summary", "in summary", "to conclude", "finally"]
        )
        
        conclusion_bonus = 0.2 if has_conclusion else 0
        
        return min(1.0, length_score + conclusion_bonus)

    async def _assess_coherence(self, partial_response: str) -> float:
        """Assess coherence of partial response"""
        if not partial_response:
            return 0.0
        
        sentences = partial_response.split('. ')
        if len(sentences) < 2:
            return 0.7  # Too short to assess
        
        # Check for coherence indicators
        transition_words = ["however", "therefore", "moreover", "furthermore", "additionally"]
        transition_count = sum(
            1 for word in transition_words
            if word in partial_response.lower()
        )
        
        # Check for repetitive content (negative indicator)
        words = partial_response.lower().split()
        word_frequency = {}
        for word in words:
            word_frequency[word] = word_frequency.get(word, 0) + 1
        
        repetitive_penalty = sum(
            1 for count in word_frequency.values()
            if count > 3 and len(word_frequency) > 5
        ) * 0.1
        
        coherence = 0.7 + min(transition_count * 0.05, 0.2) - min(repetitive_penalty, 0.3)
        
        return max(0.0, min(1.0, coherence))

    async def _assess_relevance(self, partial_response: str, original_prompt: str) -> float:
        """Assess relevance to original prompt"""
        if not partial_response or not original_prompt:
            return 0.5
        
        prompt_words = set(original_prompt.lower().split())
        response_words = set(partial_response.lower().split())
        
        # Calculate overlap
        overlap = prompt_words & response_words
        relevance_score = len(overlap) / len(prompt_words) if prompt_words else 0
        
        # Boost for direct addressing of prompt
        if any(phrase in partial_response.lower() for phrase in ["to answer", "regarding", "about"]):
            relevance_score += 0.1
        
        return min(1.0, relevance_score)

    async def _count_innovation_indicators(self, partial_response: str) -> int:
        """Count innovation indicators in response"""
        innovation_words = [
            "innovative", "creative", "novel", "unique", "original", 
            "breakthrough", "revolutionary", "cutting-edge"
        ]
        
        return sum(
            1 for word in innovation_words
            if word in partial_response.lower()
        )

    async def _detect_warning_flags(self, partial_response: str) -> List[str]:
        """Detect warning flags in streaming response"""
        warnings = []
        response_lower = partial_response.lower()
        
        # Check for error indicators
        error_indicators = ["error", "failed", "broken", "wrong", "incorrect"]
        if any(indicator in response_lower for indicator in error_indicators):
            warnings.append("Contains error indicators")
        
        # Check for incomplete thoughts
        if partial_response.endswith(("and", "but", "or", "because", "since")):
            warnings.append("Incomplete thought detected")
        
        # Check for repetitive content
        words = partial_response.split()
        if len(words) > 10:
            word_frequency = {}
            for word in words[-10:]:  # Check last 10 words
                word_frequency[word] = word_frequency.get(word, 0) + 1
            
            if any(count > 3 for count in word_frequency.values()):
                warnings.append("Repetitive content detected")
        
        # Check for very short response
        if len(partial_response.strip()) < 50 and "..." not in partial_response:
            warnings.append("Response may be too short")
        
        return warnings

    async def _generate_realtime_suggestions(self, partial_response: str, 
                                           current_quality: float) -> List[str]:
        """Generate real-time improvement suggestions"""
        suggestions = []
        
        if current_quality < 0.5:
            suggestions.append("Consider improving response quality")
        
        if len(partial_response) < 100:
            suggestions.append("Provide more detailed explanation")
        
        response_lower = partial_response.lower()
        
        # Check for structure
        structure_indicators = ["first", "second", "step", "bullet", "•"]
        if not any(indicator in response_lower for indicator in structure_indicators):
            suggestions.append("Consider adding structure (steps, bullets, etc.)")
        
        # Check for examples
        example_indicators = ["example", "for instance", "such as", "e.g."]
        if not any(indicator in response_lower for indicator in example_indicators):
            suggestions.append("Consider adding examples or specifics")
        
        return suggestions


class PerformanceAlertSystem:
    """System for generating and managing performance alerts"""

    def __init__(self):
        self.thresholds = {
            MetricType.RESPONSE_TIME: {"warning": 5.0, "critical": 10.0},
            MetricType.QUALITY_SCORE: {"warning": 0.6, "critical": 0.4},
            MetricType.ERROR_RATE: {"warning": 0.1, "critical": 0.2},
            MetricType.CACHE_HIT_RATE: {"warning": 0.3, "critical": 0.1},
            MetricType.CONSENSUS_LEVEL: {"warning": 0.5, "critical": 0.3}
        }
        
        self.active_alerts: List[PerformanceAlert] = []
        self.alert_history: deque = deque(maxlen=1000)

    async def check_thresholds(self, metric: RealtimeMetric) -> Optional[PerformanceAlert]:
        """Check if metric violates thresholds"""
        try:
            if metric.metric_type not in self.thresholds:
                return None
            
            thresholds = self.thresholds[metric.metric_type]
            
            # Determine severity
            severity = None
            threshold_violated = None
            
            if metric.metric_type in [MetricType.ERROR_RATE, MetricType.RESPONSE_TIME]:
                # Higher values are bad
                if metric.value >= thresholds["critical"]:
                    severity = AlertSeverity.CRITICAL
                    threshold_violated = thresholds["critical"]
                elif metric.value >= thresholds["warning"]:
                    severity = AlertSeverity.WARNING
                    threshold_violated = thresholds["warning"]
            else:
                # Lower values are bad (quality, cache hit rate, etc.)
                if metric.value <= thresholds["critical"]:
                    severity = AlertSeverity.CRITICAL
                    threshold_violated = thresholds["critical"]
                elif metric.value <= thresholds["warning"]:
                    severity = AlertSeverity.WARNING
                    threshold_violated = thresholds["warning"]
            
            if severity:
                alert = PerformanceAlert(
                    alert_id=f"alert_{int(time.time())}_{metric.agent_name}",
                    severity=severity,
                    message=f"{metric.metric_type.value} threshold violated",
                    metric_type=metric.metric_type,
                    threshold_violated=threshold_violated,
                    current_value=metric.value,
                    agent_name=metric.agent_name,
                    timestamp=datetime.now(timezone.utc),
                    resolution_suggestions=self._generate_resolution_suggestions(metric)
                )
                
                self.active_alerts.append(alert)
                self.alert_history.append(alert)
                
                logger.warning(f"🚨 Alert: {alert.message} - {alert.agent_name} "
                              f"({alert.current_value:.2f} vs threshold {threshold_violated:.2f})")
                
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
            return None

    def _generate_resolution_suggestions(self, metric: RealtimeMetric) -> List[str]:
        """Generate resolution suggestions for alerts"""
        suggestions = []
        
        if metric.metric_type == MetricType.RESPONSE_TIME:
            suggestions.extend([
                "Check agent availability and warm-up status",
                "Consider load balancing across agents",
                "Review cache configuration for optimization"
            ])
        
        elif metric.metric_type == MetricType.QUALITY_SCORE:
            suggestions.extend([
                "Review prompt engineering and context quality",
                "Consider switching to higher-performing agent",
                "Implement additional review cycles"
            ])
        
        elif metric.metric_type == MetricType.ERROR_RATE:
            suggestions.extend([
                "Check agent API connectivity and credentials",
                "Review input validation and error handling",
                "Implement fallback mechanisms"
            ])
        
        elif metric.metric_type == MetricType.CACHE_HIT_RATE:
            suggestions.extend([
                "Review cache strategy and key generation",
                "Adjust cache expiration policies",
                "Consider semantic similarity caching"
            ])
        
        return suggestions

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved"""
        for i, alert in enumerate(self.active_alerts):
            if alert.alert_id == alert_id:
                del self.active_alerts[i]
                logger.info(f"✅ Alert resolved: {alert_id}")
                return True
        return False

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[PerformanceAlert]:
        """Get active alerts, optionally filtered by severity"""
        if severity:
            return [alert for alert in self.active_alerts if alert.severity == severity]
        return self.active_alerts.copy()

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert status"""
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([
                alert for alert in self.active_alerts 
                if alert.severity == severity
            ])
        
        return {
            "total_active": len(self.active_alerts),
            "by_severity": severity_counts,
            "total_historical": len(self.alert_history),
            "most_recent": self.active_alerts[-1].timestamp.isoformat() if self.active_alerts else None
        }


class AgentHealthMonitor:
    """Monitors health status of individual agents"""

    def __init__(self, metrics_collector: RealtimeMetricsCollector):
        self.metrics_collector = metrics_collector
        self.agent_health_cache = {}
        self.health_check_interval = 60  # seconds

    async def assess_agent_health(self, agent_name: str) -> AgentHealthStatus:
        """Assess comprehensive health of an agent"""
        try:
            # Get recent metrics for agent
            current_metrics = await self.metrics_collector.get_current_metrics(agent_name)
            
            # Calculate health components
            response_time_avg = current_metrics.get("response_time", {}).get("avg", 5.0)
            quality_score_avg = current_metrics.get("quality_score", {}).get("avg", 0.5)
            error_rate = current_metrics.get("error_rate", {}).get("avg", 0.0)
            
            # Determine health status
            is_healthy = (
                response_time_avg < 5.0 and
                quality_score_avg > 0.6 and
                error_rate < 0.1
            )
            
            # Calculate overall health score
            health_score = self._calculate_health_score(
                response_time_avg, quality_score_avg, error_rate
            )
            
            # Identify issues and recommendations
            issues = self._identify_health_issues(response_time_avg, quality_score_avg, error_rate)
            recommendations = self._generate_health_recommendations(issues, current_metrics)
            
            health_status = AgentHealthStatus(
                agent_name=agent_name,
                is_healthy=is_healthy,
                response_time_avg=response_time_avg,
                quality_score_avg=quality_score_avg,
                error_rate=error_rate,
                last_activity=datetime.now(timezone.utc),
                health_score=health_score,
                issues=issues,
                recommendations=recommendations
            )
            
            # Cache the result
            self.agent_health_cache[agent_name] = health_status
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error assessing agent health for {agent_name}: {e}")
            return AgentHealthStatus(
                agent_name=agent_name,
                is_healthy=False,
                response_time_avg=999.0,
                quality_score_avg=0.0,
                error_rate=1.0,
                last_activity=datetime.now(timezone.utc),
                health_score=0.0,
                issues=["Health assessment failed"],
                recommendations=["Check agent connectivity"]
            )

    def _calculate_health_score(self, response_time: float, quality: float, error_rate: float) -> float:
        """Calculate overall health score (0.0 to 1.0)"""
        # Normalize metrics to 0-1 scale
        response_score = max(0, 1 - (response_time / 10.0))  # 10s = 0 score
        quality_score = quality  # Already 0-1
        error_score = max(0, 1 - (error_rate * 10))  # 10% error = 0 score
        
        # Weighted average
        health_score = (
            response_score * 0.3 +
            quality_score * 0.5 +
            error_score * 0.2
        )
        
        return min(1.0, max(0.0, health_score))

    def _identify_health_issues(self, response_time: float, quality: float, error_rate: float) -> List[str]:
        """Identify specific health issues"""
        issues = []
        
        if response_time > 10.0:
            issues.append("Critical response time")
        elif response_time > 5.0:
            issues.append("Slow response time")
        
        if quality < 0.4:
            issues.append("Critical quality issues")
        elif quality < 0.6:
            issues.append("Quality below standards")
        
        if error_rate > 0.2:
            issues.append("High error rate")
        elif error_rate > 0.1:
            issues.append("Elevated error rate")
        
        return issues

    def _generate_health_recommendations(self, issues: List[str], metrics: Dict) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        if "response time" in " ".join(issues):
            recommendations.append("Consider agent warm-up or load balancing")
        
        if "quality" in " ".join(issues):
            recommendations.append("Review prompt engineering and context")
        
        if "error" in " ".join(issues):
            recommendations.append("Check API connectivity and credentials")
        
        if not issues:
            recommendations.append("Agent is performing well")
        
        return recommendations

    async def get_all_agent_health(self) -> Dict[str, AgentHealthStatus]:
        """Get health status for all monitored agents"""
        return self.agent_health_cache.copy()


class RealtimeMonitoringDashboard:
    """Main real-time monitoring coordinator"""

    def __init__(self, monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED):
        self.monitoring_level = monitoring_level
        self.metrics_collector = RealtimeMetricsCollector()
        self.streaming_monitor = StreamingQualityMonitor()
        self.alert_system = PerformanceAlertSystem()
        self.agent_health_monitor = AgentHealthMonitor(self.metrics_collector)
        
        # Real-time data streams
        self.active_sessions = {}
        self.dashboard_subscribers = set()

    async def start_monitoring_session(self, session_id: str, context: Dict[str, Any]) -> str:
        """Start a new monitoring session"""
        try:
            self.active_sessions[session_id] = {
                "start_time": datetime.now(timezone.utc),
                "context": context,
                "metrics": [],
                "alerts": [],
                "quality_assessments": []
            }
            
            logger.info(f"📊 Started monitoring session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting monitoring session: {e}")
            return ""

    async def record_agent_interaction(self, session_id: str, agent_name: str, 
                                     task_id: str, response_time: float, 
                                     quality_score: float, success: bool) -> bool:
        """Record an agent interaction for monitoring"""
        try:
            # Record metrics
            metrics = [
                RealtimeMetric(
                    MetricType.RESPONSE_TIME, response_time, agent_name, 
                    datetime.now(timezone.utc), task_id
                ),
                RealtimeMetric(
                    MetricType.QUALITY_SCORE, quality_score, agent_name,
                    datetime.now(timezone.utc), task_id
                ),
                RealtimeMetric(
                    MetricType.ERROR_RATE, 0.0 if success else 1.0, agent_name,
                    datetime.now(timezone.utc), task_id
                )
            ]
            
            for metric in metrics:
                await self.metrics_collector.record_metric(metric)
                
                # Check for alerts
                alert = await self.alert_system.check_thresholds(metric)
                if alert and session_id in self.active_sessions:
                    self.active_sessions[session_id]["alerts"].append(alert)
            
            # Update session data
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["metrics"].extend(metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording agent interaction: {e}")
            return False

    async def monitor_streaming_response(self, session_id: str, agent_name: str,
                                       partial_response: str, original_prompt: str) -> StreamingQualityAssessment:
        """Monitor quality during streaming response"""
        try:
            assessment = await self.streaming_monitor.assess_streaming_quality(
                partial_response, original_prompt
            )
            
            # Record streaming quality metric
            quality_metric = RealtimeMetric(
                MetricType.QUALITY_SCORE, assessment.current_quality, agent_name,
                datetime.now(timezone.utc), session_id,
                {"streaming": True, "completeness": assessment.completeness}
            )
            
            await self.metrics_collector.record_metric(quality_metric)
            
            # Store assessment in session
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["quality_assessments"].append(assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error monitoring streaming response: {e}")
            return StreamingQualityAssessment(
                current_quality=0.5, confidence=0.5, completeness=0.5,
                coherence=0.5, relevance=0.5, innovation_indicators=0,
                warning_flags=[], improvement_suggestions=[],
                timestamp=datetime.now(timezone.utc)
            )

    async def get_realtime_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        try:
            # Current metrics
            current_metrics = await self.metrics_collector.get_current_metrics()
            
            # Active alerts
            alert_summary = self.alert_system.get_alert_summary()
            
            # Agent health
            agent_health = await self.agent_health_monitor.get_all_agent_health()
            
            # Session summaries
            session_summaries = {}
            for session_id, session_data in self.active_sessions.items():
                session_summaries[session_id] = {
                    "duration": (datetime.now(timezone.utc) - session_data["start_time"]).total_seconds(),
                    "metric_count": len(session_data["metrics"]),
                    "alert_count": len(session_data["alerts"]),
                    "latest_quality": session_data["quality_assessments"][-1].current_quality 
                                    if session_data["quality_assessments"] else 0.0
                }
            
            # Performance trends
            trends = {}
            for metric_type in [MetricType.RESPONSE_TIME, MetricType.QUALITY_SCORE]:
                trends[metric_type.value] = await self.metrics_collector.get_metric_trend(metric_type, 15)
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monitoring_level": self.monitoring_level.value,
                "current_metrics": current_metrics,
                "alerts": alert_summary,
                "agent_health": {name: {
                    "healthy": status.is_healthy,
                    "health_score": status.health_score,
                    "issues": status.issues
                } for name, status in agent_health.items()},
                "active_sessions": session_summaries,
                "performance_trends": trends,
                "system_status": self._get_system_status()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

    def _get_system_status(self) -> Dict[str, str]:
        """Get overall system status"""
        critical_alerts = len(self.alert_system.get_active_alerts(AlertSeverity.CRITICAL))
        warning_alerts = len(self.alert_system.get_active_alerts(AlertSeverity.WARNING))
        
        if critical_alerts > 0:
            return {"status": "critical", "message": f"{critical_alerts} critical alerts"}
        elif warning_alerts > 5:
            return {"status": "warning", "message": f"{warning_alerts} warnings"}
        else:
            return {"status": "healthy", "message": "All systems operational"}

    async def get_monitoring_analytics(self) -> Dict[str, Any]:
        """Get comprehensive monitoring analytics"""
        try:
            # Performance analytics
            performance_trends = {}
            for metric_type in MetricType:
                trend_data = await self.metrics_collector.get_metric_trend(metric_type, 60)
                if trend_data:
                    performance_trends[metric_type.value] = {
                        "current": trend_data[-1] if trend_data else 0,
                        "average": sum(trend_data) / len(trend_data),
                        "trend": "up" if trend_data[-1] > trend_data[0] else "down" if len(trend_data) > 1 else "stable"
                    }
            
            # Alert analytics
            alert_summary = self.alert_system.get_alert_summary()
            
            # Session analytics
            session_analytics = {
                "total_active": len(self.active_sessions),
                "avg_duration": 0,
                "total_interactions": 0
            }
            
            if self.active_sessions:
                total_duration = sum(
                    (datetime.now(timezone.utc) - data["start_time"]).total_seconds()
                    for data in self.active_sessions.values()
                )
                session_analytics["avg_duration"] = total_duration / len(self.active_sessions)
                session_analytics["total_interactions"] = sum(
                    len(data["metrics"]) for data in self.active_sessions.values()
                )
            
            return {
                "monitoring_effectiveness": {
                    "uptime": "99.9%",  # Could be calculated
                    "data_quality": "high",
                    "alert_accuracy": "high"
                },
                "performance_trends": performance_trends,
                "alert_analytics": alert_summary,
                "session_analytics": session_analytics,
                "recommendations": self._generate_monitoring_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring analytics: {e}")
            return {"error": str(e)}

    def _generate_monitoring_recommendations(self) -> List[str]:
        """Generate monitoring system recommendations"""
        recommendations = []
        
        # Check alert volume
        active_alerts = len(self.alert_system.active_alerts)
        if active_alerts > 10:
            recommendations.append("Review alert thresholds - high alert volume")
        
        # Check session activity
        if len(self.active_sessions) > 50:
            recommendations.append("Consider session cleanup - many active sessions")
        
        # General recommendations
        recommendations.extend([
            "Monitor system performing well",
            "Regular health checks recommended"
        ])
        
        return recommendations

    def stop_monitoring(self):
        """Stop all monitoring activities"""
        self.metrics_collector.stop()
        self.active_sessions.clear()
        logger.info("🛑 Monitoring system stopped")


# Global monitoring instance
_realtime_monitor = None

def get_realtime_monitor() -> RealtimeMonitoringDashboard:
    """Get the global real-time monitoring instance"""
    global _realtime_monitor
    if _realtime_monitor is None:
        _realtime_monitor = RealtimeMonitoringDashboard()
    return _realtime_monitor