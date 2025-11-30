#!/bin/bash

# Manual ChatterFix Deployment Script
# Use this if GitHub Actions deployment is not working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ChatterFix Manual Deployment${NC}"
echo "=================================="
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
else
    echo -e "${GREEN}✅ gcloud CLI found${NC}"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
else
    echo -e "${GREEN}✅ Docker found${NC}"
fi

echo ""

# Check authentication
echo -e "${YELLOW}🔐 Checking GCP authentication...${NC}"
if gcloud auth list --filter="status:ACTIVE" --format="value(account)" | grep -q .; then
    ACCOUNT=$(gcloud auth list --filter="status:ACTIVE" --format="value(account)")
    echo -e "${GREEN}✅ Authenticated as: $ACCOUNT${NC}"
else
    echo -e "${YELLOW}⚠️  Not authenticated. Running gcloud auth login...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}☁️  Setting GCP project...${NC}"
gcloud config set project fredfix
echo -e "${GREEN}✅ Project set to fredfix${NC}"

echo ""

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable artifactregistry.googleapis.com --quiet
echo -e "${GREEN}✅ APIs enabled${NC}"

echo ""

# Build and deploy
echo -e "${YELLOW}🏗️  Building and deploying to Cloud Run...${NC}"

# Create unique tag
BUILD_TAG="build-$(date +%s)"

echo "Building application..."
gcloud run deploy chatterfix \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars "ENVIRONMENT=production,USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=fredfix,FIREBASE_API_KEY=AIzaSyAaXlvuopHtTZglfghnlc_hBqGr1YzPrBk,CMMS_PORT=8080" \
  --tag "$BUILD_TAG"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo ""
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe chatterfix --region us-central1 --format="value(status.url)")
    echo -e "${GREEN}📱 Service URL: $SERVICE_URL${NC}"
    echo ""
    
    # Test the deployment
    echo -e "${YELLOW}🧪 Testing deployment...${NC}"
    if curl -f "$SERVICE_URL/health" --max-time 10 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check failed, but service is deployed${NC}"
        echo "Check logs with: gcloud run logs read --service chatterfix --region us-central1"
    fi
    
    echo ""
    echo -e "${GREEN}🎯 Deployment Summary:${NC}"
    echo "  🌐 URL: $SERVICE_URL"
    echo "  📍 Region: us-central1"
    echo "  🔥 Database: Firestore"
    echo "  📦 Build tag: $BUILD_TAG"
    echo ""
    echo -e "${GREEN}✅ ChatterFix is now live on Google Cloud Run!${NC}"
    
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Check that billing is enabled for project 'fredfix'"
    echo "2. Ensure you have Cloud Run Admin permissions"
    echo "3. Check Cloud Build logs for detailed errors"
    echo "4. Run: gcloud run logs read --service chatterfix --region us-central1"
    exit 1
fi