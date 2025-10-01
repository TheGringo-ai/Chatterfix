#!/bin/bash

# ChatterFix CMMS - Database Service Deployment Script
# Deploy the database microservice to Cloud Run

set -e

echo "🗄️ Deploying ChatterFix Database Service..."

# Configuration
SERVICE_NAME="chatterfix-database"
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

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

# Create a temporary directory for database service
echo "📦 Preparing database service for deployment..."
rm -rf /tmp/database-service
mkdir -p /tmp/database-service

# Copy database service files
cp database_service.py /tmp/database-service/main.py
cp simple_database_manager.py /tmp/database-service/
cp database_service_requirements.txt /tmp/database-service/requirements.txt

# Create Dockerfile for database service
cat > /tmp/database-service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# Deploy database service
echo "📦 Deploying database service to Cloud Run..."
cd /tmp/database-service
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 5 \
    --min-instances 1 \
    --set-env-vars "ENVIRONMENT=production,DATABASE_URL=postgresql://yoyofred:%40Gringo420@136.112.167.114/chatterfix_cmms" \
    --tag latest

echo_info "Database service deployment completed!"

# Get service URL
DB_SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo_info "Database Service URL: $DB_SERVICE_URL"

# Health check
echo "🏥 Performing health check..."
if curl -s -f "$DB_SERVICE_URL/health" > /dev/null 2>&1; then
    echo_info "Database service health check passed"
    
    # Test database connection
    echo "🔍 Testing database connection..."
    HEALTH_RESPONSE=$(curl -s "$DB_SERVICE_URL/health")
    echo "Health response: $HEALTH_RESPONSE"
else
    echo_warning "Database service health check failed - service may still be starting"
fi

echo ""
echo "🎉 Database Service Deployment Summary:"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   URL: $DB_SERVICE_URL"
echo ""

# Save the URL for main app deployment
echo "DATABASE_SERVICE_URL=$DB_SERVICE_URL" > .env.database
echo_info "Database service URL saved to .env.database"

echo_info "ChatterFix Database Service deployment completed!"