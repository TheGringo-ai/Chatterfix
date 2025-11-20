"""
Unit tests for ChatterFix CMMS API endpoints
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from chatterfix_enterprise_v3_ai_powerhouse import app, init_database, DatabaseConnection, config, sanitize_string, validate_uuid

# Use test database
TEST_DB = "test_chatterfix.db"
config.DATABASE_FILE = TEST_DB
os.environ["DATABASE_FILE"] = TEST_DB


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    # Initialize test database
    init_database()
    client = TestClient(app)
    yield client
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["version"] == "3.0.0"
        assert data["service"] == "ChatterFix Enterprise AI Powerhouse"
        assert "database" in data
        assert "timestamp" in data
    
    def test_ready_endpoint(self, client):
        """Test /ready endpoint returns 200"""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "message" in data
    
    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        content = response.text
        assert "chatterfix_work_orders_total" in content
        assert "chatterfix_assets_total" in content
        assert "# HELP" in content


class TestSecurityMiddleware:
    """Test security headers and rate limiting"""
    
    def test_security_headers(self, client):
        """Test security headers are present"""
        response = client.get("/health")
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"
        assert "strict-transport-security" in response.headers
    
    def test_rate_limiting_headers(self, client):
        """Test rate limit headers are present"""
        response = client.get("/api/work-orders")
        assert "x-ratelimit-limit" in response.headers
        assert response.headers["x-ratelimit-limit"] == "60"


class TestAIEndpoints:
    """Test AI-powered endpoints"""
    
    def test_ai_dashboard(self, client):
        """Test /api/ai/dashboard endpoint"""
        response = client.get("/api/ai/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "ai_status" in data
        assert data["ai_status"] == "fully_operational"
        assert "total_assets" in data
        assert "ai_efficiency_score" in data
    
    def test_ai_insights(self, client):
        """Test /api/ai/insights endpoint"""
        response = client.get("/api/ai/insights")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert isinstance(data["insights"], list)


class TestWorkOrderEndpoints:
    """Test work order endpoints"""
    
    def test_get_work_orders(self, client):
        """Test /api/work-orders endpoint"""
        response = client.get("/api/work-orders")
        assert response.status_code == 200
        data = response.json()
        assert "work_orders" in data
        assert "total" in data
        assert isinstance(data["work_orders"], list)


class TestVoiceCommandEndpoint:
    """Test voice command processing"""
    
    def test_voice_command_validation(self, client):
        """Test voice command with invalid data"""
        # Test missing required fields
        response = client.post("/api/voice/command", json={})
        assert response.status_code == 422  # Validation error
    
    def test_voice_command_valid_request(self, client):
        """Test voice command with valid data"""
        request_data = {
            "audio_data": "base64_encoded_audio_data",
            "technician_id": "tech-001",
            "location": "Building A",
            "priority": "high"
        }
        response = client.post("/api/voice/command", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "work_order_id" in data


class TestSmartScanEndpoint:
    """Test smart part scanning"""
    
    def test_smart_scan_validation(self, client):
        """Test smart scan with invalid data"""
        response = client.post("/api/smart-scan/part", json={})
        assert response.status_code == 422  # Validation error
    
    def test_smart_scan_valid_request(self, client):
        """Test smart scan with valid data"""
        request_data = {
            "image_data": "base64_encoded_image_data",
            "context": "part_identification",
            "confidence_threshold": 0.9
        }
        response = client.post("/api/smart-scan/part", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "detected_parts" in data


class TestDatabaseConnection:
    """Test database connection context manager"""
    
    def test_database_context_manager(self):
        """Test DatabaseConnection context manager"""
        with DatabaseConnection(TEST_DB) as (conn, cursor):
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_database_rollback_on_error(self):
        """Test database rollback on error"""
        try:
            with DatabaseConnection(TEST_DB) as (conn, cursor):
                cursor.execute("SELECT 1")
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected
        
        # Verify database is still functional
        with DatabaseConnection(TEST_DB) as (conn, cursor):
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1


class TestConfiguration:
    """Test configuration validation"""
    
    def test_config_initialization(self):
        """Test configuration loads correctly"""
        assert config.PORT == 8080
        assert config.HOST == "0.0.0.0"
        assert config.ENV == "development"
        assert config.DATABASE_FILE is not None
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Port should be valid
        assert 1 <= config.PORT <= 65535
        # Environment should be set
        assert config.ENV in ["development", "staging", "production"]


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        # Test normal string
        assert sanitize_string("Hello World") == "Hello World"
        
        # Test string with control characters
        assert sanitize_string("Hello\x00World") == "HelloWorld"
        assert sanitize_string("Hello\nWorld") == "Hello World"
        
        # Test max length
        long_string = "a" * 2000
        assert len(sanitize_string(long_string, max_length=100)) == 100
        
        # Test empty string
        assert sanitize_string("") == ""
        assert sanitize_string("   ") == ""
    
    def test_validate_uuid(self):
        """Test UUID validation"""
        # Valid UUID
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        
        # Invalid UUIDs
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("") is False
        assert validate_uuid("123") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
