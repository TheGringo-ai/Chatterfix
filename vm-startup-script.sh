#!/bin/bash
set -e

echo "🔧 ChatterFix Complete Stack Setup"
echo "=================================="
cd /home/yoyofred_gringosgambit_com

# Kill existing processes
echo "🛑 Stopping existing services..."
sudo pkill -f python3 || true
sudo pkill -f ollama || true
sudo systemctl stop ollama 2>/dev/null || true

# Install/Update Python packages
echo "📦 Installing Python dependencies..."
python3 -m pip install --upgrade pip --user
python3 -m pip install --user fastapi uvicorn httpx asyncpg python-multipart jinja2

# Install Ollama if not present
echo "🤖 Setting up Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "   Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "   ✅ Ollama already installed"
fi

# Create Ollama systemd service
echo "🔧 Configuring Ollama service..."
sudo tee /etc/systemd/system/ollama.service > /dev/null << 'OLLAMA_SERVICE'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
Type=simple
User=root
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
OLLAMA_SERVICE

# Start Ollama
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama

echo "⏳ Waiting for Ollama to start..."
sleep 10

# Test Ollama
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running"
    
    # Pull essential models in background
    echo "📥 Pulling AI models..."
    nohup bash -c "
        sleep 5
        ollama pull mistral:7b 2>&1 | tee ollama-pull.log
        ollama pull llama3:8b 2>&1 | tee -a ollama-pull.log
        echo 'Models downloaded at $(date)' >> ollama-pull.log
    " &
    
else
    echo "⚠️  Ollama startup may be slow - will retry"
fi

# Start ChatterFix if app exists
if [ -f "chatterfix_complete.py" ]; then
    echo "🚀 Starting ChatterFix Complete..."
    nohup python3 chatterfix_complete.py > chatterfix.log 2>&1 &
    sleep 3
    
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ ChatterFix is running"
    else
        echo "⚠️  ChatterFix startup in progress"
    fi
else
    echo "📋 ChatterFix app not found - manual deployment needed"
fi

echo ""
echo "🎉 Setup complete!"
echo "🌐 ChatterFix: http://35.237.149.25:8080"
echo "🤖 Ollama: http://35.237.149.25:11434"
echo "📊 Health: http://35.237.149.25:8080/health"
echo ""
