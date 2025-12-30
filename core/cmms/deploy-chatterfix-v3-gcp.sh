#!/bin/bash

# ChatterFix Enterprise v3.0 AI Powerhouse - GCP Deployment
echo "🚀 Deploying ChatterFix Enterprise v3.0 AI Powerhouse to GCP..."

# Build and deploy to Cloud Run
gcloud run deploy chatterfix-v3-ai \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --env-vars-file .env.production \
    --project fredfix

echo "✅ ChatterFix Enterprise v3.0 AI Powerhouse deployed to GCP!"
echo "🌐 URL will be provided after deployment"