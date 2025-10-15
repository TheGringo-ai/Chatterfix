#!/bin/bash
echo "🚀 Deploying Ollama Optimizations to VM..."

# Stop existing services
sudo systemctl stop ollama || true
sudo pkill -f ollama || true
sudo pkill -f fix_it_fred || true

# Apply Ollama optimizations
sudo mkdir -p /etc/systemd/system
sudo cp ollama.service /etc/systemd/system/
sudo cp fix-it-fred.service /etc/systemd/system/
sudo systemctl daemon-reload

# Install monitor as service
sudo cp monitor-services.py /usr/local/bin/
sudo chmod +x /usr/local/bin/monitor-services.py

# Start services
sudo systemctl enable ollama
sudo systemctl enable fix-it-fred
sudo systemctl start ollama

# Wait for Ollama to start
sleep 10

# Load optimized model
sudo -u root /usr/local/bin/ollama pull llama3.2:1b

# Start Fix It Fred
sudo systemctl start fix-it-fred

# Wait and test
sleep 15
python3 test-performance.py

echo "✅ Optimization deployment complete!"
echo "📊 Services status:"
sudo systemctl status ollama --no-pager
sudo systemctl status fix-it-fred --no-pager

echo ""
echo "🔧 To monitor services:"
echo "sudo journalctl -u ollama -f"
echo "sudo journalctl -u fix-it-fred -f"
echo ""
echo "🧪 To test performance:"
echo "python3 test-performance.py"
