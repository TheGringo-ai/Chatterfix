#!/bin/bash

# ChatterFix CMMS Storybook Deployment Script
# This script builds and deploys the Storybook to Google Cloud Run

set -e

# Configuration
PROJECT_ID="chatterfix-ai-platform"
SERVICE_NAME="chatterfix-storybook"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting ChatterFix CMMS Storybook deployment..."

# Check if required tools are installed
command -v gcloud >/dev/null 2>&1 || { echo "❌ Google Cloud SDK is required but not installed. Aborting." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }

# Authenticate with Google Cloud
echo "🔐 Checking Google Cloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "🔑 Please authenticate with Google Cloud:"
    gcloud auth login
fi

# Set the project
echo "📋 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Ensuring required APIs are enabled..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the Docker image
echo "🏗️  Building Docker image..."
docker build -f Dockerfile.storybook -t ${IMAGE_NAME}:latest .

# Push the image to Google Container Registry
echo "📤 Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --port 80 \
    --set-env-vars "ENVIRONMENT=production" \
    --labels "app=chatterfix-cmms,component=storybook,version=latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "📖 Storybook is available at: ${SERVICE_URL}"
echo ""
echo "🔗 Quick links:"
echo "   • Storybook: ${SERVICE_URL}"
echo "   • Cloud Console: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics?project=${PROJECT_ID}"
echo ""
echo "💡 To update the deployment, run this script again."
echo "💡 To view logs: gcloud logs tail --project=${PROJECT_ID} --service=${SERVICE_NAME}"