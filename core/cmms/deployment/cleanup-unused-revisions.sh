#!/bin/bash

# ChatterFix CMMS - Cleanup Unused Cloud Run Revisions
# This will free up CPU quota by deleting inactive revisions

echo "🧹 ChatterFix CMMS - Cleaning Up Unused Revisions"
echo "=================================================="
echo "This will free up CPU quota by removing inactive revisions"
echo ""

REGION="us-central1"

echo "📊 Getting list of inactive revisions..."

# Get all revisions that are NOT actively serving traffic
INACTIVE_REVISIONS=$(gcloud run revisions list --region=$REGION --format="value(name)" --filter="status.conditions[0].status:False")

echo "Found inactive revisions to delete:"
echo "$INACTIVE_REVISIONS"
echo ""

if [ -z "$INACTIVE_REVISIONS" ]; then
    echo "✅ No inactive revisions found to clean up"
else
    echo "🗑️ Deleting inactive revisions to free up CPU quota..."
    
    for revision in $INACTIVE_REVISIONS; do
        echo "Deleting revision: $revision"
        gcloud run revisions delete $revision --region=$REGION --quiet
    done
    
    echo ""
    echo "✅ Cleanup complete!"
fi

echo ""
echo "📊 Checking quota usage after cleanup..."
echo "Go to: https://console.cloud.google.com/iam-admin/quotas?project=fredfix"
echo "Look for: Cloud Run Admin API > Total CPU allocation"
echo ""
echo "🚀 After cleanup, you should have free CPU quota to deploy unified services!"
echo "Run: ./deploy-consolidated-services.sh"