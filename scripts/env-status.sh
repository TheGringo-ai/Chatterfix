#!/bin/bash
# =============================================================================
# ENVIRONMENT STATUS
# =============================================================================
# Shows the status of both DEV and PROD environments
# =============================================================================

echo "🔍 CHATTERFIX ENVIRONMENT STATUS"
echo "=================================="
echo ""

# DEV Environment
echo "📦 DEV ENVIRONMENT (gringo-core)"
echo "-----------------------------------"
DEV_REVISION=$(gcloud run services describe gringo-core --region us-central1 --project fredfix --format="value(status.latestReadyRevisionName)" 2>/dev/null)
echo "   Revision: $DEV_REVISION"
echo "   URL: https://gringo-core-650169261019.us-central1.run.app"
echo "   Demo: https://gringo-core-650169261019.us-central1.run.app/demo"
echo ""

# PROD Environment
echo "🚀 PROD ENVIRONMENT (chatterfix-cmms)"
echo "-----------------------------------"
PROD_REVISION=$(gcloud run services describe chatterfix-cmms --region us-central1 --project fredfix --format="value(status.latestReadyRevisionName)" 2>/dev/null)
echo "   Revision: $PROD_REVISION"
echo "   URL: https://chatterfix.com"
echo "   Demo: https://chatterfix.com/demo"
echo ""

# Compare
echo "📊 COMPARISON"
echo "-----------------------------------"
if [[ "$DEV_REVISION" == "$PROD_REVISION" ]]; then
    echo "   ✅ DEV and PROD are in sync!"
else
    echo "   ⚠️  DEV and PROD are DIFFERENT"
    echo "   DEV:  $DEV_REVISION"
    echo "   PROD: $PROD_REVISION"
    echo ""
    echo "   Run ./scripts/deploy-prod.sh to sync"
fi
echo ""

# Quick commands
echo "📋 QUICK COMMANDS"
echo "-----------------------------------"
echo "   Deploy to DEV:  ./scripts/deploy-dev.sh"
echo "   Deploy to PROD: ./scripts/deploy-prod.sh"
echo "   View this:      ./scripts/env-status.sh"
echo ""
