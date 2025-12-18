"""
ChatterFix Premium Modules API Router
Unified endpoint for managing premium module licenses and upgrades

Premium Modules:
- IoT Advanced: $199/month + $25/sensor
- QualityFix: $99/month
- SafetyFix: $99/month
- Enterprise Bundle: $299/technician/month (includes all)
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Import premium licensing system
try:
    from app.modules.premium_licensing import (
        PremiumModule,
        get_license_status,
        get_upgrade_options,
        get_all_premium_modules,
        get_module_info,
        get_current_customer_id,
        check_iot_access,
        check_quality_access,
        check_safety_access,
        check_enterprise_access,
    )

    LICENSING_AVAILABLE = True
except ImportError:
    LICENSING_AVAILABLE = False
    logger.warning("Premium licensing module not available")

    def get_current_customer_id():
        return "demo_customer_1"


# Initialize router
router = APIRouter(prefix="/premium", tags=["Premium Modules"])

# Initialize templates
try:
    templates = Jinja2Templates(directory="app/templates")
except Exception:
    templates = None


# ===== PYDANTIC MODELS =====


class ModuleActivationRequest(BaseModel):
    """Request to activate a premium module"""

    module: str = Field(
        ..., description="Module ID: iot_advanced, quality_fix, safety_fix, enterprise"
    )
    payment_method_id: Optional[str] = None
    billing_cycle: str = Field(default="monthly", description="monthly or annual")


class ContactSalesRequest(BaseModel):
    """Request to contact sales for enterprise pricing"""

    name: str
    email: str
    company: str
    phone: Optional[str] = None
    message: Optional[str] = None
    modules_interested: List[str] = []


# ===== API ENDPOINTS =====


@router.get("/status")
async def get_premium_status():
    """Get comprehensive premium modules status for current customer"""
    customer_id = get_current_customer_id()

    if LICENSING_AVAILABLE:
        license_status = await get_license_status(customer_id)
        upgrade_options = await get_upgrade_options(customer_id)

        return JSONResponse(
            {
                "success": True,
                "customer_id": customer_id,
                "license_status": license_status,
                "available_upgrades": upgrade_options["upgrade_options"],
                "all_modules": get_all_premium_modules(),
            }
        )
    else:
        return JSONResponse(
            {
                "success": True,
                "mode": "demo",
                "message": "Running in demo mode - all premium features available",
                "customer_id": customer_id,
                "modules_enabled": {
                    "iot_advanced": True,
                    "quality_fix": True,
                    "safety_fix": True,
                },
            }
        )


@router.get("/modules")
async def list_premium_modules():
    """List all available premium modules with pricing and features"""
    modules = [
        {
            "id": "iot_advanced",
            "name": "IoT Advanced",
            "tagline": "Real-time sensor monitoring & predictive analytics",
            "price": "$199/month + $25/sensor",
            "price_details": {
                "base": 199,
                "per_sensor": 25,
                "currency": "USD",
                "billing": "monthly",
            },
            "features": [
                "Real-time sensor monitoring",
                "Predictive maintenance analytics",
                "Advanced alerting system",
                "Voice-integrated sensor queries",
                "Custom dashboard builder",
                "Historical trend analysis",
                "MQTT, Modbus, HTTP API support",
                "Unlimited sensors (with Enterprise)",
            ],
            "supported_protocols": [
                "Modbus TCP/RTU",
                "MQTT",
                "HTTP API",
                "OPC-UA",
                "Serial",
            ],
            "upgrade_url": "/premium/activate/iot_advanced",
            "learn_more_url": "https://chatterfix.com/modules/iot-advanced",
        },
        {
            "id": "quality_fix",
            "name": "QualityFix",
            "tagline": "HACCP, ISO, and food safety compliance",
            "price": "$99/month",
            "price_details": {"base": 99, "currency": "USD", "billing": "monthly"},
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
                "AI-powered quality insights",
            ],
            "certifications_supported": [
                "SQF",
                "FSMA",
                "ISO 22000",
                "FSSC 22000",
                "BRC",
                "IFS",
            ],
            "upgrade_url": "/premium/activate/quality_fix",
            "learn_more_url": "https://chatterfix.com/modules/quality-fix",
        },
        {
            "id": "safety_fix",
            "name": "SafetyFix",
            "tagline": "OSHA compliance & enterprise safety management",
            "price": "$99/month",
            "price_details": {"base": 99, "currency": "USD", "billing": "monthly"},
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
                "Cost-benefit safety analytics",
            ],
            "compliance_standards": ["OSHA", "EPA", "DOT", "ISO 45001", "NFPA"],
            "upgrade_url": "/premium/activate/safety_fix",
            "learn_more_url": "https://chatterfix.com/modules/safety-fix",
        },
        {
            "id": "enterprise",
            "name": "Enterprise Bundle",
            "tagline": "Complete platform with all premium modules",
            "price": "$299/technician/month",
            "price_details": {
                "per_technician": 299,
                "currency": "USD",
                "billing": "monthly",
                "includes": ["iot_advanced", "quality_fix", "safety_fix"],
            },
            "features": [
                "All IoT Advanced features",
                "All QualityFix features",
                "All SafetyFix features",
                "White-label customization",
                "Priority support",
                "Custom integrations",
                "Dedicated success manager",
                "Unlimited API calls",
                "Multi-site management",
                "Advanced reporting",
            ],
            "upgrade_url": "/premium/contact-sales",
            "learn_more_url": "https://chatterfix.com/enterprise",
        },
    ]

    # Add current access status if licensing is available
    if LICENSING_AVAILABLE:
        customer_id = get_current_customer_id()
        for module in modules:
            module_id = module["id"]
            if module_id == "iot_advanced":
                module["has_access"] = await check_iot_access(customer_id)
            elif module_id == "quality_fix":
                module["has_access"] = await check_quality_access(customer_id)
            elif module_id == "safety_fix":
                module["has_access"] = await check_safety_access(customer_id)
            elif module_id == "enterprise":
                module["has_access"] = await check_enterprise_access(customer_id)

    return JSONResponse(
        {
            "success": True,
            "modules": modules,
            "bundle_savings": "Save 25% with Enterprise Bundle vs. individual modules",
        }
    )


@router.get("/modules/{module_id}")
async def get_module_details(module_id: str):
    """Get detailed information about a specific premium module"""
    module_map = {
        "iot_advanced": PremiumModule.IOT_ADVANCED,
        "quality_fix": PremiumModule.QUALITY_FIX,
        "safety_fix": PremiumModule.SAFETY_FIX,
        "enterprise": PremiumModule.ENTERPRISE,
    }

    if module_id not in module_map:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")

    if LICENSING_AVAILABLE:
        module_info = get_module_info(module_map[module_id])
        customer_id = get_current_customer_id()

        # Check if customer has access
        has_access = False
        if module_id == "iot_advanced":
            has_access = await check_iot_access(customer_id)
        elif module_id == "quality_fix":
            has_access = await check_quality_access(customer_id)
        elif module_id == "safety_fix":
            has_access = await check_safety_access(customer_id)
        elif module_id == "enterprise":
            has_access = await check_enterprise_access(customer_id)

        return JSONResponse(
            {
                "success": True,
                "module_id": module_id,
                "has_access": has_access,
                **module_info,
            }
        )
    else:
        return JSONResponse(
            {
                "success": True,
                "module_id": module_id,
                "has_access": True,
                "mode": "demo",
            }
        )


@router.post("/activate/{module_id}")
async def activate_module(module_id: str, request: ModuleActivationRequest):
    """Activate a premium module (placeholder for payment integration)"""
    valid_modules = ["iot_advanced", "quality_fix", "safety_fix", "enterprise"]

    if module_id not in valid_modules:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")

    # TODO: Integrate with Stripe or other payment processor
    # This is a placeholder for the actual payment flow

    return JSONResponse(
        {
            "success": True,
            "message": f"Module activation request received for {module_id}",
            "next_steps": [
                "Contact sales@chatterfix.com to complete activation",
                "Or visit https://chatterfix.com/upgrade for self-service",
            ],
            "module": module_id,
            "billing_cycle": request.billing_cycle,
            "contact_sales": "sales@chatterfix.com",
            "upgrade_url": f"https://chatterfix.com/upgrade/{module_id.replace('_', '-')}",
        }
    )


@router.post("/contact-sales")
async def contact_sales(request: ContactSalesRequest):
    """Submit a request to contact sales for enterprise pricing"""
    # TODO: Integrate with CRM (HubSpot, Salesforce, etc.)

    logger.info(f"Sales inquiry from {request.email} at {request.company}")

    return JSONResponse(
        {
            "success": True,
            "message": "Thank you for your interest! Our sales team will contact you within 24 hours.",
            "reference_id": f"ENT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "contact": {
                "name": request.name,
                "email": request.email,
                "company": request.company,
            },
            "next_steps": [
                "A sales representative will contact you within 24 hours",
                "You can also email us directly at sales@chatterfix.com",
                "Or call us at 1-800-CHATTER",
            ],
        }
    )


@router.get("/pricing")
async def get_pricing_table():
    """Get comprehensive pricing table for all modules"""
    return JSONResponse(
        {
            "success": True,
            "pricing": {
                "core": {
                    "name": "ChatterFix Core",
                    "price": "$49/technician/month",
                    "features": [
                        "Voice commands",
                        "Computer vision",
                        "Work order management",
                        "Asset management",
                        "Basic reporting",
                        "Mobile app access",
                    ],
                    "included": True,
                },
                "iot_advanced": {
                    "name": "IoT Advanced",
                    "price": "$199/month + $25/sensor",
                    "type": "add-on",
                    "features": [
                        "Real-time sensor monitoring",
                        "Predictive analytics",
                        "Advanced alerts",
                        "Voice sensor queries",
                    ],
                },
                "quality_fix": {
                    "name": "QualityFix",
                    "price": "$99/month",
                    "type": "add-on",
                    "features": [
                        "HACCP compliance",
                        "ISO 22000",
                        "Batch traceability",
                        "Supplier audits",
                    ],
                },
                "safety_fix": {
                    "name": "SafetyFix",
                    "price": "$99/month",
                    "type": "add-on",
                    "features": [
                        "OSHA compliance",
                        "Incident tracking",
                        "Lab results",
                        "Safety analytics",
                    ],
                },
                "enterprise": {
                    "name": "Enterprise Bundle",
                    "price": "$299/technician/month",
                    "type": "bundle",
                    "includes": ["iot_advanced", "quality_fix", "safety_fix"],
                    "additional_features": [
                        "White-label",
                        "Priority support",
                        "Custom integrations",
                        "Dedicated success manager",
                    ],
                    "savings": "25% vs individual modules",
                },
            },
            "comparison_url": "https://chatterfix.com/pricing",
            "contact_sales": "sales@chatterfix.com",
        }
    )


@router.get("/trial")
async def get_trial_info():
    """Get information about free trial options"""
    customer_id = get_current_customer_id()

    return JSONResponse(
        {
            "success": True,
            "trial_options": {
                "all_modules": {
                    "duration": "14 days",
                    "features": "Full access to all premium modules",
                    "credit_card_required": False,
                    "start_url": "/premium/start-trial",
                }
            },
            "current_status": {
                "customer_id": customer_id,
                "is_trial": True,  # In development mode
                "trial_days_remaining": 14,
            },
            "faq": [
                {
                    "question": "What happens after the trial ends?",
                    "answer": "You'll be prompted to select a plan. Your data is preserved.",
                },
                {
                    "question": "Can I extend my trial?",
                    "answer": "Contact sales@chatterfix.com for trial extensions.",
                },
            ],
        }
    )


logger.info("Premium Modules API router initialized")
