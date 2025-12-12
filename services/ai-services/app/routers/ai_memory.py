"""
🧠 AI Memory Router
Endpoints for accessing and managing AI memory system
Designed with AI Team collaboration to prevent repeat mistakes
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.ai_memory_system import AIMemorySystem, get_ai_memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-memory", tags=["AI Memory"])


# Request/Response models
class IntegrationErrorRequest(BaseModel):
    source_service: str
    target_service: str
    error_type: str
    error_description: str
    original_request: Dict[str, Any]
    expected_format: Optional[Dict[str, Any]] = None
    solution_applied: Optional[str] = ""
    resolution_time_minutes: Optional[float] = 0


class APIContractRequest(BaseModel):
    service_name: str
    endpoint: str
    expected_parameters: Dict[str, Any]
    response_format: Dict[str, Any]
    parameter_mappings: Optional[Dict[str, str]] = None


class SuccessPatternRequest(BaseModel):
    pattern_type: str
    source_service: str
    target_service: str
    pattern_description: str
    implementation_code: str


class IntegrationCheckRequest(BaseModel):
    source_service: str
    target_service: str
    request_data: Dict[str, Any]


@router.get("/health")
async def memory_health():
    """Check AI memory system health"""
    try:
        memory = await get_ai_memory()
        stats = memory.get_memory_stats()

        return {
            "healthy": True,
            "service": "ai_memory",
            "stats": stats,
            "features": [
                "api_contract_memory",
                "integration_error_tracking",
                "success_pattern_storage",
                "proactive_issue_detection",
            ],
        }
    except Exception as e:
        logger.error(f"Memory health check failed: {e}")
        return {"healthy": False, "error": str(e)}


@router.post("/record-error")
async def record_integration_error(
    request: IntegrationErrorRequest, memory: AIMemorySystem = Depends(get_ai_memory)
):
    """Record a new integration error and solution"""
    try:
        error_id = await memory.record_integration_error(
            source_service=request.source_service,
            target_service=request.target_service,
            error_type=request.error_type,
            error_description=request.error_description,
            original_request=request.original_request,
            expected_format=request.expected_format,
            solution_applied=request.solution_applied,
            resolution_time_minutes=request.resolution_time_minutes,
        )

        return {
            "success": True,
            "error_id": error_id,
            "message": "Integration error recorded in AI memory",
            "memory_updated": True,
        }

    except Exception as e:
        logger.error(f"Failed to record error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-api-contract")
async def record_api_contract(
    request: APIContractRequest, memory: AIMemorySystem = Depends(get_ai_memory)
):
    """Record API contract information"""
    try:
        contract_id = await memory.record_api_contract(
            service_name=request.service_name,
            endpoint=request.endpoint,
            expected_parameters=request.expected_parameters,
            response_format=request.response_format,
            parameter_mappings=request.parameter_mappings,
        )

        return {
            "success": True,
            "contract_id": contract_id,
            "message": "API contract recorded in AI memory",
            "memory_updated": True,
        }

    except Exception as e:
        logger.error(f"Failed to record API contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-success-pattern")
async def record_success_pattern(
    request: SuccessPatternRequest, memory: AIMemorySystem = Depends(get_ai_memory)
):
    """Record a successful integration pattern"""
    try:
        pattern_id = await memory.record_success_pattern(
            pattern_type=request.pattern_type,
            source_service=request.source_service,
            target_service=request.target_service,
            pattern_description=request.pattern_description,
            implementation_code=request.implementation_code,
        )

        return {
            "success": True,
            "pattern_id": pattern_id,
            "message": "Success pattern recorded in AI memory",
            "memory_updated": True,
        }

    except Exception as e:
        logger.error(f"Failed to record success pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-integration")
async def check_integration_issues(
    request: IntegrationCheckRequest, memory: AIMemorySystem = Depends(get_ai_memory)
):
    """Check for potential integration issues before making API calls"""
    try:
        issue_check = await memory.check_for_known_issues(
            source_service=request.source_service,
            target_service=request.target_service,
            request_data=request.request_data,
        )

        if issue_check:
            return {
                "issues_detected": True,
                "prevention_successful": True,
                "issue_details": issue_check,
                "recommendation": "Use suggested parameter mappings to avoid known errors",
            }
        else:
            return {
                "issues_detected": False,
                "request_looks_good": True,
                "message": "No known issues detected for this integration",
            }

    except Exception as e:
        logger.error(f"Integration check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{source_service}/{target_service}")
async def get_success_patterns(
    source_service: str,
    target_service: str,
    pattern_type: Optional[str] = None,
    memory: AIMemorySystem = Depends(get_ai_memory),
):
    """Get success patterns for service integration"""
    try:
        if pattern_type:
            pattern = await memory.get_success_pattern(
                pattern_type, source_service, target_service
            )
            if pattern:
                return {
                    "pattern_found": True,
                    "pattern": pattern.__dict__,
                    "implementation_code": pattern.implementation_code,
                }
            else:
                return {
                    "pattern_found": False,
                    "message": "No pattern found for specified criteria",
                }
        else:
            # Return all patterns for this service pair
            all_patterns = [
                pattern.__dict__
                for pattern in memory.success_patterns.values()
                if pattern.source_service == source_service
                and pattern.target_service == target_service
            ]
            return {"patterns_found": len(all_patterns), "patterns": all_patterns}

    except Exception as e:
        logger.error(f"Failed to get success patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{source_service}/{target_service}")
async def get_integration_history(
    source_service: str,
    target_service: str,
    memory: AIMemorySystem = Depends(get_ai_memory),
):
    """Get integration error history between two services"""
    try:
        history = await memory.get_integration_history(source_service, target_service)

        return {
            "history_found": len(history),
            "integration_history": [error.__dict__ for error in history],
            "insights": {
                "total_errors": len(history),
                "resolved_errors": sum(1 for e in history if e.resolved),
                "common_error_types": list(set(e.error_type for e in history)),
                "avg_resolution_time": (
                    sum(e.resolution_time_minutes for e in history) / len(history)
                    if history
                    else 0
                ),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get integration history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_memory_stats(memory: AIMemorySystem = Depends(get_ai_memory)):
    """Get comprehensive AI memory statistics"""
    try:
        stats = memory.get_memory_stats()

        # Add additional insights
        error_types = {}
        for error in memory.integration_errors.values():
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1

        pattern_types = {}
        for pattern in memory.success_patterns.values():
            pattern_types[pattern.pattern_type] = (
                pattern_types.get(pattern.pattern_type, 0) + 1
            )

        stats.update(
            {
                "error_type_distribution": error_types,
                "pattern_type_distribution": pattern_types,
                "memory_effectiveness": {
                    "prevented_repeat_errors": "Calculated based on pattern usage",
                    "time_saved_minutes": sum(
                        e.resolution_time_minutes
                        for e in memory.integration_errors.values()
                    ),
                    "learning_rate": "Improving with each recorded interaction",
                },
            }
        )

        return stats

    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def ai_memory_dashboard():
    """AI Memory system dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🧠 AI Memory Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .memory-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
            }
            .error-item {
                background: #f8f9fa;
                border-left: 4px solid #dc3545;
                padding: 10px;
                margin: 5px 0;
            }
            .pattern-item {
                background: #f8f9fa;
                border-left: 4px solid #28a745;
                padding: 10px;
                margin: 5px 0;
            }
            .code-snippet {
                background: #282c34;
                color: #abb2bf;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>🧠 AI Memory Dashboard</h1>
            <p class="lead">Learning system to prevent repeat coding mistakes</p>
            
            <!-- Memory Stats -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="memory-card text-center">
                        <h3 id="api-contracts">-</h3>
                        <p>API Contracts</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="memory-card text-center">
                        <h3 id="integration-errors">-</h3>
                        <p>Integration Errors</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="memory-card text-center">
                        <h3 id="success-patterns">-</h3>
                        <p>Success Patterns</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="memory-card text-center">
                        <h3 id="resolution-rate">-</h3>
                        <p>Resolution Rate</p>
                    </div>
                </div>
            </div>
            
            <!-- Integration Checker -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5>🔍 Integration Issue Checker</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <label for="source-service" class="form-label">Source Service:</label>
                            <select class="form-select" id="source-service">
                                <option value="cmms">CMMS</option>
                                <option value="ai_team">AI Team</option>
                                <option value="external">External</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label for="target-service" class="form-label">Target Service:</label>
                            <select class="form-select" id="target-service">
                                <option value="fix_it_fred">Fix it Fred</option>
                                <option value="ai_team">AI Team</option>
                                <option value="linesmart">LineSmart</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-primary mt-4" onclick="checkIntegration()">
                                Check Integration
                            </button>
                        </div>
                    </div>
                    <div class="mt-3">
                        <label for="request-data" class="form-label">Request Data (JSON):</label>
                        <textarea class="form-control" id="request-data" rows="3" 
                                  placeholder='{"description": "Pump motor running hot", "priority": "high"}'></textarea>
                    </div>
                    <div class="mt-3">
                        <div id="integration-check-results"></div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Memory Activity -->
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>📋 Recent Integration Errors</h5>
                        </div>
                        <div class="card-body">
                            <div id="recent-errors">Loading...</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>✅ Success Patterns</h5>
                        </div>
                        <div class="card-body">
                            <div id="success-patterns-list">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            async function loadMemoryStats() {
                try {
                    const response = await fetch('/ai-memory/stats');
                    const stats = await response.json();
                    
                    document.getElementById('api-contracts').textContent = stats.total_api_contracts || 0;
                    document.getElementById('integration-errors').textContent = stats.total_integration_errors || 0;
                    document.getElementById('success-patterns').textContent = stats.success_patterns || 0;
                    document.getElementById('resolution-rate').textContent = 
                        ((stats.resolution_rate || 0) * 100).toFixed(1) + '%';
                    
                } catch (error) {
                    console.error('Failed to load memory stats:', error);
                }
            }
            
            async function checkIntegration() {
                const sourceService = document.getElementById('source-service').value;
                const targetService = document.getElementById('target-service').value;
                const requestData = document.getElementById('request-data').value;
                
                if (!requestData.trim()) {
                    alert('Please enter request data JSON');
                    return;
                }
                
                try {
                    const parsedData = JSON.parse(requestData);
                    
                    const response = await fetch('/ai-memory/check-integration', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            source_service: sourceService,
                            target_service: targetService,
                            request_data: parsedData
                        })
                    });
                    
                    const result = await response.json();
                    
                    let resultHtml = '';
                    if (result.issues_detected) {
                        resultHtml = `
                            <div class="alert alert-warning">
                                <h6>⚠️ Potential Issues Detected</h6>
                                <p><strong>Recommendation:</strong> ${result.recommendation}</p>
                                <details>
                                    <summary>Issue Details</summary>
                                    <pre class="code-snippet">${JSON.stringify(result.issue_details, null, 2)}</pre>
                                </details>
                            </div>
                        `;
                    } else {
                        resultHtml = `
                            <div class="alert alert-success">
                                <h6>✅ Integration Looks Good</h6>
                                <p>${result.message}</p>
                            </div>
                        `;
                    }
                    
                    document.getElementById('integration-check-results').innerHTML = resultHtml;
                    
                } catch (error) {
                    document.getElementById('integration-check-results').innerHTML = 
                        `<div class="alert alert-danger">Error: ${error.message}</div>`;
                }
            }
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                loadMemoryStats();
            });
        </script>
    </body>
    </html>
    """


@router.get("/export")
async def export_memory(memory: AIMemorySystem = Depends(get_ai_memory)):
    """Export all AI memory for backup or sharing"""
    try:
        export_data = {
            "api_contracts": {k: v.__dict__ for k, v in memory.api_contracts.items()},
            "integration_errors": {
                k: v.__dict__ for k, v in memory.integration_errors.items()
            },
            "success_patterns": {
                k: v.__dict__ for k, v in memory.success_patterns.items()
            },
            "export_metadata": {
                "export_time": memory.get_memory_stats()["last_updated"],
                "total_items": len(memory.api_contracts)
                + len(memory.integration_errors)
                + len(memory.success_patterns),
            },
        }

        return JSONResponse(content=export_data)

    except Exception as e:
        logger.error(f"Failed to export memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))
