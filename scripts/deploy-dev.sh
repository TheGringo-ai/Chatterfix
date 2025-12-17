#!/bin/bash
# =============================================================================
# DEPLOY TO DEV (gringo-core)
# =============================================================================
# This deploys to the development environment for testing
# URL: https://gringo-core-650169261019.us-central1.run.app
# Cost: ~$0 when idle (scales to 0)
# =============================================================================

set -e

echo "🚀 DEPLOYING TO DEV ENVIRONMENT"
echo "================================"
echo "Service: gringo-core"
echo "Project: fredfix"
echo "Region: us-central1"
echo ""

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  Warning: You have uncommitted changes"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build the image
echo "📦 Building Docker image..."
gcloud builds submit --tag gcr.io/fredfix/gringo-core:latest --project fredfix

# Deploy to dev
echo "🚀 Deploying to gringo-core (DEV)..."
gcloud run deploy gringo-core \
    --image gcr.io/fredfix/gringo-core:latest \
    --region us-central1 \
    --project fredfix \
    --platform managed \
    --set-env-vars="ENVIRONMENT=development" \
    --min-instances=0 \
    --max-instances=2

echo ""
echo "✅ DEV DEPLOYMENT COMPLETE!"
echo "================================"
echo "🔗 Dev URL: https://gringo-core-650169261019.us-central1.run.app"
echo "🔗 Demo: https://gringo-core-650169261019.us-central1.run.app/demo"
echo ""
echo "Test your changes, then run ./scripts/deploy-prod.sh to go live!"
