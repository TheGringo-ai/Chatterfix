#!/bin/bash

# Production Deployment Script for ChatterFix
# Deploys to Cloud Run with custom domain configuration
# This script ensures consistent deployment to the same service every time

set -e

# ============================================================================
# DEPLOYMENT CONFIGURATION - DO NOT CHANGE THESE VALUES
# ============================================================================
PROJECT_ID="fredfix"
REGION="us-central1" 
SERVICE_NAME="chatterfix-cmms"  # THIS IS YOUR PRODUCTION SERVICE
DOMAIN="chatterfix.com"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 ChatterFix Production Deployment"
echo "===================================="
echo "🎯 Target Project: $PROJECT_ID"
echo "🎯 Target Service: $SERVICE_NAME" 
echo "🎯 Target Region: $REGION"
echo "🎯 Target Domain: $DOMAIN"
echo "🎯 Image Name: $IMAGE_NAME"
echo

# Safety check - confirm this is the right project
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "❌ ERROR: Wrong GCP project!"
    echo "   Current: $CURRENT_PROJECT"
    echo "   Expected: $PROJECT_ID"
    echo "   Run: gcloud config set project $PROJECT_ID"
    exit 1
fi

# Safety check - verify we're not accidentally creating a new service
echo "🔍 Verifying target service exists..."
if ! gcloud run services describe $SERVICE_NAME --region=$REGION --quiet > /dev/null 2>&1; then
    echo "❌ ERROR: Service '$SERVICE_NAME' does not exist!"
    echo "   This script only deploys to existing services."
    echo "   Available services:"
    gcloud run services list --region=$REGION
    exit 1
fi

echo "✅ Service verification passed"
echo

# Create substitution variables for Cloud Build
cat > cloudbuild-prod.yaml << EOF
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - '$IMAGE_NAME:latest'
      - '--build-arg'
      - 'USE_FIRESTORE=true'
      - '.'

  # Push the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '$IMAGE_NAME:latest'

  # Deploy to Cloud Run - UPDATE EXISTING SERVICE ONLY
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

echo "📋 Cloud Build configuration created"
echo "🔨 Starting deployment to $SERVICE_NAME..."
echo

# Trigger the build with explicit project
gcloud builds submit --config cloudbuild-prod.yaml --project=$PROJECT_ID .

# Deployment verification
echo
echo "🔍 Verifying deployment..."
sleep 10  # Give Cloud Run a moment to update

# Check service status
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
echo "  - Custom domain: https://chatterfix.com"
echo "  - Custom domain: https://www.chatterfix.com"
echo
echo "📊 To monitor: gcloud run services describe $SERVICE_NAME --region=$REGION"