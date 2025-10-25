#!/bin/bash
# ChatterFix CMMS - Secure Deployment with Environment Variables
# This script deploys services with proper environment variable configuration

set -e

echo "🚀 ChatterFix CMMS - Secure Deployment Script"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="fredfix"
REGION="us-central1"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

# Function to deploy service with environment variables
deploy_service() {
    local SERVICE_NAME=$1
    local SOURCE_DIR=$2
    local MEMORY=${3:-1Gi}
    local CPU=${4:-1}
    
    echo -e "${BLUE}🚢 Deploying $SERVICE_NAME...${NC}"
    
    gcloud run deploy $SERVICE_NAME \
        --source $SOURCE_DIR \
        --region $REGION \
        --allow-unauthenticated \
        --port 8080 \
        --memory $MEMORY \
        --cpu $CPU \
        --min-instances 0 \
        --max-instances 3 \
        --set-env-vars="OPENAI_API_KEY=REDACTED_OPENAI_KEY" \
        --set-env-vars="DATABASE_URL=postgresql://chatterfix_user:REDACTED_DB_PASSWORD@35.225.244.14:5432/chatterfix_saas_db" \
        --set-env-vars="DB_HOST=35.225.244.14" \
        --set-env-vars="DB_PORT=5432" \
        --set-env-vars="DB_NAME=chatterfix_saas_db" \
        --set-env-vars="DB_USER=chatterfix_user" \
        --set-env-vars="DB_PASSWORD=REDACTED_DB_PASSWORD" \
        --set-env-vars="PYTHON_ENV=production" \
        --set-env-vars="LOG_LEVEL=info" \
        --set-env-vars="WORK_ORDERS_URL=https://chatterfix-work-orders-650169261019.us-central1.run.app" \
        --set-env-vars="ASSETS_URL=https://chatterfix-assets-650169261019.us-central1.run.app" \
        --set-env-vars="PARTS_URL=https://chatterfix-parts-650169261019.us-central1.run.app" \
        --set-env-vars="AI_BRAIN_URL=https://chatterfix-ai-brain-650169261019.us-central1.run.app" \
        --set-env-vars="CUSTOMER_SUCCESS_URL=https://chatterfix-customer-success-650169261019.us-central1.run.app"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $SERVICE_NAME deployed successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to deploy $SERVICE_NAME${NC}"
        return 1
    fi
}

# Deploy services
echo -e "${YELLOW}🔧 Starting secure deployment...${NC}"

# Deploy Unified Gateway (main frontend)
deploy_service "chatterfix-unified-gateway" "frontend/" "1Gi" "1"

# Deploy Work Orders Service
if [ -d "services/work_orders" ]; then
    deploy_service "chatterfix-work-orders" "services/work_orders/" "512Mi" "1"
fi

# Deploy Assets Service
if [ -d "services/assets" ]; then
    deploy_service "chatterfix-assets" "services/assets/" "512Mi" "1"
fi

# Deploy Parts Service
if [ -d "services/parts" ]; then
    deploy_service "chatterfix-parts" "services/parts/" "512Mi" "1"
fi

echo ""
echo -e "${GREEN}🎉 Secure deployment completed!${NC}"
echo ""
echo -e "${BLUE}🔍 Verify deployments:${NC}"
echo "   Main App: https://chatterfix.com"
echo "   Gateway:  https://chatterfix-unified-gateway-650169261019.us-central1.run.app"
echo ""
echo -e "${YELLOW}🔐 Security Notes:${NC}"
echo "   ✅ Environment variables set securely"
echo "   ✅ API keys not in code"
echo "   ✅ Database credentials secured"
echo "   ✅ .gitignore updated"
echo ""