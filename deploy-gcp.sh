#!/bin/bash
# ChatterFix AI Services GCP Deployment Script
# Designed with AI Team collaboration

set -e

echo "🚀 ChatterFix AI Services GCP Deployment"
echo "🤖 Designed with AI Team collaboration"

# Configuration
PROJECT_ID=${PROJECT_ID:-"chatterfix-ai"}
REGION="us-central1"
ZONE="us-central1-a"
CLUSTER_NAME="ai-services-cluster"
SERVICE_NAME="ai-services"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Setup GCP project
setup_project() {
    log_info "Setting up GCP project: $PROJECT_ID"
    
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log_info "Enabling required GCP APIs..."
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        container.googleapis.com \
        secretmanager.googleapis.com \
        storage.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com
    
    log_success "GCP project setup complete"
}

# Create storage buckets
create_storage() {
    log_info "Creating Cloud Storage buckets..."
    
    # Create lifecycle configuration file
    cat > /tmp/lifecycle.json <<'EOL'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
EOL
    
    # AI Memory bucket
    MEMORY_BUCKET="chatterfix-ai-memory-$PROJECT_ID"
    if ! gsutil ls -b gs://$MEMORY_BUCKET &> /dev/null; then
        gsutil mb -l $REGION gs://$MEMORY_BUCKET
        gsutil lifecycle set /tmp/lifecycle.json gs://$MEMORY_BUCKET
        log_success "Created AI memory bucket: gs://$MEMORY_BUCKET"
    else
        log_warning "AI memory bucket already exists"
    fi
    
    # Model artifacts bucket
    MODELS_BUCKET="chatterfix-models-$PROJECT_ID"
    if ! gsutil ls -b gs://$MODELS_BUCKET &> /dev/null; then
        gsutil mb -l $REGION gs://$MODELS_BUCKET
        gsutil lifecycle set /tmp/lifecycle.json gs://$MODELS_BUCKET
        log_success "Created models bucket: gs://$MODELS_BUCKET"
    else
        log_warning "Models bucket already exists"
    fi
    
    # Cleanup
    rm -f /tmp/lifecycle.json
}

# Setup secrets
setup_secrets() {
    log_info "Setting up API key secrets..."
    
    # Check if secrets exist, create placeholders if not
    SECRETS=("openai-api-key" "anthropic-api-key" "google-api-key" "xai-api-key")
    
    for secret in "${SECRETS[@]}"; do
        if ! gcloud secrets describe $secret &> /dev/null; then
            echo "placeholder-key-change-me" | gcloud secrets create $secret --data-file=-
            log_warning "Created placeholder secret: $secret (CHANGE THIS!)"
        else
            log_info "Secret $secret already exists"
        fi
    done
    
    log_warning "Remember to update secret values with actual API keys!"
}

# Create GKE cluster
create_cluster() {
    log_info "Creating GKE cluster for gRPC services..."
    
    if ! gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE &> /dev/null; then
        gcloud container clusters create $CLUSTER_NAME \
            --zone=$ZONE \
            --num-nodes=2 \
            --machine-type=e2-standard-2 \
            --enable-autoscaling \
            --max-nodes=10 \
            --min-nodes=1 \
            --enable-autorepair \
            --enable-autoupgrade \
            --disk-size=20GB \
            --disk-type=pd-standard \
            --no-enable-basic-auth \
            --no-issue-client-certificate \
            --enable-ip-alias \
            --enable-stackdriver-kubernetes
        
        log_success "GKE cluster created: $CLUSTER_NAME"
    else
        log_warning "GKE cluster already exists"
    fi
    
    # Get cluster credentials
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    log_info "Deploying Kubernetes resources..."
    
    # Create namespace
    kubectl create namespace ai-services --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy AI Team gRPC service
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-team-grpc
  namespace: ai-services
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-team-grpc
  template:
    metadata:
      labels:
        app: ai-team-grpc
    spec:
      containers:
      - name: ai-team-grpc
        image: gcr.io/$PROJECT_ID/ai-team-grpc:latest
        ports:
        - containerPort: 50051
        env:
        - name: GRPC_PORT
          value: "50051"
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - /bin/grpc_health_probe
            - -addr=:50051
          initialDelaySeconds: 30
        readinessProbe:
          exec:
            command:
            - /bin/grpc_health_probe
            - -addr=:50051
          initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ai-team-grpc-service
  namespace: ai-services
spec:
  selector:
    app: ai-team-grpc
  ports:
  - port: 50051
    targetPort: 50051
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-team-grpc-hpa
  namespace: ai-services
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-team-grpc
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
    
    log_success "Kubernetes resources deployed"
}

# Build and deploy
build_and_deploy() {
    log_info "Building and deploying AI Services..."
    
    # Submit build to Cloud Build
    gcloud builds submit --config=cloudbuild.yaml .
    
    log_success "Build and deployment complete"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create uptime check
    gcloud alpha monitoring uptime create \
        --project=$PROJECT_ID \
        --display-name="AI Services Health Check" \
        --http-check-path="/health" \
        --hostname="$SERVICE_NAME-$PROJECT_ID.uc.r.appspot.com" \
        --port=443 \
        --use-ssl || log_warning "Uptime check may already exist"
    
    log_success "Monitoring setup complete"
}

# Main deployment function
main() {
    echo "Starting deployment with PROJECT_ID: $PROJECT_ID"
    
    check_prerequisites
    setup_project
    create_storage
    setup_secrets
    create_cluster
    deploy_kubernetes
    build_and_deploy
    setup_monitoring
    
    log_success "🎉 ChatterFix AI Services deployed successfully!"
    echo ""
    echo "📊 Service URLs:"
    echo "   AI Services API: https://$SERVICE_NAME-$PROJECT_ID.uc.r.appspot.com"
    echo "   Health Check: https://$SERVICE_NAME-$PROJECT_ID.uc.r.appspot.com/health"
    echo "   AI Memory Dashboard: https://$SERVICE_NAME-$PROJECT_ID.uc.r.appspot.com/ai-memory/"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Update API key secrets in Secret Manager"
    echo "   2. Test endpoints with your external services"
    echo "   3. Monitor performance in Cloud Console"
    echo ""
    echo "🤖 AI Team collaboration: Ready for continuous evolution!"
}

# Run deployment
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi