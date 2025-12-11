#!/bin/bash

# ChatterFix Production Deployment Script
# Uses Cloud Build for robust deployments
# Usage: ./deploy-production.sh

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ID="fredfix"
REGION="us-central1" 
SERVICE_NAME="gringo-core"
DOMAIN="chatterfix.com"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
DEPLOY_MODE="cloudbuild"

echo "🚀 ChatterFix Production Deployment"
echo "===================================="
echo "🎯 Target Project: $PROJECT_ID"
echo "🎯 Target Service: $SERVICE_NAME" 
echo "🎯 Target Region: $REGION"
echo "🎯 Target Domain: $DOMAIN"
echo "🎯 Image Name: $IMAGE_NAME"
echo

# ============================================================================
# PRE-DEPLOYMENT CHECKS
# ============================================================================
echo "🔍 Running sync verification..."
./sync-check.sh

echo "🔍 Verifying target service exists..."
if ! gcloud run services describe $SERVICE_NAME --region=$REGION --quiet > /dev/null 2>&1; then
    echo "❌ ERROR: Service '$SERVICE_NAME' does not exist!"
    echo "   Please create it first or check your configuration."
    exit 1
fi

echo "✅ Pre-deployment checks passed"
echo

# ============================================================================
# DEPLOYMENT EXECUTION
# ============================================================================

echo "🔨 Using Cloud Build deployment..."

# Create temporary Cloud Build configuration
cat > /tmp/cloudbuild-deploy.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - '$IMAGE_NAME:latest'
      - '--build-arg'
      - 'USE_FIRESTORE=true'
      - '.'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '$IMAGE_NAME:latest'

  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - '$SERVICE_NAME'
      - '--image=$IMAGE_NAME:latest'
      - '--region=$REGION'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--set-env-vars=USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,LOG_LEVEL=info'
      - '--memory=2Gi'
      - '--cpu=1'
      - '--concurrency=80'
      - '--max-instances=10'
      - '--min-instances=1'
      - '--timeout=300s'

images:
  - '$IMAGE_NAME:latest'

timeout: '1200s'
EOF

echo "🔨 Starting Cloud Build deployment..."
gcloud builds submit --config /tmp/cloudbuild-deploy.yaml --project=$PROJECT_ID .
rm /tmp/cloudbuild-deploy.yaml

# ============================================================================
# POST-DEPLOYMENT VERIFICATION
# ============================================================================
echo
echo "🔍 Verifying deployment..."
sleep 10

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "✅ Service URL: $SERVICE_URL"

# Test health endpoint
if curl -s "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "⚠️  Health check failed (service may still be starting)"
fi

echo
echo "🎉 Deployment completed!"
echo "====================================="
echo "🌐 Your app is available at:"
echo "  - Cloud Run URL: $SERVICE_URL"
echo "  - Custom domain: https://$DOMAIN"
echo "  - Custom domain: https://www.$DOMAIN"
echo
echo "📊 To monitor: gcloud run services describe $SERVICE_NAME --region=$REGION"
