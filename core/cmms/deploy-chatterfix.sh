#!/bin/bash

# ChatterFix CMMS - Simple Deployment Script for chatterfix.com
# Quick deployment to the configured chatterfix.com domain

set -e

echo "🚀 Deploying ChatterFix CMMS to chatterfix.com..."

# Configuration
SERVICE_NAME="chatterfix-cmms"
REGION="us-central1"
DOMAIN="chatterfix.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Deploy to Cloud Run using clean UI Gateway
echo "📦 Building and deploying ChatterFix UI Gateway to Cloud Run..."
echo "🚀 Using clean microservices architecture with app.py..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --min-instances 1 \
    --set-env-vars "ENVIRONMENT=production,DOMAIN=$DOMAIN,DATABASE_URL=postgresql://yoyofred:%40Gringo420@136.112.167.114/chatterfix_cmms" \
    --tag latest

echo_info "Deployment completed successfully!"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo_info "Service URL: $SERVICE_URL"

# Check if domain mapping exists
echo "🌐 Checking domain configuration..."
if gcloud run domain-mappings describe $DOMAIN --region=$REGION --quiet > /dev/null 2>&1; then
    echo_info "Domain mapping exists for $DOMAIN"
else
    echo_warning "Domain mapping not found. Run ./setup-chatterfix-domain.sh first"
fi

# Health check
echo "🏥 Performing health check..."
if curl -s -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo_info "Health check passed"
else
    echo_warning "Health check failed - service may still be starting"
fi

echo ""
echo "🎉 Deployment Summary:"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Domain: https://$DOMAIN"
echo "   Cloud Run URL: $SERVICE_URL"
echo ""
echo "🔗 Access your application:"
echo "   https://$DOMAIN (if DNS is configured)"
echo "   $SERVICE_URL (direct Cloud Run URL)"
echo ""

echo_info "ChatterFix CMMS deployment completed!"