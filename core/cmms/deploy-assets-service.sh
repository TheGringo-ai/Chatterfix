#!/bin/bash

echo "🏭 Deploying ChatterFix Assets Service..."

# Set environment variables
export PROJECT_ID="fredfix"
export SERVICE_NAME="chatterfix-assets"
export REGION="us-central1"

# Get database service URL
if [ -f ".env.database" ]; then
    export DATABASE_SERVICE_URL=$(cat .env.database | grep URL | cut -d'=' -f2)
    echo "📊 Using database service URL: $DATABASE_SERVICE_URL"
else
    export DATABASE_SERVICE_URL="https://chatterfix-database-psycl7nhha-uc.a.run.app"
    echo "⚠️ Using default database service URL: $DATABASE_SERVICE_URL"
fi

# Create a temporary directory for assets service
echo "📦 Preparing assets service for deployment..."
rm -rf /tmp/assets-service
mkdir -p /tmp/assets-service

# Copy assets service files
cp assets_service.py /tmp/assets-service/main.py
cp assets_service_requirements.txt /tmp/assets-service/requirements.txt

# Create Dockerfile for assets service
cat > /tmp/assets-service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8082
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
EOF

# Deploy assets service
echo "📦 Deploying assets service to Cloud Run..."
cd /tmp/assets-service
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8082 \
    --set-env-vars DATABASE_SERVICE_URL=$DATABASE_SERVICE_URL \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300s \
    --max-instances 10 \
    --project $PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' --project $PROJECT_ID)

echo "✅ Assets service deployment completed!"
echo "✅ Assets Service URL: $SERVICE_URL"

# Save URL to file
echo "ASSETS_SERVICE_URL=$SERVICE_URL" > .env.assets

# Health check
echo "🏥 Performing health check..."
sleep 5
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" || echo "Health check failed")
echo "Health response: $HEALTH_RESPONSE"

echo ""
echo "🎉 Assets Service Deployment Summary:"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION" 
echo "   URL: $SERVICE_URL"
echo ""
echo "✅ Assets service URL saved to .env.assets"
echo "✅ ChatterFix Assets Service deployment completed!"