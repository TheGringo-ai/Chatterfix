#!/bin/bash
# Quick deployment using Cloud Run source deploy
# Speed: 2-5 minutes (vs 5-15 with full Docker rebuild)
# Use this for rapid development iterations

set -e

echo "🚀 Quick Deploy - ChatterFix"
echo "============================"
echo "Using Cloud Run source deploy (no local Docker build)"
echo ""

# Check if logged in
if ! gcloud auth print-identity-token &>/dev/null; then
    echo "❌ Not logged in to gcloud. Run: gcloud auth login"
    exit 1
fi

# Deploy directly from source
echo "📤 Deploying from source..."
gcloud run deploy chatterfix-cmms \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=fredfix,ENVIRONMENT=production" \
  --set-secrets="FIREBASE_API_KEY=FIREBASE_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,OPENAI_API_KEY=openai-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest" \
  --project fredfix

echo ""
echo "✅ Deployment complete!"
echo "🌐 https://chatterfix.com"
