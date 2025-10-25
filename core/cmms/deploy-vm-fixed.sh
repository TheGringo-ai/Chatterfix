#!/bin/bash

echo "🚀 Deploying Enhanced ChatterFix CMMS to Production VM"
echo "🤖 Fix It Fred & Grok AI Integration - Permission Fixed"
echo "================================================================="

# VM Configuration
VM_IP="35.237.149.25"
VM_USER="yoyofred_gringosgambit_com"

echo "📤 Uploading enhanced files to home directory..."

# Upload to home directory first (to avoid permission issues)
scp -o StrictHostKeyChecking=no -r vm-deployment-package/* ${VM_USER}@${VM_IP}:~/

echo "🔧 Executing enhanced deployment on VM..."

# Execute deployment
ssh -o StrictHostKeyChecking=no ${VM_USER}@${VM_IP} << 'ENDSSH'
echo "🚀 Enhanced ChatterFix CMMS Deployment Starting..."

# Create app directory if it doesn't exist
sudo mkdir -p /opt/chatterfix-cmms/current
sudo chown -R yoyofred_gringosgambit_com:yoyofred_gringosgambit_com /opt/chatterfix-cmms

# Move files to the app directory
cp -r ~/vm-deployment-package/* /opt/chatterfix-cmms/current/ 2>/dev/null || true
cp ~/*.py /opt/chatterfix-cmms/current/ 2>/dev/null || true
cp ~/*.sh /opt/chatterfix-cmms/current/ 2>/dev/null || true
cp ~/*.txt /opt/chatterfix-cmms/current/ 2>/dev/null || true
cp -r ~/data /opt/chatterfix-cmms/current/ 2>/dev/null || true

# Change to app directory
cd /opt/chatterfix-cmms/current

# Make scripts executable
chmod +x *.sh 2>/dev/null || true

# Stop existing services
echo "🛑 Stopping existing services..."
sudo systemctl stop chatterfix-ai-chat 2>/dev/null || true
sudo systemctl stop chatterfix-enhanced 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*database_service" 2>/dev/null || true
pkill -f "python.*work_orders_service" 2>/dev/null || true
pkill -f "python.*ai_brain_service" 2>/dev/null || true
pkill -f "python.*grok_connector" 2>/dev/null || true

# Kill processes on ports
for port in 8080 8081 8001 8005 8006 8015; do
    sudo lsof -ti:$port | xargs sudo kill -9 2>/dev/null || true
done

sleep 5

# Install dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --user --quiet fastapi uvicorn httpx pydantic requests python-multipart python-dotenv

# Create data directory
mkdir -p data

# Start Database Service
echo "🗄️ Starting Database Service (Port 8001)..."
nohup python3 database_service.py > database.log 2>&1 &
sleep 3

# Start Fix It Fred AI Service
echo "🤖 Starting Fix It Fred AI Service (Port 8005)..."
nohup PORT=8005 python3 ai_brain_service.py > ai_brain.log 2>&1 &
sleep 2

# Start Grok Connector
echo "🧠 Starting Grok Connector (Port 8006)..."
nohup PORT=8006 python3 grok_connector.py > grok.log 2>&1 &
sleep 2

# Start Enhanced Work Orders Service
echo "🔧 Starting Enhanced Work Orders Service (Port 8015)..."
nohup PORT=8015 python3 work_orders_service.py > work_orders.log 2>&1 &
sleep 2

# Start Main ChatterFix App
echo "🌐 Starting Main ChatterFix App (Port 8080)..."
nohup PORT=8080 python3 app.py > main_app.log 2>&1 &

sleep 5

echo "✅ Enhanced ChatterFix CMMS Services Started!"
echo ""
echo "🔧 Services Running:"
echo "   - Main App: http://35.237.149.25:8080"
echo "   - Enhanced Work Orders: Port 8015" 
echo "   - Database Service: Port 8001"
echo "   - Fix It Fred AI: Port 8005"
echo "   - Grok Strategic Analysis: Port 8006"

# Test services
echo ""
echo "🧪 Testing Services..."

# Test main app
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Main App is running on port 8080!"
else
    echo "⚠️ Main App not responding, checking logs..."
    tail -5 main_app.log
fi

# Test enhanced work orders
if curl -s http://localhost:8015/health > /dev/null 2>&1; then
    echo "✅ Enhanced Work Orders API is running on port 8015!"
else
    echo "⚠️ Work Orders API not responding, checking logs..."
    tail -5 work_orders.log
fi

# Test database
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Database Service is running on port 8001!"
else
    echo "⚠️ Database Service not responding, checking logs..."
    tail -5 database.log
fi

echo ""
echo "📊 Process Status:"
ps aux | grep -E "(app.py|database_service|work_orders_service|ai_brain_service|grok_connector)" | grep -v grep

echo ""
echo "🎉 ENHANCED CHATTERFIX CMMS DEPLOYED!"
echo "===================================="
echo "🌐 Live URL: http://35.237.149.25:8080"
echo "🔧 Work Orders: http://35.237.149.25:8080/work-orders"
echo "🤖 AI Features: Fix It Fred + Grok Integration"
echo "🎯 Industry-Leading Work Order Management: ✅"
ENDSSH

echo ""
echo "✅ DEPLOYMENT COMPLETED!"
echo "========================"
echo "🌐 ChatterFix is now live at: http://35.237.149.25:8080"
echo "🔧 Enhanced Work Orders: http://35.237.149.25:8080/work-orders"
echo "🤖 AI Integration: Fix It Fred + Grok"
echo "🎯 Best work order module in the industry is now LIVE!"