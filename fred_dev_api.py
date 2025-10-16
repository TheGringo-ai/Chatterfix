#!/usr/bin/env python3
"""
Fix It Fred Development API Server
Provides web-based interface for Fred to control VM operations
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import asyncio
from fix_it_fred_dev_hooks import FixItFredDevHooks

app = FastAPI(
    title="Fix It Fred Development API",
    description="Direct VM control interface for Fix It Fred",
    version="1.0.0"
)

# Initialize Fred's dev hooks
fred = FixItFredDevHooks()

# Request models
class CommandRequest(BaseModel):
    command: str
    description: str = "Fred command"

class DeployRequest(BaseModel):
    local_file: str
    remote_path: str

class EditFileRequest(BaseModel):
    file_path: str
    content: str
    auto_deploy: bool = True

class GitRequest(BaseModel):
    operation: str
    message: str = "🤖 Fix It Fred: Automated operation"

class LiveEditRequest(BaseModel):
    file_path: str
    old_content: str
    new_content: str
    auto_deploy: bool = True

@app.get("/")
async def root():
    """Fred's development control panel"""
    return {
        "message": "🤖 Fix It Fred Development API",
        "vm_ip": fred.vm_ip,
        "status": "ready",
        "capabilities": [
            "execute_commands",
            "deploy_code", 
            "edit_files",
            "git_operations",
            "service_management",
            "auto_healing"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test VM connectivity
    test_result = fred.execute_vm_command("echo 'ping'", "Health check")
    
    return {
        "status": "healthy" if test_result["success"] else "degraded",
        "vm_connection": test_result["success"],
        "vm_ip": fred.vm_ip,
        "timestamp": fred.logger.handlers[0].formatter.formatTime(
            fred.logger.handlers[0].formatter.datefmt
        ) if fred.logger.handlers else "unknown"
    }

@app.post("/command")
async def execute_command(request: CommandRequest):
    """Execute command on VM"""
    result = fred.execute_vm_command(request.command, request.description)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return {
        "success": True,
        "output": result["output"],
        "command": request.command,
        "description": request.description
    }

@app.post("/deploy")
async def deploy_file(request: DeployRequest):
    """Deploy file to VM"""
    result = fred.deploy_code_to_vm(request.local_file, request.remote_path)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@app.post("/edit")
async def edit_file(request: EditFileRequest):
    """Edit file on VM"""
    result = fred.edit_file_on_vm(request.file_path, request.content)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
        
    # Auto-deploy if requested
    if request.auto_deploy:
        deploy_result = fred.full_deployment_cycle()
        return {
            "edit_result": result,
            "deployment_result": deploy_result
        }
    
    return result

@app.post("/git")
async def git_operation(request: GitRequest):
    """Perform git operation"""
    result = fred.git_operations(request.operation, request.message)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@app.post("/service/{service_name}/restart")
async def restart_service(service_name: str):
    """Restart a service"""
    result = fred.restart_service(service_name)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@app.get("/service/{service_name}/status")
async def service_status(service_name: str):
    """Check service status"""
    result = fred.check_service_status(service_name)
    
    return {
        "service": service_name,
        "active": "active" in result["output"] if result["success"] else False,
        "output": result["output"],
        "success": result["success"]
    }

@app.post("/deploy/full")
async def full_deployment(background_tasks: BackgroundTasks):
    """Full deployment cycle"""
    result = fred.full_deployment_cycle()
    return result

@app.post("/live-edit")
async def live_edit(request: LiveEditRequest):
    """Live edit with automatic deployment"""
    result = fred.live_code_edit(
        request.file_path,
        request.old_content, 
        request.new_content,
        request.auto_deploy
    )
    
    return result

@app.post("/heal")
async def auto_heal():
    """Monitor and heal services"""
    healing_actions = fred.monitor_and_heal()
    return {
        "healing_actions": healing_actions,
        "actions_taken": len(healing_actions)
    }

@app.get("/services/status")
async def all_services_status():
    """Get status of all services"""
    services = ["chatterfix-cmms", "nginx", "fix-it-fred-git"]
    status_results = {}
    
    for service in services:
        result = fred.check_service_status(service)
        status_results[service] = {
            "active": "active" in result["output"] if result["success"] else False,
            "status": result["output"].strip() if result["success"] else "unknown"
        }
        
    return status_results

@app.post("/services/restart-all")
async def restart_all_services():
    """Restart all ChatterFix services"""
    services = ["chatterfix-cmms", "nginx", "fix-it-fred-git"]
    restart_results = {}
    
    for service in services:
        result = fred.restart_service(service)
        restart_results[service] = result
        await asyncio.sleep(2)  # Wait between restarts
        
    return restart_results

@app.get("/vm/info")
async def vm_info():
    """Get VM information"""
    info_result = fred.execute_vm_command(
        "echo 'VM Info:' && uptime && df -h / && free -h", 
        "VM information"
    )
    
    return {
        "vm_ip": fred.vm_ip,
        "info": info_result["output"] if info_result["success"] else "Failed to get info",
        "success": info_result["success"]
    }

@app.websocket("/ws/logs")
async def websocket_logs(websocket):
    """WebSocket for real-time logs (future enhancement)"""
    await websocket.accept()
    await websocket.send_text("🤖 Fix It Fred Development Logs - Connected")
    
    # This can be enhanced to stream real-time logs
    try:
        while True:
            await asyncio.sleep(10)
            await websocket.send_text(f"🕐 Heartbeat: {asyncio.get_event_loop().time()}")
    except:
        pass

if __name__ == "__main__":
    print("🤖 Starting Fix It Fred Development API Server...")
    print(f"🌐 VM IP: {fred.vm_ip}")
    print("📱 API available at: http://localhost:8000")
    print("📚 Docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )