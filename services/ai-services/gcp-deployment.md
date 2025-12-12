# 🚀 GCP Deployment Strategy for AI Services Microservice

*Designed with AI Team Collaboration (Claude, ChatGPT, Gemini, Grok)*

## Architecture Overview

### Core GCP Services
- **Cloud Run** - Serverless container platform for HTTP APIs
- **Google Kubernetes Engine (GKE)** - Container orchestration for gRPC services  
- **Cloud Build** - CI/CD pipeline for continuous deployment
- **Secret Manager** - Secure API key management
- **Cloud Storage** - AI memory persistence
- **Cloud Load Balancing** - Traffic distribution and scaling
- **Cloud Monitoring** - Performance and health monitoring

### Deployment Pattern: Hybrid Container Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    Internet/External Services            │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Cloud Load Balancer                        │
│                   (HTTPS/TLS)                          │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                Cloud Run (HTTP APIs)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │        AI Services FastAPI                      │   │
│  │  • /ai-team/* - REST endpoints                  │   │
│  │  • /fix-it-fred/* - Analysis APIs              │   │
│  │  • /ai-memory/* - Learning system              │   │
│  │  • /linesmart/* - Training integration         │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │ gRPC Internal
┌─────────────────────▼───────────────────────────────────┐
│           Google Kubernetes Engine (GKE)                │
│  ┌─────────────────────────────────────────────────┐   │
│  │           AI Team gRPC Server                   │   │
│  │  • Multi-model collaboration                   │   │
│  │  • Claude, ChatGPT, Gemini, Grok               │   │
│  │  • Internal communication only                 │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Cloud Storage Buckets                     │
│  • AI Memory persistence (JSON files)                  │
│  • Model artifacts and configurations                  │
│  • Backup and disaster recovery                        │
└─────────────────────────────────────────────────────────┘
```

## Implementation Strategy

### 1. Container Setup

#### Dockerfile for Cloud Run (HTTP APIs)
```dockerfile
# services/ai-services/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Use Cloud Run PORT environment variable
CMD exec uvicorn main:app --host=0.0.0.0 --port=$PORT
```

#### Kubernetes Deployment for gRPC
```yaml
# k8s/ai-team-grpc.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-team-grpc
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-team-grpc
  template:
    metadata:
      labels:
        app: ai-team-grpc
    spec:
      containers:
      - name: ai-team-grpc
        image: gcr.io/PROJECT_ID/ai-team-grpc:latest
        ports:
        - containerPort: 50051
        env:
        - name: GRPC_PORT
          value: "50051"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: ai-team-grpc-service
spec:
  selector:
    app: ai-team-grpc
  ports:
  - port: 50051
    targetPort: 50051
  type: ClusterIP
```

### 2. CI/CD Pipeline with Cloud Build

#### cloudbuild.yaml
```yaml
# CI/CD pipeline for continuous deployment
steps:
  # Build AI Services HTTP container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/ai-services:$COMMIT_SHA', 
           '-f', 'services/ai-services/Dockerfile', './services/ai-services']

  # Build AI Team gRPC container  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/ai-team-grpc:$COMMIT_SHA',
           '-f', 'ai_team/Dockerfile', './ai_team']

  # Run tests
  - name: 'gcr.io/$PROJECT_ID/ai-services:$COMMIT_SHA'
    entrypoint: 'python'
    args: ['-m', 'pytest', 'tests/']

  # Push containers
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/ai-services:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/ai-team-grpc:$COMMIT_SHA']

  # Deploy to Cloud Run (HTTP APIs)
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'ai-services'
    - '--image'
    - 'gcr.io/$PROJECT_ID/ai-services:$COMMIT_SHA'
    - '--platform'
    - 'managed'
    - '--region'
    - 'us-central1'
    - '--allow-unauthenticated'
    - '--max-instances'
    - '100'
    - '--memory'
    - '2Gi'
    - '--cpu'
    - '2'
    - '--set-env-vars'
    - 'AI_TEAM_GRPC_URL=ai-team-grpc-service:50051'

  # Deploy to GKE (gRPC services)
  - name: 'gcr.io/cloud-builders/kubectl'
    args: ['set', 'image', 'deployment/ai-team-grpc', 
           'ai-team-grpc=gcr.io/$PROJECT_ID/ai-team-grpc:$COMMIT_SHA']
    env:
    - 'CLOUDSDK_COMPUTE_ZONE=us-central1-a'
    - 'CLOUDSDK_CONTAINER_CLUSTER=ai-services-cluster'

options:
  logging: CLOUD_LOGGING_ONLY
```

### 3. Secret Management Setup

```bash
# Create secrets for API keys
gcloud secrets create openai-api-key --data-file=openai-key.txt
gcloud secrets create anthropic-api-key --data-file=anthropic-key.txt
gcloud secrets create google-api-key --data-file=google-key.txt
gcloud secrets create xai-api-key --data-file=xai-key.txt

# Grant access to Cloud Run service
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:AI_SERVICES_SA@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 4. Storage Configuration

```python
# app/services/cloud_storage_memory.py
from google.cloud import storage
import json
import os

class CloudStorageMemory:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = os.getenv("AI_MEMORY_BUCKET", "chatterfix-ai-memory")
        self.bucket = self.client.bucket(self.bucket_name)
    
    async def save_memory(self, memory_type: str, data: dict):
        """Save memory data to Cloud Storage"""
        blob = self.bucket.blob(f"memory/{memory_type}.json")
        blob.upload_from_string(json.dumps(data, indent=2))
    
    async def load_memory(self, memory_type: str) -> dict:
        """Load memory data from Cloud Storage"""
        try:
            blob = self.bucket.blob(f"memory/{memory_type}.json")
            if blob.exists():
                return json.loads(blob.download_as_text())
            return {}
        except Exception:
            return {}
```

### 5. Environment-Specific Configuration

```yaml
# config/production.yaml
services:
  ai_services:
    url: "https://ai-services-HASH-uc.a.run.app"
    max_instances: 100
    memory: "2Gi"
    cpu: 2
  
  ai_team_grpc:
    cluster: "ai-services-cluster"
    replicas: 3
    memory: "1Gi"
    cpu: "500m"

storage:
  memory_bucket: "chatterfix-ai-memory-prod"
  model_artifacts: "chatterfix-models"

monitoring:
  enable_tracing: true
  log_level: "INFO"
  alert_policies:
    - error_rate_threshold: 5%
    - latency_threshold: 2000ms
```

### 6. Deployment Commands

```bash
# Initial setup
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com container.googleapis.com cloudbuild.googleapis.com

# Create GKE cluster for gRPC services
gcloud container clusters create ai-services-cluster \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --zone=us-central1-a \
  --enable-autoscaling \
  --max-nodes=10 \
  --min-nodes=1

# Create storage bucket
gsutil mb gs://chatterfix-ai-memory-prod

# Build and deploy
gcloud builds submit --config=cloudbuild.yaml .

# Setup custom domain (optional)
gcloud run domain-mappings create --service=ai-services --domain=api.chatterfix.com
```

### 7. Scaling and Cost Optimization

#### Auto-scaling Configuration
```yaml
# Cloud Run auto-scales 0-100 instances based on:
- Concurrent requests per instance: 80
- CPU utilization: 70%
- Memory utilization: 80%

# GKE horizontal pod autoscaler:
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-team-grpc-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-team-grpc
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Benefits of This Architecture

1. **Continuous Evolution**: Cloud Build automatically deploys code changes
2. **High Availability**: Multi-region deployment with load balancing
3. **Cost Effective**: Pay-per-use Cloud Run + optimized GKE scaling
4. **Secure**: Secret Manager for API keys, private GKE network
5. **Scalable**: Auto-scaling handles traffic spikes
6. **Observable**: Cloud Monitoring and Logging integration
7. **Resilient**: AI Memory backed up to Cloud Storage

## External Service Integration

Services can query the AI Services using:

```bash
# Health check
curl https://ai-services-HASH-uc.a.run.app/health

# AI Team collaboration
curl -X POST https://ai-services-HASH-uc.a.run.app/ai-team/execute \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze this technical issue", "context": "System context"}'

# Fix it Fred analysis
curl -X POST https://ai-services-HASH-uc.a.run.app/fix-it-fred/analyze \
  -H "Content-Type: application/json" \
  -d '{"issue_description": "Motor overheating", "severity": "high"}'

# AI Memory learning
curl -X POST https://ai-services-HASH-uc.a.run.app/ai-memory/check-integration \
  -H "Content-Type: application/json" \
  -d '{"source_service": "external", "target_service": "ai_team", "request_data": {...}}'
```

## Estimated Costs (Monthly)

- Cloud Run (HTTP APIs): $50-200 (based on usage)
- GKE cluster: $100-300 (3 nodes, auto-scaling)
- Cloud Storage: $10-50 (AI memory data)
- Load Balancer: $20
- Secret Manager: $5
- Cloud Build: $10-30 (CI/CD pipelines)

**Total: ~$195-605/month** (scales with usage)

This architecture provides a production-ready, scalable, and cost-effective deployment for your evolving AI Services microservice.