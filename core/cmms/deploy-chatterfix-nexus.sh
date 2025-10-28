#!/bin/bash

echo "🚀 Deploying ChatterFix Nexus to Google Cloud Run..."

# Set variables
PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-nexus"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Build and push Docker image for Cloud Run (linux/amd64)
echo "📦 Building Docker image for Cloud Run..."
docker build --platform linux/amd64 -f Dockerfile.nexus -t ${IMAGE_NAME}:latest .

echo "🔄 Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars "XAI_API_KEY=${XAI_API_KEY},OPENAI_API_KEY=${OPENAI_API_KEY}" \
    --project ${PROJECT_ID}

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

echo "✅ ChatterFix Nexus deployed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "📊 Access the dashboard at: ${SERVICE_URL}"

# Configure custom domain mapping (chatterfix.com)
echo "🔗 Setting up custom domain mapping..."
gcloud beta run domain-mappings create \
    --service ${SERVICE_NAME} \
    --domain chatterfix.com \
    --region ${REGION} \
    --project ${PROJECT_ID}

echo "🎉 ChatterFix Nexus is now live at https://chatterfix.com"