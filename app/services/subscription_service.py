"""
Subscription Service
Handles free trial, subscription status, and access control
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from app.core.firestore_db import get_firestore_manager

logger = logging.getLogger(__name__)

# Trial configuration
FREE_TRIAL_DAYS = 30


class SubscriptionStatus(str, Enum):
    """Subscription status values"""
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionService:
    """Service for managing subscriptions and trial periods"""

    def __init__(self):
        self.firestore = None

    def _get_firestore(self):
        """Lazy load Firestore manager"""
        if not self.firestore:
            self.firestore = get_firestore_manager()
        return self.firestore

    def calculate_trial_dates(self) -> Dict[str, str]:
        """Calculate trial start and end dates"""
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=FREE_TRIAL_DAYS)
        return {
            "trial_start_date": now.isoformat(),
            "trial_end_date": trial_end.isoformat(),
            "subscription_status": SubscriptionStatus.TRIAL,
            "days_remaining": FREE_TRIAL_DAYS,
        }

    async def get_subscription_status(self, organization_id: str) -> Dict[str, Any]:
        """
        Get the subscription status for an organization
        Returns trial days remaining, status, and access permissions
        """
        try:
            firestore = self._get_firestore()
            org = await firestore.get_document("organizations", organization_id)

            if not org:
                return {
                    "status": SubscriptionStatus.EXPIRED,
                    "has_access": False,
                    "days_remaining": 0,
                    "message": "Organization not found",
                }

            subscription_status = org.get("subscription_status", SubscriptionStatus.TRIAL)
            trial_end_str = org.get("trial_end_date")

            # If active subscription, always grant access
            if subscription_status == SubscriptionStatus.ACTIVE:
                return {
                    "status": SubscriptionStatus.ACTIVE,
                    "has_access": True,
                    "days_remaining": None,  # Unlimited for paid
                    "message": "Active subscription",
                    "plan": org.get("subscription_plan", "professional"),
                }

            # Check trial period
            if trial_end_str:
                try:
                    # Handle both ISO format and datetime objects
                    if isinstance(trial_end_str, str):
                        trial_end = datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
                    else:
                        trial_end = trial_end_str

                    now = datetime.now(timezone.utc)

                    if now < trial_end:
                        days_remaining = (trial_end - now).days
                        return {
                            "status": SubscriptionStatus.TRIAL,
                            "has_access": True,
                            "days_remaining": max(0, days_remaining),
                            "trial_end_date": trial_end.isoformat(),
                            "message": f"Free trial: {days_remaining} days remaining",
                        }
                    else:
                        # Trial expired
                        return {
                            "status": SubscriptionStatus.EXPIRED,
                            "has_access": False,
                            "days_remaining": 0,
                            "trial_end_date": trial_end.isoformat(),
                            "message": "Free trial expired. Please upgrade to continue.",
                        }
                except Exception as e:
                    logger.error(f"Error parsing trial date: {e}")

            # No trial date set - assume new account, grant trial
            return {
                "status": SubscriptionStatus.TRIAL,
                "has_access": True,
                "days_remaining": FREE_TRIAL_DAYS,
                "message": f"Free trial: {FREE_TRIAL_DAYS} days",
            }

        except Exception as e:
            logger.error(f"Error checking subscription status: {e}")
            # SECURITY: Fail closed - deny access on error to prevent unauthorized access
            return {
                "status": SubscriptionStatus.EXPIRED,
                "has_access": False,
                "days_remaining": 0,
                "message": "Unable to verify subscription status. Please try again or contact support.",
                "error": True,
            }

    async def check_access(self, organization_id: str) -> bool:
        """
        Simple check if organization has access to the system
        Returns True if they have an active subscription or valid trial
        """
        status = await self.get_subscription_status(organization_id)
        return status.get("has_access", False)

    async def activate_subscription(
        self,
        organization_id: str,
        plan: str = "professional",
        months: int = 12,
    ) -> Dict[str, Any]:
        """
        Activate a paid subscription for an organization
        """
        try:
            firestore = self._get_firestore()
            now = datetime.now(timezone.utc)
            subscription_end = now + timedelta(days=months * 30)

            update_data = {
                "subscription_status": SubscriptionStatus.ACTIVE,
                "subscription_plan": plan,
                "subscription_start_date": now.isoformat(),
                "subscription_end_date": subscription_end.isoformat(),
                "updated_at": now.isoformat(),
            }

            await firestore.update_document("organizations", organization_id, update_data)

            return {
                "success": True,
                "status": SubscriptionStatus.ACTIVE,
                "plan": plan,
                "valid_until": subscription_end.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error activating subscription: {e}")
            return {"success": False, "error": str(e)}

    async def extend_trial(self, organization_id: str, extra_days: int = 14) -> Dict[str, Any]:
        """
        Extend trial period for an organization (for special cases)
        """
        try:
            firestore = self._get_firestore()
            org = await firestore.get_document("organizations", organization_id)

            if not org:
                return {"success": False, "error": "Organization not found"}

            current_end_str = org.get("trial_end_date")
            if current_end_str:
                if isinstance(current_end_str, str):
                    current_end = datetime.fromisoformat(current_end_str.replace('Z', '+00:00'))
                else:
                    current_end = current_end_str
            else:
                current_end = datetime.now(timezone.utc)

            new_end = current_end + timedelta(days=extra_days)

            await firestore.update_document(
                "organizations",
                organization_id,
                {
                    "trial_end_date": new_end.isoformat(),
                    "trial_extended": True,
                    "trial_extension_days": extra_days,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            return {
                "success": True,
                "new_trial_end": new_end.isoformat(),
                "extended_by_days": extra_days,
            }

        except Exception as e:
            logger.error(f"Error extending trial: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_subscription_service = None


def get_subscription_service() -> SubscriptionService:
    """Get the subscription service singleton"""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service
