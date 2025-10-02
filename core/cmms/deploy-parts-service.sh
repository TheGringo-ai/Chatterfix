#!/bin/bash

echo "🔧 Deploying ChatterFix Parts Service..."

# Set environment variables
export PROJECT_ID="fredfix"
export SERVICE_NAME="chatterfix-parts"
export REGION="us-central1"

# Get database service URL
if [ -f ".env.database" ]; then
    export DATABASE_SERVICE_URL=$(cat .env.database | grep URL | cut -d'=' -f2)
    echo "📊 Using database service URL: $DATABASE_SERVICE_URL"
else
    export DATABASE_SERVICE_URL="https://chatterfix-database-psycl7nhha-uc.a.run.app"
    echo "⚠️ Using default database service URL: $DATABASE_SERVICE_URL"
fi

# Create a temporary directory for parts service
echo "📦 Preparing parts service for deployment..."
rm -rf /tmp/parts-service
mkdir -p /tmp/parts-service

# Copy parts service files
cp parts_service.py /tmp/parts-service/main.py
cp parts_service_requirements.txt /tmp/parts-service/requirements.txt

# Create Dockerfile for parts service
cat > /tmp/parts-service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8083
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8083"]
EOF

# Deploy parts service
echo "📦 Deploying parts service to Cloud Run..."
cd /tmp/parts-service
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8083 \
    --set-env-vars DATABASE_SERVICE_URL=$DATABASE_SERVICE_URL \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300s \
    --max-instances 10 \
    --project $PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' --project $PROJECT_ID)

echo "✅ Parts service deployment completed!"
echo "✅ Parts Service URL: $SERVICE_URL"

# Save URL to file
echo "PARTS_SERVICE_URL=$SERVICE_URL" > .env.parts

# Health check
echo "🏥 Performing health check..."
sleep 5
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" || echo "Health check failed")
echo "Health response: $HEALTH_RESPONSE"

echo ""
echo "🎉 Parts Service Deployment Summary:"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION" 
echo "   URL: $SERVICE_URL"
echo ""
echo "✅ Parts service URL saved to .env.parts"
echo "✅ ChatterFix Parts Service deployment completed!"