"""
HTTP Client for AI Team Service
Replaces gRPC client with HTTP REST API calls
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, AsyncGenerator

import httpx

logger = logging.getLogger(__name__)


class AITeamHTTPClient:
    """HTTP client for communicating with the AI Team Service"""

    def __init__(self):
        self.base_url = os.getenv("AI_TEAM_SERVICE_URL", "http://localhost:8080")
        self.api_key = os.getenv("INTERNAL_API_KEY", "ai-team-service-key-change-me")
        self.timeout = httpx.Timeout(300.0)  # 5 minute timeout for AI tasks

        # Remove trailing slash from base URL
        self.base_url = self.base_url.rstrip("/")

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ChatterFix-CMMS/1.0",
            },
        )

        logger.info(f"✅ AI Team HTTP client initialized: {self.base_url}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check AI Team service health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"AI Team health check failed: {e}")
            return {"status": "error", "error": str(e), "available": False}
        except Exception as e:
            logger.error(f"Unexpected health check error: {e}")
            return {"status": "error", "error": str(e), "available": False}

    async def execute_collaborative_task(
        self,
        prompt: str,
        context: str = "",
        required_agents: Optional[List[str]] = None,
        max_iterations: int = 3,
        project_context: str = "ChatterFix",
        fast_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute collaborative AI task via HTTP API

        Args:
            prompt: Task prompt
            context: Additional context
            required_agents: Specific agents to use (None = all)
            max_iterations: Max collaboration rounds
            project_context: Project name
            fast_mode: Skip refinement phase for ~50% faster responses
        """
        try:
            mode = "⚡ FAST" if fast_mode else "🔄 FULL"
            logger.info(f"🚀 Executing {mode} AI team task: {prompt[:100]}...")

            request_data = {
                "prompt": prompt,
                "context": context,
                "required_agents": required_agents,
                "max_iterations": max_iterations,
                "project_context": project_context,
                "fast_mode": fast_mode,
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/execute", json=request_data
            )
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"✅ AI team task completed in {result.get('total_time', 0):.2f}s"
            )

            # Convert to AITaskResponse-compatible format
            return {
                "task_id": result.get("task_id", ""),
                "success": result.get("success", True),
                "final_result": result.get("final_answer", ""),
                "model_responses": result.get("agent_responses", []),
                "collaboration_summary": result.get(
                    "collaboration_summary", "AI team collaboration completed"
                ),
                "confidence_score": result.get("confidence_score", 0.7),
            }

        except httpx.HTTPError as e:
            logger.error(f"❌ AI team task failed: {e}")
            # Return fallback response in correct format
            return {
                "task_id": f"fallback-{int(time.time())}",
                "success": False,
                "final_result": "AI team service temporarily unavailable. Please try again later.",
                "model_responses": [],
                "collaboration_summary": f"Error: {str(e)}",
                "confidence_score": 0.0,
            }
        except Exception as e:
            logger.error(f"Unexpected AI team error: {e}")
            return {
                "task_id": f"error-{int(time.time())}",
                "success": False,
                "final_result": "An unexpected error occurred with the AI team service.",
                "model_responses": [],
                "collaboration_summary": f"Unexpected error: {str(e)}",
                "confidence_score": 0.0,
            }

    async def stream_collaborative_task(
        self,
        prompt: str,
        context: str = "",
        required_agents: Optional[List[str]] = None,
        max_iterations: int = 3,
        project_context: str = "ChatterFix",
        fast_mode: bool = False,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream collaborative AI task responses"""
        try:
            request_data = {
                "prompt": prompt,
                "context": context,
                "required_agents": required_agents,
                "max_iterations": max_iterations,
                "project_context": project_context,
                "fast_mode": fast_mode,
            }

            async with self.client.stream(
                "POST", f"{self.base_url}/api/v1/stream", json=request_data
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # Remove "data: " prefix
                            yield data
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            logger.error(f"AI team streaming failed: {e}")
            yield {
                "type": "error",
                "message": f"Streaming failed: {str(e)}",
                "timestamp": time.time(),
            }
        except Exception as e:
            logger.error(f"Unexpected streaming error: {e}")
            yield {
                "type": "error",
                "message": f"Unexpected error: {str(e)}",
                "timestamp": time.time(),
            }

    async def get_available_models(self) -> Dict[str, Any]:
        """Get list of available AI models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/models")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Get models failed: {e}")
            return {"models": [], "total": 0, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected get models error: {e}")
            return {"models": [], "total": 0, "error": str(e)}

    async def get_analytics(self) -> Dict[str, Any]:
        """Get AI team analytics"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/analytics")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Get analytics failed: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected analytics error: {e}")
            return {"error": str(e)}

    async def search_memory(
        self, query: str, max_results: int = 10, search_type: str = "semantic"
    ) -> Dict[str, Any]:
        """Search AI team memory system"""
        try:
            request_data = {
                "query": query,
                "max_results": max_results,
                "search_type": search_type,
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/memory/search", json=request_data
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Memory search failed: {e}")
            return {"results": [], "total_results": 0, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected memory search error: {e}")
            return {"results": [], "total_results": 0, "error": str(e)}

    async def rebuild_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Rebuild search index for AI team memory"""
        try:
            request_data = {"force_rebuild": force_rebuild}

            response = await self.client.post(
                f"{self.base_url}/api/v1/memory/rebuild", json=request_data
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Index rebuild failed: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected rebuild error: {e}")
            return {"status": "error", "error": str(e)}


# Global client instance
_ai_team_client: Optional[AITeamHTTPClient] = None


async def get_ai_team_client() -> AITeamHTTPClient:
    """Get or create AI team HTTP client instance"""
    global _ai_team_client

    if _ai_team_client is None:
        _ai_team_client = AITeamHTTPClient()

    return _ai_team_client


async def execute_ai_team_task(
    prompt: str,
    context: str = "",
    required_agents: Optional[List[str]] = None,
    max_iterations: int = 3,
    project_context: str = "ChatterFix",
    fast_mode: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to execute AI team task

    Args:
        prompt: Task prompt
        context: Additional context
        required_agents: Specific agents to use
        max_iterations: Max collaboration rounds
        project_context: Project name
        fast_mode: Skip refinement for faster responses (~50% faster)
    """
    client = await get_ai_team_client()
    return await client.execute_collaborative_task(
        prompt=prompt,
        context=context,
        required_agents=required_agents,
        max_iterations=max_iterations,
        project_context=project_context,
        fast_mode=fast_mode,
    )


async def check_ai_team_health() -> bool:
    """Check if AI team service is available"""
    try:
        client = await get_ai_team_client()
        health = await client.health_check()
        return health.get("status") == "healthy"
    except Exception:
        return False
