#!/bin/bash

# ChatterFix CMMS - Main Application Deployment Script
# Deploy the main application microservice to Cloud Run

set -e

echo "🚀 Deploying ChatterFix Main Application..."

# Configuration
SERVICE_NAME="chatterfix-cmms"
REGION="us-central1"
DOMAIN="chatterfix.com"
PROJECT_ID=$(gcloud config get-value project)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if database service URL is available
if [ -f ".env.database" ]; then
    source .env.database
    echo_info "Using database service URL: $DATABASE_SERVICE_URL"
else
    echo_warning "No database service URL found. Please run deploy-database-service.sh first"
    echo "Using default database service URL..."
    DATABASE_SERVICE_URL="https://chatterfix-database-$REGION-$PROJECT_ID.a.run.app"
fi

# Create a temporary directory for main application
echo "📦 Preparing main application for deployment..."
rm -rf /tmp/main-app
mkdir -p /tmp/main-app

# Copy main application files
cp app_microservice.py /tmp/main-app/main.py
cp database_client.py /tmp/main-app/
cp app_microservice_requirements.txt /tmp/main-app/requirements.txt

# Create Dockerfile for main application
cat > /tmp/main-app/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# Build and deploy main application
echo "📦 Deploying main application to Cloud Run..."
cd /tmp/main-app
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --min-instances 1 \
    --set-env-vars "ENVIRONMENT=production,DOMAIN=$DOMAIN,DATABASE_SERVICE_URL=$DATABASE_SERVICE_URL,JWT_SECRET=your-jwt-secret-change-in-production" \
    --tag latest

echo_info "Main application deployment completed!"

# Get service URL
MAIN_SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo_info "Main Service URL: $MAIN_SERVICE_URL"

# Check if domain mapping exists
echo "🌐 Checking domain configuration..."
if gcloud run domain-mappings describe $DOMAIN --region=$REGION --quiet > /dev/null 2>&1; then
    echo_info "Domain mapping exists for $DOMAIN"
else
    echo_warning "Domain mapping not found. Creating domain mapping..."
    
    # Create domain mapping
    gcloud run domain-mappings create \
        --service=$SERVICE_NAME \
        --domain=$DOMAIN \
        --region=$REGION \
        --quiet
    
    if [ $? -eq 0 ]; then
        echo_info "Domain mapping created successfully"
        echo_warning "Please configure DNS to point $DOMAIN to ghs.googlehosted.com"
    else
        echo_error "Failed to create domain mapping"
    fi
fi

# Health check
echo "🏥 Performing health check..."
if curl -s -f "$MAIN_SERVICE_URL/health" > /dev/null 2>&1; then
    echo_info "Main application health check passed"
    
    # Test database connectivity through main app
    echo "🔍 Testing database connectivity..."
    HEALTH_RESPONSE=$(curl -s "$MAIN_SERVICE_URL/health")
    echo "Health response: $HEALTH_RESPONSE"
else
    echo_warning "Main application health check failed - service may still be starting"
fi

echo ""
echo "🎉 Main Application Deployment Summary:"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Domain: https://$DOMAIN"
echo "   Cloud Run URL: $MAIN_SERVICE_URL"
echo "   Database Service: $DATABASE_SERVICE_URL"
echo ""
echo "🔗 Access your application:"
echo "   https://$DOMAIN (if DNS is configured)"
echo "   $MAIN_SERVICE_URL (direct Cloud Run URL)"
echo ""

echo_info "ChatterFix Main Application deployment completed!"