#!/usr/bin/env python3
"""
ChatterFix CMMS - AI Collaboration API Endpoints
FastAPI endpoints for the AI Collaboration System
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from ai_collaboration_system import (
    collaboration_system,
    AIModel,
    TaskStatus, 
    Priority,
    initialize_ai_collaboration
)

logger = logging.getLogger(__name__)

# Create router for AI collaboration endpoints
ai_collaboration_router = APIRouter(prefix="/api/ai-collaboration", tags=["AI Collaboration"])

# Pydantic models for API requests/responses
class StartSessionRequest(BaseModel):
    ai_model: str
    context_notes: Optional[str] = ""

class EndSessionRequest(BaseModel):
    session_id: str
    handoff_notes: Optional[str] = ""
    next_ai: Optional[str] = None

class CreateTaskRequest(BaseModel):
    title: str
    description: str
    assigned_ai: str
    priority: str
    estimated_effort: Optional[int] = 1
    due_date: Optional[datetime] = None

class CompleteTaskRequest(BaseModel):
    task_id: str
    completion_notes: Optional[str] = ""
    artifacts: Optional[List[str]] = None

class UpdateTaskRequest(BaseModel):
    task_id: str
    status: str
    notes: Optional[str] = ""
    actual_effort: Optional[int] = None

class DeployRequest(BaseModel):
    description: Optional[str] = ""

class KnowledgeQueryRequest(BaseModel):
    query: str

class HandoffRequest(BaseModel):
    from_ai: str
    to_ai: str
    urgency: Optional[str] = "normal"
    context_notes: Optional[str] = ""

# Initialize collaboration system on startup
async def get_collaboration_system():
    """Dependency to get collaboration system instance"""
    if not hasattr(collaboration_system, 'database'):
        await initialize_ai_collaboration()
    return collaboration_system

@ai_collaboration_router.get("/status")
async def get_system_status(
    system: Any = Depends(get_collaboration_system)
):
    """Get comprehensive AI collaboration system status"""
    try:
        status = await system.get_system_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/session/start")
async def start_ai_session(
    request: StartSessionRequest,
    system: Any = Depends(get_collaboration_system)
):
    """Start a new AI collaboration session"""
    try:
        ai_model = AIModel(request.ai_model.lower())
        session_id, session_data = await system.start_ai_session(
            ai_model, request.context_notes
        )
        
        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "session_data": session_data
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error starting AI session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/session/end")
async def end_ai_session(
    request: EndSessionRequest,
    system: Any = Depends(get_collaboration_system)
):
    """End an AI collaboration session"""
    try:
        next_ai = AIModel(request.next_ai.lower()) if request.next_ai else None
        session_summary = await system.end_ai_session(
            request.session_id, request.handoff_notes, next_ai
        )
        
        if "error" in session_summary:
            raise HTTPException(status_code=404, detail=session_summary["error"])
        
        return JSONResponse(content={
            "success": True,
            "session_summary": session_summary
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error ending AI session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/task/create")
async def create_collaboration_task(
    request: CreateTaskRequest,
    ai_model: str,  # Current AI making the request
    system: Any = Depends(get_collaboration_system)
):
    """Create a new collaboration task"""
    try:
        assigned_ai = AIModel(request.assigned_ai.lower())
        created_by = AIModel(ai_model.lower())
        priority = Priority(request.priority.lower())
        
        task_id = await system.create_task(
            title=request.title,
            description=request.description,
            assigned_ai=assigned_ai,
            priority=priority,
            created_by=created_by,
            estimated_effort=request.estimated_effort,
            due_date=request.due_date
        )
        
        return JSONResponse(content={
            "success": True,
            "task_id": task_id,
            "message": f"Task assigned to {assigned_ai.value}"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {e}")
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/task/complete")
async def complete_collaboration_task(
    request: CompleteTaskRequest,
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Mark a task as completed"""
    try:
        ai = AIModel(ai_model.lower())
        await system.complete_task(
            task_id=request.task_id,
            ai_model=ai,
            completion_notes=request.completion_notes,
            artifacts=request.artifacts
        )
        
        return JSONResponse(content={
            "success": True,
            "message": f"Task {request.task_id} completed by {ai.value}"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.put("/task/update")
async def update_task_status(
    request: UpdateTaskRequest,
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Update task status and progress"""
    try:
        ai = AIModel(ai_model.lower())
        status = TaskStatus(request.status.lower())
        
        await system.workflow_manager.update_task_status(
            task_id=request.task_id,
            new_status=status,
            ai_model=ai,
            notes=request.notes,
            actual_effort=request.actual_effort
        )
        
        return JSONResponse(content={
            "success": True,
            "message": f"Task {request.task_id} updated to {status.value}"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {e}")
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.get("/tasks/{ai_model}")
async def get_ai_tasks(
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Get active tasks for specific AI model"""
    try:
        ai = AIModel(ai_model.lower())
        tasks = system.database.get_active_tasks_for_ai(ai)
        
        # Convert tasks to dict format
        task_data = []
        for task in tasks:
            task_dict = {
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority.value,
                "created_by": task.created_by.value,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "estimated_effort": task.estimated_effort,
                "actual_effort": task.actual_effort,
                "dependencies": task.dependencies,
                "completion_criteria": task.completion_criteria,
                "notes": task.notes,
                "artifacts": task.artifacts
            }
            task_data.append(task_dict)
        
        return JSONResponse(content={
            "success": True,
            "ai_model": ai.value,
            "task_count": len(task_data),
            "tasks": task_data
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.get("/tasks/{ai_model}/recommendations")
async def get_task_recommendations(
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Get intelligent task recommendations for AI model"""
    try:
        ai = AIModel(ai_model.lower())
        recommendations = await system.workflow_manager.get_task_recommendations(ai)
        
        return JSONResponse(content={
            "success": True,
            "ai_model": ai.value,
            "recommendations": recommendations
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/handoff/initiate")
async def initiate_ai_handoff(
    request: HandoffRequest,
    system: Any = Depends(get_collaboration_system)
):
    """Initiate handoff between AI models"""
    try:
        from_ai = AIModel(request.from_ai.lower())
        to_ai = AIModel(request.to_ai.lower())
        
        handoff_id = await system.handoff_manager.initiate_handoff(
            from_ai, to_ai, request.urgency, request.context_notes
        )
        
        return JSONResponse(content={
            "success": True,
            "handoff_id": handoff_id,
            "message": f"Handoff initiated from {from_ai.value} to {to_ai.value}"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error initiating handoff: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/handoff/{handoff_id}/receive")
async def receive_ai_handoff(
    handoff_id: str,
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Receive and process AI handoff"""
    try:
        receiving_ai = AIModel(ai_model.lower())
        handoff_data = await system.handoff_manager.receive_handoff(handoff_id, receiving_ai)
        
        if "error" in handoff_data:
            raise HTTPException(status_code=404, detail=handoff_data["error"])
        
        return JSONResponse(content={
            "success": True,
            "handoff_data": handoff_data
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error receiving handoff: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/deploy/safety-check")
async def deployment_safety_check(
    request: DeployRequest,
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Run deployment safety checks with backup creation"""
    try:
        ai = AIModel(ai_model.lower())
        deployment_result = await system.deploy_with_safety(ai, request.description)
        
        return JSONResponse(content={
            "success": True,
            "deployment_result": deployment_result
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error in deployment safety check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/deploy/rollback/{backup_id}")
async def rollback_deployment(
    backup_id: str,
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Rollback deployment to previous backup"""
    try:
        ai = AIModel(ai_model.lower())
        success = await system.deployment_safety.rollback_deployment(backup_id)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"Deployment rolled back to {backup_id} by {ai.value}"
            })
        else:
            raise HTTPException(status_code=404, detail="Backup not found or rollback failed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error in rollback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/knowledge/query")
async def query_knowledge_base(
    request: KnowledgeQueryRequest,
    ai_model: str,
    system: Any = Depends(get_collaboration_system)
):
    """Query the ChatterFix knowledge base"""
    try:
        ai = AIModel(ai_model.lower())
        results = await system.query_knowledge(request.query, ai)
        
        return JSONResponse(content={
            "success": True,
            "query": request.query,
            "ai_model": ai.value,
            "result_count": len(results),
            "results": results
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid AI model: {e}")
    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.get("/context/current")
async def get_current_context(
    system: Any = Depends(get_collaboration_system)
):
    """Get current project context"""
    try:
        context = await system.context_manager.capture_current_context()
        
        return JSONResponse(content={
            "success": True,
            "context": {
                "context_id": context.context_id,
                "timestamp": context.timestamp.isoformat(),
                "system_state": context.system_state,
                "active_features": context.active_features,
                "known_issues": context.known_issues,
                "recent_changes": context.recent_changes,
                "deployment_status": context.deployment_status,
                "test_results": context.test_results,
                "technical_debt": context.technical_debt
            }
        })
    except Exception as e:
        logger.error(f"Error getting current context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.get("/context/history")
async def get_context_history(
    limit: int = 10,
    system: Any = Depends(get_collaboration_system)
):
    """Get context history"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(system.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT context_id, timestamp, deployment_status, system_state 
            FROM project_context 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "context_id": row[0],
                "timestamp": row[1],
                "deployment_status": row[2],
                "system_state_summary": "Available" if row[3] else "No data"
            })
        
        return JSONResponse(content={
            "success": True,
            "history_count": len(history),
            "history": history
        })
    except Exception as e:
        logger.error(f"Error getting context history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.post("/context/auto-save")
async def trigger_context_auto_save(
    background_tasks: BackgroundTasks,
    system: Any = Depends(get_collaboration_system)
):
    """Trigger automatic context saving"""
    try:
        background_tasks.add_task(system.context_manager.auto_save_context)
        
        return JSONResponse(content={
            "success": True,
            "message": "Context auto-save triggered"
        })
    except Exception as e:
        logger.error(f"Error triggering context auto-save: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ai_collaboration_router.get("/ai-models")
async def get_available_ai_models():
    """Get list of available AI models and their roles"""
    models = [
        {
            "model": "claude",
            "role": "Architecture & Code Quality",
            "description": "Focuses on system design, code quality, and technical architecture"
        },
        {
            "model": "chatgpt",
            "role": "Frontend & User Experience",
            "description": "Specializes in frontend development and user interface improvements"
        },
        {
            "model": "grok",
            "role": "Debugging & Performance",
            "description": "Handles debugging, performance optimization, and troubleshooting"
        },
        {
            "model": "llama",
            "role": "Data & Analytics",
            "description": "Manages data processing, analytics, and AI/ML features"
        }
    ]
    
    return JSONResponse(content={
        "success": True,
        "available_models": models
    })

@ai_collaboration_router.get("/health")
async def health_check():
    """Health check endpoint for the AI collaboration system"""
    try:
        # Basic health check
        return JSONResponse(content={
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "AI Collaboration System is operational"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers for the router
@ai_collaboration_router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

# Export the router for inclusion in main app
__all__ = ["ai_collaboration_router"]