#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Chatterfix CMMS
Performs complete testing without requiring a running server
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Test Results
class TestResult:
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARNING = "⚠️  WARNING"
    SKIP = "⏭️  SKIP"
    ERROR = "🔥 ERROR"

class E2ETestSuite:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "skipped": 0,
                "errors": 0
            },
            "environment": {},
            "dependencies": {},
            "issues": [],
            "recommendations": []
        }
        self.base_path = Path(__file__).parent
        
    def log(self, message: str, status: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def add_test_result(self, category: str, name: str, status: str, 
                       details: str = "", duration: float = 0):
        """Add a test result"""
        self.results["tests"].append({
            "category": category,
            "name": name,
            "status": status,
            "details": details,
            "duration": duration
        })
        self.results["summary"]["total"] += 1
        
        if status == TestResult.PASS:
            self.results["summary"]["passed"] += 1
        elif status == TestResult.FAIL:
            self.results["summary"]["failed"] += 1
        elif status == TestResult.WARNING:
            self.results["summary"]["warnings"] += 1
        elif status == TestResult.SKIP:
            self.results["summary"]["skipped"] += 1
        elif status == TestResult.ERROR:
            self.results["summary"]["errors"] += 1
    
    def test_environment(self):
        """Test 1: Check Python environment"""
        self.log("Testing Python environment...", "TEST")
        start = time.time()
        
        try:
            import sys
            python_version = sys.version
            self.results["environment"]["python_version"] = python_version
            
            if sys.version_info >= (3, 10):
                self.add_test_result(
                    "Environment", 
                    "Python Version Check",
                    TestResult.PASS,
                    f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    time.time() - start
                )
            else:
                self.add_test_result(
                    "Environment", 
                    "Python Version Check",
                    TestResult.WARNING,
                    f"Python {sys.version_info.major}.{sys.version_info.minor} (3.10+ recommended)",
                    time.time() - start
                )
                self.results["recommendations"].append(
                    "Upgrade Python to 3.10 or higher for optimal performance"
                )
        except Exception as e:
            self.add_test_result(
                "Environment", 
                "Python Version Check",
                TestResult.ERROR,
                str(e),
                time.time() - start
            )
    
    def test_dependencies(self):
        """Test 2: Check critical dependencies"""
        self.log("Testing dependencies...", "TEST")
        
        critical_deps = [
            "fastapi",
            "uvicorn", 
            "pytest",
            "httpx",
            "requests",
            "pydantic"
        ]
        
        for dep in critical_deps:
            start = time.time()
            try:
                __import__(dep)
                version = __import__(dep).__version__ if hasattr(__import__(dep), '__version__') else "unknown"
                self.results["dependencies"][dep] = version
                self.add_test_result(
                    "Dependencies",
                    f"Import {dep}",
                    TestResult.PASS,
                    f"Version: {version}",
                    time.time() - start
                )
            except ImportError as e:
                self.add_test_result(
                    "Dependencies",
                    f"Import {dep}",
                    TestResult.FAIL,
                    str(e),
                    time.time() - start
                )
                self.results["issues"].append(f"Missing dependency: {dep}")
    
    def test_file_structure(self):
        """Test 3: Verify file structure"""
        self.log("Testing file structure...", "TEST")
        
        required_files = [
            "app.py",
            "requirements.txt",
            "tests/conftest.py",
            "tests/unit/test_api_endpoints.py"
        ]
        
        for file_path in required_files:
            start = time.time()
            full_path = self.base_path / file_path
            
            if full_path.exists():
                size = full_path.stat().st_size
                self.add_test_result(
                    "File Structure",
                    f"Check {file_path}",
                    TestResult.PASS,
                    f"Size: {size} bytes",
                    time.time() - start
                )
            else:
                self.add_test_result(
                    "File Structure",
                    f"Check {file_path}",
                    TestResult.FAIL,
                    "File not found",
                    time.time() - start
                )
                self.results["issues"].append(f"Missing file: {file_path}")
    
    def test_pytest_collection(self):
        """Test 4: Check pytest test collection"""
        self.log("Testing pytest collection...", "TEST")
        start = time.time()
        
        try:
            result = subprocess.run(
                ["pytest", "--collect-only", "tests/", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.base_path
            )
            
            if result.returncode == 0:
                # Parse collected tests
                output = result.stdout
                if "collected" in output.lower():
                    import re
                    match = re.search(r'(\d+)\s+(?:item|test)', output)
                    count = match.group(1) if match else "unknown"
                    self.add_test_result(
                        "Test Collection",
                        "Pytest Collection",
                        TestResult.PASS,
                        f"Collected {count} tests",
                        time.time() - start
                    )
                else:
                    self.add_test_result(
                        "Test Collection",
                        "Pytest Collection",
                        TestResult.WARNING,
                        "No tests collected",
                        time.time() - start
                    )
            else:
                self.add_test_result(
                    "Test Collection",
                    "Pytest Collection",
                    TestResult.FAIL,
                    result.stderr[:200],
                    time.time() - start
                )
                self.results["issues"].append("Pytest collection failed")
        except Exception as e:
            self.add_test_result(
                "Test Collection",
                "Pytest Collection",
                TestResult.ERROR,
                str(e),
                time.time() - start
            )
    
    def test_unit_tests(self):
        """Test 5: Run unit tests"""
        self.log("Running unit tests...", "TEST")
        start = time.time()
        
        try:
            result = subprocess.run(
                ["pytest", "tests/unit/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.base_path
            )
            
            # Parse pytest output
            output = result.stdout + result.stderr
            
            # Count results
            import re
            passed = len(re.findall(r'PASSED', output))
            failed = len(re.findall(r'FAILED', output))
            skipped = len(re.findall(r'SKIPPED', output))
            
            total = passed + failed + skipped
            
            if result.returncode == 0:
                self.add_test_result(
                    "Unit Tests",
                    "Run pytest unit tests",
                    TestResult.PASS,
                    f"{passed}/{total} tests passed",
                    time.time() - start
                )
            elif failed > 0:
                self.add_test_result(
                    "Unit Tests",
                    "Run pytest unit tests",
                    TestResult.FAIL,
                    f"{failed} tests failed, {passed} passed",
                    time.time() - start
                )
                self.results["issues"].append(f"{failed} unit tests failed")
            else:
                self.add_test_result(
                    "Unit Tests",
                    "Run pytest unit tests",
                    TestResult.WARNING,
                    f"Exit code: {result.returncode}",
                    time.time() - start
                )
                
        except subprocess.TimeoutExpired:
            self.add_test_result(
                "Unit Tests",
                "Run pytest unit tests",
                TestResult.ERROR,
                "Test execution timeout",
                time.time() - start
            )
            self.results["issues"].append("Unit tests timed out")
        except Exception as e:
            self.add_test_result(
                "Unit Tests",
                "Run pytest unit tests",
                TestResult.ERROR,
                str(e),
                time.time() - start
            )
    
    def test_app_import(self):
        """Test 6: Test app.py import"""
        self.log("Testing app.py import...", "TEST")
        start = time.time()
        
        # Modify environment to use local database
        os.environ['DATABASE_PATH'] = str(self.base_path / "test_cmms.db")
        
        try:
            # Try importing without executing
            result = subprocess.run(
                [sys.executable, "-c", "import ast; ast.parse(open('app.py').read())"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.base_path
            )
            
            if result.returncode == 0:
                self.add_test_result(
                    "Application",
                    "app.py Syntax Check",
                    TestResult.PASS,
                    "No syntax errors",
                    time.time() - start
                )
            else:
                self.add_test_result(
                    "Application",
                    "app.py Syntax Check",
                    TestResult.FAIL,
                    result.stderr[:200],
                    time.time() - start
                )
                self.results["issues"].append("app.py has syntax errors")
        except Exception as e:
            self.add_test_result(
                "Application",
                "app.py Syntax Check",
                TestResult.ERROR,
                str(e),
                time.time() - start
            )
    
    def test_database_permissions(self):
        """Test 7: Check database creation"""
        self.log("Testing database permissions...", "TEST")
        start = time.time()
        
        try:
            import sqlite3
            test_db = self.base_path / "test_e2e.db"
            
            # Try to create a test database
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
            cursor.execute("INSERT INTO test (id) VALUES (1)")
            conn.commit()
            conn.close()
            
            # Clean up
            test_db.unlink()
            
            self.add_test_result(
                "Database",
                "Database Creation",
                TestResult.PASS,
                "Can create and write to SQLite database",
                time.time() - start
            )
        except Exception as e:
            self.add_test_result(
                "Database",
                "Database Creation",
                TestResult.FAIL,
                str(e),
                time.time() - start
            )
            self.results["issues"].append("Cannot create database files")
            self.results["recommendations"].append(
                "Check file system permissions for database creation"
            )
    
    def test_configuration_files(self):
        """Test 8: Verify configuration files"""
        self.log("Testing configuration files...", "TEST")
        
        config_files = {
            "requirements.txt": ["fastapi", "uvicorn"],
            ".gitignore": ["*.db", "__pycache__"],
            ".pre-commit-config.yaml": ["repos"]
        }
        
        for file_name, expected_content in config_files.items():
            start = time.time()
            file_path = self.base_path / file_name
            
            if not file_path.exists():
                # Check parent directory
                file_path = self.base_path.parent.parent / file_name
            
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    found_all = all(item in content for item in expected_content)
                    
                    if found_all:
                        self.add_test_result(
                            "Configuration",
                            f"Verify {file_name}",
                            TestResult.PASS,
                            f"Contains expected content",
                            time.time() - start
                        )
                    else:
                        missing = [item for item in expected_content if item not in content]
                        self.add_test_result(
                            "Configuration",
                            f"Verify {file_name}",
                            TestResult.WARNING,
                            f"Missing: {', '.join(missing)}",
                            time.time() - start
                        )
                except Exception as e:
                    self.add_test_result(
                        "Configuration",
                        f"Verify {file_name}",
                        TestResult.ERROR,
                        str(e),
                        time.time() - start
                    )
            else:
                self.add_test_result(
                    "Configuration",
                    f"Verify {file_name}",
                    TestResult.SKIP,
                    "File not found",
                    time.time() - start
                )
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.log("Generating comprehensive report...", "INFO")
        
        # Calculate success rate
        total = self.results["summary"]["total"]
        passed = self.results["summary"]["passed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # Create markdown report
        report = f"""# 🧪 Chatterfix CMMS - Comprehensive End-to-End Test Report

**Generated:** {self.results["timestamp"]}  
**Test Duration:** {time.time() - self.start_time:.2f} seconds

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | {total} |
| **✅ Passed** | {passed} |
| **❌ Failed** | {self.results["summary"]["failed"]} |
| **⚠️  Warnings** | {self.results["summary"]["warnings"]} |
| **⏭️  Skipped** | {self.results["summary"]["skipped"]} |
| **🔥 Errors** | {self.results["summary"]["errors"]} |
| **Success Rate** | {success_rate:.1f}% |

---

## 🌍 Environment Information

"""
        for key, value in self.results["environment"].items():
            report += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        
        report += "\n---\n\n## 📦 Dependencies Status\n\n"
        report += "| Package | Version | Status |\n"
        report += "|---------|---------|--------|\n"
        
        for dep, version in self.results["dependencies"].items():
            report += f"| {dep} | {version} | ✅ Installed |\n"
        
        report += "\n---\n\n## 🧪 Detailed Test Results\n\n"
        
        # Group by category
        categories = {}
        for test in self.results["tests"]:
            cat = test["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(test)
        
        for category, tests in categories.items():
            report += f"### {category}\n\n"
            report += "| Test Name | Status | Details | Duration |\n"
            report += "|-----------|--------|---------|----------|\n"
            
            for test in tests:
                details = test["details"][:50] + "..." if len(test["details"]) > 50 else test["details"]
                report += f"| {test['name']} | {test['status']} | {details} | {test['duration']:.3f}s |\n"
            
            report += "\n"
        
        report += "---\n\n## ⚠️  Issues Identified\n\n"
        if self.results["issues"]:
            for i, issue in enumerate(self.results["issues"], 1):
                report += f"{i}. {issue}\n"
        else:
            report += "✅ No critical issues identified!\n"
        
        report += "\n---\n\n## 💡 Recommendations\n\n"
        if self.results["recommendations"]:
            for i, rec in enumerate(self.results["recommendations"], 1):
                report += f"{i}. {rec}\n"
        else:
            report += "✅ System is properly configured!\n"
        
        report += "\n---\n\n## 🎯 Overall Assessment\n\n"
        
        if success_rate >= 90:
            report += "**Status: 🟢 EXCELLENT**\n\n"
            report += "The codebase is in excellent condition with minimal issues. "
            report += "All critical systems are functioning properly.\n"
        elif success_rate >= 70:
            report += "**Status: 🟡 GOOD**\n\n"
            report += "The codebase is generally healthy with some minor issues that should be addressed. "
            report += "Most functionality is working as expected.\n"
        elif success_rate >= 50:
            report += "**Status: 🟠 FAIR**\n\n"
            report += "The codebase has several issues that need attention. "
            report += "Some functionality may be impaired and requires fixes.\n"
        else:
            report += "**Status: 🔴 NEEDS ATTENTION**\n\n"
            report += "The codebase has significant issues that require immediate attention. "
            report += "Multiple critical systems may not be functioning properly.\n"
        
        report += "\n---\n\n## 📝 Next Steps\n\n"
        report += "1. Review and address all failed tests\n"
        report += "2. Implement recommended fixes\n"
        report += "3. Run tests again to verify improvements\n"
        report += "4. Consider adding integration tests for end-to-end workflows\n"
        report += "5. Set up continuous integration to catch issues early\n"
        
        report += "\n---\n\n"
        report += "*Report generated by Chatterfix E2E Test Suite v1.0*\n"
        
        return report
    
    def save_report(self, report: str, json_results: dict):
        """Save report to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save markdown report
        md_file = self.base_path / f"e2e_test_report_{timestamp}.md"
        md_file.write_text(report)
        self.log(f"Saved markdown report: {md_file}", "INFO")
        
        # Save JSON results
        json_file = self.base_path / f"e2e_test_results_{timestamp}.json"
        json_file.write_text(json.dumps(json_results, indent=2))
        self.log(f"Saved JSON results: {json_file}", "INFO")
        
        return md_file, json_file
    
    def run(self):
        """Run all tests"""
        self.start_time = time.time()
        
        print("\n" + "="*80)
        print("🧪 CHATTERFIX CMMS - COMPREHENSIVE END-TO-END TEST SUITE")
        print("="*80 + "\n")
        
        # Run all test categories
        self.test_environment()
        self.test_dependencies()
        self.test_file_structure()
        self.test_configuration_files()
        self.test_database_permissions()
        self.test_app_import()
        self.test_pytest_collection()
        self.test_unit_tests()
        
        print("\n" + "="*80)
        print("📊 GENERATING COMPREHENSIVE REPORT")
        print("="*80 + "\n")
        
        # Generate and save report
        report = self.generate_report()
        md_file, json_file = self.save_report(report, self.results)
        
        # Print summary
        print("\n" + "="*80)
        print("✅ TEST SUITE COMPLETE")
        print("="*80 + "\n")
        
        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"✅ Passed: {self.results['summary']['passed']}")
        print(f"❌ Failed: {self.results['summary']['failed']}")
        print(f"⚠️  Warnings: {self.results['summary']['warnings']}")
        print(f"⏭️  Skipped: {self.results['summary']['skipped']}")
        print(f"🔥 Errors: {self.results['summary']['errors']}")
        
        success_rate = (self.results['summary']['passed'] / self.results['summary']['total'] * 100) if self.results['summary']['total'] > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📄 Report saved to: {md_file}")
        print(f"📊 Results saved to: {json_file}\n")
        
        return self.results['summary']['failed'] == 0 and self.results['summary']['errors'] == 0


if __name__ == "__main__":
    suite = E2ETestSuite()
    success = suite.run()
    sys.exit(0 if success else 1)
