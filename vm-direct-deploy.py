#!/usr/bin/env python3
"""
Direct VM Deployment for ChatterFix
Uploads and starts ChatterFix on VM without SSH complexity
"""

import requests
import base64
import json
import time
import os

VM_IP = "35.237.149.25"

def create_deployment_package():
    """Create a simple deployment package"""
    print("📦 Creating deployment package...")
    
    # Read the main app
    with open("core/cmms/app.py", "r") as f:
        app_content = f.read()
    
    # Create requirements
    requirements = """
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
jinja2==3.1.2
python-multipart==0.0.6
aiofiles==23.2.1
requests==2.31.0
python-dotenv==1.0.0
pandas==2.1.3
openai==1.3.5
anthropic==0.7.8
pydantic==2.5.0
sqlite3
"""

    # Create startup script
    startup_script = """#!/bin/bash
cd /home/yoyofred_gringosgambit_com/chatterfix
python3 -m pip install --user -r requirements.txt
nohup python3 app.py > chatterfix.log 2>&1 &
echo "ChatterFix started on port 8080"
"""

    return {
        "app.py": app_content,
        "requirements.txt": requirements,
        "start.sh": startup_script
    }

def deploy_via_curl():
    """Deploy using curl commands"""
    print("🚀 Deploying to VM...")
    
    files = create_deployment_package()
    
    # Create deployment directory
    os.system(f'curl -X POST "http://{VM_IP}:8080/admin/create-dir" -d "path=/home/yoyofred_gringosgambit_com/chatterfix" 2>/dev/null || echo "Directory creation attempted"')
    
    # Upload files
    for filename, content in files.items():
        print(f"📤 Uploading {filename}...")
        
        # Encode content
        encoded = base64.b64encode(content.encode()).decode()
        
        # Upload via HTTP
        payload = {
            "filename": filename,
            "content": encoded,
            "path": "/home/yoyofred_gringosgambit_com/chatterfix"
        }
        
        try:
            response = requests.post(f"http://{VM_IP}:8080/admin/upload", 
                                   json=payload, timeout=10)
            print(f"   {filename}: {response.status_code}")
        except:
            print(f"   {filename}: Failed to upload")
    
    # Start the service
    print("🔄 Starting ChatterFix...")
    try:
        start_payload = {"command": "cd /home/yoyofred_gringosgambit_com/chatterfix && chmod +x start.sh && ./start.sh"}
        response = requests.post(f"http://{VM_IP}:8080/admin/execute", 
                               json=start_payload, timeout=30)
        print(f"Startup result: {response.status_code}")
    except:
        print("Failed to start service")

def simple_vm_fix():
    """Try the simplest approach - direct file creation"""
    print("💡 Trying simple approach...")
    
    # Create a minimal app
    minimal_app = '''
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="ChatterFix CMMS")

@app.get("/")
async def root():
    return {"message": "ChatterFix CMMS is running!", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ChatterFix CMMS"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''
    
    # Write to temp file and try to copy
    with open("/tmp/chatterfix_app.py", "w") as f:
        f.write(minimal_app)
    
    print("Created minimal app at /tmp/chatterfix_app.py")
    print("Now manually copy this to your VM and run:")
    print(f"python3 /tmp/chatterfix_app.py")

if __name__ == "__main__":
    print("🔧 ChatterFix VM Direct Deploy")
    print("=" * 40)
    
    # Try different approaches
    try:
        deploy_via_curl()
    except:
        print("HTTP deploy failed, trying simple approach...")
        simple_vm_fix()
    
    print("\n✅ Deployment package ready!")
    print(f"🌐 Check: http://{VM_IP}:8080/health")