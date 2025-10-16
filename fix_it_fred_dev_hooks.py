#!/usr/bin/env python3
"""
Fix It Fred Development Hooks - Direct GCP VM Integration
Gives Fix It Fred autonomous control over your GCP VM for development
"""

import os
import json
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path
import requests
from google.cloud import compute_v1
from google.oauth2 import service_account

# Configuration
PROJECT_ID = "fredfix"
ZONE = "us-east1-b"
INSTANCE_NAME = "chatterfix-cmms-production"
VM_USER = "yoyofred_gringosgambit_com"
REPO_PATH = "/home/yoyofred_gringosgambit_com/chatterfix-docker"

class FixItFredDevHooks:
    def __init__(self):
        """Initialize Fix It Fred with direct GCP access"""
        self.setup_logging()
        self.setup_gcp_client()
        self.vm_ip = self.get_vm_external_ip()
        
    def setup_logging(self):
        """Configure logging for Fred's operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='🤖 [Fix It Fred] %(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/tmp/fix_it_fred_dev.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_gcp_client(self):
        """Initialize GCP compute client with service account"""
        try:
            # Use the same service account we created for GitHub Actions
            self.compute_client = compute_v1.InstancesClient()
            self.logger.info("✅ GCP client initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize GCP client: {e}")
            
    def get_vm_external_ip(self):
        """Get the external IP of the VM"""
        try:
            request = compute_v1.GetInstanceRequest(
                project=PROJECT_ID,
                zone=ZONE,
                instance=INSTANCE_NAME
            )
            instance = self.compute_client.get(request=request)
            external_ip = instance.network_interfaces[0].access_configs[0].nat_ip
            self.logger.info(f"🌐 VM External IP: {external_ip}")
            return external_ip
        except Exception as e:
            self.logger.error(f"❌ Failed to get VM IP: {e}")
            return "35.237.149.25"  # Fallback to known IP
            
    def execute_vm_command(self, command, description="Command"):
        """Execute command on VM via gcloud compute ssh"""
        try:
            self.logger.info(f"🔧 {description}: {command}")
            
            # Use gcloud compute ssh with our service account
            gcloud_cmd = [
                "gcloud", "compute", "ssh", INSTANCE_NAME,
                "--zone", ZONE,
                "--command", command,
                "--quiet"
            ]
            
            result = subprocess.run(
                gcloud_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ {description} completed successfully")
                return {"success": True, "output": result.stdout, "error": ""}
            else:
                self.logger.error(f"❌ {description} failed: {result.stderr}")
                return {"success": False, "output": result.stdout, "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ {description} timed out")
            return {"success": False, "output": "", "error": "Command timed out"}
        except Exception as e:
            self.logger.error(f"❌ {description} error: {e}")
            return {"success": False, "output": "", "error": str(e)}
            
    def restart_service(self, service_name):
        """Restart a systemd service on the VM"""
        command = f"sudo systemctl restart {service_name}"
        return self.execute_vm_command(command, f"Restart {service_name}")
        
    def check_service_status(self, service_name):
        """Check status of a systemd service"""
        command = f"sudo systemctl is-active {service_name}"
        return self.execute_vm_command(command, f"Check {service_name} status")
        
    def deploy_code_to_vm(self, local_file, remote_path):
        """Deploy code file to VM"""
        try:
            self.logger.info(f"📤 Deploying {local_file} to {remote_path}")
            
            gcloud_cmd = [
                "gcloud", "compute", "scp",
                local_file,
                f"{INSTANCE_NAME}:{remote_path}",
                "--zone", ZONE,
                "--quiet"
            ]
            
            result = subprocess.run(
                gcloud_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ Deployed {local_file} successfully")
                return {"success": True, "message": f"Deployed to {remote_path}"}
            else:
                self.logger.error(f"❌ Deployment failed: {result.stderr}")
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            self.logger.error(f"❌ Deployment error: {e}")
            return {"success": False, "error": str(e)}
            
    def edit_file_on_vm(self, file_path, content):
        """Edit a file directly on the VM"""
        # Create a temporary file with the content
        temp_file = f"/tmp/fred_edit_{int(time.time())}.tmp"
        
        try:
            with open(temp_file, 'w') as f:
                f.write(content)
                
            # Deploy the temp file to VM
            deploy_result = self.deploy_code_to_vm(temp_file, f"/tmp/fred_edit.tmp")
            
            if deploy_result["success"]:
                # Move the temp file to the target location
                move_cmd = f"sudo mv /tmp/fred_edit.tmp {file_path} && sudo chown {VM_USER}:{VM_USER} {file_path}"
                result = self.execute_vm_command(move_cmd, f"Update {file_path}")
                
                # Clean up local temp file
                os.remove(temp_file)
                return result
            else:
                os.remove(temp_file)
                return deploy_result
                
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return {"success": False, "error": str(e)}
            
    def git_operations(self, operation, message="Fix It Fred auto-commit"):
        """Perform git operations on the VM"""
        git_commands = {
            "status": "cd /home/yoyofred_gringosgambit_com/chatterfix-docker && git status",
            "add": "cd /home/yoyofred_gringosgambit_com/chatterfix-docker && git add .",
            "commit": f"cd /home/yoyofred_gringosgambit_com/chatterfix-docker && git commit -m '{message}'",
            "push": "cd /home/yoyofred_gringosgambit_com/chatterfix-docker && git push origin main",
            "pull": "cd /home/yoyofred_gringosgambit_com/chatterfix-docker && git pull origin main"
        }
        
        if operation in git_commands:
            return self.execute_vm_command(git_commands[operation], f"Git {operation}")
        else:
            return {"success": False, "error": f"Unknown git operation: {operation}"}
            
    def full_deployment_cycle(self, files_to_deploy=None):
        """Complete deployment cycle with restart"""
        self.logger.info("🚀 Starting full deployment cycle")
        
        results = {
            "deployment": {},
            "git_operations": {},
            "service_restarts": {},
            "health_checks": {}
        }
        
        # 1. Deploy files if provided
        if files_to_deploy:
            for local_file, remote_path in files_to_deploy.items():
                results["deployment"][local_file] = self.deploy_code_to_vm(local_file, remote_path)
                
        # 2. Git operations
        results["git_operations"]["add"] = self.git_operations("add")
        results["git_operations"]["commit"] = self.git_operations("commit", "🤖 Fix It Fred: Automated deployment")
        
        # 3. Restart services
        services = ["chatterfix-cmms", "nginx", "fix-it-fred-git"]
        for service in services:
            results["service_restarts"][service] = self.restart_service(service)
            time.sleep(2)  # Wait between restarts
            
        # 4. Health checks
        time.sleep(10)  # Wait for services to start
        
        # Check application health
        try:
            health_response = requests.get(f"http://{self.vm_ip}:8080/health", timeout=10)
            results["health_checks"]["main_app"] = {
                "success": health_response.status_code == 200,
                "status_code": health_response.status_code
            }
        except Exception as e:
            results["health_checks"]["main_app"] = {"success": False, "error": str(e)}
            
        # Check Fix It Fred Git Integration
        try:
            git_health_response = requests.get(f"http://{self.vm_ip}:9002/health", timeout=10)
            results["health_checks"]["git_integration"] = {
                "success": git_health_response.status_code == 200,
                "status_code": git_health_response.status_code
            }
        except Exception as e:
            results["health_checks"]["git_integration"] = {"success": False, "error": str(e)}
            
        self.logger.info("✅ Full deployment cycle completed")
        return results
        
    def live_code_edit(self, file_path, old_content, new_content, auto_deploy=True):
        """Live edit code on VM with automatic deployment"""
        self.logger.info(f"✏️ Live editing {file_path}")
        
        # Create backup
        backup_cmd = f"cp {file_path} {file_path}.backup.$(date +%s)"
        backup_result = self.execute_vm_command(backup_cmd, "Create backup")
        
        # Edit the file
        edit_result = self.edit_file_on_vm(file_path, new_content)
        
        if edit_result["success"] and auto_deploy:
            # Automatic deployment cycle
            deploy_result = self.full_deployment_cycle()
            return {
                "edit": edit_result,
                "backup": backup_result,
                "deployment": deploy_result
            }
        else:
            return {
                "edit": edit_result,
                "backup": backup_result
            }
            
    def monitor_and_heal(self):
        """Monitor services and auto-heal if needed"""
        self.logger.info("🩺 Starting monitoring and auto-healing")
        
        services_to_monitor = [
            "chatterfix-cmms",
            "nginx", 
            "fix-it-fred-git"
        ]
        
        healing_actions = []
        
        for service in services_to_monitor:
            status = self.check_service_status(service)
            
            if not status["success"] or "active" not in status["output"]:
                self.logger.warning(f"⚠️ Service {service} is not active, attempting restart")
                restart_result = self.restart_service(service)
                healing_actions.append({
                    "service": service,
                    "action": "restart",
                    "result": restart_result
                })
                
        return healing_actions

def main():
    """Main function for Fix It Fred dev hooks"""
    fred = FixItFredDevHooks()
    
    print("🤖 Fix It Fred Development Hooks Initialized!")
    print(f"🌐 VM IP: {fred.vm_ip}")
    print(f"📁 Repository Path: {REPO_PATH}")
    print("\n✅ Available Commands:")
    print("  fred.execute_vm_command(command, description)")
    print("  fred.restart_service(service_name)")
    print("  fred.deploy_code_to_vm(local_file, remote_path)")
    print("  fred.edit_file_on_vm(file_path, content)")
    print("  fred.git_operations(operation, message)")
    print("  fred.full_deployment_cycle(files_to_deploy)")
    print("  fred.live_code_edit(file_path, old_content, new_content)")
    print("  fred.monitor_and_heal()")
    
    # Test connection
    test_result = fred.execute_vm_command("echo 'Fix It Fred connected successfully!'", "Connection test")
    if test_result["success"]:
        print("🎉 Fix It Fred is connected and ready for autonomous development!")
    else:
        print("⚠️ Connection test failed - check GCP authentication")
        
    return fred

if __name__ == "__main__":
    fred = main()