#!/bin/bash

# AI Team Service Deployment Script
# Deploys the independent AI Team service to Google Cloud Run

set -e

# Configuration
PROJECT_ID="fredfix"
SERVICE_NAME="ai-team-service"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
PLATFORM="linux/amd64"

echo "🤖 AI Team Service Deployment"
echo "=================================="
echo "🎯 Project: $PROJECT_ID"
echo "🎯 Service: $SERVICE_NAME"
echo "🎯 Region: $REGION"
echo "🎯 Image: $IMAGE_NAME"

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Must be run from ai-team-service directory"
    exit 1
fi

# Authenticate with Google Cloud
echo "🔐 Checking Google Cloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with Google Cloud. Please run: gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

echo "🏗️  Building Docker image..."
docker build --platform $PLATFORM -t $IMAGE_NAME:latest .

echo "📤 Pushing to Container Registry..."
docker push $IMAGE_NAME:latest

echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 50 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "INTERNAL_API_KEY=chatterfix-ai-team-2025-secure-key" \
    --set-env-vars "FIRESTORE_PROJECT_ID=${PROJECT_ID}" \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
    --set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY}" \
    --set-env-vars "XAI_API_KEY=${XAI_API_KEY}" \
    --set-env-vars "LOG_LEVEL=INFO" \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "🔍 Verifying deployment..."
sleep 5

# Test health endpoint
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "⚠️  Health check failed, but service is deployed"
fi

# Test basic API
if curl -f "$SERVICE_URL/api/v1/models" -H "Authorization: Bearer chatterfix-ai-team-2025-secure-key" > /dev/null 2>&1; then
    echo "✅ API endpoints accessible"
else
    echo "⚠️  API endpoints may not be ready yet"
fi

echo ""
echo "🎉 AI Team Service Deployment Complete!"
echo "======================================"
echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Health Check: $SERVICE_URL/health"
echo "🤖 API Docs: $SERVICE_URL/docs"
echo "🔧 Models: $SERVICE_URL/api/v1/models"
echo "📈 Analytics: $SERVICE_URL/api/v1/analytics"
echo ""
echo "🔑 API Key: chatterfix-ai-team-2025-secure-key"
echo ""
echo "📝 Next steps:"
echo "1. Update ChatterFix environment variables:"
echo "   AI_TEAM_SERVICE_URL=$SERVICE_URL"
echo "   INTERNAL_API_KEY=chatterfix-ai-team-2025-secure-key"
echo "   DISABLE_AI_TEAM_GRPC=true"
echo "2. Deploy updated ChatterFix with HTTP client"
echo "3. Test integration between services"