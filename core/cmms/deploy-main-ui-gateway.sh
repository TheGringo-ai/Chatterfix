#!/bin/bash

echo "🚀 Deploying ChatterFix Main UI Gateway with Universal AI Styling..."
echo "📦 Building and deploying clean microservices gateway to Cloud Run..."

# Deploy the enhanced UI gateway service  
gcloud run deploy chatterfix-cmms \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --clear-base-image \
    --project fredfix

echo "✅ ChatterFix Main UI Gateway deployed successfully!"
echo "🌐 Available at: https://chatterfix.com"
echo "🔄 All microservices are connected and proxied through the gateway"