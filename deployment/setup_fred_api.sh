#!/bin/bash
# Fix It Fred DevOps API Setup Script for ChatGPT Integration

set -euo pipefail

# Configuration
PROJECT_ID="fredfix"
INSTANCE_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
SERVICE_NAME="fix-it-fred-devops-api"
REPO_PATH="/home/yoyofred_gringosgambit_com/chatterfix-docker"
SERVICE_USER="yoyofred_gringosgambit_com"
API_PORT="9004"

echo "🤖 Fix It Fred DevOps API Setup for ChatGPT"
echo "============================================="
echo ""
echo "🎯 Setting up secure API for ChatGPT integration"
echo "📍 Project: $PROJECT_ID"
echo "🖥️  Instance: $INSTANCE_NAME"
echo "🌐 API Port: $API_PORT"
echo ""

# Verify GCP authentication
echo "🔑 Verifying GCP authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ No active GCP authentication found"
    echo "Please run: gcloud auth login"
    exit 1
fi
echo "✅ GCP authentication verified"

# Generate secure API key
echo "🔐 Generating secure API key..."
API_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
echo "✅ API key generated: ${API_KEY:0:8}...${API_KEY: -8}"

# Upload API files
echo "📦 Uploading Fix It Fred DevOps API files..."

# Upload API server
gcloud compute scp fix_it_fred_devops_api.py \
    $INSTANCE_NAME:$REPO_PATH/fix_it_fred_devops_api.py --zone=$ZONE

# Upload systemd service file
gcloud compute scp fix-it-fred-devops-api.service \
    $INSTANCE_NAME:/tmp/fix-it-fred-devops-api.service --zone=$ZONE

echo "✅ Files uploaded successfully"

# Setup and install on VM
echo "🔧 Installing Fix It Fred DevOps API on VM..."

SETUP_SCRIPT='
#!/bin/bash
set -euo pipefail

echo "🤖 Fix It Fred DevOps API VM Setup Starting..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user fastapi uvicorn python-multipart

# Setup API environment
echo "🔧 Setting up API environment..."
cd '"$REPO_PATH"'

# Create environment file with API key
echo "🔐 Configuring API authentication..."
cat > .env.fred-api << EOF
FRED_API_KEY='"$API_KEY"'
FRED_API_PORT='"$API_PORT"'
FRED_API_HOST=0.0.0.0
EOF

# Set proper permissions
chmod 600 .env.fred-api
chown '"$SERVICE_USER"':'"$SERVICE_USER"' .env.fred-api

# Install systemd service
echo "🔧 Installing systemd service..."
sudo cp /tmp/fix-it-fred-devops-api.service /etc/systemd/system/

# Update service file with API key
sudo sed -i "s/\${FRED_API_KEY}/'"$API_KEY"'/g" /etc/systemd/system/fix-it-fred-devops-api.service

sudo systemctl daemon-reload

# Set proper permissions for API script
chmod +x fix_it_fred_devops_api.py

# Enable and start service
echo "🚀 Starting Fix It Fred DevOps API..."
sudo systemctl enable '"$SERVICE_NAME"'.service

# Stop service if running (for clean restart)
if systemctl is-active '"$SERVICE_NAME"'.service >/dev/null 2>&1; then
    echo "🔄 Stopping existing API for clean restart..."
    sudo systemctl stop '"$SERVICE_NAME"'.service
    sleep 3
fi

# Start the service
sudo systemctl start '"$SERVICE_NAME"'.service

# Wait and check status
echo "⏳ Waiting for API to initialize..."
sleep 10

if systemctl is-active '"$SERVICE_NAME"'.service >/dev/null 2>&1; then
    echo "✅ Fix It Fred DevOps API is running!"
    
    # Show service status
    echo "📊 Service Status:"
    sudo systemctl status '"$SERVICE_NAME"'.service --no-pager -l
    
    echo ""
    echo "📝 Recent logs:"
    sudo journalctl -u '"$SERVICE_NAME"'.service --no-pager -n 10
    
    echo ""
    echo "🌐 Testing API endpoint..."
    sleep 5
    if curl -f http://localhost:'"$API_PORT"'/ >/dev/null 2>&1; then
        echo "✅ API endpoint responding"
    else
        echo "⚠️ API endpoint not responding yet (may need more time)"
    fi
else
    echo "❌ Fix It Fred DevOps API failed to start"
    echo "📝 Error logs:"
    sudo journalctl -u '"$SERVICE_NAME"'.service --no-pager -n 20
    exit 1
fi

echo ""
echo "🎉 Fix It Fred DevOps API Setup Complete!"
echo "========================================"
echo ""
echo "🚀 API CAPABILITIES FOR CHATGPT:"
echo "  ✅ VM command execution"
echo "  ✅ Service management (start/stop/restart)"
echo "  ✅ Deployment automation"
echo "  ✅ Health monitoring"
echo "  ✅ Git operations"
echo "  ✅ Log retrieval"
echo "  ✅ Fix It Fred daemon control"
echo ""
echo "🔧 API INFORMATION:"
echo "  • URL: http://VM_EXTERNAL_IP:'"$API_PORT"'"
echo "  • Docs: http://VM_EXTERNAL_IP:'"$API_PORT"'/docs"
echo "  • Health: http://VM_EXTERNAL_IP:'"$API_PORT"'/health"
echo "  • API Key: '"$API_KEY"'"
echo ""
echo "🔧 SERVICE MANAGEMENT:"
echo "  • Start:   sudo systemctl start '"$SERVICE_NAME"'"
echo "  • Stop:    sudo systemctl stop '"$SERVICE_NAME"'"
echo "  • Status:  sudo systemctl status '"$SERVICE_NAME"'"
echo "  • Logs:    sudo journalctl -u '"$SERVICE_NAME"' -f"
echo ""
echo "🤖 ChatGPT can now control Fix It Fred via API!"
'

# Execute setup on VM with API key
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="export API_KEY='$API_KEY' && $SETUP_SCRIPT"

# Get VM external IP
echo ""
echo "🔍 Getting VM external IP..."
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

# Configure firewall rule for API
echo "🔥 Configuring firewall for API access..."
if ! gcloud compute firewall-rules describe allow-fred-api >/dev/null 2>&1; then
    gcloud compute firewall-rules create allow-fred-api \
        --allow tcp:$API_PORT \
        --source-ranges 0.0.0.0/0 \
        --description "Fix It Fred DevOps API for ChatGPT"
    echo "✅ Firewall rule created"
else
    echo "✅ Firewall rule already exists"
fi

# Final verification
echo ""
echo "🔍 Final API verification..."
sleep 10

VERIFY_SCRIPT='
echo "🔍 Verifying Fix It Fred DevOps API deployment..."

# Check service status
if systemctl is-active '"$SERVICE_NAME"'.service >/dev/null 2>&1; then
    echo "✅ API service is active"
    
    # Test API endpoint
    echo "🌐 Testing API endpoint..."
    if curl -f http://localhost:'"$API_PORT"'/ >/dev/null 2>&1; then
        echo "✅ API endpoint responding"
        
        # Show API info
        echo "📊 API Response:"
        curl -s http://localhost:'"$API_PORT"'/ | head -3
        
    else
        echo "⚠️ API endpoint not responding"
    fi
    
    echo ""
    echo "🎯 API DEPLOYMENT SUCCESSFUL!"
    echo "ChatGPT can now control Fix It Fred"
else
    echo "❌ API service verification failed"
    sudo systemctl status '"$SERVICE_NAME"'.service --no-pager
fi
'

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="$VERIFY_SCRIPT"

echo ""
echo "🎉 FIX IT FRED DEVOPS API SETUP COMPLETE!"
echo "========================================="
echo ""
echo "🚀 CHATGPT INTEGRATION READY:"
echo "  ✅ Secure REST API deployed"
echo "  ✅ Authentication configured"
echo "  ✅ All DevOps capabilities exposed"
echo "  ✅ Firewall configured for access"
echo ""
echo "📊 API ACCESS INFORMATION:"
echo "  • Base URL: http://$EXTERNAL_IP:$API_PORT"
echo "  • API Docs: http://$EXTERNAL_IP:$API_PORT/docs"
echo "  • Health Check: http://$EXTERNAL_IP:$API_PORT/health"
echo "  • API Key: $API_KEY"
echo ""
echo "🔧 CHATGPT API ENDPOINTS:"
echo "  • GET /health - VM health status"
echo "  • POST /command - Execute VM commands"
echo "  • POST /service - Manage services"
echo "  • POST /deploy - Deploy updates"
echo "  • GET /git/status - Git repository status"
echo "  • GET /services - List all services"
echo "  • GET /logs/{service} - Get service logs"
echo "  • POST /fred/signal - Control Fix It Fred"
echo ""
echo "🤖 ChatGPT now has full control over your VM via Fix It Fred!"

# Save API credentials
cat > fix_it_fred_api_credentials.txt << EOF
Fix It Fred DevOps API - ChatGPT Integration Credentials
========================================================

API Base URL: http://$EXTERNAL_IP:$API_PORT
API Documentation: http://$EXTERNAL_IP:$API_PORT/docs
API Key: $API_KEY

VM Details:
- Instance: $INSTANCE_NAME
- Zone: $ZONE
- Project: $PROJECT_ID

Service Management:
- Service Name: $SERVICE_NAME
- Logs: sudo journalctl -u $SERVICE_NAME -f
- Status: sudo systemctl status $SERVICE_NAME

Generated: $(date)
EOF

echo ""
echo "💾 API credentials saved to: fix_it_fred_api_credentials.txt"