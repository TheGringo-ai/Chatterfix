#!/bin/bash
# ChatterFix CMMS Mars-Level AI Platform - Automated Google Cloud Setup
# 🚀 Using existing API keys from .env file

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Auto-setting up ChatterFix CMMS Mars-Level AI Platform for Google Cloud${NC}"

# Load existing environment variables
source .env

# Extract values
XAI_KEY="${XAI_API_KEY}"
PROJECT_ID="fredfix"
SERVICE_ACCOUNT_EMAIL="chatterfix-cmms-mars-level@fredfix.iam.gserviceaccount.com"

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"
echo -e "${GREEN}✅ Found XAI API Key: ${XAI_KEY:0:20}...${NC}"

# Generate secure JWT secret
JWT_SECRET="chatterfix-mars-level-ai-jwt-$(openssl rand -hex 32)"

# Create secrets in Secret Manager using existing keys
echo -e "${YELLOW}🔒 Creating secrets in Secret Manager...${NC}"

# JWT Secret
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret --data-file=- --labels="app=chatterfix-cmms,component=mars-level-ai" 2>/dev/null || \
echo -n "$JWT_SECRET" | gcloud secrets versions add jwt-secret --data-file=-

echo -e "${GREEN}✅ JWT secret created${NC}"

# XAI API Key
echo -n "$XAI_KEY" | gcloud secrets create xai-api-key --data-file=- --labels="app=chatterfix-cmms,component=mars-level-ai" 2>/dev/null || \
echo -n "$XAI_KEY" | gcloud secrets versions add xai-api-key --data-file=-

echo -e "${GREEN}✅ XAI API key created${NC}"

# OpenAI API Key (placeholder - can be updated later)
OPENAI_PLACEHOLDER="your-openai-key-here-update-in-secret-manager"
echo -n "$OPENAI_PLACEHOLDER" | gcloud secrets create openai-api-key --data-file=- --labels="app=chatterfix-cmms,component=mars-level-ai" 2>/dev/null || \
echo -n "$OPENAI_PLACEHOLDER" | gcloud secrets versions add openai-api-key --data-file=-

echo -e "${YELLOW}⚠️  OpenAI API key set to placeholder - update in Secret Manager if needed${NC}"

# HuggingFace API Key (optional placeholder)
HF_PLACEHOLDER="optional-huggingface-key"
echo -n "$HF_PLACEHOLDER" | gcloud secrets create huggingface-api-key --data-file=- --labels="app=chatterfix-cmms,component=mars-level-ai" 2>/dev/null || \
echo -n "$HF_PLACEHOLDER" | gcloud secrets versions add huggingface-api-key --data-file=-

echo -e "${GREEN}✅ HuggingFace API key created (optional)${NC}"

# Grant service account access to secrets
echo -e "${YELLOW}🔐 Granting secret access to service account...${NC}"
for secret in jwt-secret xai-api-key openai-api-key huggingface-api-key; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor" 2>/dev/null || true
done

# Create the service account key file that GitHub needs
echo -e "${YELLOW}🔑 Creating GitHub secrets...${NC}"

# Get the existing service account key (since we already created it)
TEMP_KEY_FILE="temp-gcp-key.json"
gcloud iam service-accounts keys create $TEMP_KEY_FILE --iam-account=$SERVICE_ACCOUNT_EMAIL 2>/dev/null || echo "Using existing key"

# Display GitHub secrets setup
echo -e "${BLUE}=== GitHub Repository Secrets Setup ===${NC}"
echo -e "${YELLOW}Add these secrets to your GitHub repository:${NC}"
echo ""
echo "1. Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo "2. Click 'New repository secret' for each:"
echo ""
echo -e "${BLUE}Secret Name: GCP_PROJECT_ID${NC}"
echo "Value: $PROJECT_ID"
echo ""
echo -e "${BLUE}Secret Name: GCP_SA_KEY${NC}"
echo "Value: (copy the entire JSON below)"
echo "---JSON START---"
if [[ -f "$TEMP_KEY_FILE" ]]; then
    cat $TEMP_KEY_FILE
else
    echo "Error: Service account key file not found. Please run the setup manually."
fi
echo "---JSON END---"
echo ""

# Cleanup
rm -f $TEMP_KEY_FILE

echo -e "${GREEN}=== Ready for Deployment! ===${NC}"
echo ""
echo "🎯 Next steps:"
echo "1. ✅ Google Cloud setup complete"
echo "2. 📋 Add the above secrets to your GitHub repository"
echo "3. 🚀 Deploy with:"
echo ""
echo "   git add ."
echo "   git commit -m '🚀 Deploy ChatterFix CMMS Mars-Level AI Platform to GCP'"
echo "   git push origin main"
echo ""
echo "4. 🌐 Your app will be live at: https://chatterfix-cmms-mars-level-[hash]-uc.a.run.app"
echo ""
echo -e "${BLUE}🎉 Mars-Level AI Platform ready for takeoff! 🚀${NC}"