#!/bin/bash

# ChatterFix Fast Development Deployment
# Deploys only code changes without full Docker rebuild
# Perfect for quick iterations during development

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}⚡ ChatterFix Fast Development Deploy${NC}"
echo "====================================="

# Configuration
PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-cmms"
REGION="us-central1"

# Check if we're in sync (quick check)
if ! git diff --quiet; then
    echo -e "${YELLOW}⚠️  Uncommitted changes detected${NC}"
    echo "   Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
fi

echo -e "${YELLOW}🔍 Fast deployment options:${NC}"
echo "1. Source-only deploy (fastest - ~2 min)"
echo "2. Quick Docker rebuild (fast - ~5 min)" 
echo "3. Full deployment (slow - ~10 min)"
echo
echo -n "Choose option (1-3): "
read -r choice

case $choice in
    1)
        echo -e "${GREEN}🚀 Source-only deployment...${NC}"
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --region=$REGION \
            --project=$PROJECT_ID \
            --allow-unauthenticated \
            --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,LOG_LEVEL=info" \
            --memory=2Gi \
            --cpu=1 \
            --min-instances=1 \
            --max-instances=10 \
            --timeout=300s \
            --quiet
        ;;
    2)
        echo -e "${GREEN}🔨 Quick Docker rebuild...${NC}"
        # Build only the current changes
        docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:dev-$(date +%s) .
        docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:dev-$(date +%s)
        gcloud run deploy $SERVICE_NAME \
            --image=gcr.io/$PROJECT_ID/$SERVICE_NAME:dev-$(date +%s) \
            --region=$REGION \
            --project=$PROJECT_ID \
            --allow-unauthenticated \
            --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,LOG_LEVEL=info" \
            --quiet
        ;;
    3)
        echo -e "${GREEN}🏗️  Full deployment...${NC}"
        ./deploy-production.sh
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}✅ Deployment completed!${NC}"

# Test the deployment
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "🌐 Testing deployment..."

if curl -s "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Service is healthy${NC}"
    echo "📱 Live at: $SERVICE_URL"
    echo "🌍 Domain: https://chatterfix.com"
else
    echo -e "${YELLOW}⚠️  Service may still be starting...${NC}"
fi

echo
echo -e "${BLUE}💡 Development Tips:${NC}"
echo "• Use option 1 for quick code changes"
echo "• Use option 2 for dependency changes"  
echo "• Use option 3 for production releases"
echo "• Test locally first: python main.py"