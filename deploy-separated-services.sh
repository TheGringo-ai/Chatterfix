#!/bin/bash

# Combined Deployment Script for Separated ChatterFix Services
# Deploys AI Team Service and ChatterFix Core as separate microservices

set -e

PROJECT_ID="fredfix"
REGION="us-central1"

echo "🚀 ChatterFix Microservices Deployment"
echo "======================================"
echo "🎯 Project: $PROJECT_ID"
echo "🎯 Region: $REGION"
echo ""
echo "This will deploy:"
echo "1. 🤖 AI Team Service (independent microservice)"
echo "2. 🏭 ChatterFix Core (main CMMS application)"

# Authenticate with Google Cloud
echo ""
echo "🔐 Checking Google Cloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with Google Cloud. Please run: gcloud auth login"
    exit 1
fi

gcloud config set project $PROJECT_ID

# Phase 1: Deploy AI Team Service
echo ""
echo "📋 Phase 1: Deploying AI Team Service..."
echo "========================================"

if [ ! -d "ai-team-service" ]; then
    echo "❌ Error: ai-team-service directory not found"
    echo "Please ensure you're running this script from the ChatterFix root directory"
    exit 1
fi

cd ai-team-service
echo "🏗️  Building and deploying AI Team Service..."
./deploy-ai-team.sh

# Get the AI Team service URL for ChatterFix configuration
AI_TEAM_SERVICE_URL=$(gcloud run services describe ai-team-service --region=$REGION --format="value(status.url)")
echo "✅ AI Team Service deployed at: $AI_TEAM_SERVICE_URL"

cd ..

# Phase 2: Deploy ChatterFix Core with AI Team HTTP integration
echo ""
echo "📋 Phase 2: Deploying ChatterFix Core..."
echo "======================================="

echo "🔧 Configuring ChatterFix to use AI Team HTTP service..."

# Update environment variables for ChatterFix
export AI_TEAM_SERVICE_URL="$AI_TEAM_SERVICE_URL"
export DISABLE_AI_TEAM_GRPC="true"
export INTERNAL_API_KEY="ai-team-service-key-change-me"

echo "🏗️  Building ChatterFix Core with updated configuration..."
docker build --platform linux/amd64 -t gcr.io/$PROJECT_ID/gringo-core:latest .

echo "📤 Pushing ChatterFix Core to Container Registry..."
docker push gcr.io/$PROJECT_ID/gringo-core:latest

echo "🚢 Deploying ChatterFix Core..."
gcloud run deploy gringo-core \
    --image gcr.io/$PROJECT_ID/gringo-core:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1.5Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 1 \
    --max-instances 50 \
    --set-env-vars "AI_TEAM_SERVICE_URL=$AI_TEAM_SERVICE_URL" \
    --set-env-vars "DISABLE_AI_TEAM_GRPC=true" \
    --set-env-vars "INTERNAL_API_KEY=ai-team-service-key-change-me" \
    --port 8000

# Get ChatterFix service URL
CHATTERFIX_SERVICE_URL=$(gcloud run services describe gringo-core --region=$REGION --format="value(status.url)")

echo ""
echo "🔍 Verifying deployments..."

# Test AI Team service
echo "Testing AI Team service..."
if curl -f "$AI_TEAM_SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ AI Team service is healthy"
else
    echo "⚠️  AI Team service may not be ready"
fi

# Test ChatterFix service
echo "Testing ChatterFix service..."
if curl -f "$CHATTERFIX_SERVICE_URL" > /dev/null 2>&1; then
    echo "✅ ChatterFix service is healthy"
else
    echo "⚠️  ChatterFix service may not be ready"
fi

# Test integration
echo "Testing service integration..."
sleep 10
if curl -f "$CHATTERFIX_SERVICE_URL/ai-team" > /dev/null 2>&1; then
    echo "✅ AI Team integration working"
else
    echo "⚠️  AI Team integration may need time to initialize"
fi

echo ""
echo "🎉 Microservices Deployment Complete!"
echo "====================================="
echo ""
echo "🤖 AI Team Service:"
echo "   URL: $AI_TEAM_SERVICE_URL"
echo "   Health: $AI_TEAM_SERVICE_URL/health"
echo "   API Docs: $AI_TEAM_SERVICE_URL/docs"
echo "   Models: $AI_TEAM_SERVICE_URL/api/v1/models"
echo ""
echo "🏭 ChatterFix Core:"
echo "   URL: $CHATTERFIX_SERVICE_URL"
echo "   AI Team: $CHATTERFIX_SERVICE_URL/ai-team"
echo "   Demo: $CHATTERFIX_SERVICE_URL/demo"
echo ""
echo "🔗 Custom Domains:"
echo "   https://chatterfix.com"
echo "   https://www.chatterfix.com"
echo ""
echo "📊 Service Architecture:"
echo "   ┌─────────────────┐    HTTP API     ┌─────────────────┐"
echo "   │   ChatterFix    │◄──────────────►│   AI Team       │"
echo "   │   CMMS Core     │    REST/JSON    │   Service       │"
echo "   │   (Cloud Run)   │                 │   (Cloud Run)   │"
echo "   └─────────────────┘                 └─────────────────┘"
echo ""
echo "✅ Benefits Achieved:"
echo "   • Independent scaling for AI workloads"
echo "   • Faster ChatterFix deployments (no gRPC startup)"
echo "   • Fault isolation between services"
echo "   • Reduced resource costs during idle periods"
echo ""
echo "🔧 Configuration Applied:"
echo "   AI_TEAM_SERVICE_URL: $AI_TEAM_SERVICE_URL"
echo "   DISABLE_AI_TEAM_GRPC: true"
echo "   INTERNAL_API_KEY: ai-team-service-key-change-me"
echo ""
echo "⚠️  SECURITY NOTE:"
echo "   Change INTERNAL_API_KEY in production!"
echo ""
echo "🎯 Next Steps:"
echo "   1. Test AI collaboration features"
echo "   2. Monitor service performance"
echo "   3. Update API keys for production"
echo "   4. Configure custom domain SSL"