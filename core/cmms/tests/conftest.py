"""Test configuration and fixtures for ChatterFix CMMS."""

import asyncio
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Test configuration
TEST_DATABASE_URL = "sqlite:///./test_cmms.db"
TEST_OLLAMA_URL = "http://localhost:11434"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_app():
    """Create a test FastAPI application instance."""
    # Import here to avoid circular imports
    try:
        from app import app

        return app
    except ImportError:
        # Create a minimal test app if main app is not available
        from fastapi import FastAPI

        test_app = FastAPI()

        @test_app.get("/")
        async def root():
            return {"status": "test"}

        @test_app.get("/health")
        async def health():
            return {"status": "healthy"}

        return test_app


@pytest.fixture
def client(test_app):
    """Create a test client for synchronous testing."""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app):
    """Create an async test client for asynchronous testing."""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    yield db_path

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response for testing."""
    return {
        "model": "llama3.1:8b",
        "response": "This is a test response from the AI assistant.",
        "done": True,
        "context": [],
        "total_duration": 1000000000,
        "load_duration": 500000000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 200000000,
        "eval_count": 20,
        "eval_duration": 300000000,
    }


@pytest.fixture
def sample_work_order():
    """Sample work order data for testing."""
    return {
        "id": "WO-TEST-001",
        "title": "Test Maintenance Task",
        "description": "This is a test work order for unit testing",
        "priority": "medium",
        "status": "open",
        "asset_id": "AST-TEST-001",
        "assigned_to": "test-technician",
        "created_at": "2024-01-01T10:00:00Z",
        "estimated_hours": 2.5,
    }


@pytest.fixture
def sample_asset():
    """Sample asset data for testing."""
    return {
        "id": "AST-TEST-001",
        "name": "Test Equipment",
        "description": "Test equipment for unit testing",
        "location": "Test Lab",
        "status": "operational",
        "manufacturer": "Test Corp",
        "model": "TEST-2024",
        "serial_number": "TEST123456",
        "installation_date": "2024-01-01",
        "last_maintenance": "2024-06-01",
    }


@pytest.fixture
def sample_inventory_item():
    """Sample inventory item for testing."""
    return {
        "id": "INV-TEST-001",
        "name": "Test Part",
        "description": "Test part for unit testing",
        "part_number": "TEST-PART-001",
        "quantity": 50,
        "unit_cost": 25.99,
        "supplier": "Test Supplier",
        "location": "Warehouse A",
        "reorder_level": 10,
        "reorder_quantity": 25,
    }


@pytest.fixture
def admin_user():
    """Sample admin user for testing."""
    return {
        "id": "user-admin-001",
        "username": "admin",
        "email": "admin@chatterfix.com",
        "role": "admin",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def technician_user():
    """Sample technician user for testing."""
    return {
        "id": "user-tech-001",
        "username": "technician",
        "email": "tech@chatterfix.com",
        "role": "technician",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def api_headers():
    """Standard API headers for testing."""
    return {"Content-Type": "application/json", "Accept": "application/json"}


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield

    # Cleanup any test files that might have been created
    test_files = ["test_cmms.db", "test_upload.txt", "test_image.jpg"]

    for file in test_files:
        if os.path.exists(file):
            try:
                os.unlink(file)
            except PermissionError:
                pass  # File might be in use


# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests."""
    return {
        "max_response_time": 2.0,  # seconds
        "max_memory_usage": 100,  # MB
        "concurrent_users": 10,
        "test_duration": 30,  # seconds
    }


# Security testing fixtures
@pytest.fixture
def security_payloads():
    """Common security test payloads."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; SELECT * FROM users",
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
        ],
    }


# Mock external services
@pytest.fixture
def mock_external_services(monkeypatch):
    """Mock external service calls for testing."""

    def mock_ollama_request(*args, **kwargs):
        return {
            "status_code": 200,
            "json": lambda: {"response": "Mocked AI response", "done": True},
        }

    def mock_email_send(*args, **kwargs):
        return True

    def mock_sms_send(*args, **kwargs):
        return True

    # Apply mocks
    monkeypatch.setattr("requests.post", mock_ollama_request)
    monkeypatch.setattr("requests.get", mock_ollama_request)

    return {
        "ollama": mock_ollama_request,
        "email": mock_email_send,
        "sms": mock_sms_send,
    }
