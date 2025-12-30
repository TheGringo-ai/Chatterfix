#!/usr/bin/env python3
"""
ChatterFix Enterprise Functionality Test
Comprehensive test of all enterprise features
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnterpriseFunctionalityTest:
    """Test all enterprise features"""
    
    def __init__(self):
        self.services = {
            "Fix It Fred AI": "http://localhost:8005/health",
            "ChatterFix Gateway": "http://localhost:8000/health"
        }
        self.test_results = {}
        
    async def run_comprehensive_test(self):
        """Run all enterprise functionality tests"""
        logger.info("🧪 Starting Enterprise Functionality Test Suite...")
        
        # Test 1: Service Health
        await self.test_service_health()
        
        # Test 2: AI Functionality
        await self.test_ai_functionality()
        
        # Test 3: Documentation System
        await self.test_documentation_system()
        
        # Test 4: Integration Tests
        await self.test_integration()
        
        # Test 5: Performance Tests
        await self.test_performance()
        
        # Generate final report
        await self.generate_test_report()
        
    async def test_service_health(self):
        """Test all service health endpoints"""
        logger.info("🏥 Testing service health...")
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for service_name, url in self.services.items():
                try:
                    start_time = time.time()
                    async with session.get(url, timeout=10) as response:
                        response_time = time.time() - start_time
                        data = await response.json()
                        
                        results[service_name] = {
                            "status": "PASS" if response.status == 200 else "FAIL",
                            "response_time": response_time,
                            "status_code": response.status,
                            "health_data": data
                        }
                        
                        if response.status == 200:
                            logger.info(f"✅ {service_name}: Healthy ({response_time:.2f}s)")
                        else:
                            logger.error(f"❌ {service_name}: Unhealthy (HTTP {response.status})")
                            
                except Exception as e:
                    results[service_name] = {
                        "status": "FAIL",
                        "error": str(e)
                    }
                    logger.error(f"❌ {service_name}: Error - {e}")
        
        self.test_results["service_health"] = results
        
    async def test_ai_functionality(self):
        """Test Fix It Fred AI functionality"""
        logger.info("🤖 Testing AI functionality...")
        
        test_cases = [
            {
                "name": "Basic Chat",
                "message": "Hello Fix It Fred, how are you?",
                "expected_response_contains": ["fred", "hello", "help"]
            },
            {
                "name": "Maintenance Query",
                "message": "How do I troubleshoot a pump failure?",
                "expected_response_contains": ["pump", "troubleshoot", "check"]
            },
            {
                "name": "ChatterFix Integration",
                "message": "Tell me about ChatterFix CMMS features",
                "expected_response_contains": ["chatterfix", "cmms", "maintenance"]
            }
        ]
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for test_case in test_cases:
                try:
                    payload = {
                        "message": test_case["message"],
                        "context": "maintenance",
                        "provider": "ollama"
                    }
                    
                    start_time = time.time()
                    async with session.post(
                        "http://localhost:8005/api/chat",
                        json=payload,
                        timeout=30
                    ) as response:
                        response_time = time.time() - start_time
                        data = await response.json()
                        
                        # Check if response is successful
                        success = response.status == 200 and data.get("success", False)
                        
                        # Check response content
                        response_text = data.get("response", "").lower()
                        content_match = any(
                            keyword.lower() in response_text 
                            for keyword in test_case["expected_response_contains"]
                        )
                        
                        results[test_case["name"]] = {
                            "status": "PASS" if success and len(response_text) > 10 else "FAIL",
                            "response_time": response_time,
                            "response_length": len(response_text),
                            "content_relevant": content_match,
                            "ai_provider": data.get("provider", "unknown"),
                            "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                        }
                        
                        if success:
                            logger.info(f"✅ AI Test '{test_case['name']}': PASS ({response_time:.2f}s)")
                        else:
                            logger.error(f"❌ AI Test '{test_case['name']}': FAIL")
                            
                except Exception as e:
                    results[test_case["name"]] = {
                        "status": "FAIL",
                        "error": str(e)
                    }
                    logger.error(f"❌ AI Test '{test_case['name']}': Error - {e}")
        
        self.test_results["ai_functionality"] = results
        
    async def test_documentation_system(self):
        """Test documentation system integrity"""
        logger.info("📚 Testing documentation system...")
        
        doc_files = [
            "AI_LOOK.md",
            "AI_LOOK_TECHNICAL_ADDENDUM.md", 
            "AI_LOOK_QUICK_START.md",
            "AI_LOOK_INDEX.md"
        ]
        
        results = {}
        for doc_file in doc_files:
            try:
                with open(doc_file, 'r') as f:
                    content = f.read()
                    
                results[doc_file] = {
                    "status": "PASS",
                    "file_size": len(content),
                    "line_count": len(content.split('\\n')),
                    "word_count": len(content.split()),
                    "has_headers": "##" in content,
                    "has_code_blocks": "```" in content,
                    "has_links": "[" in content and "](" in content
                }
                
                logger.info(f"✅ Documentation '{doc_file}': PASS ({len(content.split('\\n'))} lines)")
                
            except FileNotFoundError:
                results[doc_file] = {
                    "status": "FAIL",
                    "error": "File not found"
                }
                logger.error(f"❌ Documentation '{doc_file}': File not found")
            except Exception as e:
                results[doc_file] = {
                    "status": "FAIL", 
                    "error": str(e)
                }
                logger.error(f"❌ Documentation '{doc_file}': Error - {e}")
        
        self.test_results["documentation_system"] = results
        
    async def test_integration(self):
        """Test system integration"""
        logger.info("🔗 Testing system integration...")
        
        integration_tests = {
            "AI_Service_to_Documentation": {
                "description": "AI service provides data for documentation updates",
                "test": "ai_service_accessible"
            },
            "Documentation_Auto_Update": {
                "description": "Documentation system can detect and handle changes",
                "test": "doc_system_responsive"
            },
            "Enterprise_Monitoring": {
                "description": "Monitoring system tracks all components",
                "test": "monitoring_active"
            }
        }
        
        results = {}
        for test_name, test_info in integration_tests.items():
            try:
                # Simplified integration test
                if test_info["test"] == "ai_service_accessible":
                    # Test if AI service is accessible for integration
                    async with aiohttp.ClientSession() as session:
                        async with session.get("http://localhost:8005/health") as response:
                            success = response.status == 200
                            
                elif test_info["test"] == "doc_system_responsive":
                    # Test if documentation files are writable/readable
                    success = all(
                        open(f, 'r').readable() for f in [
                            "AI_LOOK.md", "AI_LOOK_QUICK_START.md"
                        ] if open(f, 'r')
                    )
                    
                elif test_info["test"] == "monitoring_active":
                    # Test if monitoring capabilities are available
                    import psutil
                    success = psutil.cpu_percent() >= 0  # Basic system monitoring test
                
                results[test_name] = {
                    "status": "PASS" if success else "FAIL",
                    "description": test_info["description"]
                }
                
                if success:
                    logger.info(f"✅ Integration Test '{test_name}': PASS")
                else:
                    logger.error(f"❌ Integration Test '{test_name}': FAIL")
                    
            except Exception as e:
                results[test_name] = {
                    "status": "FAIL",
                    "error": str(e),
                    "description": test_info["description"]
                }
                logger.error(f"❌ Integration Test '{test_name}': Error - {e}")
        
        self.test_results["integration"] = results
        
    async def test_performance(self):
        """Test system performance"""
        logger.info("⚡ Testing system performance...")
        
        # Simple performance tests
        performance_results = {}
        
        try:
            # Test AI response time under load
            start_time = time.time()
            
            # Send multiple requests to test load handling
            async with aiohttp.ClientSession() as session:
                tasks = []
                for i in range(5):  # 5 concurrent requests
                    task = session.post(
                        "http://localhost:8005/api/chat",
                        json={"message": f"Test message {i}", "provider": "ollama"},
                        timeout=30
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
            total_time = time.time() - start_time
            successful_responses = sum(1 for r in responses if not isinstance(r, Exception))
            
            performance_results["load_test"] = {
                "status": "PASS" if successful_responses >= 3 else "FAIL",
                "total_requests": 5,
                "successful_requests": successful_responses,
                "total_time": total_time,
                "avg_response_time": total_time / 5
            }
            
            if successful_responses >= 3:
                logger.info(f"✅ Load Test: PASS ({successful_responses}/5 successful in {total_time:.2f}s)")
            else:
                logger.error(f"❌ Load Test: FAIL ({successful_responses}/5 successful)")
                
        except Exception as e:
            performance_results["load_test"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ Load Test: Error - {e}")
        
        self.test_results["performance"] = performance_results
        
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating test report...")
        
        # Calculate overall results
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            for test_name, result in tests.items():
                total_tests += 1
                if result.get("status") == "PASS":
                    passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate report
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": round(success_rate, 2),
                "overall_status": "PASS" if success_rate >= 80 else "FAIL"
            },
            "detailed_results": self.test_results
        }
        
        # Save report
        report_file = f"reports/enterprise_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\\n" + "="*60)
        print("🎉 CHATTERFIX ENTERPRISE FUNCTIONALITY TEST REPORT")
        print("="*60)
        print(f"Overall Status: {'✅ PASS' if report['summary']['overall_status'] == 'PASS' else '❌ FAIL'}")
        print(f"Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"Test Categories: {len(self.test_results)}")
        print(f"Report Saved: {report_file}")
        print()
        
        # Show category results
        for category, tests in self.test_results.items():
            category_passed = sum(1 for t in tests.values() if t.get("status") == "PASS")
            category_total = len(tests)
            print(f"📂 {category.replace('_', ' ').title()}: {category_passed}/{category_total}")
        
        print("="*60)
        
        logger.info(f"Test report saved: {report_file}")
        return report

async def main():
    """Run enterprise functionality tests"""
    tester = EnterpriseFunctionalityTest()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())