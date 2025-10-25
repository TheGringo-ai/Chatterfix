#!/bin/bash

set -e

echo "🚀 Deploying Consolidated ChatterFix CMMS Service"
echo "================================================"

# Configuration  
PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-consolidated-cmms"
REGION="us-central1"
MIN_INSTANCES=0
MAX_INSTANCES=3
MEMORY="1Gi"
CPU="1"
ARTIFACT_REGISTRY="us-central1-docker.pkg.dev"

# Build and deploy
echo "📦 Building Docker image..."
cp Dockerfile.consolidated Dockerfile
gcloud builds submit --tag $ARTIFACT_REGISTRY/$PROJECT_ID/chatterfix/$SERVICE_NAME .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $ARTIFACT_REGISTRY/$PROJECT_ID/chatterfix/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --min-instances $MIN_INSTANCES \
  --max-instances $MAX_INSTANCES \
  --port 8080 \
  --set-env-vars="GCS_BUCKET=chatterfix-attachments,CHATTERFIX_API_KEY=chatterfix_secure_api_key_2025_cmms_prod_v1" \
  --timeout=300

echo "✅ Deployment complete!"
echo "🌐 Service URL: https://$SERVICE_NAME-psycl7nhha-uc.a.run.app"

# Health check
echo "🔍 Running health check..."
sleep 10
curl -f -H "x-api-key: chatterfix_secure_api_key_2025_cmms_prod_v1" "https://$SERVICE_NAME-psycl7nhha-uc.a.run.app/health" || echo "❌ Health check failed"

echo "📊 Service endpoints:"
echo "  - Work Orders: https://$SERVICE_NAME-psycl7nhha-uc.a.run.app/work_orders"
echo "  - Assets: https://$SERVICE_NAME-psycl7nhha-uc.a.run.app/assets" 
echo "  - Parts: https://$SERVICE_NAME-psycl7nhha-uc.a.run.app/parts"
echo "  - Health: https://$SERVICE_NAME-psycl7nhha-uc.a.run.app/health"