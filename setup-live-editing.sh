#!/bin/bash

# 🔥 Set up Fix It Fred Live Editing System
# Allows real-time code changes without full deployments

set -e

VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
PROJECT="fredfix"

echo "🔥 Setting up Fix It Fred Live Editing System..."
echo "================================================"

# Create the live editing system deployment
cat > /tmp/setup-live-editing.sh << 'EOFSETUP'
#!/bin/bash

echo "🔥 Installing Fix It Fred Live Editing System..."

# Create live editing directory structure
sudo mkdir -p /opt/chatterfix-live
sudo mkdir -p /opt/chatterfix-live/backups
sudo mkdir -p /opt/chatterfix-live/patches
sudo chown -R yoyofred_gringosgambit_com:yoyofred_gringosgambit_com /opt/chatterfix-live

# Install development tools
echo "📦 Installing development tools..."
python3 -m pip install watchdog

# Create live editing API script
cat > /opt/chatterfix-live/live_editor.py << 'EOFEDITOR'
#!/usr/bin/env python3
"""
Fix It Fred Live Editor API
Allows real-time code editing without full deployments
"""

import os
import json
import subprocess
import shutil
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Fix It Fred Live Editor", version="1.0.0")

class CodeEdit(BaseModel):
    file_path: str
    old_content: str
    new_content: str
    description: str

class FileContent(BaseModel):
    content: str

# Configuration
APP_DIR = "/opt/chatterfix-unified"
BACKUP_DIR = "/opt/chatterfix-live/backups"
SERVICE_NAME = "chatterfix"

def backup_file(file_path: str) -> str:
    """Create backup of file before editing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{os.path.basename(file_path)}_{timestamp}.backup"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
        return backup_path
    return ""

def reload_service():
    """Reload the ChatterFix service"""
    try:
        # For hot reload, we use SIGHUP to reload without full restart
        subprocess.run(["sudo", "systemctl", "reload", SERVICE_NAME], check=True)
        return True
    except:
        try:
            # Fallback to restart if reload doesn't work
            subprocess.run(["sudo", "systemctl", "restart", SERVICE_NAME], check=True)
            return True
        except:
            return False

@app.get("/")
async def root():
    return {"message": "Fix It Fred Live Editor API", "status": "active"}

@app.get("/files/{file_name}")
async def get_file_content(file_name: str):
    """Get current content of a file"""
    file_path = os.path.join(APP_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"file_path": file_path, "content": content, "size": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.post("/edit/{file_name}")
async def edit_file(file_name: str, edit: CodeEdit):
    """Edit a file with hot reload"""
    file_path = os.path.join(APP_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create backup
    backup_path = backup_file(file_path)
    
    try:
        # Read current content
        with open(file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # Verify old content matches (safety check)
        if edit.old_content not in current_content:
            return {
                "success": False, 
                "error": "Old content not found in file - file may have been modified",
                "backup": backup_path
            }
        
        # Apply the edit
        new_content = current_content.replace(edit.old_content, edit.new_content)
        
        # Write the new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Hot reload the service
        reload_success = reload_service()
        
        return {
            "success": True,
            "message": f"File edited successfully: {edit.description}",
            "file_path": file_path,
            "backup": backup_path,
            "reloaded": reload_success,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Restore from backup if edit failed
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
        
        raise HTTPException(status_code=500, detail=f"Edit failed: {str(e)}")

@app.post("/quick-edit/{file_name}")
async def quick_edit(file_name: str, content: FileContent):
    """Quick edit - replace entire file content"""
    file_path = os.path.join(APP_DIR, file_name)
    
    # Create backup
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.content)
        
        reload_success = reload_service()
        
        return {
            "success": True,
            "message": f"File replaced successfully",
            "file_path": file_path,
            "backup": backup_path,
            "reloaded": reload_success,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Restore from backup if edit failed
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
        
        raise HTTPException(status_code=500, detail=f"Quick edit failed: {str(e)}")

@app.get("/backups")
async def list_backups():
    """List available backups"""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for file in os.listdir(BACKUP_DIR):
            if file.endswith('.backup'):
                path = os.path.join(BACKUP_DIR, file)
                stat = os.stat(path)
                backups.append({
                    "name": file,
                    "path": path,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
    return {"backups": sorted(backups, key=lambda x: x['created'], reverse=True)}

@app.post("/restore/{backup_name}")
async def restore_backup(backup_name: str):
    """Restore a file from backup"""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Extract original filename from backup name
    original_name = backup_name.split('_')[0] + '.py'  # Assume .py for now
    original_path = os.path.join(APP_DIR, original_name)
    
    try:
        shutil.copy2(backup_path, original_path)
        reload_success = reload_service()
        
        return {
            "success": True,
            "message": f"Restored from backup: {backup_name}",
            "original_path": original_path,
            "reloaded": reload_success
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
EOFEDITOR

# Make the editor executable
chmod +x /opt/chatterfix-live/live_editor.py

# Create systemd service for live editor
sudo tee /etc/systemd/system/chatterfix-live-editor.service > /dev/null << 'EOFSERVICE'
[Unit]
Description=Fix It Fred Live Editor API
After=network.target

[Service]
User=yoyofred_gringosgambit_com
Group=yoyofred_gringosgambit_com
WorkingDirectory=/opt/chatterfix-live
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 live_editor.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOFSERVICE

# Create GitHub sync script for selective changes
cat > /opt/chatterfix-live/sync_to_github.py << 'EOFSYNC'
#!/usr/bin/env python3
"""
Fix It Fred GitHub Sync
Syncs only specific changes to GitHub without full deployment
"""

import os
import subprocess
import json
from datetime import datetime

def sync_file_to_github(file_path: str, commit_message: str):
    """Sync a specific file to GitHub"""
    try:
        # Navigate to repo directory
        repo_dir = "/opt/chatterfix-repo"  # We'll clone repo here
        
        if not os.path.exists(repo_dir):
            # Clone repo if it doesn't exist
            subprocess.run([
                "git", "clone", 
                "https://github.com/TheGringo-ai/Chatterfix.git", 
                repo_dir
            ], check=True)
        
        os.chdir(repo_dir)
        
        # Pull latest changes
        subprocess.run(["git", "pull", "origin", "main"], check=True)
        
        # Copy the modified file to the repo
        relative_path = os.path.relpath(file_path, "/opt/chatterfix-unified")
        target_path = os.path.join(repo_dir, "vm-deployment", relative_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Copy file
        subprocess.run(["cp", file_path, target_path], check=True)
        
        # Git add, commit, push
        subprocess.run(["git", "add", target_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        return {"success": True, "message": "Synced to GitHub"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        result = sync_file_to_github(sys.argv[1], sys.argv[2])
        print(json.dumps(result))
EOFSYNC

chmod +x /opt/chatterfix-live/sync_to_github.py

# Start the live editor service
sudo systemctl daemon-reload
sudo systemctl enable chatterfix-live-editor
sudo systemctl start chatterfix-live-editor

# Update firewall for live editor port
sudo ufw allow 8001

echo "✅ Fix It Fred Live Editor installed!"
echo "🔗 Live Editor API: http://35.237.149.25:8001"
echo "📝 Edit files: POST /edit/{filename}"
echo "📁 Get files: GET /files/{filename}"  
echo "💾 Backups: GET /backups"
echo "🔄 Hot reload: Automatic on edits"

EOFSETUP

# Deploy to VM
echo "📤 Deploying live editing system to VM..."
gcloud compute scp /tmp/setup-live-editing.sh $VM_NAME:~/setup-live-editing.sh --zone=$ZONE --project=$PROJECT

echo "🚀 Installing live editing system on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="chmod +x ~/setup-live-editing.sh && sudo ~/setup-live-editing.sh"

echo ""
echo "🎉 FIX IT FRED LIVE EDITING SYSTEM READY!"
echo "========================================"
echo "✅ Edit files in real-time without full deployment"
echo "✅ Hot reload - changes apply instantly" 
echo "✅ Automatic backups before changes"
echo "✅ GitHub sync for specific files only"
echo ""
echo "🔗 Live Editor API: http://35.237.149.25:8001"
echo "📖 API Docs: http://35.237.149.25:8001/docs"
echo ""
echo "Fix It Fred can now edit code live!"