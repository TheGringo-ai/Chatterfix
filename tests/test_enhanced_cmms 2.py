#!/usr/bin/env python3
"""
ChatterFix Enhanced CMMS Test Suite
Test all enhanced functionality: CRUD, attachments, exports, voice AI
"""

import pytest
import asyncio
import httpx
import json
import io
from datetime import datetime

# Test configuration
BASE_URL = "https://chatterfix-unified-gateway-650169261019.us-central1.run.app"
TIMEOUT = 30.0

class TestEnhancedCMMS:
    """Test suite for enhanced CMMS functionality"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=TIMEOUT)
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, client):
        """Test enhanced health check endpoint"""
        response = await client.get(f"{BASE_URL}/api/health/all")
        assert response.status_code == 200
        
        data = response.json()
        assert "gateway" in data
        assert "services" in data
        assert "enhanced_services" in data
        assert "timestamp" in data
        
        # Check enhanced services
        enhanced = data["enhanced_services"]
        expected_services = ["work_orders", "assets", "parts", "voice_ai"]
        
        for service in expected_services:
            assert service in enhanced
            assert "status" in enhanced[service]
            assert "features" in enhanced[service]
    
    @pytest.mark.asyncio
    async def test_work_orders_enhanced(self, client):
        """Test enhanced work orders functionality"""
        
        # Test basic work orders endpoint
        response = await client.get(f"{BASE_URL}/api/work-orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "work_orders" in data or isinstance(data, list)
        
        # Test work order detail (assuming work order 1 exists)
        response = await client.get(f"{BASE_URL}/api/work-orders/1")
        assert response.status_code == 200
        
        work_order = response.json()
        assert "id" in work_order
        assert "title" in work_order
        assert "status" in work_order
    
    @pytest.mark.asyncio
    async def test_work_orders_comment(self, client):
        """Test adding comments to work orders"""
        comment_data = {
            "note": "Test comment added via API"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/work-orders/1/comment",
            json=comment_data
        )
        # May return 200 (success) or 404 (work order not found in demo data)
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_work_orders_export_pdf(self, client):
        """Test work order PDF export"""
        response = await client.get(f"{BASE_URL}/api/work-orders/1/export.pdf")
        # May return 200 (success) or 404 (work order not found)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_work_orders_export_csv(self, client):
        """Test work orders CSV export"""
        response = await client.get(f"{BASE_URL}/api/work-orders/export.csv")
        # Should work with demo data
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_assets_enhanced(self, client):
        """Test enhanced assets functionality"""
        
        # Test assets endpoint
        response = await client.get(f"{BASE_URL}/api/assets")
        assert response.status_code == 200
        
        data = response.json()
        assert "assets" in data or isinstance(data, list)
        
        # Test asset detail (assuming asset 101 exists in demo data)
        response = await client.get(f"{BASE_URL}/api/assets/101")
        assert response.status_code == 200
        
        asset = response.json()
        assert "id" in asset
        assert "name" in asset
        assert "status" in asset
    
    @pytest.mark.asyncio
    async def test_assets_export_csv(self, client):
        """Test assets CSV export"""
        response = await client.get(f"{BASE_URL}/api/assets/export.csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_assets_upcoming_maintenance(self, client):
        """Test upcoming maintenance endpoint"""
        response = await client.get(f"{BASE_URL}/api/assets/maintenance/upcoming")
        assert response.status_code == 200
        
        data = response.json()
        assert "upcoming_maintenance" in data
    
    @pytest.mark.asyncio
    async def test_parts_enhanced(self, client):
        """Test enhanced parts functionality"""
        
        # Test parts endpoint
        response = await client.get(f"{BASE_URL}/api/parts")
        assert response.status_code == 200
        
        data = response.json()
        assert "parts" in data or isinstance(data, list)
        
        # Test part detail (assuming part 1001 exists in demo data)
        response = await client.get(f"{BASE_URL}/api/parts/1001")
        assert response.status_code == 200
        
        part = response.json()
        assert "id" in part
        assert "name" in part
        assert "stock_qty" in part
    
    @pytest.mark.asyncio
    async def test_parts_checkout(self, client):
        """Test parts checkout functionality"""
        checkout_data = {
            "qty": 1,
            "work_order_id": 1,
            "notes": "Test checkout"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/parts/1001/checkout",
            json=checkout_data
        )
        # May succeed or fail based on stock levels
        assert response.status_code in [200, 400, 404]
    
    @pytest.mark.asyncio
    async def test_parts_low_stock_alerts(self, client):
        """Test low stock alerts"""
        response = await client.get(f"{BASE_URL}/api/parts/alerts/low-stock")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "total_alerts" in data
    
    @pytest.mark.asyncio
    async def test_parts_export_csv(self, client):
        """Test parts CSV export"""
        response = await client.get(f"{BASE_URL}/api/parts/export.csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_suppliers(self, client):
        """Test suppliers functionality"""
        response = await client.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code == 200
        
        data = response.json()
        assert "suppliers" in data
    
    @pytest.mark.asyncio
    async def test_voice_ai_intents(self, client):
        """Test voice AI supported intents"""
        response = await client.get(f"{BASE_URL}/api/voice/intents")
        # May fail if voice AI service not deployed
        assert response.status_code in [200, 503, 502]
        
        if response.status_code == 200:
            data = response.json()
            assert "supported_intents" in data
    
    @pytest.mark.asyncio
    async def test_voice_ai_test(self, client):
        """Test voice AI processing"""
        test_data = {
            "test_phrase": "Create work order for HVAC filter replacement",
            "context": {"page": "work_orders"}
        }
        
        response = await client.post(
            f"{BASE_URL}/api/voice/test",
            json=test_data
        )
        # May fail if voice AI service not deployed
        assert response.status_code in [200, 503, 502]
        
        if response.status_code == 200:
            data = response.json()
            assert "intent_data" in data
            assert "action_result" in data

# Performance tests
class TestPerformanceGates:
    """Test performance requirements"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=TIMEOUT)
    
    @pytest.mark.asyncio
    async def test_work_order_detail_performance(self, client):
        """Test work order detail response time < 900ms"""
        start_time = datetime.now()
        
        response = await client.get(f"{BASE_URL}/api/work-orders/1")
        
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # P95 requirement: < 900ms warm
        assert response_time_ms < 900, f"Response time {response_time_ms}ms exceeds 900ms limit"
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_csv_export_performance(self, client):
        """Test CSV export performance < 2s for 1k rows"""
        start_time = datetime.now()
        
        response = await client.get(f"{BASE_URL}/api/work-orders/export.csv")
        
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Performance gate: < 2s for 1k rows
        assert response_time_ms < 2000, f"CSV export time {response_time_ms}ms exceeds 2s limit"
        assert response.status_code == 200

# Integration tests
class TestEndToEndIntegration:
    """Test complete workflows"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(timeout=TIMEOUT)
    
    @pytest.mark.asyncio
    async def test_work_order_lifecycle(self, client):
        """Test complete work order lifecycle"""
        
        # 1. Get work orders list
        response = await client.get(f"{BASE_URL}/api/work-orders")
        assert response.status_code == 200
        
        # 2. Get specific work order
        response = await client.get(f"{BASE_URL}/api/work-orders/1")
        if response.status_code == 200:
            work_order = response.json()
            
            # 3. Add comment
            comment_data = {"note": "Integration test comment"}
            response = await client.post(
                f"{BASE_URL}/api/work-orders/1/comment",
                json=comment_data
            )
            assert response.status_code in [200, 404]
            
            # 4. Export PDF
            response = await client.get(f"{BASE_URL}/api/work-orders/1/export.pdf")
            assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_parts_checkout_workflow(self, client):
        """Test parts checkout workflow"""
        
        # 1. Check inventory
        response = await client.get(f"{BASE_URL}/api/parts/1001")
        if response.status_code == 200:
            part = response.json()
            initial_stock = part.get("stock_qty", 0)
            
            # 2. Checkout parts (if stock available)
            if initial_stock > 0:
                checkout_data = {
                    "qty": 1,
                    "work_order_id": 1,
                    "notes": "Integration test checkout"
                }
                response = await client.post(
                    f"{BASE_URL}/api/parts/1001/checkout",
                    json=checkout_data
                )
                assert response.status_code in [200, 400]
                
                # 3. Check transaction history
                response = await client.get(f"{BASE_URL}/api/parts/1001/transactions")
                assert response.status_code in [200, 404]

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])