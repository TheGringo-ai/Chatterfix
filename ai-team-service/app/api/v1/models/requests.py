"""
Request models for AI Team Service API
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class ExecuteTaskRequest(BaseModel):
    """Request model for executing collaborative AI task"""
    prompt: str = Field(..., description="The task prompt for AI collaboration")
    context: Optional[str] = Field("", description="Additional context for the task")
    required_agents: Optional[List[str]] = Field(None, description="Specific agents to use")
    max_iterations: Optional[int] = Field(3, ge=1, le=10, description="Maximum collaboration iterations")
    project_context: Optional[str] = Field("ChatterFix", description="Project context")
    fast_mode: Optional[bool] = Field(False, description="Skip refinement phase for ~50% faster responses")

class StreamTaskRequest(BaseModel):
    """Request model for streaming collaborative AI task"""
    prompt: str = Field(..., description="The task prompt for AI collaboration")
    context: Optional[str] = Field("", description="Additional context for the task")
    required_agents: Optional[List[str]] = Field(None, description="Specific agents to use")
    max_iterations: Optional[int] = Field(3, ge=1, le=10, description="Maximum collaboration iterations")
    project_context: Optional[str] = Field("ChatterFix", description="Project context")
    fast_mode: Optional[bool] = Field(False, description="Skip refinement phase for ~50% faster responses")

class MemorySearchRequest(BaseModel):
    """Request model for memory system search"""
    query: str = Field(..., description="Search query")
    max_results: Optional[int] = Field(10, ge=1, le=100, description="Maximum results to return")
    search_type: Optional[str] = Field("semantic", description="Type of search (semantic, keyword, hybrid)")

class RebuildIndexRequest(BaseModel):
    """Request model for rebuilding search index"""
    force_rebuild: Optional[bool] = Field(False, description="Force complete rebuild")