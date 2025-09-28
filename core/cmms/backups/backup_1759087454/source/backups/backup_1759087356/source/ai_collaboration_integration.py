#!/usr/bin/env python3
"""
ChatterFix CMMS - AI Collaboration Integration
Integration script to add AI collaboration endpoints to the main app
"""

from fastapi import FastAPI
from ai_collaboration_api import ai_collaboration_router
from ai_collaboration_system import initialize_ai_collaboration
import logging

logger = logging.getLogger(__name__)

def integrate_ai_collaboration(app: FastAPI):
    """
    Integrate AI Collaboration System with the main ChatterFix app
    
    Args:
        app: FastAPI application instance
    """
    try:
        # Include the AI collaboration router
        app.include_router(ai_collaboration_router)
        
        # Add startup event to initialize the collaboration system
        @app.on_event("startup")
        async def startup_ai_collaboration():
            """Initialize AI collaboration system on app startup"""
            try:
                await initialize_ai_collaboration()
                logger.info("✅ AI Collaboration System integrated successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AI Collaboration System: {e}")
        
        # Add dashboard route
        @app.get("/ai-collaboration")
        async def ai_collaboration_dashboard():
            """Serve the AI collaboration dashboard"""
            from fastapi.responses import FileResponse
            import os
            
            dashboard_path = os.path.join(
                os.path.dirname(__file__), 
                "templates", 
                "ai_collaboration_dashboard.html"
            )
            
            if os.path.exists(dashboard_path):
                return FileResponse(dashboard_path)
            else:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Dashboard not found")
        
        logger.info("🚀 AI Collaboration endpoints integrated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to integrate AI Collaboration System: {e}")
        return False

# Usage example for manual integration
if __name__ == "__main__":
    from fastapi import FastAPI
    
    # Create test app
    test_app = FastAPI()
    
    # Integrate AI collaboration
    integrate_ai_collaboration(test_app)
    
    print("✅ AI Collaboration System integration complete")
    print("📋 Available endpoints:")
    print("  - GET  /ai-collaboration - Dashboard")
    print("  - GET  /api/ai-collaboration/status - System status")
    print("  - POST /api/ai-collaboration/session/start - Start AI session")
    print("  - POST /api/ai-collaboration/session/end - End AI session")
    print("  - POST /api/ai-collaboration/task/create - Create task")
    print("  - POST /api/ai-collaboration/task/complete - Complete task")
    print("  - GET  /api/ai-collaboration/tasks/{ai_model} - Get AI tasks")
    print("  - POST /api/ai-collaboration/knowledge/query - Query knowledge")
    print("  - POST /api/ai-collaboration/deploy/safety-check - Deployment safety")
    print("  - GET  /api/ai-collaboration/context/current - Current context")
    print("  - POST /api/ai-collaboration/handoff/initiate - Initiate handoff")
    print("  - And more...")