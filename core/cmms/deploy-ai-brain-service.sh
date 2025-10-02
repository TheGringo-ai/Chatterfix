#!/bin/bash

echo "🧠 Deploying ChatterFix AI Brain Service - Mars-Level AI..."

# Set environment variables
export PROJECT_ID="fredfix"
export SERVICE_NAME="chatterfix-ai-brain"
export REGION="us-central1"

# Create a temporary directory for AI brain service
echo "📦 Preparing AI brain service for deployment..."
rm -rf /tmp/ai-brain-service
mkdir -p /tmp/ai-brain-service

# Copy AI brain service files
cp ai_brain_service.py /tmp/ai-brain-service/main.py
cp ai_brain_service_requirements.txt /tmp/ai-brain-service/requirements.txt

# Create Dockerfile for AI brain service
cat > /tmp/ai-brain-service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8084
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]
EOF

# Deploy AI brain service
echo "📦 Deploying AI brain service to Cloud Run..."
cd /tmp/ai-brain-service
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8084 \
    --set-env-vars AI_PROVIDER=grok \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300s \
    --max-instances 10 \
    --project $PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' --project $PROJECT_ID)

echo "✅ AI Brain service deployment completed!"
echo "✅ AI Brain Service URL: $SERVICE_URL"

# Save URL to file
echo "AI_BRAIN_SERVICE_URL=$SERVICE_URL" > .env.ai_brain

# Health check
echo "🏥 Performing health check..."
sleep 5
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" || echo "Health check failed")
echo "Health response: $HEALTH_RESPONSE"

echo ""
echo "🎉 AI Brain Service Deployment Summary:"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION" 
echo "   URL: $SERVICE_URL"
echo "   Features: Mars-Level AI, Multi-AI Orchestration, Quantum Analytics"
echo ""
echo "✅ AI Brain service URL saved to .env.ai_brain"
echo "✅ ChatterFix AI Brain Service deployment completed!"