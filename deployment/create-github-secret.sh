#!/bin/bash

echo "🔑 Creating GitHub Actions Service Account for ChatterFix"
echo "=================================================="

# Create service account
echo "📝 Creating service account..."
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployer" \
  --description="Service account for GitHub Actions to deploy ChatterFix"

# Add required permissions
echo "🔐 Adding IAM permissions..."
gcloud projects add-iam-policy-binding fredfix \
  --member="serviceAccount:github-actions@fredfix.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding fredfix \
  --member="serviceAccount:github-actions@fredfix.iam.gserviceaccount.com" \
  --role="roles/compute.osLogin"

gcloud projects add-iam-policy-binding fredfix \
  --member="serviceAccount:github-actions@fredfix.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
echo "🔑 Creating service account key..."
gcloud iam service-accounts keys create ~/github-actions-key.json \
  --iam-account=github-actions@fredfix.iam.gserviceaccount.com

echo ""
echo "✅ Service account key created!"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Copy the content below:"
echo "2. Go to: https://github.com/fredfix/ai-tools/settings/secrets/actions"
echo "3. Click 'New repository secret'"
echo "4. Name: GCP_SA_KEY"
echo "5. Value: [paste the JSON below]"
echo ""
echo "🔑 SERVICE ACCOUNT KEY JSON:"
echo "==========================================="
cat ~/github-actions-key.json
echo ""
echo "==========================================="
echo ""
echo "🚨 IMPORTANT: Delete the local key file after copying:"
echo "rm ~/github-actions-key.json"