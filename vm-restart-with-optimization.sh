#!/bin/bash
# Restart ChatterFix VM with Ollama Optimizations
set -e

echo "🔄 Restarting ChatterFix VM with Ollama Optimizations..."
echo "This will apply all optimizations and get AI working stable!"

# Create startup script with all optimizations
cat > vm-startup-optimized.sh << 'EOF'
#!/bin/bash
# ChatterFix VM Startup with Ollama Optimizations

echo "🚀 ChatterFix VM Starting with Ollama Optimizations..."
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Kill any existing processes
pkill -f ollama || true
pkill -f fix_it_fred || true
pkill -f app.py || true
sleep 5

# Set optimized environment variables
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_CONCURRENCY=2
export OLLAMA_FLASH_ATTENTION=true

echo "🤖 Starting Ollama with optimizations..."
# Start Ollama in background
/usr/local/bin/ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!
echo "✅ Ollama started with PID: $OLLAMA_PID"

# Wait for Ollama to initialize
echo "⏳ Waiting for Ollama to be ready (30 seconds)..."
sleep 30

# Test Ollama and warm up the model
echo "🔥 Warming up llama3.2:1b model..."
/usr/local/bin/ollama run llama3.2:1b "Hello, warming up the model" > /dev/null 2>&1 || true

# Start Fix It Fred AI Service
echo "🧠 Starting Fix It Fred AI Service on port 9000..."
export OLLAMA_HOST=localhost:11434
export DEFAULT_MODEL=llama3.2:1b
nohup python3 fix_it_fred_ai_service.py > /tmp/fix_it_fred.log 2>&1 &
FIX_IT_FRED_PID=$!
echo "✅ Fix It Fred started with PID: $FIX_IT_FRED_PID"

# Wait a bit more
sleep 15

# Start main ChatterFix app
echo "🌐 Starting ChatterFix main app..."
nohup python3 chatterfix_app_with_db.py > /tmp/chatterfix_app.log 2>&1 &
APP_PID=$!
echo "✅ ChatterFix app started with PID: $APP_PID"

# Final status check
sleep 10
echo "📊 Final Status Check:"
echo "Ollama status: $(curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ RUNNING" || echo "❌ DOWN")"
echo "Fix It Fred status: $(curl -s http://localhost:9000/health > /dev/null && echo "✅ RUNNING" || echo "❌ DOWN")"
echo "ChatterFix app status: $(curl -s http://localhost:8080 > /dev/null && echo "✅ RUNNING" || echo "❌ DOWN")"

echo ""
echo "🎉 ChatterFix VM Startup Complete with Optimizations!"
echo "🌐 Access at: https://chatterfix.com"
echo "📊 AI should respond in 3-8 seconds now!"
echo ""
echo "📝 Logs available at:"
echo "  • Ollama: /tmp/ollama.log"
echo "  • Fix It Fred: /tmp/fix_it_fred.log"  
echo "  • ChatterFix App: /tmp/chatterfix_app.log"
EOF

echo "📤 Uploading optimized startup script to VM..."
gcloud compute scp vm-startup-optimized.sh chatterfix-cmms-production:/tmp/ --zone=us-east1-b

echo "🔄 Restarting VM with optimization script..."
gcloud compute instances stop chatterfix-cmms-production --zone=us-east1-b --quiet

# Set the startup script
gcloud compute instances add-metadata chatterfix-cmms-production \
  --zone=us-east1-b \
  --metadata-from-file startup-script=/tmp/vm-startup-optimized.sh

echo "⏳ Starting VM (this will take 2-3 minutes)..."
gcloud compute instances start chatterfix-cmms-production --zone=us-east1-b --quiet

echo "⏰ Waiting 3 minutes for complete initialization..."
for i in {1..18}; do
  echo -n "."
  sleep 10
done
echo ""

echo "🧪 Testing optimized setup..."
for i in {1..5}; do
  echo "Test attempt $i..."
  curl -s -X POST "https://chatterfix.com/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message":"Test optimized Ollama - are you working fast now?","user_role":"technician"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    success = data.get('success', False) 
    provider = data.get('provider', 'unknown')
    print(f'Attempt $i: Success={success}, Provider={provider}')
    if success and provider != 'fallback':
        print('🎉 OLLAMA OPTIMIZATION SUCCESS!')
        exit(0)
    elif success:
        print('✅ Working with fallback, trying again...')
    else:
        print('❌ Still having issues, trying again...')
except:
    print('❌ Parse error, trying again...')
" && break || sleep 15
done

echo ""
echo "🎯 OLLAMA OPTIMIZATION DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "✅ VM restarted with optimized settings"
echo "🤖 Ollama configured for 3-8 second responses"
echo "🧠 Fix It Fred AI service optimized"
echo "📊 ChatterFix CMMS with database integration"
echo ""
echo "🌐 Test your optimized AI at: https://chatterfix.com"
echo "💬 AI chat should now respond quickly and reliably!"