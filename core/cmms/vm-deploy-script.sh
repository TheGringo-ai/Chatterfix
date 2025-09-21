#!/bin/bash

# VM Auto-Deploy Script for Universal AI Assistant
echo "🚀 Starting VM deployment of Universal AI Assistant..."

# Set variables
REPO_URL="https://github.com/TheGringo-ai/Chatterfix.git"
APP_DIR="/opt/chatterfix-cmms"
SERVICE_NAME="chatterfix-cmms"

# Change to app directory
cd $APP_DIR || exit 1

# Stop the service
echo "🛑 Stopping ChatterFix service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Pull latest code
echo "📥 Pulling latest code from main branch..."
git pull origin main

# Install/update dependencies if requirements changed
if [ -f requirements.txt ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt --quiet
fi

# Set proper permissions
echo "🔐 Setting file permissions..."
sudo chown -R $(whoami):$(whoami) $APP_DIR
chmod +x *.py *.sh 2>/dev/null || true

# Restart the service
echo "🔄 Starting ChatterFix service..."
sudo systemctl start $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# Check service status
echo "✅ Checking service status..."
sudo systemctl status $SERVICE_NAME --no-pager -l

# Test the universal AI endpoints
echo "🤖 Testing Universal AI endpoints..."
sleep 5

# Test AI injection endpoint
echo "Testing /ai-inject.js endpoint..."
curl -s -I http://localhost:8000/ai-inject.js | head -1

# Test global AI processing endpoint
echo "Testing /global-ai/process-message endpoint..."
curl -s -X POST http://localhost:8000/global-ai/process-message \
  -H "Content-Type: application/json" \
  -d '{"message": "Test deployment", "page": "/dashboard"}' | head -1

echo "🎉 VM deployment complete!"
echo "🌐 Universal AI Assistant is now available on: https://chatterfix.com"
echo "🔧 Check all dashboard pages for the floating AI assistant button"