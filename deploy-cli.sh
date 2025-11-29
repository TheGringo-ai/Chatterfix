#!/bin/bash

# ChatterFix CLI Deployment Script
# Complete deployment to chatterfix.com via Google Cloud CLI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID="chatterfix-cmms"
REGION="us-central1"
SERVICE_NAME="chatterfix-cmms"
DOMAIN="chatterfix.com"
SERVICE_ACCOUNT_NAME="chatterfix-sa"

echo -e "${BLUE}🚀 ChatterFix CLI Deployment${NC}"
echo "==============================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Domain: $DOMAIN"
echo

# Step 1: Verify gcloud is installed and authenticated
echo -e "${YELLOW}Step 1: Checking gcloud setup...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud CLI first.${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}🔐 Please authenticate with Google Cloud:${NC}"
    gcloud auth login
fi

# Step 2: Set up project
echo -e "${YELLOW}Step 2: Setting up GCP project...${NC}"
echo "Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Create project if it doesn't exist
if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
    echo "Creating project: $PROJECT_ID"
    gcloud projects create $PROJECT_ID --name="ChatterFix CMMS"
    
    # Enable billing (you'll need to link a billing account)
    echo -e "${YELLOW}⚠️  Please enable billing for project $PROJECT_ID in the console:${NC}"
    echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    read -p "Press Enter after enabling billing..."
fi

# Step 3: Enable APIs
echo -e "${YELLOW}Step 3: Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com  
gcloud services enable containerregistry.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable firebase.googleapis.com
gcloud services enable domains.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"

# Step 4: Set up Firestore
echo -e "${YELLOW}Step 4: Setting up Firestore database...${NC}"
if ! gcloud firestore databases list --filter="type:FIRESTORE_NATIVE" --format="value(name)" | grep -q "databases"; then
    echo "Creating Firestore database..."
    gcloud firestore databases create --region=$REGION --type=firestore-native
    echo -e "${GREEN}✅ Firestore database created${NC}"
else
    echo -e "${GREEN}✅ Firestore database already exists${NC}"
fi

# Step 5: Create service account
echo -e "${YELLOW}Step 5: Setting up service account...${NC}"
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" &>/dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="ChatterFix Service Account" \
        --description="Service account for ChatterFix CMMS"
    
    # Grant permissions
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/datastore.user"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/firebase.admin"
    
    echo -e "${GREEN}✅ Service account created and configured${NC}"
else
    echo -e "${GREEN}✅ Service account already exists${NC}"
fi

# Step 6: Build and push container
echo -e "${YELLOW}Step 6: Building and pushing container image...${NC}"
# Configure Docker for gcloud
gcloud auth configure-docker

# Build the image
echo "Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

# Push the image
echo "Pushing to Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

echo -e "${GREEN}✅ Container image built and pushed${NC}"

# Step 7: Deploy to Cloud Run
echo -e "${YELLOW}Step 7: Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image=gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --service-account="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,LOG_LEVEL=info" \
    --memory=2Gi \
    --cpu=1 \
    --concurrency=80 \
    --max-instances=10 \
    --min-instances=1 \
    --timeout=300s

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo -e "${GREEN}✅ Service deployed successfully!${NC}"
echo "Service URL: $SERVICE_URL"

# Step 8: Test the deployment
echo -e "${YELLOW}Step 8: Testing deployment...${NC}"
if curl -s "${SERVICE_URL}/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Service is healthy and responding${NC}"
else
    echo -e "${YELLOW}⚠️  Service deployed but health check failed${NC}"
fi

# Step 9: Set up custom domain mapping
echo -e "${YELLOW}Step 9: Setting up custom domain mapping...${NC}"

# Check if domain is verified
VERIFIED_DOMAINS=$(gcloud domains list-user-verified --format="value(domain)" 2>/dev/null || echo "")
if [[ "$VERIFIED_DOMAINS" != *"$DOMAIN"* ]]; then
    echo -e "${YELLOW}⚠️  Domain $DOMAIN not verified in Google Search Console${NC}"
    echo "Please verify your domain first:"
    echo "1. Go to: https://search.google.com/search-console"
    echo "2. Add property: $DOMAIN"
    echo "3. Complete verification"
    echo
    read -p "Press Enter after verifying the domain..."
fi

# Create domain mapping
echo "Creating domain mapping for $DOMAIN..."
if gcloud run domain-mappings create \
    --service=$SERVICE_NAME \
    --domain=$DOMAIN \
    --region=$REGION \
    --platform=managed; then
    
    echo -e "${GREEN}✅ Domain mapping created${NC}"
    
    # Get DNS records
    echo -e "${YELLOW}📋 DNS Configuration Required:${NC}"
    echo "Add these DNS records to your domain provider:"
    echo
    
    # Wait a moment for the mapping to be processed
    sleep 10
    
    gcloud run domain-mappings describe $DOMAIN --region=$REGION \
        --format="table(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)" \
        2>/dev/null || echo "DNS records will be available shortly. Check with:"
    
    echo "gcloud run domain-mappings describe $DOMAIN --region=$REGION"
else
    echo -e "${YELLOW}⚠️  Domain mapping creation failed. You may need to verify domain ownership first.${NC}"
fi

# Step 10: Set up Firebase Authentication
echo -e "${YELLOW}Step 10: Firebase Authentication setup...${NC}"
echo "Manual setup required in Firebase Console:"
echo "1. Go to: https://console.firebase.google.com/project/$PROJECT_ID"
echo "2. Authentication > Sign-in method > Enable Email/Password"
echo "3. Project Settings > Authorized domains > Add $DOMAIN"

echo
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "==============================="
echo -e "${BLUE}Service URL:${NC} $SERVICE_URL"
echo -e "${BLUE}Custom Domain:${NC} https://$DOMAIN (after DNS setup)"
echo -e "${BLUE}Firebase Console:${NC} https://console.firebase.google.com/project/$PROJECT_ID"
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Configure DNS records for $DOMAIN"
echo "2. Set up Firebase Authentication"
echo "3. Test the application at https://$DOMAIN"
echo
echo -e "${YELLOW}🔍 Monitor Deployment:${NC}"
echo "Service logs: gcloud run logs read --service=$SERVICE_NAME --region=$REGION"
echo "Domain status: gcloud run domain-mappings describe $DOMAIN --region=$REGION"
echo "Health check: curl $SERVICE_URL/health"