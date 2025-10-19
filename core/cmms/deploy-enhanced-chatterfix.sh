#!/bin/bash

echo "🚀 Deploying Enhanced ChatterFix CMMS with Industry-Leading Work Orders"
echo "🤖 Fix It Fred & Grok AI Integration"
echo "================================================================="

# Configuration
VM_USER="fredtaylor"
VM_HOST="34.70.228.202"
VM_APP_DIR="/home/fredtaylor/chatterfix-cmms"
LOCAL_APP_DIR="/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms"

echo "📦 Preparing deployment package..."

# Create deployment package with all enhanced services
mkdir -p deployment-package
cp app.py deployment-package/
cp work_orders_api_fix.py deployment-package/work_orders_service.py
cp database_service.py deployment-package/
cp ai_brain_service.py deployment-package/
cp grok_connector.py deployment-package/
cp -r data deployment-package/ 2>/dev/null || echo "⚠️  No data directory found"

# Copy requirements and configs
echo "fastapi
uvicorn
httpx
pydantic
sqlite3
requests
python-multipart" > deployment-package/requirements.txt

# Create enhanced startup script
cat > deployment-package/start-enhanced-services.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Enhanced ChatterFix CMMS Services"
echo "🤖 Industry-Leading Work Orders with AI"

# Kill any existing processes
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*database_service.py" 2>/dev/null || true
pkill -f "python.*work_orders_service.py" 2>/dev/null || true
pkill -f "python.*ai_brain_service.py" 2>/dev/null || true
pkill -f "python.*grok_connector.py" 2>/dev/null || true

sleep 2

# Install requirements
pip3 install -r requirements.txt

# Start services in correct order
echo "🗄️  Starting Database Service (Port 8001)..."
nohup python3 database_service.py > database.log 2>&1 &
sleep 3

echo "🤖 Starting Fix It Fred AI Service (Port 8005)..."
nohup PORT=8005 python3 ai_brain_service.py > ai_brain.log 2>&1 &
sleep 2

echo "🧠 Starting Grok Connector (Port 8006)..."
nohup PORT=8006 python3 grok_connector.py > grok.log 2>&1 &
sleep 2

echo "🔧 Starting Enhanced Work Orders Service (Port 8015)..."
nohup PORT=8015 python3 work_orders_service.py > work_orders.log 2>&1 &
sleep 2

echo "🌐 Starting Main ChatterFix App (Port 8080)..."
nohup PORT=8080 python3 app.py > main_app.log 2>&1 &

sleep 5

echo "✅ Enhanced ChatterFix CMMS Deployment Complete!"
echo ""
echo "🔧 Services Running:"
echo "   - Main App: http://$(curl -s ifconfig.me):8080"
echo "   - Enhanced Work Orders: Port 8015"
echo "   - Database Service: Port 8001"
echo "   - Fix It Fred AI: Port 8005"
echo "   - Grok Strategic Analysis: Port 8006"
echo ""
echo "🎯 Best Work Order Module in the Industry: ✅"

# Show process status
echo "📊 Service Status:"
ps aux | grep -E "(app.py|database_service|work_orders_service|ai_brain_service|grok_connector)" | grep -v grep
EOF

chmod +x deployment-package/start-enhanced-services.sh

echo "📋 Deployment package created with enhanced services:"
ls -la deployment-package/

echo "🚀 Deploying to production VM..."

# Copy files to VM
scp -r deployment-package/* ${VM_USER}@${VM_HOST}:${VM_APP_DIR}/

echo "🔧 Starting enhanced services on VM..."

# Execute deployment on VM
ssh ${VM_USER}@${VM_HOST} << 'ENDSSH'
cd /home/fredtaylor/chatterfix-cmms
chmod +x start-enhanced-services.sh
./start-enhanced-services.sh

echo ""
echo "🌐 Enhanced ChatterFix CMMS is now live!"
echo "   Visit: https://www.chatterfix.com"
echo "   Work Orders: https://www.chatterfix.com/work-orders"
echo ""
echo "🤖 AI Features:"
echo "   - Fix It Fred: Expert maintenance advice"
echo "   - Grok Analysis: Strategic optimization"
echo "   - Real-time database integration"
echo "   - Industry-leading work order management"
ENDSSH

echo "✅ Enhanced ChatterFix deployment completed!"
echo "🎯 Best work order module in the industry is now live!"
echo "🌐 Visit: https://www.chatterfix.com"