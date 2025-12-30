#!/bin/bash
# ChatterFix CMMS v4.0 - GCP Deployment Script
# 🌍🚀 Global AI Platform Deployment to Google Cloud Platform

echo "🌍🚀 ChatterFix CMMS v4.0 - GCP Deployment"
echo "=========================================="
echo "Deploying Global AI Platform to Google Cloud Platform"
echo ""

# Configuration
PROJECT_ID=${PROJECT_ID:-"chatterfix-global"}
REGION=${REGION:-"us-central1"}
ZONE=${ZONE:-"us-central1-a"}
CLUSTER_NAME="chatterfix-v4-cluster"
SERVICE_NAME="chatterfix-v4"

# Check if gcloud is installed and configured
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found. Please install it first."
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "🔧 Setting up GCP project..."
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# Enable required APIs
echo "🔌 Enabling required GCP APIs..."
gcloud services enable \
    containerregistry.googleapis.com \
    container.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sql-component.googleapis.com \
    redis.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com

# Create Cloud SQL instance for production database
echo "🗄️ Setting up Cloud SQL PostgreSQL instance..."
gcloud sql instances create chatterfix-v4-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=ChatterFixV4SecurePassword \
    --storage-type=SSD \
    --storage-size=20GB \
    --backup-start-time=02:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=3 \
    --maintenance-release-channel=production || echo "Database already exists"

# Create database
gcloud sql databases create chatterfix_v4 --instance=chatterfix-v4-db || echo "Database already exists"

# Create Redis instance for caching
echo "🔴 Setting up Redis instance..."
gcloud redis instances create chatterfix-v4-cache \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_6_x || echo "Redis already exists"

# Build and push container images
echo "🏗️ Building container images..."

# Create Dockerfile for ChatterFix v4.0
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir sentence-transformers faiss-cpu numpy httpx

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "app.py"]
EOF

# Create .dockerignore
cat > .dockerignore << 'EOF'
.git
.gitignore
README.md
.env*
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.pytest_cache
.mypy_cache
venv/
pids/
logs/
*.db
*.sqlite
.DS_Store
node_modules/
EOF

# Build main application
echo "📦 Building main ChatterFix application..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/chatterfix-v4:latest .

# Create deployment configuration
echo "📋 Creating Kubernetes deployment configuration..."
cat > k8s-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatterfix-v4
  labels:
    app: chatterfix-v4
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatterfix-v4
  template:
    metadata:
      labels:
        app: chatterfix-v4
    spec:
      containers:
      - name: chatterfix-v4
        image: gcr.io/$PROJECT_ID/chatterfix-v4:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chatterfix-secrets
              key: database-url
        - name: XAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatterfix-secrets
              key: xai-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatterfix-secrets
              key: openai-api-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatterfix-secrets
              key: anthropic-api-key
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatterfix-secrets
              key: google-api-key
        - name: ENVIRONMENT
          value: "production"
        - name: PROJECT_ID
          value: "$PROJECT_ID"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: chatterfix-v4-service
spec:
  selector:
    app: chatterfix-v4
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
---
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: chatterfix-ssl-cert
spec:
  domains:
  - chatterfix.com
  - www.chatterfix.com
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chatterfix-v4-ingress
  annotations:
    kubernetes.io/ingress.global-static-ip-name: chatterfix-ip
    networking.gke.io/managed-certificates: chatterfix-ssl-cert
    kubernetes.io/ingress.class: "gce"
spec:
  rules:
  - host: chatterfix.com
    http:
      paths:
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: chatterfix-v4-service
            port:
              number: 80
  - host: www.chatterfix.com
    http:
      paths:
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: chatterfix-v4-service
            port:
              number: 80
EOF

# Create GKE cluster
echo "☸️ Creating GKE cluster..."
gcloud container clusters create $CLUSTER_NAME \
    --zone=$ZONE \
    --machine-type=e2-standard-4 \
    --num-nodes=3 \
    --enable-autoscaling \
    --min-nodes=2 \
    --max-nodes=10 \
    --enable-autorepair \
    --enable-autoupgrade \
    --disk-size=50GB \
    --disk-type=pd-ssd \
    --enable-ip-alias \
    --enable-stackdriver-kubernetes \
    --addons=HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver || echo "Cluster already exists"

# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

# Reserve static IP
echo "🌐 Reserving static IP address..."
gcloud compute addresses create chatterfix-ip --global || echo "IP already reserved"

# Create secrets (you'll need to update these with real values)
echo "🔐 Creating Kubernetes secrets..."
kubectl create secret generic chatterfix-secrets \
    --from-literal=database-url="postgresql://postgres:ChatterFixV4SecurePassword@/chatterfix_v4?host=/cloudsql/$PROJECT_ID:$REGION:chatterfix-v4-db" \
    --from-literal=xai-api-key="$XAI_API_KEY" \
    --from-literal=openai-api-key="$OPENAI_API_KEY" \
    --from-literal=anthropic-api-key="$ANTHROPIC_API_KEY" \
    --from-literal=google-api-key="$GOOGLE_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy to cluster
echo "🚀 Deploying ChatterFix v4.0 to GKE..."
kubectl apply -f k8s-deployment.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/chatterfix-v4 --timeout=600s

# Get service details
echo "📊 Getting service information..."
kubectl get services
kubectl get ingress

# Get static IP
STATIC_IP=$(gcloud compute addresses describe chatterfix-ip --global --format="value(address)")
echo ""
echo "🎉 ChatterFix v4.0 Deployment Complete!"
echo "======================================"
echo ""
echo "🌍 Static IP: $STATIC_IP"
echo "🔗 URL: https://chatterfix.com"
echo "📊 Kubernetes Dashboard: kubectl proxy"
echo "📈 Monitoring: https://console.cloud.google.com/monitoring"
echo ""
echo "🔧 Next Steps:"
echo "  1. Update DNS to point to: $STATIC_IP"
echo "  2. Wait for SSL certificate provisioning (~15 minutes)"
echo "  3. Test all AI services and endpoints"
echo "  4. Monitor deployment in GCP Console"
echo ""
echo "📝 Useful Commands:"
echo "  kubectl get pods"
echo "  kubectl logs -f deployment/chatterfix-v4"
echo "  kubectl describe service chatterfix-v4-service"
echo ""
echo "🌍🚀 ChatterFix v4.0 is ready to rock the entire planet!"