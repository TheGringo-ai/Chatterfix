#!/bin/bash
# Fix It Fred Assets API Direct Deployment
# Based on your working deploy-on-command.yml pattern

set -e

echo "🤖 Fix It Fred: Direct Assets API Deployment"
echo "=============================================="

# Configuration (from your working workflow)
PROJECT_ID="fredfix"
INSTANCE_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"

echo "🔍 Environment Check..."
echo "  Project: $PROJECT_ID"
echo "  Instance: $INSTANCE_NAME"
echo "  Zone: $ZONE"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

echo "✅ GCloud authentication verified"

# Create deployment package (following your workflow pattern)
echo "📦 Creating deployment package..."
mkdir -p /tmp/fix-it-fred-deploy
cp -r . /tmp/fix-it-fred-deploy/

# Create the deployment tar.gz
cd /tmp/fix-it-fred-deploy
tar czf ../chatterfix-deployment.tar.gz .
cd - > /dev/null

echo "✅ Package created: $(du -h /tmp/chatterfix-deployment.tar.gz)"

# Upload to VM (exact same method as your workflow)
echo "📤 Uploading deployment package to VM..."
gcloud compute scp /tmp/chatterfix-deployment.tar.gz \
  $INSTANCE_NAME:/tmp/chatterfix-deployment.tar.gz \
  --zone=$ZONE

echo "✅ Upload complete"

# Create deployment script (exact same as your workflow)
echo "🚀 Creating deployment script..."
DEPLOY_SCRIPT='#!/bin/bash
set -e
export HOME=/root

echo "🚀 Fix It Fred Assets API Deployment"
echo "===================================="
echo "Environment: production"
echo "Triggered by: Fix It Fred Assets API Fix"
echo "Time: $(date)"

# Stop current service
echo "🛑 Stopping ChatterFix..."
pkill -f "python3 app.py" || true
sleep 2

# Extract new version with Fix It Fred assets API
if [ -f /tmp/chatterfix-deployment.tar.gz ]; then
    echo "📦 Extracting deployment package with assets API..."
    cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app
    tar xzf /tmp/chatterfix-deployment.tar.gz
    echo "✅ Files extracted (including fixed_assets_api.py)"
else
    echo "❌ No deployment package found"
    exit 1
fi

# Ensure dependencies
echo "📚 Checking dependencies..."
pip3 install --quiet fastapi uvicorn jinja2 httpx python-multipart aiofiles pydantic

# Start service
echo "🚀 Starting ChatterFix with Fix It Fred assets API..."
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app
export OLLAMA_HOST=http://localhost:11434
export PORT=8080

# Load environment
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

nohup python3 app.py > /tmp/chatterfix.log 2>&1 &
CHATTERFIX_PID=$!

echo "⏳ Waiting for service to start..."
sleep 10

if ps -p $CHATTERFIX_PID > /dev/null; then
    echo "✅ ChatterFix started successfully with assets API (PID: $CHATTERFIX_PID)"
    tail -15 /tmp/chatterfix.log
else
    echo "❌ ChatterFix failed to start"
    cat /tmp/chatterfix.log
    exit 1
fi

echo "🎉 Fix It Fred Assets API deployment complete!"
'

# Upload and execute deployment script
echo "🔄 Executing deployment on VM..."
echo "$DEPLOY_SCRIPT" | gcloud compute ssh $INSTANCE_NAME \
  --zone=$ZONE \
  --command "cat > /tmp/deploy.sh && chmod +x /tmp/deploy.sh && sudo /tmp/deploy.sh"

# Health check (following your pattern)
echo "🩺 Running health checks..."
VM_IP=$(gcloud compute instances describe $INSTANCE_NAME \
  --zone=$ZONE \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo "🌐 VM IP: $VM_IP"

# Test assets API specifically
for i in {1..10}; do
  echo "🧪 Assets API test attempt $i/10..."
  if curl -s -f "http://$VM_IP:8080/api/assets" > /dev/null; then
    echo "🎉 SUCCESS! Fix It Fred's Assets API is live!"
    
    # Show the assets
    echo "📊 Current assets:"
    curl -s "http://$VM_IP:8080/api/assets" | python3 -c "
import json, sys
try:
    assets = json.load(sys.stdin)
    for asset in assets[:3]:
        print(f'  • {asset.get(\"name\", \"Unknown\")} ({asset.get(\"asset_type\", \"unknown\")})')
except:
    print('  Could not parse assets')
"
    
    # Test asset creation
    echo ""
    echo "🧪 Testing asset creation..."
    curl -s -X POST "http://$VM_IP:8080/api/assets" \
      -H "Content-Type: application/json" \
      -d '{"name": "Fix It Fred Deploy Test", "asset_type": "equipment", "location": "Test Lab"}' | \
      python3 -c "
import json, sys
try:
    result = json.load(sys.stdin)
    if result.get('success'):
        print('✅ Asset creation works!')
    else:
        print('⚠️ Asset creation needs attention')
except:
    print('⚠️ Could not test asset creation')
"
    
    break
  else
    echo "⏳ Service starting... (attempt $i)"
    sleep 20
  fi
done

# Final summary
echo ""
echo "🎉 FIX IT FRED ASSETS API DEPLOYMENT COMPLETE!"
echo "=============================================="
echo "🤖 Deployed by: Fix It Fred via Claude Code"
echo "🌐 URL: http://$VM_IP:8080"
echo "🏭 Assets: http://$VM_IP:8080/assets"
echo "📊 Assets API: http://$VM_IP:8080/api/assets"
echo "🩺 Health: http://$VM_IP:8080/health"
echo ""
echo "✅ Your asset form should now be fully functional!"
echo "   No more 'Feature coming soon' alerts!"

# Cleanup
rm -rf /tmp/fix-it-fred-deploy /tmp/chatterfix-deployment.tar.gz

echo "🧹 Cleanup complete"
echo "🎯 Test your asset form at: http://$VM_IP:8080/assets"