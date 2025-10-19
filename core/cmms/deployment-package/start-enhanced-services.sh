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
