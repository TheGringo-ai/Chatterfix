#!/usr/bin/env python3
"""
Focused System Test for ChatterFix CMMS
Tests the actual working components on port 8000
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class FocusedSystemTester:
    def __init__(self):
        self.base_url = 'http://localhost:8000'
        self.results = {
            'test_timestamp': datetime.now().isoformat(),
            'service_status': {},
            'api_endpoints': {},
            'frontend_pages': {},
            'database_connectivity': {},
            'overall_assessment': {}
        }
        
    def test_basic_connectivity(self):
        """Test basic service connectivity"""
        print("Testing basic service connectivity...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.results['service_status'] = {
                    'status': 'healthy',
                    'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                    'health_data': health_data
                }
                print(f"✅ Service healthy: {health_data}")
            else:
                self.results['service_status'] = {
                    'status': 'unhealthy',
                    'http_code': response.status_code
                }
                print(f"❌ Service unhealthy: HTTP {response.status_code}")
        except Exception as e:
            self.results['service_status'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ Service connection failed: {e}")
    
    def test_api_endpoints(self):
        """Test individual API endpoints"""
        print("\nTesting API endpoints...")
        
        endpoints = [
            '/api/parts',
            '/api/work-orders', 
            '/api/assets'
        ]
        
        for endpoint in endpoints:
            print(f"Testing {endpoint}...")
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.results['api_endpoints'][endpoint] = {
                            'status': 'working',
                            'response_time_ms': response_time,
                            'data_type': type(data).__name__,
                            'data_length': len(data) if isinstance(data, (list, dict)) else 'unknown'
                        }
                        print(f"✅ {endpoint}: Working ({response_time}ms)")
                    except json.JSONDecodeError:
                        self.results['api_endpoints'][endpoint] = {
                            'status': 'working_no_json',
                            'response_time_ms': response_time,
                            'content_length': len(response.content)
                        }
                        print(f"⚠️ {endpoint}: Working but no JSON response")
                elif response.status_code == 500:
                    self.results['api_endpoints'][endpoint] = {
                        'status': 'internal_error',
                        'response_time_ms': response_time,
                        'error_content': response.text[:200] if response.text else 'No error details'
                    }
                    print(f"❌ {endpoint}: Internal Server Error")
                else:
                    self.results['api_endpoints'][endpoint] = {
                        'status': f'http_{response.status_code}',
                        'response_time_ms': response_time
                    }
                    print(f"❌ {endpoint}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.results['api_endpoints'][endpoint] = {
                    'status': 'exception',
                    'error': str(e)
                }
                print(f"❌ {endpoint}: Exception - {e}")
    
    def test_frontend_pages(self):
        """Test frontend page accessibility"""
        print("\nTesting frontend pages...")
        
        pages = [
            ('Homepage', '/'),
            ('API Docs', '/docs'),
            ('OpenAPI Schema', '/openapi.json')
        ]
        
        for page_name, path in pages:
            print(f"Testing {page_name} ({path})...")
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    self.results['frontend_pages'][page_name] = {
                        'status': 'accessible',
                        'response_time_ms': response_time,
                        'content_length': len(response.content),
                        'content_type': response.headers.get('content-type', 'unknown')
                    }
                    print(f"✅ {page_name}: Accessible ({response_time}ms)")
                else:
                    self.results['frontend_pages'][page_name] = {
                        'status': f'http_{response.status_code}',
                        'response_time_ms': response_time
                    }
                    print(f"❌ {page_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.results['frontend_pages'][page_name] = {
                    'status': 'exception',
                    'error': str(e)
                }
                print(f"❌ {page_name}: Exception - {e}")
    
    def test_crud_operations(self):
        """Test basic CRUD operations"""
        print("\nTesting CRUD operations...")
        
        # Test POST to create a new part
        test_part = {
            "name": "Test Part for Testing",
            "part_number": f"TEST-{int(time.time())}",
            "description": "Automated test part",
            "quantity": 5,
            "unit_cost": 19.99
        }
        
        try:
            print("Testing CREATE operation (POST /api/parts)...")
            create_response = requests.post(
                f"{self.base_url}/api/parts",
                json=test_part,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                try:
                    created_data = create_response.json()
                    self.results['database_connectivity']['create_test'] = {
                        'status': 'working',
                        'created_item': created_data
                    }
                    print("✅ CREATE operation: Working")
                    
                    # If we got an ID back, try to fetch it
                    if isinstance(created_data, dict) and 'id' in created_data:
                        item_id = created_data['id']
                        print(f"Testing READ operation (GET /api/parts/{item_id})...")
                        read_response = requests.get(f"{self.base_url}/api/parts/{item_id}", timeout=10)
                        
                        if read_response.status_code == 200:
                            self.results['database_connectivity']['read_test'] = {
                                'status': 'working',
                                'retrieved_item': read_response.json()
                            }
                            print("✅ READ operation: Working")
                        else:
                            self.results['database_connectivity']['read_test'] = {
                                'status': f'failed_http_{read_response.status_code}'
                            }
                            print(f"❌ READ operation: HTTP {read_response.status_code}")
                            
                except json.JSONDecodeError:
                    self.results['database_connectivity']['create_test'] = {
                        'status': 'no_json_response',
                        'raw_response': create_response.text[:200]
                    }
                    print("⚠️ CREATE operation: Success but no JSON response")
            else:
                self.results['database_connectivity']['create_test'] = {
                    'status': f'failed_http_{create_response.status_code}',
                    'error_content': create_response.text[:200]
                }
                print(f"❌ CREATE operation: HTTP {create_response.status_code}")
                
        except Exception as e:
            self.results['database_connectivity']['create_test'] = {
                'status': 'exception',
                'error': str(e)
            }
            print(f"❌ CREATE operation: Exception - {e}")
    
    def analyze_system_health(self):
        """Analyze overall system health"""
        print("\nAnalyzing overall system health...")
        
        working_components = 0
        total_components = 0
        
        # Count service health
        if self.results['service_status'].get('status') == 'healthy':
            working_components += 1
        total_components += 1
        
        # Count API endpoints
        for endpoint_result in self.results['api_endpoints'].values():
            if endpoint_result.get('status') == 'working':
                working_components += 1
            total_components += 1
        
        # Count frontend pages
        for page_result in self.results['frontend_pages'].values():
            if page_result.get('status') == 'accessible':
                working_components += 1
            total_components += 1
        
        # Count database operations
        for db_test in self.results['database_connectivity'].values():
            if db_test.get('status') == 'working':
                working_components += 1
            total_components += 1
        
        health_percentage = (working_components / total_components * 100) if total_components > 0 else 0
        
        # Determine overall status
        if health_percentage >= 80:
            overall_status = "GOOD"
        elif health_percentage >= 60:
            overall_status = "FAIR"
        elif health_percentage >= 40:
            overall_status = "POOR"
        else:
            overall_status = "CRITICAL"
        
        self.results['overall_assessment'] = {
            'health_percentage': round(health_percentage, 2),
            'overall_status': overall_status,
            'working_components': working_components,
            'total_components': total_components,
            'key_issues': self.identify_key_issues()
        }
        
        print(f"\n🎯 Overall System Health: {overall_status} ({health_percentage:.1f}%)")
        print(f"📊 Components Working: {working_components}/{total_components}")
        
    def identify_key_issues(self):
        """Identify key issues affecting the system"""
        issues = []
        
        # Check if service is down
        if self.results['service_status'].get('status') != 'healthy':
            issues.append("Main service connectivity issues")
        
        # Check API endpoints
        failing_apis = [
            endpoint for endpoint, result in self.results['api_endpoints'].items()
            if result.get('status') not in ['working', 'working_no_json']
        ]
        if failing_apis:
            issues.append(f"API endpoints failing: {', '.join(failing_apis)}")
        
        # Check database connectivity
        db_issues = [
            test_name for test_name, result in self.results['database_connectivity'].items()
            if result.get('status') != 'working'
        ]
        if db_issues:
            issues.append(f"Database operations failing: {', '.join(db_issues)}")
        
        return issues
    
    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"focused_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {filename}")
    
    def run_focused_test(self):
        """Run the complete focused test suite"""
        print("=" * 60)
        print("CHATTERFIX CMMS FOCUSED SYSTEM TEST")
        print("=" * 60)
        
        self.test_basic_connectivity()
        self.test_api_endpoints()
        self.test_frontend_pages()
        self.test_crud_operations()
        self.analyze_system_health()
        self.save_results()
        
        return self.results

if __name__ == "__main__":
    tester = FocusedSystemTester()
    results = tester.run_focused_test()