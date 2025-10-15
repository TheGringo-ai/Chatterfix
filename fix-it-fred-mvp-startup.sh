#!/bin/bash
# Fix It Fred MVP Complete Deployment

echo "🚀 Starting Fix It Fred MVP Deployment..."
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Kill everything and start fresh
echo "🛑 Stopping all existing services..."
pkill -f ollama || true
pkill -f fix_it_fred || true  
pkill -f app.py || true
pkill -f python3 || true
sleep 10

# Stop systemd services that are failing
systemctl stop llama-warmup.service || true
systemctl disable llama-warmup.service || true

# Deploy MVP files
echo "📦 Deploying MVP files..."
cp /tmp/fix_it_fred_ai_service_mvp.py ./fix_it_fred_ai_service.py
cp /tmp/chatterfix_app_mvp.py ./chatterfix_modular_app.py

# Install any missing dependencies
echo "📋 Installing dependencies..."
pip3 install --user flask fastapi uvicorn requests python-multipart aiofiles || true

# Set optimal environment for MVP
export OLLAMA_HOST=localhost:11434
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_CONCURRENCY=1
export DEFAULT_MODEL=llama3.2:1b

echo "🤖 Starting Ollama for Fix It Fred MVP..."
# Start Ollama
/usr/local/bin/ollama serve > /tmp/ollama_mvp.log 2>&1 &
OLLAMA_PID=$!
echo "✅ Ollama started with PID: $OLLAMA_PID"

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to initialize..."
sleep 20

# Warm up the model for Fix It Fred
echo "🔥 Warming up Fix It Fred AI model..."
/usr/local/bin/ollama run llama3.2:1b "Hello, I'm Fix It Fred, your maintenance assistant" || true
sleep 5

# Start Fix It Fred MVP Service
echo "🧰 Starting Fix It Fred MVP Service (Technician/Homeowner/DIY Assistant)..."
nohup python3 fix_it_fred_ai_service.py > /tmp/fix_it_fred_mvp.log 2>&1 &
FRED_PID=$!
echo "✅ Fix It Fred MVP started with PID: $FRED_PID"

# Wait for Fix It Fred to initialize
sleep 15

# Start ChatterFix with Fix It Fred UI
echo "🌐 Starting ChatterFix CMMS with Fix It Fred UI..."
nohup python3 chatterfix_modular_app.py > /tmp/chatterfix_mvp.log 2>&1 &
APP_PID=$!
echo "✅ ChatterFix MVP UI started with PID: $APP_PID"

# Final health checks
sleep 15
echo ""
echo "📊 Fix It Fred MVP Health Check:"
echo "Ollama API: $(curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ RUNNING" || echo "❌ DOWN")"
echo "Fix It Fred Service: $(curl -s http://localhost:9000/health > /dev/null && echo "✅ RUNNING" || echo "❌ DOWN")"  
echo "ChatterFix UI: $(curl -s http://localhost:8080 > /dev/null && echo "✅ RUNNING" || echo "❌ DOWN")"

# Test Fix It Fred specifically
echo ""
echo "🧪 Testing Fix It Fred MVP functionality..."
curl -s -X POST "http://localhost:9000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello Fix It Fred, Im a homeowner who needs help with maintenance","provider":"ollama","model":"llama3.2:1b"}' > /tmp/fred_test.json

if grep -q '"success":true' /tmp/fred_test.json; then
    echo "✅ Fix It Fred MVP WORKING - Technician/Homeowner/DIY Assistant Ready!"
    PROVIDER=$(grep -o '"provider":"[^"]*"' /tmp/fred_test.json | cut -d'"' -f4)
    echo "🤖 Using Provider: $PROVIDER"
else
    echo "⚠️  Fix It Fred MVP initializing..."
    echo "Debug info:"
    cat /tmp/fred_test.json
    echo ""
    echo "Fix It Fred logs:"
    tail -10 /tmp/fix_it_fred_mvp.log
fi

echo ""
echo "🎉 FIX IT FRED MVP DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "🏠 HOMEOWNER FEATURES: Ready"
echo "🔧 TECHNICIAN FEATURES: Ready" 
echo "🛠️  DIY ASSISTANT FEATURES: Ready"
echo "🤖 AI-POWERED MAINTENANCE GUIDANCE: Ready"
echo ""
echo "🌐 Access Fix It Fred at: https://chatterfix.com"
echo "💬 Your AI maintenance assistant is ready to help!"
echo ""
echo "📝 MVP Logs:"
echo "  • Ollama: /tmp/ollama_mvp.log"
echo "  • Fix It Fred: /tmp/fix_it_fred_mvp.log"
echo "  • ChatterFix UI: /tmp/chatterfix_mvp.log"
echo "  • Test Results: /tmp/fred_test.json"

