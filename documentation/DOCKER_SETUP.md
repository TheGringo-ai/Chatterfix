# 🐳 ChatterFix CMMS - Docker Setup Guide

## Quick Start (5 minutes)

### 1. Prerequisites
- Docker Desktop installed and running
- At least 8GB RAM available for Docker
- 10GB free disk space

### 2. Setup Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials (optional for basic testing)
# Minimum required: GITHUB_PAT (if using GitHub features)
```

### 3. Start ChatterFix

```bash
# Start all services (ChatterFix + Ollama)
docker compose up -d

# View logs
docker compose logs -f

# Or start and watch logs simultaneously
docker compose up
```

### 4. Access Your Application

**Main Application:**
- URL: http://localhost:8080
- Health Check: http://localhost:8080/health

**Ollama API:**
- URL: http://localhost:11434
- Models: http://localhost:11434/api/tags

### 5. First-Time Model Download

The first time you run the containers, Ollama will download:
- **Mistral 7B** (~4GB) - Fast, efficient model
- **Llama3 8B** (~4.7GB) - Advanced model

This takes 10-20 minutes depending on your internet speed.

## Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart services
docker compose restart

# View logs
docker compose logs -f chatterfix
docker compose logs -f ollama

# Rebuild after code changes
docker compose up -d --build

# Remove everything (including volumes)
docker compose down -v

# Check service status
docker compose ps

# Execute command in running container
docker compose exec chatterfix python -c "import sys; print(sys.version)"
```

## Development Workflow

### Hot Reload Development

Your local code is mounted into the container, so changes to Python files will be reflected immediately (if using a dev server with auto-reload).

```bash
# Watch logs while developing
docker compose logs -f chatterfix
```

### Testing AI Features

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test ChatterFix health
curl http://localhost:8080/health

# Test AI endpoint (if available)
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how can you help me?"}'
```

## Troubleshooting

### Ollama models not downloading
```bash
# Check Ollama logs
docker compose logs ollama

# Manually pull models
docker compose exec ollama ollama pull mistral:7b
docker compose exec ollama ollama pull llama3:8b
```

### ChatterFix won't start
```bash
# Check logs
docker compose logs chatterfix

# Rebuild container
docker compose up -d --build chatterfix

# Check if port 8080 is available
lsof -i :8080
```

### Out of disk space
```bash
# Clean up unused Docker resources
docker system prune -a --volumes

# Remove just ChatterFix volumes
docker compose down -v
```

### Port conflicts
If ports 8080 or 11434 are already in use, edit `docker-compose.yml`:

```yaml
ports:
  - "8081:8080"  # Change 8080 to 8081 (or any free port)
```

## Production Deployment

For production, you may want to:

1. **Use external database** instead of SQLite
2. **Remove volume mounts** for code (copy instead)
3. **Add nginx** reverse proxy
4. **Configure SSL/TLS** certificates
5. **Set resource limits** in docker-compose.yml

Example resource limits:
```yaml
services:
  chatterfix:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Architecture

```
┌─────────────────────┐
│   Browser/Client    │
└──────────┬──────────┘
           │
           ▼
    ┌─────────────┐
    │ Port 8080   │
    │ ChatterFix  │ ◄─── Your Application
    │   (FastAPI) │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ Port 11434  │
    │   Ollama    │ ◄─── Local LLM Engine
    │ (Mistral,   │
    │  Llama3)    │
    └─────────────┘
```

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_PAT` | GitHub Personal Access Token | No | - |
| `GCLOUD_PROJECT` | GCP Project ID | No | fredfix |
| `OLLAMA_HOST` | Ollama service URL | Auto | http://ollama:11434 |
| `OPENAI_API_KEY` | OpenAI API key | No | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | No | - |
| `XAI_API_KEY` | xAI API key | No | - |
| `SERVICE_MODE` | Service mode (default/unified_backend/unified_ai) | No | default |
| `PORT` | Application port | No | 8080 |

## Next Steps

1. ✅ Start containers: `docker compose up -d`
2. ✅ Wait for Ollama models to download (check logs)
3. ✅ Access http://localhost:8080
4. ✅ Test AI features with local Ollama models
5. ✅ Customize .env for your needs

## Support

- **Documentation:** See other README files in this repo
- **Logs:** `docker compose logs -f`
- **Issues:** Check GitHub issues
- **Health Check:** http://localhost:8080/health
