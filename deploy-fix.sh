#!/bin/bash
# Quick deploy of fixed fix_it_fred_ollama.py

set -e
export HOME=/root

echo "🔧 Deploying Fix It Fred Ollama Fix"
echo "===================================="

# Navigate to app directory
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Download the fixed file from the tarball (assuming it's uploaded to /tmp)
if [ -f /tmp/fix-it-fred-fixed.tar.gz ]; then
    echo "📦 Extracting fixed code..."
    tar xzf /tmp/fix-it-fred-fixed.tar.gz
    echo "✅ Code extracted"
else
    echo "❌ Tarball not found at /tmp/fix-it-fred-fixed.tar.gz"
    exit 1
fi

# Restart ChatterFix
echo "🔄 Restarting ChatterFix..."
pkill -f "python3 app.py" || true
sleep 2

export OLLAMA_HOST=http://localhost:11434
export PORT=8080

# Load .env if exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

nohup python3 app.py > /tmp/chatterfix.log 2>&1 &
CHATTERFIX_PID=$!

echo "⏳ Waiting for ChatterFix to start..."
sleep 8

if ps -p $CHATTERFIX_PID > /dev/null; then
    echo "✅ ChatterFix restarted successfully (PID: $CHATTERFIX_PID)"
    echo "📋 Recent logs:"
    tail -15 /tmp/chatterfix.log
else
    echo "❌ ChatterFix failed to start. Logs:"
    cat /tmp/chatterfix.log
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "Test with: curl http://localhost:8080/api/ollama/status"
