---
description: Invoke the multi-model AI team to collaborate on a task (usage: /ai-team <task>; optional args supported)
---

# AI Team Collaboration Workflow

## Quick usage

```text
/ai-team <TASK_DESCRIPTION>
```

Any text after `/ai-team` will be passed as `$ARGUMENTS`.

---

## 🧠 Self-Orchestrating AI Team

This system automatically decides how to handle your request:

### Complexity Routing (Automatic)

| Score | Tier | What Happens |
|-------|------|--------------|
| 1-3 | SIMPLE | Single fast model (Gemini Flash) |
| 4-6 | MEDIUM | Two models collaborate |
| 7-10 | COMPLEX | Full team consensus debate |

### Task: $ARGUMENTS

---

## Step 1: Index Codebase Context

First, gather relevant context from the codebase:

```python
# Run this to get codebase context
from app.services.codebase_indexer import get_codebase_indexer

indexer = get_codebase_indexer()
context = indexer.get_context_for_query("$ARGUMENTS")
print(context)
```

Or manually check relevant files based on the task.

---

## Step 2: Assess Complexity

Rate the task complexity (1-10):

**Simple (1-3):**
- Typo fixes, formatting
- Simple queries ("Where is X?")
- Single-line changes

**Medium (4-6):**
- Write a function
- Add a field to a model
- Fix a specific bug

**Complex (7-10):**
- Architecture changes
- Multi-file refactors
- Security-critical changes
- New features

---

## Step 3: Route to Appropriate Team

### For SIMPLE tasks:
Use a single model (you, Claude) to solve directly.

### For MEDIUM tasks:
1. Propose solution
2. Self-review for issues
3. Implement

### For COMPLEX tasks:
Run the Consensus Engine:

```python
from app.services.ai_consensus_engine import get_consensus_engine
from app.services.codebase_indexer import get_codebase_indexer

indexer = get_codebase_indexer()
context = indexer.get_context_for_query("$ARGUMENTS")

engine = get_consensus_engine()
result = await engine.reach_consensus(
    user_request="$ARGUMENTS",
    codebase_context=context,
    min_models=3  # Full team
)

print(result.final_answer)
print(result.debate_summary)
```

---

## AI Team Roles

| Agent | Role | Specialty |
|-------|------|-----------|
| **Claude** | Lead Architect | Architecture, planning, analysis |
| **Gemini** | Creative Innovator | UI/UX, creative solutions |
| **Grok** | Strategic Reasoner | Complex reasoning, strategy |
| **ChatGPT** | Senior Developer | Coding, debugging, optimization |

---

## Consensus Debate Flow (Complex Tasks)

```
┌─────────────────────────────────────────┐
│  1. PROPOSER (Gemini)                   │
│     Creates initial solution            │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  2. CRITIC (ChatGPT)                    │
│     Reviews for bugs, security issues   │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  3. JUDGE (Grok)                        │
│     Decides if critique is valid        │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  4. SYNTHESIZER (Gemini)                │
│     Creates final answer                │
└─────────────────────────────────────────┘
```

---

## Memory Integration

The AI team uses the knowledge base to:
- ✅ Recall past solutions from Firestore
- ✅ Avoid repeated mistakes (CLAUDE.md lessons)
- ✅ Apply learned patterns
- ✅ Track solution success rates

---

## Key Files

| File | Purpose |
|------|---------|
| `app/services/codebase_indexer.py` | Maps entire codebase |
| `app/services/ai_consensus_engine.py` | Multi-model debate |
| `app/services/ai_router.py` | Complexity routing |
| `app/services/ai_team_intelligence.py` | Learning system |
| `scripts/ai-precommit-review.py` | Mistake detection |

---

## Examples

**Simple:** "Fix the typo in auth.py line 45"
→ Route to single model, fix directly

**Medium:** "Add a 'priority' field to the Asset model"
→ Two models collaborate, implement with review

**Complex:** "Implement offline mode for the mobile app"
→ Full team consensus: propose → critique → judge → synthesize

---

## Now executing for: $ARGUMENTS
