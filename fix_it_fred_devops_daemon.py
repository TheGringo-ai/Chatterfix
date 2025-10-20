#!/usr/bin/env python3
"""
Fix It Fred DevOps Daemon - Autonomous VM Management
Continuously monitors, heals, and deploys changes
"""

import os
import sys
import json
import time
import signal
import logging
import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration from environment
FRED_MODE = os.getenv('FRED_MODE', 'development')
FRED_LOG_LEVEL = os.getenv('FRED_LOG_LEVEL', 'INFO')
FRED_HEALING_INTERVAL = int(os.getenv('FRED_HEALING_INTERVAL', '60'))
FRED_DEPLOYMENT_CHECK_INTERVAL = int(os.getenv('FRED_DEPLOYMENT_CHECK_INTERVAL', '300'))
GITHUB_REPO = os.getenv('GITHUB_REPO', 'TheGringo-ai/Chatterfix')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'main-clean')
REPO_PATH = "/home/yoyofred_gringosgambit_com/chatterfix-docker"

class FixItFredDevOpsDaemon:
    def __init__(self):
        """Initialize Fix It Fred DevOps Daemon"""
        self.setup_logging()
        self.running = True
        self.last_health_check = datetime.now()
        self.last_deployment_check = datetime.now()
        self.last_commit_sha = None
        self.services_to_monitor = [
            "nginx",
            "chatterfix-cmms", 
            "fix-it-fred-git"
        ]
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGUSR1, self.health_check_signal)
        
        self.logger.info("🤖 Fix It Fred DevOps Daemon initialized")
        
    def setup_logging(self):
        """Setup structured logging"""
        log_level = getattr(logging, FRED_LOG_LEVEL.upper(), logging.INFO)
        
        # Create structured formatter
        formatter = logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
            '"service":"fix-it-fred-devops","message":"%(message)s",'
            '"module":"%(module)s","function":"%(funcName)s"}'
        )
        
        # Setup handlers
        self.logger = logging.getLogger('fix-it-fred-devops')
        self.logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = Path("/var/log/fix-it-fred-devops.log")
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except PermissionError:
            # Fallback to user directory
            file_handler = logging.FileHandler("/tmp/fix-it-fred-devops.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received signal {signum}, shutting down gracefully")
        self.running = False
        
    def health_check_signal(self, signum, frame):
        """Handle health check signal (SIGUSR1)"""
        self.logger.info("🩺 Health check signal received, performing immediate check")
        asyncio.create_task(self.perform_health_check())
        
    async def execute_command(self, command, description="Command"):
        """Execute shell command asynchronously"""
        try:
            self.logger.debug(f"🔧 Executing: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=REPO_PATH
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
                self.logger.debug(f"✅ {description} completed")
            else:
                self.logger.error(f"❌ {description} failed: {result['stderr']}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Command execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "description": description
            }
            
    async def check_service_status(self, service_name):
        """Check if a systemd service is active"""
        result = await self.execute_command(
            f"systemctl is-active {service_name}",
            f"Check {service_name} status"
        )
        
        is_active = result["success"] and "active" in result["stdout"]
        
        return {
            "service": service_name,
            "active": is_active,
            "status": result["stdout"] if result["success"] else "unknown"
        }
        
    async def restart_service(self, service_name):
        """Restart a systemd service"""
        self.logger.info(f"🔄 Restarting service: {service_name}")
        
        result = await self.execute_command(
            f"sudo systemctl restart {service_name}",
            f"Restart {service_name}"
        )
        
        if result["success"]:
            self.logger.info(f"✅ Successfully restarted {service_name}")
            
            # Wait and verify restart
            await asyncio.sleep(5)
            status = await self.check_service_status(service_name)
            
            if status["active"]:
                self.logger.info(f"✅ {service_name} is now active")
                return {"success": True, "restarted": True, "active": True}
            else:
                self.logger.warning(f"⚠️ {service_name} restart but not active")
                return {"success": True, "restarted": True, "active": False}
        else:
            self.logger.error(f"❌ Failed to restart {service_name}")
            return {"success": False, "error": result.get("stderr", "Unknown error")}
            
    async def perform_health_check(self):
        """Perform comprehensive health check and healing"""
        self.logger.info("🩺 Starting health check and auto-healing")
        
        healing_actions = []
        
        # Check all monitored services
        for service in self.services_to_monitor:
            status = await self.check_service_status(service)
            
            if not status["active"]:
                self.logger.warning(f"⚠️ Service {service} is not active, attempting restart")
                
                restart_result = await self.restart_service(service)
                healing_actions.append({
                    "service": service,
                    "action": "restart",
                    "success": restart_result["success"],
                    "timestamp": datetime.now().isoformat()
                })
                
        # Check application endpoints
        await self.check_application_health()
        
        # Check disk space
        await self.check_system_resources()
        
        self.last_health_check = datetime.now()
        
        if healing_actions:
            self.logger.info(f"🔧 Health check complete: {len(healing_actions)} healing actions taken")
        else:
            self.logger.info("✅ Health check complete: All services healthy")
            
        return healing_actions
        
    async def check_application_health(self):
        """Check application-specific health endpoints"""
        endpoints = [
            ("http://localhost:8080/health", "Main application"),
            ("http://localhost:9002/health", "Git integration service")
        ]
        
        for url, name in endpoints:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.logger.debug(f"✅ {name} health check passed")
                else:
                    self.logger.warning(f"⚠️ {name} health check failed: HTTP {response.status_code}")
            except requests.RequestException as e:
                self.logger.warning(f"⚠️ {name} health check failed: {e}")
                
    async def check_system_resources(self):
        """Check system resources (disk, memory, etc.)"""
        # Check disk space
        df_result = await self.execute_command("df -h /", "Check disk space")
        if df_result["success"]:
            lines = df_result["stdout"].split('\n')
            if len(lines) > 1:
                usage_line = lines[1]
                usage_percent = usage_line.split()[4].rstrip('%')
                try:
                    if int(usage_percent) > 85:
                        self.logger.warning(f"⚠️ High disk usage: {usage_percent}%")
                        await self.cleanup_old_files()
                except ValueError:
                    pass
                    
        # Check memory
        free_result = await self.execute_command("free -h", "Check memory")
        if free_result["success"]:
            self.logger.debug("💾 Memory status checked")
            
    async def cleanup_old_files(self):
        """Clean up old log files and temporary files"""
        self.logger.info("🧹 Performing automatic cleanup")
        
        cleanup_commands = [
            "find /tmp -name '*.log' -mtime +7 -delete",
            "find /var/log -name '*.log.*' -mtime +30 -delete",
            "docker system prune -f",
            "journalctl --vacuum-time=7d"
        ]
        
        for cmd in cleanup_commands:
            await self.execute_command(f"sudo {cmd}", "Cleanup operation")
            
    async def check_for_updates(self):
        """Check for new commits and deploy if needed"""
        self.logger.debug("🔍 Checking for repository updates")
        
        # Fetch latest changes
        fetch_result = await self.execute_command("git fetch origin", "Fetch updates")
        if not fetch_result["success"]:
            self.logger.error("❌ Failed to fetch git updates")
            return
            
        # Check if there are new commits
        log_result = await self.execute_command(
            f"git log HEAD..origin/{GITHUB_BRANCH} --oneline",
            "Check for new commits"
        )
        
        if log_result["success"] and log_result["stdout"]:
            new_commits = log_result["stdout"].split('\n')
            self.logger.info(f"🆕 Found {len(new_commits)} new commits, deploying...")
            
            await self.deploy_updates()
        else:
            self.logger.debug("✅ Repository is up to date")
            
        self.last_deployment_check = datetime.now()
        
    async def deploy_updates(self):
        """Deploy latest updates from repository"""
        self.logger.info("🚀 Starting automatic deployment")
        
        # Pull latest changes
        pull_result = await self.execute_command(
            f"git pull origin {GITHUB_BRANCH}",
            "Pull latest changes"
        )
        
        if not pull_result["success"]:
            self.logger.error("❌ Failed to pull latest changes")
            return
            
        # Install/update dependencies if requirements changed
        if "requirements" in pull_result["stdout"] or "package" in pull_result["stdout"]:
            self.logger.info("📦 Installing updated dependencies")
            await self.execute_command("pip3 install --user -r requirements.txt", "Install dependencies")
            
        # Restart services to apply changes
        self.logger.info("🔄 Restarting services after deployment")
        restart_services = ["chatterfix-cmms", "nginx"]
        
        for service in restart_services:
            await self.restart_service(service)
            await asyncio.sleep(2)  # Stagger restarts
            
        # Wait for services to stabilize
        await asyncio.sleep(10)
        
        # Verify deployment health
        healing_actions = await self.perform_health_check()
        
        if not healing_actions:
            self.logger.info("✅ Deployment completed successfully")
            await self.create_deployment_commit()
        else:
            self.logger.warning("⚠️ Deployment completed with issues requiring healing")
            
    async def create_deployment_commit(self):
        """Create a deployment marker commit"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"🤖 Fix It Fred: Auto-deployment completed {timestamp}"
        
        # Create deployment log entry
        deployment_log = {
            "timestamp": timestamp,
            "type": "auto_deployment",
            "status": "success",
            "services_restarted": self.services_to_monitor,
            "fred_version": "1.0.0"
        }
        
        with open("/tmp/fred_deployment.log", "w") as f:
            json.dump(deployment_log, f, indent=2)
            
    async def run_daemon(self):
        """Main daemon loop"""
        self.logger.info("🚀 Fix It Fred DevOps Daemon starting")
        self.logger.info(f"📊 Mode: {FRED_MODE}")
        self.logger.info(f"🔄 Healing interval: {FRED_HEALING_INTERVAL}s")
        self.logger.info(f"📡 Deployment check interval: {FRED_DEPLOYMENT_CHECK_INTERVAL}s")
        
        # Initial health check
        await self.perform_health_check()
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Health check cycle
                if (current_time - self.last_health_check).seconds >= FRED_HEALING_INTERVAL:
                    await self.perform_health_check()
                    
                # Deployment check cycle
                if (current_time - self.last_deployment_check).seconds >= FRED_DEPLOYMENT_CHECK_INTERVAL:
                    await self.check_for_updates()
                    
                # Sleep for a short interval
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"❌ Daemon loop error: {e}")
                await asyncio.sleep(30)  # Wait longer on errors
                
        self.logger.info("🛑 Fix It Fred DevOps Daemon stopped")

async def main():
    """Main entry point"""
    daemon = FixItFredDevOpsDaemon()
    await daemon.run_daemon()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Fix It Fred DevOps Daemon interrupted")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)