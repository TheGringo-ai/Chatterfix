#!/bin/bash

set -e

echo "🧹 Cleaning up old ChatterFix services to reduce resource usage"
echo "=============================================================="

# List of services to potentially remove (keeping main gateway and new consolidated service)
OLD_SERVICES=(
    "chatterfix-assets"
    "chatterfix-parts"
    "chatterfix-work-orders"
    "chatterfix-customer-success"
    "chatterfix-data-room"
    "chatterfix-revenue-intelligence"
    "chatterfix-fix-it-fred-enhanced"
    "chatterfix-unified-gateway-enhanced"
)

REGION="us-central1"

echo "📋 Current services before cleanup:"
gcloud run services list --region=$REGION --format="table(metadata.name,status.url)"

echo ""
echo "⚠️  This will delete the following services:"
for service in "${OLD_SERVICES[@]}"; do
    echo "  - $service"
done

echo ""
read -p "Are you sure you want to delete these services? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

# Delete services
for service in "${OLD_SERVICES[@]}"; do
    echo "🗑️  Deleting service: $service"
    gcloud run services delete $service --region=$REGION --quiet || echo "⚠️  Service $service not found or already deleted"
done

echo ""
echo "✅ Cleanup complete!"
echo "📋 Remaining services:"
gcloud run services list --region=$REGION --format="table(metadata.name,status.url)"

echo ""
echo "💡 Resource savings achieved by consolidating multiple services into one!"
echo "🎯 Keep these services running:"
echo "  - chatterfix-consolidated-cmms (work orders + assets + parts)"
echo "  - chatterfix-gateway-phase7 or chatterfix-unified-gateway-east (main UI)"