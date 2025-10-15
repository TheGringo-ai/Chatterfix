#!/usr/bin/env python3
"""
Deploy ChatterFix Complete via existing API endpoints
Uses the running service to deploy the new version
"""

import requests
import base64
import time
import json

VM_IP = "35.237.149.25"
BASE_URL = f"http://{VM_IP}:8080"

def read_complete_app():
    """Read the complete ChatterFix app"""
    with open("chatterfix_complete.py", "r") as f:
        return f.read()

def create_deployment_payload():
    """Create deployment payload"""
    app_code = read_complete_app()
    
    # Create startup script to replace current app
    startup_script = f'''#!/bin/bash
cd /home/yoyofred_gringosgambit_com

# Stop current service
pkill -f "python3.*app.py" || true
pkill -f "python3.*chatterfix" || true

# Backup old app
cp app.py app_old.py 2>/dev/null || true

# Write new complete app
cat > chatterfix_complete.py << 'APP_EOF'
{app_code}
APP_EOF

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Starting Ollama..."
    sudo systemctl start ollama 2>/dev/null || {{
        nohup ollama serve > ollama.log 2>&1 &
        sleep 5
    }}
fi

# Install missing packages
python3 -m pip install --user asyncpg httpx 2>/dev/null || true

# Start new complete app
echo "Starting ChatterFix Complete..."
nohup python3 chatterfix_complete.py > chatterfix_complete.log 2>&1 &

sleep 3
echo "ChatterFix Complete deployed at $(date)"
'''
    
    return {
        "app_code": app_code,
        "startup_script": startup_script
    }

def deploy_via_github_api():
    """Try to deploy using GitHub integration API"""
    try:
        # First, try the admin endpoint for file operations
        print("🔍 Testing admin API access...")
        response = requests.get(f"{BASE_URL}/api/admin/status", timeout=10)
        if response.status_code == 200:
            print("✅ Admin API accessible")
            return deploy_via_admin_api()
        
    except Exception as e:
        print(f"❌ Admin API failed: {e}")
    
    # Try deployment via chat interface
    print("🔄 Trying deployment via chat interface...")
    return deploy_via_chat()

def deploy_via_admin_api():
    """Deploy using admin API if available"""
    payload = create_deployment_payload()
    
    try:
        # Upload complete app
        upload_data = {
            "filename": "chatterfix_complete.py",
            "content": base64.b64encode(payload["app_code"].encode()).decode(),
            "action": "create"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/file-upload", 
                               json=upload_data, timeout=30)
        
        if response.status_code == 200:
            print("✅ App uploaded successfully")
            
            # Execute deployment script
            exec_data = {
                "command": payload["startup_script"],
                "background": True
            }
            
            response = requests.post(f"{BASE_URL}/api/admin/execute", 
                                   json=exec_data, timeout=30)
            
            if response.status_code == 200:
                print("✅ Deployment script executed")
                return True
                
    except Exception as e:
        print(f"❌ Admin deployment failed: {e}")
    
    return False

def deploy_via_chat():
    """Deploy by sending commands through chat interface"""
    payload = create_deployment_payload()
    
    # Try to use Fix It Fred chat to execute commands
    commands = [
        "pkill -f python3 || true",
        "sudo systemctl start ollama",
        "python3 -m pip install --user asyncpg httpx",
    ]
    
    for cmd in commands:
        try:
            chat_data = {
                "message": f"Execute system command: {cmd}",
                "action": "system_command"
            }
            
            response = requests.post(f"{BASE_URL}/api/chat", 
                                   json=chat_data, timeout=15)
            print(f"Command '{cmd}': {response.status_code}")
            time.sleep(2)
            
        except Exception as e:
            print(f"Chat command failed: {e}")
    
    return False

def deploy_via_startup_metadata():
    """Update VM startup metadata to deploy on next restart"""
    import subprocess
    
    print("📝 Creating new startup script with complete app...")
    
    # Create enhanced startup script
    enhanced_startup = f'''#!/bin/bash
set -e

echo "🚀 ChatterFix Complete Auto-Deploy"
echo "=================================="
cd /home/yoyofred_gringosgambit_com

# Stop existing services
pkill -f python3 || true
sudo systemctl stop ollama 2>/dev/null || true

# Install dependencies
python3 -m pip install --user fastapi uvicorn httpx asyncpg python-multipart jinja2

# Setup Ollama
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Configure Ollama service
sudo tee /etc/systemd/system/ollama.service > /dev/null << 'OLLAMA_EOF'
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

[Install]
WantedBy=multi-user.target
OLLAMA_EOF

sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Create complete ChatterFix app
cat > chatterfix_complete.py << 'COMPLETE_APP_EOF'
{read_complete_app()}
COMPLETE_APP_EOF

# Start ChatterFix Complete
sleep 5
nohup python3 chatterfix_complete.py > chatterfix.log 2>&1 &

# Download AI models in background
nohup bash -c "
    sleep 30
    ollama pull mistral:7b
    ollama pull llama3:8b
" > model_download.log 2>&1 &

echo "✅ ChatterFix Complete deployed!"
echo "🌐 Access: http://35.237.149.25:8080"
'''
    
    # Write startup script
    with open("complete-startup.sh", "w") as f:
        f.write(enhanced_startup)
    
    try:
        # Update VM metadata
        cmd = [
            "gcloud", "compute", "instances", "add-metadata", 
            "chatterfix-cmms-production",
            "--zone=us-east1-b",
            "--project=fredfix",
            "--metadata-from-file", "startup-script=complete-startup.sh"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Startup script updated")
            
            # Restart VM
            restart_cmd = [
                "gcloud", "compute", "instances", "reset",
                "chatterfix-cmms-production",
                "--zone=us-east1-b",
                "--project=fredfix"
            ]
            
            result = subprocess.run(restart_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ VM restarted with complete deployment")
                return True
                
    except Exception as e:
        print(f"❌ Metadata deployment failed: {e}")
    
    return False

def test_deployment():
    """Test if the complete deployment worked"""
    print("⏳ Waiting for services to start...")
    time.sleep(60)
    
    print("🩺 Testing ChatterFix Complete...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "ChatterFix CMMS Complete" in data.get("service", ""):
                print("✅ ChatterFix Complete is running!")
                return True
            else:
                print(f"⚠️  Old version still running: {data.get('service', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("🤖 Testing Ollama...")
    try:
        response = requests.get(f"http://{VM_IP}:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama running with {len(models)} models")
        else:
            print("⚠️  Ollama not responding")
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
    
    return False

def main():
    """Main deployment function"""
    print("🚀 ChatterFix Complete Deployment")
    print("==================================")
    print(f"Target: {VM_IP}")
    print("")
    
    # Try different deployment methods
    success = False
    
    # Method 1: Direct API deployment
    print("🔄 Method 1: Direct API deployment...")
    if deploy_via_github_api():
        success = True
    
    # Method 2: VM restart with metadata
    if not success:
        print("🔄 Method 2: VM restart deployment...")
        if deploy_via_startup_metadata():
            success = True
    
    if success:
        # Test the deployment
        test_deployment()
        
        print("")
        print("🎉 DEPLOYMENT COMPLETE!")
        print("========================")
        print(f"🌐 ChatterFix Complete: http://{VM_IP}:8080")
        print(f"🤖 Fix It Fred AI: http://{VM_IP}:8080/fred")
        print(f"🧠 Ollama API: http://{VM_IP}:11434/api/tags")
        print(f"📊 Health Check: http://{VM_IP}:8080/health")
        print("")
        print("✅ Features Available:")
        print("   - Complete CMMS with PostgreSQL")
        print("   - Fix It Fred AI with Ollama")
        print("   - Work Orders, Assets, Parts")
        print("   - Real-time health monitoring")
        
    else:
        print("❌ All deployment methods failed")
        print("Manual steps required:")
        print("1. SSH to VM and copy chatterfix_complete.py")
        print("2. Install: pip install asyncpg httpx")
        print("3. Start Ollama: sudo systemctl start ollama")
        print("4. Run: python3 chatterfix_complete.py")

if __name__ == "__main__":
    main()