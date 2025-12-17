#!/bin/bash
# =============================================================================
# DEPLOY TO PRODUCTION (chatterfix-cmms)
# =============================================================================
# This deploys to PRODUCTION - chatterfix.com
# URL: https://chatterfix.com
#
# ⚠️  WARNING: This affects real users!
# =============================================================================

set -e

echo "🚨 DEPLOYING TO PRODUCTION"
echo "================================"
echo "Service: chatterfix-cmms"
echo "Domain: chatterfix.com"
echo "Project: fredfix"
echo ""

# Safety checks
echo "⚠️  PRODUCTION DEPLOYMENT CHECKLIST:"
echo "  1. Have you tested on DEV first?"
echo "  2. Are all changes committed?"
echo "  3. Is this the code you want to deploy?"
echo ""
read -p "Are you sure you want to deploy to PRODUCTION? (yes/no) " -r
if [[ ! $REPLY == "yes" ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ ERROR: You have uncommitted changes!"
    echo "   Commit your changes before deploying to production."
    exit 1
fi

# Get current git info
COMMIT_SHA=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B | head -1)
BRANCH=$(git branch --show-current)

echo ""
echo "📋 Deployment Info:"
echo "   Branch: $BRANCH"
echo "   Commit: $COMMIT_SHA"
echo "   Message: $COMMIT_MSG"
echo ""

# Build the image with a versioned tag
echo "📦 Building Docker image..."
gcloud builds submit \
    --tag gcr.io/fredfix/gringo-core:latest \
    --tag gcr.io/fredfix/gringo-core:$COMMIT_SHA \
    --project fredfix

# Deploy to production
echo "🚀 Deploying to chatterfix-cmms (PRODUCTION)..."
gcloud run deploy chatterfix-cmms \
    --image gcr.io/fredfix/gringo-core:$COMMIT_SHA \
    --region us-central1 \
    --project fredfix \
    --platform managed \
    --set-env-vars="ENVIRONMENT=production" \
    --min-instances=0 \
    --max-instances=10

echo ""
echo "✅ PRODUCTION DEPLOYMENT COMPLETE!"
echo "================================"
echo "🔗 Production URL: https://chatterfix.com"
echo "🔗 Demo: https://chatterfix.com/demo"
echo ""
echo "📋 Deployed commit: $COMMIT_SHA"
echo ""
echo "Monitor the deployment at:"
echo "https://console.cloud.google.com/run/detail/us-central1/chatterfix-cmms/logs?project=fredfix"
