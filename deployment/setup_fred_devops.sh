#!/bin/bash
# Fix It Fred DevOps Production Setup Script
# Sets up autonomous deployment, monitoring, and healing system

set -euo pipefail

# Configuration
PROJECT_ID="fredfix"
INSTANCE_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
SERVICE_NAME="fix-it-fred-devops"
REPO_PATH="/home/yoyofred_gringosgambit_com/chatterfix-docker"
SERVICE_USER="yoyofred_gringosgambit_com"

echo "🤖 Fix It Fred DevOps Production Setup"
echo "======================================"
echo ""
echo "🎯 Setting up autonomous VM management system"
echo "📍 Project: $PROJECT_ID"
echo "🖥️  Instance: $INSTANCE_NAME"
echo "🌍 Zone: $ZONE"
echo ""

# Verify GCP authentication
echo "🔑 Verifying GCP authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ No active GCP authentication found"
    echo "Please run: gcloud auth login"
    exit 1
fi
echo "✅ GCP authentication verified"

# Check if VM exists and is running
echo "🔍 Checking VM status..."
VM_STATUS=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="value(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$VM_STATUS" = "NOT_FOUND" ]; then
    echo "❌ VM $INSTANCE_NAME not found in zone $ZONE"
    exit 1
elif [ "$VM_STATUS" != "RUNNING" ]; then
    echo "⚠️ VM is not running (status: $VM_STATUS)"
    echo "Starting VM..."
    gcloud compute instances start $INSTANCE_NAME --zone=$ZONE
    echo "⏳ Waiting for VM to be ready..."
    sleep 30
fi
echo "✅ VM is running"

# Upload Fix It Fred DevOps files
echo "📦 Uploading Fix It Fred DevOps system files..."

# Upload daemon script
gcloud compute scp fix_it_fred_devops_daemon.py \
    $INSTANCE_NAME:$REPO_PATH/fix_it_fred_devops_daemon.py --zone=$ZONE

# Upload systemd service file
gcloud compute scp fix-it-fred-devops.service \
    $INSTANCE_NAME:/tmp/fix-it-fred-devops.service --zone=$ZONE

echo "✅ Files uploaded successfully"

# Setup and install on VM
echo "🔧 Installing Fix It Fred DevOps system on VM..."

SETUP_SCRIPT='
#!/bin/bash
set -euo pipefail

echo "🤖 Fix It Fred DevOps VM Setup Starting..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user requests watchdog asyncio

# Setup log directory
echo "📝 Setting up logging..."
sudo mkdir -p /var/log
sudo touch /var/log/fix-it-fred-devops.log
sudo chown '"$SERVICE_USER"':'"$SERVICE_USER"' /var/log/fix-it-fred-devops.log

# Install systemd service
echo "🔧 Installing systemd service..."
sudo cp /tmp/fix-it-fred-devops.service /etc/systemd/system/
sudo systemctl daemon-reload

# Set proper permissions
echo "🔒 Setting up permissions..."
cd '"$REPO_PATH"'
chmod +x fix_it_fred_devops_daemon.py

# Enable and start service
echo "🚀 Starting Fix It Fred DevOps service..."
sudo systemctl enable '"$SERVICE_NAME"'.service

# Stop service if running (for clean restart)
if systemctl is-active '"$SERVICE_NAME"'.service >/dev/null 2>&1; then
    echo "🔄 Stopping existing service for clean restart..."
    sudo systemctl stop '"$SERVICE_NAME"'.service
    sleep 5
fi

# Start the service
sudo systemctl start '"$SERVICE_NAME"'.service

# Wait and check status
echo "⏳ Waiting for service to initialize..."
sleep 10

if systemctl is-active '"$SERVICE_NAME"'.service >/dev/null 2>&1; then
    echo "✅ Fix It Fred DevOps service is running!"
    
    # Show service status
    echo "📊 Service Status:"
    sudo systemctl status '"$SERVICE_NAME"'.service --no-pager -l
    
    echo ""
    echo "📝 Recent logs:"
    sudo journalctl -u '"$SERVICE_NAME"'.service --no-pager -n 10
else
    echo "❌ Fix It Fred DevOps service failed to start"
    echo "📝 Error logs:"
    sudo journalctl -u '"$SERVICE_NAME"'.service --no-pager -n 20
    exit 1
fi

echo ""
echo "🎉 Fix It Fred DevOps Setup Complete!"
echo "===================================="
echo ""
echo "🚀 AUTONOMOUS CAPABILITIES ENABLED:"
echo "  ✅ Continuous health monitoring (every 60 seconds)"
echo "  ✅ Automatic service healing"
echo "  ✅ Git repository monitoring (every 5 minutes)"
echo "  ✅ Autonomous deployment on code changes"
echo "  ✅ System resource management"
echo "  ✅ Log rotation and cleanup"
echo ""
echo "🔧 SERVICE MANAGEMENT:"
echo "  • Start:   sudo systemctl start '"$SERVICE_NAME"'"
echo "  • Stop:    sudo systemctl stop '"$SERVICE_NAME"'"
echo "  • Status:  sudo systemctl status '"$SERVICE_NAME"'"
echo "  • Logs:    sudo journalctl -u '"$SERVICE_NAME"' -f"
echo "  • Health:  sudo systemctl kill --signal=SIGUSR1 '"$SERVICE_NAME"'"
echo ""
echo "🤖 Fix It Fred is now autonomously managing your VM!"
'

# Execute setup on VM
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="$SETUP_SCRIPT"

# Verify deployment
echo ""
echo "🔍 Final verification..."
VERIFY_SCRIPT='
echo "🔍 Verifying Fix It Fred DevOps deployment..."

# Check service status
if systemctl is-active '"$SERVICE_NAME"'.service >/dev/null 2>&1; then
    echo "✅ Service is active"
    
    # Trigger immediate health check
    echo "🩺 Triggering health check..."
    sudo systemctl kill --signal=SIGUSR1 '"$SERVICE_NAME"'.service
    
    # Wait and show recent activity
    sleep 5
    echo "📝 Recent activity:"
    sudo journalctl -u '"$SERVICE_NAME"'.service --no-pager -n 5
    
    echo ""
    echo "🎯 DEPLOYMENT SUCCESSFUL!"
    echo "Fix It Fred DevOps is now running autonomously"
else
    echo "❌ Service verification failed"
    sudo systemctl status '"$SERVICE_NAME"'.service --no-pager
fi
'

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="$VERIFY_SCRIPT"

echo ""
echo "🎉 FIX IT FRED DEVOPS PRODUCTION SETUP COMPLETE!"
echo "==============================================="
echo ""
echo "🚀 AUTONOMOUS SYSTEM ACTIVE:"
echo "  ✅ Health monitoring and auto-healing"
echo "  ✅ Continuous deployment detection"
echo "  ✅ Service management and recovery"
echo "  ✅ System resource optimization"
echo ""
echo "📊 MONITORING:"
echo "  • VM Console: https://console.cloud.google.com/compute/instances"
echo "  • Service Logs: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo journalctl -u $SERVICE_NAME -f'"
echo "  • Health Check: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo systemctl kill --signal=SIGUSR1 $SERVICE_NAME'"
echo ""
echo "🔄 GITHUB ACTIONS:"
echo "  • Workflow will now auto-deploy on push to main-clean"
echo "  • Health checks run before every deployment"
echo "  • Manual deployment: GitHub Actions > Fix It Fred Auto-Deploy"
echo ""
echo "🤖 Fix It Fred is now your autonomous DevOps assistant!"