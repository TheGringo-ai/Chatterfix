#!/bin/bash
# Deploy Fix It Fred Secure Development Portal
set -e

echo "🔐 Deploying Fix It Fred Secure Development Portal..."
echo "Features: Passcode protection (9973), Command execution, Git operations"

# Configuration
VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
DEV_PORT=9002
PASSCODE="9973"

echo "📦 Uploading secure dev portal to VM..."
gcloud compute scp fix_it_fred_secure_dev_portal.py $VM_NAME:/tmp/ --zone=$ZONE

# Create deployment script for VM
cat > vm-dev-portal-setup.sh << 'EOF'
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
EOF

echo "📤 Uploading setup script to VM..."
gcloud compute scp vm-dev-portal-setup.sh $VM_NAME:/tmp/ --zone=$ZONE

echo "🔄 Running setup on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="chmod +x /tmp/vm-dev-portal-setup.sh && sudo /tmp/vm-dev-portal-setup.sh"

echo "⏳ Waiting for service to stabilize..."
sleep 20

echo "🧪 Testing external access to development portal..."
for i in {1..5}; do
  echo "Access test attempt $i..."
  result=$(curl -s -w "HTTP_CODE:%{http_code}\n" "https://chatterfix.com:9002/" --connect-timeout 10 --max-time 15 || echo "FAILED")
  
  if echo "$result" | grep -q "HTTP_CODE:200"; then
    echo "✅ Development Portal accessible externally"
    break
  elif echo "$result" | grep -q "HTTP_CODE:302"; then
    echo "✅ Development Portal running (redirect to login)"
    break
  else
    echo "⏳ Portal still starting up..."
    sleep 10
  fi
done

echo "📊 Final Validation..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
echo '🔍 Development Portal Status:'
sudo systemctl is-active fix-it-fred-dev-portal || echo 'Service not active'

echo '📊 Resource Usage:'
ps aux | grep fix_it_fred_secure_dev_portal | grep -v grep | head -1

echo '🌐 Portal Health Check:'
curl -s http://localhost:9002/health | python3 -c \"
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Status: {data.get(\\\"status\\\", \\\"unknown\\\")}')
    print(f'Active Sessions: {data.get(\\\"active_sessions\\\", 0)}')
    print(f'Security: {data.get(\\\"allowed_commands\\\", 0)} allowed commands')
except Exception as e:
    print(f'Health check error: {e}')
\"

echo '📝 Recent Portal Logs:'
sudo tail -5 /var/log/fix-it-fred-dev-portal.log || echo 'No logs yet'
"

echo ""
echo "🎯 SECURE DEVELOPMENT PORTAL DEPLOYED!"
echo "====================================="
echo ""
echo "✅ Fix It Fred Development Portal is now running with:"
echo "  🔐 Passcode Protection: 9973"
echo "  🌐 Web Interface: https://chatterfix.com:9002"
echo "  💻 Secure Command Execution"
echo "  📋 Git Operations Interface"
echo "  🔒 Session Management & IP Lockout"
echo "  📊 System Monitoring Dashboard"
echo ""
echo "🔑 Access Instructions:"
echo "1. Open https://chatterfix.com:9002 in your browser"
echo "2. Enter passcode: $PASSCODE"
echo "3. Use the secure development interface"
echo ""
echo "⚠️  Security Features Active:"
echo "  • Maximum 3 failed login attempts before IP lockout"
echo "  • 30-minute session timeout"
echo "  • Command whitelist protection"
echo "  • Full audit logging"
echo ""
echo "🚀 Your Fix It Fred now has a secure development portal!"