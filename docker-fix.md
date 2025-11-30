# Docker Reliability Solutions for ChatterFix

## Why Docker Keeps Breaking
1. **Docker Desktop updates** break compatibility
2. **Network timeouts** on image downloads
3. **Large build contexts** slow everything down
4. **Resource limits** cause builds to fail

## Quick Fixes

### 1. Skip Docker for Development
```bash
# Use local Python instead
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 2. Use Pre-built Images (Faster)
```bash
# Pull from registry instead of building
docker pull python:3.11-slim
docker run -it --rm -v $(pwd):/app -w /app -p 8000:8080 python:3.11-slim bash
```

### 3. Cloud Run Direct Deploy (Skip Docker)
```bash
# Deploy directly to Cloud Run without local Docker
gcloud run deploy chatterfix-cmms --source . --region us-central1
```

### 4. Docker Alternatives

**Option A: Podman (Docker replacement)**
```bash
brew install podman
podman build -t chatterfix .
podman run -d -p 8000:8080 chatterfix
```

**Option B: Lima + nerdctl**
```bash
brew install lima
limactl start docker
nerdctl build -t chatterfix .
```

## Docker Settings to Fix Issues

### In Docker Desktop Settings:
1. **Resources** → Increase memory to 4GB+
2. **Advanced** → Enable "Use containerd for pulling and storing images"
3. **General** → Disable "Send usage statistics"

### Network Fixes:
```bash
# Reset Docker network
docker system prune -a
docker network prune

# Use different registry
docker pull --platform linux/amd64 python:3.11-slim
```

## Immediate Workaround
Since your main goal is deployment, focus on Cloud Run which builds in the cloud:

```bash
# Push code and let GCP build it
git push
# Triggers GitHub Actions → Cloud Build → Cloud Run
```

This avoids local Docker entirely while still containerizing for production.