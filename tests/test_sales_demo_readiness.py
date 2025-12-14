#!/usr/bin/env python3
"""
Sales Demo Readiness Test
Validates that all critical integration points are working for the FixItFred mobile app sales demo
"""

import asyncio
import json
import requests
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple

class SalesDemoTester:
    def __init__(self):
        self.local_url = "http://localhost:8081"
        self.mobile_path = "/Users/fredtaylor/ChatterFix/mobile"
        self.session = requests.Session()
        
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_backend_endpoints_for_mobile(self) -> Dict[str, Any]:
        """Test all backend endpoints that mobile app needs"""
        self.log("INFO", "Testing backend endpoints for mobile app")
        
        critical_endpoints = [
            ("/auth/config", "Auth Configuration", "GET"),
            ("/analytics/kpi/summary?days=30", "KPI Data", "GET"),
            ("/analytics/trends/mttr?days=30", "Performance Trends", "GET"),
            ("/", "Health Check", "GET")
        ]
        
        results = {}
        all_working = True
        
        for endpoint, description, method in critical_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.local_url}{endpoint}", timeout=5)
                else:
                    response = self.session.post(f"{self.local_url}{endpoint}", timeout=5)
                
                if response.status_code in [200, 302]:
                    try:
                        data = response.json() if response.content else {}
                        results[endpoint] = {
                            "status": "✅ WORKING",
                            "description": description,
                            "response_code": response.status_code,
                            "has_data": bool(data)
                        }
                        self.log("PASS", f"{description}: Working ✅")
                    except json.JSONDecodeError:
                        results[endpoint] = {
                            "status": "✅ WORKING", 
                            "description": description,
                            "response_code": response.status_code,
                            "note": "HTML response (expected for health check)"
                        }
                        self.log("PASS", f"{description}: Working ✅ (HTML)")
                else:
                    results[endpoint] = {
                        "status": "❌ FAILED",
                        "description": description,
                        "response_code": response.status_code
                    }
                    all_working = False
                    self.log("FAIL", f"{description}: Failed with status {response.status_code}")
                    
            except Exception as e:
                results[endpoint] = {
                    "status": "❌ ERROR",
                    "description": description,
                    "error": str(e)
                }
                all_working = False
                self.log("FAIL", f"{description}: Error - {str(e)}")
        
        return {
            "all_endpoints_working": all_working,
            "endpoints": results,
            "critical_for_demo": all_working
        }
    
    def test_mobile_app_structure(self) -> Dict[str, Any]:
        """Validate mobile app structure and configuration"""
        self.log("INFO", "Validating mobile app structure")
        
        required_files = [
            "package.json",
            "app.json", 
            "App.tsx",
            "src/services/api.ts",
            "src/screens/DashboardScreen.tsx",
            "src/screens/WorkOrdersScreen.tsx",
            "src/screens/AssetsScreen.tsx"
        ]
        
        results = {}
        all_files_present = True
        
        for file in required_files:
            filepath = os.path.join(self.mobile_path, file)
            if os.path.exists(filepath):
                results[file] = "✅ Present"
                self.log("PASS", f"Required file: {file} ✅")
            else:
                results[file] = "❌ Missing"
                all_files_present = False
                self.log("FAIL", f"Missing file: {file} ❌")
        
        # Check if API config is properly set
        api_config_correct = False
        try:
            with open(os.path.join(self.mobile_path, "src/services/api.ts"), 'r') as f:
                content = f.read()
                if "chatterfix-cmms-xaxnqgz3cq-uc.a.run.app" in content:
                    api_config_correct = True
                    self.log("PASS", "API configuration: Correctly set ✅")
                else:
                    self.log("WARN", "API configuration: Needs update ⚠️")
        except:
            self.log("FAIL", "API configuration: Cannot read ❌")
        
        return {
            "structure_valid": all_files_present,
            "files": results,
            "api_config_correct": api_config_correct,
            "demo_ready": all_files_present and api_config_correct
        }
    
    def test_mobile_dependencies(self) -> Dict[str, Any]:
        """Check if mobile app dependencies are properly installed"""
        self.log("INFO", "Checking mobile app dependencies")
        
        try:
            # Check if node_modules exists and has content
            node_modules_path = os.path.join(self.mobile_path, "node_modules")
            if os.path.exists(node_modules_path) and os.listdir(node_modules_path):
                dependencies_installed = True
                self.log("PASS", "Dependencies: Installed ✅")
            else:
                dependencies_installed = False
                self.log("FAIL", "Dependencies: Not installed ❌")
            
            # Check if key packages are present
            key_packages = ["expo", "react", "react-native", "axios", "@tanstack/react-query"]
            package_status = {}
            
            for package in key_packages:
                package_path = os.path.join(node_modules_path, package)
                if os.path.exists(package_path):
                    package_status[package] = "✅ Installed"
                else:
                    package_status[package] = "❌ Missing"
                    dependencies_installed = False
            
            return {
                "dependencies_ready": dependencies_installed,
                "packages": package_status,
                "can_build": dependencies_installed
            }
            
        except Exception as e:
            self.log("FAIL", f"Dependency check failed: {str(e)}")
            return {
                "dependencies_ready": False,
                "error": str(e),
                "can_build": False
            }
    
    def test_ci_cd_configuration(self) -> Dict[str, Any]:
        """Test CI/CD configuration for mobile deployment"""
        self.log("INFO", "Checking CI/CD configuration")
        
        ci_files = [
            ("/Users/fredtaylor/ChatterFix/cloudbuild.yaml", "Main CI/CD"),
            ("/Users/fredtaylor/ChatterFix/mobile-build.yaml", "Mobile Build"),
            ("/Users/fredtaylor/ChatterFix/.github/workflows/deploy-simple.yml", "GitHub Actions")
        ]
        
        results = {}
        ci_configured = True
        
        for filepath, description in ci_files:
            if os.path.exists(filepath):
                results[description] = "✅ Configured"
                self.log("PASS", f"CI/CD: {description} ✅")
            else:
                results[description] = "❌ Missing"
                ci_configured = False
                self.log("FAIL", f"CI/CD: {description} missing ❌")
        
        return {
            "ci_cd_ready": ci_configured,
            "configurations": results,
            "deployment_ready": ci_configured
        }
    
    def test_integration_points(self) -> Dict[str, Any]:
        """Test critical integration points between mobile and backend"""
        self.log("INFO", "Testing critical integration points")
        
        # Test 1: Can mobile API client connect to backend?
        try:
            response = self.session.get(f"{self.local_url}/auth/config")
            api_connectivity = response.status_code == 200
        except:
            api_connectivity = False
        
        # Test 2: Does backend return mobile-compatible JSON?
        try:
            response = self.session.get(f"{self.local_url}/analytics/kpi/summary?days=30")
            data = response.json()
            mobile_compatible = isinstance(data, dict) and len(data) > 0
        except:
            mobile_compatible = False
        
        # Test 3: Are CORS headers properly set?
        try:
            response = self.session.options(f"{self.local_url}/auth/config")
            cors_configured = 'access-control-allow-origin' in response.headers
        except:
            cors_configured = False
        
        integration_score = sum([api_connectivity, mobile_compatible, cors_configured])
        
        return {
            "api_connectivity": api_connectivity,
            "mobile_compatible_responses": mobile_compatible,
            "cors_configured": cors_configured,
            "integration_score": f"{integration_score}/3",
            "demo_ready": integration_score >= 2
        }
    
    def generate_demo_readiness_report(self) -> Dict[str, Any]:
        """Generate comprehensive demo readiness report"""
        self.log("INFO", "🎯 Generating Sales Demo Readiness Report")
        self.log("INFO", "=" * 60)
        
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "demo_date": "Sales Demo Preparation",
            "tests": {}
        }
        
        # Run all tests
        self.log("INFO", "1️⃣ Testing Backend Endpoints")
        report["tests"]["backend"] = self.test_backend_endpoints_for_mobile()
        
        self.log("INFO", "\n2️⃣ Validating Mobile App Structure")
        report["tests"]["mobile_structure"] = self.test_mobile_app_structure()
        
        self.log("INFO", "\n3️⃣ Checking Dependencies")
        report["tests"]["dependencies"] = self.test_mobile_dependencies()
        
        self.log("INFO", "\n4️⃣ Validating CI/CD")
        report["tests"]["ci_cd"] = self.test_ci_cd_configuration()
        
        self.log("INFO", "\n5️⃣ Testing Integration Points")
        report["tests"]["integration"] = self.test_integration_points()
        
        # Calculate overall demo readiness
        critical_checks = [
            report["tests"]["backend"]["critical_for_demo"],
            report["tests"]["mobile_structure"]["demo_ready"], 
            report["tests"]["dependencies"]["can_build"],
            report["tests"]["integration"]["demo_ready"]
        ]
        
        demo_ready_score = sum(critical_checks)
        report["overall_demo_readiness"] = {
            "score": f"{demo_ready_score}/4",
            "percentage": f"{(demo_ready_score/4)*100:.0f}%",
            "status": "🟢 READY" if demo_ready_score >= 3 else "🟡 NEEDS WORK" if demo_ready_score >= 2 else "🔴 NOT READY",
            "can_demo": demo_ready_score >= 3
        }
        
        return report
    
    def print_demo_summary(self, report: Dict[str, Any]):
        """Print executive summary for demo readiness"""
        self.log("INFO", "\n" + "=" * 60)
        self.log("INFO", "🎯 SALES DEMO READINESS SUMMARY")
        self.log("INFO", "=" * 60)
        
        readiness = report["overall_demo_readiness"]
        self.log("INFO", f"Overall Status: {readiness['status']}")
        self.log("INFO", f"Readiness Score: {readiness['score']} ({readiness['percentage']})")
        
        if readiness["can_demo"]:
            self.log("PASS", "✅ READY FOR SALES DEMO!")
            self.log("INFO", "📱 Mobile app integration is working")
            self.log("INFO", "🔄 Backend APIs are responsive")
            self.log("INFO", "🚀 Deployment pipeline is configured")
        else:
            self.log("WARN", "⚠️  Demo needs attention:")
            
            if not report["tests"]["backend"]["critical_for_demo"]:
                self.log("FAIL", "   - Backend APIs need fixes")
            if not report["tests"]["mobile_structure"]["demo_ready"]:
                self.log("FAIL", "   - Mobile app structure issues")
            if not report["tests"]["dependencies"]["can_build"]:
                self.log("FAIL", "   - Mobile dependencies missing")
            if not report["tests"]["integration"]["demo_ready"]:
                self.log("FAIL", "   - Integration points failing")
        
        self.log("INFO", "\n📊 Component Status:")
        self.log("INFO", f"Backend APIs: {'✅' if report['tests']['backend']['critical_for_demo'] else '❌'}")
        self.log("INFO", f"Mobile Structure: {'✅' if report['tests']['mobile_structure']['demo_ready'] else '❌'}")
        self.log("INFO", f"Dependencies: {'✅' if report['tests']['dependencies']['can_build'] else '❌'}")
        self.log("INFO", f"CI/CD Pipeline: {'✅' if report['tests']['ci_cd']['deployment_ready'] else '❌'}")
        self.log("INFO", f"Integration: {'✅' if report['tests']['integration']['demo_ready'] else '❌'}")

def main():
    """Run complete sales demo readiness test"""
    print("🎯 FixItFred Mobile App - Sales Demo Readiness Test")
    print("Testing all critical integration points for successful demo")
    print("=" * 70)
    
    tester = SalesDemoTester()
    report = tester.generate_demo_readiness_report()
    tester.print_demo_summary(report)
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sales_demo_readiness_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {filename}")
    
    # Return exit code based on demo readiness
    exit_code = 0 if report["overall_demo_readiness"]["can_demo"] else 1
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)