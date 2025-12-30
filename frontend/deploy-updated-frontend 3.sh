#!/bin/bash

set -e

echo "🚀 Deploying Updated ChatterFix Frontend"
echo "========================================"

# Configuration
PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-unified-gateway-updated"
REGION="us-central1"
MIN_INSTANCES=0
MAX_INSTANCES=2
MEMORY="512Mi"
CPU="1"
ARTIFACT_REGISTRY="us-central1-docker.pkg.dev"

echo "📦 Preparing frontend deployment with consolidated service URLs..."

# Create temporary Dockerfile for frontend
cat > Dockerfile.frontend << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY phase6b-unified-gateway.py main.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "main.py"]
EOF

echo "🔧 Setting environment variables for consolidated services..."

# Build and deploy
echo "📦 Building Docker image..."
cp Dockerfile.frontend Dockerfile
gcloud builds submit --tag $ARTIFACT_REGISTRY/$PROJECT_ID/chatterfix/$SERVICE_NAME .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $ARTIFACT_REGISTRY/$PROJECT_ID/chatterfix/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --min-instances $MIN_INSTANCES \
  --max-instances $MAX_INSTANCES \
  --port 8080 \
  --set-env-vars="WORK_ORDERS_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,ASSETS_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,PARTS_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,CUSTOMER_SUCCESS_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,REVENUE_INTELLIGENCE_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,DATA_ROOM_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,CHATTERFIX_API_KEY=chatterfix_secure_api_key_2025_cmms_prod_v1" \
  --timeout=300

echo "✅ Deployment complete!"
echo "🌐 Frontend URL: https://$SERVICE_NAME-650169261019.us-central1.run.app"

# Health check
echo "🔍 Running health check..."
sleep 10
curl -f "https://$SERVICE_NAME-650169261019.us-central1.run.app/health" || echo "❌ Health check failed"

echo "📊 Frontend now uses consolidated CMMS service:"
echo "  - Work Orders: Consolidated CMMS"
echo "  - Assets: Consolidated CMMS" 
echo "  - Parts: Consolidated CMMS"
echo "  - All requests proxied to: https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app"

# Cleanup
rm -f Dockerfile.frontend