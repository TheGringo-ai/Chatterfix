"""
AI Team Collaboration Router for FastAPI
Integrates the gRPC AI Team service with the web interface
"""

import asyncio
import json
import logging
import os

# Import our AI team client
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from ai_team.grpc_client import get_ai_team_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-team", tags=["AI Team Collaboration"])


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
        client = get_ai_team_client()
        health_status = await client.health_check()
        return health_status
    except Exception as e:
        logger.error(f"AI team health check failed: {e}")
        return {"healthy": False, "error": str(e)}


@router.get("/models")
async def get_available_models():
    """Get list of available AI models"""
    try:
        client = get_ai_team_client()
        models = await client.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to get AI models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=AITaskResponse)
async def execute_ai_task(request: AITaskRequest):
    """Execute a collaborative task with the AI team"""
    try:
        client = get_ai_team_client()

        result = await client.execute_task(
            prompt=request.prompt,
            context=request.context or "",
            required_models=request.required_models,
            task_type=request.task_type,
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
            client = get_ai_team_client()

            async for update in client.stream_collaboration(
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


@router.get("/dashboard")
async def ai_team_dashboard():
    """AI team collaboration dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Team Collaboration Dashboard</title>
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
            <p class="lead">Multi-Model AI Team with Autogen Framework</p>
            
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
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                loadTeamStatus();
                loadAvailableModels();
            });
        </script>
    </body>
    </html>
    """


# Background task to start gRPC server
async def start_grpc_server():
    """Start the gRPC AI team server in background"""
    try:
        # Import and start the gRPC server
        from ai_team.grpc_server import serve

        await serve(port=50051)
    except Exception as e:
        logger.error(f"Failed to start gRPC server: {e}")


@router.on_event("startup")
async def startup_event():
    """Start gRPC server when FastAPI starts"""
    # Start gRPC server in background
    asyncio.create_task(start_grpc_server())
    logger.info("AI Team gRPC server starting...")


@router.get("/")
async def ai_team_root():
    """Redirect to dashboard"""
    return await ai_team_dashboard()
