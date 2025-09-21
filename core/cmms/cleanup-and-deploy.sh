#!/bin/bash

echo "🧹 ChatterFix Process Cleanup and Universal AI Deployment..."

# Kill all duplicate python/uvicorn processes
echo "🛑 Stopping all duplicate processes..."
sudo pkill -f "python.*app.py" || true
sudo pkill -f "uvicorn" || true
sleep 3

# Stop systemd service
echo "🛑 Stopping systemd service..."
sudo systemctl stop chatterfix-cmms 2>/dev/null || true

# Navigate to correct directory
cd /opt/chatterfix-cmms/core/cmms || {
    echo "❌ Could not find CMMS directory"
    exit 1
}

# Update to latest code
echo "📥 Pulling latest code..."
git fetch origin
git reset --hard origin/main

# Run comprehensive deployment
echo "🚀 Running Universal AI deployment..."
chmod +x deploy-universal-ai.sh
./deploy-universal-ai.sh

# Verify only one instance is running
echo "🔍 Verifying single instance..."
PROCESS_COUNT=$(pgrep -f "python.*app.py" | wc -l)
echo "Running Python processes: $PROCESS_COUNT"

if [ "$PROCESS_COUNT" -eq 1 ]; then
    echo "✅ Single instance confirmed!"
else
    echo "⚠️ Multiple instances detected: $PROCESS_COUNT"
fi

echo "🎉 Cleanup and deployment complete!"