#!/bin/bash

# ChatterFix Sync Verification Script
# Ensures local files, repository, and deployment are all synchronized

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 ChatterFix Sync Verification${NC}"
echo "================================="
echo

# ============================================================================
# 1. CHECK GIT STATUS
# ============================================================================
echo -e "${YELLOW}📋 Checking Git Status...${NC}"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📌 Current branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if ! git diff --quiet; then
    echo -e "${YELLOW}⚠️  Uncommitted changes detected:${NC}"
    git status --porcelain
    echo -e "${YELLOW}   Run 'git add .' and 'git commit' to fix${NC}"
    SYNC_ISSUES=true
else
    echo -e "${GREEN}✅ Working directory clean${NC}"
fi

# Check for untracked files (excluding secrets and temp files)
UNTRACKED=$(git ls-files --others --exclude-standard | grep -v "^secrets/" | grep -v "^scripts/" | grep -v "__pycache__" | grep -v ".pyc$" || true)
if [ -n "$UNTRACKED" ]; then
    echo -e "${YELLOW}⚠️  Important untracked files:${NC}"
    echo "$UNTRACKED" | sed 's/^/   /'
    echo -e "${YELLOW}   Consider adding these to git${NC}"
    SYNC_ISSUES=true
else
    echo -e "${GREEN}✅ No important untracked files${NC}"
fi

echo

# ============================================================================
# 2. CHECK REMOTE SYNC
# ============================================================================
echo -e "${YELLOW}🌐 Checking Remote Sync...${NC}"

# Fetch latest from remote
git fetch origin --quiet

# Check if local is ahead/behind remote
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
BASE=$(git merge-base @ @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo -e "${YELLOW}⚠️  No upstream branch set${NC}"
    SYNC_ISSUES=true
elif [ $LOCAL = $REMOTE ]; then
    echo -e "${GREEN}✅ Local and remote are in sync${NC}"
elif [ $LOCAL = $BASE ]; then
    echo -e "${YELLOW}⚠️  Local is behind remote (need to pull)${NC}"
    echo -e "${YELLOW}   Run 'git pull' to sync${NC}"
    SYNC_ISSUES=true
elif [ $REMOTE = $BASE ]; then
    echo -e "${YELLOW}⚠️  Local is ahead of remote (need to push)${NC}"
    echo -e "${YELLOW}   Run 'git push' to sync${NC}"
    SYNC_ISSUES=true
else
    echo -e "${RED}❌ Local and remote have diverged${NC}"
    echo -e "${RED}   Manual merge required${NC}"
    SYNC_ISSUES=true
fi

echo

# ============================================================================
# 3. CHECK DEPLOYMENT CONFIGURATION
# ============================================================================
echo -e "${YELLOW}⚙️  Checking Deployment Configuration...${NC}"

# Check if deployment files exist
DEPLOYMENT_FILES=(
    "deploy-production.sh"
    ".deployment-config"
    ".firebaserc"
    "firebase.json"
    "cloudbuild-prod.yaml"
)

for file in "${DEPLOYMENT_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
        SYNC_ISSUES=true
    fi
done

# Check deployment script is executable
if [ -x "deploy-production.sh" ]; then
    echo -e "${GREEN}✅ deploy-production.sh is executable${NC}"
else
    echo -e "${YELLOW}⚠️  deploy-production.sh not executable${NC}"
    chmod +x deploy-production.sh
    echo -e "${GREEN}✅ Fixed executable permission${NC}"
fi

echo

# ============================================================================
# 4. CHECK GCP CONFIGURATION
# ============================================================================
echo -e "${YELLOW}☁️  Checking GCP Configuration...${NC}"

# Check gcloud is configured
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not installed${NC}"
    SYNC_ISSUES=true
else
    # Check current project
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    EXPECTED_PROJECT="fredfix"
    
    if [ "$CURRENT_PROJECT" = "$EXPECTED_PROJECT" ]; then
        echo -e "${GREEN}✅ GCP project: $CURRENT_PROJECT${NC}"
    else
        echo -e "${YELLOW}⚠️  Wrong GCP project: $CURRENT_PROJECT (expected: $EXPECTED_PROJECT)${NC}"
        echo -e "${YELLOW}   Run 'gcloud config set project $EXPECTED_PROJECT'${NC}"
        SYNC_ISSUES=true
    fi
    
    # Check if service exists
    if gcloud run services describe chatterfix-cmms --region=us-central1 --quiet > /dev/null 2>&1; then
        echo -e "${GREEN}✅ chatterfix-cmms service exists${NC}"
    else
        echo -e "${RED}❌ chatterfix-cmms service not found${NC}"
        SYNC_ISSUES=true
    fi
fi

echo

# ============================================================================
# 5. CHECK FIREBASE CONFIGURATION
# ============================================================================
echo -e "${YELLOW}🔥 Checking Firebase Configuration...${NC}"

# Check Firebase credentials
if [ -f "secrets/firebase-admin.json" ]; then
    echo -e "${GREEN}✅ Firebase admin credentials exist${NC}"
else
    echo -e "${RED}❌ Firebase admin credentials missing${NC}"
    echo -e "${RED}   File should be at: secrets/firebase-admin.json${NC}"
    SYNC_ISSUES=true
fi

# Check Firebase CLI
if command -v firebase &> /dev/null; then
    echo -e "${GREEN}✅ Firebase CLI installed${NC}"
    
    # Check if firebase project is set
    if firebase use 2>/dev/null | grep -q "fredfix"; then
        echo -e "${GREEN}✅ Firebase project set to fredfix${NC}"
    else
        echo -e "${YELLOW}⚠️  Firebase project not set to fredfix${NC}"
        echo -e "${YELLOW}   Run 'firebase use fredfix'${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Firebase CLI not installed${NC}"
    echo -e "${YELLOW}   Run 'npm install -g firebase-tools'${NC}"
fi

echo

# ============================================================================
# 6. FINAL SYNC REPORT
# ============================================================================
echo "================================="
if [ "${SYNC_ISSUES}" = "true" ]; then
    echo -e "${RED}❌ SYNC ISSUES DETECTED${NC}"
    echo -e "${YELLOW}📋 To fix sync issues:${NC}"
    echo "   1. Fix any git status issues above"
    echo "   2. Commit and push changes to repository"
    echo "   3. Ensure GCP project is set to 'fredfix'"
    echo "   4. Verify Firebase configuration"
    echo "   5. Run this script again to verify"
    echo
    exit 1
else
    echo -e "${GREEN}✅ EVERYTHING IS IN SYNC!${NC}"
    echo -e "${GREEN}🚀 Ready for deployment${NC}"
    echo
    echo "Your system is perfectly synchronized:"
    echo "  ✅ Local files committed"
    echo "  ✅ Repository up to date"  
    echo "  ✅ GCP configured correctly"
    echo "  ✅ Firebase ready"
    echo "  ✅ Deployment files present"
    echo
    echo "Safe to deploy with: ./deploy-production.sh"
    exit 0
fi