"""
Response models for AI Team Service API
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """Individual agent response"""
    agent: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role")
    response: str = Field(..., description="Agent response content")
    model_type: str = Field(..., description="Model type used")
    confidence: float = Field(0.7, description="Response confidence score")
    timestamp: float = Field(..., description="Response timestamp")

class ExecuteTaskResponse(BaseModel):
    """Response model for collaborative task execution"""
    task_id: str = Field(..., description="Unique task identifier")
    final_answer: str = Field(..., description="Final collaborative answer")
    agent_responses: List[AgentResponse] = Field(..., description="Individual agent responses")
    collaboration_log: List[str] = Field(..., description="Collaboration process log")
    total_time: float = Field(..., description="Total execution time in seconds")
    confidence_score: float = Field(..., description="Overall confidence score")
    success: bool = Field(True, description="Task execution success")

class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Task status (running, completed, failed)")
    progress: Optional[float] = Field(None, description="Task progress percentage")
    start_time: float = Field(..., description="Task start timestamp")
    end_time: Optional[float] = Field(None, description="Task end timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Overall health status")
    agents: Dict[str, str] = Field(..., description="Agent health status")
    active_tasks: int = Field(..., description="Number of active tasks")
    memory_system: str = Field(..., description="Memory system status")
    timestamp: float = Field(..., description="Health check timestamp")
    error: Optional[str] = Field(None, description="Error message if any")

class AgentInfo(BaseModel):
    """Agent information"""
    name: str = Field(..., description="Agent name")
    model_type: str = Field(..., description="Model type")
    role: str = Field(..., description="Agent role")
    capabilities: List[str] = Field(..., description="Agent capabilities")
    available: bool = Field(..., description="Agent availability")
    conversation_history_length: int = Field(0, description="Conversation history length")

class AnalyticsResponse(BaseModel):
    """Response model for analytics"""
    total_agents: int = Field(..., description="Total number of agents")
    available_agents: int = Field(..., description="Number of available agents")
    agent_details: List[AgentInfo] = Field(..., description="Detailed agent information")
    performance_history: Dict[str, Any] = Field({}, description="Performance history")
    total_tasks_completed: int = Field(0, description="Total completed tasks")
    total_tasks_failed: int = Field(0, description="Total failed tasks")
    timestamp: float = Field(..., description="Analytics timestamp")

class MemorySearchResponse(BaseModel):
    """Response model for memory search"""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_time: float = Field(..., description="Search execution time")
    query: str = Field(..., description="Original search query")