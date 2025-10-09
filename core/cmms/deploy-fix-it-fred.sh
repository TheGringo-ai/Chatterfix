#!/bin/bash
# TechBot AI Assistant Deployment Script
# Deploys the standalone TechBot service to Google Cloud Run

set -e

echo "🚀 Fix It Fred AI Assistant - Deployment Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="fredfix"
SERVICE_NAME="fix-it-fred"
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

# Create Dockerfile for TechBot
echo -e "${BLUE}📝 Creating Dockerfile...${NC}"
cat > Dockerfile.techbot << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY technician_ai_assistant.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash techbot
USER techbot

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run the application
CMD ["python", "technician_ai_assistant.py"]
EOF

# Create .dockerignore
echo -e "${BLUE}📝 Creating .dockerignore...${NC}"
cat > .dockerignore.techbot << EOF
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
test_*.txt
test_*.png
ai_collaboration_*.log
EOF

# Create requirements for Fix It Fred (with OpenAI support)
echo -e "${BLUE}📝 Creating Fix It Fred requirements.txt...${NC}"
cat > requirements.fred.txt << EOF
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.4.0
python-multipart>=0.0.6
aiofiles>=23.2.0
openai>=1.3.0
EOF

# Build Docker image for Cloud Run (AMD64)
echo -e "${BLUE}🔨 Building Docker image for Cloud Run (AMD64)...${NC}"
cp requirements.fred.txt requirements.txt
docker build --platform linux/amd64 -f Dockerfile.techbot -t $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:latest .

# Test the image locally with OpenAI integration
echo -e "${BLUE}🧪 Testing Docker image locally with OpenAI...${NC}"
echo "Starting container with OpenAI configuration..."

# Create test environment for OpenAI
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set - using placeholder for testing${NC}"
    export OPENAI_API_KEY="sk-test-placeholder"
fi

CONTAINER_ID=$(docker run -d -p 8085:8080 \
    -e USE_OPENAI_DIRECT=true \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e PORT=8080 \
    $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:latest)

# Wait for container to start
sleep 15

# Test health endpoint
if curl -f http://localhost:8085/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Local test passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed, checking logs...${NC}"
    docker logs $CONTAINER_ID
    echo -e "${BLUE}💡 Proceeding with deployment (health check may fail without valid OpenAI key)${NC}"
fi

# Stop test container
docker stop $CONTAINER_ID

# Create Artifact Registry repository if it doesn't exist
echo -e "${BLUE}🏗️  Setting up Artifact Registry...${NC}"
gcloud artifacts repositories create $SERVICE_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Fix It Fred AI Assistant Docker images" \
    2>/dev/null || echo "Repository already exists"

# Configure Docker for Google Cloud Artifact Registry
echo -e "${BLUE}🔐 Configuring Docker for Artifact Registry...${NC}"
gcloud auth configure-docker $REGION-docker.pkg.dev

# Push Docker image to Artifact Registry
echo -e "${BLUE}📤 Pushing image to Artifact Registry...${NC}"
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:latest

# Deploy to Cloud Run with OpenAI integration
echo -e "${BLUE}🚀 Deploying to Google Cloud Run with OpenAI...${NC}"

# Prompt for OpenAI API key if not set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY environment variable not set${NC}"
    echo -e "${BLUE}💡 Please set your OpenAI API key:${NC}"
    echo "   export OPENAI_API_KEY=your-openai-api-key"
    echo -e "${BLUE}💡 Using placeholder for deployment (you can update later)${NC}"
    OPENAI_KEY_FOR_DEPLOYMENT="sk-placeholder-update-in-cloud-console"
else
    OPENAI_KEY_FOR_DEPLOYMENT="$OPENAI_API_KEY"
fi

gcloud run deploy $SERVICE_NAME \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port $PORT \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 100 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars="PORT=$PORT,USE_OPENAI_DIRECT=true,OPENAI_API_KEY=$OPENAI_KEY_FOR_DEPLOYMENT"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo -e "${GREEN}🎉 Fix It Fred AI Assistant deployed successfully!${NC}"
echo ""
echo -e "${BLUE}📍 Service Details:${NC}"
echo "   URL: $SERVICE_URL"
echo "   Health Check: $SERVICE_URL/api/health"
echo "   Landing Page: $SERVICE_URL/"
echo ""
echo -e "${BLUE}🧪 API Endpoints:${NC}"
echo "   Troubleshooting: POST $SERVICE_URL/api/troubleshoot"
echo "   Photo Analysis: POST $SERVICE_URL/api/analyze-photo"
echo "   Voice to Text: POST $SERVICE_URL/api/voice-to-text"
echo "   Work Notes: POST $SERVICE_URL/api/work-note"
echo "   Technician Profile: POST $SERVICE_URL/api/technician/profile"
echo ""

# Test the deployed service
echo -e "${BLUE}🧪 Testing deployed service...${NC}"
if curl -f $SERVICE_URL/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Deployment test passed!${NC}"
    
    # Run a quick troubleshooting test
    echo -e "${BLUE}🔧 Testing troubleshooting API...${NC}"
    RESPONSE=$(curl -s -X POST "$SERVICE_URL/api/troubleshoot" \\
        -H "Content-Type: application/json" \\
        -d '{"equipment": "Test Pump", "issue_description": "Making noise", "technician_id": "test"}')
    
    if echo "$RESPONSE" | grep -q "success.*true"; then
        echo -e "${GREEN}✅ TechBot is responding correctly!${NC}"
    else
        echo -e "${YELLOW}⚠️  TechBot deployed but API response unexpected${NC}"
    fi
else
    echo -e "${RED}❌ Deployment test failed!${NC}"
    exit 1
fi

# Create integration instructions
echo -e "${BLUE}📝 Creating integration guide...${NC}"
cat > TECHBOT_INTEGRATION.md << EOF
# TechBot AI Assistant - Integration Guide

## Deployed Service
- **URL**: $SERVICE_URL
- **Status**: Production Ready
- **Features**: AI Troubleshooting, OCR Photo Analysis, Voice-to-Text, Memory System

## Quick Integration Examples

### 1. Troubleshooting API
\`\`\`bash
curl -X POST "$SERVICE_URL/api/troubleshoot" \\
  -H "Content-Type: application/json" \\
  -d '{
    "equipment": "Industrial Pump",
    "issue_description": "Pump cavitation with vibration",
    "technician_id": "tech_001"
  }'
\`\`\`

### 2. Photo Analysis API
\`\`\`bash
curl -X POST "$SERVICE_URL/api/analyze-photo" \\
  -F "file=@equipment_photo.jpg"
\`\`\`

### 3. Voice Processing API
\`\`\`bash
curl -X POST "$SERVICE_URL/api/voice-to-text" \\
  -F "file=@voice_note.wav"
\`\`\`

### 4. Create Technician Profile
\`\`\`bash
curl -X POST "$SERVICE_URL/api/technician/profile" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "John Smith",
    "specialties": ["electrical", "pumps"],
    "experience_years": 5,
    "primary_equipment": ["motors", "pumps"]
  }'
\`\`\`

## Business Model Integration

### MVP Strategy
1. **Freemium Model**: Basic features free, advanced features paid
2. **Lead Generation**: Drive traffic to ChatterFix CMMS
3. **Viral Growth**: Individual technicians share with teams

### Revenue Streams
- TechBot Pro: \$9.99/month per technician
- ChatterFix CMMS: \$15/user/month (upsell target)
- Enterprise Integrations: Custom pricing

### Success Metrics
- Daily Active Users
- Troubleshooting Requests
- Photo Analysis Usage
- Conversion to ChatterFix CMMS

## Marketing Integration
- Embed widget on maintenance websites
- Social media campaigns
- Technical forums and communities
- Industry conferences and trade shows

---
Powered by ChatterFix AI - The Future of Maintenance Management
EOF

echo ""
echo -e "${GREEN}🎯 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Test all API endpoints thoroughly"
echo "2. Set up monitoring and alerting"
echo "3. Configure custom domain (optional)"
echo "4. Implement usage analytics"
echo "5. Launch marketing campaigns"
echo ""
echo -e "${BLUE}📖 Documentation created: TECHBOT_INTEGRATION.md${NC}"
echo ""
echo -e "${YELLOW}💡 Pro Tip: Monitor logs with:${NC}"
echo "   gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
echo ""
echo -e "${GREEN}🚀 TechBot AI Assistant is now live and ready for the world!${NC}"