#!/bin/bash

# ChatterFix CMMS AI Suite - Complete GCP Cloud Run Deployment
# Deploys the main app with all AI assistant services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 ChatterFix CMMS AI Suite - GCP Deployment${NC}"
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

# Create requirements.txt with all AI dependencies
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
sqlite3==3.8.7
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# AI Dependencies
httpx==0.25.2
openai==1.3.0
anthropic==0.7.8

# Multimedia processing
Pillow==10.1.0
opencv-python-headless==4.8.1.78
SpeechRecognition==3.10.0
pydub==0.25.1
audioop-lts==0.2.2
standard-aifc==3.13.0
standard-chunk==3.13.0

# Additional utilities
python-dotenv==1.0.0
numpy==1.24.3
requests==2.31.0
python-multipart==0.0.6
EOF

# Create Dockerfile for Cloud Run
echo -e "${YELLOW}🐳 Creating optimized Dockerfile for Cloud Run...${NC}"
cat > Dockerfile << 'EOF'
# Use Python 3.11 slim image for better compatibility
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Install system dependencies for multimedia processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
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

# Run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
EOF

# Create app.yaml for environment configuration
echo -e "${YELLOW}⚙️ Creating Cloud Run configuration...${NC}"
cat > app.yaml << 'EOF'
runtime: python311

env_variables:
  # Database configuration
  DATABASE_FILE: "chatterfix_enterprise_v3.db"
  
  # AI API Keys (will be set from environment or secrets)
  OPENAI_API_KEY: ""
  ANTHROPIC_API_KEY: ""
  XAI_API_KEY: ""
  
  # Application settings
  DEBUG: "False"
  ENVIRONMENT: "production"

automatic_scaling:
  min_instances: 0
  max_instances: 10
  
resources:
  cpu: 2
  memory: 4Gi

handlers:
- url: /static
  static_dir: static
  secure: always

- url: /.*
  script: auto
  secure: always
EOF

# Create startup script that runs all AI services
echo -e "${YELLOW}🚀 Creating startup script for all AI services...${NC}"
cat > start_ai_suite.py << 'EOF'
#!/usr/bin/env python3
"""
ChatterFix CMMS AI Suite Startup Script
Runs all AI services in the same process for Cloud Run deployment
"""

import asyncio
import uvicorn
import threading
import time
import os
from multiprocessing import Process

def run_main_app():
    """Run the main ChatterFix CMMS application"""
    print("🚀 Starting main ChatterFix CMMS application on port 8080...")
    uvicorn.run("app:app", host="0.0.0.0", port=8080, log_level="info")

def run_sales_ai():
    """Run the sales AI assistant service"""
    print("💰 Starting sales AI assistant on port 8081...")
    os.environ["PORT"] = "8081"
    uvicorn.run("chatterfix_sales_ai:app", host="0.0.0.0", port=8081, log_level="info")

def run_technical_ai():
    """Run the technical AI assistant service"""
    print("🔧 Starting technical AI assistant on port 8082...")
    os.environ["PORT"] = "8082"
    uvicorn.run("technical_ai_assistant:app", host="0.0.0.0", port=8082, log_level="info")

def run_intelligent_ai():
    """Run the intelligent AI assistant service"""
    print("🧠 Starting intelligent AI assistant on port 8083...")
    os.environ["PORT"] = "8083"
    uvicorn.run("intelligent_ai_assistant:app", host="0.0.0.0", port=8083, log_level="info")

def run_claude_code_assistant():
    """Run the Claude code assistant service"""
    print("🤖 Starting Claude code assistant on port 8084...")
    os.environ["PORT"] = "8084"
    uvicorn.run("claude_code_assistant:app", host="0.0.0.0", port=8084, log_level="info")

if __name__ == "__main__":
    print("🎉 ChatterFix CMMS AI Suite - Starting all services...")
    
    # Start all services in separate processes
    processes = []
    
    services = [
        run_main_app,
        run_sales_ai,
        run_technical_ai,
        run_intelligent_ai,
        run_claude_code_assistant
    ]
    
    for service in services:
        process = Process(target=service)
        process.start()
        processes.append(process)
        time.sleep(2)  # Stagger startup
    
    # Wait for all processes
    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        for process in processes:
            process.terminate()
        for process in processes:
            process.join()
EOF

# Update Dockerfile to use the startup script
cat > Dockerfile << 'EOF'
# Use Python 3.11 slim image for better compatibility
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Install system dependencies for multimedia processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
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

# Make startup script executable
RUN chmod +x start_ai_suite.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the AI suite
CMD ["python", "start_ai_suite.py"]
EOF

# Build and deploy to Cloud Run
echo -e "${YELLOW}🏗️ Building container image...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --concurrency 80 \
  --max-instances 10 \
  --min-instances 1 \
  --port 8080 \
  --set-env-vars="ENVIRONMENT=production,DATABASE_FILE=chatterfix_enterprise_v3.db"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "🌐 Your ChatterFix CMMS AI Suite is now live at:"
echo "   • Main Application: $SERVICE_URL"
echo "   • Sales Assistant: $SERVICE_URL (integrated)"
echo "   • Technical Assistant: $SERVICE_URL (integrated)"
echo "   • Landing Page: $SERVICE_URL/templates/landing_page_demo.html"
echo ""
echo "🤖 AI Assistant Services (all integrated):"
echo "   • Sales AI: Customer conversion and ROI calculator"
echo "   • Technical AI: Photo analysis, voice commands, multimedia"
echo "   • Intelligent AI: Role-based personalities for all user types"
echo "   • Claude Code AI: Development and code assistance"
echo ""
echo "📋 Service management:"
echo "   • Logs: gcloud run services logs read $SERVICE_NAME --region $REGION"
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
rm -f app.yaml start_ai_suite.py

echo -e "${GREEN}✅ ChatterFix CMMS AI Suite deployment complete!${NC}"