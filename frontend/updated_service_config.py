"""
Updated ChatterFix Service Configuration for Consolidated CMMS
This replaces the old individual service URLs with the new consolidated service
"""

import os

# NEW CONSOLIDATED SERVICE CONFIGURATION
CONSOLIDATED_CMMS_URL = "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app"

# Updated service configuration for post-consolidation
UPDATED_SERVICE_URLS = {
    # CONSOLIDATED SERVICES (New unified endpoints)
    "work_orders": f"{CONSOLIDATED_CMMS_URL}/work_orders",
    "assets": f"{CONSOLIDATED_CMMS_URL}/assets", 
    "parts": f"{CONSOLIDATED_CMMS_URL}/parts",
    "cmms_health": f"{CONSOLIDATED_CMMS_URL}/health",
    
    # REMAINING SEPARATE SERVICES (Still running individually)
    "gateway": os.getenv("GATEWAY_URL", "https://chatterfix-unified-gateway-east-psycl7nhha-ue.a.run.app"),
    "voice_ai": os.getenv("VOICE_AI_URL", "https://chatterfix-voice-ai-650169261019.us-central1.run.app"),
    
    # DEPRECATED SERVICES (Now handled by consolidated CMMS)
    # These are kept for reference but point to the consolidated service
    "customer_success": f"{CONSOLIDATED_CMMS_URL}/work_orders",  # Redirect to work orders
    "revenue_intelligence": f"{CONSOLIDATED_CMMS_URL}/assets",   # Redirect to assets  
    "data_room": f"{CONSOLIDATED_CMMS_URL}/parts",              # Redirect to parts
    "fix_it_fred": os.getenv("FIX_IT_FRED_URL", "https://chatterfix-fix-it-fred-650169261019.us-central1.run.app"),
}

# Environment variable overrides (for production deployment)
def get_service_url(service_name: str) -> str:
    """Get service URL with environment variable override support"""
    env_var = f"{service_name.upper()}_URL"
    return os.getenv(env_var, UPDATED_SERVICE_URLS.get(service_name, ""))

# Helper function to update existing code
def migrate_old_urls():
    """Helper to migrate from old URL structure to new consolidated structure"""
    migration_map = {
        "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app/work_orders": f"{CONSOLIDATED_CMMS_URL}/work_orders",
        "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app/assets": f"{CONSOLIDATED_CMMS_URL}/assets",
        "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app/parts": f"{CONSOLIDATED_CMMS_URL}/parts",
        "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app/work_orders": f"{CONSOLIDATED_CMMS_URL}/work_orders",
        "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app/assets": f"{CONSOLIDATED_CMMS_URL}/assets",
        "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app/parts": f"{CONSOLIDATED_CMMS_URL}/parts",
    }
    return migration_map

print("✅ ChatterFix Service Configuration Updated for Consolidated CMMS")
print(f"🌐 Consolidated Service: {CONSOLIDATED_CMMS_URL}")
print("📋 Updated Endpoints:")
for service, url in UPDATED_SERVICE_URLS.items():
    print(f"  - {service}: {url}")