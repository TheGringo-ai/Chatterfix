"""
gRPC Server for AI Team Multi-Model Collaboration
Implements the AITeamService protocol buffer interface
"""

import asyncio
import logging
import uuid
from concurrent import futures
from typing import Any, Dict

import grpc

# Import our autogen framework
from .autogen_framework import CollaborationResult, get_orchestrator


# These would be generated from the .proto file
# For now, we'll create mock implementations
class TaskRequest:
    def __init__(self):
        self.task_id = ""
        self.prompt = ""
        self.context = ""
        self.required_models = []
        self.task_type = 0
        self.parameters = {}
        self.max_iterations = 3
        self.enable_autogen = True


class TaskResponse:
    def __init__(self):
        self.task_id = ""
        self.success = False
        self.final_result = ""
        self.model_responses = []
        self.collaboration_summary = ""
        self.iterations_completed = 0
        self.confidence_score = 0.0


class CollaborationResponse:
    def __init__(self):
        self.task_id = ""
        self.model_name = ""
        self.partial_response = ""
        self.response_type = 0
        self.progress = 0.0
        self.is_final = False


class ModelsRequest:
    pass


class ModelsResponse:
    def __init__(self):
        self.models = []


class HealthRequest:
    pass


class HealthResponse:
    def __init__(self):
        self.healthy = True
        self.status = ""
        self.active_models = []
        self.pending_tasks = 0


class AIModel:
    def __init__(
        self,
        name,
        provider,
        capabilities,
        available=True,
        performance_score=0.8,
        version="1.0",
    ):
        self.name = name
        self.provider = provider
        self.capabilities = capabilities
        self.available = available
        self.performance_score = performance_score
        self.version = version


class ModelResponse:
    def __init__(
        self,
        model_name,
        response,
        confidence=0.8,
        response_time_ms=500,
        success=True,
        error_message="",
    ):
        self.model_name = model_name
        self.response = response
        self.confidence = confidence
        self.response_time_ms = response_time_ms
        self.success = success
        self.error_message = error_message


logger = logging.getLogger(__name__)


class AITeamServiceImplementation:
    """Implementation of the AITeamService"""

    def __init__(self):
        self.orchestrator = get_orchestrator()
        self.active_tasks: Dict[str, Any] = {}

    async def ExecuteTask(self, request: TaskRequest) -> TaskResponse:
        """Execute a collaborative task with the AI team"""
        try:
            task_id = request.task_id or str(uuid.uuid4())

            logger.info(f"Executing task {task_id}: {request.prompt[:100]}...")

            # Execute collaboration using autogen framework
            result = await self.orchestrator.execute_collaborative_task(
                task_id=task_id,
                prompt=request.prompt,
                context=request.context,
                required_agents=(
                    list(request.required_models) if request.required_models else None
                ),
                max_iterations=request.max_iterations or 3,
            )

            # Convert to gRPC response
            response = TaskResponse()
            response.task_id = result.task_id
            response.success = result.success
            response.final_result = result.final_answer
            response.collaboration_summary = " | ".join(result.collaboration_log)
            response.iterations_completed = len(result.agent_responses)
            response.confidence_score = result.confidence_score

            # Convert agent responses
            response.model_responses = []
            for agent_resp in result.agent_responses:
                model_resp = ModelResponse(
                    model_name=agent_resp.get("agent", "unknown"),
                    response=agent_resp.get("response", ""),
                    confidence=0.8,  # Default confidence
                    response_time_ms=int(
                        result.total_time * 1000 / len(result.agent_responses)
                    ),
                    success=True,
                )
                response.model_responses.append(model_resp)

            logger.info(f"Task {task_id} completed successfully")
            return response

        except Exception as e:
            logger.error(f"Error executing task: {e}")
            response = TaskResponse()
            response.task_id = request.task_id or "error"
            response.success = False
            response.final_result = f"Error: {str(e)}"
            response.collaboration_summary = "Task failed due to error"
            response.confidence_score = 0.0
            return response

    async def StreamCollaboration(self, request: TaskRequest):
        """Stream collaborative responses from multiple models"""
        try:
            task_id = request.task_id or str(uuid.uuid4())

            logger.info(f"Streaming collaboration for task {task_id}")

            async for update in self.orchestrator.stream_collaboration(
                task_id=task_id, prompt=request.prompt, context=request.context
            ):
                response = CollaborationResponse()
                response.task_id = task_id
                response.model_name = update.get("agent", "system")
                response.partial_response = update.get("message", "")
                response.progress = update.get("progress", 0.0)
                response.is_final = update.get("type") == "complete"

                yield response

        except Exception as e:
            logger.error(f"Error streaming collaboration: {e}")
            error_response = CollaborationResponse()
            error_response.task_id = request.task_id or "error"
            error_response.model_name = "system"
            error_response.partial_response = f"Error: {str(e)}"
            error_response.is_final = True
            yield error_response

    async def GetAvailableModels(self, request: ModelsRequest) -> ModelsResponse:
        """Get available AI models and their capabilities"""
        try:
            agent_status = self.orchestrator.get_agent_status()

            response = ModelsResponse()
            response.models = []

            for agent_info in agent_status["agents"]:
                model = AIModel(
                    name=agent_info["name"],
                    provider=agent_info["model_type"],
                    capabilities=agent_info["capabilities"],
                    available=agent_info["enabled"],
                    performance_score=0.8,  # Default score
                    version="1.0",
                )
                response.models.append(model)

            logger.info(f"Returning {len(response.models)} available models")
            return response

        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return ModelsResponse()

    async def HealthCheck(self, request: HealthRequest) -> HealthResponse:
        """Health check for AI team service"""
        try:
            agent_status = self.orchestrator.get_agent_status()

            response = HealthResponse()
            response.healthy = True
            response.status = "AI Team Service is running"
            response.active_models = [
                agent["name"] for agent in agent_status["agents"] if agent["enabled"]
            ]
            response.pending_tasks = len(self.active_tasks)

            return response

        except Exception as e:
            logger.error(f"Health check error: {e}")
            response = HealthResponse()
            response.healthy = False
            response.status = f"Error: {str(e)}"
            response.active_models = []
            response.pending_tasks = 0
            return response


async def serve(port: int = 50051):
    """Start the gRPC AI Team server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add our service implementation
    ai_team_service = AITeamServiceImplementation()

    # In a real implementation, this would use the generated gRPC code:
    # ai_team_pb2_grpc.add_AITeamServiceServicer_to_server(ai_team_service, server)

    # For now, we'll manually bind to the port
    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting AI Team gRPC server on {listen_addr}")

    await server.start()

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down AI Team gRPC server")
        await server.stop(grace=5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
