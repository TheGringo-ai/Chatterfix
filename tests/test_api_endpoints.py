"""
Comprehensive test suite for ChatterFix CMMS API endpoints
Tests authentication, functionality, and data integrity
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
import os
import json

# Configuration
API_KEY = os.getenv("CHATTERFIX_API_KEY", "chatterfix_secure_api_key_2025_cmms_prod_v1")
BASE_URL = os.getenv("BACKEND_URL", "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app")

class TestAPIEndpoints:
    """Test suite for all CMMS API endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Provide authentication headers for requests"""
        return {"x-api-key": API_KEY}
    
    @pytest.fixture
    def invalid_headers(self):
        """Provide invalid authentication headers for negative testing"""
        return {"x-api-key": "invalid_key"}
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for API testing"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    # Health Check Tests
    async def test_health_endpoint_requires_auth(self, client):
        """Test that health endpoint requires authentication"""
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 422  # Missing API key
    
    async def test_health_endpoint_rejects_invalid_auth(self, client, invalid_headers):
        """Test that health endpoint rejects invalid API keys"""
        response = await client.get(f"{BASE_URL}/health", headers=invalid_headers)
        assert response.status_code == 401
    
    async def test_health_endpoint_success(self, client, auth_headers):
        """Test that health endpoint returns healthy status with valid auth"""
        response = await client.get(f"{BASE_URL}/health", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "consolidated_cmms"
        assert "modules" in data
        assert "work_orders" in data["modules"]
        assert "assets" in data["modules"]
        assert "parts" in data["modules"]

    # Work Orders Tests
    async def test_work_orders_list(self, client, auth_headers):
        """Test work orders list endpoint returns data"""
        response = await client.get(f"{BASE_URL}/work_orders/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "work_orders" in data
        assert isinstance(data["work_orders"], list)
        assert len(data["work_orders"]) > 0
        assert "total" in data
        assert data["total"] > 0
    
    async def test_work_orders_data_structure(self, client, auth_headers):
        """Test work orders have correct data structure"""
        response = await client.get(f"{BASE_URL}/work_orders/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        work_order = data["work_orders"][0]
        
        # Required fields
        required_fields = ["id", "title", "description", "status", "priority", "created_at"]
        for field in required_fields:
            assert field in work_order
        
        # Valid status values
        valid_statuses = ["Open", "In Progress", "On Hold", "Completed", "Cancelled"]
        assert work_order["status"] in valid_statuses
        
        # Valid priority values
        valid_priorities = ["Low", "Medium", "High", "Critical"]
        assert work_order["priority"] in valid_priorities
    
    async def test_work_orders_stats(self, client, auth_headers):
        """Test work orders statistics endpoint"""
        response = await client.get(f"{BASE_URL}/work_orders/stats/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_work_orders" in data
        assert "by_status" in data
        assert "by_priority" in data
        assert "completion_rate" in data
        assert data["total_work_orders"] > 0

    # Assets Tests
    async def test_assets_list(self, client, auth_headers):
        """Test assets list endpoint returns data"""
        response = await client.get(f"{BASE_URL}/assets/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "assets" in data
        assert isinstance(data["assets"], list)
        assert len(data["assets"]) > 0
        assert "total" in data
        assert data["total"] > 0
    
    async def test_assets_data_structure(self, client, auth_headers):
        """Test assets have correct data structure"""
        response = await client.get(f"{BASE_URL}/assets/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        asset = data["assets"][0]
        
        # Required fields
        required_fields = ["id", "name", "asset_type", "status", "created_at"]
        for field in required_fields:
            assert field in asset
        
        # Valid asset types
        valid_types = ["HVAC", "Safety", "Production", "Elevator", "Lighting", "Power", "Structure", "Plumbing"]
        assert asset["asset_type"] in valid_types
    
    async def test_assets_stats(self, client, auth_headers):
        """Test assets statistics endpoint"""
        response = await client.get(f"{BASE_URL}/assets/stats/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_assets" in data
        assert "by_type" in data
        assert "by_condition" in data
        assert data["total_assets"] > 0

    # Parts Tests
    async def test_parts_list(self, client, auth_headers):
        """Test parts list endpoint returns data"""
        response = await client.get(f"{BASE_URL}/parts/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "parts" in data
        assert isinstance(data["parts"], list)
        assert len(data["parts"]) > 0
        assert "total" in data
        assert data["total"] > 0
    
    async def test_parts_data_structure(self, client, auth_headers):
        """Test parts have correct data structure"""
        response = await client.get(f"{BASE_URL}/parts/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        part = data["parts"][0]
        
        # Required fields
        required_fields = ["id", "name", "category", "current_stock", "min_stock", "unit_cost"]
        for field in required_fields:
            assert field in part
        
        # Validate stock levels
        assert part["current_stock"] >= 0
        assert part["min_stock"] >= 0
        assert part["unit_cost"] >= 0
    
    async def test_parts_stats(self, client, auth_headers):
        """Test parts statistics endpoint"""
        response = await client.get(f"{BASE_URL}/parts/stats/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_parts" in data
        assert "by_category" in data
        assert "low_stock_count" in data
        assert data["total_parts"] > 0

    # Authentication Tests
    async def test_authentication_missing_key(self, client):
        """Test that endpoints reject requests without API key"""
        endpoints = ["/work_orders/", "/assets/", "/parts/"]
        
        for endpoint in endpoints:
            response = await client.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 422  # Missing required field
    
    async def test_authentication_invalid_key(self, client, invalid_headers):
        """Test that endpoints reject requests with invalid API key"""
        endpoints = ["/work_orders/", "/assets/", "/parts/"]
        
        for endpoint in endpoints:
            response = await client.get(f"{BASE_URL}{endpoint}", headers=invalid_headers)
            assert response.status_code == 401  # Unauthorized

    # Rate Limiting Tests
    async def test_rate_limiting(self, client, auth_headers):
        """Test that rate limiting is enforced"""
        # Make rapid requests to trigger rate limiting
        responses = []
        
        for i in range(25):
            response = await client.get(f"{BASE_URL}/health", headers=auth_headers)
            responses.append(response.status_code)
        
        # Should see some 429 responses after hitting the limit
        rate_limited_count = responses.count(429)
        assert rate_limited_count > 0, "Rate limiting should be triggered"

    # Performance Tests
    async def test_response_times(self, client, auth_headers):
        """Test that API responses are within acceptable time limits"""
        import time
        
        endpoints = ["/health", "/work_orders/", "/assets/", "/parts/"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await client.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < 5.0, f"{endpoint} took {response_time:.2f}s (too slow)"

    # Data Consistency Tests
    async def test_data_consistency(self, client, auth_headers):
        """Test that data is consistent across related endpoints"""
        # Get work orders count from list endpoint
        wo_response = await client.get(f"{BASE_URL}/work_orders/", headers=auth_headers)
        wo_data = wo_response.json()
        wo_count_from_list = len(wo_data["work_orders"])
        
        # Get work orders count from stats endpoint
        stats_response = await client.get(f"{BASE_URL}/work_orders/stats/summary", headers=auth_headers)
        stats_data = stats_response.json()
        wo_count_from_stats = stats_data["total_work_orders"]
        
        # Counts should match
        assert wo_count_from_list == wo_count_from_stats, "Work order counts don't match between endpoints"

    # CRUD Operations Tests
    async def test_work_order_creation(self, client, auth_headers):
        """Test creating a new work order"""
        new_work_order = {
            "title": "Test Work Order",
            "description": "This is a test work order created by the test suite",
            "priority": "Medium",
            "assigned_to": "Test User",
            "estimated_hours": 2.0
        }
        
        response = await client.post(
            f"{BASE_URL}/work_orders/",
            headers=auth_headers,
            json=new_work_order
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "work_order" in data
        
        created_wo = data["work_order"]
        assert created_wo["title"] == new_work_order["title"]
        assert created_wo["description"] == new_work_order["description"]
        assert created_wo["priority"] == new_work_order["priority"]

# Integration Tests
class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def auth_headers(self):
        return {"x-api-key": API_KEY}
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    async def test_full_workflow(self, client, auth_headers):
        """Test a complete CMMS workflow"""
        # 1. Check system health
        health_response = await client.get(f"{BASE_URL}/health", headers=auth_headers)
        assert health_response.status_code == 200
        
        # 2. List work orders
        wo_response = await client.get(f"{BASE_URL}/work_orders/", headers=auth_headers)
        assert wo_response.status_code == 200
        
        # 3. List assets
        assets_response = await client.get(f"{BASE_URL}/assets/", headers=auth_headers)
        assert assets_response.status_code == 200
        
        # 4. List parts
        parts_response = await client.get(f"{BASE_URL}/parts/", headers=auth_headers)
        assert parts_response.status_code == 200
        
        # 5. Get statistics
        stats_response = await client.get(f"{BASE_URL}/work_orders/stats/summary", headers=auth_headers)
        assert stats_response.status_code == 200
        
        # All operations should succeed
        assert all(r.status_code == 200 for r in [
            health_response, wo_response, assets_response, parts_response, stats_response
        ])

if __name__ == "__main__":
    # Run tests directly if script is executed
    pytest.main([__file__, "-v"])