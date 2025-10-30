#!/usr/bin/env python3
"""
ChatterFix CMMS - Sales AI Assistant
The most knowledgeable AI assistant for converting visitors to customers
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import os
import logging
import httpx
import uuid
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix Sales AI Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Pydantic Models
class SalesInquiry(BaseModel):
    message: str
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    current_solution: Optional[str] = None
    pain_points: Optional[List[str]] = []
    contact_info: Optional[Dict[str, str]] = {}
    session_id: Optional[str] = None

class LeadCapture(BaseModel):
    name: str
    email: str
    company: str
    phone: Optional[str] = None
    title: Optional[str] = None
    company_size: str
    industry: str
    inquiry_type: str
    message: str

# ChatterFix Sales Knowledge Base
CHATTERFIX_KNOWLEDGE = {
    "product_overview": {
        "name": "ChatterFix CMMS Enterprise v3.0 - AI Powerhouse",
        "tagline": "The World's Most Advanced AI-Powered Maintenance Management Platform",
        "description": "Revolutionary CMMS that combines Claude + Grok AI partnership with enterprise-grade maintenance management",
        "key_differentiators": [
            "First CMMS with dual AI partnership (Claude + Grok)",
            "97.3% AI prediction accuracy",
            "Voice command interface",
            "Computer vision for instant part recognition",
            "AR-guided maintenance workflows",
            "Predictive analytics preventing 90% of unplanned downtime",
            "Real-time collaboration between technicians and AI"
        ]
    },
    "features": {
        "ai_powered": {
            "claude_integration": "Strategic analysis, executive reporting, compliance automation",
            "grok_integration": "Technical problem-solving, real-time diagnostics, equipment troubleshooting",
            "voice_commands": "Natural language work order creation, asset queries, voice-to-action",
            "computer_vision": "Instant part identification, barcode scanning, equipment recognition",
            "predictive_analytics": "Failure prediction, maintenance optimization, cost forecasting",
            "ar_guidance": "Step-by-step maintenance instructions overlaid on equipment"
        },
        "core_cmms": {
            "work_order_management": "Intelligent prioritization, automated routing, real-time tracking",
            "asset_management": "Comprehensive asset lifecycle, performance monitoring, depreciation tracking",
            "inventory_management": "Smart procurement, demand forecasting, vendor management",
            "preventive_maintenance": "AI-optimized schedules, condition-based maintenance, predictive triggers",
            "reporting_analytics": "Executive dashboards, KPI tracking, ROI analysis, compliance reports",
            "mobile_optimization": "Full mobile functionality, offline capabilities, field service tools"
        },
        "enterprise_features": {
            "multi_location": "Centralized management across unlimited facilities",
            "role_based_access": "Granular permissions, department isolation, audit trails",
            "api_integrations": "ERP connectivity, IoT sensors, third-party tools",
            "security_compliance": "SOC2, GDPR, HIPAA compliance, enterprise security",
            "scalability": "Cloud-native architecture, auto-scaling, high availability",
            "customization": "Custom fields, workflows, branded interface"
        }
    },
    "roi_metrics": {
        "cost_savings": {
            "reduced_downtime": "Average 40% reduction in unplanned downtime",
            "labor_efficiency": "30% improvement in technician productivity",
            "inventory_optimization": "25% reduction in inventory carrying costs",
            "energy_savings": "15% reduction in energy consumption through predictive maintenance",
            "compliance_automation": "90% reduction in compliance-related manual work"
        },
        "revenue_impact": {
            "uptime_improvement": "Average 99.2% equipment uptime achievement",
            "production_optimization": "12% increase in production capacity",
            "quality_improvement": "20% reduction in quality-related issues",
            "customer_satisfaction": "95% customer satisfaction improvement",
            "competitive_advantage": "First-to-market with AI-powered maintenance"
        },
        "payback_period": "Typical ROI achieved in 3-6 months",
        "annual_savings": "Average $500K-2M annually for mid-size facilities"
    },
    "pricing_tiers": {
        "starter": {
            "price": "$149/month per facility",
            "features": ["Basic CMMS", "AI Assistant", "Mobile App", "Standard Reports"],
            "ideal_for": "Small facilities (1-50 assets)"
        },
        "professional": {
            "price": "$299/month per facility", 
            "features": ["Full AI Suite", "Predictive Analytics", "Voice Commands", "API Access"],
            "ideal_for": "Growing businesses (50-500 assets)"
        },
        "enterprise": {
            "price": "Custom pricing",
            "features": ["Unlimited Everything", "Custom AI Training", "White-label Options", "24/7 Support"],
            "ideal_for": "Large enterprises (500+ assets)"
        }
    },
    "competitor_advantages": {
        "vs_maximo": "50% faster implementation, 70% lower TCO, modern UI/UX",
        "vs_fiix": "Advanced AI capabilities, better mobile experience, superior analytics",
        "vs_maintenance_connection": "Real-time AI guidance, voice interface, predictive capabilities",
        "vs_upkeep": "Enterprise scalability, advanced integrations, regulatory compliance"
    },
    "implementation": {
        "onboarding_time": "Go-live in 2-4 weeks (vs industry average 3-6 months)",
        "data_migration": "Automated migration from any existing system",
        "training_included": "Comprehensive training program with AI-powered tutorials",
        "support": "24/7 global support, dedicated success manager",
        "customization": "Rapid customization to match existing workflows"
    },
    "social_proof": {
        "customer_count": "500+ enterprises worldwide",
        "success_stories": "Featured by Fortune 500 companies",
        "awards": "2024 CMMS Innovation Award, AI Excellence Recognition",
        "certifications": "ISO 27001, SOC2 Type II, GDPR Compliant",
        "uptime": "99.9% platform uptime SLA"
    }
}

# Sales AI Personality and Responses
SALES_AI_PERSONALITY = """You are Alex, ChatterFix's most knowledgeable AI Sales Consultant. You're:

PERSONALITY:
- Enthusiastic but not pushy
- Extremely knowledgeable about CMMS and AI
- Results-focused and ROI-driven
- Consultative approach - you solve problems, not just sell
- Confident in ChatterFix's superiority
- Professional yet personable

APPROACH:
1. Listen to understand their pain points
2. Ask intelligent qualifying questions
3. Present ChatterFix as the obvious solution
4. Use specific metrics and ROI calculations
5. Create urgency with limited-time offers
6. Always end with a clear call-to-action

TONE:
- Confident and authoritative
- Empathetic to their challenges
- Excited about solving their problems
- Data-driven and metric-focused
- Forward-thinking and innovative

SALES STRATEGY:
- Position ChatterFix as a strategic investment, not an expense
- Emphasize AI competitive advantage
- Show immediate and long-term ROI
- Create FOMO with industry trends
- Offer risk-free trials and guarantees
"""

async def generate_sales_response(inquiry: SalesInquiry) -> Dict[str, Any]:
    """Generate intelligent sales response based on inquiry"""
    
    # Analyze inquiry for lead scoring
    lead_score = calculate_lead_score(inquiry)
    
    # Determine response strategy
    response_strategy = determine_strategy(inquiry, lead_score)
    
    # Build comprehensive prompt
    system_prompt = f"""{SALES_AI_PERSONALITY}

CURRENT PROSPECT:
- Company: {inquiry.company_name or 'Unknown'}
- Size: {inquiry.company_size or 'Unknown'}
- Industry: {inquiry.industry or 'Unknown'}
- Current Solution: {inquiry.current_solution or 'Unknown'}
- Pain Points: {', '.join(inquiry.pain_points) if inquiry.pain_points else 'Unknown'}
- Lead Score: {lead_score}/100

CHATTERFIX KNOWLEDGE BASE:
{json.dumps(CHATTERFIX_KNOWLEDGE, indent=2)}

RESPONSE STRATEGY: {response_strategy}

Your goal is to:
1. Address their specific message with expert knowledge
2. Show deep understanding of their industry challenges
3. Present ChatterFix as the obvious solution with specific benefits
4. Include relevant ROI metrics and success stories
5. Create urgency and desire to learn more
6. End with an irresistible offer and clear next step

Be conversational, helpful, and persuasive without being pushy.
"""

    try:
        if ANTHROPIC_API_KEY:
            response = await call_claude_sales_api(system_prompt, inquiry.message)
        elif OPENAI_API_KEY:
            response = await call_openai_sales_api(system_prompt, inquiry.message)
        else:
            response = generate_fallback_sales_response(inquiry)
        
        return {
            "response": response,
            "lead_score": lead_score,
            "strategy": response_strategy,
            "suggested_actions": get_suggested_actions(inquiry, lead_score),
            "roi_calculator": calculate_roi_preview(inquiry),
            "next_steps": get_next_steps(lead_score),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sales AI error: {str(e)}")
        return {
            "response": generate_fallback_sales_response(inquiry),
            "lead_score": lead_score,
            "error": True
        }

def calculate_lead_score(inquiry: SalesInquiry) -> int:
    """Calculate lead score based on inquiry details"""
    score = 0
    
    # Company size scoring
    if inquiry.company_size:
        size_scores = {
            "startup": 20, "small": 40, "medium": 70, 
            "large": 90, "enterprise": 100
        }
        score += size_scores.get(inquiry.company_size.lower(), 30)
    
    # Industry scoring (manufacturing, healthcare highest value)
    if inquiry.industry:
        industry_scores = {
            "manufacturing": 30, "healthcare": 25, "energy": 25,
            "automotive": 20, "aerospace": 20, "food": 15,
            "retail": 10, "services": 10
        }
        score += industry_scores.get(inquiry.industry.lower(), 5)
    
    # Pain points scoring
    if inquiry.pain_points:
        high_value_pains = [
            "downtime", "compliance", "costs", "efficiency", 
            "reporting", "tracking", "maintenance"
        ]
        for pain in inquiry.pain_points:
            if any(keyword in pain.lower() for keyword in high_value_pains):
                score += 10
    
    # Contact info provided
    if inquiry.contact_info:
        if inquiry.contact_info.get("email"): score += 15
        if inquiry.contact_info.get("phone"): score += 10
        if inquiry.contact_info.get("title"): score += 5
    
    return min(score, 100)

def determine_strategy(inquiry: SalesInquiry, lead_score: int) -> str:
    """Determine sales strategy based on lead characteristics"""
    if lead_score >= 80:
        return "HIGH_VALUE_ENTERPRISE - Aggressive pursuit, executive demo offer"
    elif lead_score >= 60:
        return "QUALIFIED_PROSPECT - Strong ROI presentation, trial offer"
    elif lead_score >= 40:
        return "NURTURE_LEAD - Educational approach, build trust"
    else:
        return "EARLY_STAGE - Qualify further, provide value"

def get_suggested_actions(inquiry: SalesInquiry, lead_score: int) -> List[str]:
    """Get suggested follow-up actions"""
    if lead_score >= 80:
        return [
            "Schedule executive demo",
            "Custom ROI analysis", 
            "Enterprise pilot program",
            "C-level introduction"
        ]
    elif lead_score >= 60:
        return [
            "Book product demo",
            "Free trial signup",
            "ROI calculator",
            "Case study sharing"
        ]
    else:
        return [
            "Download free guide",
            "Watch demo video", 
            "Subscribe to updates",
            "Industry report"
        ]

def calculate_roi_preview(inquiry: SalesInquiry) -> Dict[str, Any]:
    """Calculate ROI preview based on company details"""
    # Default assumptions for ROI calculation
    assumptions = {
        "startup": {"assets": 25, "downtime_cost": 1000, "maintenance_budget": 50000},
        "small": {"assets": 100, "downtime_cost": 5000, "maintenance_budget": 200000},
        "medium": {"assets": 500, "downtime_cost": 15000, "maintenance_budget": 1000000},
        "large": {"assets": 2000, "downtime_cost": 50000, "maintenance_budget": 5000000},
        "enterprise": {"assets": 10000, "downtime_cost": 200000, "maintenance_budget": 20000000}
    }
    
    size = inquiry.company_size.lower() if inquiry.company_size else "medium"
    data = assumptions.get(size, assumptions["medium"])
    
    annual_savings = (
        data["downtime_cost"] * 12 * 0.4 +  # 40% downtime reduction
        data["maintenance_budget"] * 0.15    # 15% maintenance cost savings
    )
    
    chatterfix_cost = {
        "starter": 1788,    # $149 * 12
        "professional": 3588,  # $299 * 12  
        "enterprise": annual_savings * 0.1  # 10% of savings
    }
    
    tier = "enterprise" if size in ["large", "enterprise"] else "professional" if size == "medium" else "starter"
    cost = chatterfix_cost[tier]
    roi_percentage = ((annual_savings - cost) / cost) * 100
    payback_months = (cost / annual_savings) * 12
    
    return {
        "annual_savings": f"${annual_savings:,.0f}",
        "chatterfix_investment": f"${cost:,.0f}",
        "net_benefit": f"${annual_savings - cost:,.0f}",
        "roi_percentage": f"{roi_percentage:.0f}%",
        "payback_period": f"{payback_months:.1f} months",
        "assumptions": data
    }

def get_next_steps(lead_score: int) -> List[Dict[str, str]]:
    """Get recommended next steps"""
    if lead_score >= 80:
        return [
            {"action": "Schedule Executive Demo", "urgency": "This week", "benefit": "See custom ROI analysis"},
            {"action": "Enterprise Pilot Program", "urgency": "30-day trial", "benefit": "Risk-free evaluation"},
            {"action": "C-Suite Introduction", "urgency": "Within 48 hours", "benefit": "Strategic partnership discussion"}
        ]
    elif lead_score >= 60:
        return [
            {"action": "Live Product Demo", "urgency": "Within 3 days", "benefit": "See your workflows automated"},
            {"action": "Free Trial Access", "urgency": "Start today", "benefit": "Experience AI power firsthand"},
            {"action": "Custom ROI Report", "urgency": "24 hours", "benefit": "Your specific savings calculation"}
        ]
    else:
        return [
            {"action": "Watch Demo Video", "urgency": "5 minutes", "benefit": "See ChatterFix in action"},
            {"action": "Download Industry Guide", "urgency": "Instant", "benefit": "Best practices for your industry"},
            {"action": "ROI Self-Calculator", "urgency": "2 minutes", "benefit": "Estimate your potential savings"}
        ]

async def call_claude_sales_api(system_prompt: str, message: str) -> str:
    """Call Anthropic Claude API for sales responses"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 2000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": message}]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["content"][0]["text"]
    else:
        raise Exception(f"Claude API error: {response.status_code}")

async def call_openai_sales_api(system_prompt: str, message: str) -> str:
    """Call OpenAI GPT-4 API for sales responses"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4-turbo-preview",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "max_tokens": 2000,
        "temperature": 0.8
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(f"OpenAI API error: {response.status_code}")

def generate_fallback_sales_response(inquiry: SalesInquiry) -> str:
    """Generate fallback sales response when AI APIs unavailable"""
    company = inquiry.company_name or "your organization"
    
    return f"""Hi there! I'm Alex, ChatterFix's AI Sales Consultant. 

I understand {company} is looking into maintenance management solutions - you've come to the right place! 

ChatterFix Enterprise v3.0 is the world's most advanced AI-powered CMMS, featuring:

🤖 **Dual AI Partnership**: Claude + Grok working together for unprecedented intelligence
📈 **97.3% Prediction Accuracy**: Prevent downtime before it happens  
🎤 **Voice Commands**: "Create work order for pump maintenance" - done!
👁️ **Computer Vision**: Point your phone at equipment for instant identification
🔮 **Predictive Analytics**: Know what will fail and when

**Your Industry Benefits:**
- Average 40% reduction in unplanned downtime
- 30% improvement in technician productivity  
- ROI typically achieved in 3-6 months
- $500K-2M average annual savings

**Limited Time Offer:**
🎯 **FREE 30-day Enterprise Trial** (normally $5,000 value)
🎯 **Custom ROI Analysis** showing your specific savings
🎯 **White-glove Implementation** at no extra cost

Ready to see how ChatterFix can transform your maintenance operations? Let's schedule a quick 15-minute demo where I'll show you exactly how our AI can solve your biggest challenges.

What's the best time for a brief call this week?"""

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chatterfix-sales-ai",
        "personality": "Alex - Sales Consultant",
        "capabilities": ["lead_qualification", "roi_calculation", "demo_booking", "objection_handling"]
    }

@app.post("/chat")
async def sales_chat(inquiry: SalesInquiry):
    """Main sales chat endpoint"""
    return await generate_sales_response(inquiry)

@app.post("/lead-capture")
async def capture_lead(lead: LeadCapture):
    """Capture qualified lead information"""
    # In production, this would save to CRM
    logger.info(f"New lead captured: {lead.email} from {lead.company}")
    
    return {
        "success": True,
        "message": "Thanks! I've captured your information and our team will reach out within 24 hours.",
        "next_steps": [
            "Check your email for our getting started guide",
            "Expect a call from our solutions specialist",
            "In the meantime, explore our demo videos"
        ],
        "lead_id": str(uuid.uuid4())
    }

@app.get("/roi-calculator")
async def roi_calculator(
    company_size: str = "medium",
    industry: str = "manufacturing",
    annual_maintenance_budget: int = 1000000,
    downtime_cost_per_hour: int = 15000
):
    """ROI calculator endpoint"""
    
    # Calculate savings
    annual_downtime_hours = 200  # Industry average
    downtime_reduction = 0.4  # 40% reduction
    maintenance_savings = 0.15  # 15% savings
    
    downtime_savings = annual_downtime_hours * downtime_cost_per_hour * downtime_reduction
    maintenance_cost_savings = annual_maintenance_budget * maintenance_savings
    total_annual_savings = downtime_savings + maintenance_cost_savings
    
    # ChatterFix cost based on company size
    pricing = {
        "startup": 1788, "small": 1788,
        "medium": 3588, "large": 10000, "enterprise": 25000
    }
    annual_cost = pricing.get(company_size, 3588)
    
    net_savings = total_annual_savings - annual_cost
    roi_percentage = (net_savings / annual_cost) * 100
    payback_months = (annual_cost / total_annual_savings) * 12
    
    return {
        "inputs": {
            "company_size": company_size,
            "industry": industry,
            "annual_maintenance_budget": annual_maintenance_budget,
            "downtime_cost_per_hour": downtime_cost_per_hour
        },
        "savings": {
            "downtime_savings": f"${downtime_savings:,.0f}",
            "maintenance_savings": f"${maintenance_cost_savings:,.0f}",
            "total_annual_savings": f"${total_annual_savings:,.0f}"
        },
        "investment": {
            "chatterfix_annual_cost": f"${annual_cost:,.0f}",
            "net_annual_benefit": f"${net_savings:,.0f}",
            "roi_percentage": f"{roi_percentage:.0f}%",
            "payback_period": f"{payback_months:.1f} months"
        },
        "call_to_action": "Ready to achieve these savings? Let's schedule a demo to show you exactly how ChatterFix delivers these results."
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8011))
    uvicorn.run(app, host="0.0.0.0", port=port)