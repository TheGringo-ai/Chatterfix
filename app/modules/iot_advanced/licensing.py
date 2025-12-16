"""
ChatterFix IoT Advanced Module - Licensing System
Controls access to premium IoT features based on customer subscription

NOTE: This module now wraps the unified premium_licensing system.
All premium modules (IoT, Quality, Safety) use the same licensing infrastructure.
"""

import logging
from typing import Dict
from functools import wraps

logger = logging.getLogger(__name__)

# Import from the unified premium licensing system
try:
    from app.modules.premium_licensing import (
        premium_licensing_manager,
        PremiumModule,
        LicenseTier,
        PremiumLicense,
        require_iot_license,
        require_enterprise_license,
        check_iot_access,
        get_license_status,
        get_current_customer_id,
        get_customer_id_from_user,
        PREMIUM_MODULE_PRICING
    )
    PREMIUM_LICENSING_AVAILABLE = True
except ImportError:
    PREMIUM_LICENSING_AVAILABLE = False
    logger.warning("Premium licensing module not available - using fallback")


# Backwards compatibility aliases
class LicenseLevel:
    """License tier definitions (backwards compatibility)"""
    CORE = "core"
    IOT_ADVANCED = "iot_advanced"
    QUALITY_FIX = "quality_fix"
    SAFETY_FIX = "safety_fix"
    ENTERPRISE = "enterprise"


if PREMIUM_LICENSING_AVAILABLE:
    # Use the unified licensing manager
    licensing_manager = premium_licensing_manager
    ChatterFixLicense = PremiumLicense
else:
    # Fallback implementation for backwards compatibility
    from datetime import datetime, timedelta

    class ChatterFixLicense:
        """Fallback license class"""
        def __init__(self, customer_id: str, license_data: Dict):
            self.customer_id = customer_id
            self.tier = license_data.get("tier", LicenseLevel.CORE)
            self.features = license_data.get("features", [])
            self.sensor_limit = license_data.get("sensor_limit", 0)
            self.api_limit = license_data.get("api_calls_per_month", 1000)
            self.expires_at = license_data.get("expires_at")
            self.is_trial = license_data.get("is_trial", False)
            self.trial_days_remaining = license_data.get("trial_days_remaining", 0)

        @property
        def has_iot_access(self) -> bool:
            return self.tier in [LicenseLevel.IOT_ADVANCED, LicenseLevel.ENTERPRISE]

        @property
        def has_enterprise_access(self) -> bool:
            return self.tier == LicenseLevel.ENTERPRISE

        @property
        def is_expired(self) -> bool:
            if not self.expires_at:
                return False
            try:
                return datetime.now() > datetime.fromisoformat(self.expires_at)
            except:
                return False

    class FallbackLicensingManager:
        """Fallback licensing manager"""
        async def get_customer_license(self, customer_id: str) -> ChatterFixLicense:
            # Development mode - return full access
            return ChatterFixLicense(customer_id, {
                "tier": LicenseLevel.ENTERPRISE,
                "features": ["voice", "vision", "iot", "quality", "safety"],
                "sensor_limit": 100,
                "api_calls_per_month": 50000,
                "is_trial": True,
                "trial_days_remaining": 30
            })

        async def check_feature_access(self, customer_id: str, feature: str) -> bool:
            return True  # Allow all in fallback mode

    licensing_manager = FallbackLicensingManager()

    def get_current_customer_id() -> str:
        return "demo_customer_1"

    def require_iot_license(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper

    def require_enterprise_license(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper

    async def check_iot_access(customer_id: str) -> bool:
        return True

    async def get_license_status(customer_id: str) -> Dict:
        return {
            "customer_id": customer_id,
            "tier": "enterprise",
            "modules_enabled": {"iot_advanced": True, "quality_fix": True, "safety_fix": True},
            "is_trial": True
        }


async def validate_sensor_count(customer_id: str, sensor_count: int) -> Dict:
    """Validate if customer can add more sensors"""
    if PREMIUM_LICENSING_AVAILABLE:
        license_obj = await premium_licensing_manager.get_customer_license(customer_id)
        sensor_limit = license_obj.sensor_limit
    else:
        sensor_limit = 100  # Default for fallback

    if sensor_limit == 0:
        return {
            "valid": False,
            "message": "Sensor monitoring requires IoT Advanced Module",
            "upgrade_required": True
        }
    elif sensor_limit == -1:
        return {
            "valid": True,
            "message": "Unlimited sensors available"
        }
    elif sensor_count <= sensor_limit:
        return {
            "valid": True,
            "message": f"Sensors: {sensor_count}/{sensor_limit}",
            "remaining": sensor_limit - sensor_count
        }
    else:
        return {
            "valid": False,
            "message": f"Sensor limit exceeded: {sensor_count}/{sensor_limit}",
            "upgrade_required": True
        }


logger.info("IoT Advanced Licensing initialized (using unified premium licensing system)")