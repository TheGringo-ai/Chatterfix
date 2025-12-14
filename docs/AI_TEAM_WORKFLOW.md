# AI Team Workflow Guide

## Complete Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLAUDE CODE                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        MCP Server Integration                            ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐││
│  │  │ai_team_build│ │ai_team_exec │ │ai_team_rev  │ │ai_team_generate     │││
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘││
│  └─────────┼───────────────┼───────────────┼───────────────────┼───────────┘│
│            └───────────────┴───────────────┴───────────────────┘            │
│                                     │                                        │
│                              HTTP REST API                                   │
│                                     │                                        │
└─────────────────────────────────────┼────────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI TEAM SERVICE (:8082)                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        AutoGen Framework                                 ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ││
│  │  │ ClaudeAgent  │  │ ChatGPTAgent │  │ GeminiAgent  │  │  GrokAgent  │  ││
│  │  │ (Architect)  │  │ (Developer)  │  │ (Innovator)  │  │ (Reasoner)  │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    Autonomous Builder (AutoGen GroupChat)               ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐││
│  │  │RequirementAnalyzer│ │FeatureImplementer│  │    DeploymentAgent    │ ││
│  │  └──────────────────┘  └──────────────────┘  └────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         AI Team Tools                                    ││
│  │  UIGenerator │ DatabaseGen │ TestGen │ GitTools │ CodeReviewer         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     Memory System (Never Repeat Mistakes)               ││
│  │  ConversationHistory │ MistakePatterns │ SolutionKnowledgeBase         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Starting the AI Team

### Option 1: Docker Compose (Recommended)

```bash
# Start all services including AI Team
docker-compose up -d

# Or just the AI Team service
docker-compose up -d ai-team-service redis
```

### Option 2: Direct Python

```bash
cd ai-team-service
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8082
```

## Using the AI Team

### Method 1: CLI Tool

```bash
# Execute a collaborative task
python scripts/ai_team_cli.py execute "Analyze the codebase for performance issues"

# Invoke the Autonomous Builder
python scripts/ai_team_cli.py build "I need expense tracking for maintenance budgets"

# Request code review
python scripts/ai_team_cli.py review app/routers/work_orders.py

# Generate a feature
python scripts/ai_team_cli.py generate inventory_alerts "Alert system for low stock levels"

# Check health
python scripts/ai_team_cli.py health

# List available AI models
python scripts/ai_team_cli.py models
```

### Method 2: Python API

```python
from app.clients import (
    execute_ai_task,
    invoke_autonomous_builder,
    ai_code_review,
    check_ai_team_health
)

# Execute a task
result = await execute_ai_task(
    "Optimize the database queries in work_orders.py",
    context="Focus on N+1 query problems"
)

# Invoke the autonomous builder
result = await invoke_autonomous_builder(
    "Add a calendar view for scheduled maintenance"
)

# Request code review
with open("app/routers/work_orders.py") as f:
    code = f.read()
result = await ai_code_review(code, "app/routers/work_orders.py")
```

### Method 3: MCP Server (Claude Code Native)

Add to `~/.claude/settings.json`:

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

Then in Claude Code conversations:
- "Use the AI team to review this code"
- "Have the AI team build a budget tracking feature"
- "Ask the AI team to optimize database queries"

### Method 4: Direct HTTP API

```bash
# Health check
curl http://localhost:8082/health

# Execute task
curl -X POST http://localhost:8082/api/v1/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "prompt": "Analyze this codebase structure",
    "required_agents": ["claude", "chatgpt"],
    "max_iterations": 3
  }'

# Stream task (Server-Sent Events)
curl -X POST http://localhost:8082/api/v1/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "prompt": "Generate a complete inventory feature",
    "required_agents": ["claude", "chatgpt", "gemini"]
  }'
```

## AI Team Capabilities

### Multi-Model Collaboration
- **Claude**: Lead architect, analysis, planning
- **ChatGPT**: Senior developer, coding, debugging
- **Gemini**: Creative innovator, UI/UX, solutions
- **Grok**: Strategic reasoner, analysis, strategy

### Autonomous Building
The Autonomous Builder uses AutoGen GroupChat to:
1. **Analyze Requirements** - Break down customer requests
2. **Design Architecture** - Plan implementation approach
3. **Generate Code** - Create models, services, routers, templates
4. **Test & Deploy** - Run tests and deploy changes
5. **Communicate** - Provide friendly customer feedback

### Memory System
Never repeat mistakes:
- All conversations stored
- Mistake patterns tracked
- Solution patterns catalogued
- Proactive issue prevention

## Example Workflow

```bash
# 1. Start the AI Team
docker-compose up -d ai-team-service redis

# 2. Check health
python scripts/ai_team_cli.py health

# 3. Build a feature
python scripts/ai_team_cli.py build "I need a dashboard showing maintenance costs by department"

# 4. Review the generated code
python scripts/ai_team_cli.py review app/routers/costs.py

# 5. Deploy (if auto_deploy enabled)
# Or manually review and commit
```

## Environment Variables

```bash
# AI Team Service
AI_TEAM_SERVICE_URL=http://localhost:8082
AI_TEAM_API_KEY=your-api-key

# API Keys for AI Models
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
XAI_API_KEY=...
```
