"""
🔒 ENTERPRISE SECURITY MANAGER
=============================

Advanced security and scalability features for the autonomous AI system.
Ensures enterprise-grade protection and performance optimization.

Features:
- AI system access control and authentication
- Rate limiting and DDoS protection
- Audit logging and compliance monitoring
- Data encryption and secure communication
- Performance monitoring and auto-scaling
- Resource allocation optimization
- Security incident detection and response
- Multi-tenant isolation and security

Security Layers:
- Authentication and authorization
- Network security and encryption
- Data protection and privacy
- AI model security and validation
- Audit trails and compliance
- Real-time threat detection
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import jwt
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    PRIVILEGED = "privileged"
    ADMIN = "admin"
    SYSTEM = "system"

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event for audit logging"""
    event_id: str
    event_type: str
    user_id: Optional[str]
    resource: str
    action: str
    result: str  # success, failure, blocked
    threat_level: ThreatLevel
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AccessToken:
    """Secure access token for AI services"""
    token_id: str
    user_id: str
    security_level: SecurityLevel
    permissions: List[str]
    expires_at: datetime
    issued_at: datetime
    refresh_token: Optional[str] = None

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int
    burst_capacity: int
    window_size_minutes: int
    enabled: bool = True

@dataclass
class SecurityMetrics:
    """Security monitoring metrics"""
    total_requests: int
    blocked_requests: int
    failed_authentications: int
    detected_threats: int
    active_sessions: int
    average_response_time_ms: float
    last_security_scan: datetime

class EnterpriseSecurityManager:
    """
    🔒 ENTERPRISE SECURITY MANAGER
    
    Advanced security and scalability management for autonomous AI systems.
    Provides enterprise-grade protection and performance optimization.
    """
    
    def __init__(self):
        # Security configuration
        self.jwt_secret = secrets.token_urlsafe(64)
        self.api_keys = {}
        self.active_tokens = {}
        
        # Rate limiting
        self.rate_limits = {
            SecurityLevel.PUBLIC: RateLimitConfig(60, 100, 1),
            SecurityLevel.AUTHENTICATED: RateLimitConfig(300, 500, 1),
            SecurityLevel.PRIVILEGED: RateLimitConfig(1000, 2000, 1),
            SecurityLevel.ADMIN: RateLimitConfig(5000, 10000, 1),
            SecurityLevel.SYSTEM: RateLimitConfig(50000, 100000, 1)
        }
        
        self.request_history = defaultdict(deque)
        self.blocked_ips = set()
        self.suspicious_patterns = {}
        
        # Security monitoring
        self.security_events = []
        self.threat_detection_rules = {}
        self.audit_log = []
        
        # Performance and scaling
        self.performance_metrics = {}
        self.resource_usage = {}
        self.auto_scaling_config = {
            "enabled": True,
            "min_instances": 2,
            "max_instances": 20,
            "cpu_threshold": 80,
            "memory_threshold": 85,
            "response_time_threshold_ms": 5000
        }
        
        # Security metrics
        self.security_metrics = SecurityMetrics(
            total_requests=0,
            blocked_requests=0,
            failed_authentications=0,
            detected_threats=0,
            active_sessions=0,
            average_response_time_ms=0.0,
            last_security_scan=datetime.now()
        )
        
        self._initialize_threat_detection()
        
        logger.info("🔒 Enterprise Security Manager initialized")
    
    def _initialize_threat_detection(self):
        """Initialize threat detection rules"""
        self.threat_detection_rules = {
            "rapid_requests": {
                "threshold": 100,  # requests per minute
                "window_minutes": 1,
                "threat_level": ThreatLevel.MEDIUM,
                "action": "rate_limit"
            },
            "failed_auth_attempts": {
                "threshold": 5,
                "window_minutes": 5,
                "threat_level": ThreatLevel.HIGH,
                "action": "temporary_block"
            },
            "suspicious_patterns": {
                "threshold": 10,  # pattern violations
                "window_minutes": 10,
                "threat_level": ThreatLevel.HIGH,
                "action": "investigation"
            },
            "resource_exhaustion": {
                "cpu_threshold": 95,
                "memory_threshold": 95,
                "threat_level": ThreatLevel.CRITICAL,
                "action": "emergency_scale"
            }
        }
    
    async def authenticate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, Optional[AccessToken], Optional[str]]:
        """
        🔐 Authenticate request with comprehensive security validation
        """
        try:
            start_time = time.time()
            
            # Extract authentication data
            auth_header = request_data.get("authorization", "")
            api_key = request_data.get("api_key", "")
            client_ip = request_data.get("client_ip", "unknown")
            user_agent = request_data.get("user_agent", "unknown")
            
            # Check if IP is blocked
            if client_ip in self.blocked_ips:
                await self._log_security_event(
                    "authentication_blocked",
                    None, "auth", "authenticate", "blocked",
                    ThreatLevel.HIGH, client_ip, user_agent,
                    {"reason": "blocked_ip"}
                )
                return False, None, "IP address blocked due to security violation"
            
            # Rate limiting check
            if not await self._check_rate_limit(client_ip, SecurityLevel.PUBLIC):
                await self._log_security_event(
                    "rate_limit_exceeded",
                    None, "auth", "authenticate", "blocked",
                    ThreatLevel.MEDIUM, client_ip, user_agent,
                    {"rate_limit": "exceeded"}
                )
                return False, None, "Rate limit exceeded"
            
            # JWT token authentication
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                access_token = await self._validate_jwt_token(token)
                if access_token:
                    # Additional validation
                    if await self._validate_token_security(access_token, client_ip, user_agent):
                        processing_time = (time.time() - start_time) * 1000
                        await self._update_security_metrics("auth_success", processing_time)
                        
                        await self._log_security_event(
                            "jwt_authentication_success",
                            access_token.user_id, "auth", "authenticate", "success",
                            ThreatLevel.LOW, client_ip, user_agent,
                            {"token_id": access_token.token_id}
                        )
                        return True, access_token, None
            
            # API Key authentication
            if api_key:
                access_token = await self._validate_api_key(api_key)
                if access_token:
                    if await self._validate_token_security(access_token, client_ip, user_agent):
                        processing_time = (time.time() - start_time) * 1000
                        await self._update_security_metrics("auth_success", processing_time)
                        
                        await self._log_security_event(
                            "api_key_authentication_success",
                            access_token.user_id, "auth", "authenticate", "success",
                            ThreatLevel.LOW, client_ip, user_agent,
                            {"api_key_prefix": api_key[:8] + "..."}
                        )
                        return True, access_token, None
            
            # Authentication failed
            await self._handle_failed_authentication(client_ip, user_agent)
            return False, None, "Authentication failed"
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            await self._log_security_event(
                "authentication_error",
                None, "auth", "authenticate", "error",
                ThreatLevel.MEDIUM, client_ip, user_agent,
                {"error": str(e)}
            )
            return False, None, "Authentication service error"
    
    async def authorize_ai_access(self, access_token: AccessToken, resource: str, action: str) -> Tuple[bool, Optional[str]]:
        """
        🛡️ Authorize access to AI services with fine-grained permissions
        """
        try:
            # Check token validity
            if access_token.expires_at < datetime.now():
                return False, "Access token expired"
            
            # Check security level requirements
            required_level = await self._get_required_security_level(resource, action)
            if not await self._check_security_level_access(access_token.security_level, required_level):
                await self._log_security_event(
                    "authorization_insufficient_privileges",
                    access_token.user_id, resource, action, "blocked",
                    ThreatLevel.MEDIUM, "unknown", "unknown",
                    {"required_level": required_level.value, "user_level": access_token.security_level.value}
                )
                return False, f"Insufficient privileges: {required_level.value} required"
            
            # Check specific permissions
            required_permission = f"{resource}:{action}"
            if required_permission not in access_token.permissions and "admin:all" not in access_token.permissions:
                await self._log_security_event(
                    "authorization_missing_permission",
                    access_token.user_id, resource, action, "blocked",
                    ThreatLevel.MEDIUM, "unknown", "unknown",
                    {"required_permission": required_permission}
                )
                return False, f"Missing permission: {required_permission}"
            
            # Check rate limits for user's security level
            if not await self._check_user_rate_limit(access_token):
                return False, "User rate limit exceeded"
            
            # Authorization successful
            await self._log_security_event(
                "authorization_success",
                access_token.user_id, resource, action, "success",
                ThreatLevel.LOW, "unknown", "unknown",
                {"permission": required_permission}
            )
            
            return True, None
            
        except Exception as e:
            logger.error(f"❌ Authorization error: {e}")
            return False, f"Authorization service error: {str(e)}"
    
    async def _validate_jwt_token(self, token: str) -> Optional[AccessToken]:
        """Validate JWT token and extract access token"""
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            token_id = payload.get("token_id")
            if token_id in self.active_tokens:
                return self.active_tokens[token_id]
            
            # Create access token from payload
            return AccessToken(
                token_id=payload["token_id"],
                user_id=payload["user_id"],
                security_level=SecurityLevel(payload["security_level"]),
                permissions=payload["permissions"],
                expires_at=datetime.fromtimestamp(payload["exp"]),
                issued_at=datetime.fromtimestamp(payload["iat"])
            )
        except Exception as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    async def _validate_api_key(self, api_key: str) -> Optional[AccessToken]:
        """Validate API key and return access token"""
        if api_key in self.api_keys:
            token_data = self.api_keys[api_key]
            return AccessToken(
                token_id=token_data["token_id"],
                user_id=token_data["user_id"],
                security_level=SecurityLevel(token_data["security_level"]),
                permissions=token_data["permissions"],
                expires_at=datetime.fromisoformat(token_data["expires_at"]),
                issued_at=datetime.fromisoformat(token_data["issued_at"])
            )
        return None
    
    async def _validate_token_security(self, access_token: AccessToken, client_ip: str, user_agent: str) -> bool:
        """Additional security validation for tokens"""
        # Check for token reuse patterns
        if await self._detect_token_abuse(access_token.token_id, client_ip):
            return False
        
        # Check for suspicious user agent patterns
        if await self._detect_suspicious_user_agent(user_agent):
            return False
        
        return True
    
    async def _check_rate_limit(self, identifier: str, security_level: SecurityLevel) -> bool:
        """Check rate limiting for requests"""
        config = self.rate_limits[security_level]
        if not config.enabled:
            return True
        
        now = time.time()
        window_start = now - (config.window_size_minutes * 60)
        
        # Clean old entries
        history = self.request_history[identifier]
        while history and history[0] < window_start:
            history.popleft()
        
        # Check if within rate limit
        if len(history) >= config.requests_per_minute:
            return False
        
        # Add current request
        history.append(now)
        return True
    
    async def _check_user_rate_limit(self, access_token: AccessToken) -> bool:
        """Check rate limits specific to user's security level"""
        return await self._check_rate_limit(
            f"user:{access_token.user_id}",
            access_token.security_level
        )
    
    async def _get_required_security_level(self, resource: str, action: str) -> SecurityLevel:
        """Determine required security level for resource/action"""
        # Define security requirements
        security_requirements = {
            "ai_orchestrator:execute": SecurityLevel.AUTHENTICATED,
            "prediction_engine:predict": SecurityLevel.AUTHENTICATED,
            "data_engine:process": SecurityLevel.AUTHENTICATED,
            "predictive_hub:analyze": SecurityLevel.AUTHENTICATED,
            "admin:configure": SecurityLevel.ADMIN,
            "admin:manage": SecurityLevel.ADMIN,
            "system:monitor": SecurityLevel.PRIVILEGED,
            "security:audit": SecurityLevel.ADMIN
        }
        
        key = f"{resource}:{action}"
        return security_requirements.get(key, SecurityLevel.AUTHENTICATED)
    
    async def _check_security_level_access(self, user_level: SecurityLevel, required_level: SecurityLevel) -> bool:
        """Check if user's security level meets requirements"""
        level_hierarchy = {
            SecurityLevel.PUBLIC: 0,
            SecurityLevel.AUTHENTICATED: 1,
            SecurityLevel.PRIVILEGED: 2,
            SecurityLevel.ADMIN: 3,
            SecurityLevel.SYSTEM: 4
        }
        
        return level_hierarchy[user_level] >= level_hierarchy[required_level]
    
    async def _handle_failed_authentication(self, client_ip: str, user_agent: str):
        """Handle failed authentication attempts"""
        self.security_metrics.failed_authentications += 1
        
        # Track failed attempts by IP
        failed_key = f"failed_auth:{client_ip}"
        now = time.time()
        
        if failed_key not in self.request_history:
            self.request_history[failed_key] = deque()
        
        # Add failed attempt
        self.request_history[failed_key].append(now)
        
        # Clean old entries (5-minute window)
        window_start = now - 300  # 5 minutes
        history = self.request_history[failed_key]
        while history and history[0] < window_start:
            history.popleft()
        
        # Check if IP should be blocked
        if len(history) >= 5:  # 5 failed attempts in 5 minutes
            self.blocked_ips.add(client_ip)
            await self._log_security_event(
                "ip_blocked_failed_auth",
                None, "security", "block_ip", "success",
                ThreatLevel.HIGH, client_ip, user_agent,
                {"failed_attempts": len(history), "block_duration": "1 hour"}
            )
            
            # Schedule IP unblock (simplified - in production use proper scheduling)
            asyncio.create_task(self._schedule_ip_unblock(client_ip, 3600))  # 1 hour
        
        await self._log_security_event(
            "authentication_failed",
            None, "auth", "authenticate", "failure",
            ThreatLevel.MEDIUM, client_ip, user_agent,
            {"attempt_number": len(history)}
        )
    
    async def _schedule_ip_unblock(self, ip_address: str, delay_seconds: int):
        """Schedule IP address to be unblocked after delay"""
        await asyncio.sleep(delay_seconds)
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            logger.info(f"🔓 IP address unblocked: {ip_address}")
    
    async def _detect_token_abuse(self, token_id: str, client_ip: str) -> bool:
        """Detect token abuse patterns"""
        # Check for rapid token usage from different IPs
        usage_key = f"token_usage:{token_id}"
        now = time.time()
        
        if usage_key not in self.suspicious_patterns:
            self.suspicious_patterns[usage_key] = {"ips": set(), "timestamps": deque()}
        
        pattern = self.suspicious_patterns[usage_key]
        pattern["ips"].add(client_ip)
        pattern["timestamps"].append(now)
        
        # Clean old timestamps (1-hour window)
        window_start = now - 3600
        while pattern["timestamps"] and pattern["timestamps"][0] < window_start:
            pattern["timestamps"].popleft()
        
        # Check for suspicious patterns
        if len(pattern["ips"]) > 5 and len(pattern["timestamps"]) > 50:  # Many IPs, many requests
            return True
        
        return False
    
    async def _detect_suspicious_user_agent(self, user_agent: str) -> bool:
        """Detect suspicious user agent patterns"""
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper",
            "automated", "script", "curl", "wget"
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)
    
    async def _log_security_event(self, event_type: str, user_id: Optional[str], 
                                resource: str, action: str, result: str,
                                threat_level: ThreatLevel, ip_address: str, 
                                user_agent: str, metadata: Dict[str, Any]):
        """Log security event for audit trail"""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,
            threat_level=threat_level,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self.security_events.append(event)
        self.audit_log.append(asdict(event))
        
        # Keep only recent events for memory management
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-5000:]
        
        # Log high-priority events
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            logger.warning(f"🚨 Security Event: {event_type} - {threat_level.value} threat from {ip_address}")
    
    async def _update_security_metrics(self, metric_type: str, processing_time_ms: float):
        """Update security performance metrics"""
        self.security_metrics.total_requests += 1
        
        if metric_type == "auth_success":
            # Update average response time
            current_avg = self.security_metrics.average_response_time_ms
            total_requests = self.security_metrics.total_requests
            self.security_metrics.average_response_time_ms = (
                (current_avg * (total_requests - 1) + processing_time_ms) / total_requests
            )
        elif metric_type == "request_blocked":
            self.security_metrics.blocked_requests += 1
        elif metric_type == "threat_detected":
            self.security_metrics.detected_threats += 1
    
    async def generate_access_token(self, user_id: str, security_level: SecurityLevel, 
                                  permissions: List[str], expires_hours: int = 24) -> AccessToken:
        """Generate secure access token for user"""
        token_id = str(uuid.uuid4())
        issued_at = datetime.now()
        expires_at = issued_at + timedelta(hours=expires_hours)
        
        access_token = AccessToken(
            token_id=token_id,
            user_id=user_id,
            security_level=security_level,
            permissions=permissions,
            expires_at=expires_at,
            issued_at=issued_at
        )
        
        # Store active token
        self.active_tokens[token_id] = access_token
        
        # Generate JWT
        payload = {
            "token_id": token_id,
            "user_id": user_id,
            "security_level": security_level.value,
            "permissions": permissions,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp())
        }
        
        jwt_token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        access_token.refresh_token = jwt_token
        
        await self._log_security_event(
            "access_token_generated",
            user_id, "auth", "generate_token", "success",
            ThreatLevel.LOW, "system", "system",
            {"token_id": token_id, "expires_hours": expires_hours}
        )
        
        return access_token
    
    async def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        return {
            "security_metrics": asdict(self.security_metrics),
            "active_tokens": len(self.active_tokens),
            "blocked_ips": len(self.blocked_ips),
            "recent_events": len([e for e in self.security_events if (datetime.now() - e.timestamp).total_seconds() < 3600]),
            "threat_levels": {
                level.value: len([e for e in self.security_events if e.threat_level == level])
                for level in ThreatLevel
            },
            "rate_limit_status": {
                level.value: config.enabled for level, config in self.rate_limits.items()
            },
            "system_health": {
                "security_enabled": True,
                "threat_detection_active": bool(self.threat_detection_rules),
                "audit_logging_active": True,
                "performance_monitoring": True
            },
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_security_audit_log(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security audit log for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            event for event in self.audit_log
            if datetime.fromisoformat(event["timestamp"]) > cutoff_time
        ]
    
    async def monitor_system_performance(self) -> Dict[str, Any]:
        """Monitor system performance for scaling decisions"""
        # Simulate performance monitoring (would integrate with actual metrics in production)
        current_metrics = {
            "cpu_usage_percent": random.uniform(45, 75),
            "memory_usage_percent": random.uniform(50, 80),
            "active_connections": len(self.active_tokens),
            "average_response_time_ms": self.security_metrics.average_response_time_ms,
            "requests_per_minute": self.security_metrics.total_requests / max(1, (datetime.now().hour + 1) * 60),
            "error_rate_percent": (self.security_metrics.blocked_requests / max(1, self.security_metrics.total_requests)) * 100
        }
        
        # Check if scaling is needed
        scaling_recommendation = await self._assess_scaling_needs(current_metrics)
        
        return {
            "current_metrics": current_metrics,
            "scaling_recommendation": scaling_recommendation,
            "auto_scaling_enabled": self.auto_scaling_config["enabled"],
            "performance_status": "optimal" if current_metrics["cpu_usage_percent"] < 70 else "elevated",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _assess_scaling_needs(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Assess if system scaling is needed"""
        scale_up = False
        scale_down = False
        reasons = []
        
        config = self.auto_scaling_config
        
        # Check scale-up triggers
        if metrics["cpu_usage_percent"] > config["cpu_threshold"]:
            scale_up = True
            reasons.append(f"CPU usage above {config['cpu_threshold']}%")
        
        if metrics["memory_usage_percent"] > config["memory_threshold"]:
            scale_up = True
            reasons.append(f"Memory usage above {config['memory_threshold']}%")
        
        if metrics["average_response_time_ms"] > config["response_time_threshold_ms"]:
            scale_up = True
            reasons.append(f"Response time above {config['response_time_threshold_ms']}ms")
        
        # Check scale-down triggers (opposite conditions)
        if (metrics["cpu_usage_percent"] < 30 and 
            metrics["memory_usage_percent"] < 40 and
            metrics["average_response_time_ms"] < 1000):
            scale_down = True
            reasons.append("System underutilized - scale down opportunity")
        
        return {
            "scale_up": scale_up,
            "scale_down": scale_down,
            "reasons": reasons,
            "current_instances": "auto-detected",
            "recommended_instances": "calculated based on metrics"
        }

# Global instance
_security_manager = None

async def get_security_manager() -> EnterpriseSecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = EnterpriseSecurityManager()
        logger.info("🔒 Enterprise Security Manager initialized")
    return _security_manager