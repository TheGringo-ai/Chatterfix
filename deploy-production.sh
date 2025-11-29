#!/bin/bash

# Production Deployment Script for ChatterFix
# Deploys to Cloud Run with custom domain configuration

set -e

PROJECT_ID="chatterfix-cmms"
REGION="us-central1"
SERVICE_NAME="chatterfix-cmms"
DOMAIN="chatterfix.com"

echo "🚀 Deploying ChatterFix to Production"
echo "====================================="
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Domain: $DOMAIN"
echo

# Create substitution variables for Cloud Build
cat > cloudbuild-prod.yaml << 'EOF'
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/${PROJECT_ID}/chatterfix-cmms:latest'
      - '--build-arg'
      - 'USE_FIRESTORE=true'
      - '.'

  # Push the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/${PROJECT_ID}/chatterfix-cmms:latest'

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'chatterfix-cmms'
      - '--image=gcr.io/${PROJECT_ID}/chatterfix-cmms:latest'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--set-env-vars=USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},LOG_LEVEL=info'
      - '--memory=2Gi'
      - '--cpu=1'
      - '--concurrency=80'
      - '--max-instances=10'
      - '--min-instances=1'
      - '--timeout=300s'

  # Create domain mapping
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'domain-mappings'
      - 'create'
      - '--service=chatterfix-cmms'
      - '--domain=chatterfix.com'
      - '--region=us-central1'
      - '--platform=managed'

images:
  - 'gcr.io/${PROJECT_ID}/chatterfix-cmms:latest'

timeout: '1200s'
EOF

echo "📋 Cloud Build configuration created"
echo "🔨 Starting deployment..."

# Trigger the build
gcloud builds submit --config cloudbuild-prod.yaml --project=$PROJECT_ID .

echo "✅ Deployment initiated!"
echo
echo "🌐 Service will be available at:"
echo "  - Cloud Run URL: https://chatterfix-cmms-[hash]-uc.a.run.app"
echo "  - Custom domain: https://chatterfix.com (after DNS setup)"
echo
echo "📋 Next: Configure DNS records for chatterfix.com"