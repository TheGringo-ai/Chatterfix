"""
AI Team API Endpoints
Provides access to AI Team Intelligence features:
- Real-time context sharing (/ai/context)
- Voice command queries (/ai/voice)
- Consensus requests (/ai/consensus)
- Proactive monitoring (/ai/health)
- Learning pipeline status (/ai/learning)

Part of the Ultimate AI Development Platform from CLAUDE.md
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.ai_team_intelligence import get_ai_team_intelligence
from app.services.ai_memory_integration import get_ai_memory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Team"])


# =========================================================================
# REQUEST/RESPONSE MODELS
# =========================================================================

class ContextRequest(BaseModel):
    """Request model for context queries"""
    topic: str = Field(..., min_length=1, max_length=500)
    include_solutions: bool = True
    include_mistakes: bool = True
    include_recent_changes: bool = True
    limit: int = Field(default=10, ge=1, le=50)


class VoiceQueryRequest(BaseModel):
    """Request model for voice/natural language queries"""
    query: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = ""


class ConsensusRequest(BaseModel):
    """Request model for AI team consensus"""
    topic: str = Field(..., min_length=1, max_length=500)
    context: str = Field(default="", max_length=2000)
    models: Optional[List[str]] = None


class CodeReviewRequest(BaseModel):
    """Request model for code review"""
    code: str = Field(..., min_length=1, max_length=50000)
    file_path: Optional[str] = ""
    language: Optional[str] = "python"


class LearningReportRequest(BaseModel):
    """Request model for learning from errors"""
    error_type: str
    error_message: str
    context: Dict[str, Any] = {}
    stack_trace: Optional[str] = ""
    resolution: Optional[str] = ""


# =========================================================================
# CONTEXT SHARING API
# =========================================================================

@router.get("/context")
async def get_context(
    topic: str = Query(..., min_length=1, description="Topic to get context for"),
    include_solutions: bool = Query(True, description="Include solution patterns"),
    include_mistakes: bool = Query(True, description="Include mistake patterns"),
    include_changes: bool = Query(True, description="Include recent code changes"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results per category"),
):
    """
    Get real-time context for any topic.

    This is the central knowledge API for all AI models to share context.
    Returns solutions, mistakes, and recent changes related to the topic.

    Example:
        GET /ai/context?topic=firebase&include_solutions=true
    """
    try:
        intelligence = get_ai_team_intelligence()

        context = await intelligence.get_context(
            topic=topic,
            include_solutions=include_solutions,
            include_mistakes=include_mistakes,
            include_recent_changes=include_changes,
            limit=limit,
        )

        return JSONResponse({
            "status": "success",
            "data": context,
        })

    except Exception as e:
        logger.error(f"Context API error: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500,
        )


@router.post("/context")
async def query_context(request: ContextRequest):
    """
    Query context with full options (POST method).

    Use this when you need more control over the query parameters.
    """
    try:
        intelligence = get_ai_team_intelligence()

        context = await intelligence.get_context(
            topic=request.topic,
            include_solutions=request.include_solutions,
            include_mistakes=request.include_mistakes,
            include_recent_changes=request.include_recent_changes,
            limit=request.limit,
        )

        return JSONResponse({
            "status": "success",
            "data": context,
        })

    except Exception as e:
        logger.error(f"Context API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# VOICE/NATURAL LANGUAGE QUERIES
# =========================================================================

@router.post("/voice")
async def voice_query(request: VoiceQueryRequest):
    """
    Process natural language queries about the AI team's knowledge.

    Supports queries like:
    - "What mistakes have we made with authentication?"
    - "Show me solutions for Firebase issues"
    - "What's the team consensus on using Redux?"
    - "What's the system health status?"

    This endpoint powers voice-activated AI team interactions.
    """
    try:
        intelligence = get_ai_team_intelligence()

        result = await intelligence.process_voice_query(request.query)

        return JSONResponse({
            "status": "success",
            "query": request.query,
            "data": result,
        })

    except Exception as e:
        logger.error(f"Voice query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ask")
async def ask_ai_team(
    q: str = Query(..., min_length=1, description="Your question for the AI team"),
):
    """
    Simple GET endpoint for asking the AI team questions.

    Example:
        GET /ai/ask?q=What+mistakes+have+we+made+with+Firebase
    """
    try:
        intelligence = get_ai_team_intelligence()
        result = await intelligence.process_voice_query(q)

        return JSONResponse({
            "status": "success",
            "question": q,
            "answer": result.get("response", ""),
            "details": result,
        })

    except Exception as e:
        logger.error(f"Ask AI error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# CONSENSUS SYSTEM
# =========================================================================

@router.post("/consensus")
async def get_consensus(request: ConsensusRequest):
    """
    Get AI team consensus on a topic.

    Queries multiple AI model perspectives and analyzes agreement.
    Used for major architectural decisions or complex problem-solving.

    Available models: claude, gemini, grok, chatgpt
    """
    try:
        intelligence = get_ai_team_intelligence()

        consensus = await intelligence.get_consensus(
            topic=request.topic,
            context=request.context,
            models=request.models,
        )

        return JSONResponse({
            "status": "success",
            "data": consensus,
        })

    except Exception as e:
        logger.error(f"Consensus API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# PROACTIVE MONITORING
# =========================================================================

@router.get("/health")
async def get_ai_health():
    """
    Get AI team health status and predictions.

    Returns:
    - Memory stats (conversations, mistakes, solutions)
    - Recent error trends
    - Issue predictions
    - Overall health score
    """
    try:
        intelligence = get_ai_team_intelligence()
        memory = get_ai_memory_service()

        stats = await memory.get_memory_stats()
        predictions = await intelligence.predict_issues(recent_hours=24)

        return JSONResponse({
            "status": "success",
            "data": {
                "memory_stats": stats,
                "predictions": predictions,
                "health_score": predictions.get("health_score", 100),
            },
        })

    except Exception as e:
        logger.error(f"Health API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review")
async def review_code(request: CodeReviewRequest):
    """
    Proactively review code for potential issues.

    Analyzes code against known mistake patterns and suggests improvements.
    Used by pre-commit hooks and CI/CD pipelines.
    """
    try:
        intelligence = get_ai_team_intelligence()

        result = await intelligence.analyze_for_issues(
            code_content=request.code,
            file_path=request.file_path or "",
        )

        return JSONResponse({
            "status": "success",
            "data": result,
        })

    except Exception as e:
        logger.error(f"Review API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# LEARNING PIPELINE
# =========================================================================

@router.post("/learn")
async def report_learning(request: LearningReportRequest):
    """
    Report an error or issue to the learning pipeline.

    The AI team will:
    1. Check if this is a known issue
    2. Generate prevention strategies
    3. Add to knowledge base for future prevention
    """
    try:
        intelligence = get_ai_team_intelligence()

        # Create an exception-like object for the learning pipeline
        class ReportedError(Exception):
            pass

        error = ReportedError(request.error_message)
        error.__class__.__name__ = request.error_type

        result = await intelligence.learn_from_error(
            error=error,
            context={
                **request.context,
                "stack_trace": request.stack_trace,
                "reported_resolution": request.resolution,
            },
        )

        return JSONResponse({
            "status": "success",
            "data": result,
        })

    except Exception as e:
        logger.error(f"Learning API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_learning_stats():
    """
    Get statistics about the AI team's learning.

    Returns counts of:
    - Total AI conversations captured
    - Mistake patterns identified
    - Solutions in knowledge base
    - Code changes tracked
    """
    try:
        memory = get_ai_memory_service()
        stats = await memory.get_memory_stats()

        return JSONResponse({
            "status": "success",
            "data": stats,
        })

    except Exception as e:
        logger.error(f"Stats API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# KNOWLEDGE BASE ACCESS
# =========================================================================

@router.get("/mistakes")
async def get_mistakes(
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search term"),
):
    """
    Get mistake patterns from the knowledge base.

    Used to review what issues have been encountered and their solutions.
    """
    try:
        memory = get_ai_memory_service()

        if search:
            mistakes = await memory.find_similar_mistakes(search)
        else:
            mistakes = await memory.firestore.get_collection(
                "mistake_patterns", limit=limit, order_by="-timestamp"
            )

        return JSONResponse({
            "status": "success",
            "count": len(mistakes),
            "data": mistakes,
        })

    except Exception as e:
        logger.error(f"Mistakes API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/solutions")
async def get_solutions(
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search term"),
):
    """
    Get solutions from the knowledge base.

    Used to find proven solutions to common problems.
    """
    try:
        memory = get_ai_memory_service()

        if search:
            solutions = await memory.find_solutions(search)
        else:
            solutions = await memory.firestore.get_collection(
                "solution_knowledge_base", limit=limit, order_by="-timestamp"
            )

        return JSONResponse({
            "status": "success",
            "count": len(solutions),
            "data": solutions,
        })

    except Exception as e:
        logger.error(f"Solutions API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# CODE CHANGE TRACKING
# =========================================================================

class CodeChangeRequest(BaseModel):
    """Request model for recording code changes"""
    files_modified: List[str] = Field(..., min_length=1)
    change_description: str = Field(..., min_length=1, max_length=2000)
    change_type: str = Field(default="update", description="Type: create, update, delete, refactor")
    session_id: Optional[str] = None
    ai_reasoning: Optional[str] = ""
    related_task: Optional[str] = ""


class SessionActivityRequest(BaseModel):
    """Request model for recording session activity"""
    session_id: str = Field(..., min_length=1)
    activity_type: str = Field(..., description="Type: start, task, error, solution, end")
    description: str = Field(..., min_length=1, max_length=2000)
    metadata: Dict[str, Any] = {}


@router.post("/changes")
async def record_code_change(request: CodeChangeRequest):
    """
    Record a code change from a development session.

    Tracks all code modifications with context for pattern learning.
    Used for:
    - Understanding change patterns
    - Tracking AI-assisted modifications
    - Building knowledge of codebase evolution
    """
    try:
        from datetime import datetime, timezone
        memory = get_ai_memory_service()

        change_data = {
            "files_modified": request.files_modified,
            "change_description": request.change_description,
            "change_type": request.change_type,
            "session_id": request.session_id,
            "ai_reasoning": request.ai_reasoning,
            "related_task": request.related_task,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Store in Firestore
        doc_id = await memory.firestore.create_document("code_changes", change_data)

        return JSONResponse({
            "status": "success",
            "message": "Code change recorded",
            "change_id": doc_id,
        })

    except Exception as e:
        logger.error(f"Code change recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/changes")
async def get_code_changes(
    limit: int = Query(20, ge=1, le=100),
    session_id: Optional[str] = Query(None, description="Filter by session"),
    file_path: Optional[str] = Query(None, description="Filter by file path"),
):
    """
    Get recorded code changes from development sessions.

    Used to review change history and understand modification patterns.
    """
    try:
        memory = get_ai_memory_service()

        changes = await memory.firestore.get_collection(
            "code_changes", limit=limit, order_by="-timestamp"
        )

        # Apply filters
        if session_id:
            changes = [c for c in changes if c.get("session_id") == session_id]
        if file_path:
            changes = [c for c in changes if file_path in c.get("files_modified", [])]

        return JSONResponse({
            "status": "success",
            "count": len(changes),
            "data": changes,
        })

    except Exception as e:
        logger.error(f"Code changes API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session")
async def record_session_activity(request: SessionActivityRequest):
    """
    Record session activity for development tracking.

    Captures:
    - Session start/end times
    - Tasks worked on
    - Errors encountered
    - Solutions applied
    """
    try:
        from datetime import datetime, timezone
        memory = get_ai_memory_service()

        activity_data = {
            "session_id": request.session_id,
            "activity_type": request.activity_type,
            "description": request.description,
            "metadata": request.metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await memory.firestore.create_document("session_activities", activity_data)

        return JSONResponse({
            "status": "success",
            "message": f"Session activity '{request.activity_type}' recorded",
        })

    except Exception as e:
        logger.error(f"Session activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# AUTO-CONTEXT QUERY HOOK
# =========================================================================

@router.post("/auto-context")
async def auto_context_hook(request: Request):
    """
    Auto-context query hook for development sessions.

    Called before major operations to automatically provide relevant context.
    Checks:
    - Similar past mistakes for the current task
    - Relevant solutions from knowledge base
    - Recent changes to related files
    - Known issues with dependencies

    This powers the "never repeat mistakes" system.
    """
    try:
        body = await request.json()
        task_description = body.get("task", "")
        files_involved = body.get("files", [])
        operation_type = body.get("operation", "unknown")

        intelligence = get_ai_team_intelligence()
        memory = get_ai_memory_service()

        # Gather relevant context automatically
        context_data = {
            "similar_mistakes": [],
            "relevant_solutions": [],
            "related_changes": [],
            "warnings": [],
            "recommendations": [],
        }

        # Check for similar past mistakes
        if task_description:
            similar_mistakes = await memory.find_similar_mistakes(task_description)
            if similar_mistakes:
                context_data["similar_mistakes"] = similar_mistakes[:5]
                context_data["warnings"].append(
                    f"Found {len(similar_mistakes)} similar past issues. Review before proceeding."
                )

        # Find relevant solutions
        if task_description:
            solutions = await memory.find_solutions(task_description)
            if solutions:
                context_data["relevant_solutions"] = solutions[:5]

        # Check for recent changes to involved files
        if files_involved:
            recent_changes = await memory.firestore.get_collection(
                "code_changes", limit=20, order_by="-timestamp"
            )
            for change in recent_changes:
                if any(f in change.get("files_modified", []) for f in files_involved):
                    context_data["related_changes"].append(change)
                    if len(context_data["related_changes"]) >= 5:
                        break

        # Generate recommendations based on operation type
        if operation_type == "deploy":
            context_data["recommendations"].append(
                "Run full test suite before deploying"
            )
            context_data["recommendations"].append(
                "Verify all datetime objects use .strftime() for JSON"
            )
        elif operation_type == "auth":
            context_data["recommendations"].append(
                "Ensure cookies are set on the RETURNED response object"
            )
            context_data["recommendations"].append(
                "Use credentials: 'include' in fetch calls"
            )
        elif operation_type == "firebase":
            context_data["recommendations"].append(
                "Check all Firebase config fields are present"
            )
            context_data["recommendations"].append(
                "Verify Admin SDK credentials for server-side operations"
            )

        return JSONResponse({
            "status": "success",
            "context": context_data,
            "has_warnings": len(context_data["warnings"]) > 0,
            "warning_count": len(context_data["warnings"]),
        })

    except Exception as e:
        logger.error(f"Auto-context hook error: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e),
            "context": {},
        }, status_code=500)


# =========================================================================
# ERROR CATEGORIZATION
# =========================================================================

class ErrorCategorizationRequest(BaseModel):
    """Request model for error categorization"""
    error_message: str = Field(..., min_length=1)
    stack_trace: Optional[str] = ""
    file_path: Optional[str] = ""
    context: Dict[str, Any] = {}


@router.post("/categorize-error")
async def categorize_error(request: ErrorCategorizationRequest):
    """
    Categorize an error using AI Team intelligence.

    Analyzes error patterns and returns:
    - Error category (auth, database, serialization, network, etc.)
    - Severity level (low, medium, high, critical)
    - Known pattern matches
    - Suggested resolutions
    """
    try:
        intelligence = get_ai_team_intelligence()
        memory = get_ai_memory_service()

        # Determine category from error message
        error_msg_lower = request.error_message.lower()

        categories = {
            "auth": ["auth", "token", "session", "login", "permission", "unauthorized", "forbidden"],
            "database": ["firestore", "firebase", "database", "query", "document", "collection"],
            "serialization": ["json", "serialize", "datetime", "encode", "decode", "format"],
            "network": ["network", "connection", "timeout", "fetch", "request", "http", "api"],
            "validation": ["validation", "invalid", "required", "type error", "schema"],
            "file": ["file", "path", "read", "write", "permission", "not found"],
        }

        detected_category = "unknown"
        for category, keywords in categories.items():
            if any(kw in error_msg_lower for kw in keywords):
                detected_category = category
                break

        # Determine severity
        severity = "medium"
        if any(kw in error_msg_lower for kw in ["critical", "crash", "fatal", "emergency"]):
            severity = "critical"
        elif any(kw in error_msg_lower for kw in ["warning", "deprecated"]):
            severity = "low"
        elif any(kw in error_msg_lower for kw in ["error", "failed", "exception"]):
            severity = "high"

        # Find similar known issues
        similar = await memory.find_similar_mistakes(request.error_message)

        # Generate suggestions based on category
        suggestions = []
        if detected_category == "auth":
            suggestions = [
                "Check if cookies are set on the returned response object",
                "Verify credentials: 'include' is used in fetch calls",
                "Ensure session tokens are properly validated"
            ]
        elif detected_category == "serialization":
            suggestions = [
                "Use .strftime('%Y-%m-%d %H:%M') for datetime in JSON",
                "Check for non-serializable objects in response",
                "Verify model schema matches data structure"
            ]
        elif detected_category == "database":
            suggestions = [
                "Verify Firestore connection is properly initialized",
                "Check document/collection paths are correct",
                "Ensure organization_id is included for multi-tenant queries"
            ]

        result = {
            "category": detected_category,
            "severity": severity,
            "known_matches": len(similar),
            "similar_issues": similar[:3] if similar else [],
            "suggestions": suggestions,
        }

        return JSONResponse({
            "status": "success",
            "data": result,
        })

    except Exception as e:
        logger.error(f"Error categorization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
