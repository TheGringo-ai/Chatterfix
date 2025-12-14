"""
HTTP Client for AI Team Service
Handles communication with the AI Team microservice for multi-model collaboration
"""
import logging
import os
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx

logger = logging.getLogger(__name__)


class AITeamHTTPClient:
    """HTTP client for communicating with the AI Team Service"""

    def __init__(self):
        self.base_url = os.getenv("AI_TEAM_SERVICE_URL", "http://localhost:8082").rstrip('/')
        self.api_key = os.getenv("AI_TEAM_API_KEY", "dev-key")
        self.timeout = httpx.Timeout(300.0)  # 5 min timeout for AI tasks
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        logger.info(f"AI Team HTTP client initialized: {self.base_url}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def health_check(self) -> dict:
        """Check AI Team service health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"AI Team health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_available_models(self) -> List[dict]:
        """Get list of available AI models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/models")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to get AI models: {e}")
            return []

    async def execute_task(
        self,
        prompt: str,
        context: str = "",
        required_agents: Optional[List[str]] = None,
        max_iterations: int = 3,
        project_context: str = "ChatterFix"
    ) -> dict:
        """
        Execute a collaborative AI task using the full AI team

        Args:
            prompt: The task description
            context: Additional context for the task
            required_agents: Specific agents to use (claude, chatgpt, gemini, grok)
            max_iterations: Maximum collaboration rounds
            project_context: Project name for context

        Returns:
            Task result with agent responses and final answer
        """
        try:
            payload = {
                "prompt": prompt,
                "context": context,
                "required_agents": required_agents or ["claude", "chatgpt"],
                "max_iterations": max_iterations,
                "project_context": project_context
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"AI task execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def stream_task(
        self,
        prompt: str,
        context: str = "",
        required_agents: Optional[List[str]] = None,
        max_iterations: int = 3,
        project_context: str = "ChatterFix"
    ) -> AsyncGenerator[dict, None]:
        """
        Stream a collaborative AI task with real-time responses

        Yields:
            Chunks of agent responses as they're generated
        """
        try:
            payload = {
                "prompt": prompt,
                "context": context,
                "required_agents": required_agents or ["claude", "chatgpt"],
                "max_iterations": max_iterations,
                "project_context": project_context
            }

            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/v1/stream",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        yield data
        except Exception as e:
            logger.error(f"AI task streaming failed: {e}")
            yield {"type": "error", "message": str(e)}

    async def get_task_status(self, task_id: str) -> dict:
        """Get status of a specific task"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {"error": str(e)}

    async def invoke_autonomous_builder(
        self,
        customer_request: str,
        auto_deploy: bool = False
    ) -> dict:
        """
        Invoke the Autonomous ChatterFix Builder

        This triggers the full AutoGen-based autonomous builder that:
        - Analyzes customer requirements
        - Generates and implements features
        - Tests and optionally deploys changes

        Args:
            customer_request: Natural language description of what's needed
            auto_deploy: Whether to automatically deploy changes

        Returns:
            Implementation result
        """
        try:
            payload = {
                "prompt": f"""AUTONOMOUS BUILD REQUEST:
{customer_request}

Instructions:
1. Analyze this requirement using CustomerRequirementAnalyzer
2. Break it into implementation tasks
3. Generate code using FeatureImplementer
4. {'Deploy using DeploymentAgent' if auto_deploy else 'Prepare for manual review'}
5. Provide customer-friendly response

Use all available AI models for best results.""",
                "context": "Autonomous ChatterFix Builder activated",
                "required_agents": ["claude", "chatgpt", "gemini", "grok"],
                "max_iterations": 5,
                "project_context": "ChatterFix Autonomous Build"
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Autonomous builder failed: {e}")
            return {"success": False, "error": str(e)}

    async def code_review(self, code: str, file_path: str = "") -> dict:
        """Request AI-powered code review"""
        try:
            payload = {
                "prompt": f"""Review this code for:
1. Security vulnerabilities
2. Performance issues
3. Best practices
4. Potential bugs

File: {file_path}

```
{code}
```

Provide specific, actionable feedback.""",
                "context": "Code review request",
                "required_agents": ["claude", "chatgpt"],
                "max_iterations": 2,
                "project_context": "ChatterFix Code Review"
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Code review failed: {e}")
            return {"success": False, "error": str(e)}

    async def generate_feature(
        self,
        feature_name: str,
        description: str,
        feature_type: str = "crud"
    ) -> dict:
        """Generate a complete feature using AI team"""
        try:
            payload = {
                "prompt": f"""Generate a complete {feature_type} feature for ChatterFix:

Feature Name: {feature_name}
Description: {description}

Generate:
1. Pydantic models (app/models/)
2. Firestore service (app/services/)
3. FastAPI router (app/routers/)
4. HTML templates (templates/)
5. Unit tests (tests/)

Follow ChatterFix patterns and coding standards.""",
                "context": f"Feature generation: {feature_name}",
                "required_agents": ["claude", "chatgpt", "gemini"],
                "max_iterations": 3,
                "project_context": "ChatterFix Feature Generation"
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Feature generation failed: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_ai_team_client: Optional[AITeamHTTPClient] = None


async def get_ai_team_client() -> AITeamHTTPClient:
    """Get or create AI Team HTTP client instance"""
    global _ai_team_client
    if _ai_team_client is None:
        _ai_team_client = AITeamHTTPClient()
    return _ai_team_client


# Convenience functions
async def execute_ai_task(prompt: str, context: str = "") -> dict:
    """Convenience function for executing AI tasks"""
    client = await get_ai_team_client()
    return await client.execute_task(prompt, context)


async def invoke_autonomous_builder(request: str) -> dict:
    """Convenience function for invoking autonomous builder"""
    client = await get_ai_team_client()
    return await client.invoke_autonomous_builder(request)


async def ai_code_review(code: str, file_path: str = "") -> dict:
    """Convenience function for code review"""
    client = await get_ai_team_client()
    return await client.code_review(code, file_path)


async def check_ai_team_health() -> bool:
    """Check if AI Team service is available"""
    try:
        client = await get_ai_team_client()
        result = await client.health_check()
        return result.get("status") == "healthy"
    except Exception:
        return False
