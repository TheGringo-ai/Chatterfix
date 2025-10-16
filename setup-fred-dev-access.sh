#!/bin/bash

echo "🤖 Setting up Fix It Fred Development Hooks"
echo "==========================================="

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

echo "✅ gcloud authentication verified"

# Set up environment variables
export PROJECT_ID="fredfix"
export ZONE="us-east1-b"
export INSTANCE_NAME="chatterfix-cmms-production"
export SERVICE_ACCOUNT="github-actions@fredfix.iam.gserviceaccount.com"

echo "🔧 Configuring Fix It Fred with enhanced VM permissions..."

# Grant additional permissions for development operations
echo "🔐 Adding development permissions to service account..."

# Add roles for comprehensive VM management
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/compute.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/logging.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/monitoring.admin"

echo "✅ Enhanced permissions granted"

# Install required Python packages
echo "📦 Installing required Python packages..."
pip3 install --user google-cloud-compute google-auth requests

# Create Fred's working directory
echo "📁 Setting up Fred's working directory..."
mkdir -p ~/.fix_it_fred
chmod 700 ~/.fix_it_fred

# Set up Fred's SSH configuration for VM access
echo "🔑 Configuring SSH access for Fred..."
gcloud compute instances add-metadata $INSTANCE_NAME \
  --zone=$ZONE \
  --metadata enable-oslogin=TRUE

# Test VM connection
echo "🧪 Testing VM connection..."
VM_IP=$(gcloud compute instances describe $INSTANCE_NAME \
  --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo "🌐 VM External IP: $VM_IP"

# Test SSH connection
if gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="echo 'Fred connection test successful'" --quiet; then
    echo "✅ SSH connection test passed"
else
    echo "⚠️ SSH connection test failed - this may require manual setup"
fi

# Create Fred's startup script on VM
echo "🚀 Setting up Fred's runtime environment on VM..."

FRED_SETUP_SCRIPT='#!/bin/bash
echo "🤖 Setting up Fix It Fred runtime environment..."

# Create Fred'"'"'s working directory on VM
sudo mkdir -p /opt/fix-it-fred
sudo chown '"$USER"':'"$USER"' /opt/fix-it-fred

# Install required packages on VM
sudo apt-get update -qq
sudo apt-get install -y python3-pip git curl

# Install Python packages for Fred'"'"'s operations
pip3 install --user fastapi uvicorn watchdog requests psutil

# Create Fred'"'"'s service management script
cat > /opt/fix-it-fred/service-manager.sh << '\''EOF'\''
#!/bin/bash
case "$1" in
    restart-all)
        echo "🔄 Restarting all ChatterFix services..."
        sudo systemctl restart chatterfix-cmms
        sudo systemctl restart nginx
        sudo systemctl restart fix-it-fred-git 2>/dev/null || echo "Git service not found"
        ;;
    status-all)
        echo "📊 Service Status Report:"
        echo "========================"
        for service in chatterfix-cmms nginx fix-it-fred-git; do
            status=$(sudo systemctl is-active $service 2>/dev/null || echo "not-found")
            echo "$service: $status"
        done
        ;;
    health-check)
        echo "🏥 Health Check Report:"
        echo "======================"
        curl -s http://localhost:8080/health || echo "Main app: DOWN"
        curl -s http://localhost:9002/health || echo "Git service: DOWN"
        ;;
    *)
        echo "Usage: $0 {restart-all|status-all|health-check}"
        exit 1
        ;;
esac
EOF

chmod +x /opt/fix-it-fred/service-manager.sh

# Set up Fred'"'"'s auto-deployment hooks
cat > /opt/fix-it-fred/auto-deploy.sh << '\''EOF'\''
#!/bin/bash
echo "🚀 Fix It Fred Auto-Deployment Starting..."

cd /home/yoyofred_gringosgambit_com/chatterfix-docker || exit 1

# Git operations
git add .
git commit -m "🤖 Fix It Fred: Automated deployment $(date)"

# Restart services
/opt/fix-it-fred/service-manager.sh restart-all

# Health check
sleep 10
/opt/fix-it-fred/service-manager.sh health-check

echo "✅ Auto-deployment completed"
EOF

chmod +x /opt/fix-it-fred/auto-deploy.sh

echo "✅ Fix It Fred runtime environment ready"
'

# Execute the setup script on VM
echo "$FRED_SETUP_SCRIPT" | gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="cat > /tmp/fred_setup.sh && chmod +x /tmp/fred_setup.sh && /tmp/fred_setup.sh"

# Create local Fred configuration
echo "📝 Creating Fix It Fred configuration..."
cat > ~/.fix_it_fred/config.json << EOF
{
  "project_id": "$PROJECT_ID",
  "zone": "$ZONE",
  "instance_name": "$INSTANCE_NAME",
  "vm_ip": "$VM_IP",
  "vm_user": "yoyofred_gringosgambit_com",
  "repo_path": "/home/yoyofred_gringosgambit_com/chatterfix-docker",
  "services": [
    "chatterfix-cmms",
    "nginx",
    "fix-it-fred-git"
  ],
  "auto_healing": true,
  "auto_deployment": true,
  "git_auto_commit": true
}
EOF

echo "🎉 Fix It Fred Development Hooks Setup Complete!"
echo ""
echo "✅ CAPABILITIES ENABLED:"
echo "  🔧 Direct VM command execution"
echo "  🚀 Autonomous code deployment"
echo "  ✏️ Live file editing on VM"
echo "  🔄 Service restart management"
echo "  🩺 Auto-healing monitoring"
echo "  📚 Git operations automation"
echo "  💾 Automatic backups"
echo ""
echo "🚀 NEXT STEPS:"
echo "  1. Run: python3 fix_it_fred_dev_hooks.py"
echo "  2. Test with: fred.execute_vm_command('uptime', 'Test command')"
echo "  3. Deploy code: fred.deploy_code_to_vm('local_file.py', '/remote/path.py')"
echo "  4. Live edit: fred.live_code_edit('/path/to/file.py', old_content, new_content)"
echo ""
echo "🤖 Fix It Fred is now ready for autonomous development!"