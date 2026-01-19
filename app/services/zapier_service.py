"""
Zapier Integration Service for ChatterFix CMMS

Provides webhook management and event dispatching for Zapier triggers.
Enables ChatterFix to connect with 5,000+ apps through Zapier.
"""

import asyncio
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ZapierEventType(str, Enum):
    """Events that can trigger Zapier workflows"""
    # Work Order Events
    WORK_ORDER_CREATED = "work_order.created"
    WORK_ORDER_UPDATED = "work_order.updated"
    WORK_ORDER_COMPLETED = "work_order.completed"
    WORK_ORDER_STATUS_CHANGED = "work_order.status_changed"
    WORK_ORDER_ASSIGNED = "work_order.assigned"
    WORK_ORDER_OVERDUE = "work_order.overdue"

    # Asset Events
    ASSET_CREATED = "asset.created"
    ASSET_UPDATED = "asset.updated"
    ASSET_STATUS_CHANGED = "asset.status_changed"
    ASSET_CRITICAL = "asset.critical"

    # Preventive Maintenance Events
    PM_DUE = "pm.due"
    PM_OVERDUE = "pm.overdue"
    PM_COMPLETED = "pm.completed"

    # Inventory Events
    PART_LOW_STOCK = "part.low_stock"
    PART_OUT_OF_STOCK = "part.out_of_stock"

    # Safety Events
    SAFETY_INCIDENT = "safety.incident"
    SAFETY_HAZARD_DETECTED = "safety.hazard_detected"


class WebhookSubscription(BaseModel):
    """A Zapier webhook subscription"""
    id: str
    organization_id: str
    event_type: ZapierEventType
    webhook_url: str
    api_key_hash: str  # Hashed for security
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_triggered: Optional[str] = None
    trigger_count: int = 0


class WebhookPayload(BaseModel):
    """Standard payload sent to Zapier webhooks"""
    event_type: str
    timestamp: str
    organization_id: str
    data: Dict[str, Any]


class ZapierService:
    """
    Manages Zapier webhook subscriptions and event dispatching.

    Features:
    - Webhook subscription CRUD
    - Event dispatching with retry logic
    - API key management for authentication
    - Rate limiting and security
    """

    def __init__(self, firestore_manager=None):
        self.firestore_manager = firestore_manager
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._subscriptions_cache: Dict[str, List[WebhookSubscription]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamp: Dict[str, float] = {}

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    # ==================== API Key Management ====================

    def generate_api_key(self) -> str:
        """Generate a secure API key for Zapier authentication"""
        return f"zk_{secrets.token_urlsafe(32)}"

    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """Verify an API key against stored hash"""
        return hmac.compare_digest(self.hash_api_key(api_key), stored_hash)

    # ==================== Subscription Management ====================

    async def create_subscription(
        self,
        organization_id: str,
        event_type: ZapierEventType,
        webhook_url: str,
    ) -> Dict[str, Any]:
        """
        Create a new webhook subscription.
        Returns the subscription and a NEW API key (only shown once).
        """
        api_key = self.generate_api_key()

        subscription_id = f"sub_{secrets.token_urlsafe(16)}"

        subscription = WebhookSubscription(
            id=subscription_id,
            organization_id=organization_id,
            event_type=event_type,
            webhook_url=webhook_url,
            api_key_hash=self.hash_api_key(api_key),
        )

        # Store in Firestore
        if self.firestore_manager:
            await self.firestore_manager.create_document(
                "zapier_subscriptions",
                subscription.model_dump(),
                document_id=subscription_id
            )

        # Invalidate cache
        self._invalidate_cache(organization_id)

        logger.info(f"Created Zapier subscription {subscription_id} for {event_type}")

        return {
            "subscription": subscription.model_dump(),
            "api_key": api_key,  # Only returned on creation!
            "message": "Save this API key - it won't be shown again"
        }

    async def get_subscriptions(
        self,
        organization_id: str,
        event_type: Optional[ZapierEventType] = None
    ) -> List[WebhookSubscription]:
        """Get all subscriptions for an organization"""
        # Check cache
        cache_key = f"{organization_id}:{event_type or 'all'}"
        if self._is_cache_valid(cache_key):
            return self._subscriptions_cache.get(cache_key, [])

        filters = [
            {"field": "organization_id", "operator": "==", "value": organization_id},
            {"field": "is_active", "operator": "==", "value": True},
        ]

        if event_type:
            filters.append({"field": "event_type", "operator": "==", "value": event_type.value})

        if self.firestore_manager:
            docs = await self.firestore_manager.get_collection(
                "zapier_subscriptions",
                filters=filters
            )
            subscriptions = [WebhookSubscription(**doc) for doc in docs]
        else:
            subscriptions = []

        # Update cache
        self._subscriptions_cache[cache_key] = subscriptions
        self._cache_timestamp[cache_key] = datetime.now(timezone.utc).timestamp()

        return subscriptions

    async def delete_subscription(
        self,
        subscription_id: str,
        organization_id: str,
        api_key: str
    ) -> bool:
        """Delete a subscription (requires API key verification)"""
        if self.firestore_manager:
            doc = await self.firestore_manager.get_document(
                "zapier_subscriptions",
                subscription_id
            )

            if not doc:
                return False

            # Verify ownership and API key
            if doc.get("organization_id") != organization_id:
                return False

            if not self.verify_api_key(api_key, doc.get("api_key_hash", "")):
                return False

            await self.firestore_manager.delete_document(
                "zapier_subscriptions",
                subscription_id
            )

            self._invalidate_cache(organization_id)
            logger.info(f"Deleted Zapier subscription {subscription_id}")
            return True

        return False

    async def update_subscription(
        self,
        subscription_id: str,
        organization_id: str,
        api_key: str,
        updates: Dict[str, Any]
    ) -> Optional[WebhookSubscription]:
        """Update a subscription (requires API key verification)"""
        if self.firestore_manager:
            doc = await self.firestore_manager.get_document(
                "zapier_subscriptions",
                subscription_id
            )

            if not doc or doc.get("organization_id") != organization_id:
                return None

            if not self.verify_api_key(api_key, doc.get("api_key_hash", "")):
                return None

            # Only allow updating certain fields
            allowed_updates = {
                k: v for k, v in updates.items()
                if k in ["webhook_url", "is_active"]
            }

            if allowed_updates:
                await self.firestore_manager.update_document(
                    "zapier_subscriptions",
                    subscription_id,
                    allowed_updates
                )

                self._invalidate_cache(organization_id)

                # Return updated subscription
                doc.update(allowed_updates)
                return WebhookSubscription(**doc)

        return None

    # ==================== Event Dispatching ====================

    async def dispatch_event(
        self,
        organization_id: str,
        event_type: ZapierEventType,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dispatch an event to all subscribed webhooks.
        Returns results of webhook calls.
        """
        subscriptions = await self.get_subscriptions(organization_id, event_type)

        if not subscriptions:
            logger.debug(f"No subscriptions for {event_type} in org {organization_id}")
            return {"dispatched": 0, "results": []}

        payload = WebhookPayload(
            event_type=event_type.value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            organization_id=organization_id,
            data=data
        )

        # Dispatch to all subscribers concurrently
        tasks = [
            self._send_webhook(sub, payload)
            for sub in subscriptions
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))

        logger.info(
            f"Dispatched {event_type} to {len(subscriptions)} webhooks, "
            f"{success_count} successful"
        )

        return {
            "dispatched": len(subscriptions),
            "successful": success_count,
            "results": [r if isinstance(r, dict) else {"error": str(r)} for r in results]
        }

    async def _send_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Send webhook with retry logic"""
        for attempt in range(max_retries):
            try:
                response = await self.http_client.post(
                    subscription.webhook_url,
                    json=payload.model_dump(),
                    headers={
                        "Content-Type": "application/json",
                        "X-ChatterFix-Event": payload.event_type,
                        "X-ChatterFix-Timestamp": payload.timestamp,
                    }
                )

                success = 200 <= response.status_code < 300

                # Update subscription stats
                if self.firestore_manager:
                    await self.firestore_manager.update_document(
                        "zapier_subscriptions",
                        subscription.id,
                        {
                            "last_triggered": datetime.now(timezone.utc).isoformat(),
                            "trigger_count": subscription.trigger_count + 1
                        }
                    )

                return {
                    "success": success,
                    "subscription_id": subscription.id,
                    "status_code": response.status_code,
                    "attempt": attempt + 1
                }

            except Exception as e:
                logger.warning(
                    f"Webhook attempt {attempt + 1} failed for {subscription.id}: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {
            "success": False,
            "subscription_id": subscription.id,
            "error": "Max retries exceeded"
        }

    # ==================== Cache Management ====================

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self._cache_timestamp:
            return False
        age = datetime.now(timezone.utc).timestamp() - self._cache_timestamp[cache_key]
        return age < self._cache_ttl

    def _invalidate_cache(self, organization_id: str):
        """Invalidate all cache entries for an organization"""
        keys_to_remove = [
            k for k in self._subscriptions_cache.keys()
            if k.startswith(organization_id)
        ]
        for key in keys_to_remove:
            self._subscriptions_cache.pop(key, None)
            self._cache_timestamp.pop(key, None)


# ==================== Event Helper Functions ====================

# Global service instance (initialized in main.py)
_zapier_service: Optional[ZapierService] = None


def get_zapier_service() -> ZapierService:
    """Get the global Zapier service instance"""
    global _zapier_service
    if _zapier_service is None:
        _zapier_service = ZapierService()
    return _zapier_service


def set_zapier_service(service: ZapierService):
    """Set the global Zapier service instance"""
    global _zapier_service
    _zapier_service = service


async def trigger_zapier_event(
    organization_id: str,
    event_type: ZapierEventType,
    data: Dict[str, Any]
):
    """
    Convenience function to trigger Zapier events from anywhere in the app.

    Usage:
        from app.services.zapier_service import trigger_zapier_event, ZapierEventType

        await trigger_zapier_event(
            organization_id=user.organization_id,
            event_type=ZapierEventType.WORK_ORDER_CREATED,
            data={"id": wo.id, "title": wo.title, ...}
        )
    """
    service = get_zapier_service()
    try:
        await service.dispatch_event(organization_id, event_type, data)
    except Exception as e:
        # Log but don't fail - Zapier events are non-critical
        logger.error(f"Failed to dispatch Zapier event {event_type}: {e}")
