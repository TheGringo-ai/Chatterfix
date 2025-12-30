#!/bin/bash

echo "🚀 Deploying ChatterFix AI-Enhanced CMMS to Production Server"
echo "=============================================="

# Server details
SERVER="chatterfix-prod"
SERVER_IP="35.237.149.25"
DEPLOY_DIR="/home/yoyofred_gringosgambit_com/chatterfix-cmms"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📦 Preparing deployment package...${NC}"

# Create deployment package
tar -czf chatterfix-ai-enhanced.tar.gz \
    app.py \
    ai_enhanced.py \
    ai.py \
    admin.py \
    assets.py \
    dashboard.py \
    navigation_component.py \
    part.py \
    prevenative.py \
    technician.py \
    workorders.py \
    requirements.txt 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to create deployment package${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment package created${NC}"

# Copy to server
echo -e "${YELLOW}📤 Copying files to server...${NC}"
scp chatterfix-ai-enhanced.tar.gz $SERVER:~/

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to copy files to server${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Files copied to server${NC}"

# Deploy on server
echo -e "${YELLOW}🔧 Deploying on server...${NC}"

ssh $SERVER << 'ENDSSH'
    set -e
    
    # Colors
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'
    
    echo -e "${YELLOW}📁 Setting up deployment directory...${NC}"
    
    # Create directory if not exists
    mkdir -p /home/yoyofred_gringosgambit_com/chatterfix-cmms
    cd /home/yoyofred_gringosgambit_com/chatterfix-cmms
    
    # Backup existing deployment
    if [ -d "backup" ]; then
        rm -rf backup.old
        mv backup backup.old
    fi
    mkdir -p backup
    cp -r *.py backup/ 2>/dev/null || true
    
    # Extract new files
    echo -e "${YELLOW}📦 Extracting deployment package...${NC}"
    tar -xzf ~/chatterfix-ai-enhanced.tar.gz
    
    # Install/update requirements
    echo -e "${YELLOW}📚 Installing Python dependencies...${NC}"
    pip3 install --user httpx websockets
    
    # Check if service exists
    if systemctl --user list-units --all | grep -q chatterfix-cmms.service; then
        echo -e "${YELLOW}🔄 Restarting ChatterFix CMMS service...${NC}"
        systemctl --user restart chatterfix-cmms
    else
        echo -e "${YELLOW}🆕 Creating systemd service...${NC}"
        
        # Create systemd service file
        cat > ~/.config/systemd/user/chatterfix-cmms.service << 'EOF'
[Unit]
Description=ChatterFix AI-Enhanced CMMS
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/yoyofred_gringosgambit_com/chatterfix-cmms
ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
Restart=always
RestartSec=10
Environment="PATH=/home/yoyofred_gringosgambit_com/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=default.target
EOF
        
        # Enable and start service
        systemctl --user daemon-reload
        systemctl --user enable chatterfix-cmms
        systemctl --user start chatterfix-cmms
    fi
    
    # Wait for service to start
    sleep 3
    
    # Check service status
    if systemctl --user is-active --quiet chatterfix-cmms; then
        echo -e "${GREEN}✅ ChatterFix CMMS service is running${NC}"
    else
        echo -e "${RED}❌ Service failed to start${NC}"
        systemctl --user status chatterfix-cmms
        exit 1
    fi
    
    # Test endpoints
    echo -e "${YELLOW}🧪 Testing AI endpoints...${NC}"
    
    # Test main endpoint
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200"; then
        echo -e "${GREEN}✅ Main endpoint responding${NC}"
    else
        echo -e "${RED}❌ Main endpoint not responding${NC}"
    fi
    
    # Test AI enhanced endpoint
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ai-enhanced/dashboard/universal | grep -q "200"; then
        echo -e "${GREEN}✅ AI Enhanced endpoint responding${NC}"
    else
        echo -e "${YELLOW}⚠️  AI Enhanced endpoint not yet ready${NC}"
    fi
    
    # Check Ollama connection
    echo -e "${YELLOW}🤖 Checking Llama AI connection...${NC}"
    if curl -s http://35.237.149.25:11434/api/tags | grep -q "llama"; then
        echo -e "${GREEN}✅ Llama AI server connected${NC}"
    else
        echo -e "${YELLOW}⚠️  Llama AI server not responding on port 11434${NC}"
    fi
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo "Access your AI-Enhanced CMMS at:"
    echo "  http://35.237.149.25:8000"
    echo ""
    echo "AI Features available at:"
    echo "  http://35.237.149.25:8000/ai-enhanced/dashboard/universal"
    echo ""
    echo "AI Assistant will appear as a floating button (🤖) on all pages"
ENDSSH

# Cleanup
rm -f chatterfix-ai-enhanced.tar.gz

echo -e "${GREEN}✨ ChatterFix AI-Enhanced CMMS deployed successfully!${NC}"
echo ""
echo "🌐 Access your platform at: http://$SERVER_IP:8000"
echo "🤖 AI Assistant available on all pages"
echo "🎤 Voice commands enabled"
echo "📷 OCR scanning ready"
echo "📊 PM planning board integrated"
echo ""
echo "To view logs: ssh $SERVER 'journalctl --user -u chatterfix-cmms -f'"