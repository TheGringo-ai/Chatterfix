---
description: Invoke the multi-model AI team to collaborate on a task (usage: /ai-team <task>; optional args supported)
---

# AI Team Collaboration Workflow

## Quick usage

Run this command from Claude Code:

```text
/ai-team <TASK_DESCRIPTION>
```

Any text after `/ai-team` will be passed in as `$ARGUMENTS`.

### Suggested prompt to Claude

Use the AI team workflow below to solve: $ARGUMENTS

Invoke the multi-model AI team for complex problem solving.

## Available AI Team Members

Based on the autogen framework in `ai_team/`:

1. **Claude (Lead Architect)**
   - Architecture design
   - Code analysis
   - Planning and strategy

2. **ChatGPT (Senior Developer)**
   - Coding implementation
   - Debugging
   - Optimization

3. **Gemini (Creative Innovator)**
   - UI/UX design
   - Creative solutions
   - Innovation

4. **Grok (Strategic Reasoner)**
   - Complex reasoning
   - Analysis
   - Strategy

5. **Grok Code (Rapid Coder)**
   - Fast implementation
   - Quick fixes
   - Optimization

## Collaboration Modes

From `ai_team/collaboration_engine.py`:

- **parallel**: All agents work simultaneously
- **sequential**: Agents work in order
- **devils_advocate**: Critical analysis mode
- **consensus_building**: Reach agreement
- **peer_review**: Cross-review solutions
- **brainstorming**: Generate ideas
- **critical_analysis**: Deep analysis

## Usage

### For Architecture Decisions
Use Claude + Grok for architectural analysis and strategic planning.

### For Bug Fixes
Use ChatGPT + Grok Code for rapid debugging and fixes.

### For New Features
Use all agents in brainstorming mode, then Claude for final design.

### For Code Reviews
Use peer_review mode with all available agents.

## Memory Integration

The AI team uses the Ultimate Memory System to:
- Recall past solutions
- Avoid repeated mistakes
- Apply learned patterns
- Track solution success rates

## Invoking the Team

For complex tasks, consider invoking through:
```python
from ai_team.autogen_framework import AutogenFramework

framework = AutogenFramework()
result = await framework.collaborate(
    task="Your task description",
    mode="consensus_building",
    agents=["claude", "chatgpt", "gemini"]
)
```

## Task Routing

The `ai_team/task_routing.py` automatically routes tasks to the best agent based on:
- Task type (coding, analysis, creative, etc.)
- Agent capabilities
- Historical success rates
- Current workload

## Cross-Application Learning

Solutions found here are shared across:
- ChatterFix CMMS
- Fix it Fred
- LineSmart Training

This ensures patterns learned in one app benefit all apps.
