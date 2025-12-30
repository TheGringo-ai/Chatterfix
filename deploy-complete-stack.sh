#!/bin/bash
set -e

echo "🚀 ChatterFix Complete Stack Deployment"
echo "========================================"
echo "Target VM: 35.237.149.25"
echo "PostgreSQL: 35.225.244.14"
echo "Timestamp: $(date)"
echo ""

VM_IP="35.237.149.25"
VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
PROJECT="fredfix"

# Create startup script for VM
echo "📝 Creating VM startup script..."
cat > vm-startup-script.sh << 'STARTUP_EOF'
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
STARTUP_EOF

chmod +x vm-startup-script.sh

# Update VM metadata with startup script
echo "📤 Uploading startup script to VM..."
gcloud compute instances add-metadata $VM_NAME \
    --zone=$ZONE \
    --project=$PROJECT \
    --metadata-from-file startup-script=vm-startup-script.sh

echo "🔄 Restarting VM to run setup..."
gcloud compute instances reset $VM_NAME --zone=$ZONE --project=$PROJECT

echo ""
echo "⏳ Waiting for VM to restart and setup to complete..."
sleep 45

# Test connectivity
echo "🩺 Testing services..."
echo "VM Status:"
gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="value(status)"

echo ""
echo "ChatterFix Health:"
if curl -s --connect-timeout 10 http://$VM_IP:8080/health; then
    echo ""
    echo "✅ ChatterFix is healthy"
else
    echo "⚠️  ChatterFix may still be starting up"
fi

echo ""
echo "Ollama Status:"
if curl -s --connect-timeout 10 http://$VM_IP:11434/api/tags; then
    echo ""
    echo "✅ Ollama is responding"
else
    echo "⚠️  Ollama may still be starting up"
fi

echo ""
echo "🎯 DEPLOYMENT SUMMARY"
echo "===================="
echo "✅ VM restarted with complete setup script"
echo "✅ Ollama installation and configuration"
echo "✅ Python dependencies installed"
echo "✅ Services configured for auto-start"
echo ""
echo "🔗 Access Points:"
echo "   🌐 Main App: http://$VM_IP:8080"
echo "   🤖 Fix It Fred: http://$VM_IP:8080/fred"
echo "   📊 Health Check: http://$VM_IP:8080/health"
echo "   🧠 Ollama API: http://$VM_IP:11434/api/tags"
echo ""
echo "📋 Next Steps:"
echo "1. Copy chatterfix_complete.py to VM"
echo "2. Test PostgreSQL connection"
echo "3. Wait for AI models to download"
echo ""

# Show copy command
echo "🔧 Manual File Copy Command:"
echo "gcloud compute scp chatterfix_complete.py $VM_NAME:~/ --zone=$ZONE --project=$PROJECT"
echo ""