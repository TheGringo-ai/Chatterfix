"""
AI Team Multi-Model Collaboration Package

This package provides:
- gRPC-based AI team service
- Autogen framework for multi-model collaboration
- Integration with Claude, ChatGPT, Gemini, Grok, and other AI models
- FastAPI web interface for AI team collaboration

Usage:
    from ai_team import get_orchestrator, get_ai_team_client

    # Get the autogen orchestrator
    orchestrator = get_orchestrator()

    # Execute collaborative task
    result = await orchestrator.execute_collaborative_task(
        task_id="task_1",
        prompt="How can we optimize database performance?",
        context="PostgreSQL database with high read workload"
    )
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)

from .autogen_framework import (
    AutogenOrchestrator,
    CollaborationResult,
    get_orchestrator,
)
from .grpc_client import AITeamClient, get_ai_team_client

__version__ = "1.0.0"
__author__ = "ChatterFix AI Team"

__all__ = [
    "get_orchestrator",
    "AutogenOrchestrator",
    "CollaborationResult",
    "get_ai_team_client",
    "AITeamClient",
]
