#!/bin/bash
"""
🔧 Deploy Fix-It Fred DIY Tech Assistant to Cloud Run
Standalone app for DIY tech and small business maintenance
"""

echo "🔧 Fix-It Fred DIY Tech Assistant Deployment"
echo "============================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SERVICE_NAME="fix-it-fred-diy"
REGION="us-central1"
PROJECT_ID="fredfix"
PORT="8080"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION" 
echo "Project: $PROJECT_ID"
echo "Port: $PORT"
echo ""

# Step 1: Create Dockerfile for Fix-It Fred
echo -e "${BLUE}1. Creating Dockerfile...${NC}"
cat > Dockerfile.fixit << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY fix_it_fred_diy.py .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "fix_it_fred_diy.py"]
EOF

echo "✅ Dockerfile created"

# Step 2: Create requirements.txt
echo -e "${BLUE}2. Creating requirements.txt...${NC}"
cat > requirements.fixit.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlite3-utils==3.35
python-multipart==0.0.6
jinja2==3.1.2
aiofiles==23.2.1
httpx==0.25.0
python-dateutil==2.8.2
EOF

echo "✅ Requirements file created"

# Step 3: Build and push Docker image
echo -e "${BLUE}3. Building Docker image...${NC}"
docker build -f Dockerfile.fixit -t $IMAGE_NAME .

echo -e "${BLUE}4. Pushing to Google Container Registry...${NC}"
docker push $IMAGE_NAME

# Step 4: Deploy to Cloud Run
echo -e "${BLUE}5. Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port $PORT \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="ENVIRONMENT=production" \
  --timeout 300

# Step 5: Get service URL
echo -e "${BLUE}6. Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}🎉 Fix-It Fred DIY Assistant Deployed Successfully!${NC}"
echo ""
echo "📱 Service URL: $SERVICE_URL"
echo "🔧 DIY Jobs: $SERVICE_URL/jobs"
echo "📋 Parts Lists: $SERVICE_URL/parts"
echo "⏰ Reminders: $SERVICE_URL/reminders"
echo "💬 AI Chat: $SERVICE_URL/chat"
echo "🏥 Health: $SERVICE_URL/health"
echo ""

# Step 6: Test deployment
echo -e "${BLUE}7. Testing deployment...${NC}"
echo "Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $SERVICE_URL/health)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed: $HEALTH_STATUS${NC}"
    
    # Test main endpoints
    echo "Testing main endpoints..."
    for endpoint in "" "jobs" "parts" "reminders" "instructions"; do
        status=$(curl -s -o /dev/null -w "%{http_code}" $SERVICE_URL/$endpoint)
        if [ "$status" = "200" ]; then
            echo -e "${GREEN}✅ /$endpoint: $status${NC}"
        else
            echo -e "${YELLOW}⚠️ /$endpoint: $status${NC}"
        fi
    done
    
    echo ""
    echo -e "${GREEN}🚀 Fix-It Fred DIY Assistant is LIVE!${NC}"
    echo "Ready to help with DIY projects and maintenance scheduling"
    
else
    echo -e "${YELLOW}⚠️ Health check failed: $HEALTH_STATUS${NC}"
    echo "Check logs: gcloud run logs read $SERVICE_NAME --region=$REGION"
fi

echo ""
echo -e "${BLUE}📊 Service Information:${NC}"
echo "========================"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "URL: $SERVICE_URL"
echo "Features:"
echo "  • DIY job planning with step-by-step instructions"
echo "  • Parts and materials list generator"
echo "  • Maintenance reminder system"
echo "  • AI-powered DIY assistance"
echo "  • Service scheduling for small businesses"
echo ""

# Cleanup temporary files
rm -f Dockerfile.fixit requirements.fixit.txt

echo -e "${GREEN}🔧 Fix-It Fred DIY Deployment Complete!${NC}"