#!/bin/bash

# ChatterFix Sync & Deploy
# One command to sync everything and deploy

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔄 ChatterFix Sync & Deploy${NC}"
echo "============================"

# 1. Sync check
echo -e "${YELLOW}1. 🔍 Running sync verification...${NC}"
if ! ./sync-check.sh; then
    echo -e "${RED}❌ Sync issues detected. Fix them first.${NC}"
    exit 1
fi

# 2. Commit changes if any
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}2. 💾 Auto-committing changes...${NC}"
    git add .
    echo -n "Commit message (or press Enter for auto): "
    read -r commit_msg
    if [ -z "$commit_msg" ]; then
        commit_msg="auto: sync and deploy $(date '+%Y-%m-%d %H:%M')"
    fi
    git commit -m "$commit_msg"
else
    echo -e "${GREEN}2. ✅ No changes to commit${NC}"
fi

# 3. Push to repository
echo -e "${YELLOW}3. ⬆️  Pushing to repository...${NC}"
git push origin main

# 4. Choose deployment method
echo -e "${YELLOW}4. 🚀 Choose deployment:${NC}"
echo "   f = Fast deploy (~2 min)"
echo "   p = Production deploy (~10 min)"
echo -n "Choice (f/p): "
read -r deploy_choice

case $deploy_choice in
    f|F)
        echo -e "${GREEN}⚡ Fast deployment...${NC}"
        gcloud run deploy chatterfix-cmms \
            --source . \
            --region=us-central1 \
            --project=fredfix \
            --allow-unauthenticated \
            --quiet
        ;;
    p|P)
        echo -e "${GREEN}🏭 Production deployment...${NC}"
        ./deploy-production.sh
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Sync & Deploy Complete!${NC}"
echo "🌍 Live at: https://chatterfix.com"