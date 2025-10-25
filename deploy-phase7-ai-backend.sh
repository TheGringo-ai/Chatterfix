#!/bin/bash

set -e

echo "🚀 Deploying Phase 7 AI-Enhanced Backend"
echo "========================================"

# Configuration
PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-consolidated-cmms"
REGION="us-central1"
MIN_INSTANCES=0
MAX_INSTANCES=3
MEMORY="1Gi"
CPU="1"

echo "📦 Deploying AI-enhanced consolidated CMMS service..."

# Deploy with source code (includes all AI modules)
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --min-instances $MIN_INSTANCES \
  --max-instances $MAX_INSTANCES \
  --port 8080 \
  --set-env-vars="GCS_BUCKET=chatterfix-attachments,CHATTERFIX_API_KEY=chatterfix_secure_api_key_2025_cmms_prod_v1,RATE_LIMIT_REQUESTS=20,RATE_LIMIT_WINDOW=60" \
  --timeout=300

echo "✅ Backend deployment complete!"
echo "🧠 AI Features: Predictive maintenance, insights, anomaly detection"
echo "🌐 Backend URL: https://$SERVICE_NAME-650169261019.us-central1.run.app"

# Test AI endpoints
echo "🔍 Testing AI endpoints..."
sleep 15

echo "Testing predictive maintenance..."
curl -s -H "x-api-key: chatterfix_secure_api_key_2025_cmms_prod_v1" \
  "https://$SERVICE_NAME-650169261019.us-central1.run.app/predictive_maintenance" \
  | head -5

echo "Testing AI insights..."
curl -s -H "x-api-key: chatterfix_secure_api_key_2025_cmms_prod_v1" \
  "https://$SERVICE_NAME-650169261019.us-central1.run.app/insights/summary" \
  | head -5

echo "Testing anomaly alerts..."
curl -s -H "x-api-key: chatterfix_secure_api_key_2025_cmms_prod_v1" \
  "https://$SERVICE_NAME-650169261019.us-central1.run.app/alerts" \
  | head -5

echo "🎉 Phase 7 AI backend deployment complete!"