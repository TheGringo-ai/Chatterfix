#!/bin/bash
set -e

echo "🔧 Setting up Fix It Fred Git Integration on VM..."

# Install dependencies
echo "📋 Installing Python dependencies..."
pip3 install --user watchdog flask cryptography psutil schedule requests || true

# Create service directory
sudo mkdir -p /opt/fix-it-fred-git
sudo cp /tmp/fix_it_fred_git_integration_stable.py /opt/fix-it-fred-git/
sudo chmod +x /opt/fix-it-fred-git/fix_it_fred_git_integration_stable.py

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/fix-it-fred-git.service > /dev/null << 'SERVICE'
[Unit]
Description=Fix It Fred Git Integration Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fix-it-fred-git
ExecStart=/usr/bin/python3 /opt/fix-it-fred-git/fix_it_fred_git_integration_stable.py --repo-path=/home/yoyofred_gringosgambit_com/chatterfix-docker
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/fix-it-fred-git
Environment=FLASK_ENV=production

# Resource limits
MemoryMax=512M
CPUQuota=25%

# Logging
StandardOutput=append:/var/log/fix-it-fred-git.log
StandardError=append:/var/log/fix-it-fred-git-error.log

[Install]
WantedBy=multi-user.target
SERVICE

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
echo "🚀 Starting Fix It Fred Git Integration service..."
sudo systemctl enable fix-it-fred-git.service
sudo systemctl start fix-it-fred-git.service

# Wait for startup
echo "⏳ Waiting for service to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
sudo systemctl status fix-it-fred-git.service --no-pager

echo "🌐 Testing API endpoints..."
# Test health endpoint
curl -s http://localhost:9001/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"✅ Service Status: {data.get('status', 'unknown')}\")
    print(f\"🤖 AI Providers: {len(data.get('ai_providers', {}))}\")
    print(f\"📊 Queue Size: {data.get('queue_size', 0)}\")
    resources = data.get('resources', {})
    print(f\"💾 Memory: {resources.get('memory_mb', 0)}MB / {resources.get('memory_limit', 0)}MB\")
    print(f\"⚡ CPU: {resources.get('cpu_percent', 0)}% / {resources.get('cpu_limit', 0)}%\")
except:
    print('❌ API not responding yet')
"

echo ""
echo "🎉 Fix It Fred Git Integration Deployed Successfully!"
echo "================================="
echo ""
echo "📋 Service Details:"
echo "  • Service: fix-it-fred-git.service"
echo "  • Port: 9001"
echo "  • Logs: /var/log/fix-it-fred-git.log"
echo "  • Config: /tmp/fix_it_fred_git/"
echo ""
echo "🌐 API Endpoints:"
echo "  • Health: http://localhost:9001/health"
echo "  • Git Status: http://localhost:9001/api/git/status"
echo "  • Providers: http://localhost:9001/api/providers"
echo "  • Recent Commits: http://localhost:9001/api/git/commits"
echo ""
echo "🔑 To add AI provider API keys:"
echo "  curl -X POST http://localhost:9001/api/providers/openai/key \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"api_key\":\"your-openai-key\"}'"
echo ""
echo "🔍 Monitor service:"
echo "  sudo systemctl status fix-it-fred-git"
echo "  sudo journalctl -u fix-it-fred-git -f"
echo "  tail -f /var/log/fix-it-fred-git.log"
