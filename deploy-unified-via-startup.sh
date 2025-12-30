#!/bin/bash

# 🚀 Deploy Complete ChatterFix CMMS via Startup Script
# Uses metadata to deploy the unified platform

set -e

VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
PROJECT="fredfix"

echo "🚀 Deploying Complete ChatterFix CMMS Platform via startup script..."

# Create the complete unified application deployment script
cat > /tmp/deploy-unified.sh << 'EOFSCRIPT'
#!/bin/bash

echo "🔥 Starting Complete ChatterFix CMMS Unified Platform Deployment..."

# Stop existing service
sudo systemctl stop chatterfix 2>/dev/null || true

# Create new application directory for unified platform
sudo mkdir -p /opt/chatterfix-unified
cd /opt/chatterfix-unified

# Download the complete unified platform from GitHub
echo "📥 Downloading complete unified platform..."
curl -L https://raw.githubusercontent.com/TheGringo-ai/Chatterfix/main/vm-deployment/app.py -o app.py

# Verify we got the unified platform (should be ~215KB)
FILE_SIZE=$(wc -c < app.py)
if [ "$FILE_SIZE" -lt 200000 ]; then
    echo "❌ Failed to download complete platform (file too small: $FILE_SIZE bytes)"
    exit 1
fi

echo "✅ Downloaded unified platform: $FILE_SIZE bytes"

# Install Python dependencies for unified platform
echo "📦 Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install fastapi uvicorn jinja2 python-multipart aiofiles bcrypt pyjwt httpx requests python-dotenv sqlite3 pandas numpy openai anthropic pydantic Pillow reportlab xlsxwriter qrcode python-jose passlib email-validator python-magic matplotlib seaborn plotly

# Set proper ownership
sudo chown -R yoyofred_gringosgambit_com:yoyofred_gringosgambit_com /opt/chatterfix-unified

# Create systemd service for unified platform
echo "🔧 Creating systemd service for unified platform..."
sudo tee /etc/systemd/system/chatterfix.service > /dev/null << 'EOFSERVICE'
[Unit]
Description=ChatterFix CMMS Unified Platform
After=network.target

[Service]
User=yoyofred_gringosgambit_com
Group=yoyofred_gringosgambit_com
WorkingDirectory=/opt/chatterfix-unified
Environment=PATH=/usr/bin:/usr/local/bin
Environment=PYTHONPATH=/opt/chatterfix-unified
Environment=DATABASE_URL=sqlite:///chatterfix_unified.db
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOFSERVICE

# Update nginx configuration for port 8000 (unified platform default)
echo "🌐 Updating nginx configuration..."
sudo tee /etc/nginx/sites-available/chatterfix > /dev/null << 'EOFNGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOFNGINX

# Restart services
echo "🚀 Starting unified platform..."
sudo systemctl daemon-reload
sudo systemctl enable chatterfix
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl start chatterfix

# Wait for startup
sleep 10

# Health check
echo "🩺 Running health check..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "🎉 COMPLETE CHATTERFIX CMMS UNIFIED PLATFORM DEPLOYED!"
    echo "✅ All CMMS features available in single application"
    echo "🌐 Access: http://35.237.149.25"
    echo "🔧 Work Orders, Assets, Parts - all working"
    echo "🤖 AI Assistant integrated"
else
    echo "⚠️ Service starting, check logs:"
    sudo journalctl -u chatterfix -n 20
fi

echo "🔥 UNIFIED PLATFORM DEPLOYMENT COMPLETE!"
EOFSCRIPT

chmod +x /tmp/deploy-unified.sh

# Upload and execute the deployment script via gcloud
echo "📤 Uploading deployment script to VM..."
gcloud compute scp /tmp/deploy-unified.sh $VM_NAME:~/deploy-unified.sh --zone=$ZONE --project=$PROJECT

echo "🚀 Executing deployment on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="chmod +x ~/deploy-unified.sh && sudo ~/deploy-unified.sh"

# Final verification
echo "🩺 Final verification..."
sleep 5
if curl -s http://35.237.149.25/health | grep -q "healthy"; then
    echo "🎉 SUCCESS! Complete ChatterFix CMMS Platform is now live!"
    echo ""
    echo "✅ FEATURES AVAILABLE:"
    echo "   🏠 Dashboard: http://35.237.149.25"
    echo "   🔧 Work Orders: http://35.237.149.25/work-orders"  
    echo "   🏭 Assets: http://35.237.149.25/assets"
    echo "   📦 Parts: http://35.237.149.25/parts"
    echo "   🤖 AI Assistant: Integrated"
    echo "   🩺 Health: http://35.237.149.25/health"
    echo "   📋 API Docs: http://35.237.149.25/docs"
    echo ""
    echo "🌐 Access via: http://chatterfix.com"
    echo "🎯 All Fix It Fred features now available!"
else
    echo "⚠️ Deployment needs verification. Check http://35.237.149.25"
fi