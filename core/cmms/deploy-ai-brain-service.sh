#!/bin/bash
# ChatterFix AI Brain Service Deployment Script
# Deploys the AI Brain service with Ollama to Google Cloud Run

set -e

echo "🧠 ChatterFix AI Brain Service - Deployment Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="chatterfix-cmms"
SERVICE_NAME="chatterfix-ai-brain"
REGION="us-central1"
PORT=8080

echo -e "${BLUE}📋 Configuration:${NC}"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Port: $PORT"
echo ""

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker not found. Please install Docker.${NC}"
    exit 1
fi

# Set project
echo -e "${BLUE}🔧 Setting up Google Cloud project...${NC}"
gcloud config set project $PROJECT_ID

# Create Dockerfile for AI Brain Service
echo -e "${BLUE}📝 Creating Dockerfile...${NC}"
cat > Dockerfile.ai-brain << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai_brain_service.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash aiuser
USER aiuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run the application
CMD ["python", "ai_brain_service.py"]
EOF

# Create .dockerignore for AI Brain
echo -e "${BLUE}📝 Creating .dockerignore...${NC}"
cat > .dockerignore.ai-brain << EOF
__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
README.md
.env
.venv
venv/
.pytest_cache
.coverage
htmlcov/
.tox/
.mypy_cache
.DS_Store
*.log
technician_ai_assistant.py
deploy-*.sh
Dockerfile*
EOF

# Create requirements for AI Brain (minimal set)
echo -e "${BLUE}📝 Creating AI Brain requirements.txt...${NC}"
cat > requirements.ai-brain.txt << EOF
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.4.0
openai>=1.3.0
anthropic>=0.7.0
requests>=2.31.0
python-multipart>=0.0.6
aiofiles>=23.2.0
EOF

# Build Docker image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
cp requirements.ai-brain.txt requirements.txt
docker build -f Dockerfile.ai-brain -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

# Test the image locally first
echo -e "${BLUE}🧪 Testing Docker image locally...${NC}"
echo "Starting container..."
CONTAINER_ID=$(docker run -d -p 9001:8080 gcr.io/$PROJECT_ID/$SERVICE_NAME:latest)

# Wait for container to start
sleep 15

# Test health endpoint
if curl -f http://localhost:9001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Local test passed!${NC}"
else
    echo -e "${RED}❌ Local test failed!${NC}"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    exit 1
fi

# Stop test container
docker stop $CONTAINER_ID

# Configure Docker for Google Cloud
echo -e "${BLUE}🔐 Configuring Docker for Google Cloud...${NC}"
gcloud auth configure-docker

# Push Docker image to Google Container Registry
echo -e "${BLUE}📤 Pushing image to Google Container Registry...${NC}"
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# Deploy to Cloud Run
echo -e "${BLUE}🚀 Deploying to Google Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \\
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \\
    --platform managed \\
    --region $REGION \\
    --allow-unauthenticated \\
    --port $PORT \\
    --memory 2Gi \\
    --cpu 2 \\
    --timeout 300 \\
    --concurrency 100 \\
    --min-instances 0 \\
    --max-instances 10 \\
    --set-env-vars="PORT=$PORT"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo -e "${GREEN}🎉 ChatterFix AI Brain Service deployed successfully!${NC}"
echo ""
echo -e "${BLUE}📍 Service Details:${NC}"
echo "   URL: $SERVICE_URL"
echo "   Health Check: $SERVICE_URL/api/health"
echo "   Chat API: $SERVICE_URL/api/ai/chat"
echo ""

# Test the deployed service
echo -e "${BLUE}🧪 Testing deployed service...${NC}"
if curl -f $SERVICE_URL/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Deployment test passed!${NC}"
    
    # Run a quick AI test
    echo -e "${BLUE}🤖 Testing AI chat API...${NC}"
    RESPONSE=$(curl -s -X POST "$SERVICE_URL/api/ai/chat" \\
        -H "Content-Type: application/json" \\
        -d '{
            "message": "Hello AI, please respond with just: AI BRAIN WORKING",
            "context": "test"
        }' | head -200)
    
    if echo "$RESPONSE" | grep -q "AI BRAIN WORKING\|working\|hello"; then
        echo -e "${GREEN}✅ AI Brain is responding correctly!${NC}"
    else
        echo -e "${YELLOW}⚠️  AI Brain deployed but response may need verification${NC}"
        echo "Response preview: $(echo "$RESPONSE" | head -1)"
    fi
else
    echo -e "${RED}❌ Deployment test failed!${NC}"
    exit 1
fi

# Create integration instructions
echo -e "${BLUE}📝 Creating integration guide...${NC}"
cat > AI_BRAIN_INTEGRATION.md << EOF
# ChatterFix AI Brain Service - Integration Guide

## Deployed Service
- **URL**: $SERVICE_URL
- **Status**: Production Ready
- **Features**: Multi-Provider AI (OpenAI, xAI, Anthropic, Local), Chat API

## API Endpoints

### 1. Health Check
\`\`\`bash
curl "$SERVICE_URL/api/health"
\`\`\`

### 2. Chat API
\`\`\`bash
curl -X POST "$SERVICE_URL/api/ai/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "How do I troubleshoot a pump issue?",
    "context": "maintenance"
  }'
\`\`\`

### 3. Provider-Specific Chat
\`\`\`bash
curl -X POST "$SERVICE_URL/api/ai/openai/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Analyze this equipment failure",
    "context": "technical"
  }'
\`\`\`

## Integration with Fix It Fred

Update Fix It Fred to use this production AI service:

1. Change AI_BRAIN_URL to: $SERVICE_URL
2. Test all AI-powered features
3. Monitor response times and costs

## Monitoring

- **Logs**: \`gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" --limit 50\`
- **Metrics**: Available in Google Cloud Console
- **Scaling**: Auto-scales 0-10 instances based on demand

---
ChatterFix AI Brain Service - Powered by Multi-Provider AI
EOF

echo ""
echo -e "${GREEN}🎯 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Update Fix It Fred to use: $SERVICE_URL"
echo "2. Test AI integration thoroughly"
echo "3. Monitor usage and costs"
echo "4. Deploy Fix It Fred service"
echo ""
echo -e "${BLUE}📖 Documentation created: AI_BRAIN_INTEGRATION.md${NC}"
echo ""
echo -e "${YELLOW}💡 Pro Tip: Monitor logs with:${NC}"
echo "   gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
echo ""
echo -e "${GREEN}🚀 AI Brain Service is now live and ready!${NC}"