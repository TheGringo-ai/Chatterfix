# AI Team Service

Independent microservice for multi-model AI collaboration with advanced memory system.

## Overview

The AI Team Service provides HTTP REST APIs for:
- Multi-model AI collaboration (Claude, ChatGPT, Gemini, Grok)
- Advanced memory system with mistake prevention
- Real-time streaming responses
- Performance analytics and monitoring

## Architecture

```
AI Team Service (Cloud Run)
├── FastAPI HTTP Server (Port 8080)
├── Multi-Model AI Orchestrator
│   ├── Claude Agent (Anthropic API)
│   ├── ChatGPT Agent (OpenAI API)  
│   ├── Gemini Agent (Google AI API)
│   └── Grok Agent (xAI API)
├── Memory System (Firebase/Firestore)
└── Analytics & Monitoring
```

## API Endpoints

### Core AI Collaboration
- `POST /api/v1/execute` - Execute collaborative AI task
- `POST /api/v1/stream` - Stream collaborative responses
- `GET /api/v1/models` - Get available AI models
- `GET /api/v1/health` - Service health check

### Analytics & Memory
- `GET /api/v1/analytics` - Comprehensive performance analytics
- `POST /api/v1/memory/search` - Search knowledge base
- `POST /api/v1/memory/index/rebuild` - Rebuild search index

## Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API key for ChatGPT
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `GOOGLE_API_KEY` - Google AI API key for Gemini
- `XAI_API_KEY` - xAI API key for Grok
- `INTERNAL_API_KEY` - Internal service authentication

### Optional
- `ENVIRONMENT` - Deployment environment (development/production)
- `AI_MEMORY_BUCKET` - GCS bucket for memory system storage
- `ENABLE_MEMORY_SYSTEM` - Enable/disable memory system (default: true)
- `DEBUG` - Enable debug logging (default: false)

## Deployment

### Local Development
```bash
cd ai-team-service
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8080
```

### Docker
```bash
docker build -t ai-team-service .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  ai-team-service
```

### Cloud Run
```bash
# Deploy using script
chmod +x deploy-ai-team.sh
./deploy-ai-team.sh

# Or manual deployment
gcloud run deploy ai-team-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Usage Examples

### Execute AI Task
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://ai-team-service.run.app/api/v1/execute",
        json={
            "prompt": "How can we improve system performance?",
            "context": "High-traffic web application",
            "max_iterations": 3
        },
        headers={"X-API-Key": "your-api-key"}
    )
    result = response.json()
```

### Stream Collaboration
```javascript
const response = await fetch('/api/v1/stream', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
        prompt: 'Design a new feature',
        context: 'Mobile application'
    })
});

const reader = response.body.getReader();
while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    // Process streaming updates
}
```

## Integration with ChatterFix

The AI Team Service integrates with ChatterFix Core via HTTP REST APIs:

1. ChatterFix imports `app.services.ai_team_http_client`
2. HTTP client handles service discovery and authentication
3. Existing AI Team router proxies requests to the service
4. Backward compatibility maintained for existing endpoints

## Performance & Scaling

- **Horizontal scaling**: Multiple Cloud Run instances
- **Auto-scaling**: 0 to 10 instances based on demand
- **Resource limits**: 2 CPU, 2GB memory per instance
- **Timeout**: 60 minutes for complex AI tasks
- **Concurrency**: 80 requests per instance

## Monitoring

- **Health checks**: `/health` endpoint for service monitoring
- **Analytics**: Real-time performance metrics via `/api/v1/analytics`
- **Logging**: Structured Cloud Logging integration
- **Metrics**: CPU, memory, request latency monitoring

## Security

- **Internal API keys**: Service-to-service authentication
- **CORS**: Configured for ChatterFix domains
- **Secrets**: AI API keys stored in Google Secret Manager
- **Network**: Internal VPC communication (optional)

## Development

### Adding New AI Models
1. Create new agent class in `app/services/ai_orchestrator.py`
2. Implement `AIAgent` interface
3. Add to `setup_default_agents()` method
4. Update configuration with API credentials

### Memory System Integration
1. Implement actual storage backend in `app/services/memory_service.py`
2. Connect to Firebase/Firestore for persistence
3. Enable advanced learning algorithms
4. Add knowledge graph capabilities

## Troubleshooting

### Common Issues
- **API Key errors**: Verify secrets are configured in Cloud Run
- **Timeout errors**: Increase timeout for complex AI tasks
- **Memory errors**: Monitor and adjust resource limits
- **Connection errors**: Check network connectivity and firewall rules

### Debugging
```bash
# View logs
gcloud logs read --service=ai-team-service --limit=50

# Check service status
gcloud run services describe ai-team-service --region=us-central1
```