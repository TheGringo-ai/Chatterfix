#!/bin/bash

# ChatterFix CMMS Production Deployment Script
# Deploys the complete CMMS application to production VM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ChatterFix CMMS Production Deployment${NC}"
echo "================================================"

# Configuration
VM_HOST="chatterfix-prod"
REMOTE_DIR="/opt/chatterfix-cmms"
SERVICE_NAME="chatterfix-cmms"

echo -e "${YELLOW}📋 Step 1: Stopping existing services...${NC}"
ssh $VM_HOST "
sudo systemctl stop $SERVICE_NAME || echo 'Service not running'
sudo pkill -f 'uvicorn.*app:app' || echo 'No uvicorn processes'
sudo pkill -f 'python.*cmms' || echo 'No CMMS processes'
sudo pkill -f 'streamlit.*technician' || echo 'No streamlit processes'
"

echo -e "${YELLOW}📦 Step 2: Creating deployment package...${NC}"
# Create temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "Created temp directory: $TEMP_DIR"

# Copy all necessary files
cp -r . $TEMP_DIR/cmms/
cd $TEMP_DIR

# Remove unnecessary files
rm -rf cmms/__pycache__
rm -rf cmms/.git
rm -rf cmms/ai-memory
rm -rf cmms/exports
rm -rf cmms/uploads
find cmms/ -name "*.pyc" -delete
find cmms/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Create archive
tar -czf cmms-deployment.tar.gz cmms/
echo "Package created: $(ls -lh cmms-deployment.tar.gz)"

echo -e "${YELLOW}🚁 Step 3: Uploading to VM...${NC}"
scp cmms-deployment.tar.gz $VM_HOST:/tmp/

echo -e "${YELLOW}📂 Step 4: Installing on VM...${NC}"
ssh $VM_HOST "
# Create application directory
sudo mkdir -p $REMOTE_DIR
sudo rm -rf $REMOTE_DIR/core
cd /tmp
tar -xzf cmms-deployment.tar.gz
sudo mv cmms/* $REMOTE_DIR/
sudo chown -R \$USER:\$USER $REMOTE_DIR
rm -f cmms-deployment.tar.gz
rm -rf cmms/

# Go to the application directory
cd $REMOTE_DIR/core/cmms

# Create virtual environment if it doesn't exist
if [ ! -d 'venv' ]; then
    echo 'Creating Python virtual environment...'
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate

# Install requirements
if [ -f 'requirements.txt' ]; then
    pip install -r requirements.txt
else
    # Install basic requirements
    pip install fastapi uvicorn aiohttp pydantic
fi

# Ensure all required modules are available
pip install python-multipart jinja2 python-jose[cryptography] passlib[bcrypt] || true
"

echo -e "${YELLOW}⚙️ Step 5: Creating systemd service...${NC}"
ssh $VM_HOST "
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=ChatterFix CMMS Application
After=network.target

[Service]
Type=simple
User=\$USER
Group=\$USER
WorkingDirectory=$REMOTE_DIR/core/cmms
Environment=PATH=$REMOTE_DIR/core/cmms/venv/bin
ExecStart=$REMOTE_DIR/core/cmms/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
"

echo -e "${YELLOW}🌐 Step 6: Configuring Nginx for HTTPS...${NC}"
ssh $VM_HOST "
# Create Nginx configuration for HTTPS
sudo tee /etc/nginx/sites-available/chatterfix-cmms > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name chatterfix.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/chatterfix.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chatterfix.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection \"1; mode=block\";
    add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;

    # CMMS Application
    location /cmms/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
    }

    # Root redirect to CMMS
    location = / {
        return 301 /cmms/dashboard/main;
    }

    # Static files
    location /static/ {
        alias $REMOTE_DIR/core/cmms/static/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name chatterfix.com;
    return 301 https://\$server_name\$request_uri;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/chatterfix-cmms /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
"

echo -e "${YELLOW}🚀 Step 7: Starting services...${NC}"
ssh $VM_HOST "
cd $REMOTE_DIR/core/cmms
sudo systemctl start $SERVICE_NAME
sleep 3
sudo systemctl status $SERVICE_NAME --no-pager -l
"

echo -e "${YELLOW}🔍 Step 8: Health checks...${NC}"
ssh $VM_HOST "
echo 'Checking application health...'
curl -f http://localhost:8000/dashboard/main > /dev/null 2>&1 && echo '✅ App responding on port 8000' || echo '❌ App not responding'
curl -f http://localhost:8000/cmms/workorders/dashboard > /dev/null 2>&1 && echo '✅ Work orders dashboard accessible' || echo '❌ Work orders dashboard not accessible'

echo 'Checking Nginx configuration...'
sudo nginx -t && echo '✅ Nginx config valid' || echo '❌ Nginx config invalid'
"

# Cleanup
cd /
rm -rf $TEMP_DIR

echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo "🌐 Access your CMMS at:"
echo "   • https://chatterfix.com/cmms/dashboard/main"
echo "   • https://chatterfix.com/cmms/workorders/dashboard"
echo ""
echo "📋 Service management:"
echo "   • Status: ssh $VM_HOST 'sudo systemctl status $SERVICE_NAME'"
echo "   • Logs:   ssh $VM_HOST 'sudo journalctl -u $SERVICE_NAME -f'"
echo "   • Stop:   ssh $VM_HOST 'sudo systemctl stop $SERVICE_NAME'"
echo "   • Start:  ssh $VM_HOST 'sudo systemctl start $SERVICE_NAME'"