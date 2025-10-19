#!/bin/bash
# Quick Fix It Fred Assets API Deployment - Essential Files Only

set -e

echo "🚀 Fix It Fred: Quick Assets API Fix"
echo "====================================="

# Configuration
PROJECT_ID="fredfix"
INSTANCE_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"

echo "📦 Creating minimal deployment package..."

# Create temporary directory with only essential files
mkdir -p /tmp/fred-quick-deploy

# Copy only the essential files
cp app.py /tmp/fred-quick-deploy/ 2>/dev/null || echo "app.py not found, continuing..."
cp fixed_assets_api.py /tmp/fred-quick-deploy/
cp *.py /tmp/fred-quick-deploy/ 2>/dev/null || true

# Copy templates if they exist
if [ -d templates ]; then
    cp -r templates /tmp/fred-quick-deploy/
fi

# Copy static files if they exist
if [ -d static ]; then
    cp -r static /tmp/fred-quick-deploy/
fi

cd /tmp/fred-quick-deploy
tar czf ../fred-assets-fix.tar.gz .
cd - > /dev/null

echo "✅ Quick package created: $(du -h /tmp/fred-assets-fix.tar.gz)"

# Upload directly
echo "📤 Quick upload to VM..."
gcloud compute scp /tmp/fred-assets-fix.tar.gz \
  $INSTANCE_NAME:/tmp/fred-assets-fix.tar.gz \
  --zone=$ZONE

echo "🔧 Quick deployment..."

# Simple deployment script
QUICK_DEPLOY='#!/bin/bash
echo "🚀 Fix It Fred Quick Assets API Fix"
echo "Extracting assets API fix..."

cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Backup current
cp app.py app_backup_$(date +%Y%m%d_%H%M%S).py 2>/dev/null || true

# Extract new files
tar xzf /tmp/fred-assets-fix.tar.gz

echo "✅ Assets API files updated"

# Restart service
echo "🔄 Restarting ChatterFix..."
pkill -f "python3 app.py" || true
sleep 3

export OLLAMA_HOST=http://localhost:11434
export PORT=8080
nohup python3 app.py > /tmp/chatterfix.log 2>&1 &

echo "⏳ Waiting for restart..."
sleep 5

if pgrep -f "python3 app.py" > /dev/null; then
    echo "✅ ChatterFix restarted with assets API"
else
    echo "⚠️ Service may still be starting"
fi

echo "🎉 Quick fix complete!"
'

# Execute quick deployment
echo "$QUICK_DEPLOY" | gcloud compute ssh $INSTANCE_NAME \
  --zone=$ZONE \
  --command "cat > /tmp/quick-deploy.sh && chmod +x /tmp/quick-deploy.sh && sudo /tmp/quick-deploy.sh"

# Quick test
echo "🧪 Quick test..."
sleep 10

VM_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

if curl -s "http://$VM_IP:8080/api/assets" | grep -q "id\|name"; then
    echo "🎉 SUCCESS! Assets API is working!"
    curl -s "http://$VM_IP:8080/api/assets" | head -3
else
    echo "⏳ Assets API may still be loading..."
    curl -s "http://$VM_IP:8080/health" || echo "Service still starting..."
fi

# Cleanup
rm -rf /tmp/fred-quick-deploy /tmp/fred-assets-fix.tar.gz

echo "🎯 Test your assets at: http://$VM_IP:8080/assets"