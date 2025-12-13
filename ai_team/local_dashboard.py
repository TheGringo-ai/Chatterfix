#!/usr/bin/env python3
"""
🚀 AI TEAM LOCAL DASHBOARD
==========================
Comprehensive local dashboard for monitoring and controlling the AI team.
Real-time insights into memory system, learning analytics, and team performance.

Usage: python ai_team/local_dashboard.py
Access: http://localhost:8888
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add project root to Python path
try:
    project_root = Path(__file__).parent.parent
except NameError:
    # Handle case when __file__ is not defined (e.g., in exec)
    project_root = Path.cwd()
sys.path.append(str(project_root))

# Import our AI team modules with fallback
try:
    from ai_team.autogen_framework import get_orchestrator
    from ai_team.ultimate_memory_system import ultimate_memory
    from ai_team.universal_ai_platform import universal_ai

    AI_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI modules not available: {e}")
    print("📊 Running dashboard in demo mode...")
    AI_MODULES_AVAILABLE = False

    # Mock objects for demo mode
    class MockMemorySystem:
        async def get_learning_analytics(self):
            return {
                "total_conversations": 127,
                "patterns_learned": 23,
                "solutions_stored": 89,
                "mistakes_prevented": 15,
                "learning_velocity": 0.85,
                "pattern_recognition_accuracy": 0.92,
                "mistake_prevention_rate": 0.98,
                "solution_success_rate": 0.94,
            }

        async def search_knowledge(self, query, application=None, limit=10):
            return [f"Demo result {i} for '{query}'" for i in range(min(3, limit))]

        async def initialize(self):
            pass

    class MockUniversalPlatform:
        async def get_platform_analytics(self):
            return {
                "platform_metrics": {
                    "total_applications": 3,
                    "active_applications": 3,
                    "cross_app_patterns": 12,
                    "platform_effectiveness": 87,
                }
            }

    from dataclasses import dataclass
    from typing import List

    @dataclass
    class MockCollaborationResult:
        task_id: str
        success: bool
        final_answer: str
        agent_responses: List
        collaboration_log: List
        total_time: float
        confidence_score: float

    class MockAutogenOrchestrator:
        async def execute_collaborative_task(
            self, task_id, prompt, context="", required_agents=None
        ):
            return MockCollaborationResult(
                task_id=task_id,
                success=True,
                final_answer=f"Mock collaboration result for: {prompt}",
                agent_responses=[],
                collaboration_log=[],
                total_time=0.1,
                confidence_score=0.8,
            )

    ultimate_memory = MockMemorySystem()
    universal_ai = MockUniversalPlatform()
    get_orchestrator = lambda: MockAutogenOrchestrator()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Team Dashboard",
    description="Local dashboard for monitoring and controlling the AI team",
    version="1.0.0",
)

# Static files and templates
try:
    dashboard_dir = Path(__file__).parent / "dashboard"
except NameError:
    dashboard_dir = Path.cwd() / "ai_team" / "dashboard"

dashboard_dir.mkdir(exist_ok=True)
templates_dir = dashboard_dir / "templates"
templates_dir.mkdir(exist_ok=True)
static_dir = dashboard_dir / "static"
static_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# WebSocket connections for real-time updates
connected_websockets: List[WebSocket] = []


class AITeamDashboard:
    """Main dashboard controller for AI team monitoring"""

    def __init__(self):
        self.memory_system = ultimate_memory
        self.universal_platform = universal_ai
        self.autogen_framework = get_orchestrator()
        self.start_time = datetime.now()

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Memory system status
            memory_stats = await self.memory_system.get_learning_analytics()

            # Platform analytics
            platform_analytics = await self.universal_platform.get_platform_analytics()

            # System health
            uptime = datetime.now() - self.start_time

            return {
                "status": "online",
                "uptime": str(uptime).split(".")[0],
                "memory_system": {
                    "total_conversations": memory_stats.get("total_conversations", 0),
                    "patterns_learned": memory_stats.get("patterns_learned", 0),
                    "solutions_stored": memory_stats.get("solutions_stored", 0),
                    "mistakes_prevented": memory_stats.get("mistakes_prevented", 0),
                },
                "platform": {
                    "applications": platform_analytics.get("platform_metrics", {}).get(
                        "total_applications", 0
                    ),
                    "active_apps": platform_analytics.get("platform_metrics", {}).get(
                        "active_applications", 0
                    ),
                    "cross_app_patterns": platform_analytics.get(
                        "platform_metrics", {}
                    ).get("cross_app_patterns", 0),
                    "effectiveness": platform_analytics.get("platform_metrics", {}).get(
                        "platform_effectiveness", 0
                    ),
                },
                "autogen": {
                    "status": "ready",
                    "models_available": ["claude", "gpt-4", "gemini"],
                    "active_conversations": 0,
                },
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "uptime": str(datetime.now() - self.start_time).split(".")[0],
            }

    async def get_recent_interactions(self, limit: int = 10) -> List[Dict]:
        """Get recent AI team interactions"""
        try:
            # This would connect to the actual memory database
            # For now, return sample data
            return [
                {
                    "id": f"interaction_{i}",
                    "timestamp": (
                        datetime.now() - timedelta(minutes=i * 5)
                    ).isoformat(),
                    "application": ["ChatterFix", "Fix it Fred", "LineSmart"][i % 3],
                    "user_request": f"Sample request {i}",
                    "ai_response": f"AI response {i}",
                    "success": True,
                    "learning_points": i % 3,
                }
                for i in range(limit)
            ]
        except Exception as e:
            logger.error(f"Error getting recent interactions: {e}")
            return []

    async def get_learning_analytics(self) -> Dict[str, Any]:
        """Get detailed learning analytics"""
        try:
            analytics = await self.memory_system.get_learning_analytics()

            return {
                "learning_velocity": analytics.get("learning_velocity", 0),
                "pattern_recognition_accuracy": analytics.get(
                    "pattern_recognition_accuracy", 0
                ),
                "mistake_prevention_rate": analytics.get("mistake_prevention_rate", 0),
                "solution_success_rate": analytics.get("solution_success_rate", 0),
                "top_patterns": analytics.get("top_patterns", []),
                "application_performance": analytics.get("application_performance", {}),
                "recent_improvements": analytics.get("recent_improvements", []),
            }
        except Exception as e:
            logger.error(f"Error getting learning analytics: {e}")
            return {"error": str(e)}


# Initialize dashboard
dashboard = AITeamDashboard()


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    return await dashboard.get_system_status()


@app.get("/api/interactions")
async def get_interactions(limit: int = 10):
    """Get recent interactions"""
    return await dashboard.get_recent_interactions(limit)


@app.get("/api/analytics")
async def get_analytics():
    """Get learning analytics"""
    return await dashboard.get_learning_analytics()


@app.post("/api/memory/search")
async def search_memory(query: dict):
    """Search the AI team memory"""
    try:
        results = await dashboard.memory_system.search_knowledge(
            query=query.get("query", ""),
            application=query.get("application"),
            limit=query.get("limit", 10),
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/team/collaborate")
async def team_collaborate(request: dict):
    """Trigger AI team collaboration"""
    try:
        task_id = f"dashboard_task_{datetime.now().timestamp()}"
        result = await dashboard.autogen_framework.execute_collaborative_task(
            task_id=task_id,
            prompt=request.get("prompt"),
            context=request.get("context", ""),
            required_agents=None,
        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Collaboration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    connected_websockets.append(websocket)

    try:
        while True:
            # Send periodic updates
            status = await dashboard.get_system_status()
            await websocket.send_json(
                {
                    "type": "status_update",
                    "data": status,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Wait for next update or client message
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            except asyncio.TimeoutError:
                pass  # Continue sending updates

    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


async def broadcast_update(message: Dict):
    """Broadcast update to all connected clients"""
    if connected_websockets:
        for websocket in connected_websockets.copy():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                connected_websockets.remove(websocket)


if __name__ == "__main__":
    print("🚀 Starting AI Team Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8888")
    print("🔧 Features: Real-time monitoring, memory search, team collaboration")

    # Run the dashboard
    uvicorn.run(
        "local_dashboard:app", host="0.0.0.0", port=8888, reload=True, log_level="info"
    )
