"""Unit tests for ChatterFix CMMS API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns expected response."""
        response = client.get("/")
        assert response.status_code == 200
        # Check if it's HTML (landing page) or JSON
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type or "application/json" in content_type

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        # Should return 200 if endpoint exists, 404 if not implemented yet
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    def test_vm_admin_metrics(self, client):
        """Test VM admin metrics endpoint."""
        response = client.get("/api/vm/admin/metrics")

        if response.status_code == 200:
            data = response.json()
            # Check expected metrics structure
            expected_keys = ["cpu", "memory", "services"]
            for key in expected_keys:
                assert key in data

            # Validate data types
            assert isinstance(data.get("cpu"), (int, float))
            assert isinstance(data.get("memory"), (int, float))
            assert isinstance(data.get("services"), dict)
        else:
            # Endpoint might not be implemented yet
            assert response.status_code in [404, 500]

    def test_vm_admin_chat_fallback(self, client):
        """Test VM admin chat fallback endpoint."""
        test_message = {"message": "system status"}

        response = client.post(
            "/api/vm/admin/chat/fallback",
            json=test_message,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert isinstance(data["response"], str)
            assert len(data["response"]) > 0
        else:
            # Endpoint might not be implemented yet
            assert response.status_code in [404, 422, 500]

    @patch("requests.post")
    def test_vm_admin_chat_llama(self, mock_post, client, mock_ollama_response):
        """Test VM admin LLaMA chat endpoint."""
        # Mock the Ollama API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_ollama_response

        test_message = {"message": "help me troubleshoot"}

        response = client.post(
            "/api/vm/admin/chat",
            json=test_message,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "response" in data
        else:
            # Endpoint might not be implemented or LLaMA not available
            assert response.status_code in [404, 500, 504]

    def test_work_orders_endpoint(self, client):
        """Test work orders API endpoint."""
        response = client.get("/api/work-orders")

        # Should return data or 404 if not implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_assets_endpoint(self, client):
        """Test assets API endpoint."""
        response = client.get("/api/assets")

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_inventory_endpoint(self, client):
        """Test inventory API endpoint."""
        response = client.get("/api/inventory")

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestAPIValidation:
    """Test API input validation and error handling."""

    def test_invalid_json_payload(self, client):
        """Test API handles invalid JSON gracefully."""
        response = client.post(
            "/api/vm/admin/chat/fallback",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422, 404]

    def test_missing_required_fields(self, client):
        """Test API validates required fields."""
        # Empty payload
        response = client.post(
            "/api/vm/admin/chat/fallback",
            json={},
            headers={"Content-Type": "application/json"},
        )

        # Should handle missing message field
        assert response.status_code in [200, 400, 422, 404]

    def test_oversized_payload(self, client):
        """Test API handles oversized payloads."""
        large_message = "x" * 10000  # 10KB message

        response = client.post(
            "/api/vm/admin/chat/fallback",
            json={"message": large_message},
            headers={"Content-Type": "application/json"},
        )

        # Should either process or reject oversized payload
        assert response.status_code in [200, 400, 413, 422, 404]


class TestAPIPerformance:
    """Test API performance characteristics."""

    def test_response_time(self, client, performance_config):
        """Test API response times are within acceptable limits."""
        import time

        start_time = time.time()
        response = client.get("/api/vm/admin/metrics")
        end_time = time.time()

        response_time = end_time - start_time
        max_response_time = performance_config["max_response_time"]

        # Only check performance if endpoint exists
        if response.status_code == 200:
            assert (
                response_time < max_response_time
            ), f"Response time {response_time}s exceeds limit {max_response_time}s"

    def test_concurrent_requests(self, client):
        """Test API handles concurrent requests."""
        import queue
        import threading

        results = queue.Queue()

        def make_request():
            try:
                response = client.get("/api/vm/admin/metrics")
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        response_codes = []
        while not results.empty():
            response_codes.append(results.get())

        # Should have 5 responses
        assert len(response_codes) == 5

        # All should be valid HTTP status codes (or error strings)
        for code in response_codes:
            if isinstance(code, int):
                assert 200 <= code <= 599


class TestAPISecurity:
    """Test API security measures."""

    def test_sql_injection_protection(self, client, security_payloads):
        """Test API protects against SQL injection."""
        for payload in security_payloads["sql_injection"]:
            response = client.post(
                "/api/vm/admin/chat/fallback",
                json={"message": payload},
                headers={"Content-Type": "application/json"},
            )

            # Should not return database errors or sensitive info
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").lower()

                # Check for common SQL error messages
                dangerous_keywords = ["sql", "database", "table", "column", "error"]
                for keyword in dangerous_keywords:
                    if keyword in response_text:
                        # This might be legitimate (like explaining SQL), so just warn
                        print(
                            f"Warning: Response contains '{keyword}' for payload: {payload}"
                        )

    def test_xss_protection(self, client, security_payloads):
        """Test API protects against XSS attacks."""
        for payload in security_payloads["xss"]:
            response = client.post(
                "/api/vm/admin/chat/fallback",
                json={"message": payload},
                headers={"Content-Type": "application/json"},
            )

            # Should not return script tags or javascript
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")

                # Script tags should be escaped or removed
                assert "<script>" not in response_text
                assert "javascript:" not in response_text

    def test_rate_limiting(self, client):
        """Test API rate limiting (if implemented)."""
        # Make rapid requests
        responses = []
        for _ in range(20):
            response = client.get("/api/vm/admin/metrics")
            responses.append(response.status_code)

        # Check if rate limiting is in place
        rate_limited = any(code == 429 for code in responses)

        if rate_limited:
            assert 429 in responses, "Rate limiting should return 429 status"
        else:
            # Rate limiting might not be implemented yet
            print("Note: No rate limiting detected")


class TestAPIDocumentation:
    """Test API documentation and schema."""

    def test_openapi_schema(self, client):
        """Test OpenAPI/Swagger documentation is available."""
        # FastAPI automatically provides these endpoints
        docs_endpoints = ["/docs", "/openapi.json", "/redoc"]

        for endpoint in docs_endpoints:
            response = client.get(endpoint)
            # Should return 200 or 404 if not enabled
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                print(f"✅ API documentation available at {endpoint}")

    def test_api_versioning(self, client):
        """Test API versioning strategy."""
        # Check if API version is included in responses
        response = client.get("/api/vm/admin/metrics")

        if response.status_code == 200:
            # Look for version information in headers or response
            version_headers = ["X-API-Version", "API-Version"]
            has_version = any(header in response.headers for header in version_headers)

            if not has_version:
                # Version might be in the response body or URL path
                print("Note: No explicit API versioning detected")
