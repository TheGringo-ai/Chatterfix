#!/bin/bash

echo "🔧 Fix-It Fred Simple Cloud Run Deployment"
echo "=========================================="

# Clean directory and deploy minimal setup
echo "Creating minimal deployment package..."

# Create a temporary directory for clean deployment
mkdir -p fixit-deploy
cd fixit-deploy

# Copy only essential files
cp ../fix_it_fred_diy.py .
cp ../fixit-requirements.txt requirements.txt

# Create simple Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fix_it_fred_diy.py .

EXPOSE 8080

CMD ["python", "fix_it_fred_diy.py"]
EOF

echo "Deploying to Cloud Run..."

# Deploy directly with Cloud Build
gcloud run deploy fix-it-fred-diy \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 300

echo "Getting service URL..."
SERVICE_URL=$(gcloud run services describe fix-it-fred-diy --region=us-central1 --format="value(status.url)")

echo ""
echo "🎉 Fix-It Fred DIY Assistant Deployed!"
echo "📱 URL: $SERVICE_URL"
echo "🔧 DIY Jobs: $SERVICE_URL/jobs"
echo "📋 Parts: $SERVICE_URL/parts" 
echo "⏰ Reminders: $SERVICE_URL/reminders"
echo "🏥 Health: $SERVICE_URL/health"

# Test deployment
echo ""
echo "Testing deployment..."
curl -s "$SERVICE_URL/health" && echo ""

# Cleanup
cd ..
rm -rf fixit-deploy

echo "✅ Deployment complete!"