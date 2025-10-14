#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Command Line Interface
Unified CLI for platform management
"""

import argparse
import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import importlib.util

# Add platform to path
sys.path.append(str(Path(__file__).parent))

class ChatterFixCLI:
    """Main CLI class for ChatterFix platform"""
    
    def __init__(self):
        self.platform_dir = Path(__file__).parent / "platform"
        self.tools_dir = self.platform_dir / "tools"
        
    def create_app(self, args):
        """Create a new app using the app generator"""
        try:
            # Import and use the app generator
            spec = importlib.util.spec_from_file_location(
                "create_app", 
                self.tools_dir / "create_app.py"
            )
            create_app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(create_app_module)
            
            generator = create_app_module.AppGenerator()
            
            if args.template and args.name:
                # Non-interactive mode
                variables = {}
                if args.variables:
                    for var_def in args.variables:
                        key, value = var_def.split('=', 1)
                        variables[key] = value
                
                success = generator.create_app(args.template, args.name, variables)
                if success:
                    print(f"✅ Successfully created app: {args.name}")
                else:
                    print(f"❌ Failed to create app: {args.name}")
            else:
                # Interactive mode
                generator.interactive_create()
                
        except Exception as e:
            print(f"❌ Error creating app: {e}")
            return False
        
        return True
    
    def deploy_app(self, args):
        """Deploy an app using the deployment system"""
        try:
            # Import and use the deployment manager
            spec = importlib.util.spec_from_file_location(
                "deploy", 
                self.tools_dir / "deploy.py"
            )
            deploy_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(deploy_module)
            
            manager = deploy_module.DeploymentManager()
            
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
                    return False
                
                success = manager.deploy_app(
                    args.app, 
                    args.type, 
                    args.build, 
                    args.push
                )
                
                if success:
                    print(f"✅ Successfully deployed: {args.app}")
                else:
                    print(f"❌ Failed to deploy: {args.app}")
                    
            elif args.command == "stop":
                if not args.app:
                    print("❌ App name required for stop command")
                    return False
                
                success = manager.stop_app(args.app, args.type)
                if success:
                    print(f"✅ Successfully stopped: {args.app}")
                else:
                    print(f"❌ Failed to stop: {args.app}")
                    
            elif args.command == "status":
                status = manager.get_status(args.app, args.type)
                print(f"📊 Deployment Status ({args.type}):")
                print(json.dumps(status, indent=2))
                
        except Exception as e:
            print(f"❌ Error with deployment: {e}")
            return False
        
        return True
    
    def start_platform(self, args):
        """Start the platform gateway"""
        try:
            gateway_file = Path(__file__).parent / "platform_gateway.py"
            
            if not gateway_file.exists():
                print("❌ Platform gateway not found")
                return False
            
            port = getattr(args, 'port', 8000)
            host = getattr(args, 'host', '0.0.0.0')
            
            print(f"🚀 Starting ChatterFix AI Development Platform Gateway")
            print(f"   Host: {host}")
            print(f"   Port: {port}")
            print(f"   URL: http://{host}:{port}")
            print()
            
            # Start the platform gateway
            cmd = [
                sys.executable, str(gateway_file),
                "--host", host,
                "--port", str(port)
            ]
            
            if args.reload:
                cmd.extend(["--reload"])
            
            subprocess.run(cmd)
            
        except KeyboardInterrupt:
            print("\n🛑 Platform gateway stopped")
        except Exception as e:
            print(f"❌ Error starting platform: {e}")
            return False
        
        return True
    
    def list_apps(self, args):
        """List all apps in the platform"""
        plugins_dir = self.platform_dir / "plugins"
        
        if not plugins_dir.exists():
            print("📂 No plugins directory found")
            return True
        
        apps = []
        for app_dir in plugins_dir.iterdir():
            if app_dir.is_dir():
                manifest_path = app_dir / "plugin.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        
                        apps.append({
                            "name": manifest.get("name", app_dir.name),
                            "version": manifest.get("version", "unknown"),
                            "description": manifest.get("description", "No description"),
                            "type": manifest.get("app_type", "unknown"),
                            "enabled": manifest.get("enabled", False),
                            "port": manifest.get("port", "N/A")
                        })
                    except Exception as e:
                        print(f"⚠️  Error reading manifest for {app_dir.name}: {e}")
        
        if not apps:
            print("📱 No apps found in platform")
            return True
        
        print("📱 ChatterFix Platform Apps:")
        print("=" * 80)
        print(f"{'Name':<20} {'Version':<10} {'Type':<15} {'Port':<8} {'Status':<10} {'Description'}")
        print("-" * 80)
        
        for app in apps:
            status = "Enabled" if app["enabled"] else "Disabled"
            print(f"{app['name']:<20} {app['version']:<10} {app['type']:<15} {str(app['port']):<8} {status:<10} {app['description'][:30]}")
        
        print(f"\nTotal: {len(apps)} apps")
        return True
    
    def show_status(self, args):
        """Show platform status"""
        try:
            import httpx
            
            # Try to connect to the platform gateway
            try:
                response = httpx.get("http://localhost:8000/platform/status", timeout=5)
                if response.status_code == 200:
                    status = response.json()
                    
                    print("🟢 ChatterFix AI Development Platform - Status")
                    print("=" * 60)
                    print(f"Platform: {status['platform']['name']} v{status['platform']['version']}")
                    print(f"Uptime: {status['platform'].get('uptime', 'N/A')} seconds")
                    print(f"Routes: {status.get('routes', 0)} registered")
                    print()
                    
                    # Show plugin status
                    plugins = status.get('plugins', {})
                    if plugins:
                        print("📱 Plugins:")
                        for name, plugin_info in plugins.items():
                            status_emoji = "🟢" if plugin_info['status'] == 'running' else "🔴"
                            print(f"  {status_emoji} {name} - {plugin_info['status']}")
                    
                    # Show service status
                    services = status.get('services', {})
                    if services:
                        print("\n🔧 Services:")
                        service_list = services.get('services', {})
                        for name, service_info in service_list.items():
                            status_emoji = "🟢" if service_info['status'] == 'healthy' else "🔴"
                            print(f"  {status_emoji} {name} - {service_info['status']}")
                    
                    return True
                    
            except httpx.RequestError:
                print("🔴 Platform Gateway not running")
                print("   Start with: chatterfix start")
                
        except ImportError:
            print("❌ httpx not available for status check")
        
        # Fallback: show local status
        self.list_apps(args)
        return True
    
    def show_info(self, args):
        """Show platform information"""
        print("🚀 ChatterFix AI Development Platform")
        print("=" * 50)
        print("Version: 1.0.0")
        print("Description: Seamless app ecosystem for AI development teams")
        print()
        print("Features:")
        print("  ✅ Plugin Architecture")
        print("  ✅ Auto-discovery & Registration")
        print("  ✅ Unified API Gateway")
        print("  ✅ Shared Services Framework")
        print("  ✅ Auto-deployment System")
        print("  ✅ Event-driven Communication")
        print("  ✅ Configuration Management")
        print()
        print("Quick Start:")
        print("  1. chatterfix create-app")
        print("  2. chatterfix deploy <app-name>")
        print("  3. chatterfix start")
        print()
        print("Documentation: https://chatterfix.ai/docs")
        
        return True

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ChatterFix AI Development Platform CLI",
        prog="chatterfix"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create app command
    create_parser = subparsers.add_parser("create-app", help="Create a new app")
    create_parser.add_argument("--template", "-t", help="Template name (ai_service, web_app, api)")
    create_parser.add_argument("--name", "-n", help="App name")
    create_parser.add_argument("--variables", "-v", action="append", help="Template variables (key=value)")
    
    # Deploy commands
    deploy_parser = subparsers.add_parser("deploy", help="Deploy an app")
    deploy_parser.add_argument("deploy_command", choices=["setup", "list", "deploy", "stop", "status"])
    deploy_parser.add_argument("--app", "-a", help="App name")
    deploy_parser.add_argument("--type", "-t", default="local", choices=["local", "cloud_run", "kubernetes"])
    deploy_parser.add_argument("--build", "-b", action="store_true", default=True)
    deploy_parser.add_argument("--push", "-p", action="store_true")
    
    # Start platform command
    start_parser = subparsers.add_parser("start", help="Start the platform gateway")
    start_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    start_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    start_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # List apps command
    subparsers.add_parser("list", help="List all apps")
    
    # Status command
    subparsers.add_parser("status", help="Show platform status")
    
    # Info command
    subparsers.add_parser("info", help="Show platform information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ChatterFixCLI()
    
    # Route commands
    success = True
    if args.command == "create-app":
        success = cli.create_app(args)
    elif args.command == "deploy":
        # Restructure args for deploy function
        deploy_args = argparse.Namespace()
        deploy_args.command = args.deploy_command
        deploy_args.app = args.app
        deploy_args.type = args.type
        deploy_args.build = args.build
        deploy_args.push = args.push
        success = cli.deploy_app(deploy_args)
    elif args.command == "start":
        success = cli.start_platform(args)
    elif args.command == "list":
        success = cli.list_apps(args)
    elif args.command == "status":
        success = cli.show_status(args)
    elif args.command == "info":
        success = cli.show_info(args)
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()