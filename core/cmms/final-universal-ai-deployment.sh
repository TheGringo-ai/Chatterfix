#!/bin/bash

echo "🚀 FINAL UNIVERSAL AI ASSISTANT DEPLOYMENT"
echo "============================================"

# Force stop all processes and clean slate
echo "🛑 Force stopping all ChatterFix processes..."
sudo pkill -9 -f "python.*app.py" || true
sudo pkill -9 -f "uvicorn" || true
sudo pkill -9 -f "chatterfix" || true
sleep 5

# Stop systemd services
echo "🛑 Stopping systemd services..."
sudo systemctl stop chatterfix-cmms || true
sudo systemctl stop chatterfix || true
sleep 3

# Navigate to the correct directory with universal AI code
cd /opt/chatterfix-cmms/core/cmms || {
    echo "❌ CMMS directory not found!"
    exit 1
}

# Force pull latest code
echo "📥 Force pulling latest universal AI code..."
git fetch origin
git reset --hard origin/main
git clean -fd

# Verify universal AI files exist
echo "🔍 Verifying Universal AI files..."
if [ ! -f "universal_ai_endpoints.py" ]; then
    echo "❌ universal_ai_endpoints.py not found!"
    exit 1
fi

if ! grep -q "universal_ai_endpoints" app.py; then
    echo "❌ app.py missing universal AI integration!"
    exit 1
fi

echo "✅ Universal AI files verified"

# Create/update systemd service to use correct directory
echo "⚙️ Updating systemd service configuration..."
sudo tee /etc/systemd/system/chatterfix-cmms.service > /dev/null << 'EOF'
[Unit]
Description=ChatterFix CMMS with Universal AI Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chatterfix-cmms/core/cmms
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=3
Environment=PYTHONPATH=/opt/chatterfix-cmms/core/cmms
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "🔄 Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable chatterfix-cmms
sudo systemctl start chatterfix-cmms

# Wait for service to start
echo "⏳ Waiting for service to initialize..."
sleep 15

# Test the universal AI endpoints
echo "🧪 Testing Universal AI Assistant endpoints..."

# Test 1: Health check
echo "1. Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
echo "   Health check: HTTP $HEALTH_STATUS"

# Test 2: AI injection script
echo "2. Testing /ai-inject.js endpoint..."
AI_INJECT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ai-inject.js)
if [ "$AI_INJECT_STATUS" = "200" ]; then
    echo "   ✅ AI injection endpoint working (HTTP $AI_INJECT_STATUS)"
else
    echo "   ❌ AI injection endpoint failed (HTTP $AI_INJECT_STATUS)"
fi

# Test 3: Global AI processing
echo "3. Testing /global-ai/process-message endpoint..."
AI_PROCESS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/global-ai/process-message \
  -H "Content-Type: application/json" \
  -d '{"message": "Test universal AI", "page": "/dashboard"}')
if [ "$AI_PROCESS_STATUS" = "200" ]; then
    echo "   ✅ AI processing endpoint working (HTTP $AI_PROCESS_STATUS)"
else
    echo "   ❌ AI processing endpoint failed (HTTP $AI_PROCESS_STATUS)"
fi

# Test 4: Dashboard with AI injection
echo "4. Testing dashboard AI injection..."
DASHBOARD_CONTENT=$(curl -s http://localhost:8000/)
if echo "$DASHBOARD_CONTENT" | grep -q "ChatterFix CMMS"; then
    echo "   ✅ CMMS dashboard loading"
    if echo "$DASHBOARD_CONTENT" | grep -q "ai-inject.js\|chatterFixAILoaded"; then
        echo "   ✅ AI injection detected in dashboard"
    else
        echo "   ⚠️ AI injection not detected (may need middleware fix)"
    fi
else
    echo "   ❌ Dashboard not loading correctly"
fi

# Verify single process
echo "5. Verifying single process..."
PROCESS_COUNT=$(pgrep -f "python.*app.py" | wc -l)
echo "   Running Python processes: $PROCESS_COUNT"

# Service status
echo "6. Service status:"
sudo systemctl status chatterfix-cmms --no-pager -l | head -10

echo ""
echo "🎉 UNIVERSAL AI ASSISTANT DEPLOYMENT COMPLETE!"
echo "============================================"
echo "🌐 Production URL: https://chatterfix.com"
echo "🤖 Universal AI endpoints deployed"
echo "📱 AI assistant should appear on all dashboard pages"
echo ""
echo "🔍 Quick Test URLs:"
echo "   Main Dashboard: http://$(curl -s ifconfig.me):8000/"
echo "   AI Injection:   http://$(curl -s ifconfig.me):8000/ai-inject.js"
echo "   Health Check:   http://$(curl -s ifconfig.me):8000/health"