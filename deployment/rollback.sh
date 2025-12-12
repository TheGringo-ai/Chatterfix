#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-fredfix}"
SERVICE_NAME="chatterfix"
REGION="us-central1"
DRY_RUN=false
REASON=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --reason)
      REASON="$2"
      shift 2
      ;;
    --service)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}🔄 ChatterFix Rollback Utility${NC}"
echo "=========================================="
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Project: $PROJECT_ID"
if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}Mode: DRY RUN (no changes will be made)${NC}"
fi
echo ""

# Get current revision
echo "📋 Fetching current deployment info..."
CURRENT_REVISION=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(status.latestReadyRevisionName)' 2>/dev/null)

if [ -z "$CURRENT_REVISION" ]; then
  echo -e "${RED}❌ Could not fetch current revision${NC}"
  exit 1
fi

echo -e "Current revision: ${BLUE}$CURRENT_REVISION${NC}"
echo ""

# Get revision history
echo "📜 Fetching revision history..."
REVISIONS=$(gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='table(metadata.name,status.conditions[0].lastTransitionTime,metadata.labels.version)' \
  --limit=5)

echo "$REVISIONS"
echo ""

# Get previous revision
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(metadata.name)' \
  --limit=2 | tail -n 1)

if [ -z "$PREVIOUS_REVISION" ] || [ "$PREVIOUS_REVISION" = "$CURRENT_REVISION" ]; then
  echo -e "${RED}❌ No previous revision found to rollback to${NC}"
  exit 1
fi

echo -e "🎯 Target rollback revision: ${GREEN}$PREVIOUS_REVISION${NC}"
echo ""

# Confirm rollback
if [ "$DRY_RUN" = false ]; then
  echo -e "${YELLOW}⚠️  WARNING: This will rollback the production service${NC}"
  echo -e "${YELLOW}From: $CURRENT_REVISION${NC}"
  echo -e "${YELLOW}To:   $PREVIOUS_REVISION${NC}"
  echo ""
  
  read -p "Are you sure you want to proceed? (yes/no): " -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${BLUE}ℹ️  Rollback cancelled${NC}"
    exit 0
  fi
fi

# Perform rollback
echo "🔄 Performing rollback..."

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}[DRY RUN] Would execute:${NC}"
  echo "gcloud run services update-traffic $SERVICE_NAME \\"
  echo "  --to-revisions=$PREVIOUS_REVISION=100 \\"
  echo "  --region=$REGION \\"
  echo "  --project=$PROJECT_ID"
  echo ""
  echo -e "${GREEN}✅ Dry run completed successfully${NC}"
  exit 0
fi

# Execute rollback
if gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions=$PREVIOUS_REVISION=100 \
  --region=$REGION \
  --project=$PROJECT_ID; then
  
  echo ""
  echo -e "${GREEN}✅ Rollback completed successfully${NC}"
  echo ""
  
  # Log rollback
  TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
  LOG_FILE="deployment/rollback-history.log"
  
  mkdir -p deployment
  echo "$TIMESTAMP | Rollback: $CURRENT_REVISION -> $PREVIOUS_REVISION | Reason: ${REASON:-Manual rollback}" >> $LOG_FILE
  
  echo "📝 Rollback logged to $LOG_FILE"
  echo ""
  
  # Wait for rollback to complete
  echo "⏳ Waiting for rollback to stabilize..."
  sleep 10
  
  # Verify rollback
  NEW_REVISION=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.latestReadyRevisionName)' 2>/dev/null)
  
  if [ "$NEW_REVISION" = "$PREVIOUS_REVISION" ]; then
    echo -e "${GREEN}✅ Rollback verified - service is now running $NEW_REVISION${NC}"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
      --region=$REGION \
      --project=$PROJECT_ID \
      --format='value(status.url)' 2>/dev/null)
    
    echo ""
    echo "🌐 Service URL: $SERVICE_URL"
    echo ""
    echo "💡 Run smoke tests to verify:"
    echo "   ./deployment/smoke-tests.sh $SERVICE_URL"
    echo ""
  else
    echo -e "${YELLOW}⚠️  Warning: Current revision ($NEW_REVISION) doesn't match expected ($PREVIOUS_REVISION)${NC}"
    echo "   This may take a few more moments to propagate"
  fi
  
else
  echo ""
  echo -e "${RED}❌ Rollback failed${NC}"
  exit 1
fi
