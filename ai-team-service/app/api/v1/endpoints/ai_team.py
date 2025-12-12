"""
AI Team collaboration endpoints
"""

import json
import logging
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from app.services.ai_orchestrator import AIOrchestrator
from app.api.v1.models.requests import (
    ExecuteTaskRequest,
    StreamTaskRequest
)
from app.api.v1.models.responses import (
    ExecuteTaskResponse,
    TaskStatusResponse,
    HealthResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_orchestrator() -> AIOrchestrator:
    """Dependency to get AI orchestrator"""
    # This will be injected by the main app
    from app.main import ai_orchestrator
    if ai_orchestrator is None:
        raise HTTPException(status_code=503, detail="AI orchestrator not available")
    return ai_orchestrator

@router.post("/execute", response_model=ExecuteTaskResponse)
async def execute_collaborative_task(
    request: ExecuteTaskRequest,
    orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """Execute a collaborative AI task"""
    try:
        logger.info(f"📝 Executing task: {request.prompt[:100]}...")
        
        result = await orchestrator.execute_collaborative_task(
            prompt=request.prompt,
            context=request.context or "",
            required_agents=request.required_agents,
            max_iterations=request.max_iterations or 3,
            project_context=request.project_context or "ChatterFix"
        )
        
        # Convert result to response format
        return ExecuteTaskResponse(
            task_id=result.task_id,
            final_answer=result.final_answer,
            agent_responses=[
                {
                    "agent": resp.get("agent", "unknown"),
                    "role": resp.get("role", "assistant"),
                    "response": resp.get("response", ""),
                    "model_type": resp.get("model_type", "unknown"),
                    "confidence": resp.get("confidence", 0.7),
                    "timestamp": resp.get("timestamp", 0)
                }
                for resp in result.agent_responses
            ],
            collaboration_log=result.collaboration_log,
            total_time=result.total_time,
            confidence_score=result.confidence_score,
            success=True
        )
        
    except Exception as e:
        logger.error(f"❌ Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")

@router.post("/stream")
async def stream_collaborative_task(
    request: StreamTaskRequest,
    orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """Stream a collaborative AI task with real-time responses"""
    
    async def generate_stream():
        """Generate streaming response"""
        try:
            async for chunk in orchestrator.stream_collaborative_task(
                prompt=request.prompt,
                context=request.context or "",
                required_agents=request.required_agents,
                max_iterations=request.max_iterations or 3,
                project_context=request.project_context or "ChatterFix"
            ):
                # Format as Server-Sent Events
                yield f"data: {json.dumps(chunk)}\n\n"
                
        except Exception as e:
            error_chunk = {
                "type": "error",
                "message": str(e),
                "timestamp": time.time()
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@router.get("/tasks")
async def get_active_tasks(
    orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """Get list of active tasks"""
    try:
        tasks = await orchestrator.get_active_tasks()
        return {"tasks": tasks, "total": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """Get status of specific task"""
    try:
        task_status = await orchestrator.get_task_status(task_id)
        if task_status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def ai_team_health_check(
    orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """Comprehensive health check for AI team"""
    try:
        health = await orchestrator.health_check()
        return HealthResponse(
            status=health["status"],
            agents=health["agents"],
            active_tasks=health["active_tasks"],
            memory_system=health["memory_system"],
            timestamp=health["timestamp"]
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            agents={},
            active_tasks=0,
            memory_system="error",
            timestamp=time.time(),
            error=str(e)
        )