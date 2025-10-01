#!/bin/bash

# ChatterFix CMMS - Complete Microservices Deployment Script
# Deploy both database and main application services to Cloud Run

set -e

echo "🚀 Deploying ChatterFix CMMS Microservices Architecture..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Check prerequisites
echo_step "Checking prerequisites..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
    echo "❌ gcloud is not authenticated. Please run 'gcloud auth login'"
    exit 1
fi

# Check if project is set
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No project set. Please run 'gcloud config set project YOUR_PROJECT_ID'"
    exit 1
fi

echo_info "Prerequisites check passed"
echo_info "Project: $PROJECT_ID"

# Make deployment scripts executable
chmod +x deploy-database-service.sh
chmod +x deploy-main-app.sh

echo ""
echo "===================="
echo "STEP 1: Database Service"
echo "===================="

# Deploy database service first
echo_step "Deploying database service..."
./deploy-database-service.sh

if [ $? -ne 0 ]; then
    echo "❌ Database service deployment failed!"
    exit 1
fi

echo_info "Database service deployed successfully"

echo ""
echo "===================="
echo "STEP 2: Main Application"
echo "===================="

# Wait a bit for database service to be ready
echo_step "Waiting for database service to be ready..."
sleep 10

# Deploy main application
echo_step "Deploying main application..."
./deploy-main-app.sh

if [ $? -ne 0 ]; then
    echo "❌ Main application deployment failed!"
    exit 1
fi

echo_info "Main application deployed successfully"

echo ""
echo "===================="
echo "DEPLOYMENT COMPLETE"
echo "===================="

# Final status check
echo_step "Performing final health checks..."

# Get service URLs
REGION="us-central1"
DB_SERVICE_URL=$(gcloud run services describe chatterfix-database --region=$REGION --format="value(status.url)" 2>/dev/null || echo "Not found")
MAIN_SERVICE_URL=$(gcloud run services describe chatterfix-cmms --region=$REGION --format="value(status.url)" 2>/dev/null || echo "Not found")

echo ""
echo "🎉 ChatterFix CMMS Microservices Deployment Summary:"
echo "=================================================="
echo ""
echo "📊 Services Deployed:"
echo "   • Database Service: $DB_SERVICE_URL"
echo "   • Main Application: $MAIN_SERVICE_URL"
echo ""
echo "🌐 Access Points:"
echo "   • Production URL: https://chatterfix.com"
echo "   • Direct Access: $MAIN_SERVICE_URL"
echo ""
echo "🔧 Service Endpoints:"
echo "   • Main App Health: $MAIN_SERVICE_URL/health"
echo "   • Database Health: $DB_SERVICE_URL/health"
echo "   • Work Orders: $MAIN_SERVICE_URL/workorders"
echo "   • Assets: $MAIN_SERVICE_URL/assets"
echo "   • Parts: $MAIN_SERVICE_URL/parts"
echo ""
echo "📋 Next Steps:"
echo "   1. Configure DNS to point chatterfix.com to ghs.googlehosted.com"
echo "   2. Test the application at $MAIN_SERVICE_URL"
echo "   3. Monitor logs: gcloud logs tail --service=chatterfix-cmms"
echo "   4. Monitor database: gcloud logs tail --service=chatterfix-database"
echo ""

# Test connectivity
echo_step "Testing service connectivity..."

if curl -s -f "$MAIN_SERVICE_URL/health" > /dev/null 2>&1; then
    echo_info "✅ Main application is responding"
else
    echo_warning "⚠️  Main application health check failed"
fi

if curl -s -f "$DB_SERVICE_URL/health" > /dev/null 2>&1; then
    echo_info "✅ Database service is responding"
else
    echo_warning "⚠️  Database service health check failed"
fi

echo ""
echo_info "🚀 ChatterFix CMMS Microservices deployment completed!"
echo_info "🔗 Your application should be available at: $MAIN_SERVICE_URL"