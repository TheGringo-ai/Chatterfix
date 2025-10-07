#!/usr/bin/env python3
"""
Additional ChatterFix CMMS Platform Tests
Focus on missing features, mobile responsiveness, and data consistency
"""

import requests
import json
import time
from typing import Dict, List, Any

class AdditionalCMSTests:
    def __init__(self, base_url: str = "https://chatterfix.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CMMS-Additional-Tests/1.0',
            'Content-Type': 'application/json'
        })

    def test_missing_features(self):
        """Test for additional features that weren't in main evaluation"""
        print("🔍 Testing Additional Features...")
        
        # Test Safety Module
        try:
            response = self.session.get(f"{self.base_url}/safety", timeout=10)
            if response.status_code == 200:
                print("✅ Safety Module: Available")
                content = response.text.lower()
                safety_features = [
                    ("Incident Reporting", "incident" in content),
                    ("Safety Dashboard", "dashboard" in content),
                    ("Compliance Tracking", "compliance" in content),
                    ("Safety Metrics", "metric" in content or "kpi" in content)
                ]
                for feature, found in safety_features:
                    status = "✅" if found else "⚠️"
                    print(f"   {status} {feature}: {'Found' if found else 'Not Found'}")
            else:
                print(f"❌ Safety Module: Unavailable (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Safety Module: Error - {str(e)}")
        
        # Test Document Intelligence Module
        try:
            response = self.session.get(f"{self.base_url}/document-intelligence", timeout=10)
            if response.status_code == 200:
                print("✅ Document Intelligence Module: Available")
                content = response.text.lower()
                doc_features = [
                    ("Document Upload", "upload" in content),
                    ("OCR Processing", "ocr" in content),
                    ("Search Capability", "search" in content),
                    ("AI Analysis", "ai" in content or "analysis" in content)
                ]
                for feature, found in doc_features:
                    status = "✅" if found else "⚠️"
                    print(f"   {status} {feature}: {'Found' if found else 'Not Found'}")
            else:
                print(f"❌ Document Intelligence Module: Unavailable (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Document Intelligence Module: Error - {str(e)}")
        
        # Test AI Brain Module
        try:
            response = self.session.get(f"{self.base_url}/ai-brain", timeout=10)
            if response.status_code == 200:
                print("✅ AI Brain Module: Available")
                content = response.text.lower()
                ai_features = [
                    ("Predictive Analytics", "predictive" in content),
                    ("Failure Analysis", "failure" in content),
                    ("Optimization", "optimization" in content),
                    ("Machine Learning", "machine" in content or "ml" in content)
                ]
                for feature, found in ai_features:
                    status = "✅" if found else "⚠️"
                    print(f"   {status} {feature}: {'Found' if found else 'Not Found'}")
            else:
                print(f"❌ AI Brain Module: Unavailable (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ AI Brain Module: Error - {str(e)}")

    def test_mobile_responsiveness(self):
        """Test mobile responsiveness by checking viewport and responsive elements"""
        print("\n📱 Testing Mobile Responsiveness...")
        
        # Test with mobile user agent
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        }
        
        pages_to_test = [
            "/dashboard",
            "/assets", 
            "/parts",
            "/work-orders",
            "/pm-scheduling"
        ]
        
        for page in pages_to_test:
            try:
                response = self.session.get(f"{self.base_url}{page}", headers=mobile_headers, timeout=10)
                if response.status_code == 200:
                    content = response.text.lower()
                    
                    # Check for mobile-responsive elements
                    responsive_features = [
                        ("Viewport Meta Tag", 'viewport' in content and 'width=device-width' in content),
                        ("Responsive CSS", '@media' in content or 'mobile' in content),
                        ("Touch-Friendly Elements", 'touch' in content or 'tap' in content),
                        ("Mobile Navigation", 'hamburger' in content or 'menu-toggle' in content)
                    ]
                    
                    print(f"📄 {page}:")
                    for feature, found in responsive_features:
                        status = "✅" if found else "⚠️"
                        print(f"   {status} {feature}: {'Found' if found else 'Not Found'}")
                else:
                    print(f"❌ {page}: Failed to load (HTTP {response.status_code})")
            except Exception as e:
                print(f"❌ {page}: Error - {str(e)}")

    def test_data_consistency(self):
        """Test data consistency across modules"""
        print("\n🔄 Testing Data Consistency...")
        
        try:
            # Get assets data
            assets_response = self.session.get(f"{self.base_url}/api/assets", timeout=10)
            parts_response = self.session.get(f"{self.base_url}/api/parts", timeout=10)
            work_orders_response = self.session.get(f"{self.base_url}/api/work-orders", timeout=10)
            
            if all(r.status_code == 200 for r in [assets_response, parts_response, work_orders_response]):
                assets_data = assets_response.json()
                parts_data = parts_response.json()
                work_orders_data = work_orders_response.json()
                
                print("✅ All API endpoints accessible")
                
                # Check data structure consistency
                data_checks = [
                    ("Assets Data Structure", isinstance(assets_data, (list, dict))),
                    ("Parts Data Structure", isinstance(parts_data, (list, dict))),
                    ("Work Orders Data Structure", isinstance(work_orders_data, (list, dict))),
                ]
                
                for check_name, passed in data_checks:
                    status = "✅" if passed else "❌"
                    print(f"   {status} {check_name}: {'Valid' if passed else 'Invalid'}")
                
                # Check for data relationships
                if isinstance(work_orders_data, list) and isinstance(assets_data, list):
                    wo_with_assets = sum(1 for wo in work_orders_data if isinstance(wo, dict) and wo.get('asset_id'))
                    print(f"   📊 Work Orders with Asset Links: {wo_with_assets}/{len(work_orders_data)}")
                
            else:
                failed_endpoints = []
                if assets_response.status_code != 200:
                    failed_endpoints.append(f"Assets API (HTTP {assets_response.status_code})")
                if parts_response.status_code != 200:
                    failed_endpoints.append(f"Parts API (HTTP {parts_response.status_code})")
                if work_orders_response.status_code != 200:
                    failed_endpoints.append(f"Work Orders API (HTTP {work_orders_response.status_code})")
                
                print(f"❌ Failed endpoints: {', '.join(failed_endpoints)}")
                
        except Exception as e:
            print(f"❌ Data Consistency Test Failed: {str(e)}")

    def test_api_performance(self):
        """Test API response times and performance"""
        print("\n⚡ Testing API Performance...")
        
        endpoints = [
            "/api/assets",
            "/api/parts", 
            "/api/work-orders",
            "/api/managers/kpis",
            "/api/pm-schedules"
        ]
        
        performance_results = []
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=15)
                end_time = time.time()
                
                response_time = end_time - start_time
                performance_results.append((endpoint, response.status_code, response_time))
                
                if response.status_code == 200:
                    if response_time < 2.0:
                        status = "🚀 Fast"
                    elif response_time < 5.0:
                        status = "✅ Good"
                    else:
                        status = "⚠️ Slow"
                else:
                    status = "❌ Failed"
                
                print(f"   {status} {endpoint}: {response_time:.2f}s (HTTP {response.status_code})")
                
            except Exception as e:
                print(f"   ❌ {endpoint}: Error - {str(e)}")
                performance_results.append((endpoint, "ERROR", 0))
        
        # Calculate average response time
        valid_times = [t for _, status, t in performance_results if isinstance(t, float) and t > 0]
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            print(f"\n   📊 Average Response Time: {avg_time:.2f}s")

    def test_security_headers(self):
        """Test for security headers and HTTPS"""
        print("\n🔒 Testing Security...")
        
        try:
            response = self.session.get(f"{self.base_url}/dashboard", timeout=10)
            headers = response.headers
            
            security_checks = [
                ("HTTPS Enabled", self.base_url.startswith("https://")),
                ("X-Frame-Options", "X-Frame-Options" in headers),
                ("X-Content-Type-Options", "X-Content-Type-Options" in headers),
                ("Content-Security-Policy", "Content-Security-Policy" in headers),
                ("Strict-Transport-Security", "Strict-Transport-Security" in headers)
            ]
            
            for check_name, passed in security_checks:
                status = "✅" if passed else "⚠️"
                print(f"   {status} {check_name}: {'Present' if passed else 'Missing'}")
                
        except Exception as e:
            print(f"❌ Security Test Failed: {str(e)}")

    def run_additional_tests(self):
        """Run all additional tests"""
        print("🔬 Starting Additional ChatterFix CMMS Tests")
        print("=" * 60)
        
        self.test_missing_features()
        self.test_mobile_responsiveness()
        self.test_data_consistency()
        self.test_api_performance()
        self.test_security_headers()
        
        print("\n" + "=" * 60)
        print("📋 Additional Testing Complete")

def main():
    """Main execution function"""
    tester = AdditionalCMSTests()
    tester.run_additional_tests()

if __name__ == "__main__":
    main()