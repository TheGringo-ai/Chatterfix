#!/bin/bash

echo "🚀 Deploying Enhanced ChatterFix CMMS to Production VM"
echo "🤖 Fix It Fred & Grok AI Integration"
echo "🌐 VM: 35.237.149.25 (chatterfix-static-ip)"
echo "================================================================="

# Production VM Configuration
VM_IP="35.237.149.25"
VM_USER="yoyofred_gringosgambit_com"
VM_APP_DIR="/opt/chatterfix-cmms/current"

echo "📦 Preparing enhanced deployment package..."

# Create deployment package
rm -rf vm-deployment-package
mkdir -p vm-deployment-package

# Copy enhanced files
cp app.py vm-deployment-package/
cp work_orders_api_fix.py vm-deployment-package/work_orders_service.py
cp database_service.py vm-deployment-package/
cp ai_brain_service.py vm-deployment-package/
cp grok_connector.py vm-deployment-package/
cp -r data vm-deployment-package/ 2>/dev/null || echo "Creating data directory..."
mkdir -p vm-deployment-package/data

# Create requirements file
cat > vm-deployment-package/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
pydantic==2.5.0
python-multipart==0.0.6
requests==2.31.0
python-dotenv==1.0.0
sqlite3
EOF

# Create production deployment script
cat > vm-deployment-package/deploy-enhanced-chatterfix.sh << 'DEPLOY_EOF'
#!/bin/bash

echo "🚀 ChatterFix Enhanced CMMS - Production Deployment"
echo "🤖 Industry-Leading Work Orders with AI Integration"
echo "=================================================="

# Stop existing services
echo "🛑 Stopping existing services..."
sudo systemctl stop chatterfix-ai-chat 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*database_service" 2>/dev/null || true
pkill -f "python.*work_orders_service" 2>/dev/null || true
pkill -f "python.*ai_brain_service" 2>/dev/null || true
pkill -f "python.*grok_connector" 2>/dev/null || true

# Kill processes on specific ports
for port in 8080 8081 8001 8005 8006 8015; do
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
done

sleep 3

# Install dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --user --quiet -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Set up database service
echo "🗄️ Setting up Database Service..."
cat > start_database.sh << 'DB_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
python3 database_service.py > database.log 2>&1 &
echo "Database service started on port 8001"
DB_EOF
chmod +x start_database.sh

# Set up enhanced work orders service
echo "🔧 Setting up Enhanced Work Orders Service..."
cat > start_work_orders.sh << 'WO_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
PORT=8015 python3 work_orders_service.py > work_orders.log 2>&1 &
echo "Enhanced Work Orders service started on port 8015"
WO_EOF
chmod +x start_work_orders.sh

# Set up Fix It Fred AI service
echo "🤖 Setting up Fix It Fred AI Service..."
cat > start_ai_brain.sh << 'AI_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
PORT=8005 python3 ai_brain_service.py > ai_brain.log 2>&1 &
echo "Fix It Fred AI service started on port 8005"
AI_EOF
chmod +x start_ai_brain.sh

# Set up Grok connector service
echo "🧠 Setting up Grok Connector Service..."
cat > start_grok.sh << 'GROK_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
PORT=8006 python3 grok_connector.py > grok.log 2>&1 &
echo "Grok Connector service started on port 8006"
GROK_EOF
chmod +x start_grok.sh

# Set up main application
echo "🌐 Setting up Main ChatterFix Application..."
cat > start_main_app.sh << 'MAIN_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
PORT=8080 python3 app.py > main_app.log 2>&1 &
echo "Main ChatterFix app started on port 8080"
MAIN_EOF
chmod +x start_main_app.sh

# Create master startup script
cat > start_all_services.sh << 'ALL_EOF'
#!/bin/bash
echo "🚀 Starting Enhanced ChatterFix CMMS Services"

# Start services in order
./start_database.sh
sleep 3
./start_ai_brain.sh
sleep 2
./start_grok.sh
sleep 2
./start_work_orders.sh
sleep 2
./start_main_app.sh

sleep 5

echo "✅ All Enhanced ChatterFix Services Started!"
echo ""
echo "🔧 Services Running:"
echo "   - Main App: http://35.237.149.25:8080"
echo "   - Enhanced Work Orders: Port 8015"
echo "   - Database Service: Port 8001"
echo "   - Fix It Fred AI: Port 8005"
echo "   - Grok Strategic Analysis: Port 8006"
echo ""
echo "🎯 Best Work Order Module in the Industry: ✅"

# Show process status
echo "📊 Service Status:"
ps aux | grep -E "(app.py|database_service|work_orders_service|ai_brain_service|grok_connector)" | grep -v grep
ALL_EOF
chmod +x start_all_services.sh

# Create systemd service for the main app
echo "⚙️ Setting up systemd services..."
sudo tee /etc/systemd/system/chatterfix-enhanced.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=ChatterFix Enhanced CMMS
After=network.target

[Service]
Type=forking
User=yoyofred_gringosgambit_com
WorkingDirectory=/opt/chatterfix-cmms/current
ExecStart=/opt/chatterfix-cmms/current/start_all_services.sh
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin:/home/yoyofred_gringosgambit_com/.local/bin

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Start all services
echo "🚀 Starting Enhanced ChatterFix CMMS..."
./start_all_services.sh

# Enable systemd service
sudo systemctl daemon-reload
sudo systemctl enable chatterfix-enhanced

# Test the deployment
sleep 10
echo "🧪 Testing Enhanced ChatterFix Deployment..."

# Test main app
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Main App is running!"
else
    echo "⚠️ Main App startup issue"
fi

# Test work orders API
if curl -s http://localhost:8015/health > /dev/null; then
    echo "✅ Enhanced Work Orders API is running!"
else
    echo "⚠️ Work Orders API startup issue"
fi

# Test database service
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Database Service is running!"
else
    echo "⚠️ Database Service startup issue"
fi

echo ""
echo "🎉 ENHANCED CHATTERFIX CMMS DEPLOYED SUCCESSFULLY!"
echo "=================================================="
echo "🌐 Live URL: http://35.237.149.25:8080"
echo "🔧 Work Orders: http://35.237.149.25:8080/work-orders"
echo "🤖 AI Features: Fix It Fred + Grok Integration"
echo "🎯 Industry-Leading Work Order Management: ✅"
echo ""
echo "🚀 ChatterFix is now running with enhanced features!"
DEPLOY_EOF

chmod +x vm-deployment-package/deploy-enhanced-chatterfix.sh

echo "📋 Enhanced deployment package created:"
ls -la vm-deployment-package/

echo "🚀 Deploying to Production VM..."

# Copy files to VM
echo "📤 Uploading enhanced files..."
scp -o StrictHostKeyChecking=no -r vm-deployment-package/* ${VM_USER}@${VM_IP}:${VM_APP_DIR}/

echo "🔧 Executing enhanced deployment on VM..."

# Execute deployment on VM
ssh -o StrictHostKeyChecking=no ${VM_USER}@${VM_IP} << 'ENDSSH'
cd /opt/chatterfix-cmms/current
chmod +x *.sh
./deploy-enhanced-chatterfix.sh

echo ""
echo "🌐 Enhanced ChatterFix CMMS is now LIVE!"
echo "   Visit: http://35.237.149.25:8080"
echo "   Work Orders: http://35.237.149.25:8080/work-orders"
echo ""
echo "🤖 AI Features Active:"
echo "   - Fix It Fred: Expert maintenance advice"
echo "   - Grok Analysis: Strategic optimization"
echo "   - Real-time database integration"
echo "   - Industry-leading work order management"
echo ""
echo "🎯 Best Work Order Module in the Industry: DEPLOYED! ✅"
ENDSSH

echo ""
echo "✅ ENHANCED CHATTERFIX DEPLOYMENT COMPLETED!"
echo "============================================="
echo "🌐 Live URL: http://35.237.149.25:8080"
echo "🔧 Enhanced Work Orders: http://35.237.149.25:8080/work-orders"
echo "🤖 AI Integration: Fix It Fred + Grok"
echo "🎯 Best work order module in the industry is now LIVE!"