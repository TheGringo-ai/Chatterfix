"""
AI Team Collaboration Router for FastAPI
Integrates the gRPC AI Team service with the web interface
"""

import json
import logging

# Import our AI team client
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_user_from_cookie

# Use HTTP client instead of gRPC
from app.services.ai_team_http_client import get_ai_team_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-team", tags=["AI Team Collaboration"])
templates = Jinja2Templates(directory="app/templates")


# Request/Response models
class AITaskRequest(BaseModel):
    prompt: str
    context: Optional[str] = ""
    required_models: Optional[List[str]] = None
    task_type: Optional[str] = "COLLABORATIVE_ANALYSIS"
    max_iterations: Optional[int] = 3


class AITaskResponse(BaseModel):
    task_id: str
    success: bool
    final_result: str
    model_responses: List[Dict[str, Any]]
    collaboration_summary: str
    confidence_score: float


class StreamRequest(BaseModel):
    prompt: str
    context: Optional[str] = ""


@router.get("/health")
async def ai_team_health():
    """Check AI team service health"""
    try:
        client = await get_ai_team_client()
        health_status = await client.health_check()
        return health_status
    except Exception as e:
        logger.error(f"AI team health check failed: {e}")
        return {"healthy": False, "error": str(e)}


@router.get("/models")
async def get_available_models():
    """Get list of available AI models"""
    try:
        client = await get_ai_team_client()
        models = await client.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to get AI models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=AITaskResponse)
async def execute_ai_task(request: AITaskRequest):
    """Execute a collaborative task with the AI team"""
    try:
        client = await get_ai_team_client()

        result = await client.execute_collaborative_task(
            prompt=request.prompt,
            context=request.context or "",
            required_agents=request.required_models,
            max_iterations=request.max_iterations,
        )

        return AITaskResponse(**result)

    except Exception as e:
        logger.error(f"AI task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_ai_collaboration(request: StreamRequest):
    """Stream collaborative responses from AI team"""

    async def generate_stream():
        try:
            client = await get_ai_team_client()

            async for update in client.stream_collaborative_task(
                prompt=request.prompt, context=request.context or ""
            ):
                # Format as Server-Sent Events
                yield f"data: {json.dumps(update)}\n\n"

        except Exception as e:
            logger.error(f"AI streaming failed: {e}")
            error_update = {"type": "error", "message": f"Streaming error: {str(e)}"}
            yield f"data: {json.dumps(error_update)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@router.get("/analytics")
async def ai_team_analytics():
    """Get comprehensive AI team analytics"""
    try:
        client = await get_ai_team_client()
        analytics = await client.get_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Failed to get AI team analytics: {e}")
        return {"error": str(e)}


@router.get("/memory/search")
async def search_knowledge(q: str, content_types: str = None, limit: int = 20):
    """Search the AI team knowledge base"""
    try:
        client = await get_ai_team_client()

        # Parse content types if provided
        content_type_list = None
        if content_types:
            content_type_list = [t.strip() for t in content_types.split(",")]

        results = await client.search_memory(query=q, max_results=limit)

        return results
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        return {"error": str(e)}


@router.post("/memory/index/rebuild")
async def rebuild_knowledge_index():
    """Rebuild the searchable knowledge index"""
    try:
        client = await get_ai_team_client()
        result = await client.rebuild_index(force_rebuild=True)
        return result
    except Exception as e:
        logger.error(f"Failed to rebuild knowledge index: {e}")
        return {"error": str(e)}


@router.get("/dashboard", response_class=HTMLResponse)
async def ai_team_dashboard(request: Request):
    """Enhanced AI team collaboration dashboard with memory system"""
    # LESSON #22: Always get user from cookie for HTML pages
    current_user = await get_current_user_from_cookie(request)
    return templates.TemplateResponse(
        "ai_team_dashboard.html",
        {
            "request": request,
            "user": current_user,
            "current_user": current_user,
            "is_demo": current_user is None,
        },
    )


# Keep old inline HTML as backup reference (commented out)
def _old_ai_team_dashboard_inline():
    """Old inline HTML dashboard - replaced with template"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Team Collaboration Dashboard - OLD</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .model-card { margin: 10px 0; }
            .response-box { 
                background: #f8f9fa; 
                border-left: 4px solid #007bff; 
                padding: 15px; 
                margin: 10px 0; 
            }
            .streaming-output {
                background: #000;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                padding: 15px;
                height: 400px;
                overflow-y: auto;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>🤖 AI Team Collaboration Dashboard</h1>
            <p class="lead">Multi-Model AI Team with Advanced Memory System - Never Repeat Mistakes</p>
            
            <!-- Memory System Status -->
            <div class="row mb-4">
                <div class="col-md-12">
                    <div class="alert alert-info">
                        <h6><strong>🧠 ADVANCED MEMORY SYSTEM ACTIVE</strong></h6>
                        <p class="mb-0">Every conversation, mistake, and solution is captured and indexed. The AI team learns from every interaction to prevent repeating mistakes and improve performance over time.</p>
                    </div>
                </div>
            </div>
            
            <!-- AI Team Status -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>AI Team Status</h5>
                        </div>
                        <div class="card-body">
                            <div id="team-status">Loading...</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Available Models</h5>
                        </div>
                        <div class="card-body">
                            <div id="available-models">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Collaboration Interface -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5>AI Team Collaboration</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label for="prompt" class="form-label">Prompt for AI Team:</label>
                        <textarea class="form-control" id="prompt" rows="3" 
                                  placeholder="Enter your question or task for the AI team to collaborate on..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label for="context" class="form-label">Context (optional):</label>
                        <textarea class="form-control" id="context" rows="2" 
                                  placeholder="Additional context or background information..."></textarea>
                    </div>
                    <div class="mb-3">
                        <button class="btn btn-primary me-2" onclick="executeTask()">Execute Collaboration</button>
                        <button class="btn btn-success me-2" onclick="streamCollaboration()">Stream Live Collaboration</button>
                        <button class="btn btn-secondary" onclick="clearOutput()">Clear Output</button>
                    </div>
                </div>
            </div>
            
            <!-- Knowledge Search -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5>🔍 Knowledge Search</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label for="search-query" class="form-label">Search AI Team Knowledge Base:</label>
                        <input type="text" class="form-control" id="search-query" 
                               placeholder="Search conversations, mistakes, solutions, code changes...">
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="content-filter" class="form-label">Content Type:</label>
                            <select class="form-select" id="content-filter">
                                <option value="">All Types</option>
                                <option value="conversation">Conversations</option>
                                <option value="mistake">Mistake Patterns</option>
                                <option value="solution">Solution Patterns</option>
                                <option value="code_change">Code Changes</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label for="search-limit" class="form-label">Results Limit:</label>
                            <select class="form-select" id="search-limit">
                                <option value="10">10 Results</option>
                                <option value="20" selected>20 Results</option>
                                <option value="50">50 Results</option>
                            </select>
                        </div>
                    </div>
                    <button class="btn btn-secondary" onclick="searchKnowledge()">🔍 Search Knowledge</button>
                    <button class="btn btn-warning" onclick="rebuildIndex()">🔧 Rebuild Index</button>
                    
                    <div id="search-results" class="mt-3"></div>
                </div>
            </div>
            
            <!-- AI Team Analytics -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5>📊 AI Team Analytics</h5>
                </div>
                <div class="card-body">
                    <button class="btn btn-info" onclick="loadAnalytics()">📈 Load Comprehensive Analytics</button>
                    <div id="analytics-output" class="mt-3"></div>
                </div>
            </div>

            <!-- Results -->
            <div class="card">
                <div class="card-header">
                    <h5>AI Team Results</h5>
                </div>
                <div class="card-body">
                    <div id="results-output"></div>
                    <div id="streaming-output" class="streaming-output d-none"></div>
                </div>
            </div>
        </div>
        
        <script>
            // Load team status on page load
            async function loadTeamStatus() {
                try {
                    const response = await fetch('/ai-team/health');
                    const status = await response.json();
                    
                    document.getElementById('team-status').innerHTML = `
                        <div class="d-flex align-items-center">
                            <span class="badge ${status.healthy ? 'bg-success' : 'bg-danger'} me-2">
                                ${status.healthy ? 'Healthy' : 'Unhealthy'}
                            </span>
                            <span>${status.status || 'Unknown'}</span>
                        </div>
                        <small class="text-muted">
                            Active Models: ${status.active_models ? status.active_models.length : 0} | 
                            Pending Tasks: ${status.pending_tasks || 0}
                        </small>
                    `;
                } catch (error) {
                    document.getElementById('team-status').innerHTML = 
                        '<span class="text-danger">Failed to load status</span>';
                }
            }
            
            async function loadAvailableModels() {
                try {
                    const response = await fetch('/ai-team/models');
                    const data = await response.json();
                    
                    const modelsHtml = data.models.map(model => `
                        <div class="model-card">
                            <strong>${model.name}</strong> 
                            <span class="badge ${model.available ? 'bg-success' : 'bg-secondary'}">${model.provider}</span>
                            <br>
                            <small class="text-muted">Score: ${model.performance_score} | ${model.capabilities.join(', ')}</small>
                        </div>
                    `).join('');
                    
                    document.getElementById('available-models').innerHTML = modelsHtml || 'No models available';
                } catch (error) {
                    document.getElementById('available-models').innerHTML = 
                        '<span class="text-danger">Failed to load models</span>';
                }
            }
            
            async function executeTask() {
                const prompt = document.getElementById('prompt').value;
                const context = document.getElementById('context').value;
                
                if (!prompt.trim()) {
                    alert('Please enter a prompt');
                    return;
                }
                
                const resultsDiv = document.getElementById('results-output');
                resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div> AI Team is collaborating...</div>';
                
                try {
                    const response = await fetch('/ai-team/execute', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ prompt, context })
                    });
                    
                    const result = await response.json();
                    
                    let resultHtml = `
                        <div class="alert ${result.success ? 'alert-success' : 'alert-danger'}">
                            <h6>Task ${result.success ? 'Completed' : 'Failed'}</h6>
                            <strong>Confidence Score:</strong> ${(result.confidence_score * 100).toFixed(1)}%
                        </div>
                        
                        <div class="response-box">
                            <h6>Final Result:</h6>
                            <p>${result.final_result}</p>
                        </div>
                        
                        <div class="mt-3">
                            <h6>Individual Model Responses:</h6>
                    `;
                    
                    result.model_responses.forEach(resp => {
                        resultHtml += `
                            <div class="response-box">
                                <strong>${resp.model_name}:</strong>
                                <p>${resp.response}</p>
                                <small class="text-muted">Confidence: ${(resp.confidence * 100).toFixed(1)}%</small>
                            </div>
                        `;
                    });
                    
                    resultHtml += `
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">
                                <strong>Collaboration Summary:</strong> ${result.collaboration_summary}
                            </small>
                        </div>
                    `;
                    
                    resultsDiv.innerHTML = resultHtml;
                    
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
                }
            }
            
            async function streamCollaboration() {
                const prompt = document.getElementById('prompt').value;
                const context = document.getElementById('context').value;
                
                if (!prompt.trim()) {
                    alert('Please enter a prompt');
                    return;
                }
                
                const streamingDiv = document.getElementById('streaming-output');
                const resultsDiv = document.getElementById('results-output');
                
                resultsDiv.innerHTML = '';
                streamingDiv.classList.remove('d-none');
                streamingDiv.innerHTML = '> Starting AI Team collaboration...\\n';
                
                try {
                    const response = await fetch('/ai-team/stream', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ prompt, context })
                    });
                    
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    
                                    if (data.type === 'agent_thinking') {
                                        streamingDiv.innerHTML += `> ${data.message}\\n`;
                                    } else if (data.type === 'agent_response') {
                                        streamingDiv.innerHTML += `\\n[${data.model}] ${data.response}\\n\\n`;
                                    } else if (data.type === 'complete') {
                                        streamingDiv.innerHTML += `\\n> COLLABORATION COMPLETE\\n`;
                                        streamingDiv.innerHTML += `\\nFINAL ANSWER: ${data.final_answer}\\n`;
                                    }
                                    
                                    streamingDiv.scrollTop = streamingDiv.scrollHeight;
                                    
                                } catch (e) {
                                    // Ignore parsing errors for incomplete chunks
                                }
                            }
                        }
                    }
                    
                } catch (error) {
                    streamingDiv.innerHTML += `\\n> ERROR: ${error.message}\\n`;
                }
            }
            
            function clearOutput() {
                document.getElementById('results-output').innerHTML = '';
                document.getElementById('streaming-output').innerHTML = '';
                document.getElementById('streaming-output').classList.add('d-none');
            }
            
            // New functions for memory system
            async function searchKnowledge() {
                const query = document.getElementById('search-query').value;
                const contentType = document.getElementById('content-filter').value;
                const limit = document.getElementById('search-limit').value;
                
                if (!query.trim()) {
                    alert('Please enter a search query');
                    return;
                }
                
                const searchResults = document.getElementById('search-results');
                searchResults.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div> Searching knowledge base...</div>';
                
                try {
                    const params = new URLSearchParams({
                        q: query,
                        limit: limit
                    });
                    
                    if (contentType) {
                        params.append('content_types', contentType);
                    }
                    
                    const response = await fetch(`/ai-team/memory/search?${params}`);
                    const results = await response.json();
                    
                    if (results.error) {
                        searchResults.innerHTML = `<div class="alert alert-danger">Error: ${results.error}</div>`;
                        return;
                    }
                    
                    let resultsHtml = `
                        <h6>🔍 Search Results (${results.total_results} found)</h6>
                        <p><strong>Query:</strong> "${results.query}"</p>
                    `;
                    
                    if (results.results && results.results.length > 0) {
                        results.results.forEach(result => {
                            const typeIcon = {
                                'conversation': '💬',
                                'mistake': '❌',
                                'solution': '✅',
                                'code_change': '🔧'
                            }[result.type] || '📄';
                            
                            resultsHtml += `
                                <div class="card mt-2">
                                    <div class="card-body">
                                        <h6 class="card-title">
                                            ${typeIcon} ${result.type.replace('_', ' ').toUpperCase()} 
                                            <span class="badge bg-secondary">Relevance: ${(result.relevance * 100).toFixed(1)}%</span>
                                        </h6>
                                        <p class="card-text">${result.preview}</p>
                                        <small class="text-muted">
                                            ID: ${result.item_id} | 
                                            ${result.timestamp ? new Date(result.timestamp).toLocaleString() : 'No timestamp'}
                                        </small>
                                    </div>
                                </div>
                            `;
                        });
                    } else {
                        resultsHtml += '<p class="text-muted">No results found.</p>';
                    }
                    
                    searchResults.innerHTML = resultsHtml;
                    
                } catch (error) {
                    searchResults.innerHTML = `<div class="alert alert-danger">Search failed: ${error.message}</div>`;
                }
            }
            
            async function rebuildIndex() {
                const searchResults = document.getElementById('search-results');
                searchResults.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div> Rebuilding knowledge index...</div>';
                
                try {
                    const response = await fetch('/ai-team/memory/index/rebuild', {
                        method: 'POST'
                    });
                    const result = await response.json();
                    
                    if (result.error) {
                        searchResults.innerHTML = `<div class="alert alert-danger">Error: ${result.error}</div>`;
                        return;
                    }
                    
                    searchResults.innerHTML = `
                        <div class="alert alert-success">
                            <h6>✅ Index Rebuild Complete</h6>
                            <p>${result.message}</p>
                            <small class="text-muted">
                                Status: ${result.status} | 
                                Metadata: ${JSON.stringify(result.metadata, null, 2)}
                            </small>
                        </div>
                    `;
                    
                } catch (error) {
                    searchResults.innerHTML = `<div class="alert alert-danger">Index rebuild failed: ${error.message}</div>`;
                }
            }
            
            async function loadAnalytics() {
                const analyticsOutput = document.getElementById('analytics-output');
                analyticsOutput.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div> Loading comprehensive analytics...</div>';
                
                try {
                    const response = await fetch('/ai-team/analytics');
                    const analytics = await response.json();
                    
                    if (analytics.error) {
                        analyticsOutput.innerHTML = `<div class="alert alert-danger">Error: ${analytics.error}</div>`;
                        return;
                    }
                    
                    let analyticsHtml = `
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-primary text-white">
                                        <h6>📊 Learning Metrics</h6>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>Total Conversations:</strong> ${analytics.learning_metrics?.total_conversations_captured || 0}</p>
                                        <p><strong>Mistakes Identified:</strong> ${analytics.learning_metrics?.total_mistakes_identified || 0}</p>
                                        <p><strong>Solutions Captured:</strong> ${analytics.learning_metrics?.total_solutions_captured || 0}</p>
                                        <p><strong>Mistake Prevention Rate:</strong> ${((analytics.learning_metrics?.mistake_prevention_rate || 0) * 100).toFixed(1)}%</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-success text-white">
                                        <h6>🏆 AI Team Health</h6>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>Overall Health Score:</strong> ${((analytics.overall_health_score || 0) * 100).toFixed(1)}%</p>
                                        <p><strong>Learning Enabled:</strong> ${analytics.learning_enabled ? 'Yes' : 'No'}</p>
                                        <p><strong>Conversations This Week:</strong> ${analytics.recent_activity?.conversations_this_week || 0}</p>
                                        <p><strong>Avg Confidence:</strong> ${((analytics.recent_activity?.average_confidence_this_week || 0) * 20).toFixed(1)}%</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // Agent Performance
                    if (analytics.agent_analytics && Object.keys(analytics.agent_analytics).length > 0) {
                        analyticsHtml += `
                            <div class="card mt-3">
                                <div class="card-header bg-info text-white">
                                    <h6>🤖 Agent Performance</h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                        `;
                        
                        Object.entries(analytics.agent_analytics).forEach(([agent, perf]) => {
                            analyticsHtml += `
                                <div class="col-md-4 mb-3">
                                    <div class="card">
                                        <div class="card-body">
                                            <h6 class="card-title">${agent}</h6>
                                            <p class="card-text">
                                                <strong>Success Rate:</strong> ${(perf.success_rate * 100).toFixed(1)}%<br>
                                                <strong>Total Tasks:</strong> ${perf.total_tasks}<br>
                                                <strong>Avg Confidence:</strong> ${(perf.average_confidence * 100).toFixed(1)}%<br>
                                                <strong>Efficiency:</strong> ${(perf.efficiency_score * 100).toFixed(1)}%
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        
                        analyticsHtml += `
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Recommendations
                    if (analytics.ai_team_recommendations && analytics.ai_team_recommendations.length > 0) {
                        analyticsHtml += `
                            <div class="card mt-3">
                                <div class="card-header bg-warning text-dark">
                                    <h6>💡 AI Team Recommendations</h6>
                                </div>
                                <div class="card-body">
                                    <ul>
                        `;
                        
                        analytics.ai_team_recommendations.forEach(rec => {
                            analyticsHtml += `<li>${rec}</li>`;
                        });
                        
                        analyticsHtml += `
                                    </ul>
                                </div>
                            </div>
                        `;
                    }
                    
                    analyticsOutput.innerHTML = analyticsHtml;
                    
                } catch (error) {
                    analyticsOutput.innerHTML = `<div class="alert alert-danger">Analytics loading failed: ${error.message}</div>`;
                }
            }
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                loadTeamStatus();
                loadAvailableModels();
            });
        </script>
    </body>
    </html>
    """


# Background initialization for HTTP client
@router.on_event("startup")
async def startup_event():
    """Initialize AI Team HTTP client"""
    try:
        client = await get_ai_team_client()
        # Test connectivity
        health = await client.health_check()
        if health.get("status") == "healthy" or health.get("healthy", False):
            logger.info("✅ AI Team HTTP client connected successfully")
        else:
            logger.warning(
                f"⚠️ AI Team service not available: {health.get('status', 'unknown')}"
            )
    except Exception as e:
        logger.error(f"Failed to initialize AI Team HTTP client: {e}")


@router.get("/")
async def ai_team_root():
    """Redirect to dashboard"""
    return await ai_team_dashboard()
