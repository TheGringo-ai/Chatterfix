# AI Team MCP Server

This MCP (Model Context Protocol) server exposes the ChatterFix AI Team's capabilities directly to Claude Code.

## Installation

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "ai-team": {
      "command": "python",
      "args": ["/Users/fredtaylor/ChatterFix/mcp_servers/ai_team_mcp.py"],
      "env": {
        "AI_TEAM_SERVICE_URL": "http://localhost:8082",
        "AI_TEAM_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Requirements

```bash
pip install mcp httpx
```

## Available Tools

### ai_team_execute
Execute a collaborative AI task using the full AI team (Claude, ChatGPT, Gemini, Grok).

### ai_team_build
Invoke the Autonomous ChatterFix Builder to automatically implement a feature from a natural language request.

### ai_team_review
Request an AI-powered code review using multiple AI models.

### ai_team_generate
Generate a complete feature (models, services, routers, templates, tests).

### ai_team_health
Check if the AI Team service is healthy.

## Starting the AI Team Service

```bash
# Option 1: Docker Compose (recommended)
docker-compose up -d ai-team-service

# Option 2: Direct Python
cd ai-team-service
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8082
```

## Usage Examples

Once configured, you can use the AI team directly from Claude Code:

```
# In Claude Code conversation:
"Use the AI team to review this code for security issues"
"Have the AI team generate a budget tracking feature"
"Ask the AI team to optimize the database queries"
```
