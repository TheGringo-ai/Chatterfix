# AI Services Architecture

## Overview

ChatterFix uses a unified AI architecture that integrates multiple AI models for different use cases.

## Canonical Services (USE THESE)

### 1. `ai_service.py` - Fix-it-Fred AI Assistant
**Primary AI service for maintenance consulting**
- Powers the Fix-it-Fred maintenance assistant
- Uses OpenAI GPT-4 for maintenance advice
- Provides safety-first, actionable solutions
- Used by: `/ai/*` routes, work order AI suggestions

### 2. `ai_team_intelligence.py` - AI Team Intelligence
**Cross-model AI collaboration and learning system**
- Automated learning from errors
- Cross-model consensus system
- Real-time context sharing
- Proactive issue prediction
- Used by: `/ai/context`, `/ai/consensus`, `/ai/health`

### 3. `gemini_service.py` - Google Gemini Integration
**Vision and multimodal AI capabilities**
- Image analysis and OCR
- Part recognition
- Equipment condition analysis
- Voice command processing
- Used by: `/ai/analyze-image`, `/ai/voice-command`

## Deprecated/Standalone Services

### `/ai_team/` Directory (STANDALONE - DO NOT USE DIRECTLY)
This is a standalone gRPC-based AI team service. It's designed to run as a separate microservice.
- Only use if deploying as separate service
- Configure with `DISABLE_AI_TEAM_GRPC=false`
- Requires separate deployment

### `/ai-team-service/` Directory (STANDALONE - DO NOT USE DIRECTLY)
This is an HTTP-based AI team service for Cloud Run deployment.
- Only use if running as separate Cloud Run service
- Configure with `USE_AI_TEAM_HTTP=true` and `AI_TEAM_SERVICE_URL`
- Requires separate deployment

## Configuration

### Environment Variables

```bash
# Core AI Services
OPENAI_API_KEY=sk-...          # For Fix-it-Fred (ai_service.py)
GEMINI_API_KEY=AIzaSy...       # For vision/OCR (gemini_service.py)
XAI_API_KEY=xai-...            # For Grok integration (optional)
ANTHROPIC_API_KEY=sk-ant-...   # For Claude integration (optional)

# AI Team Configuration (for standalone services)
DISABLE_AI_TEAM_GRPC=true      # Disable gRPC AI team (use HTTP instead)
USE_AI_TEAM_HTTP=false         # Enable HTTP AI team client
AI_TEAM_SERVICE_URL=           # URL of AI team HTTP service
```

## Router Usage

| Router | Service | Purpose |
|--------|---------|---------|
| `ai.py` | ai_service.py, gemini_service.py | Main AI endpoints |
| `ai_team.py` | ai_team_intelligence.py | Team intelligence API |
| `ai_team_collaboration.py` | ai_team_http_client.py | External AI team |

## Adding New AI Features

1. Add to existing services when possible:
   - Maintenance advice → `ai_service.py`
   - Vision/OCR → `gemini_service.py`
   - Learning/Memory → `ai_team_intelligence.py`

2. If new service needed:
   - Create in `app/services/`
   - Follow singleton pattern
   - Add graceful fallback when API unavailable
   - Update this README

## Service Dependencies

```
ai.py (router)
├── ai_service.py (Fix-it-Fred)
│   └── OpenAI API
├── gemini_service.py (Vision)
│   └── Google Gemini API
└── ai_team_intelligence.py (Learning)
    └── Firestore (memory storage)
```

## Best Practices

1. **Always use environment variables** for API keys
2. **Implement graceful fallbacks** when APIs unavailable
3. **Log all AI interactions** for debugging
4. **Cache responses** when appropriate
5. **Rate limit** external API calls
