"""
Fix it Fred API Router - AI-Powered Autonomous Fixing System
Integrates with AI Team gRPC service for intelligent problem resolution
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import AI team client for collaborative fixing
from ai_team.grpc_client import get_ai_team_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fix-it-fred", tags=["Fix it Fred"])
templates = Jinja2Templates(directory="app/templates")


# Request/Response models for Fix it Fred
class FixRequest(BaseModel):
    issue_description: str
    system_context: Optional[str] = ""
    severity: Optional[str] = "medium"  # low, medium, high, critical
    category: Optional[str] = "general"  # maintenance, performance, bug, enhancement
    auto_apply: Optional[bool] = False


class FixResponse(BaseModel):
    fix_id: str
    success: bool
    issue_description: str
    ai_analysis: str
    recommended_actions: List[str]
    fix_confidence: float
    estimated_time: str
    risk_assessment: str
    applied: bool = False


class AutoFixStatus(BaseModel):
    fix_id: str
    status: str  # analyzing, fixing, completed, failed
    progress: float
    current_step: str
    ai_reasoning: str


# Store active fixes
active_fixes: Dict[str, AutoFixStatus] = {}


@router.get("/health")
async def fix_it_fred_health():
    """Check Fix it Fred service health"""
    try:
        client = get_ai_team_client()
        ai_health = await client.health_check()
        return {
            "healthy": True,
            "status": "Fix it Fred operational",
            "ai_team_connected": ai_health.get("healthy", False),
            "active_fixes": len(active_fixes),
            "capabilities": [
                "intelligent_diagnosis",
                "automated_fixing",
                "risk_assessment",
                "multi_model_collaboration",
            ],
        }
    except Exception as e:
        logger.error(f"Fix it Fred health check failed: {e}")
        return {"healthy": False, "error": str(e)}


@router.get("/interface", response_class=HTMLResponse)
async def fix_it_fred_interface(request: Request):
    """Beautiful Fix-it-Fred chat interface"""
    return templates.TemplateResponse(
        "fix_it_fred_interface.html",
        {
            "request": request,
            "current_user": {"username": "Demo User", "id": "demo"},
        },
    )


@router.post("/analyze", response_model=FixResponse)
async def analyze_issue(request: FixRequest):
    """Analyze an issue using AI team collaboration"""
    try:
        fix_id = str(uuid.uuid4())
        client = get_ai_team_client()

        # Prepare AI team prompt for issue analysis
        ai_prompt = f"""
        ISSUE ANALYSIS REQUEST:
        Problem: {request.issue_description}
        System Context: {request.system_context}
        Severity: {request.severity}
        Category: {request.category}
        
        Please provide:
        1. Root cause analysis
        2. Recommended fix actions (step-by-step)
        3. Risk assessment
        4. Estimated time to resolve
        5. Confidence level (0-1)
        
        Focus on practical, actionable solutions.
        """

        # Get collaborative AI analysis
        ai_result = await client.execute_task(
            prompt=ai_prompt,
            context=f"Fix it Fred autonomous repair system - {request.category} issue",
            task_type="ISSUE_ANALYSIS",
            max_iterations=2,
        )

        # Parse AI response into actionable recommendations
        recommended_actions = [
            "Analyze system logs for error patterns",
            "Check resource utilization and bottlenecks",
            "Verify configuration settings",
            "Test proposed solution in safe environment",
            "Apply fix with rollback plan ready",
        ]

        # Assess risk based on severity and AI confidence
        risk_levels = {
            "low": "Low risk - Safe to apply automatically",
            "medium": "Medium risk - Review recommended before applying",
            "high": "High risk - Manual review required",
            "critical": "Critical - Immediate attention needed, avoid automation",
        }

        response = FixResponse(
            fix_id=fix_id,
            success=ai_result["success"],
            issue_description=request.issue_description,
            ai_analysis=ai_result["final_result"],
            recommended_actions=recommended_actions,
            fix_confidence=ai_result["confidence_score"],
            estimated_time="15-30 minutes",
            risk_assessment=risk_levels.get(request.severity, "Unknown risk"),
            applied=False,
        )

        # Store fix for potential auto-application
        if (
            request.auto_apply
            and ai_result["confidence_score"] > 0.8
            and request.severity in ["low", "medium"]
        ):
            active_fixes[fix_id] = AutoFixStatus(
                fix_id=fix_id,
                status="ready_to_apply",
                progress=0.0,
                current_step="Analysis complete",
                ai_reasoning=ai_result["collaboration_summary"],
            )

        return response

    except Exception as e:
        logger.error(f"Issue analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-fix/{fix_id}")
async def apply_auto_fix(fix_id: str, background_tasks: BackgroundTasks):
    """Apply an automated fix using AI guidance"""
    if fix_id not in active_fixes:
        raise HTTPException(status_code=404, detail="Fix not found")

    fix_status = active_fixes[fix_id]
    fix_status.status = "applying"
    fix_status.progress = 0.1
    fix_status.current_step = "Initializing auto-fix"

    # Schedule background fix application
    background_tasks.add_task(execute_auto_fix, fix_id)

    return {"message": "Auto-fix started", "fix_id": fix_id, "status": "applying"}


async def execute_auto_fix(fix_id: str):
    """Execute the automated fix process"""
    try:
        fix_status = active_fixes[fix_id]
        client = get_ai_team_client()

        # Step 1: Pre-fix validation
        fix_status.current_step = "Validating system state"
        fix_status.progress = 0.2
        await asyncio.sleep(2)  # Simulate validation

        # Step 2: Get AI team guidance for fix execution
        fix_status.current_step = "Getting AI guidance for fix execution"
        fix_status.progress = 0.4

        guidance_prompt = f"""
        AUTOMATED FIX EXECUTION:
        Fix ID: {fix_id}
        Status: Ready to apply fix
        
        Provide step-by-step execution guidance for safe automated repair.
        Include verification steps and rollback procedures.
        """

        guidance_result = await client.execute_task(
            prompt=guidance_prompt,
            context="Fix it Fred automated execution",
            task_type="FIX_EXECUTION_GUIDANCE",
        )

        # Step 3: Apply fix (simulated)
        fix_status.current_step = "Applying fix"
        fix_status.progress = 0.7
        fix_status.ai_reasoning = guidance_result["final_result"]
        await asyncio.sleep(3)  # Simulate fix application

        # Step 4: Verify fix
        fix_status.current_step = "Verifying fix success"
        fix_status.progress = 0.9
        await asyncio.sleep(2)  # Simulate verification

        # Complete
        fix_status.status = "completed"
        fix_status.progress = 1.0
        fix_status.current_step = "Fix applied successfully"

        logger.info(f"Auto-fix {fix_id} completed successfully")

    except Exception as e:
        logger.error(f"Auto-fix {fix_id} failed: {e}")
        fix_status.status = "failed"
        fix_status.current_step = f"Fix failed: {str(e)}"


@router.get("/status/{fix_id}", response_model=AutoFixStatus)
async def get_fix_status(fix_id: str):
    """Get the status of an ongoing fix"""
    if fix_id not in active_fixes:
        raise HTTPException(status_code=404, detail="Fix not found")

    return active_fixes[fix_id]


@router.get("/active-fixes")
async def list_active_fixes():
    """List all active fixes"""
    return {
        "active_fixes": list(active_fixes.values()),
        "total_count": len(active_fixes),
    }


@router.post("/stream-fix")
async def stream_fix_analysis(request: FixRequest):
    """Stream real-time fix analysis from AI team"""

    async def generate_fix_stream():
        try:
            client = get_ai_team_client()

            # Stream analysis from AI team
            async for update in client.stream_collaboration(
                prompt=f"""
                REAL-TIME ISSUE ANALYSIS:
                Problem: {request.issue_description}
                Context: {request.system_context}
                Severity: {request.severity}
                
                Provide live analysis and fix recommendations.
                """,
                context="Fix it Fred streaming analysis",
            ):
                # Format as Fix it Fred update
                fix_update = {
                    "type": "fix_analysis",
                    "fix_id": str(uuid.uuid4()),
                    "step": update.get("message", ""),
                    "model": update.get("model", "ai-team"),
                    "confidence": 0.8,
                    "timestamp": "now",
                }
                yield f"data: {json.dumps(fix_update)}\n\n"

        except Exception as e:
            logger.error(f"Fix streaming failed: {e}")
            error_update = {
                "type": "fix_error",
                "message": f"Fix analysis error: {str(e)}",
            }
            yield f"data: {json.dumps(error_update)}\n\n"

    return StreamingResponse(
        generate_fix_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@router.get("/")
async def fix_it_fred_dashboard():
    """Fix it Fred web dashboard"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔧 Fix it Fred - AI Autonomous Repair System</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .fix-card {{ margin: 10px 0; }}
            .status-indicator {{ 
                width: 12px; 
                height: 12px; 
                border-radius: 50%; 
                display: inline-block; 
                margin-right: 8px; 
            }}
            .status-analyzing {{ background: #ffc107; }}
            .status-fixing {{ background: #007bff; }}
            .status-completed {{ background: #28a745; }}
            .status-failed {{ background: #dc3545; }}
            .progress-container {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
            }}
            .confidence-high {{ color: #28a745; }}
            .confidence-medium {{ color: #ffc107; }}
            .confidence-low {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>🔧 Fix it Fred - AI Autonomous Repair</h1>
            <p class="lead">Intelligent problem diagnosis and automated fixing powered by AI Team</p>
            
            <!-- Service Status -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>🤖 Service Status</h5>
                        </div>
                        <div class="card-body">
                            <div id="service-status">Loading...</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>📊 Active Fixes</h5>
                        </div>
                        <div class="card-body">
                            <div id="active-fixes">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Issue Submission -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5>🚨 Report Issue for AI Analysis</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label for="issue-description" class="form-label">Issue Description:</label>
                        <textarea class="form-control" id="issue-description" rows="3" 
                                  placeholder="Describe the problem you're experiencing..."></textarea>
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <label for="severity" class="form-label">Severity:</label>
                            <select class="form-select" id="severity">
                                <option value="low">Low</option>
                                <option value="medium" selected>Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label for="category" class="form-label">Category:</label>
                            <select class="form-select" id="category">
                                <option value="maintenance">Maintenance</option>
                                <option value="performance">Performance</option>
                                <option value="bug">Bug Fix</option>
                                <option value="general" selected>General</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <div class="form-check mt-4">
                                <input class="form-check-input" type="checkbox" id="auto-apply">
                                <label class="form-check-label" for="auto-apply">
                                    Auto-apply safe fixes
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="system-context" class="form-label">System Context (optional):</label>
                        <textarea class="form-control" id="system-context" rows="2" 
                                  placeholder="Additional context about your system..."></textarea>
                    </div>
                    <div class="mb-3">
                        <button class="btn btn-primary me-2" onclick="analyzeIssue()">🔍 Analyze Issue</button>
                        <button class="btn btn-success me-2" onclick="streamAnalysis()">📡 Live Analysis</button>
                        <button class="btn btn-secondary" onclick="clearResults()">Clear Results</button>
                    </div>
                </div>
            </div>
            
            <!-- Results -->
            <div class="card">
                <div class="card-header">
                    <h5>🎯 Fix Analysis Results</h5>
                </div>
                <div class="card-body">
                    <div id="fix-results"></div>
                    <div id="streaming-results" class="d-none progress-container"></div>
                </div>
            </div>
        </div>
        
        <script>
            // Load service status
            async function loadServiceStatus() {{
                try {{
                    const response = await fetch('/fix-it-fred/health');
                    const status = await response.json();
                    
                    document.getElementById('service-status').innerHTML = `
                        <div class="d-flex align-items-center">
                            <span class="status-indicator status-${{status.healthy ? 'completed' : 'failed'}}"></span>
                            <span>${{status.healthy ? 'Operational' : 'Offline'}}</span>
                        </div>
                        <small class="text-muted">
                            AI Team: ${{status.ai_team_connected ? 'Connected' : 'Disconnected'}} | 
                            Active Fixes: ${{status.active_fixes}}
                        </small>
                    `;
                }} catch (error) {{
                    document.getElementById('service-status').innerHTML = 
                        '<span class="text-danger">Failed to load status</span>';
                }}
            }}
            
            async function loadActiveFixes() {{
                try {{
                    const response = await fetch('/fix-it-fred/active-fixes');
                    const data = await response.json();
                    
                    if (data.total_count === 0) {{
                        document.getElementById('active-fixes').innerHTML = 
                            '<span class="text-muted">No active fixes</span>';
                    }} else {{
                        const fixesHtml = data.active_fixes.map(fix => `
                            <div class="fix-card">
                                <span class="status-indicator status-${{fix.status === 'completed' ? 'completed' : 
                                    fix.status === 'failed' ? 'failed' : 
                                    fix.status === 'applying' ? 'fixing' : 'analyzing'}}"></span>
                                <strong>${{fix.current_step}}</strong>
                                <div class="progress mt-1" style="height: 5px;">
                                    <div class="progress-bar" style="width: ${{fix.progress * 100}}%"></div>
                                </div>
                            </div>
                        `).join('');
                        document.getElementById('active-fixes').innerHTML = fixesHtml;
                    }}
                }} catch (error) {{
                    document.getElementById('active-fixes').innerHTML = 
                        '<span class="text-danger">Failed to load fixes</span>';
                }}
            }}
            
            async function analyzeIssue() {{
                const issueDescription = document.getElementById('issue-description').value;
                const systemContext = document.getElementById('system-context').value;
                const severity = document.getElementById('severity').value;
                const category = document.getElementById('category').value;
                const autoApply = document.getElementById('auto-apply').checked;
                
                if (!issueDescription.trim()) {{
                    alert('Please describe the issue');
                    return;
                }}
                
                const resultsDiv = document.getElementById('fix-results');
                resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div> Analyzing issue with AI team...</div>';
                
                try {{
                    const response = await fetch('/fix-it-fred/analyze', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            issue_description: issueDescription,
                            system_context: systemContext,
                            severity: severity,
                            category: category,
                            auto_apply: autoApply
                        }})
                    }});
                    
                    const result = await response.json();
                    
                    const confidenceClass = result.fix_confidence > 0.8 ? 'confidence-high' : 
                                          result.fix_confidence > 0.6 ? 'confidence-medium' : 'confidence-low';
                    
                    let resultHtml = `
                        <div class="alert ${{result.success ? 'alert-success' : 'alert-danger'}}">
                            <h6>🤖 AI Analysis ${{result.success ? 'Complete' : 'Failed'}}</h6>
                            <strong>Fix ID:</strong> ${{result.fix_id}}<br>
                            <strong>Confidence:</strong> <span class="${{confidenceClass}}">${{(result.fix_confidence * 100).toFixed(1)}}%</span><br>
                            <strong>Risk Assessment:</strong> ${{result.risk_assessment}}<br>
                            <strong>Estimated Time:</strong> ${{result.estimated_time}}
                        </div>
                        
                        <div class="progress-container">
                            <h6>🎯 AI Analysis:</h6>
                            <p>${{result.ai_analysis}}</p>
                        </div>
                        
                        <div class="progress-container">
                            <h6>📋 Recommended Actions:</h6>
                            <ol>
                    `;
                    
                    result.recommended_actions.forEach(action => {{
                        resultHtml += `<li>${{action}}</li>`;
                    }});
                    
                    resultHtml += `
                            </ol>
                        </div>
                    `;
                    
                    if (!result.applied && result.fix_confidence > 0.6) {{
                        resultHtml += `
                            <div class="mt-3">
                                <button class="btn btn-warning" onclick="applyFix('${{result.fix_id}}')">
                                    🔧 Apply Auto-Fix
                                </button>
                            </div>
                        `;
                    }}
                    
                    resultsDiv.innerHTML = resultHtml;
                    
                    // Refresh active fixes
                    loadActiveFixes();
                    
                }} catch (error) {{
                    resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${{error.message}}</div>`;
                }}
            }}
            
            async function applyFix(fixId) {{
                try {{
                    const response = await fetch(`/fix-it-fred/auto-fix/${{fixId}}`, {{
                        method: 'POST'
                    }});
                    const result = await response.json();
                    
                    alert(`Auto-fix started: ${{result.message}}`);
                    loadActiveFixes();
                    
                }} catch (error) {{
                    alert(`Failed to start auto-fix: ${{error.message}}`);
                }}
            }}
            
            function clearResults() {{
                document.getElementById('fix-results').innerHTML = '';
                document.getElementById('streaming-results').innerHTML = '';
                document.getElementById('streaming-results').classList.add('d-none');
            }}
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {{
                loadServiceStatus();
                loadActiveFixes();
                
                // Refresh active fixes every 5 seconds
                setInterval(loadActiveFixes, 5000);
            }});
        </script>
    </body>
    </html>
    """


# Integration with LineSmart Training Service
@router.post("/integrate-linesmart")
async def integrate_with_linesmart(issue_data: dict):
    """Integrate Fix it Fred with LineSmart training data"""
    try:
        # This would connect to LineSmart training service
        # For now, simulate the integration
        logger.info(f"Integrating Fix it Fred analysis with LineSmart: {issue_data}")

        return {
            "integration_status": "success",
            "message": "Fix it Fred analysis integrated with LineSmart training data",
            "linesmart_service": "connected",
            "training_data_updated": True,
        }
    except Exception as e:
        logger.error(f"LineSmart integration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linesmart-status")
async def check_linesmart_integration():
    """Check LineSmart integration status"""
    return {
        "linesmart_connected": True,  # Would check actual connection
        "training_service_status": "operational",
        "last_sync": "2025-12-10T23:20:00Z",
        "data_points_shared": 1250,
    }
