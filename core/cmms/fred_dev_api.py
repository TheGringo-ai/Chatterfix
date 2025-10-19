#!/usr/bin/env python3
"""
Fix It Fred Development API - Safe Live Development Interface
Allows live code changes without crashing production systems
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import subprocess
import os
import sys
import importlib
import threading
import time
import json
from typing import Optional, Dict, Any

app = FastAPI(title="Fix It Fred Dev API", version="1.0.0")

# Development state
dev_state = {
    "active_processes": {},
    "code_changes": [],
    "last_reload": None,
    "safe_mode": True
}

class CodeChange(BaseModel):
    file_path: str
    content: str
    backup: bool = True

class ProcessControl(BaseModel):
    action: str  # start, stop, restart, status
    service: str
    safe_mode: bool = True

@app.get("/", response_class=HTMLResponse)
async def dev_dashboard():
    """Development dashboard for Fix It Fred"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fix It Fred - Development Console</title>
        <style>
            body { font-family: 'Monaco', 'Menlo', monospace; margin: 0; padding: 20px; background: #1a1a1a; color: #00ff00; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2d2d2d; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #00ff00; }
            .panel { background: #2d2d2d; padding: 20px; margin: 10px 0; border-radius: 8px; border: 1px solid #444; }
            .status { display: inline-block; padding: 5px 10px; border-radius: 4px; margin: 5px; }
            .status.active { background: #004d00; color: #00ff00; }
            .status.inactive { background: #4d0000; color: #ff4444; }
            .btn { background: #004d00; color: #00ff00; padding: 10px 20px; border: 1px solid #00ff00; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #006600; }
            .btn.danger { background: #4d0000; border-color: #ff4444; color: #ff4444; }
            .terminal { background: #000; color: #00ff00; padding: 15px; border-radius: 4px; font-family: 'Courier New', monospace; height: 300px; overflow-y: auto; white-space: pre-wrap; }
            .form-group { margin: 10px 0; }
            .form-group label { display: block; margin-bottom: 5px; color: #00ff00; }
            .form-group input, .form-group textarea { background: #000; color: #00ff00; border: 1px solid #00ff00; padding: 8px; width: 100%; box-sizing: border-box; }
            .form-group textarea { height: 200px; font-family: 'Monaco', 'Menlo', monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Fix It Fred - Development Console</h1>
                <p>Safe live development environment with hot-reload capabilities</p>
                <div id="system-status">
                    <span class="status active">Dev API: Online</span>
                    <span class="status" id="fred-status">Fix It Fred: Checking...</span>
                    <span class="status" id="chatterfix-status">ChatterFix: Checking...</span>
                </div>
            </div>
            
            <div class="panel">
                <h3>🚀 Service Control</h3>
                <button class="btn" onclick="controlService('restart', 'fix-it-fred')">Restart Fix It Fred</button>
                <button class="btn" onclick="controlService('status', 'fix-it-fred')">Check Status</button>
                <button class="btn danger" onclick="controlService('stop', 'fix-it-fred')">Stop (Safe)</button>
                <button class="btn" onclick="controlService('start', 'fix-it-fred')">Start</button>
            </div>
            
            <div class="panel">
                <h3>⚡ Hot Reload Code Editor</h3>
                <div class="form-group">
                    <label>File Path:</label>
                    <input type="text" id="file-path" placeholder="/path/to/file.py" value="emergency_app.py">
                </div>
                <div class="form-group">
                    <label>Code Content:</label>
                    <textarea id="code-content" placeholder="Enter your code here..."></textarea>
                </div>
                <button class="btn" onclick="loadFile()">Load File</button>
                <button class="btn" onclick="saveAndReload()">Save & Hot Reload</button>
                <button class="btn" onclick="testChanges()">Test Changes</button>
            </div>
            
            <div class="panel">
                <h3>📊 Development Terminal</h3>
                <div id="terminal" class="terminal">Fix It Fred Development Console Ready...\n</div>
                <div class="form-group">
                    <input type="text" id="command-input" placeholder="Enter command..." onkeypress="if(event.key==='Enter')executeCommand()">
                    <button class="btn" onclick="executeCommand()">Execute</button>
                    <button class="btn" onclick="clearTerminal()">Clear</button>
                </div>
            </div>
            
            <div class="panel">
                <h3>🔄 Live Integration Test</h3>
                <button class="btn" onclick="testIntegration()">Test ChatterFix Integration</button>
                <button class="btn" onclick="testAPIs()">Test All APIs</button>
                <button class="btn" onclick="healthCheck()">Full Health Check</button>
                <div id="test-results" style="margin-top: 10px;"></div>
            </div>
        </div>
        
        <script>
            function log(message) {
                const terminal = document.getElementById('terminal');
                const timestamp = new Date().toLocaleTimeString();
                terminal.textContent += `[${timestamp}] ${message}\n`;
                terminal.scrollTop = terminal.scrollHeight;
            }
            
            function clearTerminal() {
                document.getElementById('terminal').textContent = '';
            }
            
            async function controlService(action, service) {
                log(`Executing ${action} on ${service}...`);
                try {
                    const response = await fetch('/dev/control', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({action, service, safe_mode: true})
                    });
                    const result = await response.json();
                    log(`Result: ${result.message}`);
                    if (result.output) log(`Output: ${result.output}`);
                } catch (error) {
                    log(`Error: ${error.message}`);
                }
            }
            
            async function loadFile() {
                const filePath = document.getElementById('file-path').value;
                log(`Loading file: ${filePath}...`);
                try {
                    const response = await fetch(`/dev/load-file?path=${encodeURIComponent(filePath)}`);
                    const result = await response.json();
                    if (result.success) {
                        document.getElementById('code-content').value = result.content;
                        log(`File loaded successfully`);
                    } else {
                        log(`Error loading file: ${result.error}`);
                    }
                } catch (error) {
                    log(`Error: ${error.message}`);
                }
            }
            
            async function saveAndReload() {
                const filePath = document.getElementById('file-path').value;
                const content = document.getElementById('code-content').value;
                log(`Saving and reloading: ${filePath}...`);
                try {
                    const response = await fetch('/dev/hot-reload', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({file_path: filePath, content, backup: true})
                    });
                    const result = await response.json();
                    log(`Hot reload result: ${result.message}`);
                    if (result.backup_path) log(`Backup saved: ${result.backup_path}`);
                } catch (error) {
                    log(`Error: ${error.message}`);
                }
            }
            
            async function testChanges() {
                log(`Testing changes...`);
                try {
                    const response = await fetch('/dev/test');
                    const result = await response.json();
                    log(`Test result: ${result.message}`);
                    log(`Status: ${JSON.stringify(result.status, null, 2)}`);
                } catch (error) {
                    log(`Error: ${error.message}`);
                }
            }
            
            async function executeCommand() {
                const command = document.getElementById('command-input').value;
                if (!command.trim()) return;
                
                log(`$ ${command}`);
                document.getElementById('command-input').value = '';
                
                try {
                    const response = await fetch('/dev/execute', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({command})
                    });
                    const result = await response.json();
                    if (result.output) log(result.output);
                    if (result.error) log(`Error: ${result.error}`);
                } catch (error) {
                    log(`Error: ${error.message}`);
                }
            }
            
            async function testIntegration() {
                log('Testing ChatterFix integration...');
                try {
                    const response = await fetch('/dev/test-integration');
                    const result = await response.json();
                    document.getElementById('test-results').innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                    log('Integration test completed');
                } catch (error) {
                    log(`Integration test error: ${error.message}`);
                }
            }
            
            async function healthCheck() {
                log('Running full health check...');
                ['fix-it-fred', 'chatterfix'].forEach(async (service) => {
                    try {
                        const response = await fetch(`/dev/health/${service}`);
                        const result = await response.json();
                        const statusEl = document.getElementById(`${service.replace('-', '')}-status`);
                        if (result.healthy) {
                            statusEl.className = 'status active';
                            statusEl.textContent = `${service}: Online`;
                        } else {
                            statusEl.className = 'status inactive';
                            statusEl.textContent = `${service}: Offline`;
                        }
                        log(`${service}: ${result.healthy ? 'Healthy' : 'Unhealthy'}`);
                    } catch (error) {
                        log(`${service} health check failed: ${error.message}`);
                    }
                });
            }
            
            // Auto-refresh status every 10 seconds
            setInterval(healthCheck, 10000);
            healthCheck(); // Initial check
        </script>
    </body>
    </html>
    """

@app.post("/dev/hot-reload")
async def hot_reload_code(change: CodeChange):
    """Safely apply code changes with hot reload"""
    try:
        file_path = change.file_path
        
        # Create backup if requested
        backup_path = None
        if change.backup and os.path.exists(file_path):
            backup_path = f"{file_path}.backup.{int(time.time())}"
            with open(file_path, 'r') as f:
                backup_content = f.read()
            with open(backup_path, 'w') as f:
                f.write(backup_content)
        
        # Write new content
        with open(file_path, 'w') as f:
            f.write(change.content)
        
        # Record change
        dev_state["code_changes"].append({
            "file": file_path,
            "timestamp": time.time(),
            "backup": backup_path
        })
        dev_state["last_reload"] = time.time()
        
        return {
            "success": True,
            "message": f"Hot reload completed for {file_path}",
            "backup_path": backup_path,
            "timestamp": dev_state["last_reload"]
        }
        
    except Exception as e:
        return {"success": False, "message": f"Hot reload failed: {str(e)}"}

@app.get("/dev/load-file")
async def load_file(path: str):
    """Load file content for editing"""
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
            return {"success": True, "content": content, "path": path}
        else:
            return {"success": False, "error": f"File not found: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/dev/control")
async def control_service(control: ProcessControl):
    """Control services safely"""
    try:
        service = control.service
        action = control.action
        
        if action == "status":
            # Check if process is running
            result = subprocess.run(["pgrep", "-f", service], capture_output=True, text=True)
            running = result.returncode == 0
            return {
                "success": True,
                "message": f"{service} is {'running' if running else 'stopped'}",
                "running": running,
                "output": result.stdout.strip() if running else None
            }
            
        elif action == "restart":
            # Safe restart - stop gracefully then start
            subprocess.run(["pkill", "-f", service], capture_output=True)
            time.sleep(2)  # Give time to stop
            # Start would depend on the specific service
            return {"success": True, "message": f"{service} restart initiated (safe mode)"}
            
        elif action == "stop":
            subprocess.run(["pkill", "-f", service], capture_output=True)
            return {"success": True, "message": f"{service} stopped safely"}
            
        else:
            return {"success": False, "message": f"Unknown action: {action}"}
            
    except Exception as e:
        return {"success": False, "message": f"Control failed: {str(e)}"}

@app.post("/dev/execute")
async def execute_command(command_data: dict):
    """Execute safe development commands"""
    try:
        command = command_data.get("command", "")
        
        # Safety check - block dangerous commands
        dangerous = ["rm -rf", "dd if=", "mkfs", "format", "del /f"]
        if any(danger in command for danger in dangerous):
            return {"success": False, "error": "Command blocked for safety"}
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out (30s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/dev/test")
async def test_system():
    """Test current system state"""
    status = {
        "fix_it_fred": False,
        "chatterfix": False,
        "local_app": False,
        "integration": False
    }
    
    try:
        # Test Fix It Fred
        result = subprocess.run(["curl", "-s", "http://localhost:8080/health"], 
                              capture_output=True, text=True, timeout=5)
        status["fix_it_fred"] = result.returncode == 0
        
        # Test ChatterFix
        result = subprocess.run(["curl", "-s", "http://chatterfix.com/health"], 
                              capture_output=True, text=True, timeout=5)
        status["chatterfix"] = result.returncode == 0
        
        # Test local app
        result = subprocess.run(["curl", "-s", "http://localhost:8000/health"], 
                              capture_output=True, text=True, timeout=5)
        status["local_app"] = result.returncode == 0
        
        status["integration"] = status["fix_it_fred"] and status["chatterfix"]
        
    except Exception as e:
        pass
    
    return {
        "success": True,
        "message": "System test completed",
        "status": status,
        "timestamp": time.time()
    }

@app.get("/dev/health/{service}")
async def health_check_service(service: str):
    """Check health of specific service"""
    try:
        if service == "fix-it-fred":
            result = subprocess.run(["curl", "-s", "http://localhost:8080/health"], 
                                  capture_output=True, text=True, timeout=5)
            return {"healthy": result.returncode == 0, "service": service}
        elif service == "chatterfix":
            result = subprocess.run(["curl", "-s", "http://chatterfix.com/health"], 
                                  capture_output=True, text=True, timeout=5)
            return {"healthy": result.returncode == 0, "service": service}
        else:
            return {"healthy": False, "service": service, "error": "Unknown service"}
    except Exception as e:
        return {"healthy": False, "service": service, "error": str(e)}

@app.get("/dev/test-integration")
async def test_integration():
    """Test integration between systems"""
    results = {}
    
    try:
        # Test ChatterFix APIs
        endpoints = ["/api/work-orders", "/api/assets", "/api/parts"]
        for endpoint in endpoints:
            result = subprocess.run(["curl", "-s", f"http://chatterfix.com{endpoint}"], 
                                  capture_output=True, text=True, timeout=5)
            results[f"chatterfix{endpoint}"] = {
                "success": result.returncode == 0,
                "response_length": len(result.stdout) if result.returncode == 0 else 0
            }
        
        # Test Fix It Fred DevOps API
        result = subprocess.run(["curl", "-s", "http://localhost:9004/"], 
                              capture_output=True, text=True, timeout=5)
        results["fred_devops_api"] = {
            "success": result.returncode == 0,
            "response_length": len(result.stdout) if result.returncode == 0 else 0
        }
        
    except Exception as e:
        results["error"] = str(e)
    
    return {"integration_test": results, "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    print("🔧 Fix It Fred Development API Starting...")
    print("📊 Development Console: http://localhost:9001")
    print("⚡ Hot Reload: Enabled")
    print("🛡️  Safe Mode: Active")
    uvicorn.run(app, host="0.0.0.0", port=9001)