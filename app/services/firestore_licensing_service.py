"""
ChatterFix Firestore Licensing Service
Firebase-based licensing system with Firestore storage and Firebase Authentication

This service manages premium module licenses stored in Firestore:
- IoT Advanced: $199/month + $25/sensor
- QualityFix: $99/month
- SafetyFix: $99/month
- Enterprise Bundle: $299/technician/month

License data is stored per organization and validated against Firebase Auth.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import Firestore
try:
    from app.core.firestore_db import firestore_db

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logger.warning("Firestore not available for licensing")


class LicenseModule(str, Enum):
    """Available premium modules"""

    IOT_ADVANCED = "iot_advanced"
    QUALITY_FIX = "quality_fix"
    SAFETY_FIX = "safety_fix"
    ENTERPRISE = "enterprise"


class LicenseTier(str, Enum):
    """License tier levels"""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Pricing configuration
MODULE_PRICING = {
    LicenseModule.IOT_ADVANCED: {
        "name": "IoT Advanced",
        "base_price": 199,
        "per_sensor_price": 25,
        "billing_cycle": "monthly",
    },
    LicenseModule.QUALITY_FIX: {
        "name": "QualityFix",
        "base_price": 99,
        "billing_cycle": "monthly",
    },
    LicenseModule.SAFETY_FIX: {
        "name": "SafetyFix",
        "base_price": 99,
        "billing_cycle": "monthly",
    },
    LicenseModule.ENTERPRISE: {
        "name": "Enterprise Bundle",
        "per_technician_price": 299,
        "includes_all_modules": True,
        "billing_cycle": "monthly",
    },
}


class FirestoreLicenseService:
    """
    Firestore-based licensing service for ChatterFix premium modules.

    License documents are stored in Firestore under:
    - organizations/{org_id}/license (organization license)
    - customer_licenses/{customer_id} (legacy/individual licenses)

    Demo/Public Access:
    - When no license exists, demo mode is enabled with full access
    - Demo data is always available for unauthenticated users
    """

    COLLECTION_ORG_LICENSES = "organizations"
    COLLECTION_CUSTOMER_LICENSES = "customer_licenses"
    DEMO_LICENSE_CACHE_TTL = timedelta(minutes=5)

    def __init__(self):
        self.db = None
        self._license_cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        if FIRESTORE_AVAILABLE:
            try:
                self.db = firestore_db.get_client()
                if self.db:
                    logger.info("FirestoreLicenseService initialized with Firestore")
                else:
                    logger.warning("Firestore client not available - using demo mode")
            except Exception as e:
                logger.warning(f"Could not initialize Firestore for licensing: {e}")

    def _get_demo_license(self, customer_id: str = "demo") -> Dict[str, Any]:
        """
        Return a demo license with full access to all modules.
        This ensures the demo is always available for everyone.
        """
        return {
            "customer_id": customer_id,
            "organization_id": customer_id,
            "tier": LicenseTier.ENTERPRISE.value,
            "enabled_modules": [
                LicenseModule.IOT_ADVANCED.value,
                LicenseModule.QUALITY_FIX.value,
                LicenseModule.SAFETY_FIX.value,
            ],
            "is_demo": True,
            "is_trial": True,
            "trial_days_remaining": 14,
            "trial_started_at": datetime.now().isoformat(),
            "trial_expires_at": (datetime.now() + timedelta(days=14)).isoformat(),
            "features": {
                "iot_sensors": True,
                "iot_analytics": True,
                "iot_alerts": True,
                "quality_haccp": True,
                "quality_iso": True,
                "quality_audits": True,
                "safety_incidents": True,
                "safety_osha": True,
                "safety_lab_results": True,
                "voice_commands": True,
                "computer_vision": True,
                "ai_assistant": True,
            },
            "limits": {
                "sensors": 100,
                "technicians": 50,
                "assets": 500,
                "work_orders_per_month": 10000,
                "api_calls_per_month": 100000,
            },
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "mode": "demo",
        }

    async def get_license(self, customer_id: str) -> Dict[str, Any]:
        """
        Get license for a customer/organization.
        Returns demo license if no Firestore license exists.
        """
        # Check cache first
        if customer_id in self._license_cache:
            cache_time = self._cache_timestamps.get(customer_id)
            if cache_time and datetime.now() - cache_time < self.DEMO_LICENSE_CACHE_TTL:
                return self._license_cache[customer_id]

        # Try to get from Firestore
        if self.db:
            try:
                # Check organization license first
                org_ref = self.db.collection(self.COLLECTION_ORG_LICENSES).document(
                    customer_id
                )
                org_doc = org_ref.get()

                if org_doc.exists:
                    org_data = org_doc.to_dict()
                    # Check for license sub-document
                    license_ref = org_ref.collection("license").document("current")
                    license_doc = license_ref.get()

                    if license_doc.exists:
                        license_data = license_doc.to_dict()
                        license_data["organization_id"] = customer_id
                        license_data["customer_id"] = customer_id

                        # Cache it
                        self._license_cache[customer_id] = license_data
                        self._cache_timestamps[customer_id] = datetime.now()

                        return license_data

                # Try legacy customer_licenses collection
                legacy_ref = self.db.collection(
                    self.COLLECTION_CUSTOMER_LICENSES
                ).document(customer_id)
                legacy_doc = legacy_ref.get()

                if legacy_doc.exists:
                    license_data = legacy_doc.to_dict()
                    license_data["customer_id"] = customer_id

                    self._license_cache[customer_id] = license_data
                    self._cache_timestamps[customer_id] = datetime.now()

                    return license_data

            except Exception as e:
                logger.error(f"Error fetching license from Firestore: {e}")

        # No license found - return demo license
        demo_license = self._get_demo_license(customer_id)
        self._license_cache[customer_id] = demo_license
        self._cache_timestamps[customer_id] = datetime.now()

        return demo_license

    async def check_module_access(
        self, customer_id: str, module: LicenseModule
    ) -> bool:
        """Check if customer has access to a specific module"""
        license_data = await self.get_license(customer_id)

        # Demo licenses have full access
        if license_data.get("is_demo") or license_data.get("mode") == "demo":
            return True

        # Check if trial is expired
        trial_expires = license_data.get("trial_expires_at")
        if trial_expires:
            try:
                expires_dt = datetime.fromisoformat(
                    trial_expires.replace("Z", "+00:00")
                )
                if (
                    datetime.now(expires_dt.tzinfo if expires_dt.tzinfo else None)
                    > expires_dt
                ):
                    # Trial expired - check for paid license
                    if license_data.get("status") != "active":
                        return False
            except (ValueError, TypeError):
                pass

        # Enterprise tier has access to everything
        if license_data.get("tier") == LicenseTier.ENTERPRISE.value:
            return True

        # Check enabled modules
        enabled_modules = license_data.get("enabled_modules", [])
        return module.value in enabled_modules

    async def create_license(
        self,
        organization_id: str,
        tier: LicenseTier = LicenseTier.FREE,
        enabled_modules: List[LicenseModule] = None,
        is_trial: bool = True,
        trial_days: int = 14,
    ) -> Dict[str, Any]:
        """Create a new license for an organization"""

        if enabled_modules is None:
            enabled_modules = []

        license_data = {
            "organization_id": organization_id,
            "tier": tier.value,
            "enabled_modules": [m.value for m in enabled_modules],
            "is_trial": is_trial,
            "trial_days_remaining": trial_days if is_trial else 0,
            "trial_started_at": datetime.now().isoformat() if is_trial else None,
            "trial_expires_at": (
                (datetime.now() + timedelta(days=trial_days)).isoformat()
                if is_trial
                else None
            ),
            "features": self._get_features_for_tier(tier, enabled_modules),
            "limits": self._get_limits_for_tier(tier),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
        }

        if self.db:
            try:
                # Store under organization
                org_ref = self.db.collection(self.COLLECTION_ORG_LICENSES).document(
                    organization_id
                )
                license_ref = org_ref.collection("license").document("current")
                license_ref.set(license_data)

                logger.info(
                    f"Created license for organization {organization_id}: {tier.value}"
                )

            except Exception as e:
                logger.error(f"Error creating license in Firestore: {e}")

        # Update cache
        self._license_cache[organization_id] = license_data
        self._cache_timestamps[organization_id] = datetime.now()

        return license_data

    async def activate_module(
        self,
        organization_id: str,
        module: LicenseModule,
        payment_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """Activate a premium module for an organization"""

        license_data = await self.get_license(organization_id)

        # Add module to enabled list
        enabled_modules = license_data.get("enabled_modules", [])
        if module.value not in enabled_modules:
            enabled_modules.append(module.value)

        # Update features
        features = license_data.get("features", {})
        features.update(self._get_module_features(module))

        # Update license
        license_data["enabled_modules"] = enabled_modules
        license_data["features"] = features
        license_data["updated_at"] = datetime.now().isoformat()

        if payment_confirmed:
            license_data["is_trial"] = False
            license_data["trial_expires_at"] = None

        if self.db:
            try:
                org_ref = self.db.collection(self.COLLECTION_ORG_LICENSES).document(
                    organization_id
                )
                license_ref = org_ref.collection("license").document("current")
                license_ref.update(license_data)

                logger.info(
                    f"Activated module {module.value} for organization {organization_id}"
                )

            except Exception as e:
                logger.error(f"Error activating module in Firestore: {e}")

        # Update cache
        self._license_cache[organization_id] = license_data
        self._cache_timestamps[organization_id] = datetime.now()

        return license_data

    async def start_trial(
        self,
        organization_id: str,
        modules: List[LicenseModule] = None,
        trial_days: int = 14,
    ) -> Dict[str, Any]:
        """Start a trial with specified modules (or all modules)"""

        if modules is None:
            # Trial includes all modules
            modules = [
                LicenseModule.IOT_ADVANCED,
                LicenseModule.QUALITY_FIX,
                LicenseModule.SAFETY_FIX,
            ]

        return await self.create_license(
            organization_id=organization_id,
            tier=LicenseTier.PROFESSIONAL,
            enabled_modules=modules,
            is_trial=True,
            trial_days=trial_days,
        )

    def _get_features_for_tier(
        self, tier: LicenseTier, modules: List[LicenseModule] = None
    ) -> Dict[str, bool]:
        """Get feature flags based on tier and enabled modules"""

        # Base features (always available)
        features = {
            "voice_commands": True,
            "computer_vision": True,
            "work_orders": True,
            "assets": True,
            "inventory": True,
            "basic_reports": True,
        }

        if modules:
            for module in modules:
                features.update(self._get_module_features(module))

        if tier == LicenseTier.ENTERPRISE:
            # Enterprise gets everything
            features.update(
                {
                    "iot_sensors": True,
                    "iot_analytics": True,
                    "iot_alerts": True,
                    "quality_haccp": True,
                    "quality_iso": True,
                    "quality_audits": True,
                    "safety_incidents": True,
                    "safety_osha": True,
                    "safety_lab_results": True,
                    "ai_assistant": True,
                    "white_label": True,
                    "api_access": True,
                    "priority_support": True,
                }
            )

        return features

    def _get_module_features(self, module: LicenseModule) -> Dict[str, bool]:
        """Get features for a specific module"""

        if module == LicenseModule.IOT_ADVANCED:
            return {
                "iot_sensors": True,
                "iot_analytics": True,
                "iot_alerts": True,
                "predictive_maintenance": True,
            }
        elif module == LicenseModule.QUALITY_FIX:
            return {
                "quality_haccp": True,
                "quality_iso": True,
                "quality_audits": True,
                "quality_traceability": True,
                "quality_capa": True,
            }
        elif module == LicenseModule.SAFETY_FIX:
            return {
                "safety_incidents": True,
                "safety_osha": True,
                "safety_lab_results": True,
                "safety_inspections": True,
                "safety_analytics": True,
            }
        elif module == LicenseModule.ENTERPRISE:
            return {
                "white_label": True,
                "api_access": True,
                "priority_support": True,
                "custom_integrations": True,
            }

        return {}

    def _get_limits_for_tier(self, tier: LicenseTier) -> Dict[str, int]:
        """Get usage limits based on tier"""

        limits = {
            LicenseTier.FREE: {
                "sensors": 5,
                "technicians": 5,
                "assets": 25,
                "work_orders_per_month": 100,
                "api_calls_per_month": 1000,
            },
            LicenseTier.STARTER: {
                "sensors": 25,
                "technicians": 15,
                "assets": 100,
                "work_orders_per_month": 500,
                "api_calls_per_month": 10000,
            },
            LicenseTier.PROFESSIONAL: {
                "sensors": 100,
                "technicians": 50,
                "assets": 500,
                "work_orders_per_month": 5000,
                "api_calls_per_month": 50000,
            },
            LicenseTier.ENTERPRISE: {
                "sensors": -1,  # Unlimited
                "technicians": -1,
                "assets": -1,
                "work_orders_per_month": -1,
                "api_calls_per_month": -1,
            },
        }

        return limits.get(tier, limits[LicenseTier.FREE])

    async def get_license_status(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive license status for display"""

        license_data = await self.get_license(customer_id)

        return {
            "customer_id": customer_id,
            "tier": license_data.get("tier", "free"),
            "is_demo": license_data.get("is_demo", False),
            "is_trial": license_data.get("is_trial", False),
            "trial_days_remaining": license_data.get("trial_days_remaining", 0),
            "modules": {
                "iot_advanced": LicenseModule.IOT_ADVANCED.value
                in license_data.get("enabled_modules", []),
                "quality_fix": LicenseModule.QUALITY_FIX.value
                in license_data.get("enabled_modules", []),
                "safety_fix": LicenseModule.SAFETY_FIX.value
                in license_data.get("enabled_modules", []),
            },
            "features": license_data.get("features", {}),
            "limits": license_data.get("limits", {}),
            "status": license_data.get("status", "active"),
            "expires_at": license_data.get("trial_expires_at"),
        }


# Global instance
firestore_license_service = FirestoreLicenseService()


# Convenience functions for use in routers
async def check_iot_access(customer_id: str) -> bool:
    """Check if customer has IoT Advanced access"""
    return await firestore_license_service.check_module_access(
        customer_id, LicenseModule.IOT_ADVANCED
    )


async def check_quality_access(customer_id: str) -> bool:
    """Check if customer has QualityFix access"""
    return await firestore_license_service.check_module_access(
        customer_id, LicenseModule.QUALITY_FIX
    )


async def check_safety_access(customer_id: str) -> bool:
    """Check if customer has SafetyFix access"""
    return await firestore_license_service.check_module_access(
        customer_id, LicenseModule.SAFETY_FIX
    )


async def get_license(customer_id: str) -> Dict[str, Any]:
    """Get customer license"""
    return await firestore_license_service.get_license(customer_id)


async def get_license_status(customer_id: str) -> Dict[str, Any]:
    """Get license status for display"""
    return await firestore_license_service.get_license_status(customer_id)


logger.info("Firestore Licensing Service loaded - Demo mode always available")
