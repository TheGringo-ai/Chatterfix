#!/bin/bash

# Direct Cloud Run Deployment Script
# Bypasses GitHub Actions and deploys directly from local machine

echo "🚀 Direct Cloud Run Deployment Starting..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud CLI"
    exit 1
fi

# Set up authentication
if [[ -f "secrets/GCP_SA_KEY.json" ]]; then
    echo "🔑 Using service account from secrets/GCP_SA_KEY.json"
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/GCP_SA_KEY.json"
    gcloud auth activate-service-account --key-file=secrets/GCP_SA_KEY.json
else
    echo "🔑 Using default gcloud authentication"
fi

# Set project
echo "📋 Setting GCP project to fredfix"
gcloud config set project fredfix

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    cloudaicompanion.googleapis.com \
    storage-api.googleapis.com

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy chatterfix-cmms \
    --source . \
    --region us-central1 \
    --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=fredfix,FIREBASE_API_KEY=AIzaSyAaXlvuopHtTZglfghnlc_hBqGr1YzPrBk,ENVIRONMENT=production" \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=300 \
    --allow-unauthenticated \
    --port=8080 \
    --quiet

# Get the service URL
echo "🌐 Getting service URL..."
SERVICE_URL=$(gcloud run services describe chatterfix-cmms --region us-central1 --format="value(status.url)")

echo "✅ Deployment complete!"
echo "📱 Service URL: $SERVICE_URL"
echo "🔥 Test endpoints:"
echo "   Health: $SERVICE_URL/health"
echo "   Test: $SERVICE_URL/test"
echo "   Dashboard: $SERVICE_URL/"