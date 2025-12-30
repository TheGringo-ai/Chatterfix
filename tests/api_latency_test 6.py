#!/usr/bin/env python3
"""
Phase 7 API Latency Test Suite
Validates API P95 < 1000ms enterprise requirement
"""

import pytest
import aiohttp
import asyncio
import time
import statistics
from datetime import datetime

class TestAPILatency:
    """Enterprise API latency validation"""
    
    # Critical API endpoints that must meet <1000ms P95 requirement
    critical_endpoints = [
        {
            "url": "https://chatterfix-unified-gateway-650169261019.us-central1.run.app/health",
            "max_p95_ms": 500,  # Gateway should be very fast
            "name": "unified-gateway-health"
        },
        {
            "url": "https://chatterfix-cmms-650169261019.us-central1.run.app/health", 
            "max_p95_ms": 800,
            "name": "cmms-health"
        },
        {
            "url": "https://chatterfix-revenue-intelligence-650169261019.us-central1.run.app/health",
            "max_p95_ms": 1000,
            "name": "revenue-intelligence-health"
        },
        {
            "url": "https://chatterfix-customer-success-650169261019.us-central1.run.app/health",
            "max_p95_ms": 1000,
            "name": "customer-success-health"
        },
        {
            "url": "https://chatterfix-data-room-650169261019.us-central1.run.app/health",
            "max_p95_ms": 1000,
            "name": "data-room-health"
        }
    ]
    
    # API endpoints with data queries
    api_endpoints = [
        {
            "url": "https://chatterfix-cmms-650169261019.us-central1.run.app/api/assets",
            "max_p95_ms": 1000,
            "name": "cmms-assets-api"
        },
        {
            "url": "https://chatterfix-revenue-intelligence-650169261019.us-central1.run.app/api/revenue",
            "max_p95_ms": 1200,  # Slightly higher for complex calculations
            "name": "revenue-api"
        }
    ]
    
    @pytest.mark.asyncio
    async def test_health_endpoint_p95_latency(self):
        """Test that all health endpoints meet P95 < 1000ms"""
        async with aiohttp.ClientSession() as session:
            for endpoint in self.critical_endpoints:
                response_times = []
                
                # Make 20 requests to calculate P95
                for i in range(20):
                    start_time = time.time()
                    
                    try:
                        async with session.get(endpoint["url"], timeout=aiohttp.ClientTimeout(total=10)) as response:
                            response_time_ms = (time.time() - start_time) * 1000
                            response_times.append(response_time_ms)
                            
                            assert response.status == 200, f"Endpoint {endpoint['name']} returned {response.status}"
                    
                    except asyncio.TimeoutError:
                        pytest.fail(f"Endpoint {endpoint['name']} timed out (>10s)")
                    except aiohttp.ClientError as e:
                        pytest.skip(f"Endpoint not available: {endpoint['name']} - {e}")
                    
                    # Brief pause between requests
                    await asyncio.sleep(0.1)
                
                if response_times:
                    # Calculate P95 (95th percentile)
                    p95_latency = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                    avg_latency = statistics.mean(response_times)
                    max_latency = max(response_times)
                    
                    print(f"\n{endpoint['name']} Latency Stats:")
                    print(f"  Average: {avg_latency:.1f}ms")
                    print(f"  P95: {p95_latency:.1f}ms") 
                    print(f"  Max: {max_latency:.1f}ms")
                    print(f"  Target P95: <{endpoint['max_p95_ms']}ms")
                    
                    assert p95_latency < endpoint["max_p95_ms"], \
                        f"P95 latency {p95_latency:.1f}ms exceeds {endpoint['max_p95_ms']}ms for {endpoint['name']}"
    
    @pytest.mark.asyncio
    async def test_api_endpoint_performance(self):
        """Test API endpoints with actual data queries"""
        async with aiohttp.ClientSession() as session:
            for endpoint in self.api_endpoints:
                response_times = []
                
                # Make 10 requests (fewer for data-heavy endpoints)
                for i in range(10):
                    start_time = time.time()
                    
                    try:
                        async with session.get(endpoint["url"], timeout=aiohttp.ClientTimeout(total=15)) as response:
                            response_time_ms = (time.time() - start_time) * 1000
                            response_times.append(response_time_ms)
                            
                            # Accept 200 or 404 (service might not have test data)
                            assert response.status in [200, 404, 422], \
                                f"API endpoint {endpoint['name']} returned unexpected {response.status}"
                    
                    except asyncio.TimeoutError:
                        pytest.fail(f"API endpoint {endpoint['name']} timed out (>15s)")
                    except aiohttp.ClientError as e:
                        pytest.skip(f"API endpoint not available: {endpoint['name']} - {e}")
                    
                    await asyncio.sleep(0.2)  # Longer pause for API endpoints
                
                if response_times:
                    p95_latency = statistics.quantiles(response_times, n=10)[8] if len(response_times) >= 10 else max(response_times)
                    avg_latency = statistics.mean(response_times)
                    
                    print(f"\n{endpoint['name']} API Performance:")
                    print(f"  Average: {avg_latency:.1f}ms")
                    print(f"  P95: {p95_latency:.1f}ms")
                    print(f"  Target P95: <{endpoint['max_p95_ms']}ms")
                    
                    assert p95_latency < endpoint["max_p95_ms"], \
                        f"API P95 latency {p95_latency:.1f}ms exceeds {endpoint['max_p95_ms']}ms for {endpoint['name']}"
    
    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self):
        """Test performance under concurrent load"""
        async with aiohttp.ClientSession() as session:
            # Test most critical endpoint under load
            test_url = self.critical_endpoints[0]["url"]  # unified-gateway
            
            async def make_request():
                start_time = time.time()
                async with session.get(test_url) as response:
                    return (time.time() - start_time) * 1000, response.status
            
            # Make 10 concurrent requests
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            response_times = []
            success_count = 0
            
            for result in results:
                if isinstance(result, tuple):
                    latency, status = result
                    response_times.append(latency)
                    if status == 200:
                        success_count += 1
                elif isinstance(result, Exception):
                    pytest.fail(f"Concurrent request failed: {result}")
            
            assert success_count >= 8, f"Only {success_count}/10 concurrent requests succeeded"
            
            if response_times:
                avg_concurrent_latency = statistics.mean(response_times)
                max_concurrent_latency = max(response_times)
                
                print(f"\nConcurrent Load Performance:")
                print(f"  Success Rate: {success_count}/10")
                print(f"  Average Latency: {avg_concurrent_latency:.1f}ms")
                print(f"  Max Latency: {max_concurrent_latency:.1f}ms")
                
                # Under concurrent load, should still be reasonable
                assert avg_concurrent_latency < 2000, \
                    f"Average concurrent latency {avg_concurrent_latency:.1f}ms too high"
                assert max_concurrent_latency < 5000, \
                    f"Max concurrent latency {max_concurrent_latency:.1f}ms too high"
    
    @pytest.mark.asyncio
    async def test_response_size_vs_latency(self):
        """Test that response size correlates appropriately with latency"""
        async with aiohttp.ClientSession() as session:
            test_cases = [
                {
                    "url": "https://chatterfix-unified-gateway-650169261019.us-central1.run.app/health",
                    "expected_size_kb": 0.5,  # Small JSON response
                    "max_latency_ms": 500
                },
                {
                    "url": "https://chatterfix-data-room-650169261019.us-central1.run.app/health",
                    "expected_size_kb": 1.0,  # Slightly larger response
                    "max_latency_ms": 800
                }
            ]
            
            for test_case in test_cases:
                try:
                    start_time = time.time()
                    async with session.get(test_case["url"]) as response:
                        latency_ms = (time.time() - start_time) * 1000
                        response_text = await response.text()
                        response_size_kb = len(response_text.encode('utf-8')) / 1024
                        
                        print(f"\nResponse Analysis for {test_case['url']}:")
                        print(f"  Latency: {latency_ms:.1f}ms")
                        print(f"  Size: {response_size_kb:.2f}KB") 
                        print(f"  Throughput: {response_size_kb / (latency_ms / 1000):.1f} KB/s")
                        
                        assert latency_ms < test_case["max_latency_ms"], \
                            f"Latency {latency_ms:.1f}ms exceeds {test_case['max_latency_ms']}ms"
                        
                        # Size should be reasonable for response type
                        size_ratio = response_size_kb / test_case["expected_size_kb"]
                        assert 0.1 < size_ratio < 10, \
                            f"Response size {response_size_kb:.2f}KB unexpected vs {test_case['expected_size_kb']}KB"
                
                except aiohttp.ClientError as e:
                    pytest.skip(f"Response size test skipped - endpoint not available: {e}")
    
    @pytest.mark.asyncio
    async def test_latency_consistency(self):
        """Test that latency is consistent across multiple requests"""
        async with aiohttp.ClientSession() as session:
            test_url = self.critical_endpoints[1]["url"]  # cmms-health
            
            response_times = []
            
            # Make 15 requests over time
            for i in range(15):
                start_time = time.time()
                
                try:
                    async with session.get(test_url) as response:
                        latency_ms = (time.time() - start_time) * 1000
                        response_times.append(latency_ms)
                        assert response.status == 200
                
                except aiohttp.ClientError as e:
                    pytest.skip(f"Consistency test skipped - endpoint not available: {e}")
                
                await asyncio.sleep(0.5)  # Spread requests over time
            
            if response_times:
                avg_latency = statistics.mean(response_times)
                std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
                min_latency = min(response_times)
                max_latency = max(response_times)
                
                print(f"\nLatency Consistency Analysis:")
                print(f"  Average: {avg_latency:.1f}ms")
                print(f"  Std Dev: {std_dev:.1f}ms")
                print(f"  Min: {min_latency:.1f}ms")
                print(f"  Max: {max_latency:.1f}ms")
                print(f"  Coefficient of Variation: {(std_dev / avg_latency) * 100:.1f}%")
                
                # Latency should be consistent (low coefficient of variation)
                cv = (std_dev / avg_latency) * 100 if avg_latency > 0 else 0
                assert cv < 100, f"Latency too inconsistent (CV: {cv:.1f}%)"  # Allow some variation
                
                # No single request should be extremely slow
                assert max_latency < avg_latency * 3, \
                    f"Max latency {max_latency:.1f}ms too high vs average {avg_latency:.1f}ms"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])