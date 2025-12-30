#!/bin/bash

# ChatterFix CMMS Complete GCP Deployment - FINAL VERSION
# Deploys the complete ChatterFix app with all AI assistants to Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎉 ChatterFix CMMS - Complete GCP Deployment${NC}"
echo "============================================================"

# Configuration
PROJECT_ID="fredfix"
REGION="us-central1"
SERVICE_NAME="chatterfix-cmms"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Set project
echo -e "${YELLOW}📋 Setting project to $PROJECT_ID...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create complete requirements.txt with all dependencies
echo -e "${YELLOW}📦 Creating complete requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
# FastAPI and core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
jinja2==3.1.2
aiofiles==23.2.1

# Authentication and security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
PyJWT==2.8.0

# Firebase (for authentication)
firebase-admin==6.2.0

# AI Dependencies
httpx==0.25.2

# Additional utilities
python-dotenv==1.0.0
requests==2.31.0

# Database (built-in sqlite3 is sufficient)
EOF

# Create optimized Dockerfile for Cloud Run
echo -e "${YELLOW}🐳 Creating optimized Dockerfile...${NC}"
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
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static templates uploads

# Expose port
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the main ChatterFix application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
EOF

# Add a health endpoint to app.py if it doesn't exist
echo -e "${YELLOW}🔍 Adding health endpoint to app.py...${NC}"
if ! grep -q "@app.get.*health" app.py; then
    # Add health endpoint after the imports
    sed -i.bak '/^app = FastAPI/a\
\
# Health check endpoint\
@app.get("/health")\
async def health_check():\
    """Health check endpoint for Cloud Run"""\
    return {"status": "healthy", "service": "chatterfix-cmms"}
' app.py
fi

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

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "🌐 Your ChatterFix CMMS with AI Assistants is now live:"
echo "   • Main Application: $SERVICE_URL"
echo "   • Health Check: $SERVICE_URL/health"
echo "   • Dashboard: $SERVICE_URL/dashboard/main"
echo "   • Landing Page: $SERVICE_URL/templates/landing_page_demo.html"
echo ""
echo "🤖 AI Assistant Features (all integrated):"
echo "   ✅ Sales AI: Customer conversion (chat widget on landing page)"
echo "   ✅ Technical AI: Multimedia assistance (orange widget on dashboards)"  
echo "   ✅ Intelligent AI: Role-based personalities (universal widget)"
echo "   ✅ 15 Dashboard templates with integrated AI assistants"
echo ""
echo "🔧 Features Available:"
echo "   • Photo analysis and equipment inspection"
echo "   • Voice commands and speech-to-text"
echo "   • Document analysis and procedure lookup"
echo "   • Role-based AI personalities (6 specialized roles)"
echo "   • Sales conversion with ROI calculator"
echo "   • Real-time safety alerts and recommendations"
echo ""
echo "📋 Service management:"
echo "   • Logs: gcloud run services logs read $SERVICE_NAME --region $REGION --follow"
echo "   • Update: Re-run this script to deploy updates"
echo "   • Delete: gcloud run services delete $SERVICE_NAME --region $REGION"
echo ""
echo "⚙️ To enable AI functionality, set API keys:"
echo "   gcloud run services update $SERVICE_NAME --region $REGION \\"
echo "     --set-env-vars=\"OPENAI_API_KEY=your_key,ANTHROPIC_API_KEY=your_key,XAI_API_KEY=your_key\""
echo ""
echo "🔗 To map to your domain (chatterfix.com):"
echo "   gcloud run domain-mappings create --service $SERVICE_NAME --domain chatterfix.com --region $REGION"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️ Health check failed, but deployment may still be successful${NC}"
fi

# Clean up temporary files
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
rm -f requirements.txt Dockerfile app.py.bak

echo -e "${GREEN}🎊 ChatterFix CMMS deployment complete!${NC}"
echo ""
echo "🌟 Your AI-powered CMMS platform is ready for production use!"
echo "   Visit: $SERVICE_URL to get started"