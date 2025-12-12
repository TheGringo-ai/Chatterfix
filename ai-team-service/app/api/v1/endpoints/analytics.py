"""
Analytics endpoints for AI Team Service
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from app.services.ai_orchestrator import AIOrchestrator
from app.api.v1.models.responses import AnalyticsResponse, AgentInfo

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_orchestrator() -> AIOrchestrator:
    """Dependency to get AI orchestrator"""
    from app.main import ai_orchestrator
    if ai_orchestrator is None:
        raise HTTPException(status_code=503, detail="AI orchestrator not available")
    return ai_orchestrator

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_ai_team_analytics(
    orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """Get comprehensive analytics about AI team performance"""
    try:
        analytics = await orchestrator.get_agent_analytics()
        
        # Convert to response model
        agent_details = []
        for agent_detail in analytics.get("agent_details", []):
            agent_details.append(AgentInfo(
                name=agent_detail["name"],
                model_type=agent_detail["model_type"],
                role=agent_detail["role"],
                capabilities=agent_detail["capabilities"],
                available=agent_detail["available"],
                conversation_history_length=agent_detail["conversation_history_length"]
            ))
        
        return AnalyticsResponse(
            total_agents=analytics.get("total_agents", 0),
            available_agents=analytics.get("available_agents", 0),
            agent_details=agent_details,
            performance_history=analytics.get("performance_history", {}),
            total_tasks_completed=analytics.get("total_tasks_completed", 0),
            total_tasks_failed=analytics.get("total_tasks_failed", 0),
            timestamp=analytics.get("timestamp", 0)
        )
        
    except Exception as e:
        logger.error(f"❌ Analytics request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics request failed: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """Get detailed performance metrics"""
    try:
        analytics = await orchestrator.get_agent_analytics()
        
        # Calculate performance metrics
        total_tasks = analytics.get("total_tasks_completed", 0) + analytics.get("total_tasks_failed", 0)
        success_rate = analytics.get("total_tasks_completed", 0) / max(total_tasks, 1) * 100
        
        performance = {
            "success_rate": round(success_rate, 2),
            "total_tasks": total_tasks,
            "completed_tasks": analytics.get("total_tasks_completed", 0),
            "failed_tasks": analytics.get("total_tasks_failed", 0),
            "available_agents": analytics.get("available_agents", 0),
            "total_agents": analytics.get("total_agents", 0),
            "agent_availability": round(analytics.get("available_agents", 0) / max(analytics.get("total_agents", 1), 1) * 100, 2),
            "timestamp": analytics.get("timestamp", 0)
        }
        
        return performance
        
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))