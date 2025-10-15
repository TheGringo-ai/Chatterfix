#!/bin/bash
set -e

echo "🔧 Setting up Fix It Fred Secure Development Portal on VM..."

# Install additional dependencies
echo "📋 Installing Python dependencies..."
pip3 install --user flask || true

# Create service directory
sudo mkdir -p /opt/fix-it-fred-dev
sudo cp /tmp/fix_it_fred_secure_dev_portal.py /opt/fix-it-fred-dev/
sudo chmod +x /opt/fix-it-fred-dev/fix_it_fred_secure_dev_portal.py

# Create systemd service
echo "⚙️ Creating systemd service for development portal..."
sudo tee /etc/systemd/system/fix-it-fred-dev-portal.service > /dev/null << 'SERVICE'
[Unit]
Description=Fix It Fred Secure Development Portal
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fix-it-fred-dev
ExecStart=/usr/bin/python3 /opt/fix-it-fred-dev/fix_it_fred_secure_dev_portal.py --port=9002 --host=0.0.0.0
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/fix-it-fred-dev
Environment=FLASK_ENV=production

# Resource limits (lightweight)
MemoryMax=256M
CPUQuota=15%

# Logging
StandardOutput=append:/var/log/fix-it-fred-dev-portal.log
StandardError=append:/var/log/fix-it-fred-dev-portal-error.log

[Install]
WantedBy=multi-user.target
SERVICE

# Configure firewall for development port
echo "🔥 Configuring firewall..."
sudo ufw allow 9002/tcp || true

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
echo "🚀 Starting Fix It Fred Development Portal..."
sudo systemctl enable fix-it-fred-dev-portal.service
sudo systemctl start fix-it-fred-dev-portal.service

# Wait for startup
echo "⏳ Waiting for development portal to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
sudo systemctl status fix-it-fred-dev-portal.service --no-pager

echo "🌐 Testing development portal endpoints..."
# Test health endpoint
curl -s http://localhost:9002/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"✅ Portal Status: {data.get('status', 'unknown')}\")
    print(f\"🔐 Active Sessions: {data.get('active_sessions', 0)}\")
    print(f\"🚫 Locked IPs: {data.get('locked_ips', 0)}\")
    print(f\"📋 Allowed Commands: {data.get('allowed_commands', 0)}\")
except Exception as e:
    print(f'❌ API not responding: {e}')
"

echo ""
echo "🎉 Fix It Fred Development Portal Deployed Successfully!"
echo "========================================================="
echo ""
echo "📋 Service Details:"
echo "  • Service: fix-it-fred-dev-portal.service"
echo "  • Port: 9002"
echo "  • Passcode: 9973"
echo "  • Logs: /var/log/fix-it-fred-dev-portal.log"
echo ""
echo "🌐 Access Portal:"
echo "  • Local: http://localhost:9002"
echo "  • External: https://chatterfix.com:9002"
echo ""
echo "🔐 Security Features:"
echo "  • Passcode protection (9973)"
echo "  • Session management with timeout"
echo "  • IP lockout after 3 failed attempts"
echo "  • Command whitelist security"
echo "  • Audit logging"
echo ""
echo "💻 Available Commands:"
echo "  • Git operations (status, add, commit, push)"
echo "  • System monitoring (ps, top, systemctl)"
echo "  • File operations (ls, cat, tail, head)"
echo "  • Development tools (python3, pip3, npm)"
echo ""
echo "🔍 Monitor portal:"
echo "  sudo systemctl status fix-it-fred-dev-portal"
echo "  sudo journalctl -u fix-it-fred-dev-portal -f"
echo "  tail -f /var/log/fix-it-fred-dev-portal.log"
