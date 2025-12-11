#!/bin/bash

# ChatterFix Unified Deployment Script
# Single deployment script for all environments
# Usage: ./deploy.sh [direct|cloudbuild]

set -e

# ============================================================================
# CONSTANTS
# ============================================================================
UNKNOWN_PROJECT="unknown"

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ID="fredfix"
REGION="us-central1" 
SERVICE_NAME="gringo-core"
DOMAIN="chatterfix.com"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
DEPLOY_MODE=${1:-"direct"}

# Detect CI/CD environment
IS_CI=false
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ] || [ -n "$CIRCLECI" ]; then
    IS_CI=true
    echo "🤖 CI/CD environment detected"
fi

echo "🚀 ChatterFix Unified Deployment"
echo "================================"
echo "🎯 Project: $PROJECT_ID"
echo "🎯 Service: $SERVICE_NAME" 
echo "🎯 Region: $REGION"
echo "🎯 Domain: $DOMAIN"
echo "🎯 Image: $IMAGE_NAME"
echo "🔧 Mode: $DEPLOY_MODE"
echo "🤖 CI/CD: $IS_CI"
echo

# ============================================================================
# PRE-DEPLOYMENT CHECKS
# ============================================================================
echo "🔍 Running pre-deployment checks..."

# Verify GCP project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "$UNKNOWN_PROJECT")
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    if [ "$IS_CI" = true ]; then
        echo "⚠️  Warning: GCP project mismatch in CI/CD (expected: $PROJECT_ID, got: $CURRENT_PROJECT)"
        echo "   This is normal in CI/CD - authentication will be handled by workflow"
    else
        echo "❌ ERROR: Wrong GCP project!"
        echo "   Current: $CURRENT_PROJECT"
        echo "   Expected: $PROJECT_ID"
        echo "   Run: gcloud config set project $PROJECT_ID"
        exit 1
    fi
fi

# Verify service exists (skip in CI if service doesn't exist yet)
if ! gcloud run services describe $SERVICE_NAME --region=$REGION --quiet > /dev/null 2>&1; then
    if [ "$IS_CI" = true ]; then
        echo "⚠️  Service '$SERVICE_NAME' does not exist yet"
        echo "   It will be created during deployment"
    else
        echo "❌ ERROR: Service '$SERVICE_NAME' does not exist!"
        echo "   Available services:"
        gcloud run services list --region=$REGION
        exit 1
    fi
fi

# Check git status (skip in CI/CD)
if [ "$IS_CI" = false ]; then
    if ! git diff --quiet; then
        echo "⚠️  WARNING: Uncommitted changes detected!"
        git status --porcelain
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Deployment cancelled."
            exit 1
        fi
    fi
else
    echo "✅ Skipping git status check in CI/CD environment"
fi

echo "✅ Pre-deployment checks passed"
echo

# ============================================================================
# DEPLOYMENT EXECUTION
# ============================================================================

if [ "$DEPLOY_MODE" = "cloudbuild" ]; then
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
    
else
    echo "🔨 Using direct Docker deployment..."
    
    # Build and push image directly
    echo "🏗️  Building Docker image..."
    docker build -t $IMAGE_NAME:latest . --platform linux/amd64
    
    echo "📤 Pushing to Container Registry..."
    docker push $IMAGE_NAME:latest
    
    echo "🚢 Deploying to Cloud Run..."
    gcloud run deploy $SERVICE_NAME \
      --image=$IMAGE_NAME:latest \
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
fi

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