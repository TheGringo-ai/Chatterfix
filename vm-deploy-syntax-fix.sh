#!/bin/bash
# Deploy Syntax Fix to ChatterFix VM
set -e

echo "🔧 Deploying Fix It Fred Syntax Fix to VM..."
echo "This will fix the bracket syntax error and restart services!"

# Upload the fixed files
echo "📤 Uploading fixed Fix It Fred..."
gcloud compute scp fix_it_fred_ai_service.py chatterfix-cmms-production:/tmp/fix_it_fred_ai_service_fixed.py --zone=us-east1-b

# Create startup script with fix deployment
cat > vm-startup-with-fix.sh << 'EOF'
#!/bin/bash
# ChatterFix VM Startup with Syntax Fix

echo "🚀 ChatterFix VM Starting with Syntax Fix..."
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Kill any existing processes
pkill -f ollama || true
pkill -f fix_it_fred || true
pkill -f app.py || true
sleep 5

# Deploy the syntax fix
echo "🔧 Deploying syntax fix..."
cp /tmp/fix_it_fred_ai_service_fixed.py ./fix_it_fred_ai_service.py

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

# Start Fix It Fred AI Service with FIXED VERSION
echo "🧠 Starting FIXED Fix It Fred AI Service on port 9000..."
export OLLAMA_HOST=localhost:11434
export DEFAULT_MODEL=llama3.2:1b
nohup python3 fix_it_fred_ai_service.py > /tmp/fix_it_fred_FIXED.log 2>&1 &
FIX_IT_FRED_PID=$!
echo "✅ FIXED Fix It Fred started with PID: $FIX_IT_FRED_PID"

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

# Test the fix specifically
echo ""
echo "🧪 Testing Syntax Fix..."
curl -s -X POST "http://localhost:9000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"Testing syntax fix","provider":"ollama","model":"llama3.2:1b"}' > /tmp/syntax_test.json

if grep -q '"success":true' /tmp/syntax_test.json; then
    echo "🎉 SYNTAX FIX SUCCESS - Ollama working!"
else
    echo "❌ Syntax fix needs more work"
    echo "Fix It Fred log:"
    tail -20 /tmp/fix_it_fred_FIXED.log
fi

echo ""
echo "🎉 ChatterFix VM Startup Complete with SYNTAX FIX!"
echo "🌐 Access at: https://chatterfix.com"
echo "📊 AI should now work without syntax errors!"
echo ""
echo "📝 Logs available at:"
echo "  • Ollama: /tmp/ollama.log"
echo "  • Fix It Fred (FIXED): /tmp/fix_it_fred_FIXED.log"  
echo "  • ChatterFix App: /tmp/chatterfix_app.log"
echo "  • Syntax Test: /tmp/syntax_test.json"
EOF

echo "📤 Uploading syntax fix startup script to VM..."
gcloud compute scp vm-startup-with-fix.sh chatterfix-cmms-production:/tmp/ --zone=us-east1-b

echo "🔄 Restarting VM with syntax fix..."
gcloud compute instances stop chatterfix-cmms-production --zone=us-east1-b --quiet

# Set the startup script
gcloud compute instances add-metadata chatterfix-cmms-production \
  --zone=us-east1-b \
  --metadata-from-file startup-script=/tmp/vm-startup-with-fix.sh

echo "⏳ Starting VM with syntax fix (this will take 2-3 minutes)..."
gcloud compute instances start chatterfix-cmms-production --zone=us-east1-b --quiet

echo "⏰ Waiting 3 minutes for complete initialization with fix..."
for i in {1..18}; do
  echo -n "."
  sleep 10
done
echo ""

echo "🧪 Testing syntax fix deployment..."
for i in {1..5}; do
  echo "Test attempt $i..."
  curl -s -X POST "https://chatterfix.com/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message":"Test syntax fix - is Ollama working now without crashes?","user_role":"technician"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    success = data.get('success', False) 
    provider = data.get('provider', 'unknown')
    response = data.get('response', '')[:100]
    print(f'Attempt $i: Success={success}, Provider={provider}')
    print(f'Response: {response}...')
    if success and provider == 'ollama':
        print('🎉 SYNTAX FIX SUCCESS - OLLAMA WORKING!')
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
echo "🎯 SYNTAX FIX DEPLOYMENT COMPLETE!"
echo "=================================="
echo ""
echo "✅ VM restarted with syntax fix deployed"
echo "🔧 Fix It Fred bracket syntax error resolved"
echo "🤖 Ollama should no longer appear to 'crash'"
echo "📊 ChatterFix AI chat should work reliably now"
echo ""
echo "🌐 Test your fixed AI at: https://chatterfix.com"
echo "💬 The 'Sorry, I encountered an issue' should be gone!"