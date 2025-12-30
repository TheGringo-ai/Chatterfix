#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for ChatterFix CMMS System
Tests all AI services, CMMS modules, and integration points
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

class ChatterFixSystemTester:
    def __init__(self):
        self.results = {
            'test_timestamp': datetime.now().isoformat(),
            'ai_services': {},
            'cmms_modules': {},
            'integration_tests': {},
            'performance_metrics': {},
            'overall_health': 'unknown'
        }
        
        # Service endpoints (Updated based on actual running services)
        self.main_endpoint = 'http://localhost:8000'
        self.cmms_endpoint = 'http://localhost:8000'  # Main CMMS is on port 8000
        
        # AI endpoints to test (may not all be available)
        self.ai_endpoints = {
            'main_ai_chat': 'http://localhost:8000/api/ai',
            'ollama_local': 'http://localhost:11434'  # Ollama if available
        }
        
    def test_ai_endpoint(self, name: str, url: str) -> Dict[str, Any]:
        """Test individual AI service endpoint"""
        print(f"Testing {name} at {url}...")
        
        result = {
            'name': name,
            'url': url,
            'status': 'failed',
            'response_time': None,
            'error': None,
            'endpoints_tested': {}
        }
        
        try:
            # Test health endpoint
            start_time = time.time()
            health_response = requests.get(f"{url}/health", timeout=10)
            response_time = time.time() - start_time
            
            result['response_time'] = round(response_time * 1000, 2)  # ms
            
            if health_response.status_code == 200:
                result['status'] = 'healthy'
                result['endpoints_tested']['health'] = 'pass'
                
                # Test chat endpoint if available
                try:
                    chat_payload = {
                        'message': 'Hello, this is a test message',
                        'user_id': 'test_user'
                    }
                    
                    chat_response = requests.post(
                        f"{url}/chat", 
                        json=chat_payload, 
                        timeout=15
                    )
                    
                    if chat_response.status_code == 200:
                        result['endpoints_tested']['chat'] = 'pass'
                        chat_data = chat_response.json()
                        if 'response' in chat_data:
                            result['chat_response_length'] = len(chat_data['response'])
                    else:
                        result['endpoints_tested']['chat'] = f'fail ({chat_response.status_code})'
                        
                except Exception as e:
                    result['endpoints_tested']['chat'] = f'error: {str(e)}'
                    
            else:
                result['status'] = f'unhealthy ({health_response.status_code})'
                result['endpoints_tested']['health'] = f'fail ({health_response.status_code})'
                
        except requests.exceptions.ConnectionError:
            result['error'] = 'Connection refused - service not running'
        except requests.exceptions.Timeout:
            result['error'] = 'Request timeout'
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_ai_team_coordinator(self) -> Dict[str, Any]:
        """Test AI Team Coordinator multi-AI routing"""
        print("Testing AI Team Coordinator routing and consensus...")
        
        result = {
            'status': 'failed',
            'routing_test': 'failed',
            'consensus_test': 'failed',
            'response_time': None,
            'error': None
        }
        
        try:
            # Test multi-AI query
            payload = {
                'query': 'What is the best approach for preventive maintenance?',
                'use_consensus': True,
                'required_ais': ['technical', 'intelligent']
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.ai_endpoints['ai_team_coordinator']}/team-query",
                json=payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            result['response_time'] = round(response_time * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                if 'consensus_response' in data:
                    result['consensus_test'] = 'pass'
                if 'individual_responses' in data:
                    result['routing_test'] = 'pass'
                    result['ai_participants'] = len(data['individual_responses'])
                    
                if result['consensus_test'] == 'pass' and result['routing_test'] == 'pass':
                    result['status'] = 'healthy'
            else:
                result['error'] = f'HTTP {response.status_code}'
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_cmms_module(self, module_name: str, endpoints: List[str]) -> Dict[str, Any]:
        """Test CMMS module endpoints"""
        print(f"Testing CMMS {module_name} module...")
        
        result = {
            'module': module_name,
            'status': 'failed',
            'endpoints': {},
            'crud_operations': {},
            'error': None
        }
        
        try:
            # Test each endpoint
            for endpoint in endpoints:
                url = f"{self.cmms_endpoint}/{endpoint}"
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        result['endpoints'][endpoint] = 'pass'
                    else:
                        result['endpoints'][endpoint] = f'fail ({response.status_code})'
                except Exception as e:
                    result['endpoints'][endpoint] = f'error: {str(e)}'
            
            # Test CRUD operations for work orders
            if module_name == 'work_orders':
                result['crud_operations'] = self.test_work_orders_crud()
            elif module_name == 'assets':
                result['crud_operations'] = self.test_assets_crud()
            elif module_name == 'parts':
                result['crud_operations'] = self.test_parts_crud()
                
            # Determine overall status
            passed_endpoints = sum(1 for status in result['endpoints'].values() if status == 'pass')
            if passed_endpoints == len(endpoints):
                result['status'] = 'healthy'
            elif passed_endpoints > 0:
                result['status'] = 'partial'
            else:
                result['status'] = 'failed'
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_work_orders_crud(self) -> Dict[str, str]:
        """Test Work Orders CRUD operations"""
        crud_results = {}
        
        try:
            # Test CREATE
            new_work_order = {
                'title': 'Test Work Order',
                'description': 'Automated test work order',
                'priority': 'Medium',
                'assigned_to': 'Test Technician',
                'equipment_id': 'TEST-001'
            }
            
            create_response = requests.post(
                f"{self.cmms_endpoint}/api/work_orders",
                json=new_work_order,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                crud_results['create'] = 'pass'
                work_order_id = create_response.json().get('id')
                
                # Test READ
                if work_order_id:
                    read_response = requests.get(
                        f"{self.cmms_endpoint}/api/work_orders/{work_order_id}",
                        timeout=10
                    )
                    crud_results['read'] = 'pass' if read_response.status_code == 200 else 'fail'
                    
                    # Test UPDATE
                    update_data = {'status': 'In Progress'}
                    update_response = requests.put(
                        f"{self.cmms_endpoint}/api/work_orders/{work_order_id}",
                        json=update_data,
                        timeout=10
                    )
                    crud_results['update'] = 'pass' if update_response.status_code == 200 else 'fail'
                    
                    # Test DELETE
                    delete_response = requests.delete(
                        f"{self.cmms_endpoint}/api/work_orders/{work_order_id}",
                        timeout=10
                    )
                    crud_results['delete'] = 'pass' if delete_response.status_code == 200 else 'fail'
                else:
                    crud_results['read'] = 'fail - no ID returned'
                    crud_results['update'] = 'fail - no ID returned'
                    crud_results['delete'] = 'fail - no ID returned'
            else:
                crud_results['create'] = f'fail ({create_response.status_code})'
                crud_results['read'] = 'skip'
                crud_results['update'] = 'skip'
                crud_results['delete'] = 'skip'
                
        except Exception as e:
            crud_results['error'] = str(e)
            
        return crud_results
    
    def test_assets_crud(self) -> Dict[str, str]:
        """Test Assets CRUD operations"""
        crud_results = {}
        
        try:
            # Test CREATE
            new_asset = {
                'name': 'Test Asset',
                'asset_tag': 'TEST-ASSET-001',
                'category': 'Test Equipment',
                'location': 'Test Location',
                'status': 'Active'
            }
            
            create_response = requests.post(
                f"{self.cmms_endpoint}/api/assets",
                json=new_asset,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                crud_results['create'] = 'pass'
                # Continue with READ, UPDATE, DELETE similar to work orders
            else:
                crud_results['create'] = f'fail ({create_response.status_code})'
                
        except Exception as e:
            crud_results['error'] = str(e)
            
        return crud_results
    
    def test_parts_crud(self) -> Dict[str, str]:
        """Test Parts CRUD operations"""
        crud_results = {}
        
        try:
            # Test CREATE
            new_part = {
                'part_number': 'TEST-PART-001',
                'name': 'Test Part',
                'description': 'Automated test part',
                'quantity': 10,
                'unit_cost': 25.50
            }
            
            create_response = requests.post(
                f"{self.cmms_endpoint}/api/parts",
                json=new_part,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                crud_results['create'] = 'pass'
                # Continue with READ, UPDATE, DELETE similar to work orders
            else:
                crud_results['create'] = f'fail ({create_response.status_code})'
                
        except Exception as e:
            crud_results['error'] = str(e)
            
        return crud_results
    
    def test_frontend_pages(self) -> Dict[str, Any]:
        """Test frontend pages and responsiveness"""
        pages_to_test = [
            '',  # Landing page
            'dashboard',
            'work-orders',
            'assets',
            'parts',
            'reports'
        ]
        
        results = {}
        
        for page in pages_to_test:
            url = f"{self.cmms_endpoint}/{page}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    results[page or 'landing'] = {
                        'status': 'pass',
                        'content_length': len(response.content),
                        'contains_ai_widget': 'ai-chat' in response.text.lower()
                    }
                else:
                    results[page or 'landing'] = {
                        'status': f'fail ({response.status_code})'
                    }
            except Exception as e:
                results[page or 'landing'] = {
                    'status': f'error: {str(e)}'
                }
                
        return results
    
    def run_comprehensive_test(self):
        """Run all tests and compile results"""
        print("=" * 60)
        print("CHATTERFIX CMMS COMPREHENSIVE SYSTEM TEST")
        print("=" * 60)
        
        # Test 1: AI Services
        print("\n1. Testing AI Services...")
        for name, url in self.ai_endpoints.items():
            self.results['ai_services'][name] = self.test_ai_endpoint(name, url)
        
        # Test 2: AI Team Coordinator
        print("\n2. Testing AI Team Coordinator...")
        self.results['ai_services']['team_coordinator'] = self.test_ai_team_coordinator()
        
        # Test 3: CMMS Modules
        print("\n3. Testing CMMS Modules...")
        cmms_modules = {
            'work_orders': ['work-orders', 'api/work_orders'],
            'assets': ['assets', 'api/assets'],
            'parts': ['parts', 'api/parts'],
            'dashboard': ['dashboard', 'api/dashboard/stats']
        }
        
        for module, endpoints in cmms_modules.items():
            self.results['cmms_modules'][module] = self.test_cmms_module(module, endpoints)
        
        # Test 4: Frontend Pages
        print("\n4. Testing Frontend Pages...")
        self.results['frontend_pages'] = self.test_frontend_pages()
        
        # Test 5: Integration Tests
        print("\n5. Running Integration Tests...")
        self.results['integration_tests'] = self.run_integration_tests()
        
        # Calculate overall health
        self.calculate_overall_health()
        
        # Save results
        self.save_results()
        
        return self.results
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests between modules"""
        integration_results = {}
        
        # Test AI-CMMS integration
        try:
            # Test if AI can query work orders
            payload = {
                'query': 'How many work orders are currently open?',
                'context': 'cmms_integration'
            }
            
            response = requests.post(
                f"{self.ai_endpoints['intelligent_ai']}/chat",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                integration_results['ai_cmms_integration'] = 'pass'
            else:
                integration_results['ai_cmms_integration'] = 'fail'
                
        except Exception as e:
            integration_results['ai_cmms_integration'] = f'error: {str(e)}'
        
        return integration_results
    
    def calculate_overall_health(self):
        """Calculate overall system health score"""
        total_tests = 0
        passed_tests = 0
        
        # Count AI service tests
        for service_result in self.results['ai_services'].values():
            total_tests += 1
            if service_result.get('status') == 'healthy':
                passed_tests += 1
        
        # Count CMMS module tests
        for module_result in self.results['cmms_modules'].values():
            total_tests += 1
            if module_result.get('status') == 'healthy':
                passed_tests += 1
        
        # Count frontend page tests
        for page_result in self.results['frontend_pages'].values():
            total_tests += 1
            if page_result.get('status') == 'pass':
                passed_tests += 1
        
        health_percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if health_percentage >= 90:
            self.results['overall_health'] = 'excellent'
        elif health_percentage >= 75:
            self.results['overall_health'] = 'good'
        elif health_percentage >= 50:
            self.results['overall_health'] = 'fair'
        else:
            self.results['overall_health'] = 'poor'
            
        self.results['health_score'] = round(health_percentage, 2)
        self.results['tests_summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests
        }
    
    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nTest results saved to: {filename}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Health: {self.results['overall_health'].upper()}")
        print(f"Health Score: {self.results['health_score']}%")
        print(f"Tests Passed: {self.results['tests_summary']['passed_tests']}/{self.results['tests_summary']['total_tests']}")
        
        print("\nAI Services Status:")
        for name, result in self.results['ai_services'].items():
            status = result.get('status', 'unknown')
            response_time = result.get('response_time', 'N/A')
            print(f"  {name}: {status} ({response_time}ms)")
        
        print("\nCMMS Modules Status:")
        for name, result in self.results['cmms_modules'].items():
            status = result.get('status', 'unknown')
            print(f"  {name}: {status}")
        
        if self.results['integration_tests']:
            print("\nIntegration Tests:")
            for test, result in self.results['integration_tests'].items():
                print(f"  {test}: {result}")

if __name__ == "__main__":
    tester = ChatterFixSystemTester()
    results = tester.run_comprehensive_test()
    tester.print_summary()