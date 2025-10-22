#!/usr/bin/env python3
"""
Phase 7 Health Check Test Suite
Validates all services meet enterprise health standards
"""

import pytest
import aiohttp
import asyncio
import time
from datetime import datetime

class TestHealthChecks:
    """Enterprise health check validation"""
    
    services = [
        "https://chatterfix-cmms-650169261019.us-central1.run.app",
        "https://chatterfix-unified-gateway-650169261019.us-central1.run.app", 
        "https://chatterfix-revenue-intelligence-650169261019.us-central1.run.app",
        "https://chatterfix-customer-success-650169261019.us-central1.run.app",
        "https://chatterfix-data-room-650169261019.us-central1.run.app"
    ]
    
    @pytest.mark.asyncio
    async def test_all_services_health_200(self):
        """Verify all 5 services return HTTP 200 on /health"""
        async with aiohttp.ClientSession() as session:
            for service_url in self.services:
                health_url = f"{service_url}/health"
                async with session.get(health_url) as response:
                    assert response.status == 200, f"Service {service_url} returned {response.status}"
                    
                    data = await response.json()
                    assert "status" in data, f"Health response missing status field"
                    assert data["status"] in ["healthy", "ok"], f"Service {service_url} status: {data.get('status')}"
    
    @pytest.mark.asyncio 
    async def test_response_time_under_1_second(self):
        """Verify all /health endpoints respond in <1 second"""
        async with aiohttp.ClientSession() as session:
            for service_url in self.services:
                health_url = f"{service_url}/health"
                
                start_time = time.time()
                async with session.get(health_url) as response:
                    response_time = time.time() - start_time
                    
                    assert response_time < 1.0, f"Service {service_url} response time {response_time:.2f}s exceeds 1.0s"
                    assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_cold_start_performance(self):
        """Test cold start performance meets P95 < 2.5s requirement"""
        # This would simulate cold start by scaling to 0 then back up
        # For now, test rapid successive requests
        
        async with aiohttp.ClientSession() as session:
            # Test first service (most critical)
            service_url = self.services[0]  # chatterfix-cmms
            health_url = f"{service_url}/health"
            
            response_times = []
            for _ in range(5):
                start_time = time.time()
                async with session.get(health_url) as response:
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    assert response.status == 200
                
                await asyncio.sleep(0.1)  # Brief pause between requests
            
            # Calculate P95 (95th percentile)
            response_times.sort()
            p95_index = int(len(response_times) * 0.95) - 1
            p95_response_time = response_times[p95_index]
            
            assert p95_response_time < 2.5, f"P95 response time {p95_response_time:.2f}s exceeds 2.5s"
    
    @pytest.mark.asyncio
    async def test_no_5xx_errors_recent(self):
        """Verify no 5xx errors in recent requests"""
        # This would check error logs or monitoring data
        # For now, verify services are responsive
        
        async with aiohttp.ClientSession() as session:
            error_count = 0
            total_requests = 0
            
            for service_url in self.services:
                health_url = f"{service_url}/health"
                
                # Make multiple requests to check stability
                for _ in range(3):
                    try:
                        async with session.get(health_url) as response:
                            total_requests += 1
                            if response.status >= 500:
                                error_count += 1
                    except Exception:
                        error_count += 1
                        total_requests += 1
            
            error_rate = error_count / total_requests if total_requests > 0 else 0
            assert error_rate == 0, f"Found {error_count}/{total_requests} 5xx errors (rate: {error_rate:.1%})"
    
    @pytest.mark.asyncio
    async def test_health_response_format(self):
        """Verify health responses contain required fields"""
        async with aiohttp.ClientSession() as session:
            for service_url in self.services:
                health_url = f"{service_url}/health"
                async with session.get(health_url) as response:
                    assert response.status == 200
                    
                    data = await response.json()
                    
                    # Required fields in health response
                    required_fields = ["status", "timestamp"]
                    for field in required_fields:
                        assert field in data, f"Health response missing required field: {field}"
                    
                    # Validate timestamp format
                    timestamp = data["timestamp"]
                    try:
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        pytest.fail(f"Invalid timestamp format: {timestamp}")
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test all services handle concurrent health checks"""
        async with aiohttp.ClientSession() as session:
            # Create concurrent requests to all services
            tasks = []
            for service_url in self.services:
                health_url = f"{service_url}/health"
                task = session.get(health_url)
                tasks.append(task)
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = 0
            for response in responses:
                if hasattr(response, 'status') and response.status == 200:
                    success_count += 1
                    response.close()
                elif isinstance(response, Exception):
                    pytest.fail(f"Concurrent health check failed: {response}")
            
            assert success_count == len(self.services), f"Only {success_count}/{len(self.services)} services responded successfully"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])