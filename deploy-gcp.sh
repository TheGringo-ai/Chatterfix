#!/bin/bash

# ChatterFix GCP Deployment Script
# This script sets up and deploys ChatterFix to Google Cloud Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ChatterFix GCP Deployment Script${NC}"
echo "==========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Set project ID (update this to your project)
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"chatterfix-cmms"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="chatterfix-cmms"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo

# Prompt for confirmation
read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo -e "${BLUE}🔧 Setting up GCP project...${NC}"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}📡 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    firestore.googleapis.com \
    firebase.googleapis.com \
    iam.googleapis.com

# Create Firestore database (if not exists)
echo -e "${YELLOW}🗄️  Setting up Firestore...${NC}"
gcloud firestore databases create --region=$REGION --type=firestore-native || echo "Firestore database already exists"

# Create service account for Cloud Run
echo -e "${YELLOW}🔐 Creating service account...${NC}"
SERVICE_ACCOUNT_NAME="chatterfix-service-account"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="ChatterFix CMMS Service Account" \
    --description="Service account for ChatterFix CMMS application" || echo "Service account already exists"

# Grant necessary permissions
echo -e "${YELLOW}🛡️  Granting permissions...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer"

# Build and deploy using Cloud Build
echo -e "${BLUE}🏗️  Building and deploying to Cloud Run...${NC}"

# Update the cloudbuild file with correct project ID
sed "s/PROJECT_ID/$PROJECT_ID/g" deployment/cloudbuild-cloudrun.yaml > deployment/cloudbuild-cloudrun-temp.yaml

# Trigger Cloud Build
gcloud builds submit --config=deployment/cloudbuild-cloudrun-temp.yaml .

# Clean up temp file
rm deployment/cloudbuild-cloudrun-temp.yaml

# Get the service URL
echo -e "${BLUE}🌐 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo "==========================================="
echo -e "${GREEN}🎉 ChatterFix is now deployed!${NC}"
echo -e "${BLUE}Service URL: $SERVICE_URL${NC}"
echo
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Set up Firebase Authentication in the Firebase Console"
echo "2. Configure Firebase API keys in the environment"
echo "3. Test the application at: $SERVICE_URL"
echo
echo -e "${YELLOW}🔥 Firebase Console:${NC}"
echo "https://console.firebase.google.com/project/$PROJECT_ID"
echo
echo -e "${YELLOW}☁️  Cloud Console:${NC}"
echo "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"