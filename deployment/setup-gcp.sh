#!/bin/bash

# ChatterFix CMMS - GCP Setup Script
# This script helps set up Google Cloud Platform for ChatterFix deployment

set -e

echo "🚀 ChatterFix CMMS - GCP Setup"
echo "================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
read -p "Enter your GCP Project ID: " PROJECT_ID

# Set project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage.googleapis.com

# Create App Engine app
echo "🏗️  Creating App Engine application..."
read -p "Enter region (e.g., us-central1): " REGION
gcloud app create --region=$REGION || echo "App Engine already exists"

# Create Cloud Storage bucket for static files
echo "📦 Creating Cloud Storage bucket..."
BUCKET_NAME="${PROJECT_ID}-chatterfix-storage"
gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME/ || echo "Bucket already exists"

# Set bucket permissions
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME/

# Create service account for GitHub Actions
echo "🔑 Creating service account for CI/CD..."
SA_NAME="chatterfix-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
    --display-name="ChatterFix Deployment Service Account" || echo "Service account already exists"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/appengine.appAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudbuild.builds.editor"

# Create and download service account key
echo "📥 Creating service account key..."
gcloud iam service-accounts keys create ./gcp-key.json \
    --iam-account=$SA_EMAIL

echo ""
echo "✅ GCP Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Add the following secrets to your GitHub repository:"
echo "   - GCP_SA_KEY: (contents of gcp-key.json)"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo ""
echo "2. Update deployment/app.yaml with your project settings"
echo ""
echo "3. Deploy your application:"
echo "   gcloud app deploy deployment/app.yaml"
echo ""
echo "4. Configure custom domain (optional):"
echo "   gcloud app domain-mappings create chatterfix.com"
echo ""
echo "⚠️  IMPORTANT: Keep gcp-key.json secure and never commit it to git!"
