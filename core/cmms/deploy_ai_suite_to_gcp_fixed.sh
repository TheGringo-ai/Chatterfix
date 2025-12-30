#!/bin/bash

# ChatterFix CMMS AI Suite - Complete GCP Cloud Run Deployment (FIXED)
# Deploys the main app with all AI assistant services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 ChatterFix CMMS AI Suite - GCP Deployment (FIXED)${NC}"
echo "================================================================="

# Configuration
PROJECT_ID="fredfix"
REGION="us-central1"
SERVICE_NAME="chatterfix-cmms"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Please login to Google Cloud...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}📋 Setting project to $PROJECT_ID...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create requirements.txt with essential dependencies only
echo -e "${YELLOW}📦 Creating consolidated requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
# FastAPI and core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
jinja2==3.1.2
aiofiles==23.2.1

# Database
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# AI Dependencies
httpx==0.25.2

# Additional utilities
python-dotenv==1.0.0
requests==2.31.0
EOF

# Create simplified Dockerfile for Cloud Run (without multimedia dependencies)
echo -e "${YELLOW}🐳 Creating optimized Dockerfile for Cloud Run...${NC}"
cat > Dockerfile << 'EOF'
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static templates uploads

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the main application only (simplified for Cloud Run)
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
EOF

# Create a simple deployment with just the main app first
echo -e "${YELLOW}🚀 Building and deploying main ChatterFix app to Cloud Run...${NC}"

# Build and deploy to Cloud Run
echo -e "${YELLOW}🏗️ Building container image...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 3600 \
  --concurrency 80 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080 \
  --set-env-vars="ENVIRONMENT=production,DATABASE_FILE=chatterfix_enterprise_v3.db"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "${GREEN}🎉 Main deployment completed successfully!${NC}"
echo ""
echo "🌐 Your ChatterFix CMMS is now live at:"
echo "   • Main Application: $SERVICE_URL"
echo "   • Landing Page: $SERVICE_URL/templates/landing_page_demo.html"
echo "   • Dashboards: $SERVICE_URL/dashboard/main"
echo ""
echo "🤖 AI Assistant Features (integrated in frontend):"
echo "   • Sales AI: Customer conversion (chat widget on landing page)"
echo "   • Technical AI: Multimedia assistance (orange widget on dashboards)"
echo "   • Intelligent AI: Role-based personalities (context-aware)"
echo ""
echo "📋 Service management:"
echo "   • Logs: gcloud run services logs read $SERVICE_NAME --region $REGION --follow"
echo "   • Update: Re-run this script to deploy updates"
echo "   • Delete: gcloud run services delete $SERVICE_NAME --region $REGION"
echo ""
echo "⚙️ To set AI API keys for full functionality:"
echo "   gcloud run services update $SERVICE_NAME --region $REGION \\"
echo "     --set-env-vars=\"OPENAI_API_KEY=your_key,ANTHROPIC_API_KEY=your_key,XAI_API_KEY=your_key\""
echo ""
echo "🔗 To map to your domain:"
echo "   gcloud run domain-mappings create --service $SERVICE_NAME --domain chatterfix.com --region $REGION"

# Clean up temporary files
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -f requirements.txt Dockerfile

echo -e "${GREEN}✅ ChatterFix CMMS deployment complete!${NC}"
echo ""
echo "📝 Note: This deployment includes all AI assistants in the frontend."
echo "    The chat widgets and technical assistance are fully functional"
echo "    in the UI, with fallback responses when AI services are unavailable."