#!/bin/bash
# Direct Cloud Run deployment without Cloud Build complexity

set -e

PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-cmms"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:direct"

echo "🚀 Direct Cloud Run Deployment"
echo "=============================="
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Build and push image directly
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME . --platform linux/amd64

echo "📤 Pushing to Container Registry..."
docker push $IMAGE_NAME

echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,LOG_LEVEL=info \
  --memory=2Gi \
  --cpu=1 \
  --concurrency=80 \
  --max-instances=10 \
  --min-instances=1 \
  --timeout=300s \
  --project=$PROJECT_ID

echo ""
echo "✅ Deployment completed!"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"

echo "🔍 Testing health endpoint..."
sleep 10
curl -s "$SERVICE_URL/health" || echo "Health check will be available shortly..."