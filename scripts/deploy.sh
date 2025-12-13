#!/bin/bash

# ChatterFix CMMS - Cloud Deployment Script
# Technician-First CMMS with AI-Enhanced Development

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="chatterfix-cmms"
DOCKER_IMAGE="chatterfix:latest"
CLOUD_REGION="us-central1"
CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-fredfix}"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        warn "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        warn "kubectl not found. Installing..."
        gcloud components install kubectl
    fi
    
    success "Prerequisites check complete"
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    
    # Clean build with no cache for production
    docker build --no-cache -t "$DOCKER_IMAGE" .
    
    # Tag for cloud registry
    docker tag "$DOCKER_IMAGE" "gcr.io/${CLOUD_PROJECT}/${PROJECT_NAME}:latest"
    docker tag "$DOCKER_IMAGE" "gcr.io/${CLOUD_PROJECT}/${PROJECT_NAME}:$(date +%Y%m%d-%H%M%S)"
    
    success "Docker image built successfully"
}

# Push to cloud registry
push_image() {
    log "Pushing image to Google Cloud Registry..."
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    # Push images
    docker push "gcr.io/${CLOUD_PROJECT}/${PROJECT_NAME}:latest"
    docker push "gcr.io/${CLOUD_PROJECT}/${PROJECT_NAME}:$(date +%Y%m%d-%H%M%S)"
    
    success "Image pushed to cloud registry"
}

# Deploy to Cloud Run
deploy_cloud_run() {
    log "Deploying to Cloud Run..."
    
    # Deploy with optimized settings for ChatterFix CMMS
    gcloud run deploy "$PROJECT_NAME" \
        --image "gcr.io/${CLOUD_PROJECT}/${PROJECT_NAME}:latest" \
        --region "$CLOUD_REGION" \
        --platform managed \
        --port 8080 \
        --memory 4Gi \
        --cpu 4 \
        --min-instances 2 \
        --max-instances 20 \
        --timeout 900 \
        --concurrency 80 \
        --allow-unauthenticated \
        --set-env-vars "ENVIRONMENT=production,USE_FIRESTORE=true,LOG_LEVEL=info,REDIS_URL=redis://redis:6379" \
        --execution-environment gen2 \
        --cpu-boost \
        --session-affinity \
        --quiet
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$PROJECT_NAME" \
        --region "$CLOUD_REGION" \
        --format="value(status.url)")
    
    # Update traffic to latest revision
    gcloud run services update-traffic "$PROJECT_NAME" \
        --region "$CLOUD_REGION" \
        --to-latest \
        --quiet
    
    success "Deployed to Cloud Run: $SERVICE_URL"
    
    # Test deployment
    log "Testing deployment..."
    sleep 10
    if curl -f --max-time 30 "${SERVICE_URL}/health" >/dev/null 2>&1; then
        success "Health check passed ✓"
        success "ChatterFix CMMS is live at: $SERVICE_URL"
    else
        error "Health check failed - checking logs..."
        gcloud run services logs read "$PROJECT_NAME" --region "$CLOUD_REGION" --limit=20
    fi
}

# Deploy to GKE (optional)
deploy_gke() {
    log "Deploying to Google Kubernetes Engine..."
    
    # Apply Kubernetes manifests
    if [ -d "k8s" ]; then
        kubectl apply -f k8s/
        success "Deployed to GKE cluster"
    else
        warn "No k8s directory found, skipping GKE deployment"
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    if [ -n "${SERVICE_URL:-}" ]; then
        # Wait a moment for deployment
        sleep 10
        
        # Check health endpoint
        if curl -f "${SERVICE_URL}/health" &>/dev/null; then
            success "Health check passed"
        else
            error "Health check failed"
            exit 1
        fi
    else
        warn "No service URL available for health check"
    fi
}

# Main deployment function
main() {
    log "Starting ChatterFix CMMS deployment..."
    
    # Parse arguments
    DEPLOYMENT_TYPE="${1:-cloud-run}"
    
    case "$DEPLOYMENT_TYPE" in
        "cloud-run")
            check_prerequisites
            build_image
            push_image
            deploy_cloud_run
            health_check
            ;;
        "gke")
            check_prerequisites
            build_image
            push_image
            deploy_gke
            ;;
        "local")
            build_image
            log "Starting local deployment..."
            docker-compose up -d
            success "Local deployment started"
            ;;
        *)
            error "Unknown deployment type: $DEPLOYMENT_TYPE"
            echo "Usage: $0 [cloud-run|gke|local]"
            exit 1
            ;;
    esac
    
    success "ChatterFix CMMS deployment complete!"
    log "🎯 Technician-first CMMS is ready for hands-free operation"
}

# Run main function
main "$@"