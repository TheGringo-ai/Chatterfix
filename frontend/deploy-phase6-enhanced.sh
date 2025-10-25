#!/bin/bash

set -e

echo "🚀 Deploying Phase 6 Enhanced ChatterFix Frontend"
echo "=================================================="

# Configuration
PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-phase6-enhanced"
REGION="us-central1"
MIN_INSTANCES=0
MAX_INSTANCES=2
MEMORY="512Mi"
CPU="1"
ARTIFACT_REGISTRY="us-central1-docker.pkg.dev"

echo "📦 Preparing Phase 6 enhanced frontend deployment..."

# Create optimized Dockerfile for Phase 6
cat > Dockerfile.phase6 << EOF
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

# Copy Phase 6 enhanced application
COPY phase6-enhanced-gateway.py main.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "main.py"]
EOF

echo "🔧 Setting environment variables for enhanced features..."

# Build and deploy
echo "📦 Building Docker image..."
cp Dockerfile.phase6 Dockerfile
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
  --set-env-vars="WORK_ORDERS_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,ASSETS_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,PARTS_URL=https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app,CHATTERFIX_API_KEY=chatterfix_secure_api_key_2025_cmms_prod_v1" \
  --timeout=300

echo "✅ Deployment complete!"
echo "🌐 Enhanced Frontend URL: https://$SERVICE_NAME-650169261019.us-central1.run.app"

# Health check
echo "🔍 Running health check..."
sleep 10
HEALTH_RESPONSE=$(curl -s "https://$SERVICE_NAME-650169261019.us-central1.run.app/health")
echo "Health Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "analytics"; then
    echo "✅ Analytics integration detected"
else
    echo "❌ Analytics integration not detected"
fi

if echo "$HEALTH_RESPONSE" | grep -q "premium_ux"; then
    echo "✅ Premium UX features detected"
else
    echo "❌ Premium UX features not detected"
fi

echo "📊 Phase 6 Enhanced Features Deployed:"
echo "  - 🚀 Performance optimizations (caching, lazy loading)"
echo "  - 📱 Premium UX with animated KPI cards"
echo "  - 🔍 Global search with sticky filter chips"
echo "  - 📈 Google Analytics 4 integration"
echo "  - 🎯 Backend analytics logging"
echo "  - ⚡ Request cancellation and script deferring"
echo "  - 🎨 ChatterFix brand colors (neutral gray + teal)"

# Cleanup
rm -f Dockerfile.phase6