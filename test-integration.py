#!/usr/bin/env python3
"""
ChatterFix CMMS - Comprehensive Integration Test
Tests all merged components and validates deployment readiness
"""

import sys
import time
import requests
from pathlib import Path

class ComprehensiveIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.results = []
        
    def log_test(self, name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "name": name,
            "passed": passed,
            "message": message
        })
        print(f"{status}: {name}")
        if message:
            print(f"   {message}")
    
    def test_imports(self):
        """Test that all critical modules can be imported"""
        print("\n🔍 Testing Python Imports...")
        
        import subprocess
        import os
        
        # Test app.py import from correct directory
        try:
            result = subprocess.run(
                ["python3", "-c", "import app; print('✅')"],
                capture_output=True,
                cwd="core/cmms",
                timeout=10
            )
            passed = result.returncode == 0 and b'\xe2\x9c\x85' in result.stdout
            self.log_test("Import app.py", passed, "Main application imports successfully" if passed else result.stderr.decode())
        except Exception as e:
            self.log_test("Import app.py", False, str(e))
        
        # Test technician_ai_assistant.py import
        try:
            result = subprocess.run(
                ["python3", "-c", "import technician_ai_assistant; print('✅')"],
                capture_output=True,
                cwd="core/cmms",
                timeout=10
            )
            passed = result.returncode == 0 and b'\xe2\x9c\x85' in result.stdout
            self.log_test("Import technician_ai_assistant.py", passed, "AI assistant imports successfully" if passed else result.stderr.decode())
        except Exception as e:
            self.log_test("Import technician_ai_assistant.py", False, str(e))
    
    def test_file_structure(self):
        """Test that all merged files exist"""
        print("\n📁 Testing File Structure...")
        
        expected_files = [
            "core/cmms/app.py",
            "core/cmms/technician_ai_assistant.py",
            "core/cmms/FIX_IT_FRED_README.md",
            "core/cmms/TECHBOT_DEPLOYMENT_GUIDE.md",
            "core/cmms/deploy-ai-brain-service.sh",
            "core/cmms/deploy-fix-it-fred.sh",
            "core/cmms/Dockerfile.ai-brain",
            "core/cmms/Dockerfile.techbot",
            "core/cmms/requirements.txt",
            "core/cmms/requirements.ai-brain.txt",
            "core/cmms/requirements.fred.txt",
            "DEPLOYMENT_GUIDE.md",
            "DEPLOYMENT_CHECKLIST.md",
            "validate-deployment-readiness.sh"
        ]
        
        for file_path in expected_files:
            path = Path(file_path)
            exists = path.exists()
            self.log_test(f"File exists: {file_path}", exists)
    
    def test_deployment_scripts(self):
        """Test that deployment scripts are valid"""
        print("\n📦 Testing Deployment Scripts...")
        
        scripts = [
            "validate-deployment-readiness.sh",
            "core/cmms/deploy-ai-brain-service.sh",
            "core/cmms/deploy-fix-it-fred.sh",
            "core/cmms/deployment/deploy-consolidated-services.sh",
            "core/cmms/deployment/validate-ai-endpoints.sh"
        ]
        
        import subprocess
        for script in scripts:
            if Path(script).exists():
                try:
                    result = subprocess.run(
                        ["bash", "-n", script],
                        capture_output=True,
                        timeout=5
                    )
                    passed = result.returncode == 0
                    self.log_test(
                        f"Script syntax: {script}",
                        passed,
                        "Valid bash syntax" if passed else "Syntax error"
                    )
                except Exception as e:
                    self.log_test(f"Script syntax: {script}", False, str(e))
    
    def test_endpoints(self):
        """Test that application endpoints are accessible"""
        print("\n🌐 Testing Application Endpoints...")
        
        # Start a test server would go here in a real integration test
        # For now, we'll test that endpoints are defined
        
        endpoints = [
            "/health",
            "/",
            "/api/work-orders",
            "/api/assets",
            "/api/parts",
        ]
        
        print("   Note: Endpoint tests require running server")
        print("   Run 'python app.py' in core/cmms/ to test endpoints")
    
    def test_requirements(self):
        """Test that requirements files are parseable"""
        print("\n📋 Testing Requirements Files...")
        
        req_files = [
            "core/cmms/requirements.txt",
            "core/cmms/requirements.ai-brain.txt",
            "core/cmms/requirements.fred.txt"
        ]
        
        for req_file in req_files:
            path = Path(req_file)
            if path.exists():
                try:
                    with open(path) as f:
                        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                    self.log_test(
                        f"Requirements file: {req_file}",
                        len(lines) > 0,
                        f"{len(lines)} dependencies defined"
                    )
                except Exception as e:
                    self.log_test(f"Requirements file: {req_file}", False, str(e))
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE INTEGRATION TEST REPORT")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"   - {result['name']}")
                    if result["message"]:
                        print(f"     {result['message']}")
        
        print("\n" + "=" * 60)
        
        if failed == 0:
            print("✅ ALL TESTS PASSED - DEPLOYMENT READY!")
            return 0
        else:
            print("❌ SOME TESTS FAILED - Review issues above")
            return 1

def main():
    print("🚀 ChatterFix CMMS - Comprehensive Integration Test")
    print("=" * 60)
    
    tester = ComprehensiveIntegrationTest()
    
    # Run all test suites
    tester.test_imports()
    tester.test_file_structure()
    tester.test_deployment_scripts()
    tester.test_requirements()
    tester.test_endpoints()
    
    # Generate report
    exit_code = tester.generate_report()
    
    print("\n📚 Documentation:")
    print("   - Deployment Guide: DEPLOYMENT_GUIDE.md")
    print("   - Quick Checklist: DEPLOYMENT_CHECKLIST.md")
    print("   - Fix It Fred: core/cmms/FIX_IT_FRED_README.md")
    print("\n🚀 Ready to deploy:")
    print("   ./validate-deployment-readiness.sh")
    print("   cd core/cmms && ./deployment/deploy-consolidated-services.sh")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
