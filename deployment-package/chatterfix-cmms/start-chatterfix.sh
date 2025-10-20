#!/bin/bash
set -e

echo "🚀 Starting ChatterFix CMMS Services"
echo "===================================="

# Kill existing processes
echo "🛑 Stopping existing services..."
pkill -f "python.*app.py" || true
pkill -f "python.*service.py" || true
sleep 2

# Set environment
export PYTHONPATH=/home/yoyofred_gringosgambit_com/chatterfix-cmms
export CHATTERFIX_ENV=production
export PORT=8080

cd /home/yoyofred_gringosgambit_com/chatterfix-cmms

# Start core services in background
echo "🚀 Starting services..."

# Main platform gateway (port 8080)
echo "  🌐 Starting Platform Gateway..."
nohup python3 platform_gateway.py > logs/platform_gateway.log 2>&1 &

# AI Brain service (port 8005)
echo "  🧠 Starting AI Brain Service..."
nohup python3 ai_brain_service.py > logs/ai_brain.log 2>&1 &

# Backend unified service (port 8001)
echo "  🔧 Starting Backend Service..."
nohup python3 backend_unified_service.py > logs/backend.log 2>&1 &

# Grok connector (port 8006)
echo "  🤖 Starting Grok Connector..."
nohup python3 grok_connector.py > logs/grok_connector.log 2>&1 &

# Grok infrastructure advisor (port 8007)
echo "  🏗️ Starting Infrastructure Advisor..."
nohup python3 grok_infrastructure_advisor.py > logs/grok_infrastructure.log 2>&1 &

# Budget tracker (port 8009)
echo "  💰 Starting Budget Tracker..."
nohup python3 budget_tracker.py > logs/budget_tracker.log 2>&1 &

# Mobile server (port 8080 alt)
echo "  📱 Starting Mobile Server..."
nohup python3 mobile_server.py > logs/mobile_server.log 2>&1 &

# Fred dev API (port 8004)
echo "  👨‍💻 Starting Fred Dev API..."
nohup python3 fred_dev_api.py > logs/fred_dev_api.log 2>&1 &

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 15

echo ""
echo "🧪 Testing services..."
curl -s http://localhost:8080/health && echo "✅ Platform Gateway: OK" || echo "❌ Platform Gateway: FAILED"
curl -s http://localhost:8005/health && echo "✅ AI Brain: OK" || echo "❌ AI Brain: FAILED"
curl -s http://localhost:8001/health && echo "✅ Backend: OK" || echo "❌ Backend: FAILED"
curl -s http://localhost:8006/ && echo "✅ Grok Connector: OK" || echo "❌ Grok Connector: FAILED"
curl -s http://localhost:8007/ && echo "✅ Infrastructure Advisor: OK" || echo "❌ Infrastructure Advisor: FAILED"
curl -s http://localhost:8009/ && echo "✅ Budget Tracker: OK" || echo "❌ Budget Tracker: FAILED"
curl -s http://localhost:8004/health && echo "✅ Fred Dev API: OK" || echo "❌ Fred Dev API: FAILED"

echo ""
echo "🎉 ChatterFix CMMS Services Started!"
echo "===================================="
echo "🌐 Main Dashboard: http://35.237.149.25:8080"
echo "🧠 AI Brain: http://35.237.149.25:8005"
echo "🤖 Grok Chat: http://35.237.149.25:8006"
echo "🏗️ Infrastructure: http://35.237.149.25:8007"
echo "💰 Budget: http://35.237.149.25:8009"
echo "👨‍💻 Dev API: http://35.237.149.25:8004"
echo ""
echo "📊 Check logs: tail -f logs/*.log"

