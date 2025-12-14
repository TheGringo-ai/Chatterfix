#!/usr/bin/env python3
"""
AI Team MCP Server - Model Context Protocol Server for Claude Code
===================================================================

This MCP server exposes the ChatterFix AI Team's capabilities directly
to Claude Code, allowing seamless integration of multi-model AI collaboration.

Installation:
    Add to your Claude Code settings (~/.claude/settings.json):

    {
      "mcpServers": {
        "ai-team": {
          "command": "python",
          "args": ["/path/to/ChatterFix/mcp_servers/ai_team_mcp.py"],
          "env": {
            "AI_TEAM_SERVICE_URL": "http://localhost:8082",
            "AI_TEAM_API_KEY": "your-api-key"
          }
        }
      }
    }

Available Tools:
    - ai_team_execute: Execute collaborative AI tasks
    - ai_team_build: Invoke the Autonomous Builder
    - ai_team_review: AI-powered code review
    - ai_team_generate: Generate complete features
    - ai_team_health: Check service health
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP SDK imports (fallback to simple implementation if not available)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Add project root for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AITeamMCPServer:
    """MCP Server for AI Team integration"""

    def __init__(self):
        self.base_url = os.getenv("AI_TEAM_SERVICE_URL", "http://localhost:8082")
        self.api_key = os.getenv("AI_TEAM_API_KEY", "dev-key")

    async def get_client(self):
        """Get HTTP client for AI team service"""
        import httpx
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=300.0
        )

    async def execute_task(
        self,
        prompt: str,
        context: str = "",
        agents: Optional[List[str]] = None,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """Execute a collaborative AI task"""
        async with await self.get_client() as client:
            response = await client.post(
                "/api/v1/execute",
                json={
                    "prompt": prompt,
                    "context": context,
                    "required_agents": agents or ["claude", "chatgpt"],
                    "max_iterations": max_iterations,
                    "project_context": "ChatterFix"
                }
            )
            response.raise_for_status()
            return response.json()

    async def invoke_builder(self, request: str, auto_deploy: bool = False) -> Dict[str, Any]:
        """Invoke the Autonomous ChatterFix Builder"""
        prompt = f"""AUTONOMOUS BUILD REQUEST:
{request}

Instructions:
1. Analyze this requirement using CustomerRequirementAnalyzer
2. Break it into implementation tasks
3. Generate code using FeatureImplementer
4. {'Deploy using DeploymentAgent' if auto_deploy else 'Prepare for manual review'}
5. Provide customer-friendly response

Use all available AI models for best results."""

        async with await self.get_client() as client:
            response = await client.post(
                "/api/v1/execute",
                json={
                    "prompt": prompt,
                    "context": "Autonomous ChatterFix Builder activated",
                    "required_agents": ["claude", "chatgpt", "gemini", "grok"],
                    "max_iterations": 5,
                    "project_context": "ChatterFix Autonomous Build"
                }
            )
            response.raise_for_status()
            return response.json()

    async def code_review(self, code: str, file_path: str = "") -> Dict[str, Any]:
        """AI-powered code review"""
        prompt = f"""Review this code for:
1. Security vulnerabilities
2. Performance issues
3. Best practices
4. Potential bugs

File: {file_path}

```
{code}
```

Provide specific, actionable feedback."""

        async with await self.get_client() as client:
            response = await client.post(
                "/api/v1/execute",
                json={
                    "prompt": prompt,
                    "context": "Code review request",
                    "required_agents": ["claude", "chatgpt"],
                    "max_iterations": 2,
                    "project_context": "ChatterFix Code Review"
                }
            )
            response.raise_for_status()
            return response.json()

    async def generate_feature(
        self,
        feature_name: str,
        description: str,
        feature_type: str = "crud"
    ) -> Dict[str, Any]:
        """Generate a complete feature"""
        prompt = f"""Generate a complete {feature_type} feature for ChatterFix:

Feature Name: {feature_name}
Description: {description}

Generate:
1. Pydantic models (app/models/)
2. Firestore service (app/services/)
3. FastAPI router (app/routers/)
4. HTML templates (templates/)
5. Unit tests (tests/)

Follow ChatterFix patterns and coding standards."""

        async with await self.get_client() as client:
            response = await client.post(
                "/api/v1/execute",
                json={
                    "prompt": prompt,
                    "context": f"Feature generation: {feature_name}",
                    "required_agents": ["claude", "chatgpt", "gemini"],
                    "max_iterations": 3,
                    "project_context": "ChatterFix Feature Generation"
                }
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> Dict[str, Any]:
        """Check AI Team service health"""
        async with await self.get_client() as client:
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()


# Define MCP tools
TOOLS = [
    {
        "name": "ai_team_execute",
        "description": "Execute a collaborative AI task using the full AI team (Claude, ChatGPT, Gemini, Grok). Use this for complex tasks requiring multiple AI perspectives.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The task or question for the AI team"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context for the task"
                },
                "agents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific agents to use (claude, chatgpt, gemini, grok)"
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "Maximum collaboration rounds (default: 3)"
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "ai_team_build",
        "description": "Invoke the Autonomous ChatterFix Builder to automatically implement a feature from a natural language request. This uses all AI models to analyze, design, and generate code.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "Natural language description of the feature to build"
                },
                "auto_deploy": {
                    "type": "boolean",
                    "description": "Whether to automatically deploy changes (default: false)"
                }
            },
            "required": ["request"]
        }
    },
    {
        "name": "ai_team_review",
        "description": "Request an AI-powered code review using multiple AI models for comprehensive analysis of security, performance, and best practices.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The code to review"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file being reviewed (for context)"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "ai_team_generate",
        "description": "Generate a complete feature (models, services, routers, templates, tests) using the AI team.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "feature_name": {
                    "type": "string",
                    "description": "Name of the feature (snake_case)"
                },
                "description": {
                    "type": "string",
                    "description": "Description of what the feature should do"
                },
                "feature_type": {
                    "type": "string",
                    "enum": ["crud", "api", "ui", "service"],
                    "description": "Type of feature to generate"
                }
            },
            "required": ["feature_name", "description"]
        }
    },
    {
        "name": "ai_team_health",
        "description": "Check if the AI Team service is healthy and available.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> str:
    """Handle a tool call from Claude Code"""
    server = AITeamMCPServer()

    try:
        if name == "ai_team_execute":
            result = await server.execute_task(
                prompt=arguments["prompt"],
                context=arguments.get("context", ""),
                agents=arguments.get("agents"),
                max_iterations=arguments.get("max_iterations", 3)
            )
        elif name == "ai_team_build":
            result = await server.invoke_builder(
                request=arguments["request"],
                auto_deploy=arguments.get("auto_deploy", False)
            )
        elif name == "ai_team_review":
            result = await server.code_review(
                code=arguments["code"],
                file_path=arguments.get("file_path", "")
            )
        elif name == "ai_team_generate":
            result = await server.generate_feature(
                feature_name=arguments["feature_name"],
                description=arguments["description"],
                feature_type=arguments.get("feature_type", "crud")
            )
        elif name == "ai_team_health":
            result = await server.health_check()
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


def run_server():
    """Run the MCP server"""
    if MCP_AVAILABLE:
        # Use proper MCP SDK
        server = Server("ai-team")

        @server.list_tools()
        async def list_tools():
            return [Tool(**tool) for tool in TOOLS]

        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            result = await handle_tool_call(name, arguments)
            return [TextContent(type="text", text=result)]

        async def main():
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream)

        asyncio.run(main())
    else:
        # Simple fallback - just print available tools
        print("MCP SDK not installed. Install with: pip install mcp")
        print("\nAvailable tools:")
        for tool in TOOLS:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")


if __name__ == "__main__":
    run_server()
