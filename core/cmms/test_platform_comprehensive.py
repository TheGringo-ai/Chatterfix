#!/usr/bin/env python3
"""
ChatterFix CMMS Platform Comprehensive Testing Script
Using AI team approach (ChatGPT guidance) for systematic testing
"""

import requests
import json
import time
from datetime import datetime

class ChatterFixTester:
    def __init__(self):
        self.base_urls = {
            'main': 'https://chatterfix.com',
            'ui_gateway': 'https://chatterfix-ui-gateway-psycl7nhha-uc.a.run.app',
            'work_orders': 'https://chatterfix-work-orders-psycl7nhha-uc.a.run.app',
            'assets': 'https://chatterfix-assets-psycl7nhha-uc.a.run.app', 
            'parts': 'https://chatterfix-parts-psycl7nhha-uc.a.run.app',
            'ai_brain': 'https://chatterfix-ai-brain-psycl7nhha-uc.a.run.app',
            'document_intelligence': 'https://chatterfix-document-intelligence-psycl7nhha-uc.a.run.app',
            'backend': 'https://chatterfix-backend-unified-psycl7nhha-uc.a.run.app'
        }
        self.test_results = {}
        
    def log_result(self, test_name, status, message, response_time=None):
        """Log test results with ChatGPT recommended format"""
        self.test_results[test_name] = {
            'status': status,
            'message': message,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        
    def test_health_endpoints(self):
        """Test all health endpoints - ChatGPT recommended approach"""
        print("🔍 Testing Health Endpoints...")
        
        for service, url in self.base_urls.items():
            try:
                start_time = time.time()
                response = requests.get(f"{url}/health", timeout=10)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    self.log_result(f"health_{service}", 'PASS', f"Service healthy: {status}", response_time)
                    print(f"✅ {service}: {status} ({response_time}ms)")
                else:
                    self.log_result(f"health_{service}", 'FAIL', f"HTTP {response.status_code}")
                    print(f"❌ {service}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"health_{service}", 'ERROR', str(e))
                print(f"💥 {service}: {str(e)}")
                
    def test_work_orders_api(self):
        """Test work orders functionality - Database verification approach"""
        print("\n🔍 Testing Work Orders API...")
        
        try:
            # Test GET work orders
            url = f"{self.base_urls['work_orders']}/api/work-orders"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                work_orders = response.json()
                self.log_result("work_orders_get", 'PASS', f"Retrieved {len(work_orders)} work orders")
                print(f"✅ Work Orders GET: {len(work_orders)} records")
                
                # Test POST create work order
                test_work_order = {
                    "title": "AI Test Work Order",
                    "description": "Created by AI testing team",
                    "priority": "high",
                    "status": "open",
                    "assigned_to": "AI Tester"
                }
                
                post_response = requests.post(url, json=test_work_order, timeout=10)
                if post_response.status_code in [200, 201]:
                    self.log_result("work_orders_post", 'PASS', "Successfully created test work order")
                    print(f"✅ Work Order CREATE: Success")
                else:
                    self.log_result("work_orders_post", 'FAIL', f"HTTP {post_response.status_code}")
                    print(f"❌ Work Order CREATE: HTTP {post_response.status_code}")
                    
            else:
                self.log_result("work_orders_get", 'FAIL', f"HTTP {response.status_code}")
                print(f"❌ Work Orders GET: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("work_orders_api", 'ERROR', str(e))
            print(f"💥 Work Orders API: {str(e)}")
            
    def test_ai_functionality(self):
        """Test AI features - ChatGPT integration verification"""
        print("\n🔍 Testing AI Functionality...")
        
        # Test AI Brain service
        try:
            url = f"{self.base_urls['ai_brain']}/api/chat"
            test_message = {
                "message": "Test AI functionality for work order optimization",
                "context": "maintenance_planning"
            }
            
            response = requests.post(url, json=test_message, timeout=15)
            if response.status_code == 200:
                self.log_result("ai_chat", 'PASS', "AI chat functionality working")
                print(f"✅ AI Chat: Working")
            else:
                self.log_result("ai_chat", 'FAIL', f"HTTP {response.status_code}")
                print(f"❌ AI Chat: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("ai_chat", 'ERROR', str(e))
            print(f"💥 AI Chat: {str(e)}")
            
    def test_database_connectivity(self):
        """Test database connectivity through APIs"""
        print("\n🔍 Testing Database Connectivity...")
        
        endpoints_to_test = [
            ("work_orders", "/api/work-orders"),
            ("assets", "/api/assets"),
            ("parts", "/api/parts")
        ]
        
        for service, endpoint in endpoints_to_test:
            try:
                url = f"{self.base_urls[service]}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(f"db_{service}", 'PASS', f"Database accessible, {len(data)} records")
                    print(f"✅ {service} DB: {len(data)} records")
                else:
                    self.log_result(f"db_{service}", 'FAIL', f"HTTP {response.status_code}")
                    print(f"❌ {service} DB: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"db_{service}", 'ERROR', str(e))
                print(f"💥 {service} DB: {str(e)}")
                
    def run_comprehensive_test(self):
        """Run all tests - ChatGPT recommended test suite"""
        print("🚀 ChatterFix CMMS Comprehensive Testing")
        print("=" * 50)
        
        self.test_health_endpoints()
        self.test_work_orders_api()
        self.test_ai_functionality()
        self.test_database_connectivity()
        
        # Generate summary report
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        pass_count = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        fail_count = sum(1 for result in self.test_results.values() if result['status'] == 'FAIL')
        error_count = sum(1 for result in self.test_results.values() if result['status'] == 'ERROR')
        
        print(f"✅ PASSED: {pass_count}")
        print(f"❌ FAILED: {fail_count}")
        print(f"💥 ERRORS: {error_count}")
        print(f"📈 SUCCESS RATE: {(pass_count / len(self.test_results) * 100):.1f}%")
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed results saved to test_results.json")
        
        return self.test_results

if __name__ == "__main__":
    tester = ChatterFixTester()
    results = tester.run_comprehensive_test()