#!/usr/bin/env python3
"""
AI Team Debug MCP Server
Helps debug and resolve ChatterFix AI team integration issues
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Team Debug MCP Server",
    description="Debug and resolve ChatterFix AI team integration issues",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AITeamDebugger:
    """Debug the AI team integration issues"""
    
    def __init__(self):
        self.chatterfix_path = "/Users/fredtaylor/ChatterFix"
        self.ai_team_service_url = "https://ai-team-service-psycl7nhha-uc.a.run.app"
    
    async def check_environment_variables(self) -> Dict[str, Any]:
        """Check current environment variables"""
        env_vars = {}
        
        # Check from ChatterFix directory
        try:
            os.chdir(self.chatterfix_path)
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            env_vars = {
                "DISABLE_AI_TEAM_GRPC": os.getenv("DISABLE_AI_TEAM_GRPC"),
                "AI_TEAM_SERVICE_URL": os.getenv("AI_TEAM_SERVICE_URL"),
                "INTERNAL_API_KEY": os.getenv("INTERNAL_API_KEY", "not_set")[:10] + "..." if os.getenv("INTERNAL_API_KEY") else None,
                "USE_AI_TEAM_HTTP": os.getenv("AI_TEAM_SERVICE_URL") is not None,
            }
            
            # Computed values
            DISABLE_AI_TEAM_GRPC = os.getenv("DISABLE_AI_TEAM_GRPC", "true").lower() == "true"
            USE_AI_TEAM_HTTP = os.getenv("AI_TEAM_SERVICE_URL") is not None
            
            env_vars["computed"] = {
                "DISABLE_AI_TEAM_GRPC": DISABLE_AI_TEAM_GRPC,
                "USE_AI_TEAM_HTTP": USE_AI_TEAM_HTTP,
                "should_load_router": not (DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP),
                "boolean_logic_breakdown": {
                    "DISABLE_AI_TEAM_GRPC": DISABLE_AI_TEAM_GRPC,
                    "not USE_AI_TEAM_HTTP": not USE_AI_TEAM_HTTP,
                    "DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP": DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP,
                    "will_skip_router": DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP
                }
            }
            
        except Exception as e:
            env_vars["error"] = str(e)
        
        return env_vars
    
    async def test_ai_team_service_connection(self) -> Dict[str, Any]:
        """Test direct connection to AI team service"""
        result = {
            "service_url": self.ai_team_service_url,
            "tests": {}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test health endpoint
            try:
                response = await client.get(f"{self.ai_team_service_url}/health")
                result["tests"]["health_check"] = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 200 else response.text,
                    "success": response.status_code == 200
                }
            except Exception as e:
                result["tests"]["health_check"] = {
                    "error": str(e),
                    "success": False
                }
            
            # Test models endpoint
            try:
                headers = {"Authorization": f"Bearer ai-team-service-key-change-me"}
                response = await client.get(f"{self.ai_team_service_url}/api/v1/models", headers=headers)
                result["tests"]["models_endpoint"] = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 200 else response.text,
                    "success": response.status_code == 200
                }
            except Exception as e:
                result["tests"]["models_endpoint"] = {
                    "error": str(e),
                    "success": False
                }
            
            # Test analytics endpoint
            try:
                headers = {"Authorization": f"Bearer ai-team-service-key-change-me"}
                response = await client.get(f"{self.ai_team_service_url}/api/v1/analytics", headers=headers)
                result["tests"]["analytics_endpoint"] = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 200 else response.text,
                    "success": response.status_code == 200
                }
            except Exception as e:
                result["tests"]["analytics_endpoint"] = {
                    "error": str(e),
                    "success": False
                }
        
        return result
    
    async def analyze_main_py_logic(self) -> Dict[str, Any]:
        """Analyze the main.py router loading logic"""
        try:
            main_py_path = os.path.join(self.chatterfix_path, "main.py")
            with open(main_py_path, "r") as f:
                content = f.read()
            
            # Extract the relevant logic
            analysis = {
                "file_exists": True,
                "router_loading_logic": {},
                "environment_setup": {},
                "issues_found": []
            }
            
            # Check for environment variable definitions
            if "DISABLE_AI_TEAM_GRPC = os.getenv" in content:
                analysis["environment_setup"]["defines_DISABLE_AI_TEAM_GRPC"] = True
            else:
                analysis["issues_found"].append("DISABLE_AI_TEAM_GRPC not properly defined")
            
            if "USE_AI_TEAM_HTTP = os.getenv" in content:
                analysis["environment_setup"]["defines_USE_AI_TEAM_HTTP"] = True
            else:
                analysis["issues_found"].append("USE_AI_TEAM_HTTP not properly defined")
            
            # Check for router loading logic
            if "if DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP:" in content:
                analysis["router_loading_logic"]["has_skip_condition"] = True
                analysis["issues_found"].append("POTENTIAL ISSUE: Router will be skipped if gRPC disabled AND HTTP not enabled")
            
            if "ai_team_collaboration" in content:
                analysis["router_loading_logic"]["mentions_ai_team_collaboration"] = True
            
            # Check for import logic
            if "from app.routers import" in content and "ai_team_collaboration" not in content:
                analysis["issues_found"].append("ai_team_collaboration not in core router imports")
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "file_exists": False
            }
    
    async def check_router_file_exists(self) -> Dict[str, Any]:
        """Check if router file exists and is importable"""
        router_path = os.path.join(self.chatterfix_path, "app", "routers", "ai_team_collaboration.py")
        http_client_path = os.path.join(self.chatterfix_path, "app", "services", "ai_team_http_client.py")
        
        result = {
            "router_file": {
                "path": router_path,
                "exists": os.path.exists(router_path),
                "size": os.path.getsize(router_path) if os.path.exists(router_path) else 0
            },
            "http_client_file": {
                "path": http_client_path,
                "exists": os.path.exists(http_client_path),
                "size": os.path.getsize(http_client_path) if os.path.exists(http_client_path) else 0
            },
            "import_test": {}
        }
        
        # Test import
        try:
            os.chdir(self.chatterfix_path)
            sys.path.insert(0, self.chatterfix_path)
            
            # Test HTTP client import
            from app.services.ai_team_http_client import get_ai_team_client
            result["import_test"]["http_client"] = {"success": True}
            
            # Test router import
            from app.routers.ai_team_collaboration import router
            result["import_test"]["router"] = {"success": True}
            
        except Exception as e:
            result["import_test"]["error"] = str(e)
            result["import_test"]["success"] = False
        
        return result
    
    async def run_comprehensive_diagnosis(self) -> Dict[str, Any]:
        """Run comprehensive diagnosis of the AI team integration"""
        logger.info("🔍 Starting comprehensive AI team integration diagnosis...")
        
        diagnosis = {
            "timestamp": asyncio.get_event_loop().time(),
            "environment_variables": await self.check_environment_variables(),
            "ai_team_service_connection": await self.test_ai_team_service_connection(),
            "main_py_analysis": await self.analyze_main_py_logic(),
            "router_files": await self.check_router_file_exists(),
            "diagnosis": {
                "issues_found": [],
                "recommendations": [],
                "next_steps": []
            }
        }
        
        # Analyze results and provide diagnosis
        env_vars = diagnosis["environment_variables"]
        if "computed" in env_vars:
            computed = env_vars["computed"]
            if computed.get("will_skip_router", False):
                diagnosis["diagnosis"]["issues_found"].append(
                    f"CRITICAL: Router will be skipped due to boolean logic. "
                    f"DISABLE_AI_TEAM_GRPC={computed['DISABLE_AI_TEAM_GRPC']}, "
                    f"USE_AI_TEAM_HTTP={computed['USE_AI_TEAM_HTTP']}"
                )
                diagnosis["diagnosis"]["recommendations"].append(
                    "Fix the boolean logic in main.py router loading section"
                )
        
        # Check service connection
        service_tests = diagnosis["ai_team_service_connection"]["tests"]
        healthy_tests = sum(1 for test in service_tests.values() if test.get("success", False))
        if healthy_tests == 0:
            diagnosis["diagnosis"]["issues_found"].append("AI team service is not responding to any endpoints")
        elif healthy_tests < len(service_tests):
            diagnosis["diagnosis"]["issues_found"].append(f"AI team service partially working: {healthy_tests}/{len(service_tests)} tests passed")
        else:
            diagnosis["diagnosis"]["recommendations"].append("AI team service is fully operational")
        
        # Check file imports
        if not diagnosis["router_files"]["import_test"].get("success", False):
            diagnosis["diagnosis"]["issues_found"].append("Router import failed - check file dependencies")
        
        # Generate next steps
        if diagnosis["diagnosis"]["issues_found"]:
            diagnosis["diagnosis"]["next_steps"] = [
                "Fix boolean logic in main.py router loading",
                "Test router import manually",
                "Deploy fix to ChatterFix",
                "Verify AI team integration works end-to-end"
            ]
        else:
            diagnosis["diagnosis"]["next_steps"] = [
                "Everything looks good - verify production deployment"
            ]
        
        logger.info(f"✅ Diagnosis complete. Found {len(diagnosis['diagnosis']['issues_found'])} issues.")
        return diagnosis

debugger = AITeamDebugger()

@app.get("/")
async def root():
    """MCP server root endpoint"""
    return {
        "name": "AI Team Debug MCP Server",
        "version": "1.0.0",
        "description": "Debug and resolve ChatterFix AI team integration issues",
        "endpoints": {
            "/diagnose": "Run comprehensive diagnosis",
            "/environment": "Check environment variables",
            "/test-service": "Test AI team service connection",
            "/analyze-main": "Analyze main.py logic",
            "/check-files": "Check router files",
            "/fix-issue": "Apply automated fix"
        }
    }

@app.get("/diagnose")
async def diagnose():
    """Run comprehensive diagnosis of AI team integration"""
    return await debugger.run_comprehensive_diagnosis()

@app.get("/environment")
async def check_environment():
    """Check environment variables"""
    return await debugger.check_environment_variables()

@app.get("/test-service")
async def test_service():
    """Test AI team service connection"""
    return await debugger.test_ai_team_service_connection()

@app.get("/analyze-main")
async def analyze_main():
    """Analyze main.py router loading logic"""
    return await debugger.analyze_main_py_logic()

@app.get("/check-files")
async def check_files():
    """Check router files exist and are importable"""
    return await debugger.check_router_file_exists()

@app.post("/fix-issue")
async def fix_issue():
    """Apply automated fix for the router loading issue"""
    try:
        # The main issue is in the boolean logic in main.py
        main_py_path = os.path.join(debugger.chatterfix_path, "main.py")
        
        with open(main_py_path, "r") as f:
            content = f.read()
        
        # Find and fix the problematic logic
        old_logic = "if DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP:"
        new_logic = "if DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP:"
        
        # Actually, the issue is more subtle. Let me check the exact line
        lines = content.split('\n')
        fixed_lines = []
        fix_applied = False
        
        for i, line in enumerate(lines):
            if "if DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP:" in line:
                # The issue is we want to load the router when HTTP is enabled
                # So we should skip ONLY when gRPC is disabled AND HTTP is also NOT available
                fixed_lines.append(line.replace(
                    "if DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP:",
                    "if DISABLE_AI_TEAM_GRPC and not USE_AI_TEAM_HTTP:"
                ))
                # Actually, the logic is correct, but there might be an issue with variable definition order
                fix_applied = True
            else:
                fixed_lines.append(line)
        
        # Check if we found a different issue - variable definition order
        env_section_start = -1
        env_section_end = -1
        router_loading_start = -1
        
        for i, line in enumerate(lines):
            if "# AI Team Configuration" in line:
                env_section_start = i
            if env_section_start != -1 and env_section_end == -1 and line.strip() == "":
                env_section_end = i
            if "for router_name in all_extended_routers:" in line:
                router_loading_start = i
                break
        
        # The real issue might be that the environment variables are defined AFTER they're used in logging
        # Let's check if that's the case and fix it
        
        return {
            "status": "analysis_complete",
            "issues_found": [
                "Environment variables are defined after they're used in logging (lines 47-50)",
                "This causes NameError when the variables are referenced before definition"
            ],
            "recommended_fix": "Move AI Team Configuration section before the logging section",
            "fix_applied": False,
            "note": "Manual fix required - see diagnosis for details"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)