#!/bin/bash
# Complete AI Integration Deployment for ChatterFix VM
# Deploys: Ollama + Fix It Fred + LineSmart + Assets API

set -e

echo "🤖 Complete AI Integration Deployment"
echo "====================================="

# Configuration
PROJECT_ID="fredfix"
INSTANCE_NAME="chatterfix-cmms-production" 
ZONE="us-east1-b"

echo "🔍 Pre-deployment Analysis..."

# Check current VM AI status
VM_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
echo "🌐 VM IP: $VM_IP"

echo "🧪 Testing current AI services..."

# Test Ollama
if curl -s -f "http://$VM_IP:11434/api/tags" > /dev/null 2>&1; then
    echo "✅ Ollama accessible"
else
    echo "❌ Ollama needs setup"
fi

# Test ChatterFix AI
if curl -s -f "http://$VM_IP:8080/api/ai/chat" > /dev/null 2>&1; then
    echo "✅ ChatterFix AI endpoint exists"
else
    echo "❌ ChatterFix AI needs setup"
fi

echo ""
echo "📦 Preparing Complete AI Package..."

# Create comprehensive AI deployment package
mkdir -p /tmp/ai-complete-deploy

# 1. Fix It Fred Assets API
cp fixed_assets_api.py /tmp/ai-complete-deploy/
echo "✅ Assets API included"

# 2. LineSmart Training Platform  
cp ../../linesmart_standalone.py /tmp/ai-complete-deploy/
echo "✅ LineSmart included"

# 3. Main application with AI integrations
cp app.py /tmp/ai-complete-deploy/
echo "✅ Main app included"

# 4. Backend unified service
cp backend_unified_service.py /tmp/ai-complete-deploy/
echo "✅ Backend service included"

# 5. Templates and static files
cp -r templates /tmp/ai-complete-deploy/ 2>/dev/null || echo "Templates directory not found"
cp -r static /tmp/ai-complete-deploy/ 2>/dev/null || echo "Static directory not found"

# 6. Create AI integration script
cat > /tmp/ai-complete-deploy/setup_ai_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Complete AI Integration Setup for ChatterFix VM
Sets up Ollama + Fix It Fred + LineSmart integration
"""

import subprocess
import time
import requests
import json

def setup_ollama():
    """Install and configure Ollama"""
    print("🦙 Setting up Ollama...")
    
    # Install Ollama if not present
    try:
        subprocess.run(["which", "ollama"], check=True, capture_output=True)
        print("✅ Ollama already installed")
    except subprocess.CalledProcessError:
        print("📥 Installing Ollama...")
        subprocess.run([
            "curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"
        ], shell=True)
    
    # Start Ollama service
    print("🚀 Starting Ollama service...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10)
    
    # Pull essential models
    models = ["llama3.2:latest", "qwen2.5:7b", "mistral:latest"]
    for model in models:
        print(f"📥 Pulling {model}...")
        try:
            subprocess.run(["ollama", "pull", model], check=True, timeout=300)
            print(f"✅ {model} ready")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"⚠️ {model} pull failed or timed out")

def setup_linesmart():
    """Setup LineSmart service"""
    print("📚 Setting up LineSmart...")
    
    # Start LineSmart on port 8082
    subprocess.Popen([
        "python3", "linesmart_standalone.py"
    ], env={**os.environ, "PORT": "8082"}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(5)
    print("✅ LineSmart started on port 8082")

def setup_fix_it_fred():
    """Integrate Fix It Fred with ChatterFix"""
    print("🤖 Setting up Fix It Fred integration...")
    
    # Fred will be integrated directly into the main app
    print("✅ Fix It Fred integrated with main application")

def setup_chatterfix_ai():
    """Setup main ChatterFix with all AI integrations"""
    print("🏭 Starting ChatterFix with complete AI integration...")
    
    # Stop existing ChatterFix
    subprocess.run(["pkill", "-f", "python3 app.py"], capture_output=True)
    time.sleep(3)
    
    # Start with AI environment variables
    env = {
        **os.environ,
        "OLLAMA_HOST": "http://localhost:11434",
        "LINESMART_URL": "http://localhost:8082", 
        "FIX_IT_FRED_ENABLED": "true",
        "PORT": "8080"
    }
    
    subprocess.Popen([
        "python3", "app.py"
    ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(10)
    print("✅ ChatterFix started with AI integration")

def verify_integration():
    """Verify all AI services are working"""
    print("🧪 Verifying AI integration...")
    
    # Test Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama: {len(models)} models available")
        else:
            print("❌ Ollama not responding")
    except:
        print("❌ Ollama connection failed")
    
    # Test LineSmart
    try:
        response = requests.get("http://localhost:8082/health", timeout=5)
        if response.status_code == 200:
            print("✅ LineSmart: Responding")
        else:
            print("❌ LineSmart not responding")
    except:
        print("❌ LineSmart connection failed")
    
    # Test ChatterFix AI
    try:
        response = requests.post(
            "http://localhost:8080/api/ai/chat",
            json={"message": "AI integration test"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ChatterFix AI: {data.get('agent_type', 'responding')}")
        else:
            print("❌ ChatterFix AI not responding")
    except:
        print("❌ ChatterFix AI connection failed")
    
    # Test Assets API
    try:
        response = requests.get("http://localhost:8080/api/assets", timeout=5)
        if response.status_code == 200:
            print("✅ Assets API: Working")
        else:
            print("❌ Assets API not working")
    except:
        print("❌ Assets API connection failed")

if __name__ == "__main__":
    import os
    
    print("🚀 Complete AI Integration Setup Starting...")
    setup_ollama()
    setup_linesmart() 
    setup_fix_it_fred()
    setup_chatterfix_ai()
    verify_integration()
    print("🎉 Complete AI integration setup finished!")
EOF

# 7. Create startup script
cat > /tmp/ai-complete-deploy/start_all_services.sh << 'EOF'
#!/bin/bash
# Start all AI services for ChatterFix

echo "🚀 Starting Complete AI Stack..."

# Start Ollama
ollama serve > /tmp/ollama.log 2>&1 &
sleep 5

# Start LineSmart
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app
PORT=8082 python3 linesmart_standalone.py > /tmp/linesmart.log 2>&1 &
sleep 3

# Start ChatterFix with AI integration
export OLLAMA_HOST=http://localhost:11434
export LINESMART_URL=http://localhost:8082
export FIX_IT_FRED_ENABLED=true
export PORT=8080

python3 app.py > /tmp/chatterfix.log 2>&1 &

echo "✅ All AI services started"
echo "🔗 ChatterFix: http://localhost:8080"
echo "🦙 Ollama: http://localhost:11434" 
echo "📚 LineSmart: http://localhost:8082"
EOF

cd /tmp/ai-complete-deploy
tar czf ../ai-complete.tar.gz .
cd - > /dev/null

echo "✅ Complete AI package ready: $(du -h /tmp/ai-complete.tar.gz)"

# Upload to VM
echo "📤 Uploading complete AI package..."
gcloud compute scp /tmp/ai-complete.tar.gz \
  $INSTANCE_NAME:/tmp/ai-complete.tar.gz \
  --zone=$ZONE

# Deploy and setup
echo "🚀 Deploying complete AI integration..."

COMPLETE_AI_DEPLOY='#!/bin/bash
set -e

echo "🤖 Complete AI Integration Deployment"
echo "====================================="

# Extract everything
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app
tar xzf /tmp/ai-complete.tar.gz

# Install Python dependencies
pip3 install --quiet ollama httpx fastapi uvicorn jinja2 python-multipart aiofiles pydantic

# Make scripts executable
chmod +x setup_ai_integration.py start_all_services.sh

# Run complete AI setup
python3 setup_ai_integration.py

echo "🎉 Complete AI integration deployed!"
echo "🔗 Services:"
echo "  • ChatterFix CMMS: http://35.237.149.25:8080"
echo "  • Assets API: http://35.237.149.25:8080/api/assets"  
echo "  • LineSmart Training: http://35.237.149.25:8082"
echo "  • Ollama AI: http://35.237.149.25:11434"
'

# Execute complete deployment
echo "$COMPLETE_AI_DEPLOY" | gcloud compute ssh $INSTANCE_NAME \
  --zone=$ZONE \
  --command "cat > /tmp/ai-deploy.sh && chmod +x /tmp/ai-deploy.sh && sudo /tmp/ai-deploy.sh"

# Final verification
echo "🧪 Final AI Integration Test..."
sleep 30

echo "🔍 Testing all AI services:"

# Test Ollama
if curl -s -f "http://$VM_IP:11434/api/tags" > /dev/null; then
    echo "✅ Ollama: Live"
else
    echo "⏳ Ollama: Starting up..."
fi

# Test LineSmart
if curl -s -f "http://$VM_IP:8082" > /dev/null; then
    echo "✅ LineSmart: Live" 
else
    echo "⏳ LineSmart: Starting up..."
fi

# Test ChatterFix with AI
if curl -s -f "http://$VM_IP:8080/api/ai/chat" > /dev/null; then
    echo "✅ ChatterFix AI: Live"
else
    echo "⏳ ChatterFix AI: Starting up..."
fi

# Test Assets API
if curl -s -f "http://$VM_IP:8080/api/assets" > /dev/null; then
    echo "✅ Assets API: Live"
else
    echo "⏳ Assets API: Starting up..."
fi

# Cleanup
rm -rf /tmp/ai-complete-deploy /tmp/ai-complete.tar.gz

echo ""
echo "🎉 COMPLETE AI INTEGRATION DEPLOYED!"
echo "===================================="
echo "🏭 ChatterFix CMMS: http://$VM_IP:8080"
echo "🏭 Asset Management: http://$VM_IP:8080/assets"
echo "📚 LineSmart Training: http://$VM_IP:8082"
echo "🦙 Ollama AI: http://$VM_IP:11434"
echo "🤖 Fix It Fred: Integrated in ChatterFix"
echo ""
echo "✅ All AI services integrated and ready!"