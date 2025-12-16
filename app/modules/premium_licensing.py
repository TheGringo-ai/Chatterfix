"""
ChatterFix Premium Modules - Unified Licensing System
Controls access to all premium features: IoT Advanced, QualityFix, SafetyFix

Premium Module Pricing:
- IoT Advanced: $199/month + $25/sensor
- QualityFix: $99/month (HACCP, ISO, Food Safety compliance)
- SafetyFix: $99/month (OSHA, Incident tracking, Lab results)
- Enterprise Bundle: $299/technician/month (includes all modules)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

# License server configuration
LICENSE_SERVER = os.getenv("CHATTERFIX_LICENSE_SERVER", "https://licensing.chatterfix.com")
LICENSE_API_KEY = os.getenv("CHATTERFIX_LICENSE_API_KEY")


class PremiumModule(str, Enum):
    """Available premium modules"""
    IOT_ADVANCED = "iot_advanced"
    QUALITY_FIX = "quality_fix"
    SAFETY_FIX = "safety_fix"
    ENTERPRISE = "enterprise"


class LicenseTier(str, Enum):
    """License tier definitions"""
    CORE = "core"
    IOT_ADVANCED = "iot_advanced"
    QUALITY_FIX = "quality_fix"
    SAFETY_FIX = "safety_fix"
    ENTERPRISE = "enterprise"


# Module pricing configuration
PREMIUM_MODULE_PRICING = {
    PremiumModule.IOT_ADVANCED: {
        "name": "IoT Advanced",
        "base_price": 199,
        "per_sensor_price": 25,
        "description": "Real-time sensor monitoring, predictive analytics, and advanced alerts",
        "features": [
            "Real-time sensor monitoring",
            "Predictive maintenance analytics",
            "Advanced alerting system",
            "Voice-integrated sensor queries",
            "Custom dashboard builder",
            "Historical trend analysis",
            "MQTT, Modbus, HTTP API support"
        ],
        "upgrade_url": "https://chatterfix.com/upgrade/iot-advanced"
    },
    PremiumModule.QUALITY_FIX: {
        "name": "QualityFix",
        "base_price": 99,
        "description": "Comprehensive quality management with HACCP, ISO, and food safety compliance",
        "features": [
            "HACCP plan management",
            "Temperature monitoring & compliance",
            "Batch traceability system",
            "Supplier quality audits",
            "Food safety inspections",
            "Sanitation schedules",
            "Environmental monitoring",
            "CAPA records management",
            "ISO 22000/FSSC 22000 compliance",
            "AI-powered quality insights"
        ],
        "upgrade_url": "https://chatterfix.com/upgrade/quality-fix"
    },
    PremiumModule.SAFETY_FIX: {
        "name": "SafetyFix",
        "base_price": 99,
        "description": "Enterprise safety management with OSHA compliance and incident tracking",
        "features": [
            "Incident tracking & investigation",
            "Safety violation management",
            "Lab results & environmental testing",
            "Safety inspections & audits",
            "OSHA compliance reporting",
            "AI-powered safety analysis",
            "Risk assessment tools",
            "Safety training tracking",
            "Near-miss reporting",
            "Cost-benefit safety analytics"
        ],
        "upgrade_url": "https://chatterfix.com/upgrade/safety-fix"
    },
    PremiumModule.ENTERPRISE: {
        "name": "Enterprise Bundle",
        "per_technician_price": 299,
        "description": "Complete platform with all premium modules and enterprise features",
        "features": [
            "All IoT Advanced features",
            "All QualityFix features",
            "All SafetyFix features",
            "White-label customization",
            "Priority support",
            "Custom integrations",
            "Dedicated success manager",
            "Unlimited API calls",
            "Multi-site management"
        ],
        "upgrade_url": "https://chatterfix.com/upgrade/enterprise"
    }
}


class PremiumLicense:
    """Customer premium license information"""

    def __init__(self, customer_id: str, license_data: Dict):
        self.customer_id = customer_id
        self.tier = license_data.get("tier", LicenseTier.CORE)
        self.enabled_modules: List[str] = license_data.get("enabled_modules", [])
        self.features = license_data.get("features", [])
        self.sensor_limit = license_data.get("sensor_limit", 0)
        self.api_limit = license_data.get("api_calls_per_month", 1000)
        self.expires_at = license_data.get("expires_at")
        self.is_trial = license_data.get("is_trial", False)
        self.trial_days_remaining = license_data.get("trial_days_remaining", 0)
        self.organization_id = license_data.get("organization_id")

    def has_module_access(self, module: PremiumModule) -> bool:
        """Check if customer has access to a specific premium module"""
        # Enterprise tier has access to everything
        if self.tier == LicenseTier.ENTERPRISE:
            return True

        # Check if module is in enabled modules list
        if module.value in self.enabled_modules:
            return True

        # Check tier-based access
        if module == PremiumModule.IOT_ADVANCED and self.tier == LicenseTier.IOT_ADVANCED:
            return True
        if module == PremiumModule.QUALITY_FIX and self.tier == LicenseTier.QUALITY_FIX:
            return True
        if module == PremiumModule.SAFETY_FIX and self.tier == LicenseTier.SAFETY_FIX:
            return True

        return False

    @property
    def has_iot_access(self) -> bool:
        return self.has_module_access(PremiumModule.IOT_ADVANCED)

    @property
    def has_quality_access(self) -> bool:
        return self.has_module_access(PremiumModule.QUALITY_FIX)

    @property
    def has_safety_access(self) -> bool:
        return self.has_module_access(PremiumModule.SAFETY_FIX)

    @property
    def has_enterprise_access(self) -> bool:
        return self.tier == LicenseTier.ENTERPRISE

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            return datetime.now() > datetime.fromisoformat(self.expires_at)
        except (ValueError, TypeError):
            return False

    def get_enabled_modules_list(self) -> List[str]:
        """Get list of all enabled premium modules"""
        modules = []
        if self.has_iot_access:
            modules.append("IoT Advanced")
        if self.has_quality_access:
            modules.append("QualityFix")
        if self.has_safety_access:
            modules.append("SafetyFix")
        return modules


class PremiumLicensingManager:
    """Manages all premium module licenses"""

    def __init__(self):
        self.license_cache: Dict[str, PremiumLicense] = {}
        self._firestore_service = None
        self._init_firestore_service()
        self.cache_ttl = timedelta(minutes=15)
        self.last_cache_update: Dict[str, datetime] = {}

    def _init_firestore_service(self):
        """Initialize Firestore licensing service if available"""
        try:
            from app.services.firestore_licensing_service import firestore_license_service
            self._firestore_service = firestore_license_service
            logger.info("Premium licensing using Firestore backend")
        except ImportError:
            logger.info("Premium licensing using local/demo mode")

    async def get_customer_license(self, customer_id: str) -> PremiumLicense:
        """Get customer license with caching - uses Firestore when available"""

        # Check cache first
        if (customer_id in self.license_cache and
            customer_id in self.last_cache_update and
            datetime.now() - self.last_cache_update[customer_id] < self.cache_ttl):
            return self.license_cache[customer_id]

        # Try Firestore service first if available
        if self._firestore_service:
            try:
                license_data = await self._firestore_service.get_license(customer_id)
                license_obj = PremiumLicense(customer_id, license_data)

                # Update cache
                self.license_cache[customer_id] = license_obj
                self.last_cache_update[customer_id] = datetime.now()

                return license_obj
            except Exception as e:
                logger.warning(f"Firestore license fetch failed, using fallback: {e}")

        # Fetch from license server or use development mode
        try:
            license_data = await self._fetch_license_from_server(customer_id)
            license_obj = PremiumLicense(customer_id, license_data)

            # Update cache
            self.license_cache[customer_id] = license_obj
            self.last_cache_update[customer_id] = datetime.now()

            return license_obj

        except Exception as e:
            logger.error(f"Failed to fetch license for customer {customer_id}: {e}")

            # Return cached license if available
            if customer_id in self.license_cache:
                logger.warning(f"Using cached license for customer {customer_id}")
                return self.license_cache[customer_id]

            # Fallback to demo/development license with full access
            logger.info(f"Using demo license with full access for {customer_id}")
            return PremiumLicense(customer_id, {
                "tier": LicenseTier.ENTERPRISE,
                "enabled_modules": [
                    PremiumModule.IOT_ADVANCED.value,
                    PremiumModule.QUALITY_FIX.value,
                    PremiumModule.SAFETY_FIX.value
                ],
                "is_demo": True,
                "is_trial": True
            })

    async def _fetch_license_from_server(self, customer_id: str) -> Dict:
        """Fetch license data from remote license server"""

        if not LICENSE_API_KEY:
            # Development mode - return all modules enabled for testing
            logger.warning("No license API key - returning development license with all modules")
            return {
                "tier": LicenseTier.ENTERPRISE,
                "enabled_modules": [
                    PremiumModule.IOT_ADVANCED.value,
                    PremiumModule.QUALITY_FIX.value,
                    PremiumModule.SAFETY_FIX.value
                ],
                "features": ["voice", "vision", "iot", "quality", "safety", "analytics", "alerts"],
                "sensor_limit": 100,
                "api_calls_per_month": 50000,
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "is_trial": True,
                "trial_days_remaining": 30
            }

        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available - returning development license")
            return {"tier": LicenseTier.CORE}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LICENSE_SERVER}/api/v1/licenses/{customer_id}",
                headers={"Authorization": f"Bearer {LICENSE_API_KEY}"},
                timeout=5.0
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"tier": LicenseTier.CORE}
            else:
                response.raise_for_status()
                return {"tier": LicenseTier.CORE}

    async def check_module_access(self, customer_id: str, module: PremiumModule) -> bool:
        """Check if customer has access to a specific premium module"""
        license_obj = await self.get_customer_license(customer_id)

        if license_obj.is_expired:
            logger.warning(f"License expired for customer {customer_id}")
            return False

        return license_obj.has_module_access(module)

    async def get_upgrade_options(self, customer_id: str) -> Dict:
        """Get upgrade options for customer based on current license"""
        license_obj = await self.get_customer_license(customer_id)

        upgrade_options = []

        # Add options for modules not yet enabled
        if not license_obj.has_iot_access:
            upgrade_options.append({
                "module": PremiumModule.IOT_ADVANCED.value,
                **PREMIUM_MODULE_PRICING[PremiumModule.IOT_ADVANCED]
            })

        if not license_obj.has_quality_access:
            upgrade_options.append({
                "module": PremiumModule.QUALITY_FIX.value,
                **PREMIUM_MODULE_PRICING[PremiumModule.QUALITY_FIX]
            })

        if not license_obj.has_safety_access:
            upgrade_options.append({
                "module": PremiumModule.SAFETY_FIX.value,
                **PREMIUM_MODULE_PRICING[PremiumModule.SAFETY_FIX]
            })

        # Always show enterprise option if not already enterprise
        if not license_obj.has_enterprise_access:
            upgrade_options.append({
                "module": PremiumModule.ENTERPRISE.value,
                **PREMIUM_MODULE_PRICING[PremiumModule.ENTERPRISE]
            })

        return {
            "customer_id": customer_id,
            "current_tier": license_obj.tier,
            "enabled_modules": license_obj.get_enabled_modules_list(),
            "is_trial": license_obj.is_trial,
            "trial_days_remaining": license_obj.trial_days_remaining,
            "upgrade_options": upgrade_options,
            "contact_sales": "sales@chatterfix.com"
        }

    async def get_license_status(self, customer_id: str) -> Dict:
        """Get comprehensive license status for customer"""
        license_obj = await self.get_customer_license(customer_id)
        upgrade_info = await self.get_upgrade_options(customer_id)

        return {
            "customer_id": customer_id,
            "tier": license_obj.tier,
            "modules_enabled": {
                "iot_advanced": license_obj.has_iot_access,
                "quality_fix": license_obj.has_quality_access,
                "safety_fix": license_obj.has_safety_access,
                "enterprise": license_obj.has_enterprise_access
            },
            "features_enabled": {
                "voice_commands": True,
                "computer_vision": True,
                "manual_entry": True,
                "iot_sensors": license_obj.has_iot_access,
                "predictive_analytics": license_obj.has_iot_access,
                "quality_management": license_obj.has_quality_access,
                "haccp_compliance": license_obj.has_quality_access,
                "safety_management": license_obj.has_safety_access,
                "incident_tracking": license_obj.has_safety_access,
                "enterprise_features": license_obj.has_enterprise_access
            },
            "limits": {
                "sensors": license_obj.sensor_limit,
                "api_calls_per_month": license_obj.api_limit
            },
            "trial_info": {
                "is_trial": license_obj.is_trial,
                "days_remaining": license_obj.trial_days_remaining
            },
            "expires_at": license_obj.expires_at,
            "upgrade_options": upgrade_info["upgrade_options"]
        }


# Global licensing manager instance
premium_licensing_manager = PremiumLicensingManager()


def get_current_customer_id() -> str:
    """Get customer ID from current request context"""
    # TODO: Implement proper customer ID extraction from session/JWT
    # For now, return a demo customer ID
    return "demo_customer_1"


def get_customer_id_from_user(user: Any) -> str:
    """Extract customer/organization ID from user object"""
    if user is None:
        return "demo_customer_1"

    # Try to get organization_id first (multi-tenant)
    if hasattr(user, 'organization_id') and user.organization_id:
        return user.organization_id

    # Fall back to customer_id
    if hasattr(user, 'customer_id') and user.customer_id:
        return user.customer_id

    # Fall back to user id
    if hasattr(user, 'id') and user.id:
        return user.id

    return "demo_customer_1"


# ============== LICENSING DECORATORS ==============

def require_iot_license(func):
    """Decorator to protect IoT Advanced features"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        customer_id = get_current_customer_id()

        if not await premium_licensing_manager.check_module_access(customer_id, PremiumModule.IOT_ADVANCED):
            upgrade_info = await premium_licensing_manager.get_upgrade_options(customer_id)
            return {
                "error": "IoT Advanced Module Required",
                "message": "This feature requires ChatterFix IoT Advanced Module",
                "module": "iot_advanced",
                "price": "$199/month + $25/sensor",
                "upgrade_url": "https://chatterfix.com/upgrade/iot-advanced",
                "upgrade_options": upgrade_info["upgrade_options"]
            }

        return await func(*args, **kwargs)
    return wrapper


def require_quality_license(func):
    """Decorator to protect QualityFix features"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        customer_id = get_current_customer_id()

        if not await premium_licensing_manager.check_module_access(customer_id, PremiumModule.QUALITY_FIX):
            upgrade_info = await premium_licensing_manager.get_upgrade_options(customer_id)
            return {
                "error": "QualityFix Module Required",
                "message": "This feature requires ChatterFix QualityFix Module for HACCP, ISO, and food safety compliance",
                "module": "quality_fix",
                "price": "$99/month",
                "upgrade_url": "https://chatterfix.com/upgrade/quality-fix",
                "upgrade_options": upgrade_info["upgrade_options"]
            }

        return await func(*args, **kwargs)
    return wrapper


def require_safety_license(func):
    """Decorator to protect SafetyFix features"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        customer_id = get_current_customer_id()

        if not await premium_licensing_manager.check_module_access(customer_id, PremiumModule.SAFETY_FIX):
            upgrade_info = await premium_licensing_manager.get_upgrade_options(customer_id)
            return {
                "error": "SafetyFix Module Required",
                "message": "This feature requires ChatterFix SafetyFix Module for OSHA compliance and safety management",
                "module": "safety_fix",
                "price": "$99/month",
                "upgrade_url": "https://chatterfix.com/upgrade/safety-fix",
                "upgrade_options": upgrade_info["upgrade_options"]
            }

        return await func(*args, **kwargs)
    return wrapper


def require_enterprise_license(func):
    """Decorator to protect Enterprise features"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        customer_id = get_current_customer_id()

        if not await premium_licensing_manager.check_module_access(customer_id, PremiumModule.ENTERPRISE):
            upgrade_info = await premium_licensing_manager.get_upgrade_options(customer_id)
            return {
                "error": "Enterprise License Required",
                "message": "This feature requires ChatterFix Enterprise License",
                "module": "enterprise",
                "price": "$299/technician/month",
                "upgrade_url": "https://chatterfix.com/upgrade/enterprise",
                "upgrade_options": upgrade_info["upgrade_options"]
            }

        return await func(*args, **kwargs)
    return wrapper


def require_any_premium_license(func):
    """Decorator that allows access if user has ANY premium module"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        customer_id = get_current_customer_id()
        license_obj = await premium_licensing_manager.get_customer_license(customer_id)

        if not (license_obj.has_iot_access or license_obj.has_quality_access or
                license_obj.has_safety_access or license_obj.has_enterprise_access):
            upgrade_info = await premium_licensing_manager.get_upgrade_options(customer_id)
            return {
                "error": "Premium Module Required",
                "message": "This feature requires a ChatterFix Premium Module",
                "available_modules": [
                    {"name": "IoT Advanced", "price": "$199/month"},
                    {"name": "QualityFix", "price": "$99/month"},
                    {"name": "SafetyFix", "price": "$99/month"},
                    {"name": "Enterprise Bundle", "price": "$299/technician/month"}
                ],
                "upgrade_options": upgrade_info["upgrade_options"]
            }

        return await func(*args, **kwargs)
    return wrapper


# ============== ASYNC LICENSE CHECK FUNCTIONS ==============

async def check_iot_access(customer_id: str) -> bool:
    """Check if customer has IoT Advanced access"""
    return await premium_licensing_manager.check_module_access(customer_id, PremiumModule.IOT_ADVANCED)


async def check_quality_access(customer_id: str) -> bool:
    """Check if customer has QualityFix access"""
    return await premium_licensing_manager.check_module_access(customer_id, PremiumModule.QUALITY_FIX)


async def check_safety_access(customer_id: str) -> bool:
    """Check if customer has SafetyFix access"""
    return await premium_licensing_manager.check_module_access(customer_id, PremiumModule.SAFETY_FIX)


async def check_enterprise_access(customer_id: str) -> bool:
    """Check if customer has Enterprise access"""
    return await premium_licensing_manager.check_module_access(customer_id, PremiumModule.ENTERPRISE)


async def get_license_status(customer_id: str) -> Dict:
    """Get comprehensive license status"""
    return await premium_licensing_manager.get_license_status(customer_id)


async def get_upgrade_options(customer_id: str) -> Dict:
    """Get available upgrade options"""
    return await premium_licensing_manager.get_upgrade_options(customer_id)


# ============== MODULE INFO HELPERS ==============

def get_module_info(module: PremiumModule) -> Dict:
    """Get information about a specific premium module"""
    return PREMIUM_MODULE_PRICING.get(module, {})


def get_all_premium_modules() -> Dict:
    """Get information about all premium modules"""
    return {
        module.value: {
            "module_id": module.value,
            **info
        }
        for module, info in PREMIUM_MODULE_PRICING.items()
    }


logger.info("Premium Licensing System initialized - IoT Advanced, QualityFix, SafetyFix modules available")
