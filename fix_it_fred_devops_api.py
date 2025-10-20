#!/usr/bin/env python3
"""
Fix It Fred DevOps API - ChatGPT Integration
Secure REST API for autonomous VM management and deployment
"""

import os
import sys
import json
import time
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import subprocess
import logging

# Configuration
API_PORT = int(os.getenv('FRED_API_PORT', '9004'))
API_HOST = os.getenv('FRED_API_HOST', '0.0.0.0')
API_KEY = os.getenv('FRED_API_KEY', secrets.token_urlsafe(32))
REPO_PATH = "/home/yoyofred_gringosgambit_com/chatterfix-docker"

# Initialize FastAPI
app = FastAPI(
    title="Fix It Fred DevOps API",
    description="Autonomous VM Management API for ChatGPT Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"fred-devops-api","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

# Pydantic models
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class CommandRequest(BaseModel):
    command: str
    description: Optional[str] = "API command execution"
    working_directory: Optional[str] = None

class ServiceAction(BaseModel):
    service_name: str
    action: str  # start, stop, restart, status

class DeploymentRequest(BaseModel):
    branch: Optional[str] = "main-clean"
    force: bool = False
    notify_completion: bool = True

class HealthCheckResponse(BaseModel):
    vm_status: str
    services: Dict[str, bool]
    system_resources: Dict[str, Any]
    last_deployment: Optional[str]
    fred_status: str

# Authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key authentication"""
    if not credentials or credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Utility functions
async def execute_command(command: str, description: str = "Command", cwd: str = None) -> Dict:
    """Execute shell command safely"""
    try:
        logger.info(f"🔧 Executing: {description}")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or REPO_PATH
        )
        
        stdout, stderr = await process.communicate()
        
        result = {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip(),
            "command": command,
            "description": description
        }
        
        if result["success"]:
            logger.info(f"✅ {description} completed")
        else:
            logger.error(f"❌ {description} failed: {result['stderr']}")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Command execution error: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command,
            "description": description
        }

# API Endpoints

@app.get("/", response_model=ApiResponse)
async def root():
    """API health and information endpoint"""
    return ApiResponse(
        success=True,
        message="Fix It Fred DevOps API - Ready for ChatGPT Integration",
        data={
            "service": "Fix It Fred DevOps API",
            "version": "1.0.0",
            "capabilities": [
                "VM command execution",
                "Service management", 
                "Deployment automation",
                "Health monitoring",
                "Git operations",
                "System information"
            ],
            "authentication": "Bearer token required",
            "docs": "/docs"
        }
    )

@app.get("/health", response_model=HealthCheckResponse)
async def health_check(api_key: str = Depends(verify_api_key)):
    """Comprehensive VM health check"""
    logger.info("🩺 Performing health check via API")
    
    # Check VM status
    vm_info = await execute_command("uptime && free -h && df -h /", "System info")
    
    # Check services
    services = {}
    service_list = ["nginx", "fix-it-fred-devops", "fix-it-fred-git", "docker"]
    
    for service in service_list:
        result = await execute_command(f"systemctl is-active {service}", f"Check {service}")
        services[service] = result["success"] and "active" in result["stdout"]
    
    # Get system resources
    resources = {
        "uptime": vm_info["stdout"].split('\n')[0] if vm_info["success"] else "unknown",
        "memory": vm_info["stdout"].split('\n')[1] if vm_info["success"] and len(vm_info["stdout"].split('\n')) > 1 else "unknown",
        "disk": vm_info["stdout"].split('\n')[-1] if vm_info["success"] else "unknown"
    }
    
    # Check last deployment
    git_log = await execute_command("git log -1 --oneline", "Last commit")
    last_deployment = git_log["stdout"] if git_log["success"] else None
    
    return HealthCheckResponse(
        vm_status="healthy" if vm_info["success"] else "unhealthy",
        services=services,
        system_resources=resources,
        last_deployment=last_deployment,
        fred_status="active" if services.get("fix-it-fred-devops", False) else "inactive"
    )

@app.post("/command", response_model=ApiResponse)
async def execute_vm_command(
    request: CommandRequest, 
    api_key: str = Depends(verify_api_key)
):
    """Execute command on VM"""
    logger.info(f"🔧 API command request: {request.description}")
    
    # Security: Restrict dangerous commands
    dangerous_commands = ["rm -rf", "mkfs", "dd if=", ":(){ :|:& };:", "sudo passwd"]
    if any(cmd in request.command for cmd in dangerous_commands):
        raise HTTPException(status_code=400, detail="Command not allowed for security reasons")
    
    result = await execute_command(
        request.command, 
        request.description,
        request.working_directory
    )
    
    return ApiResponse(
        success=result["success"],
        message=f"Command executed: {request.description}",
        data=result
    )

@app.post("/service", response_model=ApiResponse)
async def manage_service(
    request: ServiceAction,
    api_key: str = Depends(verify_api_key)
):
    """Manage systemd services"""
    logger.info(f"🔧 Service {request.action} request for {request.service_name}")
    
    # Validate service action
    valid_actions = ["start", "stop", "restart", "status", "enable", "disable"]
    if request.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    # Execute service command
    if request.action == "status":
        command = f"systemctl {request.action} {request.service_name}"
    else:
        command = f"sudo systemctl {request.action} {request.service_name}"
    
    result = await execute_command(command, f"{request.action} {request.service_name}")
    
    return ApiResponse(
        success=result["success"],
        message=f"Service {request.action} completed for {request.service_name}",
        data=result
    )

@app.post("/deploy", response_model=ApiResponse)
async def deploy_updates(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Deploy latest updates from repository"""
    logger.info(f"🚀 Deployment request for branch: {request.branch}")
    
    async def deployment_process():
        # Fetch latest changes
        fetch_result = await execute_command("git fetch origin", "Fetch updates")
        if not fetch_result["success"]:
            return {"success": False, "error": "Failed to fetch updates"}
        
        # Check for new commits unless forced
        if not request.force:
            log_result = await execute_command(
                f"git log HEAD..origin/{request.branch} --oneline",
                "Check for updates"
            )
            if not log_result["stdout"]:
                return {"success": True, "message": "No new commits to deploy"}
        
        # Pull latest changes
        pull_result = await execute_command(f"git pull origin {request.branch}", "Pull updates")
        if not pull_result["success"]:
            return {"success": False, "error": "Failed to pull updates"}
        
        # Restart services
        services_to_restart = ["nginx", "fix-it-fred-devops"]
        restart_results = []
        
        for service in services_to_restart:
            result = await execute_command(f"sudo systemctl restart {service}", f"Restart {service}")
            restart_results.append({"service": service, "success": result["success"]})
            await asyncio.sleep(2)  # Stagger restarts
        
        return {
            "success": True,
            "pull_result": pull_result,
            "restart_results": restart_results
        }
    
    # Execute deployment in background
    background_tasks.add_task(deployment_process)
    
    return ApiResponse(
        success=True,
        message="Deployment initiated",
        data={"branch": request.branch, "force": request.force}
    )

@app.get("/git/status", response_model=ApiResponse)
async def git_status(api_key: str = Depends(verify_api_key)):
    """Get git repository status"""
    result = await execute_command("git status --porcelain", "Git status")
    
    # Also get branch and commit info
    branch_result = await execute_command("git branch --show-current", "Current branch")
    commit_result = await execute_command("git log -1 --oneline", "Last commit")
    
    return ApiResponse(
        success=result["success"],
        message="Git status retrieved",
        data={
            "status": result["stdout"],
            "branch": branch_result["stdout"] if branch_result["success"] else "unknown",
            "last_commit": commit_result["stdout"] if commit_result["success"] else "unknown"
        }
    )

@app.get("/services", response_model=ApiResponse)
async def list_services(api_key: str = Depends(verify_api_key)):
    """List all relevant services and their status"""
    services = [
        "nginx", "fix-it-fred-devops", "fix-it-fred-git", 
        "fix-it-fred", "docker", "chatterfix"
    ]
    
    service_status = {}
    for service in services:
        result = await execute_command(f"systemctl is-active {service}", f"Check {service}")
        service_status[service] = {
            "active": result["success"] and "active" in result["stdout"],
            "status": result["stdout"] if result["success"] else "unknown"
        }
    
    return ApiResponse(
        success=True,
        message="Service status retrieved",
        data={"services": service_status}
    )

@app.get("/logs/{service}", response_model=ApiResponse)
async def get_service_logs(
    service: str, 
    lines: int = 50,
    api_key: str = Depends(verify_api_key)
):
    """Get logs for a specific service"""
    result = await execute_command(
        f"sudo journalctl -u {service} --no-pager -n {lines}",
        f"Get {service} logs"
    )
    
    return ApiResponse(
        success=result["success"],
        message=f"Logs retrieved for {service}",
        data={"logs": result["stdout"], "service": service}
    )

@app.post("/fred/signal", response_model=ApiResponse)
async def trigger_fred_action(
    signal: str = "health_check",
    api_key: str = Depends(verify_api_key)
):
    """Send signal to Fix It Fred DevOps daemon"""
    logger.info(f"📡 Triggering Fred action: {signal}")
    
    if signal == "health_check":
        result = await execute_command(
            "sudo systemctl kill --signal=SIGUSR1 fix-it-fred-devops.service",
            "Trigger Fred health check"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid signal type")
    
    return ApiResponse(
        success=result["success"],
        message=f"Fred signal sent: {signal}",
        data=result
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Fix It Fred DevOps API starting up")
    logger.info(f"🔑 API Key: {API_KEY[:8]}...{API_KEY[-8:]}")
    logger.info(f"🌐 Running on {API_HOST}:{API_PORT}")
    logger.info("📚 API Documentation: /docs")

if __name__ == "__main__":
    import uvicorn
    
    print("🤖 Fix It Fred DevOps API for ChatGPT Integration")
    print("=" * 55)
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌐 URL: http://{API_HOST}:{API_PORT}")
    print(f"📚 Docs: http://{API_HOST}:{API_PORT}/docs")
    print("=" * 55)
    
    uvicorn.run(
        "fix_it_fred_devops_api:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info"
    )