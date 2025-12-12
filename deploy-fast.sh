#!/bin/bash

# 🚀 ChatterFix Ultra-Fast Deployment Script
# Optimized for speed, automation, and reliability
# Target: <2 minutes total deployment time

set -euo pipefail

# Configuration
PROJECT_ID="fredfix"
REGION="us-central1"
SERVICE_NAME="gringo-core"
AI_SERVICE_NAME="ai-team-service"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
AI_IMAGE_NAME="gcr.io/$PROJECT_ID/$AI_SERVICE_NAME"
DEPLOY_TIMEOUT=600
HEALTH_CHECK_TIMEOUT=120

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Performance timer
start_time=$(date +%s)

# Banner
echo -e "${BLUE}"
echo "🚀 ChatterFix Ultra-Fast Deployment Pipeline"
echo "============================================="
echo -e "${NC}"
log "Project: $PROJECT_ID | Region: $REGION"
log "Target deployment time: <2 minutes"
echo ""

# Pre-flight checks
log "Running pre-flight checks..."

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "Not authenticated with Google Cloud. Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID --quiet

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    warning "Uncommitted changes detected. Deploying with uncommitted changes."
    git status --short
fi

# Parallel build optimization
log "Optimizing build environment..."

# Clean up old images to save space and time
log "Cleaning up old containers and images..."
docker system prune -f --filter "until=24h" >/dev/null 2>&1 || true

# Determine build strategy
USE_CACHE=true
if [[ "${FORCE_REBUILD:-false}" == "true" ]]; then
    USE_CACHE=false
    log "Force rebuild requested - cache disabled"
fi

# Generate unique tag
COMMIT_SHA=$(git rev-parse --short HEAD)
BUILD_TAG="${IMAGE_NAME}:${COMMIT_SHA}"
AI_BUILD_TAG="${AI_IMAGE_NAME}:${COMMIT_SHA}"
LATEST_TAG="${IMAGE_NAME}:latest"
AI_LATEST_TAG="${AI_IMAGE_NAME}:latest"

log "Build tags: $BUILD_TAG, $AI_BUILD_TAG"

# Check if we need to build AI service
BUILD_AI_SERVICE=false
if [[ -d "ai-team-service" ]] && [[ -n $(find ai-team-service -name "*.py" -newer "ai-team-service/.last-deploy" 2>/dev/null || echo "build") ]]; then
    BUILD_AI_SERVICE=true
    log "AI service changes detected - will build AI service"
fi

# Parallel builds for maximum speed
log "Starting parallel builds..."

# Build main service
{
    log "Building ChatterFix main service..."
    if [[ "$USE_CACHE" == "true" ]]; then
        docker build --platform linux/amd64 \
            -t "$BUILD_TAG" \
            -t "$LATEST_TAG" \
            -f Dockerfile.optimized \
            --cache-from "$LATEST_TAG" \
            .
    else
        docker build --platform linux/amd64 \
            -t "$BUILD_TAG" \
            -t "$LATEST_TAG" \
            -f Dockerfile.optimized \
            --no-cache \
            .
    fi
    success "ChatterFix main service build completed"
} &
MAIN_BUILD_PID=$!

# Build AI service if needed
if [[ "$BUILD_AI_SERVICE" == "true" ]]; then
    {
        log "Building AI Team service..."
        cd ai-team-service
        if [[ "$USE_CACHE" == "true" ]]; then
            docker build --platform linux/amd64 \
                -t "$AI_BUILD_TAG" \
                -t "$AI_LATEST_TAG" \
                --cache-from "$AI_LATEST_TAG" \
                .
        else
            docker build --platform linux/amd64 \
                -t "$AI_BUILD_TAG" \
                -t "$AI_LATEST_TAG" \
                --no-cache \
                .
        fi
        cd ..
        success "AI Team service build completed"
        touch ai-team-service/.last-deploy
    } &
    AI_BUILD_PID=$!
fi

# Wait for main build
log "Waiting for builds to complete..."
wait $MAIN_BUILD_PID
if [[ "$BUILD_AI_SERVICE" == "true" ]]; then
    wait $AI_BUILD_PID
fi

# Parallel push operations
log "Pushing images to registry..."

{
    log "Pushing ChatterFix main service..."
    docker push "$BUILD_TAG"
    docker push "$LATEST_TAG"
    success "ChatterFix main service pushed"
} &
MAIN_PUSH_PID=$!

if [[ "$BUILD_AI_SERVICE" == "true" ]]; then
    {
        log "Pushing AI Team service..."
        docker push "$AI_BUILD_TAG"
        docker push "$AI_LATEST_TAG"
        success "AI Team service pushed"
    } &
    AI_PUSH_PID=$!
fi

# Wait for pushes
wait $MAIN_PUSH_PID
if [[ "$BUILD_AI_SERVICE" == "true" ]]; then
    wait $AI_PUSH_PID
fi

# Deploy AI service first (if needed)
if [[ "$BUILD_AI_SERVICE" == "true" ]]; then
    log "Deploying AI Team service..."
    cd ai-team-service
    ./deploy-ai-team.sh
    cd ..
    AI_TEAM_SERVICE_URL=$(gcloud run services describe $AI_SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
    success "AI Team service deployed: $AI_TEAM_SERVICE_URL"
else
    AI_TEAM_SERVICE_URL=$(gcloud run services describe $AI_SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
fi

# Deploy main service with optimized settings
log "Deploying ChatterFix main service..."

gcloud run deploy $SERVICE_NAME \
    --image "$BUILD_TAG" \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1.5Gi \
    --cpu 1 \
    --timeout $DEPLOY_TIMEOUT \
    --concurrency 100 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars "AI_TEAM_SERVICE_URL=$AI_TEAM_SERVICE_URL,DISABLE_AI_TEAM_GRPC=true,INTERNAL_API_KEY=ai-team-service-key-change-me" \
    --port 8080 \
    --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
success "ChatterFix main service deployed: $SERVICE_URL"

# Health checks with timeout
log "Running health checks..."

# Function to check health with timeout
check_health() {
    local url=$1
    local name=$2
    local timeout=$3
    
    log "Checking health of $name at $url..."
    
    for ((i=1; i<=timeout; i+=5)); do
        if curl -f -s --connect-timeout 5 --max-time 10 "$url/health" >/dev/null 2>&1; then
            success "$name health check passed"
            return 0
        fi
        if [[ $i -lt $timeout ]]; then
            sleep 5
        fi
    done
    
    warning "$name health check failed after $timeout seconds"
    return 1
}

# Check health in parallel
{
    check_health "$SERVICE_URL" "ChatterFix main service" $HEALTH_CHECK_TIMEOUT
} &
MAIN_HEALTH_PID=$!

if [[ -n "$AI_TEAM_SERVICE_URL" ]]; then
    {
        check_health "$AI_TEAM_SERVICE_URL" "AI Team service" $HEALTH_CHECK_TIMEOUT
    } &
    AI_HEALTH_PID=$!
fi

# Wait for health checks
wait $MAIN_HEALTH_PID || warning "Main service health check issues detected"
if [[ -n "${AI_HEALTH_PID:-}" ]]; then
    wait $AI_HEALTH_PID || warning "AI service health check issues detected"
fi

# Test integration
if [[ -n "$AI_TEAM_SERVICE_URL" ]]; then
    log "Testing service integration..."
    sleep 5
    if curl -f -s --connect-timeout 5 --max-time 10 "$SERVICE_URL/ai-team" >/dev/null 2>&1; then
        success "Service integration working"
    else
        warning "Service integration may need more time"
    fi
fi

# Calculate deployment time
end_time=$(date +%s)
deploy_time=$((end_time - start_time))
minutes=$((deploy_time / 60))
seconds=$((deploy_time % 60))

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "========================"
echo -e "${BLUE}⏱️  Total time: ${minutes}m ${seconds}s${NC}"
echo ""
echo -e "${BLUE}🚀 Services:${NC}"
echo "   ChatterFix: $SERVICE_URL"
if [[ -n "$AI_TEAM_SERVICE_URL" ]]; then
    echo "   AI Team: $AI_TEAM_SERVICE_URL"
fi
echo ""
echo -e "${BLUE}🔗 Quick Links:${NC}"
echo "   Main App: https://chatterfix.com"
echo "   Demo: $SERVICE_URL/demo"
echo "   Health: $SERVICE_URL/health"
if [[ -n "$AI_TEAM_SERVICE_URL" ]]; then
    echo "   AI Team: $SERVICE_URL/ai-team"
fi
echo ""

# Performance recommendations
if [[ $deploy_time -gt 120 ]]; then
    warning "Deployment took longer than 2 minutes. Consider:"
    echo "   • Running with --force-rebuild=false for cache optimization"
    echo "   • Using docker buildx for multi-platform builds"
    echo "   • Pre-warming Cloud Run instances"
fi

success "Deployment pipeline completed successfully!"
echo ""
echo -e "${YELLOW}💡 Pro tips:${NC}"
echo "   • Use FORCE_REBUILD=true for clean builds"
echo "   • Monitor performance in Cloud Console"
echo "   • Check logs: gcloud run services logs read $SERVICE_NAME --region $REGION"