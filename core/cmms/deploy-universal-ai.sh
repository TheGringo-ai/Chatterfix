#!/bin/bash

# Universal AI Assistant Deployment Script
echo "🤖 Deploying Universal AI Assistant to ChatterFix CMMS..."

# Change to the correct app directory
cd /opt/chatterfix-cmms/core/cmms || {
    echo "❌ Could not find CMMS directory"
    exit 1
}

# Stop the service safely
echo "🛑 Stopping ChatterFix CMMS service..."
sudo systemctl stop chatterfix-cmms 2>/dev/null || true

# Pull the latest code with universal AI
echo "📥 Pulling latest code from main branch..."
git fetch origin
git reset --hard origin/main

# Verify universal AI files are present
echo "🔍 Verifying Universal AI files..."
if [ -f "universal_ai_endpoints.py" ]; then
    echo "✅ universal_ai_endpoints.py found"
else
    echo "❌ universal_ai_endpoints.py missing"
    exit 1
fi

# Check app.py for universal AI integration
if grep -q "universal_ai_endpoints" app.py; then
    echo "✅ app.py has universal AI integration"
else
    echo "❌ app.py missing universal AI integration"
    exit 1
fi

# Install any new dependencies
echo "📦 Installing dependencies..."
pip3 install --upgrade -r requirements.txt 2>/dev/null || pip3 install fastapi uvicorn requests

# Set proper permissions
echo "🔐 Setting file permissions..."
sudo chown -R $(whoami):$(whoami) /opt/chatterfix-cmms
chmod +x *.py 2>/dev/null || true

# Start the service
echo "🚀 Starting ChatterFix CMMS with Universal AI..."
sudo systemctl start chatterfix-cmms
sudo systemctl enable chatterfix-cmms

# Wait for service to start
echo "⏳ Waiting for service to initialize..."
sleep 10

# Test the universal AI endpoints
echo "🧪 Testing Universal AI endpoints..."

# Test 1: AI injection script
echo "Testing /ai-inject.js endpoint..."
AI_INJECT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ai-inject.js)
if [ "$AI_INJECT_STATUS" = "200" ]; then
    echo "✅ AI injection endpoint working"
else
    echo "❌ AI injection endpoint failed (HTTP $AI_INJECT_STATUS)"
fi

# Test 2: Global AI processing
echo "Testing /global-ai/process-message endpoint..."
AI_PROCESS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/global-ai/process-message \
  -H "Content-Type: application/json" \
  -d '{"message": "Test deployment", "page": "/dashboard"}')
if [ "$AI_PROCESS_STATUS" = "200" ]; then
    echo "✅ AI processing endpoint working"
else
    echo "❌ AI processing endpoint failed (HTTP $AI_PROCESS_STATUS)"
fi

# Test 3: Main dashboard injection
echo "Testing AI injection in main dashboard..."
DASHBOARD_CONTENT=$(curl -s http://localhost:8000/)
if echo "$DASHBOARD_CONTENT" | grep -q "chatterFixAILoaded\|ai-inject.js"; then
    echo "✅ AI assistant being injected into pages"
else
    echo "⚠️ AI injection may not be working properly"
fi

# Check service status
echo "📊 Service status:"
sudo systemctl status chatterfix-cmms --no-pager -l | head -20

echo "🎉 Universal AI Assistant deployment complete!"
echo "🌐 Visit https://chatterfix.com to test the AI assistant"
echo "🔍 Look for the floating 🤖 button on all dashboard pages"

# Final verification
curl -s -I http://localhost:8000/health | head -1
echo "✅ Health check completed"