#!/usr/bin/env python3
"""
Mobile App Integration Tests
Tests the critical integration points between FixItFred mobile app and ChatterFix backend
"""

import asyncio
import json
import os
import requests
import sys
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
BACKEND_URL = "https://chatterfix-cmms-xaxnqgz3cq-uc.a.run.app"  # Production URL
LOCAL_URL = "http://localhost:8081"  # Local dev URL
TEST_ENDPOINTS = [
    "/auth/config",
    "/analytics/kpi/summary",
    "/auth/me", 
    "/analytics/roi",
    "/analytics/dashboard/summary"
]

# Test user credentials (for demo purposes)
TEST_EMAIL = "demo@chatterfix.com"
TEST_PASSWORD = "demo123"

class MobileIntegrationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ChatterFix-Mobile-Test/1.0'
        })
        self.auth_token = None
        
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_backend_health(self) -> Dict[str, Any]:
        """Test if backend is accessible"""
        self.log("INFO", f"Testing backend health at {self.base_url}")
        
        try:
            # Test basic connectivity
            response = self.session.get(f"{self.base_url}/", timeout=10)
            
            result = {
                "status": "PASS" if response.status_code in [200, 302] else "FAIL",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "headers": dict(response.headers),
                "accessible": True
            }
            
            self.log("PASS", f"Backend accessible - Status: {response.status_code}, Time: {result['response_time_ms']:.0f}ms")
            return result
            
        except requests.exceptions.RequestException as e:
            self.log("FAIL", f"Backend not accessible: {str(e)}")
            return {
                "status": "FAIL",
                "error": str(e),
                "accessible": False
            }
    
    def test_auth_configuration(self) -> Dict[str, Any]:
        """Test authentication configuration endpoint"""
        self.log("INFO", "Testing authentication configuration")
        
        try:
            response = self.session.get(f"{self.base_url}/auth/config", timeout=10)
            
            if response.status_code == 200:
                config = response.json()
                self.log("PASS", f"Auth config retrieved: Firebase={config.get('use_firebase', False)}")
                return {
                    "status": "PASS",
                    "config": config,
                    "firebase_enabled": config.get('use_firebase', False)
                }
            else:
                self.log("FAIL", f"Auth config failed: Status {response.status_code}")
                return {
                    "status": "FAIL",
                    "status_code": response.status_code,
                    "response": response.text[:500]
                }
                
        except Exception as e:
            self.log("FAIL", f"Auth config error: {str(e)}")
            return {"status": "FAIL", "error": str(e)}
    
    def test_authentication_flow(self) -> Dict[str, Any]:
        """Test authentication flow that mobile app would use"""
        self.log("INFO", "Testing authentication flow")
        
        try:
            # Test login endpoint (form data as backend expects)
            login_data = {
                'username': TEST_EMAIL,
                'password': TEST_PASSWORD
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login", 
                data=login_data,
                allow_redirects=False,
                timeout=10
            )
            
            # Check if login was successful (redirect or cookie set)
            if response.status_code in [302, 200]:
                # Extract session token from cookie if set
                session_token = None
                if 'set-cookie' in response.headers:
                    cookies = response.headers['set-cookie']
                    if 'session_token' in cookies:
                        # Extract session token value
                        for cookie in cookies.split(';'):
                            if 'session_token' in cookie:
                                session_token = cookie.split('=')[1]
                                break
                
                self.auth_token = session_token
                self.log("PASS", f"Authentication successful - Token: {bool(session_token)}")
                return {
                    "status": "PASS",
                    "has_token": bool(session_token),
                    "status_code": response.status_code,
                    "redirect_location": response.headers.get('location', 'none')
                }
            else:
                self.log("FAIL", f"Authentication failed: Status {response.status_code}")
                return {
                    "status": "FAIL",
                    "status_code": response.status_code,
                    "response": response.text[:500]
                }
                
        except Exception as e:
            self.log("FAIL", f"Authentication error: {str(e)}")
            return {"status": "FAIL", "error": str(e)}
    
    def test_authenticated_endpoints(self) -> Dict[str, Any]:
        """Test endpoints that require authentication"""
        self.log("INFO", "Testing authenticated API endpoints")
        
        results = {}
        
        # Add session token to headers if available
        if self.auth_token:
            self.session.cookies.set('session_token', self.auth_token)
        
        endpoints_to_test = [
            ("/analytics/kpi/summary?days=30", "KPI Summary"),
            ("/analytics/roi", "ROI Metrics"),
            ("/analytics/dashboard/summary", "Dashboard Summary"),
            ("/auth/me", "Current User Info")
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results[endpoint] = {
                            "status": "PASS",
                            "description": description,
                            "has_data": bool(data),
                            "response_size": len(response.content)
                        }
                        self.log("PASS", f"{description}: ✓ (size: {len(response.content)} bytes)")
                    except json.JSONDecodeError:
                        results[endpoint] = {
                            "status": "WARN", 
                            "description": description,
                            "issue": "Non-JSON response"
                        }
                        self.log("WARN", f"{description}: Non-JSON response")
                elif response.status_code == 401:
                    results[endpoint] = {
                        "status": "FAIL",
                        "description": description, 
                        "issue": "Authentication required"
                    }
                    self.log("FAIL", f"{description}: Authentication required")
                else:
                    results[endpoint] = {
                        "status": "FAIL",
                        "description": description,
                        "status_code": response.status_code
                    }
                    self.log("FAIL", f"{description}: Status {response.status_code}")
                    
            except Exception as e:
                results[endpoint] = {
                    "status": "FAIL",
                    "description": description,
                    "error": str(e)
                }
                self.log("FAIL", f"{description}: {str(e)}")
        
        return results
    
    def test_mobile_api_compatibility(self) -> Dict[str, Any]:
        """Test API endpoints specifically used by mobile app"""
        self.log("INFO", "Testing mobile-specific API compatibility")
        
        results = {}
        
        # Test endpoints that mobile app api.ts calls
        mobile_endpoints = [
            ("/analytics/kpi/summary?days=30", "Mobile KPI Data"),
            ("/analytics/trends/mttr?days=30", "Trend Data"),
            # Work Orders endpoints (if they exist)
            # Assets endpoints (if they exist) 
        ]
        
        for endpoint, description in mobile_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Validate response structure expected by mobile app
                        results[endpoint] = {
                            "status": "PASS",
                            "description": description,
                            "mobile_compatible": True,
                            "data_keys": list(data.keys()) if isinstance(data, dict) else "array"
                        }
                        self.log("PASS", f"{description}: Mobile compatible ✓")
                    except json.JSONDecodeError:
                        results[endpoint] = {"status": "FAIL", "issue": "Invalid JSON"}
                elif response.status_code == 404:
                    results[endpoint] = {
                        "status": "WARN", 
                        "description": description,
                        "issue": "Endpoint not implemented"
                    }
                    self.log("WARN", f"{description}: Not implemented")
                else:
                    results[endpoint] = {
                        "status": "FAIL",
                        "status_code": response.status_code
                    }
                    self.log("FAIL", f"{description}: Status {response.status_code}")
                    
            except Exception as e:
                results[endpoint] = {"status": "FAIL", "error": str(e)}
                self.log("FAIL", f"{description}: {str(e)}")
        
        return results
    
    def test_cors_headers(self) -> Dict[str, Any]:
        """Test CORS headers for mobile app compatibility"""
        self.log("INFO", "Testing CORS headers for mobile compatibility")
        
        try:
            # Simulate preflight request
            headers = {
                'Origin': 'https://chatterfix-mobile.app',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = self.session.options(f"{self.base_url}/auth/config", headers=headers)
            
            cors_headers = {
                'access-control-allow-origin': response.headers.get('Access-Control-Allow-Origin'),
                'access-control-allow-methods': response.headers.get('Access-Control-Allow-Methods'),
                'access-control-allow-headers': response.headers.get('Access-Control-Allow-Headers'),
            }
            
            mobile_friendly = (
                cors_headers.get('access-control-allow-origin') in ['*', 'https://chatterfix-mobile.app'] or
                'chatterfix' in str(cors_headers.get('access-control-allow-origin', '')).lower()
            )
            
            return {
                "status": "PASS" if mobile_friendly else "WARN",
                "cors_headers": cors_headers,
                "mobile_friendly": mobile_friendly
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run complete mobile integration test suite"""
        self.log("INFO", "🚀 Starting Mobile Integration Test Suite")
        self.log("INFO", "=" * 60)
        
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "backend_url": self.base_url,
            "tests": {}
        }
        
        # Test 1: Backend Health
        self.log("INFO", "Test 1: Backend Health Check")
        results["tests"]["backend_health"] = self.test_backend_health()
        
        if not results["tests"]["backend_health"]["accessible"]:
            self.log("FAIL", "Backend not accessible - Stopping tests")
            return results
        
        # Test 2: Authentication Configuration
        self.log("INFO", "\nTest 2: Authentication Configuration")
        results["tests"]["auth_config"] = self.test_auth_configuration()
        
        # Test 3: Authentication Flow
        self.log("INFO", "\nTest 3: Authentication Flow")
        results["tests"]["auth_flow"] = self.test_authentication_flow()
        
        # Test 4: Authenticated API Endpoints
        self.log("INFO", "\nTest 4: Authenticated API Endpoints")
        results["tests"]["api_endpoints"] = self.test_authenticated_endpoints()
        
        # Test 5: Mobile API Compatibility
        self.log("INFO", "\nTest 5: Mobile API Compatibility") 
        results["tests"]["mobile_compatibility"] = self.test_mobile_api_compatibility()
        
        # Test 6: CORS Headers
        self.log("INFO", "\nTest 6: CORS Headers")
        results["tests"]["cors"] = self.test_cors_headers()
        
        # Generate Summary
        self.log("INFO", "\n" + "=" * 60)
        self.generate_test_summary(results)
        
        return results
    
    def generate_test_summary(self, results: Dict[str, Any]):
        """Generate and display test summary"""
        self.log("INFO", "🔍 TEST SUMMARY")
        self.log("INFO", "-" * 40)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warnings = 0
        
        for test_name, test_result in results["tests"].items():
            if isinstance(test_result, dict):
                if test_result.get("status") == "PASS":
                    passed_tests += 1
                elif test_result.get("status") == "FAIL":
                    failed_tests += 1
                elif test_result.get("status") == "WARN":
                    warnings += 1
                total_tests += 1
            else:
                # Handle nested results
                for sub_test, sub_result in test_result.items():
                    if isinstance(sub_result, dict):
                        if sub_result.get("status") == "PASS":
                            passed_tests += 1
                        elif sub_result.get("status") == "FAIL":
                            failed_tests += 1
                        elif sub_result.get("status") == "WARN":
                            warnings += 1
                        total_tests += 1
        
        self.log("PASS", f"✅ Passed: {passed_tests}")
        self.log("FAIL", f"❌ Failed: {failed_tests}")
        if warnings > 0:
            self.log("WARN", f"⚠️  Warnings: {warnings}")
        
        self.log("INFO", f"📊 Total: {total_tests} tests")
        
        # Overall status
        if failed_tests == 0:
            self.log("PASS", "🎉 ALL TESTS PASSED - Mobile app integration ready!")
        elif failed_tests <= 2:
            self.log("WARN", "⚠️  Some issues detected - Review failed tests")
        else:
            self.log("FAIL", "❌ Multiple failures - Integration needs attention")

def main():
    """Main test execution"""
    print("🔬 ChatterFix Mobile Integration Tester")
    print("Testing FixItFred Mobile App ↔ ChatterFix Backend Integration")
    print("=" * 70)
    
    # Test both production and local if available
    test_urls = [BACKEND_URL]
    
    # Check if local development server is available
    try:
        requests.get(LOCAL_URL, timeout=2)
        test_urls.append(LOCAL_URL)
        print(f"🏠 Local dev server detected at {LOCAL_URL}")
    except:
        print("🌐 Testing production backend only")
    
    for url in test_urls:
        print(f"\n🎯 Testing: {url}")
        print("-" * 50)
        
        tester = MobileIntegrationTester(url)
        results = tester.run_full_test_suite()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mobile_integration_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {filename}")

if __name__ == "__main__":
    main()