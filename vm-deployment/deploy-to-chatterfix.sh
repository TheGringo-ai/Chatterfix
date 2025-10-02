#!/bin/bash

echo "🚀 DEPLOYING CHATTERFIX CMMS TO VM"
echo "=================================="

# Configuration
DOMAIN="chatterfix.com"
VM_PATH="/opt/chatterfix-cmms"
SERVICE_NAME="chatterfix-cmms"

# Kill any existing background processes locally
echo "🛑 Stopping local background processes..."
pkill -f "python.*app.py" || true

echo "📦 Creating deployment package..."
tar -czf chatterfix-deployment.tar.gz app.py universal_ai_endpoints.py collaborative_ai_system.py dev_ai_assistant.py .env.collaborative

echo "📤 Uploading to chatterfix.com..."
scp chatterfix-deployment.tar.gz chatterfix-prod:/tmp/

echo "🔧 Deploying on remote server..."
ssh chatterfix-prod << 'ENDSSH'

echo "🛑 Stopping existing services..."
systemctl stop chatterfix-cmms || true
pkill -9 -f "python.*app.py" || true
pkill -9 -f "uvicorn" || true
sleep 3

echo "📁 Setting up deployment directory..."
mkdir -p /opt/chatterfix-cmms
cd /opt/chatterfix-cmms

echo "📦 Extracting deployment package..."
tar -xzf /tmp/chatterfix-deployment.tar.gz -C /opt/chatterfix-cmms/
rm -f /tmp/chatterfix-deployment.tar.gz

echo "🐍 Installing Python dependencies..."
pip3 install fastapi uvicorn requests || {
    echo "Installing pip packages via apt..."
    apt-get update
    apt-get install -y python3-fastapi python3-uvicorn python3-requests
}

echo "🗄️ Setting up data directory..."
mkdir -p /opt/chatterfix-cmms/data
chown -R root:root /opt/chatterfix-cmms

echo "⚙️ Creating systemd service..."
tee /etc/systemd/system/chatterfix-cmms.service > /dev/null << 'EOF'
[Unit]
Description=ChatterFix CMMS with Universal AI Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chatterfix-cmms
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=3
Environment=PYTHONPATH=/opt/chatterfix-cmms

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Starting service..."
systemctl daemon-reload
systemctl enable chatterfix-cmms
systemctl start chatterfix-cmms

echo "⏳ Waiting for service to initialize..."
sleep 10

echo "🧪 Testing deployment..."
# Test health endpoint
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
echo "Health check: HTTP $HEALTH_STATUS"

# Test AI injection script
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ai-inject.js)
echo "AI inject script: HTTP $AI_STATUS"

# Test dashboard
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
echo "Dashboard: HTTP $DASHBOARD_STATUS"

# Test AI processing
AI_PROCESS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/global-ai/process-message \
  -H "Content-Type: application/json" \
  -d '{"message": "test deployment", "page": "/"}')
echo "AI processing: HTTP $AI_PROCESS_STATUS"

echo "🔍 Service status:"
systemctl status chatterfix-cmms --no-pager | head -5

PUBLIC_IP=$(curl -s ifconfig.me || echo "unknown")
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo "🌐 Access your app at: http://$PUBLIC_IP:8080"
echo "🤖 AI assistant will appear on all pages"
echo "📊 Dashboard: http://$PUBLIC_IP:8080/"
echo "🔧 Work Orders: http://$PUBLIC_IP:8080/work-orders"
echo "🏭 Assets: http://$PUBLIC_IP:8080/assets"
echo "📦 Parts: http://$PUBLIC_IP:8080/parts"
echo ""
echo "✅ All tests should show HTTP 200"

ENDSSH

echo "🎉 Remote deployment completed!"
echo "Your ChatterFix CMMS is now running at https://chatterfix.com:8080"