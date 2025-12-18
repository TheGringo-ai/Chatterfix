#!/bin/bash

# 🚨 ChatterFix Emergency Rollback Script
# Fast rollback to previous working deployment
# Usage: ./rollback.sh [version] [--force]

set -euo pipefail

# Configuration
PROJECT_ID="fredfix"
REGION="us-central1"
SERVICE_NAME="gringo-core"
AI_SERVICE_NAME="ai-team-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Emergency banner
echo -e "${RED}"
echo "🚨 ChatterFix Emergency Rollback System"
echo "======================================"
echo -e "${NC}"

# Parse arguments
ROLLBACK_VERSION=""
FORCE_ROLLBACK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_ROLLBACK=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [version] [--force]"
            echo ""
            echo "Options:"
            echo "  version     Specific version to rollback to (optional)"
            echo "  --force     Skip confirmation prompts"
            echo ""
            echo "Examples:"
            echo "  $0                    # Rollback to previous version"
            echo "  $0 v2.1.0            # Rollback to specific version"
            echo "  $0 --force           # Emergency rollback without prompts"
            exit 0
            ;;
        *)
            ROLLBACK_VERSION="$1"
            shift
            ;;
    esac
done

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "Not authenticated with Google Cloud. Run: gcloud auth login"
    exit 1
fi

gcloud config set project $PROJECT_ID --quiet

# Get current service status
log "Checking current service status..."
CURRENT_SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
CURRENT_IMAGE=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.spec.template.spec.containers[0].image)" 2>/dev/null || echo "")

if [[ -z "$CURRENT_SERVICE_URL" ]]; then
    error "Service $SERVICE_NAME not found in region $REGION"
    exit 1
fi

log "Current service: $CURRENT_SERVICE_URL"
log "Current image: $CURRENT_IMAGE"

# Function to get available revisions
get_available_revisions() {
    echo "Available revisions for rollback:"
    gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --format="table(metadata.name,status.conditions[0].lastTransitionTime,spec.template.spec.template.spec.containers[0].image)" --limit=10
}

# If no specific version provided, show available options
if [[ -z "$ROLLBACK_VERSION" ]]; then
    log "Getting available revisions..."
    get_available_revisions
    echo ""
    
    if [[ "$FORCE_ROLLBACK" != "true" ]]; then
        # Get the most recent revision that's not current
        PREVIOUS_REVISION=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --format="value(metadata.name)" --limit=2 | sed -n '2p')
        
        if [[ -z "$PREVIOUS_REVISION" ]]; then
            error "No previous revision found for rollback"
            exit 1
        fi
        
        warning "Auto-selected previous revision: $PREVIOUS_REVISION"
        read -p "Continue with this rollback? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Rollback cancelled by user"
            exit 0
        fi
        ROLLBACK_VERSION="$PREVIOUS_REVISION"
    else
        # Force mode - get most recent revision
        ROLLBACK_VERSION=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --format="value(metadata.name)" --limit=2 | sed -n '2p')
        if [[ -z "$ROLLBACK_VERSION" ]]; then
            error "No previous revision found for emergency rollback"
            exit 1
        fi
        warning "Emergency rollback to: $ROLLBACK_VERSION"
    fi
fi

# Validate rollback target
if ! gcloud run revisions describe "$ROLLBACK_VERSION" --region=$REGION --service=$SERVICE_NAME >/dev/null 2>&1; then
    error "Revision '$ROLLBACK_VERSION' not found"
    log "Available revisions:"
    get_available_revisions
    exit 1
fi

# Get rollback target details
ROLLBACK_IMAGE=$(gcloud run revisions describe "$ROLLBACK_VERSION" --region=$REGION --service=$SERVICE_NAME --format="value(spec.template.spec.template.spec.containers[0].image)" 2>/dev/null || echo "unknown")

log "Rollback target: $ROLLBACK_VERSION"
log "Rollback image: $ROLLBACK_IMAGE"

# Final confirmation (unless force mode)
if [[ "$FORCE_ROLLBACK" != "true" ]]; then
    echo ""
    warning "DANGER: This will rollback the production service!"
    warning "Current: $CURRENT_IMAGE"
    warning "Rollback to: $ROLLBACK_IMAGE"
    echo ""
    read -p "Are you absolutely sure? Type 'ROLLBACK' to confirm: " -r
    if [[ $REPLY != "ROLLBACK" ]]; then
        log "Rollback cancelled by user"
        exit 0
    fi
fi

# Start rollback timer
start_time=$(date +%s)
log "Starting emergency rollback..."

# Step 1: Rollback main service
log "Rolling back main service to revision: $ROLLBACK_VERSION"

gcloud run services update-traffic $SERVICE_NAME \
    --region=$REGION \
    --to-revisions="$ROLLBACK_VERSION=100" \
    --quiet

success "Traffic switched to rollback revision"

# Step 2: Quick health check
log "Performing post-rollback health check..."
sleep 5

ROLLBACK_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

# Health check with retries
health_check_passed=false
for i in {1..6}; do
    if curl -f -s --connect-timeout 5 --max-time 10 "$ROLLBACK_URL/health" >/dev/null 2>&1; then
        success "Health check passed"
        health_check_passed=true
        break
    fi
    warning "Health check attempt $i/6 failed, retrying in 5 seconds..."
    sleep 5
done

if [[ "$health_check_passed" != "true" ]]; then
    error "CRITICAL: Health check failed after rollback!"
    error "Service may be in degraded state"
    error "Manual intervention required"
    
    # Show current status for debugging
    log "Current service status:"
    gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.conditions)"
    
    exit 1
fi

# Step 3: Test critical endpoints
log "Testing critical application endpoints..."

# Test main page
if curl -f -s --connect-timeout 5 --max-time 10 "$ROLLBACK_URL/" >/dev/null 2>&1; then
    success "Main page accessible"
else
    warning "Main page test failed"
fi

# Test demo endpoint
if curl -f -s --connect-timeout 5 --max-time 10 "$ROLLBACK_URL/demo" >/dev/null 2>&1; then
    success "Demo endpoint accessible"
else
    warning "Demo endpoint test failed"
fi

# Calculate rollback time
end_time=$(date +%s)
rollback_time=$((end_time - start_time))

echo ""
echo -e "${GREEN}🎉 Rollback Completed Successfully!${NC}"
echo "==============================="
echo -e "${BLUE}⏱️  Rollback time: ${rollback_time} seconds${NC}"
echo ""
echo -e "${BLUE}📊 Rollback Details:${NC}"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Rolled back to: $ROLLBACK_VERSION"
echo "   Current URL: $ROLLBACK_URL"
echo ""
echo -e "${BLUE}🔍 Verification:${NC}"
echo "   Health: $ROLLBACK_URL/health"
echo "   Detailed: $ROLLBACK_URL/health/detailed"
echo "   Demo: $ROLLBACK_URL/demo"
echo ""

# Post-rollback recommendations
echo -e "${YELLOW}📝 Post-Rollback Action Items:${NC}"
echo "1. Monitor service metrics for stability"
echo "2. Check application logs for any issues"
echo "3. Verify all critical features are working"
echo "4. Investigate root cause of original deployment issue"
echo "5. Plan forward fix deployment when ready"
echo ""

# Show command to view logs
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "   View logs: gcloud run services logs read $SERVICE_NAME --region $REGION"
echo "   View revisions: gcloud run revisions list --service $SERVICE_NAME --region $REGION"
echo "   Current status: curl $ROLLBACK_URL/health/detailed"
echo ""

success "Service successfully rolled back and verified!"

# Optional: Send notification (if configured)
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    log "Sending rollback notification..."
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 ChatterFix Emergency Rollback Completed\\nService: $SERVICE_NAME\\nRevision: $ROLLBACK_VERSION\\nTime: ${rollback_time}s\\nURL: $ROLLBACK_URL\"}" \
        "$SLACK_WEBHOOK_URL" || warning "Failed to send Slack notification"
fi

warning "Remember to investigate and fix the original issue!"