# ChatterFix CMMS Test Suite

## Overview
Comprehensive unit tests for the ChatterFix Enterprise CMMS API.

## Running Tests

### Run all tests
```bash
cd /path/to/core/cmms
python3 -m pytest tests/ -v
```

### Run specific test file
```bash
python3 -m pytest tests/test_api.py -v
```

### Run specific test class
```bash
python3 -m pytest tests/test_api.py::TestHealthEndpoints -v
```

### Run specific test
```bash
python3 -m pytest tests/test_api.py::TestHealthEndpoints::test_health_endpoint -v
```

### Run with coverage
```bash
pip install pytest-cov
python3 -m pytest tests/ --cov=. --cov-report=html
```

## Test Coverage

### Current Test Suites
- **TestHealthEndpoints**: Health, readiness, and metrics endpoints
- **TestSecurityMiddleware**: Security headers and rate limiting
- **TestAIEndpoints**: AI dashboard and insights
- **TestWorkOrderEndpoints**: Work order management
- **TestVoiceCommandEndpoint**: Voice command processing with validation
- **TestSmartScanEndpoint**: Smart part scanning
- **TestDatabaseConnection**: Database context manager
- **TestConfiguration**: Configuration validation
- **TestUtilityFunctions**: String sanitization and UUID validation

### Test Statistics
- **Total Tests**: 18
- **Pass Rate**: 100%
- **Coverage**: Core API endpoints and utilities

## Test Database
Tests use a separate `test_chatterfix.db` database which is created at the start of tests and cleaned up afterward.

## Dependencies
- pytest==7.4.3
- pytest-asyncio==0.21.1
- fastapi
- httpx (for TestClient)

## Adding New Tests
1. Create test class in `test_api.py` or new test file
2. Use the `client` fixture for API testing
3. Follow existing test patterns for consistency
4. Run tests to ensure they pass

## CI/CD Integration
These tests are automatically run in the GitHub Actions CI/CD pipeline on every push and pull request.
