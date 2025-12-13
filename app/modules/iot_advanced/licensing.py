"""
ChatterFix IoT Advanced Module - Licensing System
Controls access to premium IoT features based on customer subscription
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx
from functools import wraps

import logging
logger = logging.getLogger(__name__)

# License server configuration
LICENSE_SERVER = os.getenv("CHATTERFIX_LICENSE_SERVER", "https://licensing.chatterfix.com")
LICENSE_API_KEY = os.getenv("CHATTERFIX_LICENSE_API_KEY")

class LicenseLevel:
    """License tier definitions"""
    CORE = "core"
    IOT_ADVANCED = "iot_advanced" 
    ENTERPRISE = "enterprise"

class ChatterFixLicense:
    """Customer license information and validation"""
    
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
        """Check if customer has IoT Advanced module access"""
        return self.tier in [LicenseLevel.IOT_ADVANCED, LicenseLevel.ENTERPRISE]
    
    @property
    def has_enterprise_access(self) -> bool:
        """Check if customer has Enterprise features"""
        return self.tier == LicenseLevel.ENTERPRISE
    
    @property 
    def is_expired(self) -> bool:
        """Check if license is expired"""
        if not self.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)

class LicensingManager:
    """Manages customer licenses and feature access"""
    
    def __init__(self):
        self.license_cache = {}
        self.cache_ttl = timedelta(minutes=15)  # Cache licenses for 15 minutes
        self.last_cache_update = {}
    
    async def get_customer_license(self, customer_id: str) -> ChatterFixLicense:
        """Get customer license with caching"""
        
        # Check cache first
        if (customer_id in self.license_cache and 
            customer_id in self.last_cache_update and
            datetime.now() - self.last_cache_update[customer_id] < self.cache_ttl):
            return self.license_cache[customer_id]
        
        # Fetch from license server
        try:
            license_data = await self._fetch_license_from_server(customer_id)
            license = ChatterFixLicense(customer_id, license_data)
            
            # Update cache
            self.license_cache[customer_id] = license
            self.last_cache_update[customer_id] = datetime.now()
            
            return license
            
        except Exception as e:
            logger.error(f"Failed to fetch license for customer {customer_id}: {e}")
            
            # Return cached license if available
            if customer_id in self.license_cache:
                logger.warning(f"Using cached license for customer {customer_id}")
                return self.license_cache[customer_id]
            
            # Fallback to core license
            logger.warning(f"Falling back to core license for customer {customer_id}")
            return ChatterFixLicense(customer_id, {"tier": LicenseLevel.CORE})
    
    async def _fetch_license_from_server(self, customer_id: str) -> Dict:
        """Fetch license data from remote license server"""
        
        if not LICENSE_API_KEY:
            # Development mode - return IoT Advanced for testing
            logger.warning("No license API key - returning development license")
            return {
                "tier": LicenseLevel.IOT_ADVANCED,
                "features": ["voice", "vision", "iot", "analytics", "alerts"],
                "sensor_limit": 100,
                "api_calls_per_month": 50000,
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "is_trial": True,
                "trial_days_remaining": 30
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LICENSE_SERVER}/api/v1/licenses/{customer_id}",
                headers={"Authorization": f"Bearer {LICENSE_API_KEY}"},
                timeout=5.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Customer not found - return core license
                return {"tier": LicenseLevel.CORE}
            else:
                response.raise_for_status()
    
    async def check_feature_access(self, customer_id: str, feature: str) -> bool:
        """Check if customer has access to specific feature"""
        license = await self.get_customer_license(customer_id)
        
        if license.is_expired:
            logger.warning(f"License expired for customer {customer_id}")
            return False
        
        # Feature access mapping
        feature_mapping = {
            "iot_sensors": license.has_iot_access,
            "iot_analytics": license.has_iot_access,
            "iot_alerts": license.has_iot_access,
            "predictive_maintenance": license.has_iot_access,
            "enterprise_api": license.has_enterprise_access,
            "white_label": license.has_enterprise_access,
            "priority_support": license.has_enterprise_access
        }
        
        return feature_mapping.get(feature, True)  # Default to True for core features
    
    async def check_sensor_limit(self, customer_id: str, current_sensors: int) -> bool:
        """Check if customer is within sensor limits"""
        license = await self.get_customer_license(customer_id)
        
        if license.sensor_limit == 0:  # Core license - no sensors allowed
            return current_sensors == 0
        elif license.sensor_limit == -1:  # Unlimited sensors
            return True
        else:
            return current_sensors <= license.sensor_limit
    
    async def get_upgrade_info(self, customer_id: str) -> Dict:
        """Get upgrade information for customer"""
        license = await self.get_customer_license(customer_id)
        
        upgrade_options = []
        
        if license.tier == LicenseLevel.CORE:
            upgrade_options.append({
                "tier": "IoT Advanced",
                "price": "$199/month + $25/sensor",
                "features": ["Real-time monitoring", "Predictive analytics", "Advanced alerts"],
                "upgrade_url": "https://chatterfix.com/upgrade/iot-advanced"
            })
            upgrade_options.append({
                "tier": "Enterprise", 
                "price": "$299/technician/month",
                "features": ["Everything + White label", "Priority support", "Custom integrations"],
                "upgrade_url": "https://chatterfix.com/upgrade/enterprise"
            })
        elif license.tier == LicenseLevel.IOT_ADVANCED:
            upgrade_options.append({
                "tier": "Enterprise",
                "price": "$299/technician/month", 
                "features": ["White label", "Priority support", "Custom integrations"],
                "upgrade_url": "https://chatterfix.com/upgrade/enterprise"
            })
        
        return {
            "current_tier": license.tier,
            "is_trial": license.is_trial,
            "trial_days_remaining": license.trial_days_remaining,
            "upgrade_options": upgrade_options,
            "contact_sales": "sales@chatterfix.com"
        }

# Global licensing manager instance
licensing_manager = LicensingManager()

def require_iot_license(func):
    """Decorator to protect IoT Advanced features"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract customer_id from request context or kwargs
        customer_id = get_current_customer_id()
        
        if not await licensing_manager.check_feature_access(customer_id, "iot_sensors"):
            return {
                "error": "IoT Advanced Module Required",
                "message": "This feature requires ChatterFix IoT Advanced Module",
                "current_tier": "core",
                "upgrade_info": await licensing_manager.get_upgrade_info(customer_id)
            }
        
        return await func(*args, **kwargs)
    return wrapper

def require_enterprise_license(func):
    """Decorator to protect Enterprise features"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        customer_id = get_current_customer_id()
        
        if not await licensing_manager.check_feature_access(customer_id, "enterprise_api"):
            return {
                "error": "Enterprise License Required",
                "message": "This feature requires ChatterFix Enterprise License",
                "upgrade_info": await licensing_manager.get_upgrade_info(customer_id)
            }
        
        return await func(*args, **kwargs)
    return wrapper

async def check_iot_access(customer_id: str) -> bool:
    """Simple function to check IoT access"""
    return await licensing_manager.check_feature_access(customer_id, "iot_sensors")

def get_current_customer_id() -> str:
    """Get customer ID from current request context"""
    # TODO: Implement proper customer ID extraction from session/JWT
    # For now, return a demo customer ID
    return "demo_customer_1"

async def validate_sensor_count(customer_id: str, sensor_count: int) -> Dict:
    """Validate if customer can add more sensors"""
    license = await licensing_manager.get_customer_license(customer_id)
    
    if license.sensor_limit == 0:  # Core license
        return {
            "valid": False,
            "message": "Sensor monitoring requires IoT Advanced Module",
            "upgrade_required": True
        }
    elif license.sensor_limit == -1:  # Unlimited
        return {
            "valid": True,
            "message": "Unlimited sensors available"
        }
    elif sensor_count <= license.sensor_limit:
        return {
            "valid": True, 
            "message": f"Sensors: {sensor_count}/{license.sensor_limit}",
            "remaining": license.sensor_limit - sensor_count
        }
    else:
        return {
            "valid": False,
            "message": f"Sensor limit exceeded: {sensor_count}/{license.sensor_limit}",
            "upgrade_required": True
        }

async def get_license_status(customer_id: str) -> Dict:
    """Get comprehensive license status for customer"""
    license = await licensing_manager.get_customer_license(customer_id)
    upgrade_info = await licensing_manager.get_upgrade_info(customer_id)
    
    return {
        "customer_id": customer_id,
        "tier": license.tier,
        "features_enabled": {
            "voice_commands": True,
            "computer_vision": True, 
            "manual_entry": True,
            "iot_sensors": license.has_iot_access,
            "predictive_analytics": license.has_iot_access,
            "advanced_alerts": license.has_iot_access,
            "enterprise_features": license.has_enterprise_access
        },
        "limits": {
            "sensors": license.sensor_limit,
            "api_calls_per_month": license.api_limit
        },
        "trial_info": {
            "is_trial": license.is_trial,
            "days_remaining": license.trial_days_remaining
        },
        "expires_at": license.expires_at,
        "upgrade_options": upgrade_info["upgrade_options"]
    }