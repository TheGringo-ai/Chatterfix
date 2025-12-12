#!/bin/bash

# Firebase Setup Script for ChatterFix
# This script helps set up Firebase Authentication

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔥 Firebase Setup for ChatterFix${NC}"
echo "=================================="

# Get project ID
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No Google Cloud project found.${NC}"
    echo "Please set GOOGLE_CLOUD_PROJECT or run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${YELLOW}📋 Project ID: $PROJECT_ID${NC}"
echo

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${YELLOW}🔧 Installing Firebase CLI...${NC}"
    npm install -g firebase-tools
fi

# Login to Firebase (if not already logged in)
echo -e "${YELLOW}🔐 Checking Firebase authentication...${NC}"
if ! firebase projects:list &> /dev/null; then
    echo -e "${YELLOW}Please log in to Firebase...${NC}"
    firebase login
fi

# Initialize Firebase project
echo -e "${YELLOW}🔥 Setting up Firebase project...${NC}"
firebase use $PROJECT_ID --add

# Enable Authentication
echo -e "${YELLOW}🛡️  Setting up Firebase Authentication...${NC}"
echo "Please enable the following sign-in methods in the Firebase Console:"
echo "1. Email/Password"
echo "2. Google (optional)"
echo "3. Any other providers you want"
echo

# Open Firebase console
echo -e "${BLUE}Opening Firebase Console...${NC}"
echo "https://console.firebase.google.com/project/$PROJECT_ID/authentication/providers"
echo

# Create .env template
echo -e "${YELLOW}📝 Creating environment template...${NC}"
cat > .env.production << EOF
# Firebase Configuration
FIREBASE_API_KEY=your_api_key_here
FIREBASE_AUTH_DOMAIN=$PROJECT_ID.firebaseapp.com
FIREBASE_PROJECT_ID=$PROJECT_ID
FIREBASE_STORAGE_BUCKET=$PROJECT_ID.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id_here
FIREBASE_APP_ID=your_app_id_here

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
USE_FIRESTORE=true
LOG_LEVEL=info
EOF

echo -e "${GREEN}✅ Firebase setup template created!${NC}"
echo "=================================="
echo
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Go to Firebase Console: https://console.firebase.google.com/project/$PROJECT_ID"
echo "2. Enable Authentication with Email/Password"
echo "3. Go to Project Settings > General > Your apps"
echo "4. Create a web app and copy the config values"
echo "5. Update the .env.production file with your Firebase config"
echo "6. Deploy using: ./deploy-gcp.sh"
echo
echo -e "${BLUE}🎉 Firebase setup ready!${NC}"