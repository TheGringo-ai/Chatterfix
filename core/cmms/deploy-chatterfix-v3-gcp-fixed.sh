#!/bin/bash

# ChatterFix Enterprise v3.0 AI Powerhouse - GCP Deployment (Fixed)
echo "🚀 Deploying ChatterFix Enterprise v3.0 AI Powerhouse to GCP..."

# Deploy to Cloud Run with environment variables
gcloud run deploy chatterfix-v3-ai \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars="ENVIRONMENT=production,DEBUG=false,FIREBASE_PROJECT_ID=fredfix,FIREBASE_CLIENT_EMAIL=firebase-adminsdk-fbsvc@fredfix.iam.gserviceaccount.com,SECRET_KEY=chatterfix-enterprise-v3-ai-powerhouse-production-secret,DATABASE_FILE=chatterfix_enterprise_v3_production.db,DEMO_MODE=true" \
    --project fredfix

echo "✅ ChatterFix Enterprise v3.0 AI Powerhouse deployed to GCP!"