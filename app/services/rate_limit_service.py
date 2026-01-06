"""
Tiered Rate Limiting Service for ChatterFix
Firestore-configurable limits that scale with customer plans.

Features:
- Limits by org_id > user_id > IP (in priority order)
- Editable via Firestore without redeploying
- Plan tiers: public, trial, pro, enterprise
- Soft landing with proper 429 + headers
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from functools import wraps

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a plan/org"""
    plan: str
    requests_per_minute: int
    burst_limit: int
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict) -> "RateLimitConfig":
        return cls(
            plan=data.get("plan", "public"),
            requests_per_minute=data.get("rpm", 30),
            burst_limit=data.get("burst", 15),
            enabled=data.get("enabled", True)
        )


# Default limits by plan tier (fallback if Firestore unavailable)
DEFAULT_LIMITS = {
    "public": RateLimitConfig(plan="public", requests_per_minute=30, burst_limit=15),
    "trial": RateLimitConfig(plan="trial", requests_per_minute=120, burst_limit=60),
    "pro": RateLimitConfig(plan="pro", requests_per_minute=600, burst_limit=200),
    "enterprise": RateLimitConfig(plan="enterprise", requests_per_minute=3000, burst_limit=1000),
}

# In-memory cache for rate limit configs (refresh every 5 min)
_config_cache: Dict[str, Tuple[RateLimitConfig, float]] = {}
_CACHE_TTL = 300  # 5 minutes

# In-memory request counters (simple sliding window)
_request_counts: Dict[str, list] = {}


class RateLimitService:
    """
    Firestore-backed rate limiting service.

    Limits are stored in Firestore and can be edited without redeploying:
    - rate_limits/default - Default limits for each plan
    - rate_limits/{org_id} - Override limits for specific orgs
    """

    def __init__(self):
        self.firestore = None
        self._initialized = False

    def _ensure_initialized(self):
        if not self._initialized:
            try:
                self.firestore = get_firestore_manager()
                self._initialized = True
            except Exception as e:
                logger.warning(f"Firestore not available for rate limits: {e}")

    async def get_limit_config(self, org_id: Optional[str] = None, plan: str = "public") -> RateLimitConfig:
        """
        Get rate limit config for an org or plan.

        Priority:
        1. Org-specific override (rate_limits/{org_id})
        2. Plan default from Firestore (rate_limits/defaults)
        3. Hardcoded defaults
        """
        self._ensure_initialized()

        # Check cache first
        cache_key = org_id or f"plan:{plan}"
        if cache_key in _config_cache:
            config, cached_at = _config_cache[cache_key]
            if time.time() - cached_at < _CACHE_TTL:
                return config

        # Try to get from Firestore
        if self.firestore:
            try:
                # Check org-specific override first
                if org_id:
                    org_config = await self.firestore.get_document("rate_limits", org_id)
                    if org_config:
                        config = RateLimitConfig.from_dict(org_config)
                        _config_cache[cache_key] = (config, time.time())
                        return config

                # Check plan defaults
                defaults_doc = await self.firestore.get_document("rate_limits", "defaults")
                if defaults_doc and plan in defaults_doc:
                    config = RateLimitConfig.from_dict(defaults_doc[plan])
                    _config_cache[cache_key] = (config, time.time())
                    return config

            except Exception as e:
                logger.warning(f"Error fetching rate limits from Firestore: {e}")

        # Fall back to hardcoded defaults
        config = DEFAULT_LIMITS.get(plan, DEFAULT_LIMITS["public"])
        _config_cache[cache_key] = (config, time.time())
        return config

    def _get_key(self, request: Request, org_id: Optional[str], user_id: Optional[str]) -> str:
        """Get rate limit key in priority order: org > user > IP"""
        if org_id:
            return f"org:{org_id}"
        if user_id:
            return f"user:{user_id}"
        # Fallback to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _check_limit(self, key: str, config: RateLimitConfig) -> Tuple[bool, int, int]:
        """
        Check if request is within limits using sliding window.

        Returns: (allowed, remaining, reset_seconds)
        """
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Get or create request list for this key
        if key not in _request_counts:
            _request_counts[key] = []

        # Remove old requests outside the window
        _request_counts[key] = [t for t in _request_counts[key] if t > window_start]

        current_count = len(_request_counts[key])
        remaining = max(0, config.requests_per_minute - current_count)

        # Check burst (requests in last 5 seconds)
        burst_window = now - 5
        burst_count = len([t for t in _request_counts[key] if t > burst_window])

        if current_count >= config.requests_per_minute:
            # Over minute limit
            oldest = min(_request_counts[key]) if _request_counts[key] else now
            reset_seconds = int(60 - (now - oldest)) + 1
            return False, 0, reset_seconds

        if burst_count >= config.burst_limit:
            # Over burst limit
            return False, remaining, 5

        # Allow and record
        _request_counts[key].append(now)
        return True, remaining - 1, 60

    async def check_rate_limit(
        self,
        request: Request,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        plan: str = "public"
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Check if request is rate limited.

        Returns: (allowed, headers_dict)
        """
        config = await self.get_limit_config(org_id, plan)

        if not config.enabled:
            return True, {}

        key = self._get_key(request, org_id, user_id)
        allowed, remaining, reset = self._check_limit(key, config)

        headers = {
            "X-RateLimit-Limit": str(config.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset),
            "X-RateLimit-Plan": config.plan,
        }

        if not allowed:
            headers["Retry-After"] = str(reset)

        return allowed, headers


# Singleton instance
_rate_limit_service: Optional[RateLimitService] = None


def get_rate_limit_service() -> RateLimitService:
    global _rate_limit_service
    if _rate_limit_service is None:
        _rate_limit_service = RateLimitService()
    return _rate_limit_service


async def check_rate_limit(
    request: Request,
    org_id: Optional[str] = None,
    user_id: Optional[str] = None,
    plan: str = "public"
) -> Optional[JSONResponse]:
    """
    Check rate limit and return 429 response if exceeded.

    Usage in route:
        rate_limit_response = await check_rate_limit(request, org_id=user.organization_id)
        if rate_limit_response:
            return rate_limit_response
    """
    service = get_rate_limit_service()
    allowed, headers = await service.check_rate_limit(request, org_id, user_id, plan)

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please slow down or upgrade your plan.",
                "retry_after": int(headers.get("Retry-After", 60)),
                "plan": headers.get("X-RateLimit-Plan", "public"),
                "upgrade_url": "https://chatterfix.com/pricing"
            },
            headers=headers
        )

    return None


def rate_limited(plan: str = "public"):
    """
    Decorator for rate-limited endpoints.

    Usage:
        @router.get("/api/data")
        @rate_limited(plan="trial")
        async def get_data(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Try to get org_id/user_id from request state or cookies
            org_id = getattr(request.state, 'org_id', None)
            user_id = getattr(request.state, 'user_id', None)

            # Check if user is authenticated and get their plan
            current_plan = plan
            if org_id:
                # Could check org's actual plan from Firestore here
                current_plan = getattr(request.state, 'plan', plan)

            response = await check_rate_limit(request, org_id, user_id, current_plan)
            if response:
                return response

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


async def seed_default_rate_limits():
    """
    Seed default rate limit configs to Firestore.
    Run once to initialize the rate_limits collection.
    """
    try:
        firestore = get_firestore_manager()

        defaults = {
            "public": {"plan": "public", "rpm": 30, "burst": 15, "enabled": True},
            "trial": {"plan": "trial", "rpm": 120, "burst": 60, "enabled": True},
            "pro": {"plan": "pro", "rpm": 600, "burst": 200, "enabled": True},
            "enterprise": {"plan": "enterprise", "rpm": 3000, "burst": 1000, "enabled": True},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        await firestore.set_document("rate_limits", "defaults", defaults)
        logger.info("Seeded default rate limits to Firestore")
        return True

    except Exception as e:
        logger.error(f"Failed to seed rate limits: {e}")
        return False
