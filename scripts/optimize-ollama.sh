#!/bin/bash
# LLaMA/Ollama Optimization Script for ChatterFix Production
# Optimizes Ollama service for better performance and reliability

set -e

echo "🚀 Starting LLaMA/Ollama optimization..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama already installed"
fi

# Stop existing Ollama service if running
echo "🔄 Managing Ollama service..."
sudo pkill -f ollama || true
sleep 2

# Create Ollama service user if not exists
if ! id "ollama" &>/dev/null; then
    sudo useradd -r -s /bin/false -m -d /var/lib/ollama ollama
fi

# Set up Ollama environment for performance
echo "⚙️ Configuring Ollama environment..."
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KEEP_ALIVE=5m"
Environment="OLLAMA_MODELS=/var/lib/ollama/models"
Environment="OLLAMA_ORIGINS=http://localhost:*,https://chatterfix.com,https://*.chatterfix.com"
LimitNOFILE=65536
EOF

# Create systemd service for Ollama
echo "🔧 Creating Ollama systemd service..."
cat << 'EOF' | sudo tee /etc/systemd/system/ollama.service
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="HOME=/var/lib/ollama"
WorkingDirectory=/var/lib/ollama

[Install]
WantedBy=default.target
EOF

# Set proper permissions
echo "🔐 Setting permissions..."
sudo chown -R ollama:ollama /var/lib/ollama
sudo chmod 755 /var/lib/ollama

# Reload systemd and start Ollama
echo "🚀 Starting optimized Ollama service..."
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama

# Wait for service to start
echo "⏳ Waiting for Ollama to start..."
sleep 5

# Check if Ollama is responding
echo "🏥 Health checking Ollama..."
for i in {1..10}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama is responding!"
        break
    fi
    echo "⏳ Waiting for Ollama... (attempt $i/10)"
    sleep 3
done

# Pull LLaMA model if not present
echo "📥 Ensuring LLaMA 3.1:8b model is available..."
sudo -u ollama ollama pull llama3.1:8b

# Optimize model loading
echo "🔥 Pre-loading LLaMA model for faster responses..."
sudo -u ollama ollama run llama3.1:8b "Ready for ChatterFix CMMS!" || true

# Test Ollama performance
echo "🧪 Testing Ollama performance..."
time sudo -u ollama ollama run llama3.1:8b "Test response for performance check" || echo "⚠️ Performance test failed"

# Create health monitoring script
echo "💊 Setting up health monitoring..."
cat << 'EOF' | sudo tee /usr/local/bin/ollama-health.sh
#!/bin/bash
# Ollama health check and auto-restart script

OLLAMA_URL="http://localhost:11434"
MAX_RESPONSE_TIME=10

check_ollama() {
    local response_time
    response_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time $MAX_RESPONSE_TIME "$OLLAMA_URL/api/tags" 2>/dev/null || echo "999")
    
    if (( $(echo "$response_time > $MAX_RESPONSE_TIME" | bc -l) )); then
        echo "$(date): Ollama slow response ($response_time s), restarting..."
        systemctl restart ollama
        sleep 10
        # Pre-load model after restart
        sudo -u ollama ollama run llama3.1:8b "Restarted and ready!" >/dev/null 2>&1 || true
    else
        echo "$(date): Ollama healthy (${response_time}s response)"
    fi
}

check_ollama
EOF

sudo chmod +x /usr/local/bin/ollama-health.sh

# Set up cron job for health monitoring
echo "⏰ Setting up automated health monitoring..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/ollama-health.sh >> /var/log/ollama-health.log 2>&1") | crontab -

# Final status check
echo "📊 Final Ollama status:"
sudo systemctl status ollama --no-pager
echo ""
echo "🔍 Testing API endpoint:"
curl -s http://localhost:11434/api/tags | head -3 || echo "❌ API test failed"

echo ""
echo "🎉 LLaMA/Ollama optimization complete!"
echo "🔧 Service: systemctl status ollama"
echo "📋 Logs: journalctl -u ollama -f"
echo "🏥 Health: /usr/local/bin/ollama-health.sh"
echo "📊 Monitor: tail -f /var/log/ollama-health.log"