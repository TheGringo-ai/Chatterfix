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
