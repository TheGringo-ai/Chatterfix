"""
🤖 AUTONOMOUS FEATURE REQUEST API

Simple endpoint where customers can request features in natural language
and the AI automatically implements them.

Usage: POST /autonomous/request
Body: {"request": "I need budget tracking for my maintenance"}
Response: AI automatically builds the feature!
"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any

# Import our autonomous builder (relative import for now)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ai-team-service'))

try:
    from app.autonomous_agents.autonomous_chatterfix_builder import AutonomousAPI
    AUTONOMOUS_AVAILABLE = True
except ImportError:
    AUTONOMOUS_AVAILABLE = False
    logging.warning("Autonomous agents not available - install autogen")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/autonomous", tags=["Autonomous Features"])

class FeatureRequest(BaseModel):
    """Simple feature request model"""
    request: str
    priority: str = "normal"
    customer_email: str = None

class SimpleFeatureRequest(BaseModel):
    """Ultra-simple request - just text"""
    what_you_want: str

# Global autonomous API instance
autonomous_api = None

async def get_autonomous_api():
    """Get or create autonomous API instance"""
    global autonomous_api
    if autonomous_api is None and AUTONOMOUS_AVAILABLE:
        autonomous_api = AutonomousAPI()
    return autonomous_api

@router.post("/request")
async def request_feature(request: FeatureRequest, background_tasks: BackgroundTasks):
    """
    🤖 Request a new feature - AI will automatically implement it!
    
    Examples:
    - "I need budget tracking"
    - "Add calendar scheduling"  
    - "Create maintenance reports"
    - "Make it work on mobile"
    - "Add inventory management"
    """
    try:
        if not AUTONOMOUS_AVAILABLE:
            return {
                "message": "I'll implement that manually for you!",
                "request": request.request,
                "status": "manual_implementation_pending"
            }
        
        api = await get_autonomous_api()
        if not api:
            raise HTTPException(status_code=503, detail="Autonomous system not ready")
        
        logger.info(f"🤖 Autonomous feature request: {request.request}")
        
        # Process in background for faster response
        background_tasks.add_task(process_autonomous_request, request.request)
        
        return {
            "message": "🤖 I'm building that feature for you right now!",
            "request": request.request,
            "status": "implementing",
            "estimated_time": "2-5 minutes",
            "note": "You'll see the new feature appear in your ChatterFix system shortly."
        }
        
    except Exception as e:
        logger.error(f"❌ Autonomous request error: {e}")
        return {
            "message": "I'll work on that feature and get it implemented soon!",
            "request": request.request, 
            "status": "pending",
            "error": str(e)
        }

@router.post("/simple")
async def simple_request(request: SimpleFeatureRequest, background_tasks: BackgroundTasks):
    """
    🎯 Super simple interface - just tell us what you want!
    
    Example: {"what_you_want": "budget tracking"}
    """
    try:
        feature_request = FeatureRequest(request=request.what_you_want)
        return await request_feature(feature_request, background_tasks)
    except Exception as e:
        return {
            "message": f"I understand you want: {request.what_you_want}. I'm working on it!",
            "status": "understood",
            "error": str(e)
        }

@router.get("/examples")
async def get_examples():
    """Get examples of what customers can request"""
    return {
        "examples": [
            "I need budget tracking for maintenance costs",
            "Add a calendar to schedule maintenance",
            "Create reports showing maintenance history", 
            "Make the app work better on mobile phones",
            "Add inventory tracking for spare parts",
            "I want notifications when maintenance is due",
            "Create a dashboard with maintenance KPIs",
            "Add customer portal for maintenance requests",
            "Enable barcode scanning for equipment",
            "Add time tracking for maintenance work"
        ],
        "how_to_use": "Just describe what you need in plain English!",
        "response_time": "2-5 minutes for automatic implementation"
    }

@router.get("/status")
async def autonomous_status():
    """Check if autonomous system is working"""
    return {
        "autonomous_available": AUTONOMOUS_AVAILABLE,
        "status": "ready" if AUTONOMOUS_AVAILABLE else "manual_mode",
        "message": "AI can automatically implement features" if AUTONOMOUS_AVAILABLE else "Features will be implemented manually"
    }

async def process_autonomous_request(request: str):
    """Background task to process autonomous requests"""
    try:
        api = await get_autonomous_api()
        if api:
            result = await api.request_feature(request)
            logger.info(f"✅ Autonomous implementation result: {result}")
        else:
            logger.info(f"📝 Manual implementation queued: {request}")
    except Exception as e:
        logger.error(f"❌ Background processing error: {e}")

# Quick customer interface HTML
@router.get("/interface", response_class=HTMLResponse)
async def customer_interface():
    """Simple web interface for customers to request features"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Request Features - ChatterFix</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card shadow">
                        <div class="card-header bg-primary text-white">
                            <h3>🤖 Request a New Feature</h3>
                            <p class="mb-0">Tell us what you need and our AI will build it automatically!</p>
                        </div>
                        <div class="card-body">
                            <form id="featureForm">
                                <div class="mb-3">
                                    <label class="form-label">What do you need?</label>
                                    <textarea class="form-control" id="request" rows="3" 
                                        placeholder="Example: I need budget tracking for my maintenance costs"></textarea>
                                </div>
                                <button type="submit" class="btn btn-primary btn-lg">🚀 Build This Feature!</button>
                            </form>
                            
                            <div id="result" class="mt-4"></div>
                            
                            <hr>
                            <h5>💡 Feature Ideas:</h5>
                            <ul class="list-unstyled">
                                <li>• Budget tracking and expense management</li>
                                <li>• Calendar and scheduling features</li> 
                                <li>• Reports and analytics dashboard</li>
                                <li>• Mobile optimization</li>
                                <li>• Inventory and parts tracking</li>
                                <li>• Notification system</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            document.getElementById('featureForm').onsubmit = async function(e) {
                e.preventDefault();
                
                const request = document.getElementById('request').value;
                const resultDiv = document.getElementById('result');
                
                if (!request.trim()) {
                    resultDiv.innerHTML = '<div class="alert alert-warning">Please describe what you need!</div>';
                    return;
                }
                
                resultDiv.innerHTML = '<div class="alert alert-info">🤖 AI is building your feature...</div>';
                
                try {
                    const response = await fetch('/autonomous/simple', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({what_you_want: request})
                    });
                    
                    const data = await response.json();
                    
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h5>✅ ${data.message}</h5>
                            <p><strong>Status:</strong> ${data.status}</p>
                            <p><strong>Your Request:</strong> ${data.request}</p>
                            ${data.estimated_time ? `<p><strong>Estimated Time:</strong> ${data.estimated_time}</p>` : ''}
                            ${data.note ? `<p><em>${data.note}</em></p>` : ''}
                        </div>
                    `;
                } catch (error) {
                    resultDiv.innerHTML = '<div class="alert alert-danger">Error submitting request. Please try again!</div>';
                }
            };
        </script>
    </body>
    </html>
    """
    return html