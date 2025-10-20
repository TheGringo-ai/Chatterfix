#!/bin/bash
# Debug startup script for ChatterFix with Ollama

exec > /tmp/startup-debug.log 2>&1
echo "=== ChatterFix Startup Debug $(date) ==="

# UFW Configuration
echo "📝 Configuring firewall..."
ufw allow 8080/tcp
ufw reload
echo "✅ Firewall configured"

# Find Python app
echo "🔍 Looking for app.py..."
find /home -name "app.py" -type f 2>/dev/null
find /opt -name "app.py" -type f 2>/dev/null

# Check for chatterfix-docker directory
echo "📁 Checking directories..."
if [ -d "/home/yoyofred_gringosgambit_com/chatterfix-docker/app" ]; then
    APP_DIR="/home/yoyofred_gringosgambit_com/chatterfix-docker/app"
    echo "✅ Found chatterfix-docker: $APP_DIR"
elif [ -d "/opt/chatterfix-cmms/current" ]; then
    APP_DIR="/opt/chatterfix-cmms/current"
    echo "✅ Found chatterfix-cmms: $APP_DIR"
else
    echo "❌ Could not find app directory"
    exit 1
fi

# List files
echo "📋 Files in $APP_DIR:"
ls -lah "$APP_DIR" | head -20

# Check for fix_it_fred_ollama.py
if [ -f "$APP_DIR/fix_it_fred_ollama.py" ]; then
    echo "✅ fix_it_fred_ollama.py exists"
else
    echo "⚠️  fix_it_fred_ollama.py not found"
fi

# Stop existing Python processes
echo "🛑 Stopping existing Python processes..."
pkill -f "python3 app.py"
sleep 2

# Check Ollama
echo "🤖 Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama not responding, attempting to start..."
    systemctl start ollama || true
    sleep 3
fi

# Set environment
echo "🔧 Setting environment..."
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_BASE_URL=http://localhost:11434
export USE_OLLAMA=true
export PORT=8080

# Load .env if exists
if [ -f "$APP_DIR/.env" ]; then
    echo "✅ Loading .env"
    set -a
    source "$APP_DIR/.env"
    set +a
fi

# Change to app directory
cd "$APP_DIR"
echo "📂 Working directory: $(pwd)"

# Start application
echo "🚀 Starting ChatterFix..."
nohup python3 app.py > /tmp/chatterfix.log 2>&1 &
APP_PID=$!
echo "✅ Started with PID: $APP_PID"

# Wait and check
sleep 8
if ps -p $APP_PID > /dev/null; then
    echo "✅ Process still running"
    echo "📋 Recent logs:"
    tail -30 /tmp/chatterfix.log
else
    echo "❌ Process died, full logs:"
    cat /tmp/chatterfix.log
fi

# Check if port is listening
echo "🔍 Checking if port 8080 is listening..."
ss -tlnp | grep 8080 || echo "⚠️  Port 8080 not listening yet"

echo "=== Startup script complete $(date) ==="
