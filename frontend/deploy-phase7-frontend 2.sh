#!/bin/bash

set -e

echo "🚀 Deploying Phase 7 AI-Enhanced Frontend"
echo "=========================================="

# Configuration
PROJECT_ID="fredfix"
SERVICE_NAME="chatterfix-phase7-ai"
REGION="us-central1"
MIN_INSTANCES=0
MAX_INSTANCES=2
MEMORY="512Mi"
CPU="1"
ARTIFACT_REGISTRY="us-central1-docker.pkg.dev"

echo "📦 Preparing Phase 7 AI-enhanced frontend deployment..."

# Create optimized Dockerfile for Phase 7
cat > Dockerfile.phase7 << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Phase 7 AI-enhanced application
COPY phase7-ai-enhanced-gateway.py main.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "main.py"]
EOF

echo "🔧 Building and deploying Phase 7 AI frontend..."

# Build and deploy
cp Dockerfile.phase7 Dockerfile
gcloud builds submit --tag $ARTIFACT_REGISTRY/$PROJECT_ID/chatterfix/$SERVICE_NAME .

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

echo "✅ Phase 7 AI Frontend deployment complete!"
echo "🌐 AI-Enhanced Frontend URL: https://$SERVICE_NAME-650169261019.us-central1.run.app"

# Health check
echo "🔍 Running health check..."
sleep 10
HEALTH_RESPONSE=$(curl -s "https://$SERVICE_NAME-650169261019.us-central1.run.app/health")
echo "Health Response: $HEALTH_RESPONSE"

echo "🧠 Phase 7 AI Features:"
echo "  - 🤖 Predictive maintenance with ML models"
echo "  - 💡 AI-powered operational insights"
echo "  - 📊 Real-time anomaly detection"
echo "  - 🎯 Risk-based asset prioritization"
echo "  - 📈 Intelligent reporting and recommendations"

# Cleanup
rm -f Dockerfile.phase7