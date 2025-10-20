#!/bin/bash
set -e

echo "🚀 Starting ChatterFix Enterprise CMMS Deployment"

# Configuration
NAMESPACE="chatterfix-enterprise"
DEPLOYMENT_ID="${1:-$(date +%Y%m%d_%H%M%S)}"

echo "📝 Deployment ID: $DEPLOYMENT_ID"
echo "🎯 Target Namespace: $NAMESPACE"

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."
kubectl cluster-info || { echo "❌ Kubernetes cluster not accessible"; exit 1; }

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply configuration
echo "⚙️ Applying configuration..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy database
echo "🗄️ Deploying PostgreSQL database..."
kubectl apply -f k8s/postgresql-deployment.yaml

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=postgresql -n $NAMESPACE --timeout=300s

# Deploy backend services
echo "🔧 Deploying backend services..."
kubectl apply -f k8s/auth-service-deployment.yaml
kubectl apply -f k8s/work-orders-deployment.yaml
kubectl apply -f k8s/assets-deployment.yaml
kubectl apply -f k8s/parts-deployment.yaml
kubectl apply -f k8s/analytics-deployment.yaml

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=chatterfix-auth -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=chatterfix-work-orders -n $NAMESPACE --timeout=300s

# Deploy frontend
echo "🎨 Deploying frontend..."
kubectl apply -f k8s/frontend-deployment.yaml

# Deploy ingress
echo "🌐 Setting up ingress..."
kubectl apply -f k8s/ingress.yaml

# Apply auto-scaling
echo "📈 Setting up auto-scaling..."
kubectl apply -f k8s/hpa.yaml

# Deployment verification
echo "✅ Running deployment verification..."
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

echo "🎉 ChatterFix Enterprise CMMS deployment completed successfully!"
echo "🌐 Access your application at: https://enterprise.chatterfix.com"
echo "📊 Monitor deployment: kubectl get pods -n $NAMESPACE -w"
