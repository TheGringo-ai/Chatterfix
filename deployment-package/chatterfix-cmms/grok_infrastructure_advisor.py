#!/usr/bin/env python3
"""
Grok Infrastructure Advisor - AI-powered GCP and VM management with user approval
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import compute_v1
from google.cloud import run_v2
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Grok Infrastructure Advisor", version="1.0.0")

# Set up Google Cloud authentication
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'grok-ai-advisor-key.json'

class InfrastructureChange(BaseModel):
    action: str
    resource_type: str
    resource_name: str
    parameters: Dict
    reason: str
    estimated_cost: str = "Unknown"
    risk_level: str = "Medium"

class ApprovalRequest(BaseModel):
    change_id: str
    approved: bool
    user_comment: Optional[str] = None

# Global state for pending changes
pending_changes: Dict[str, InfrastructureChange] = {}
change_counter = 0

class GrokGCPMonitor:
    """Grok's GCP monitoring and advisory system"""
    
    def __init__(self):
        self.compute_client = compute_v1.InstancesClient()
        self.run_client = run_v2.ServicesClient()
        self.project_id = "fredfix"
        self.zone = "us-central1-a"
    
    async def get_compute_instances(self) -> List[Dict]:
        """Get all compute instances"""
        try:
            request = compute_v1.ListInstancesRequest(
                project=self.project_id,
                zone=self.zone
            )
            instances = []
            for instance in self.compute_client.list(request=request):
                instances.append({
                    "name": instance.name,
                    "status": instance.status,
                    "machine_type": instance.machine_type.split('/')[-1],
                    "zone": instance.zone.split('/')[-1],
                    "creation_timestamp": instance.creation_timestamp,
                    "cpu_platform": instance.cpu_platform,
                    "network_interfaces": len(instance.network_interfaces),
                    "disks": len(instance.disks)
                })
            return instances
        except Exception as e:
            logger.error(f"Error getting compute instances: {e}")
            return []
    
    async def get_cloud_run_services(self) -> List[Dict]:
        """Get all Cloud Run services"""
        try:
            services = []
            # Note: Using gcloud command since Cloud Run v2 client is complex
            result = subprocess.run(
                ['gcloud', 'run', 'services', 'list', '--format=json'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                services_data = json.loads(result.stdout)
                for service in services_data:
                    services.append({
                        "name": service.get("metadata", {}).get("name"),
                        "url": service.get("status", {}).get("url"),
                        "region": service.get("metadata", {}).get("labels", {}).get("cloud.googleapis.com/location"),
                        "ready": service.get("status", {}).get("conditions", [{}])[0].get("status") == "True",
                        "creation_time": service.get("metadata", {}).get("creationTimestamp")
                    })
            return services
        except Exception as e:
            logger.error(f"Error getting Cloud Run services: {e}")
            return []
    
    async def analyze_infrastructure(self) -> Dict:
        """Comprehensive infrastructure analysis for Grok"""
        
        instances = await self.get_compute_instances()
        services = await self.get_cloud_run_services()
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "project_id": self.project_id,
            "compute_instances": {
                "total": len(instances),
                "running": len([i for i in instances if i["status"] == "RUNNING"]),
                "details": instances
            },
            "cloud_run_services": {
                "total": len(services),
                "ready": len([s for s in services if s["ready"]]),
                "details": services
            },
            "recommendations": await self.generate_recommendations(instances, services)
        }
        
        return analysis
    
    async def generate_recommendations(self, instances: List[Dict], services: List[Dict]) -> List[Dict]:
        """Generate Grok's AI recommendations"""
        
        recommendations = []
        
        # VM Optimization recommendations
        running_instances = [i for i in instances if i["status"] == "RUNNING"]
        if len(running_instances) > 1:
            recommendations.append({
                "type": "cost_optimization",
                "priority": "medium",
                "title": "Multiple VM Instances Running",
                "description": f"You have {len(running_instances)} VM instances running. Consider consolidating workloads.",
                "potential_savings": "20-40% on compute costs",
                "action": "consolidate_vms"
            })
        
        # Cloud Run scaling recommendations
        if len(services) > 5:
            recommendations.append({
                "type": "architecture",
                "priority": "low",
                "title": "Consider Service Mesh",
                "description": f"With {len(services)} Cloud Run services, consider implementing service mesh for better observability.",
                "potential_benefit": "Improved monitoring and security",
                "action": "implement_service_mesh"
            })
        
        # Security recommendations
        recommendations.append({
            "type": "security",
            "priority": "high",
            "title": "Regular Security Audit",
            "description": "Ensure all services have proper IAM roles and network security groups.",
            "potential_benefit": "Enhanced security posture",
            "action": "security_audit"
        })
        
        return recommendations

gcp_monitor = GrokGCPMonitor()

@app.get("/")
async def root():
    """Grok Infrastructure Advisor status"""
    return {
        "service": "Grok Infrastructure Advisor",
        "status": "active",
        "capabilities": [
            "GCP monitoring",
            "VM analysis", 
            "Cloud Run oversight",
            "AI recommendations",
            "Change management with approval"
        ],
        "permissions": "Read-only with approval-based changes",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/grok/infrastructure/status")
async def get_infrastructure_status():
    """Get comprehensive infrastructure status for Grok"""
    
    try:
        analysis = await gcp_monitor.analyze_infrastructure()
        
        # Add VM system information
        vm_info = await get_vm_system_info()
        analysis["vm_system"] = vm_info
        
        return {
            "grok_analysis": "Infrastructure successfully analyzed",
            "infrastructure": analysis,
            "grok_recommendations": analysis["recommendations"],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Infrastructure analysis error: {str(e)}")

async def get_vm_system_info() -> Dict:
    """Get current VM system information"""
    try:
        # Get disk usage
        disk_result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        
        # Get memory usage
        memory_result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        
        # Get CPU info
        cpu_result = subprocess.run(['nproc'], capture_output=True, text=True)
        
        # Get system load
        load_result = subprocess.run(['uptime'], capture_output=True, text=True)
        
        return {
            "disk_usage": disk_result.stdout if disk_result.returncode == 0 else "Unknown",
            "memory_usage": memory_result.stdout if memory_result.returncode == 0 else "Unknown", 
            "cpu_cores": cpu_result.stdout.strip() if cpu_result.returncode == 0 else "Unknown",
            "system_load": load_result.stdout.strip() if load_result.returncode == 0 else "Unknown",
            "services_running": await check_local_services()
        }
    except Exception as e:
        return {"error": str(e)}

async def check_local_services() -> Dict:
    """Check status of local Fix It Fred services"""
    services = {
        "chatterfix": {"port": 8000, "status": "unknown"},
        "fix_it_fred": {"port": 8080, "status": "unknown"},
        "ai_brain": {"port": 8005, "status": "unknown"},
        "grok_connector": {"port": 8006, "status": "unknown"},
        "dev_console": {"port": 9001, "status": "unknown"}
    }
    
    async with httpx.AsyncClient(timeout=2.0) as client:
        for service, info in services.items():
            try:
                response = await client.get(f"http://localhost:{info['port']}/health")
                services[service]["status"] = "online" if response.status_code == 200 else "error"
            except:
                try:
                    response = await client.get(f"http://localhost:{info['port']}/")
                    services[service]["status"] = "online" if response.status_code == 200 else "error"
                except:
                    services[service]["status"] = "offline"
    
    return services

@app.post("/grok/infrastructure/suggest-change")
async def suggest_infrastructure_change(change: InfrastructureChange):
    """Grok suggests an infrastructure change that requires approval"""
    
    global change_counter, pending_changes
    change_counter += 1
    change_id = f"grok_change_{change_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    pending_changes[change_id] = change
    
    return {
        "message": "Grok has suggested an infrastructure change",
        "change_id": change_id,
        "change_details": change.dict(),
        "status": "pending_approval",
        "approval_required": True,
        "approval_endpoint": f"/grok/infrastructure/approve/{change_id}",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/grok/infrastructure/pending-changes")
async def get_pending_changes():
    """Get all pending changes waiting for approval"""
    
    return {
        "pending_changes": {
            change_id: change.dict() 
            for change_id, change in pending_changes.items()
        },
        "total_pending": len(pending_changes),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/grok/infrastructure/approve/{change_id}")
async def approve_change(change_id: str, approval: ApprovalRequest):
    """Approve or reject a suggested change"""
    
    if change_id not in pending_changes:
        raise HTTPException(status_code=404, detail="Change not found")
    
    change = pending_changes[change_id]
    
    if approval.approved:
        # Execute the approved change
        result = await execute_infrastructure_change(change)
        del pending_changes[change_id]
        
        return {
            "message": "Change approved and executed",
            "change_id": change_id,
            "execution_result": result,
            "user_comment": approval.user_comment,
            "timestamp": datetime.now().isoformat()
        }
    else:
        del pending_changes[change_id]
        return {
            "message": "Change rejected",
            "change_id": change_id,
            "user_comment": approval.user_comment,
            "timestamp": datetime.now().isoformat()
        }

async def execute_infrastructure_change(change: InfrastructureChange) -> Dict:
    """Execute an approved infrastructure change"""
    
    try:
        if change.action == "restart_service":
            # Restart a local service
            service_name = change.parameters.get("service_name")
            result = subprocess.run(['systemctl', 'restart', service_name], 
                                  capture_output=True, text=True)
            return {
                "action": "restart_service",
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        
        elif change.action == "scale_cloud_run":
            # Scale Cloud Run service
            service_name = change.parameters.get("service_name")
            max_instances = change.parameters.get("max_instances")
            result = subprocess.run([
                'gcloud', 'run', 'services', 'update', service_name,
                '--max-instances', str(max_instances)
            ], capture_output=True, text=True)
            return {
                "action": "scale_cloud_run",
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        
        elif change.action == "start_vm":
            # Start a VM instance
            instance_name = change.parameters.get("instance_name", "chatterfix-vm")
            zone = change.parameters.get("zone", "us-central1-a")
            result = subprocess.run([
                'gcloud', 'compute', 'instances', 'start', instance_name,
                '--zone', zone
            ], capture_output=True, text=True)
            return {
                "action": "start_vm",
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        
        elif change.action == "stop_vm":
            # Stop a VM instance
            instance_name = change.parameters.get("instance_name", "chatterfix-vm")
            zone = change.parameters.get("zone", "us-central1-a")
            result = subprocess.run([
                'gcloud', 'compute', 'instances', 'stop', instance_name,
                '--zone', zone
            ], capture_output=True, text=True)
            return {
                "action": "stop_vm",
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        
        elif change.action == "restart_vm":
            # Restart a VM instance
            instance_name = change.parameters.get("instance_name", "chatterfix-vm")
            zone = change.parameters.get("zone", "us-central1-a")
            result = subprocess.run([
                'gcloud', 'compute', 'instances', 'reset', instance_name,
                '--zone', zone
            ], capture_output=True, text=True)
            return {
                "action": "restart_vm",
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        
        elif change.action == "edit_file":
            # Edit a file on the VM
            return await execute_vm_file_edit(change.parameters)
        
        elif change.action == "run_vm_command":
            # Run a command on the VM
            return await execute_vm_command(change.parameters)
        
        elif change.action == "update_vm_size":
            # This would require stopping the VM first - high risk
            return {
                "action": "update_vm_size",
                "success": False,
                "error": "VM resizing requires downtime - not implemented for safety"
            }
        
        else:
            return {
                "action": change.action,
                "success": False,
                "error": f"Unknown action: {change.action}"
            }
            
    except Exception as e:
        return {
            "action": change.action,
            "success": False,
            "error": str(e)
        }

async def execute_vm_file_edit(parameters: Dict) -> Dict:
    """Execute file edit on VM via SSH"""
    try:
        instance_name = parameters.get("instance_name", "chatterfix-vm")
        zone = parameters.get("zone", "us-central1-a")
        file_path = parameters.get("file_path")
        file_content = parameters.get("file_content")
        backup = parameters.get("backup", True)
        
        if not file_path or not file_content:
            return {
                "action": "edit_file",
                "success": False,
                "error": "Missing file_path or file_content"
            }
        
        # Create backup if requested
        if backup:
            backup_cmd = f"sudo cp {file_path} {file_path}.grok_backup_$(date +%Y%m%d_%H%M%S)"
            backup_result = subprocess.run([
                'gcloud', 'compute', 'ssh', instance_name,
                '--zone', zone,
                '--command', backup_cmd
            ], capture_output=True, text=True)
            
            if backup_result.returncode != 0:
                return {
                    "action": "edit_file",
                    "success": False,
                    "error": f"Backup failed: {backup_result.stderr}"
                }
        
        # Write new content to file
        write_cmd = f"sudo tee {file_path} > /dev/null << 'GROK_EOF'\n{file_content}\nGROK_EOF"
        edit_result = subprocess.run([
            'gcloud', 'compute', 'ssh', instance_name,
            '--zone', zone,
            '--command', write_cmd
        ], capture_output=True, text=True)
        
        return {
            "action": "edit_file",
            "success": edit_result.returncode == 0,
            "output": edit_result.stdout,
            "error": edit_result.stderr if edit_result.returncode != 0 else None,
            "file_path": file_path,
            "backup_created": backup
        }
        
    except Exception as e:
        return {
            "action": "edit_file",
            "success": False,
            "error": str(e)
        }

async def execute_vm_command(parameters: Dict) -> Dict:
    """Execute command on VM via SSH"""
    try:
        instance_name = parameters.get("instance_name", "chatterfix-vm")
        zone = parameters.get("zone", "us-central1-a")
        command = parameters.get("command")
        
        if not command:
            return {
                "action": "run_vm_command",
                "success": False,
                "error": "Missing command parameter"
            }
        
        # Execute command on VM
        result = subprocess.run([
            'gcloud', 'compute', 'ssh', instance_name,
            '--zone', zone,
            '--command', command
        ], capture_output=True, text=True)
        
        return {
            "action": "run_vm_command",
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "command": command,
            "exit_code": result.returncode
        }
        
    except Exception as e:
        return {
            "action": "run_vm_command",
            "success": False,
            "error": str(e)
        }

@app.post("/grok/infrastructure/emergency-analysis")
async def emergency_infrastructure_analysis():
    """Grok performs emergency infrastructure analysis"""
    
    try:
        # Get current status
        analysis = await gcp_monitor.analyze_infrastructure()
        
        # Check for immediate issues
        issues = []
        
        # Check VM status
        running_vms = analysis["compute_instances"]["running"]
        total_vms = analysis["compute_instances"]["total"]
        if running_vms < total_vms:
            issues.append({
                "severity": "high",
                "type": "vm_down",
                "message": f"{total_vms - running_vms} VM(s) not running",
                "recommendation": "Check VM logs and restart if needed"
            })
        
        # Check Cloud Run services
        ready_services = analysis["cloud_run_services"]["ready"]
        total_services = analysis["cloud_run_services"]["total"]
        if ready_services < total_services:
            issues.append({
                "severity": "medium",
                "type": "service_not_ready",
                "message": f"{total_services - ready_services} Cloud Run service(s) not ready",
                "recommendation": "Check service logs and deployment status"
            })
        
        # Check local services
        vm_info = analysis.get("vm_system", {})
        local_services = vm_info.get("services_running", {})
        offline_services = [name for name, info in local_services.items() 
                           if info.get("status") == "offline"]
        
        if offline_services:
            issues.append({
                "severity": "high", 
                "type": "local_services_down",
                "message": f"Local services offline: {', '.join(offline_services)}",
                "recommendation": "Restart offline services immediately"
            })
        
        return {
            "grok_emergency_analysis": "Infrastructure emergency scan complete",
            "overall_status": "critical" if any(i["severity"] == "high" for i in issues) else "warning" if issues else "healthy",
            "issues_found": len(issues),
            "issues": issues,
            "full_analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emergency analysis failed: {str(e)}")

@app.post("/grok/vm/suggest-restart")
async def suggest_vm_restart(message_data: Dict):
    """Grok suggests VM restart with approval"""
    
    global change_counter, pending_changes
    change_counter += 1
    change_id = f"vm_restart_{change_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    change = InfrastructureChange(
        action="restart_vm",
        resource_type="compute_instance",
        resource_name="chatterfix-vm",
        parameters={
            "instance_name": "chatterfix-vm",
            "zone": "us-central1-a"
        },
        reason=f"Grok suggests VM restart: {message_data.get('message', 'No reason provided')}",
        estimated_cost="Free",
        risk_level="High"  # VM restart has downtime
    )
    
    pending_changes[change_id] = change
    
    return {
        "message": "Grok suggests VM restart",
        "change_id": change_id,
        "warning": "VM restart will cause downtime",
        "reason": change.reason,
        "approval_required": True,
        "risk_level": "High",
        "approval_endpoint": f"/grok/infrastructure/approve/{change_id}",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/grok/vm/suggest-file-edit")
async def suggest_vm_file_edit(file_edit_data: Dict):
    """Grok suggests file edit on VM with approval"""
    
    global change_counter, pending_changes
    change_counter += 1
    change_id = f"file_edit_{change_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    change = InfrastructureChange(
        action="edit_file",
        resource_type="vm_file",
        resource_name=file_edit_data.get("file_path", "unknown"),
        parameters={
            "instance_name": file_edit_data.get("instance_name", "chatterfix-vm"),
            "zone": file_edit_data.get("zone", "us-central1-a"),
            "file_path": file_edit_data.get("file_path"),
            "file_content": file_edit_data.get("file_content"),
            "backup": file_edit_data.get("backup", True)
        },
        reason=f"Grok suggests file edit: {file_edit_data.get('reason', 'No reason provided')}",
        estimated_cost="Free",
        risk_level=file_edit_data.get("risk_level", "Medium")
    )
    
    pending_changes[change_id] = change
    
    return {
        "message": "Grok suggests file edit on VM",
        "change_id": change_id,
        "file_path": file_edit_data.get("file_path"),
        "backup_enabled": file_edit_data.get("backup", True),
        "reason": change.reason,
        "approval_required": True,
        "risk_level": change.risk_level,
        "approval_endpoint": f"/grok/infrastructure/approve/{change_id}",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/grok/vm/suggest-command")
async def suggest_vm_command(command_data: Dict):
    """Grok suggests running command on VM with approval"""
    
    global change_counter, pending_changes
    change_counter += 1
    change_id = f"vm_command_{change_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Assess risk level based on command
    command = command_data.get("command", "")
    risk_level = "Low"
    if any(dangerous in command.lower() for dangerous in ["rm -rf", "sudo rm", "format", "mkfs", "dd if="]):
        risk_level = "Critical"
    elif any(risky in command.lower() for risky in ["sudo", "systemctl", "service", "kill", "pkill"]):
        risk_level = "High"
    elif any(medium in command.lower() for medium in ["install", "update", "upgrade", "restart"]):
        risk_level = "Medium"
    
    change = InfrastructureChange(
        action="run_vm_command",
        resource_type="vm_command",
        resource_name="chatterfix-vm",
        parameters={
            "instance_name": command_data.get("instance_name", "chatterfix-vm"),
            "zone": command_data.get("zone", "us-central1-a"),
            "command": command
        },
        reason=f"Grok suggests VM command: {command_data.get('reason', 'No reason provided')}",
        estimated_cost="Free",
        risk_level=risk_level
    )
    
    pending_changes[change_id] = change
    
    return {
        "message": "Grok suggests VM command execution",
        "change_id": change_id,
        "command": command,
        "reason": change.reason,
        "approval_required": True,
        "risk_level": risk_level,
        "risk_assessment": get_command_risk_assessment(command),
        "approval_endpoint": f"/grok/infrastructure/approve/{change_id}",
        "timestamp": datetime.now().isoformat()
    }

def get_command_risk_assessment(command: str) -> Dict:
    """Assess the risk of a command"""
    
    risk_indicators = {
        "critical": ["rm -rf", "format", "mkfs", "dd if=", "fdisk", "> /dev/"],
        "high": ["sudo rm", "systemctl stop", "kill -9", "reboot", "shutdown"],
        "medium": ["sudo", "systemctl restart", "service restart", "install", "update"],
        "low": ["ls", "cat", "echo", "ps", "df", "free", "uptime"]
    }
    
    assessment = {
        "level": "Low",
        "indicators": [],
        "warnings": []
    }
    
    command_lower = command.lower()
    
    for level, indicators in risk_indicators.items():
        for indicator in indicators:
            if indicator in command_lower:
                assessment["level"] = level.title()
                assessment["indicators"].append(indicator)
                
                if level == "critical":
                    assessment["warnings"].append("⚠️  CRITICAL: Command may cause data loss")
                elif level == "high":
                    assessment["warnings"].append("⚠️  HIGH: Command may cause service disruption")
                elif level == "medium":
                    assessment["warnings"].append("⚠️  MEDIUM: Command may modify system state")
    
    return assessment

if __name__ == "__main__":
    import uvicorn
    print("🤖 Grok Infrastructure Advisor Starting...")
    print("🔍 Monitoring GCP resources with AI insights")
    print("🏗️  VM control and file management enabled")
    print("⚠️  All changes require user approval")
    uvicorn.run(app, host="0.0.0.0", port=8007)