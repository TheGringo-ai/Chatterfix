#!/bin/bash
# 🤖 Complete Ollama Setup and Integration Script
# Sets up Ollama, downloads models, and integrates with ChatterFix AI Brain

set -e

# Set HOME for root user
export HOME=/root

echo "🤖 OLLAMA COMPLETE SETUP"
echo "========================"
echo "Timestamp: $(date)"
echo ""

# 1. Install Ollama if not present
echo "📦 Step 1: Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "   Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "   ✅ Ollama installed"
else
    echo "   ✅ Ollama already installed"
fi

# 2. Create systemd service for Ollama
echo ""
echo "🔧 Step 2: Setting up Ollama systemd service..."
cat > /etc/systemd/system/ollama.service << 'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
Type=simple
User=root
Environment="OLLAMA_HOST=0.0.0.0:11434"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ollama.service
systemctl restart ollama.service

echo "   ⏳ Waiting for Ollama to start..."
sleep 5

# 3. Verify Ollama is running
echo ""
echo "🔍 Step 3: Verifying Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama is running on localhost:11434"
else
    echo "   ❌ Ollama failed to start. Checking logs:"
    journalctl -u ollama.service -n 20 --no-pager
    exit 1
fi

# 4. Check for existing models
echo ""
echo "📦 Step 4: Checking for existing models..."
EXISTING_MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join([m['name'] for m in data.get('models', [])]))" 2>/dev/null || echo "")

if echo "$EXISTING_MODELS" | grep -q "llama3:8b"; then
    echo "   ✅ Llama3 8B already available"
    LLAMA3_EXISTS=true
else
    echo "   ⚠️  Llama3 8B not found"
    LLAMA3_EXISTS=false
fi

if echo "$EXISTING_MODELS" | grep -q "mistral:7b"; then
    echo "   ✅ Mistral 7B already available"
    MISTRAL_EXISTS=true
else
    echo "   ⚠️  Mistral 7B not found"
    MISTRAL_EXISTS=false
fi

# 5. Download Llama3 8B if needed
if [ "$LLAMA3_EXISTS" = false ]; then
    echo ""
    echo "⬇️  Step 5a: Downloading Llama3 8B (4.7 GB, ~5-10 min)..."
    ollama pull llama3:8b
    echo "   ✅ Llama3 8B downloaded"
else
    echo ""
    echo "⏭️  Step 5a: Skipping Llama3 download (already exists)"
fi

# 6. Download Mistral 7B in background if needed
if [ "$MISTRAL_EXISTS" = false ]; then
    echo ""
    echo "⬇️  Step 5b: Starting Mistral 7B download in background (4.4 GB)..."
    nohup ollama pull mistral:7b > /tmp/ollama-mistral-pull.log 2>&1 &
    MISTRAL_PID=$!
    echo "   🔄 Mistral download started (PID: $MISTRAL_PID)"
    echo "   📋 Monitor with: tail -f /tmp/ollama-mistral-pull.log"
else
    echo ""
    echo "⏭️  Step 5b: Skipping Mistral download (already exists)"
fi

# 7. Test Ollama with a simple prompt
echo ""
echo "🧪 Step 6: Testing Ollama with Llama3..."
TEST_RESPONSE=$(curl -s http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Say hello in exactly 5 words",
  "stream": false
}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', 'ERROR')[:100])" 2>/dev/null || echo "Test failed")

if [ "$TEST_RESPONSE" != "Test failed" ] && [ "$TEST_RESPONSE" != "ERROR" ]; then
    echo "   ✅ Ollama test successful!"
    echo "   📝 Response: $TEST_RESPONSE"
else
    echo "   ⚠️  Ollama test failed or returned error"
fi

# 8. List available models
echo ""
echo "📦 Step 7: Available Ollama models:"
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
for model in data.get('models', []):
    name = model['name']
    size = model.get('size', 0) / (1024**3)
    print(f'   ✅ {name:20s} ({size:.2f} GB)')
" 2>/dev/null || echo "   ⚠️  Could not list models"

# 9. Update ChatterFix environment for Ollama
echo ""
echo "🔧 Step 8: Configuring ChatterFix environment..."
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

if [ ! -f .env ]; then
    echo "   Creating new .env file..."
    cat > .env << 'ENVEOF'
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434
USE_OLLAMA=true

# Add your API keys here
OPENAI_API_KEY=your_openai_key_here
XAI_API_KEY=your_xai_key_here
ENVEOF
    echo "   ✅ Created .env with Ollama config"
else
    # Update existing .env
    if ! grep -q "OLLAMA_HOST" .env; then
        echo "" >> .env
        echo "# Ollama Configuration" >> .env
        echo "OLLAMA_HOST=http://localhost:11434" >> .env
        echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env
        echo "USE_OLLAMA=true" >> .env
        echo "   ✅ Added Ollama config to existing .env"
    else
        echo "   ✅ Ollama config already in .env"
    fi
fi

# 10. Restart ChatterFix to load new Ollama integration
echo ""
echo "🔄 Step 9: Restarting ChatterFix with Ollama integration..."
pkill -f "python3 app.py" || true
sleep 2

export OLLAMA_HOST=http://localhost:11434
export OLLAMA_BASE_URL=http://localhost:11434
export USE_OLLAMA=true

# Load .env
set -a
source .env 2>/dev/null || true
set +a

nohup python3 app.py > /tmp/chatterfix.log 2>&1 &
CHATTERFIX_PID=$!
echo "   ⏳ Waiting for ChatterFix to start..."
sleep 8

if ps -p $CHATTERFIX_PID > /dev/null; then
    echo "   ✅ ChatterFix restarted (PID: $CHATTERFIX_PID)"
else
    echo "   ⚠️  ChatterFix may have crashed. Check logs:"
    tail -20 /tmp/chatterfix.log
fi

# 11. Test the integration
echo ""
echo "🧪 Step 10: Testing Fix It Fred with Ollama..."
sleep 3

FRED_TEST=$(curl -s -X POST http://localhost:8080/api/ollama/status 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        models = data.get('available_models', [])
        print(f'SUCCESS: {len(models)} models available - {models}')
    else:
        print(f'INACTIVE: {data.get(\"message\", \"Unknown error\")}')
except:
    print('ERROR: Could not parse response')
" || echo "Connection failed")

echo "   📊 Status: $FRED_TEST"

# 12. Final summary
echo ""
echo "======================================"
echo "✅ OLLAMA SETUP COMPLETE"
echo "======================================"
echo ""
echo "📋 Summary:"
echo "   • Ollama Service: http://localhost:11434"
echo "   • ChatterFix CMMS: http://35.237.149.25:8080"
echo "   • Fix It Fred (Ollama): http://35.237.149.25:8080/api/fix-it-fred/troubleshoot-ollama"
echo "   • Ollama Status: http://35.237.149.25:8080/api/ollama/status"
echo ""
echo "🔧 Management Commands:"
echo "   • Check Ollama: systemctl status ollama"
echo "   • Ollama logs: journalctl -u ollama -f"
echo "   • ChatterFix logs: tail -f /tmp/chatterfix.log"
echo "   • List models: ollama list"
echo "   • Pull model: ollama pull <model-name>"
echo ""
echo "🧪 Test Commands:"
echo '   curl http://35.237.149.25:8080/api/ollama/status'
echo '   curl -X POST http://35.237.149.25:8080/api/fix-it-fred/troubleshoot-ollama -H "Content-Type: application/json" -d '"'"'{"equipment":"HVAC","issue_description":"loud noise"}'"'"''
echo ""
echo "✨ Setup completed at $(date)"
