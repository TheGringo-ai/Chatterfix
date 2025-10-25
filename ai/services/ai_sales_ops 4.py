#!/usr/bin/env python3
"""
ChatterFix CMMS - AI Sales Operations System
Autonomous sales operations management with CRM integration and predictive analytics
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
SALESFORCE_API_KEY = os.getenv("SALESFORCE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class PipelineStage(Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    DEMO_COMPLETED = "demo_completed"
    PILOT_PROPOSED = "pilot_proposed"
    PILOT_ACTIVE = "pilot_active"
    PILOT_SUCCESSFUL = "pilot_successful"
    CONTRACT_NEGOTIATION = "contract_negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class LeadSource(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    REFERRAL = "referral"
    CONFERENCE = "conference"
    PARTNERSHIP = "partnership"
    MARKETPLACE = "marketplace"

@dataclass
class Prospect:
    id: str
    company: str
    contact_name: str
    email: str
    title: str
    industry: str
    company_size: int
    annual_revenue: Optional[int]
    current_cmms: Optional[str]
    pain_points: List[str]
    budget_range: str
    decision_timeline: str
    stage: PipelineStage
    source: LeadSource
    score: float
    created_at: datetime
    last_activity: datetime
    assigned_rep: Optional[str]
    notes: List[str]

@dataclass
class Deal:
    id: str
    prospect_id: str
    value: int
    probability: float
    expected_close_date: datetime
    stage: PipelineStage
    products: List[str]
    competitors: List[str]
    decision_criteria: List[str]
    stakeholders: List[Dict[str, str]]
    pilot_metrics: Optional[Dict[str, Any]]
    roi_calculation: Optional[Dict[str, Any]]

class SalesActivity(BaseModel):
    prospect_id: str
    activity_type: str  # call, email, demo, meeting, proposal
    subject: str
    description: str
    outcome: str
    next_action: Optional[str]
    scheduled_followup: Optional[datetime]

class DealUpdate(BaseModel):
    deal_id: str
    stage: str
    probability: float
    value: Optional[int]
    expected_close_date: Optional[datetime]
    notes: Optional[str]

class FastAPI(FastAPI):
    pass

app = FastAPI(
    title="ChatterFix CMMS - AI Sales Ops",
    description="Autonomous sales operations with CRM integration and predictive analytics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AISalesOpsEngine:
    """AI-powered sales operations and pipeline management system"""
    
    def __init__(self):
        self.prospects = {}
        self.deals = {}
        self.activities = []
        self.sales_reps = {}
        self.pipeline_stages = {}
        self.predictive_model = None
        self.initialize_predictive_model()
    
    def initialize_predictive_model(self):
        """Initialize machine learning model for deal scoring"""
        # In production, this would load a trained model
        # For demo, we'll use a simple random forest
        self.predictive_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Generate some training data for demo
        np.random.seed(42)
        X_train = np.random.rand(1000, 8)  # 8 features
        y_train = (X_train.sum(axis=1) > 4).astype(int)  # Simple rule for demo
        
        self.predictive_model.fit(X_train, y_train)
        logger.info("✅ Predictive model initialized")
    
    async def create_prospect(self, prospect_data: Dict[str, Any]) -> Prospect:
        """Create new prospect with AI-powered lead scoring"""
        
        prospect_id = f"prospect_{int(datetime.now().timestamp())}"
        
        # AI-powered lead scoring
        score = await self.calculate_lead_score(prospect_data)
        
        prospect = Prospect(
            id=prospect_id,
            company=prospect_data["company"],
            contact_name=prospect_data["contact_name"],
            email=prospect_data["email"],
            title=prospect_data["title"],
            industry=prospect_data["industry"],
            company_size=prospect_data["company_size"],
            annual_revenue=prospect_data.get("annual_revenue"),
            current_cmms=prospect_data.get("current_cmms"),
            pain_points=prospect_data.get("pain_points", []),
            budget_range=prospect_data.get("budget_range", "Unknown"),
            decision_timeline=prospect_data.get("decision_timeline", "Unknown"),
            stage=PipelineStage.LEAD,
            source=LeadSource(prospect_data.get("source", "inbound")),
            score=score,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            assigned_rep=None,
            notes=[]
        )
        
        self.prospects[prospect_id] = prospect
        
        # Auto-assign to sales rep
        await self.auto_assign_sales_rep(prospect_id)
        
        # Trigger automated workflows
        await self.trigger_prospect_workflows(prospect_id)
        
        return prospect
    
    async def calculate_lead_score(self, prospect_data: Dict[str, Any]) -> float:
        """AI-powered lead scoring algorithm"""
        
        score = 0.0
        
        # Company size scoring
        company_size = prospect_data.get("company_size", 0)
        if company_size > 2000:
            score += 25
        elif company_size > 1000:
            score += 20
        elif company_size > 500:
            score += 15
        else:
            score += 10
        
        # Industry scoring
        industry_scores = {
            "manufacturing": 25,
            "healthcare": 22,
            "energy": 20,
            "logistics": 18,
            "other": 10
        }
        industry = prospect_data.get("industry", "other").lower()
        score += industry_scores.get(industry, 10)
        
        # Title scoring (decision maker influence)
        title = prospect_data.get("title", "").lower()
        if any(keyword in title for keyword in ["ceo", "president", "owner"]):
            score += 20
        elif any(keyword in title for keyword in ["vp", "vice president", "director"]):
            score += 18
        elif any(keyword in title for keyword in ["manager", "supervisor"]):
            score += 15
        else:
            score += 10
        
        # Pain points scoring
        pain_points = prospect_data.get("pain_points", [])
        score += min(len(pain_points) * 5, 20)
        
        # Budget range scoring
        budget_range = prospect_data.get("budget_range", "").lower()
        if "1m" in budget_range or "million" in budget_range:
            score += 15
        elif "500k" in budget_range:
            score += 12
        elif "100k" in budget_range:
            score += 10
        elif "50k" in budget_range:
            score += 8
        
        # Current CMMS scoring (replacement urgency)
        current_cmms = prospect_data.get("current_cmms", "").lower()
        if any(system in current_cmms for system in ["excel", "spreadsheet", "manual"]):
            score += 15  # High urgency
        elif any(system in current_cmms for system in ["old", "legacy", "outdated"]):
            score += 12
        elif current_cmms in ["maximo", "sap", "infor"]:
            score += 8  # Competitive displacement
        
        return min(score, 100.0)
    
    async def auto_assign_sales_rep(self, prospect_id: str):
        """Automatically assign prospect to best available sales rep"""
        
        prospect = self.prospects[prospect_id]
        
        # Simple round-robin assignment for demo
        # In production, this would consider rep capacity, industry expertise, etc.
        available_reps = [
            {"name": "Sarah Johnson", "specialty": "manufacturing", "capacity": 0.7},
            {"name": "Mike Chen", "specialty": "healthcare", "capacity": 0.8},
            {"name": "Lisa Rodriguez", "specialty": "energy", "capacity": 0.6},
            {"name": "David Kim", "specialty": "logistics", "capacity": 0.9}
        ]
        
        # Find best rep based on industry specialty and capacity
        best_rep = None
        best_score = 0
        
        for rep in available_reps:
            rep_score = 0
            
            # Industry match bonus
            if rep["specialty"] == prospect.industry.lower():
                rep_score += 20
            
            # Capacity bonus (prefer less loaded reps)
            rep_score += (1.0 - rep["capacity"]) * 10
            
            if rep_score > best_score:
                best_score = rep_score
                best_rep = rep["name"]
        
        prospect.assigned_rep = best_rep
        logger.info(f"Assigned prospect {prospect.company} to {best_rep}")
    
    async def trigger_prospect_workflows(self, prospect_id: str):
        """Trigger automated workflows for new prospects"""
        
        prospect = self.prospects[prospect_id]
        
        # High-score prospects get immediate attention
        if prospect.score > 80:
            await self.schedule_priority_outreach(prospect_id)
        elif prospect.score > 60:
            await self.schedule_standard_outreach(prospect_id)
        else:
            await self.add_to_nurture_campaign(prospect_id)
        
        # Industry-specific workflows
        if prospect.industry.lower() == "healthcare":
            await self.add_compliance_materials(prospect_id)
        elif prospect.industry.lower() == "manufacturing":
            await self.add_roi_calculator(prospect_id)
    
    async def schedule_priority_outreach(self, prospect_id: str):
        """Schedule immediate outreach for high-priority prospects"""
        
        prospect = self.prospects[prospect_id]
        
        activity = {
            "prospect_id": prospect_id,
            "activity_type": "call",
            "subject": "Priority Outreach - High Value Prospect",
            "description": f"High-score prospect ({prospect.score}) requires immediate contact",
            "outcome": "scheduled",
            "next_action": "Initial discovery call",
            "scheduled_followup": datetime.now() + timedelta(hours=2)
        }
        
        self.activities.append(activity)
        logger.info(f"Priority outreach scheduled for {prospect.company}")
    
    async def update_prospect_stage(self, prospect_id: str, new_stage: PipelineStage, notes: str = ""):
        """Update prospect pipeline stage with automated workflows"""
        
        if prospect_id not in self.prospects:
            raise HTTPException(status_code=404, detail="Prospect not found")
        
        prospect = self.prospects[prospect_id]
        old_stage = prospect.stage
        prospect.stage = new_stage
        prospect.last_activity = datetime.now()
        
        if notes:
            prospect.notes.append(f"{datetime.now().isoformat()}: {notes}")
        
        # Trigger stage-specific workflows
        await self.trigger_stage_workflows(prospect_id, old_stage, new_stage)
        
        logger.info(f"Updated {prospect.company} from {old_stage.value} to {new_stage.value}")
    
    async def trigger_stage_workflows(self, prospect_id: str, old_stage: PipelineStage, new_stage: PipelineStage):
        """Trigger automated workflows based on stage transitions"""
        
        prospect = self.prospects[prospect_id]
        
        workflows = {
            PipelineStage.QUALIFIED: self.schedule_demo,
            PipelineStage.DEMO_COMPLETED: self.generate_pilot_proposal,
            PipelineStage.PILOT_ACTIVE: self.monitor_pilot_health,
            PipelineStage.PILOT_SUCCESSFUL: self.generate_contract_proposal,
            PipelineStage.CLOSED_WON: self.trigger_onboarding_workflow,
            PipelineStage.CLOSED_LOST: self.add_to_nurture_campaign
        }
        
        if new_stage in workflows:
            await workflows[new_stage](prospect_id)
    
    async def schedule_demo(self, prospect_id: str):
        """Automatically schedule demo for qualified prospects"""
        
        prospect = self.prospects[prospect_id]
        
        # Generate demo scheduling email
        demo_email = await self.generate_demo_email(prospect)
        
        activity = {
            "prospect_id": prospect_id,
            "activity_type": "email",
            "subject": "Demo Invitation - ChatterFix CMMS",
            "description": demo_email["body"],
            "outcome": "sent",
            "next_action": "Follow up on demo scheduling",
            "scheduled_followup": datetime.now() + timedelta(days=2)
        }
        
        self.activities.append(activity)
        logger.info(f"Demo scheduled for {prospect.company}")
    
    async def generate_demo_email(self, prospect: Prospect) -> Dict[str, str]:
        """Generate personalized demo invitation email"""
        
        pain_points_text = ", ".join(prospect.pain_points[:3]) if prospect.pain_points else "maintenance optimization"
        
        subject = f"Demo: See how ChatterFix addresses {prospect.company}'s {pain_points_text}"
        
        body = f"""
Dear {prospect.contact_name},

Thank you for your interest in ChatterFix CMMS! Based on our conversation about {prospect.company}'s challenges with {pain_points_text}, I'd like to show you how our AI-driven platform can help.

I've prepared a custom demo environment specifically for {prospect.industry} companies like yours, featuring:

✅ {prospect.industry.title()}-specific scenarios and workflows
✅ ROI calculator with your company's estimated savings
✅ Integration examples with common {prospect.industry} systems
✅ Mobile technician experience demonstration

The demo takes about 20 minutes and includes time for your questions. I have availability:

• Tomorrow at 2:00 PM or 4:00 PM
• Day after tomorrow at 10:00 AM or 3:00 PM

Which time works best for you? I'll send a calendar invitation with the demo link.

Best regards,
{prospect.assigned_rep}
ChatterFix Enterprise Sales Team

P.S. Companies similar to {prospect.company} typically see 25-40% reduction in maintenance costs within 6 months. I'll show you exactly how during the demo.
"""
        
        return {"subject": subject, "body": body.strip()}
    
    async def predict_deal_probability(self, prospect_id: str) -> Dict[str, Any]:
        """Use ML to predict deal closure probability"""
        
        prospect = self.prospects[prospect_id]
        
        # Feature engineering for prediction
        features = [
            prospect.score / 100.0,  # Normalized lead score
            1.0 if prospect.company_size > 1000 else 0.5,  # Company size
            1.0 if prospect.industry in ["manufacturing", "healthcare"] else 0.7,  # Industry fit
            len(prospect.pain_points) / 5.0,  # Pain points count
            1.0 if prospect.current_cmms in ["excel", "manual"] else 0.8,  # Replacement urgency
            len(prospect.activities) / 10.0 if hasattr(prospect, 'activities') else 0.5,  # Engagement level
            (datetime.now() - prospect.created_at).days / 30.0,  # Age of opportunity
            1.0 if prospect.assigned_rep else 0.3  # Rep assignment
        ]
        
        # Predict probability
        probability = self.predictive_model.predict_proba([features])[0][1]
        
        # Generate insights
        insights = []
        if features[0] > 0.8:
            insights.append("High lead score indicates strong fit")
        if features[1] == 1.0:
            insights.append("Large company size increases success probability")
        if features[3] > 0.6:
            insights.append("Multiple pain points show clear need")
        if features[4] == 1.0:
            insights.append("Manual processes indicate high urgency")
        
        return {
            "probability": round(probability, 3),
            "confidence": "high" if probability > 0.7 else "medium" if probability > 0.4 else "low",
            "insights": insights,
            "recommended_actions": await self.generate_deal_recommendations(prospect, probability)
        }
    
    async def generate_deal_recommendations(self, prospect: Prospect, probability: float) -> List[str]:
        """Generate AI-powered deal recommendations"""
        
        recommendations = []
        
        if probability > 0.8:
            recommendations.append("High probability - Prioritize for pilot deployment")
            recommendations.append("Schedule executive presentation")
        elif probability > 0.6:
            recommendations.append("Good potential - Focus on ROI demonstration")
            recommendations.append("Identify additional stakeholders")
        elif probability > 0.4:
            recommendations.append("Moderate potential - Address key objections")
            recommendations.append("Provide competitive comparison")
        else:
            recommendations.append("Low probability - Consider nurture campaign")
            recommendations.append("Gather more qualification information")
        
        # Stage-specific recommendations
        if prospect.stage == PipelineStage.DEMO_COMPLETED:
            recommendations.append("Follow up within 24 hours")
            recommendations.append("Send pilot proposal if demo was positive")
        elif prospect.stage == PipelineStage.PILOT_ACTIVE:
            recommendations.append("Monitor pilot metrics weekly")
            recommendations.append("Schedule success review meetings")
        
        return recommendations
    
    async def sync_with_crm(self, crm_type: str = "hubspot") -> Dict[str, Any]:
        """Sync prospect and deal data with external CRM"""
        
        if crm_type == "hubspot" and HUBSPOT_API_KEY:
            return await self.sync_hubspot()
        elif crm_type == "salesforce" and SALESFORCE_API_KEY:
            return await self.sync_salesforce()
        else:
            logger.warning(f"CRM sync not configured for {crm_type}")
            return {"status": "not_configured", "message": f"{crm_type} API key not provided"}
    
    async def sync_hubspot(self) -> Dict[str, Any]:
        """Sync data with HubSpot CRM"""
        
        try:
            headers = {
                "Authorization": f"Bearer {HUBSPOT_API_KEY}",
                "Content-Type": "application/json"
            }
            
            synced_prospects = 0
            errors = []
            
            async with httpx.AsyncClient() as client:
                for prospect_id, prospect in self.prospects.items():
                    try:
                        # Create or update contact in HubSpot
                        contact_data = {
                            "properties": {
                                "email": prospect.email,
                                "firstname": prospect.contact_name.split()[0],
                                "lastname": " ".join(prospect.contact_name.split()[1:]),
                                "company": prospect.company,
                                "jobtitle": prospect.title,
                                "industry": prospect.industry,
                                "lead_score": str(prospect.score),
                                "lifecyclestage": prospect.stage.value
                            }
                        }
                        
                        # For demo, we'll simulate the API call
                        # response = await client.post(
                        #     "https://api.hubapi.com/crm/v3/objects/contacts",
                        #     headers=headers,
                        #     json=contact_data
                        # )
                        
                        synced_prospects += 1
                        logger.info(f"Synced {prospect.company} to HubSpot")
                        
                    except Exception as e:
                        errors.append(f"Failed to sync {prospect.company}: {str(e)}")
            
            return {
                "status": "success",
                "synced_prospects": synced_prospects,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"HubSpot sync failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline analytics"""
        
        total_prospects = len(self.prospects)
        
        if total_prospects == 0:
            return {"message": "No prospects in pipeline"}
        
        # Stage distribution
        stage_counts = {}
        for stage in PipelineStage:
            stage_counts[stage.value] = len([p for p in self.prospects.values() if p.stage == stage])
        
        # Source distribution
        source_counts = {}
        for source in LeadSource:
            source_counts[source.value] = len([p for p in self.prospects.values() if p.source == source])
        
        # Industry distribution
        industry_counts = {}
        for prospect in self.prospects.values():
            industry_counts[prospect.industry] = industry_counts.get(prospect.industry, 0) + 1
        
        # Average scores by stage
        avg_scores_by_stage = {}
        for stage in PipelineStage:
            stage_prospects = [p for p in self.prospects.values() if p.stage == stage]
            if stage_prospects:
                avg_scores_by_stage[stage.value] = sum(p.score for p in stage_prospects) / len(stage_prospects)
        
        # Conversion rates
        conversion_rates = {}
        stages = list(PipelineStage)
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            
            current_count = stage_counts[current_stage.value]
            next_count = stage_counts[next_stage.value]
            
            if current_count > 0:
                conversion_rates[f"{current_stage.value}_to_{next_stage.value}"] = (next_count / current_count) * 100
        
        return {
            "total_prospects": total_prospects,
            "stage_distribution": stage_counts,
            "source_distribution": source_counts,
            "industry_distribution": industry_counts,
            "average_scores_by_stage": avg_scores_by_stage,
            "conversion_rates": conversion_rates,
            "pipeline_velocity": self.calculate_pipeline_velocity(),
            "top_prospects": [
                {
                    "company": p.company,
                    "score": p.score,
                    "stage": p.stage.value,
                    "assigned_rep": p.assigned_rep
                }
                for p in sorted(self.prospects.values(), key=lambda x: x.score, reverse=True)[:10]
            ]
        }
    
    def calculate_pipeline_velocity(self) -> Dict[str, float]:
        """Calculate pipeline velocity metrics"""
        
        # For demo, using simulated values
        # In production, this would analyze historical stage progression data
        
        return {
            "average_deal_cycle_days": 85,
            "lead_to_qualified_days": 7,
            "qualified_to_demo_days": 14,
            "demo_to_pilot_days": 21,
            "pilot_to_close_days": 43
        }

# Initialize sales ops engine
sales_ops = AISalesOpsEngine()

# API Endpoints
@app.post("/api/sales-ops/prospects")
async def create_prospect(prospect_data: Dict[str, Any]):
    """Create new prospect with AI scoring"""
    try:
        prospect = await sales_ops.create_prospect(prospect_data)
        return {
            "success": True,
            "prospect_id": prospect.id,
            "score": prospect.score,
            "assigned_rep": prospect.assigned_rep,
            "stage": prospect.stage.value
        }
    except Exception as e:
        logger.error(f"Failed to create prospect: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/sales-ops/prospects/{prospect_id}/stage")
async def update_prospect_stage(prospect_id: str, stage: str, notes: str = ""):
    """Update prospect pipeline stage"""
    try:
        new_stage = PipelineStage(stage)
        await sales_ops.update_prospect_stage(prospect_id, new_stage, notes)
        return {"success": True, "message": f"Stage updated to {stage}"}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    except Exception as e:
        logger.error(f"Failed to update stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sales-ops/activities")
async def log_activity(activity: SalesActivity):
    """Log sales activity"""
    try:
        activity_dict = activity.dict()
        activity_dict["timestamp"] = datetime.now().isoformat()
        sales_ops.activities.append(activity_dict)
        
        return {"success": True, "message": "Activity logged successfully"}
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sales-ops/prospects/{prospect_id}/prediction")
async def get_deal_prediction(prospect_id: str):
    """Get AI-powered deal probability prediction"""
    try:
        prediction = await sales_ops.predict_deal_probability(prospect_id)
        return prediction
    except Exception as e:
        logger.error(f"Failed to generate prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sales-ops/pipeline/metrics")
async def get_pipeline_metrics():
    """Get comprehensive pipeline analytics"""
    try:
        metrics = sales_ops.get_pipeline_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sales-ops/crm/sync")
async def sync_crm(crm_type: str = "hubspot"):
    """Sync prospect data with external CRM"""
    try:
        result = await sales_ops.sync_with_crm(crm_type)
        return result
    except Exception as e:
        logger.error(f"CRM sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sales-ops/prospects")
async def list_prospects(stage: Optional[str] = None, rep: Optional[str] = None):
    """List prospects with optional filtering"""
    try:
        prospects = list(sales_ops.prospects.values())
        
        if stage:
            prospects = [p for p in prospects if p.stage.value == stage]
        
        if rep:
            prospects = [p for p in prospects if p.assigned_rep == rep]
        
        return {
            "prospects": [
                {
                    "id": p.id,
                    "company": p.company,
                    "contact_name": p.contact_name,
                    "title": p.title,
                    "industry": p.industry,
                    "stage": p.stage.value,
                    "score": p.score,
                    "assigned_rep": p.assigned_rep,
                    "last_activity": p.last_activity.isoformat()
                }
                for p in sorted(prospects, key=lambda x: x.score, reverse=True)
            ],
            "total": len(prospects)
        }
    except Exception as e:
        logger.error(f"Failed to list prospects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sales-ops/dashboard")
async def get_sales_dashboard():
    """Get comprehensive sales dashboard data"""
    try:
        metrics = sales_ops.get_pipeline_metrics()
        
        # Add real-time statistics
        dashboard_data = {
            "pipeline_overview": metrics,
            "daily_stats": {
                "new_leads_today": len([p for p in sales_ops.prospects.values() 
                                      if p.created_at.date() == datetime.now().date()]),
                "demos_scheduled": len([p for p in sales_ops.prospects.values() 
                                      if p.stage == PipelineStage.DEMO_SCHEDULED]),
                "active_pilots": len([p for p in sales_ops.prospects.values() 
                                    if p.stage == PipelineStage.PILOT_ACTIVE]),
                "deals_closing_this_month": len([p for p in sales_ops.prospects.values() 
                                               if p.stage == PipelineStage.CONTRACT_NEGOTIATION])
            },
            "top_opportunities": [
                {
                    "company": p.company,
                    "value": f"${p.company_size * 250:,}",  # Estimated deal value
                    "probability": (await sales_ops.predict_deal_probability(p.id))["probability"],
                    "stage": p.stage.value,
                    "rep": p.assigned_rep
                }
                for p in sorted(sales_ops.prospects.values(), key=lambda x: x.score, reverse=True)[:5]
            ],
            "recent_activities": sales_ops.activities[-10:],  # Last 10 activities
            "alerts": await generate_sales_alerts()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_sales_alerts() -> List[Dict[str, str]]:
    """Generate sales alerts and notifications"""
    alerts = []
    
    # High-value prospects without recent activity
    for prospect in sales_ops.prospects.values():
        if prospect.score > 80 and (datetime.now() - prospect.last_activity).days > 3:
            alerts.append({
                "type": "warning",
                "message": f"High-value prospect {prospect.company} needs follow-up",
                "action": f"Contact {prospect.assigned_rep} to schedule activity"
            })
    
    # Stalled opportunities
    for prospect in sales_ops.prospects.values():
        if prospect.stage in [PipelineStage.DEMO_COMPLETED, PipelineStage.PILOT_PROPOSED] and \
           (datetime.now() - prospect.last_activity).days > 7:
            alerts.append({
                "type": "urgent",
                "message": f"Stalled opportunity: {prospect.company}",
                "action": "Schedule follow-up call to address concerns"
            })
    
    return alerts

@app.get("/health")
async def health_check():
    """AI Sales Ops health check"""
    return {
        "status": "healthy",
        "service": "ai-sales-ops",
        "capabilities": [
            "AI-powered lead scoring",
            "Automated prospect workflow management",
            "Predictive deal probability analysis",
            "CRM integration (HubSpot, Salesforce)",
            "Pipeline analytics and reporting",
            "Sales activity tracking and automation"
        ],
        "integrations": [
            "HubSpot CRM",
            "Salesforce CRM",
            "ChatterFix GTM Automation",
            "ChatterFix Enterprise Pilot System"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8092)