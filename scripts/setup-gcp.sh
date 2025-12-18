#!/bin/bash

# GCP Setup for ChatterFix
# Enables APIs, creates service accounts, and sets up project

set -e

PROJECT_ID="chatterfix-cmms"
SERVICE_ACCOUNT="chatterfix-service-account"

echo "🔧 Setting up GCP project: $PROJECT_ID"
echo "========================================"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable firebase.googleapis.com

# Create Firestore database
echo "🗄️ Setting up Firestore..."
gcloud firestore databases create --region=us-central1 --type=firestore-native || echo "Firestore already exists"

# Create service account
echo "🔐 Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT \
  --display-name="ChatterFix Service Account" || echo "Service account exists"

# Grant permissions
echo "🛡️ Setting up permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/firebase.admin"

echo "✅ GCP setup complete!"
echo "Next: Run ./deploy-production.sh"