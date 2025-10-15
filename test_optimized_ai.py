#!/usr/bin/env python3
"""
Test script for optimized Fix It Fred AI Service
Tests all critical endpoints and functionality
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:9001"  # Test on alternate port
TEST_CASES = [
    {
        "name": "Health Check",
        "method": "GET",
        "endpoint": "/health",
        "expected": 200
    },
    {
        "name": "Provider List",
        "method": "GET", 
        "endpoint": "/api/providers",
        "expected": 200
    },
    {
        "name": "Cache Stats",
        "method": "GET",
        "endpoint": "/api/cache/stats", 
        "expected": 200
    },
    {
        "name": "Chat API (/api/chat)",
        "method": "POST",
        "endpoint": "/api/chat",
        "data": {
            "message": "What parts should I check for the pump maintenance?",
            "provider": "ollama",
            "context": "Pump #1 maintenance"
        },
        "expected": 200
    },
    {
        "name": "Chat API (/api/ai/chat) - New Endpoint",
        "method": "POST", 
        "endpoint": "/api/ai/chat",
        "data": {
            "message": "Low stock alert for bearings - recommend action",
            "provider": "ollama",
            "context": "Parts management"
        },
        "expected": 200
    }
]

def test_service():
    print("🧪 Testing Optimized Fix It Fred AI Service")
    print("=" * 50)
    
    results = []
    
    for test in TEST_CASES:
        print(f"\n🔍 Testing: {test['name']}")
        start_time = time.time()
        
        try:
            if test["method"] == "GET":
                response = requests.get(f"{BASE_URL}{test['endpoint']}", timeout=10)
            else:
                response = requests.post(
                    f"{BASE_URL}{test['endpoint']}", 
                    json=test.get("data", {}),
                    timeout=30
                )
            
            duration = time.time() - start_time
            
            if response.status_code == test["expected"]:
                print(f"✅ PASS - {test['name']} ({duration:.2f}s)")
                if test['name'].startswith("Chat"):
                    data = response.json()
                    print(f"   Response: {data.get('response', 'N/A')[:100]}...")
                    print(f"   Provider: {data.get('provider', 'N/A')}")
            else:
                print(f"❌ FAIL - {test['name']} - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
            results.append({
                "test": test['name'],
                "status": "PASS" if response.status_code == test["expected"] else "FAIL",
                "duration": duration,
                "response_code": response.status_code
            })
            
        except Exception as e:
            print(f"❌ ERROR - {test['name']}: {e}")
            results.append({
                "test": test['name'], 
                "status": "ERROR",
                "duration": 0,
                "error": str(e)
            })
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = len([r for r in results if r["status"] == "PASS"])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - AI Service Optimized Successfully!")
    else:
        print(f"\n❌ {total-passed} TESTS FAILED - Issues need attention")
    
    return results

if __name__ == "__main__":
    test_service()