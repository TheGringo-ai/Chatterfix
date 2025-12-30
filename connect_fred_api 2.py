#!/usr/bin/env python3
"""
connect_fred_api.py
-------------------
Secure connection helper for Fix It Fred DevOps API.
Enables ChatGPT or other automation agents to interact with your VM
through authenticated API calls.

Enhanced with continuous monitoring and ChatterFix CMMS integration.
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

# ==========================================================
# 🔐 Configuration
# ==========================================================
API_URL = os.getenv("FRED_API_URL", "http://35.237.149.25:9004")
API_KEY = os.getenv("FRED_API_KEY", "pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Monitoring configuration
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "300"))  # 5 minutes
CRITICAL_SERVICES = ["nginx", "fix-it-fred-devops", "fix-it-fred-devops-api", "docker"]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"fred-api-client","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

# ==========================================================
# 🧠 Core API Functions
# ==========================================================

def check_health() -> Dict[str, Any]:
    """Check VM health and Fix It Fred API status."""
    try:
        res = requests.get(f"{API_URL}/health", headers=HEADERS, timeout=10)
        res.raise_for_status()
        logger.info("✅ Connected to Fix It Fred DevOps API")
        return res.json()
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return {"error": str(e)}

def execute_command(cmd: str, description: str = "") -> Dict[str, Any]:
    """Execute a safe command on the VM."""
    payload = {"command": cmd, "description": description}
    try:
        res = requests.post(f"{API_URL}/command", headers=HEADERS, json=payload, timeout=20)
        res.raise_for_status()
        logger.info(f"💻 Command executed: {cmd}")
        return res.json()
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        return {"error": str(e)}

def manage_service(service_name: str, action: str = "restart") -> Dict[str, Any]:
    """Manage a system service (start, stop, restart, status)."""
    payload = {"service_name": service_name, "action": action}
    try:
        res = requests.post(f"{API_URL}/service", headers=HEADERS, json=payload, timeout=20)
        res.raise_for_status()
        logger.info(f"🔄 Service {action}: {service_name}")
        return res.json()
    except Exception as e:
        logger.error(f"❌ Service {action} failed: {e}")
        return {"error": str(e)}

def restart_service(service_name: str) -> Dict[str, Any]:
    """Restart a system service."""
    return manage_service(service_name, "restart")

def deploy_update(branch: str = "main-clean", force: bool = False) -> Dict[str, Any]:
    """Trigger a code deployment."""
    payload = {"branch": branch, "force": force, "notify_completion": True}
    try:
        res = requests.post(f"{API_URL}/deploy", headers=HEADERS, json=payload, timeout=30)
        res.raise_for_status()
        logger.info(f"🚀 Deployment triggered for branch '{branch}'")
        return res.json()
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return {"error": str(e)}

def get_services() -> Dict[str, Any]:
    """Get status of all services."""
    try:
        res = requests.get(f"{API_URL}/services", headers=HEADERS, timeout=15)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"❌ Service list failed: {e}")
        return {"error": str(e)}

def get_logs(service: str, lines: int = 20) -> Dict[str, Any]:
    """Fetch recent logs for a given service."""
    try:
        res = requests.get(f"{API_URL}/logs/{service}?lines={lines}", headers=HEADERS, timeout=15)
        res.raise_for_status()
        logger.info(f"📜 Retrieved logs for {service}")
        return res.json()
    except Exception as e:
        logger.error(f"❌ Log retrieval failed: {e}")
        return {"error": str(e)}

def trigger_fred_health_check() -> Dict[str, Any]:
    """Trigger immediate Fix It Fred health check."""
    payload = {"signal": "health_check"}
    try:
        res = requests.post(f"{API_URL}/fred/signal", headers=HEADERS, json=payload, timeout=15)
        res.raise_for_status()
        logger.info("🩺 Fix It Fred health check triggered")
        return res.json()
    except Exception as e:
        logger.error(f"❌ Fred signal failed: {e}")
        return {"error": str(e)}

def get_git_status() -> Dict[str, Any]:
    """Get git repository status."""
    try:
        res = requests.get(f"{API_URL}/git/status", headers=HEADERS, timeout=15)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"❌ Git status failed: {e}")
        return {"error": str(e)}

# ==========================================================
# 🔧 Enhanced Monitoring & Auto-Healing
# ==========================================================

class FredMonitor:
    """Continuous monitoring and auto-healing for ChatterFix CMMS platform."""
    
    def __init__(self):
        self.last_health_check = None
        self.failed_services = set()
        self.restart_attempts = {}
        self.max_restart_attempts = 3
        
    def check_critical_services(self) -> Dict[str, bool]:
        """Check status of critical services."""
        services_data = get_services()
        if "error" in services_data:
            logger.error("Failed to get service status")
            return {}
            
        if not services_data.get("success") or not services_data.get("data"):
            return {}
            
        services = services_data["data"].get("services", {})
        critical_status = {}
        
        for service in CRITICAL_SERVICES:
            if service in services:
                critical_status[service] = services[service].get("active", False)
            else:
                critical_status[service] = False
                
        return critical_status
    
    def auto_heal_service(self, service_name: str) -> bool:
        """Attempt to auto-heal a failed service."""
        if service_name not in self.restart_attempts:
            self.restart_attempts[service_name] = 0
            
        if self.restart_attempts[service_name] >= self.max_restart_attempts:
            logger.error(f"❌ Max restart attempts reached for {service_name}")
            return False
            
        logger.info(f"🔧 Auto-healing service: {service_name}")
        result = restart_service(service_name)
        
        if result.get("success"):
            self.restart_attempts[service_name] = 0
            logger.info(f"✅ Successfully healed {service_name}")
            return True
        else:
            self.restart_attempts[service_name] += 1
            logger.error(f"❌ Failed to heal {service_name} (attempt {self.restart_attempts[service_name]})")
            return False
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive platform health check."""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy",
            "services": {},
            "system": {},
            "actions_taken": []
        }
        
        # Check API health
        api_health = check_health()
        if "error" in api_health:
            health_report["overall_health"] = "critical"
            health_report["api_error"] = api_health["error"]
            return health_report
            
        # Extract system info from health check
        if api_health.get("vm_status") == "healthy":
            health_report["system"] = {
                "vm_status": "healthy",
                "services": api_health.get("services", {}),
                "resources": api_health.get("system_resources", {}),
                "fred_status": api_health.get("fred_status", "unknown")
            }
        else:
            health_report["overall_health"] = "degraded"
            
        # Check critical services
        critical_services = self.check_critical_services()
        health_report["services"] = critical_services
        
        # Auto-heal failed services
        for service, is_healthy in critical_services.items():
            if not is_healthy:
                health_report["overall_health"] = "degraded"
                if self.auto_heal_service(service):
                    health_report["actions_taken"].append(f"Restarted {service}")
                else:
                    health_report["actions_taken"].append(f"Failed to restart {service}")
        
        self.last_health_check = datetime.now()
        return health_report
    
    def monitor_continuously(self, duration_minutes: int = None):
        """Start continuous monitoring loop."""
        logger.info(f"🔍 Starting continuous monitoring (interval: {MONITOR_INTERVAL}s)")
        
        start_time = datetime.now()
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"🩺 Health check #{iteration}")
                
                health_report = self.comprehensive_health_check()
                
                # Log health status
                status_emoji = {
                    "healthy": "✅",
                    "degraded": "⚠️", 
                    "critical": "❌"
                }
                emoji = status_emoji.get(health_report["overall_health"], "❓")
                
                logger.info(f"{emoji} Overall health: {health_report['overall_health']}")
                
                if health_report["actions_taken"]:
                    logger.info(f"🔧 Actions taken: {', '.join(health_report['actions_taken'])}")
                
                # Check if duration limit reached
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        logger.info(f"⏰ Monitoring duration completed ({duration_minutes} minutes)")
                        break
                
                # Wait for next check
                time.sleep(MONITOR_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")

# ==========================================================
# 🚀 ChatGPT Integration Helpers
# ==========================================================

def chatgpt_health_summary() -> str:
    """Get a human-readable health summary for ChatGPT."""
    health = check_health()
    if "error" in health:
        return f"❌ API Connection Failed: {health['error']}"
    
    services = get_services()
    if "error" in services:
        return "⚠️ Could not retrieve service status"
    
    service_data = services.get("data", {}).get("services", {})
    active_services = [name for name, info in service_data.items() if info.get("active")]
    inactive_services = [name for name, info in service_data.items() if not info.get("active")]
    
    summary = f"✅ Fix It Fred API Connected\n"
    summary += f"🖥️ VM Status: {health.get('vm_status', 'unknown')}\n"
    summary += f"🤖 Fred Status: {health.get('fred_status', 'unknown')}\n"
    summary += f"✅ Active Services ({len(active_services)}): {', '.join(active_services)}\n"
    
    if inactive_services:
        summary += f"❌ Inactive Services ({len(inactive_services)}): {', '.join(inactive_services)}\n"
    
    return summary

def chatgpt_deploy_latest(branch: str = "main-clean") -> str:
    """Deploy latest code with human-readable response."""
    result = deploy_update(branch)
    if "error" in result:
        return f"❌ Deployment failed: {result['error']}"
    
    if result.get("success"):
        return f"🚀 Deployment initiated for branch '{branch}'"
    else:
        return f"⚠️ Deployment response unclear: {result}"

def chatgpt_restart_service(service: str) -> str:
    """Restart service with human-readable response."""
    result = restart_service(service)
    if "error" in result:
        return f"❌ Failed to restart {service}: {result['error']}"
    
    if result.get("success"):
        return f"✅ Successfully restarted {service}"
    else:
        return f"⚠️ Restart result unclear for {service}"

# ==========================================================
# 🧪 Test & Demo Functions
# ==========================================================

def run_basic_test():
    """Run basic API connectivity test."""
    print("🔗 Testing Fix It Fred DevOps API connection...")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n🧪 Test 1: Health Check")
    health = check_health()
    print(json.dumps(health, indent=2))
    
    # Test 2: Service status
    print("\n🧪 Test 2: Service Status")
    services = get_services()
    if services.get("success"):
        service_data = services.get("data", {}).get("services", {})
        for name, info in service_data.items():
            status = "✅ Active" if info.get("active") else "❌ Inactive"
            print(f"  {name}: {status}")
    
    # Test 3: Git status
    print("\n🧪 Test 3: Git Status")
    git = get_git_status()
    if git.get("success"):
        data = git.get("data", {})
        print(f"  Branch: {data.get('branch', 'unknown')}")
        print(f"  Last commit: {data.get('last_commit', 'unknown')}")
    
    # Test 4: ChatGPT summary
    print("\n🧪 Test 4: ChatGPT Summary")
    print(chatgpt_health_summary())

def run_monitoring_demo(duration_minutes: int = 5):
    """Run monitoring demo for specified duration."""
    monitor = FredMonitor()
    print(f"🔍 Starting {duration_minutes}-minute monitoring demo...")
    monitor.monitor_continuously(duration_minutes)

# ==========================================================
# 🎯 Main Entry Point
# ==========================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            run_basic_test()
        elif command == "monitor":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else None
            monitor = FredMonitor()
            monitor.monitor_continuously(duration)
        elif command == "health":
            print(chatgpt_health_summary())
        elif command == "deploy":
            branch = sys.argv[2] if len(sys.argv) > 2 else "main-clean"
            print(chatgpt_deploy_latest(branch))
        elif command == "restart":
            if len(sys.argv) > 2:
                service = sys.argv[2]
                print(chatgpt_restart_service(service))
            else:
                print("❌ Please specify service name: python connect_fred_api.py restart nginx")
        else:
            print("❌ Unknown command. Available: test, monitor, health, deploy, restart")
    else:
        # Default: run basic test
        run_basic_test()

# ==========================================================
# 📚 Usage Examples for ChatGPT
# ==========================================================
"""
Usage Examples:

1. Basic connection test:
   python3 connect_fred_api.py test

2. Get health summary:
   python3 connect_fred_api.py health

3. Deploy latest code:
   python3 connect_fred_api.py deploy main-clean

4. Restart a service:
   python3 connect_fred_api.py restart nginx

5. Start monitoring (infinite):
   python3 connect_fred_api.py monitor

6. Monitor for 10 minutes:
   python3 connect_fred_api.py monitor 10

7. Use in code:
   from connect_fred_api import chatgpt_health_summary, chatgpt_deploy_latest
   print(chatgpt_health_summary())
   print(chatgpt_deploy_latest())
"""