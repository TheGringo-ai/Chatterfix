#!/bin/bash
# 🤖 Deploy Ollama Integration to ChatterFix VM
# Updates app.py and adds fix_it_fred_ollama.py

set -e

echo "🤖 Deploying Ollama Integration to ChatterFix CMMS..."
echo "===================================================="

# Navigate to app directory
cd ~/chatterfix-docker/app || exit 1

# Stop current app
echo "🛑 Stopping current ChatterFix instance..."
pkill -f "python3 app.py" || true
sleep 2

# Backup current files
echo "💾 Backing up current files..."
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S) || true

# The files should already be copied via SCP
echo "✅ Using updated app.py and fix_it_fred_ollama.py"

# Verify Ollama is running
echo "🔍 Checking Ollama status..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
    OLLAMA_MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print(', '.join([m['name'] for m in data.get('models', [])]))")
    echo "📦 Available models: $OLLAMA_MODELS"
else
    echo "⚠️  Ollama not responding - starting service..."
    systemctl start ollama || true
    sleep 5
fi

# Set up environment variables
echo "🔧 Setting up environment..."
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_BASE_URL=http://localhost:11434
export USE_OLLAMA=true

# Load API keys if .env exists
if [ -f .env ]; then
    echo "📝 Loading environment from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start ChatterFix
echo "🚀 Starting ChatterFix with Ollama integration..."
nohup python3 app.py > /tmp/chatterfix.log 2>&1 &
CHATTERFIX_PID=$!

echo "⏳ Waiting for ChatterFix to start..."
sleep 10

# Check if process is running
if ps -p $CHATTERFIX_PID > /dev/null; then
    echo "✅ ChatterFix started successfully (PID: $CHATTERFIX_PID)"

    # Show recent logs
    echo ""
    echo "📋 Recent logs:"
    tail -20 /tmp/chatterfix.log

    echo ""
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "===================="
    echo "🌐 ChatterFix: http://35.237.149.25:8080"
    echo "🤖 Ollama Status: http://35.237.149.25:8080/api/ollama/status"
    echo "🔧 Fix It Fred Ollama: http://35.237.149.25:8080/api/fix-it-fred/troubleshoot-ollama"
    echo "📊 Health: http://35.237.149.25:8080/health"
else
    echo "❌ Failed to start ChatterFix - check logs:"
    tail -50 /tmp/chatterfix.log
    exit 1
fi
