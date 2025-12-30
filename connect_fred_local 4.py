#!/usr/bin/env python3
"""
connect_fred_local.py
--------------------
Local connection helper for Fix It Fred DevOps API via GCP SSH tunnel.
For situations where direct external access isn't working.
"""

import subprocess
import json
import time
import requests
from typing import Dict, Any

# Configuration
INSTANCE_NAME = "chatterfix-cmms-production"
ZONE = "us-east1-b"
LOCAL_PORT = "9004"
REMOTE_PORT = "9004"
API_KEY = "pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def execute_ssh_command(command: str) -> Dict[str, Any]:
    """Execute command on VM via SSH."""
    try:
        full_command = [
            "gcloud", "compute", "ssh", INSTANCE_NAME,
            "--zone", ZONE,
            "--command", command
        ]
        
        result = subprocess.run(
            full_command, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command
        }

def check_api_via_ssh() -> Dict[str, Any]:
    """Check API status via SSH."""
    print("🔍 Checking Fix It Fred API via SSH...")
    
    # Check service status
    service_check = execute_ssh_command("sudo systemctl is-active fix-it-fred-devops-api")
    print(f"📊 Service Status: {service_check.get('stdout', 'unknown')}")
    
    # Test local API endpoint
    api_test = execute_ssh_command("curl -s http://localhost:9004/ | head -3")
    print(f"🌐 Local API Test: {api_test.get('stdout', 'failed')}")
    
    # Get detailed service info
    service_info = execute_ssh_command("sudo systemctl status fix-it-fred-devops-api --no-pager -l")
    
    return {
        "service_active": "active" in service_check.get("stdout", ""),
        "api_responding": "success" in api_test.get("stdout", ""),
        "service_info": service_info.get("stdout", "")
    }

def proxy_api_request(endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
    """Make API request via SSH command execution."""
    print(f"📡 Proxying {method} request to {endpoint}...")
    
    if method == "GET":
        curl_cmd = f"curl -s -H 'Authorization: Bearer {API_KEY}' http://localhost:9004{endpoint}"
    else:
        data_json = json.dumps(data) if data else '{}'
        curl_cmd = f"curl -s -X {method} -H 'Authorization: Bearer {API_KEY}' -H 'Content-Type: application/json' -d '{data_json}' http://localhost:9004{endpoint}"
    
    result = execute_ssh_command(curl_cmd)
    
    if result["success"]:
        try:
            return json.loads(result["stdout"])
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw_output": result["stdout"]}
    else:
        return {"error": result.get("stderr", "Command failed")}

def chatgpt_health_via_ssh() -> str:
    """Get health summary via SSH for ChatGPT."""
    print("🩺 Getting health status for ChatGPT...")
    
    # Check API service first
    status = check_api_via_ssh()
    if not status["service_active"]:
        return "❌ Fix It Fred DevOps API service is not active"
    
    if not status["api_responding"]:
        return "⚠️ Fix It Fred DevOps API service active but not responding"
    
    # Get health data
    health = proxy_api_request("/health")
    if "error" in health:
        return f"❌ Health check failed: {health['error']}"
    
    # Get service status
    services = proxy_api_request("/services")
    if "error" in services:
        return "⚠️ Could not retrieve service status"
    
    # Build summary
    summary = "✅ Fix It Fred API Connected via SSH\n"
    summary += f"🖥️ VM Status: {health.get('vm_status', 'unknown')}\n"
    summary += f"🤖 Fred Status: {health.get('fred_status', 'unknown')}\n"
    
    if services.get("success") and services.get("data"):
        service_data = services["data"].get("services", {})
        active_services = [name for name, info in service_data.items() if info.get("active")]
        inactive_services = [name for name, info in service_data.items() if not info.get("active")]
        
        summary += f"✅ Active Services ({len(active_services)}): {', '.join(active_services)}\n"
        if inactive_services:
            summary += f"❌ Inactive Services ({len(inactive_services)}): {', '.join(inactive_services)}\n"
    
    return summary

def chatgpt_restart_service_via_ssh(service_name: str) -> str:
    """Restart service via SSH for ChatGPT."""
    print(f"🔄 Restarting {service_name} via SSH...")
    
    data = {"service_name": service_name, "action": "restart"}
    result = proxy_api_request("/service", "POST", data)
    
    if "error" in result:
        return f"❌ Failed to restart {service_name}: {result['error']}"
    
    if result.get("success"):
        return f"✅ Successfully restarted {service_name}"
    else:
        return f"⚠️ Restart result unclear for {service_name}"

def chatgpt_deploy_via_ssh(branch: str = "main-clean") -> str:
    """Deploy via SSH for ChatGPT."""
    print(f"🚀 Deploying {branch} via SSH...")
    
    data = {"branch": branch, "force": False, "notify_completion": True}
    result = proxy_api_request("/deploy", "POST", data)
    
    if "error" in result:
        return f"❌ Deployment failed: {result['error']}"
    
    if result.get("success"):
        return f"🚀 Deployment initiated for branch '{branch}'"
    else:
        return f"⚠️ Deployment response unclear: {result}"

def execute_command_via_ssh(command: str, description: str = "") -> str:
    """Execute VM command via SSH for ChatGPT."""
    print(f"💻 Executing command via SSH: {command}")
    
    data = {"command": command, "description": description}
    result = proxy_api_request("/command", "POST", data)
    
    if "error" in result:
        return f"❌ Command failed: {result['error']}"
    
    if result.get("success") and result.get("data"):
        command_result = result["data"]
        if command_result.get("success"):
            return f"✅ Command output:\n{command_result.get('stdout', '')}"
        else:
            return f"❌ Command failed:\n{command_result.get('stderr', '')}"
    else:
        return f"⚠️ Command result unclear: {result}"

def run_ssh_test():
    """Run comprehensive test via SSH."""
    print("🔗 Testing Fix It Fred API via SSH tunnel...")
    print("=" * 50)
    
    # Test 1: Service check
    print("\n🧪 Test 1: Service Status Check")
    status = check_api_via_ssh()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test 2: Health check
    print("\n🧪 Test 2: Health Check via API")
    health = proxy_api_request("/health")
    print(json.dumps(health, indent=2))
    
    # Test 3: ChatGPT summary
    print("\n🧪 Test 3: ChatGPT Health Summary")
    print(chatgpt_health_via_ssh())
    
    # Test 4: Simple command
    print("\n🧪 Test 4: Simple Command Execution")
    print(execute_command_via_ssh("uptime", "Check system uptime"))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            run_ssh_test()
        elif command == "health":
            print(chatgpt_health_via_ssh())
        elif command == "deploy":
            branch = sys.argv[2] if len(sys.argv) > 2 else "main-clean"
            print(chatgpt_deploy_via_ssh(branch))
        elif command == "restart":
            if len(sys.argv) > 2:
                service = sys.argv[2]
                print(chatgpt_restart_service_via_ssh(service))
            else:
                print("❌ Please specify service name")
        elif command == "cmd":
            if len(sys.argv) > 2:
                cmd = " ".join(sys.argv[2:])
                print(execute_command_via_ssh(cmd))
            else:
                print("❌ Please specify command")
        else:
            print("❌ Unknown command. Available: test, health, deploy, restart, cmd")
    else:
        run_ssh_test()