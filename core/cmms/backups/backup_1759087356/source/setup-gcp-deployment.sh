#!/bin/bash
# ChatterFix CMMS Mars-Level AI Platform - Google Cloud Setup Script
# 🚀 Automated setup for GCP deployment via GitHub Actions

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Setting up ChatterFix CMMS Mars-Level AI Platform for Google Cloud${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI not found${NC}"
    echo -e "${YELLOW}Installing Google Cloud CLI...${NC}"
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔑 Please authenticate with Google Cloud...${NC}"
    gcloud auth login
fi

# Get or set project ID
echo -e "${YELLOW}📋 Setting up Google Cloud project...${NC}"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")

if [[ -z "$PROJECT_ID" ]]; then
    echo -e "${YELLOW}No project selected. Please enter your Google Cloud Project ID:${NC}"
    read -p "Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com

# Create service account for deployment
SERVICE_ACCOUNT_NAME="chatterfix-cmms-mars-level"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo -e "${YELLOW}👤 Creating service account...${NC}"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --description="ChatterFix CMMS Mars-Level AI Platform deployment service account" \
    --display-name="ChatterFix CMMS Mars-Level" || true

# Grant necessary roles
echo -e "${YELLOW}🔐 Granting IAM roles...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountUser"

# Create service account key
echo -e "${YELLOW}🔑 Creating service account key...${NC}"
gcloud iam service-accounts keys create gcp-service-account-key.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

echo -e "${GREEN}✅ Service account key saved to gcp-service-account-key.json${NC}"

# Create secrets in Secret Manager
echo -e "${YELLOW}🔒 Setting up Secret Manager...${NC}"

# Function to create secret
create_secret() {
    local secret_name=$1
    local secret_description=$2
    
    echo -e "${YELLOW}Creating secret: $secret_name${NC}"
    
    # Create the secret
    gcloud secrets create $secret_name \
        --replication-policy="automatic" \
        --labels="app=chatterfix-cmms,component=mars-level-ai" || true
    
    # Prompt for value
    echo -e "${BLUE}Please enter the value for $secret_name ($secret_description):${NC}"
    read -s secret_value
    
    if [[ -n "$secret_value" ]]; then
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
        echo -e "${GREEN}✅ Secret $secret_name created${NC}"
    else
        echo -e "${YELLOW}⚠️ Skipping empty secret $secret_name${NC}"
    fi
}

# Create required secrets
create_secret "jwt-secret" "JWT Secret Key for authentication (generate a secure random string)"
create_secret "xai-api-key" "Grok/XAI API Key from x.ai"
create_secret "openai-api-key" "OpenAI API Key from platform.openai.com"

# Optional secrets
echo -e "${BLUE}Optional API keys (press Enter to skip):${NC}"
create_secret "huggingface-api-key" "HuggingFace API Key (optional)"

# Grant service account access to secrets
echo -e "${YELLOW}🔐 Granting secret access to service account...${NC}"
for secret in jwt-secret xai-api-key openai-api-key huggingface-api-key; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor" 2>/dev/null || true
done

# Display GitHub secrets setup
echo -e "${BLUE}=== GitHub Repository Secrets Setup ===${NC}"
echo -e "${YELLOW}Add these secrets to your GitHub repository settings:${NC}"
echo ""
echo "1. Go to your GitHub repository"
echo "2. Navigate to Settings > Secrets and variables > Actions"
echo "3. Add these Repository secrets:"
echo ""
echo -e "${BLUE}GCP_PROJECT_ID${NC}"
echo "Value: $PROJECT_ID"
echo ""
echo -e "${BLUE}GCP_SA_KEY${NC}"
echo "Value: (copy the entire content of gcp-service-account-key.json)"
cat gcp-service-account-key.json
echo ""

# Deployment instructions
echo -e "${GREEN}=== Deployment Instructions ===${NC}"
echo ""
echo "1. ✅ Google Cloud setup complete"
echo "2. 📋 Add the secrets above to your GitHub repository"
echo "3. 🚀 Push your code to the main branch to trigger deployment:"
echo ""
echo "   git add ."
echo "   git commit -m '🚀 Deploy ChatterFix CMMS Mars-Level AI Platform to GCP'"
echo "   git push origin main"
echo ""
echo "4. 🎯 Check GitHub Actions tab for deployment progress"
echo "5. 🌐 Your app will be available at the Cloud Run URL after deployment"
echo ""
echo -e "${BLUE}🎉 Setup complete! Your Mars-Level AI Platform is ready for deployment!${NC}"

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f gcp-service-account-key.json

echo -e "${GREEN}✅ All done! Check your email for the service account key.${NC}"