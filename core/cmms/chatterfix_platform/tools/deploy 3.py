#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Auto-Deployment System
Automated containerization and deployment for apps
"""

import os
import json
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import tempfile
import shutil
import yaml

logger = logging.getLogger(__name__)

class DeploymentConfig:
    """Deployment configuration management"""
    
    def __init__(self):
        self.config = {
            "local": {
                "type": "local",
                "docker_enabled": True,
                "auto_start": True
            },
            "cloud_run": {
                "type": "cloud_run",
                "project_id": "chatterfix-ai-platform",
                "region": "us-central1",
                "min_instances": 0,
                "max_instances": 10,
                "memory": "512Mi",
                "cpu": "1000m"
            },
            "kubernetes": {
                "type": "kubernetes",
                "namespace": "chatterfix-platform",
                "replicas": 1,
                "resources": {
                    "requests": {"memory": "256Mi", "cpu": "250m"},
                    "limits": {"memory": "512Mi", "cpu": "500m"}
                }
            },
            "docker_compose": {
                "type": "docker_compose",
                "compose_file": "docker-compose.platform.yml",
                "network": "chatterfix-platform"
            }
        }
    
    def get_config(self, deployment_type: str) -> Dict[str, Any]:
        """Get deployment configuration"""
        return self.config.get(deployment_type, {})

class DockerBuilder:
    """Docker image builder for apps"""
    
    def __init__(self):
        self.base_images = {
            "python": "python:3.11-slim",
            "node": "node:18-alpine",
            "java": "openjdk:17-jdk-slim"
        }
    
    def build_image(self, app_path: Path, app_name: str, tag: str = "latest") -> bool:
        """Build Docker image for app"""
        try:
            # Check if Dockerfile exists
            dockerfile_path = app_path / "Dockerfile"
            if not dockerfile_path.exists():
                logger.info("No Dockerfile found, generating one...")
                self._generate_dockerfile(app_path)
            
            # Build image
            image_name = f"chatterfix-{app_name}:{tag}"
            cmd = [
                "docker", "build",
                "-t", image_name,
                "-f", str(dockerfile_path),
                str(app_path)
            ]
            
            logger.info(f"Building Docker image: {image_name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully built image: {image_name}")
                return True
            else:
                logger.error(f"❌ Docker build failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Docker build error: {e}")
            return False
    
    def _generate_dockerfile(self, app_path: Path):
        """Generate Dockerfile if not present"""
        # Read plugin manifest to determine app type
        manifest_path = app_path / "plugin.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            app_type = manifest.get("app_type", "ai_service")
            port = manifest.get("port", 8000)
        else:
            app_type = "ai_service"
            port = 8000
        
        # Generate Dockerfile based on app type
        dockerfile_content = f"""# Auto-generated Dockerfile for ChatterFix Platform App
FROM {self.base_images["python"]}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

# Start application
CMD ["python", "main.py"]
"""
        
        dockerfile_path = app_path / "Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info(f"Generated Dockerfile at {dockerfile_path}")
    
    def push_image(self, app_name: str, tag: str = "latest", registry: str = None) -> bool:
        """Push image to registry"""
        try:
            image_name = f"chatterfix-{app_name}:{tag}"
            
            if registry:
                remote_image = f"{registry}/chatterfix-{app_name}:{tag}"
                
                # Tag for registry
                subprocess.run(["docker", "tag", image_name, remote_image], check=True)
                
                # Push to registry
                logger.info(f"Pushing image to registry: {remote_image}")
                result = subprocess.run(["docker", "push", remote_image], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ Successfully pushed image: {remote_image}")
                    return True
                else:
                    logger.error(f"❌ Docker push failed: {result.stderr}")
                    return False
            else:
                logger.info("No registry specified, skipping push")
                return True
                
        except Exception as e:
            logger.error(f"Docker push error: {e}")
            return False

class LocalDeployer:
    """Local deployment manager"""
    
    def __init__(self):
        self.running_containers = {}
    
    def deploy(self, app_name: str, port: int, image_name: str = None) -> bool:
        """Deploy app locally using Docker"""
        try:
            if image_name is None:
                image_name = f"chatterfix-{app_name}:latest"
            
            container_name = f"chatterfix-{app_name}"
            
            # Stop existing container if running
            self.stop(app_name)
            
            # Run new container
            cmd = [
                "docker", "run",
                "-d",
                "--name", container_name,
                "-p", f"{port}:{port}",
                "--network", "chatterfix-platform",
                "-e", f"PORT={port}",
                "-e", "BACKEND_SERVICE_URL=http://backend_unified:8088",
                "-e", "AI_SERVICE_URL=http://ai_unified:8089",
                image_name
            ]
            
            logger.info(f"Starting container: {container_name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                self.running_containers[app_name] = {
                    "container_id": container_id,
                    "container_name": container_name,
                    "port": port,
                    "started_at": datetime.now().isoformat()
                }
                logger.info(f"✅ Successfully deployed {app_name} on port {port}")
                return True
            else:
                logger.error(f"❌ Container start failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Local deployment error: {e}")
            return False
    
    def stop(self, app_name: str) -> bool:
        """Stop local app deployment"""
        try:
            container_name = f"chatterfix-{app_name}"
            
            # Stop container
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            
            # Remove container
            subprocess.run(["docker", "rm", container_name], capture_output=True)
            
            if app_name in self.running_containers:
                del self.running_containers[app_name]
            
            logger.info(f"✅ Stopped {app_name}")
            return True
            
        except Exception as e:
            logger.error(f"Stop deployment error: {e}")
            return False
    
    def status(self, app_name: str = None) -> Dict[str, Any]:
        """Get deployment status"""
        if app_name:
            return self.running_containers.get(app_name, {"status": "not_running"})
        else:
            return self.running_containers

class CloudRunDeployer:
    """Google Cloud Run deployment manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_id = config.get("project_id")
        self.region = config.get("region")
    
    def deploy(self, app_name: str, image_name: str, port: int) -> bool:
        """Deploy to Cloud Run"""
        try:
            service_name = f"chatterfix-{app_name}"
            image_url = f"gcr.io/{self.project_id}/{image_name}"
            
            # Deploy command
            cmd = [
                "gcloud", "run", "deploy", service_name,
                "--image", image_url,
                "--platform", "managed",
                "--region", self.region,
                "--port", str(port),
                "--memory", self.config.get("memory", "512Mi"),
                "--cpu", self.config.get("cpu", "1000m"),
                "--min-instances", str(self.config.get("min_instances", 0)),
                "--max-instances", str(self.config.get("max_instances", 10)),
                "--allow-unauthenticated",
                "--set-env-vars", f"PORT={port}",
                "--quiet"
            ]
            
            logger.info(f"Deploying to Cloud Run: {service_name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully deployed to Cloud Run: {service_name}")
                return True
            else:
                logger.error(f"❌ Cloud Run deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Cloud Run deployment error: {e}")
            return False

class KubernetesDeployer:
    """Kubernetes deployment manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.namespace = config.get("namespace", "chatterfix-platform")
    
    def deploy(self, app_name: str, image_name: str, port: int) -> bool:
        """Deploy to Kubernetes"""
        try:
            # Generate Kubernetes manifests
            manifests = self._generate_k8s_manifests(app_name, image_name, port)
            
            # Apply manifests
            for manifest_name, manifest_content in manifests.items():
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                    yaml.dump(manifest_content, f)
                    temp_file = f.name
                
                cmd = ["kubectl", "apply", "-f", temp_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                os.unlink(temp_file)
                
                if result.returncode != 0:
                    logger.error(f"❌ Failed to apply {manifest_name}: {result.stderr}")
                    return False
            
            logger.info(f"✅ Successfully deployed to Kubernetes: {app_name}")
            return True
            
        except Exception as e:
            logger.error(f"Kubernetes deployment error: {e}")
            return False
    
    def _generate_k8s_manifests(self, app_name: str, image_name: str, port: int) -> Dict[str, Dict]:
        """Generate Kubernetes deployment manifests"""
        service_name = f"chatterfix-{app_name}"
        
        # Deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": service_name,
                "namespace": self.namespace,
                "labels": {"app": service_name, "platform": "chatterfix"}
            },
            "spec": {
                "replicas": self.config.get("replicas", 1),
                "selector": {"matchLabels": {"app": service_name}},
                "template": {
                    "metadata": {"labels": {"app": service_name}},
                    "spec": {
                        "containers": [{
                            "name": service_name,
                            "image": image_name,
                            "ports": [{"containerPort": port}],
                            "env": [
                                {"name": "PORT", "value": str(port)},
                                {"name": "BACKEND_SERVICE_URL", "value": "http://backend-unified:8088"},
                                {"name": "AI_SERVICE_URL", "value": "http://ai-unified:8089"}
                            ],
                            "resources": self.config.get("resources", {}),
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": port},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            }
                        }]
                    }
                }
            }
        }
        
        # Service manifest
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service_name,
                "namespace": self.namespace,
                "labels": {"app": service_name, "platform": "chatterfix"}
            },
            "spec": {
                "selector": {"app": service_name},
                "ports": [{"port": 80, "targetPort": port}],
                "type": "ClusterIP"
            }
        }
        
        return {
            "deployment": deployment,
            "service": service
        }

class DeploymentManager:
    """Main deployment manager"""
    
    def __init__(self):
        self.config = DeploymentConfig()
        self.docker_builder = DockerBuilder()
        self.deployers = {
            "local": LocalDeployer(),
            "cloud_run": None,  # Initialized when needed
            "kubernetes": None,  # Initialized when needed
        }
        self.plugins_dir = Path("platform/plugins")
    
    def deploy_app(self, app_name: str, deployment_type: str = "local", 
                   build_image: bool = True, push_image: bool = False) -> bool:
        """Deploy an app"""
        try:
            logger.info(f"🚀 Deploying {app_name} ({deployment_type})")
            
            # Check if app exists
            app_path = self.plugins_dir / app_name
            if not app_path.exists():
                logger.error(f"❌ App not found: {app_name}")
                return False
            
            # Read app manifest
            manifest_path = app_path / "plugin.json"
            if not manifest_path.exists():
                logger.error(f"❌ No plugin.json found for {app_name}")
                return False
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            port = manifest.get("port", 8000)
            
            # Build Docker image if requested
            if build_image:
                if not self.docker_builder.build_image(app_path, app_name):
                    return False
            
            # Push image if requested
            if push_image:
                if not self.docker_builder.push_image(app_name):
                    return False
            
            # Get deployment configuration
            deploy_config = self.config.get_config(deployment_type)
            if not deploy_config:
                logger.error(f"❌ Unknown deployment type: {deployment_type}")
                return False
            
            # Initialize deployer if needed
            if deployment_type not in self.deployers or self.deployers[deployment_type] is None:
                if deployment_type == "cloud_run":
                    self.deployers[deployment_type] = CloudRunDeployer(deploy_config)
                elif deployment_type == "kubernetes":
                    self.deployers[deployment_type] = KubernetesDeployer(deploy_config)
            
            # Deploy
            deployer = self.deployers[deployment_type]
            image_name = f"chatterfix-{app_name}:latest"
            
            success = deployer.deploy(app_name, port if deployment_type == "local" else image_name, port)
            
            if success:
                logger.info(f"✅ Successfully deployed {app_name}")
                
                # Update plugin status
                self._update_plugin_status(app_name, "deployed", deployment_type)
            else:
                logger.error(f"❌ Failed to deploy {app_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False
    
    def stop_app(self, app_name: str, deployment_type: str = "local") -> bool:
        """Stop an app deployment"""
        try:
            deployer = self.deployers.get(deployment_type)
            if deployer and hasattr(deployer, 'stop'):
                success = deployer.stop(app_name)
                if success:
                    self._update_plugin_status(app_name, "stopped", deployment_type)
                return success
            else:
                logger.warning(f"Stop not supported for deployment type: {deployment_type}")
                return False
                
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return False
    
    def get_status(self, app_name: str = None, deployment_type: str = "local") -> Dict[str, Any]:
        """Get deployment status"""
        deployer = self.deployers.get(deployment_type)
        if deployer and hasattr(deployer, 'status'):
            return deployer.status(app_name)
        else:
            return {"error": f"Status not supported for deployment type: {deployment_type}"}
    
    def list_deployable_apps(self) -> List[str]:
        """List all deployable apps"""
        apps = []
        if self.plugins_dir.exists():
            for app_dir in self.plugins_dir.iterdir():
                if app_dir.is_dir() and (app_dir / "plugin.json").exists():
                    apps.append(app_dir.name)
        return apps
    
    def _update_plugin_status(self, app_name: str, status: str, deployment_type: str):
        """Update plugin deployment status"""
        # This could be expanded to update a database or registry
        logger.info(f"Plugin {app_name} status: {status} ({deployment_type})")
    
    def setup_docker_network(self):
        """Setup Docker network for local development"""
        try:
            # Create platform network if it doesn't exist
            result = subprocess.run(
                ["docker", "network", "create", "chatterfix-platform"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Created Docker network: chatterfix-platform")
            elif "already exists" in result.stderr:
                logger.info("ℹ️  Docker network already exists: chatterfix-platform")
            else:
                logger.warning(f"Network creation warning: {result.stderr}")
            
        except Exception as e:
            logger.error(f"Network setup error: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="ChatterFix Platform Deployment Tool")
    parser.add_argument("command", choices=["deploy", "stop", "status", "list", "setup"], help="Command to execute")
    parser.add_argument("--app", "-a", help="App name")
    parser.add_argument("--type", "-t", default="local", choices=["local", "cloud_run", "kubernetes"], help="Deployment type")
    parser.add_argument("--build", "-b", action="store_true", default=True, help="Build Docker image")
    parser.add_argument("--push", "-p", action="store_true", help="Push image to registry")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    manager = DeploymentManager()
    
    if args.command == "setup":
        manager.setup_docker_network()
    elif args.command == "list":
        apps = manager.list_deployable_apps()
        print("📱 Deployable Apps:")
        for app in apps:
            print(f"  • {app}")
    elif args.command == "deploy":
        if not args.app:
            print("❌ App name required for deploy command")
            return
        manager.deploy_app(args.app, args.type, args.build, args.push)
    elif args.command == "stop":
        if not args.app:
            print("❌ App name required for stop command")
            return
        manager.stop_app(args.app, args.type)
    elif args.command == "status":
        status = manager.get_status(args.app, args.type)
        print(f"📊 Deployment Status ({args.type}):")
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()