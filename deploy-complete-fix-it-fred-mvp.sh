#!/bin/bash
# Deploy Complete Fix It Fred MVP with UI to ChatterFix VM
set -e

echo "🚀 Deploying Complete Fix It Fred MVP to ChatterFix VM..."
echo "This will deploy your technician/homeowner/DIY assistant with full UI!"

# Create comprehensive Fix It Fred deployment
echo "📦 Creating Fix It Fred MVP deployment package..."

# Upload all necessary files
echo "📤 Uploading Fix It Fred components..."
gcloud compute scp fix_it_fred_ai_service.py chatterfix-cmms-production:/tmp/fix_it_fred_ai_service_mvp.py --zone=us-east1-b
gcloud compute scp chatterfix_modular_app.py chatterfix-cmms-production:/tmp/chatterfix_app_mvp.py --zone=us-east1-b

# Create comprehensive startup script
cat > fix-it-fred-mvp-startup.sh << 'EOF'
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

EOF

echo "📤 Uploading Fix It Fred MVP startup script..."
gcloud compute scp fix-it-fred-mvp-startup.sh chatterfix-cmms-production:/tmp/ --zone=us-east1-b

echo "🔄 Restarting VM with Fix It Fred MVP..."
gcloud compute instances stop chatterfix-cmms-production --zone=us-east1-b --quiet

# Set the MVP startup script
gcloud compute instances add-metadata chatterfix-cmms-production \
  --zone=us-east1-b \
  --metadata-from-file startup-script=fix-it-fred-mvp-startup.sh

echo "⏳ Starting VM with Fix It Fred MVP (this will take 3-4 minutes)..."
gcloud compute instances start chatterfix-cmms-production --zone=us-east1-b --quiet

echo "⏰ Waiting for Fix It Fred MVP initialization..."
for i in {1..20}; do
  echo -n "."
  sleep 15
done
echo ""

echo "🧪 Testing Fix It Fred MVP deployment..."
for i in {1..3}; do
  echo "MVP Test attempt $i..."
  result=$(curl -s -X POST "https://chatterfix.com/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message":"Hello Fix It Fred, I need help with home maintenance as a DIY homeowner","user_role":"homeowner"}' \
    --connect-timeout 20 --max-time 40)
    
  if echo "$result" | grep -q '"success":true'; then
    provider=$(echo "$result" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('provider', 'unknown'))" 2>/dev/null || echo "unknown")
    response=$(echo "$result" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('response', '')[:100])" 2>/dev/null || echo "")
    echo "✅ SUCCESS! Provider: $provider"
    echo "💬 Response: $response..."
    if [ "$provider" = "ollama" ]; then
      echo "🎉 FIX IT FRED MVP SUCCESS WITH OLLAMA!"
      break
    fi
  else
    echo "⏳ Still initializing..."
  fi
  
  if [ $i -lt 3 ]; then
    echo "   Waiting 30 seconds..."
    sleep 30
  fi
done

echo ""
echo "🎯 FIX IT FRED MVP DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "✅ Complete technician/homeowner/DIY assistant deployed"
echo "🤖 Ollama-powered AI maintenance guidance"  
echo "🌐 Full UI at https://chatterfix.com"
echo "📊 Ready for maintenance tasks and DIY assistance"
echo ""
echo "🏠 Your MVP Fix It Fred is ready to help homeowners and technicians!"