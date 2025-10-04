# 🧪 Chatterfix CMMS - Testing Quick Reference Guide

## Quick Start

### Run All Unit Tests
```bash
cd core/cmms
pytest tests/unit/ -v
```

### Run Comprehensive E2E Test Suite
```bash
cd core/cmms
python3 comprehensive_e2e_test.py
```

### Run Specific Test Class
```bash
cd core/cmms
pytest tests/unit/test_api_endpoints.py::TestAPIEndpoints -v
```

### Run with Coverage Report
```bash
cd core/cmms
pytest tests/unit/ --cov=. --cov-report=html
```

## Test Categories

### 1. Unit Tests (18 tests)
**Location:** `core/cmms/tests/unit/test_api_endpoints.py`

**What they test:**
- API endpoint responses
- Request validation
- Security features
- Performance characteristics
- API documentation

**Expected:** All tests should PASS (100% success rate)

### 2. Integration Tests
**Location:** `core/cmms/test_parts_complete.py`

**What they test:**
- Complete parts management workflow
- Create, read, update, delete operations
- UI functionality
- Error handling

**Requirements:** Requires running server at `http://localhost:8000`

**To run:**
```bash
# Terminal 1: Start server
cd core/cmms
python3 app.py

# Terminal 2: Run tests
python3 test_parts_complete.py
```

### 3. Performance Tests
**Location:** `core/cmms/tests/performance/locustfile.py`

**What they test:**
- Load capacity
- Concurrent user handling
- Response time under load
- System stability

**To run:**
```bash
cd core/cmms/tests/performance
locust -f locustfile.py --host http://localhost:8000
```

Or headless mode:
```bash
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 300s --host http://localhost:8000
```

### 4. Deployment Verification
**Location:** `test-deployment.sh`

**What it tests:**
- Production endpoint availability
- HTTPS functionality
- Core feature accessibility
- AI feature deployment

**To run:**
```bash
./test-deployment.sh
```

## Test Results

All test runs generate reports:

### E2E Test Suite Reports
- **Markdown:** `e2e_test_report_YYYYMMDD_HHMMSS.md`
- **JSON:** `e2e_test_results_YYYYMMDD_HHMMSS.json`

### Integration Test Reports
- Located in `core/cmms/`
- Format: `test_results_*.json`

## Common Issues & Solutions

### Issue: ModuleNotFoundError
```
Solution: Install dependencies
cd core/cmms
pip install -r requirements.txt
```

### Issue: Database Permission Error
```
Solution: Use local database path or fix permissions
export DATABASE_PATH="./test_cmms.db"
```

### Issue: Connection Refused (Integration Tests)
```
Solution: Start the application server first
python3 app.py
```

### Issue: Port Already in Use
```
Solution: Kill existing process or use different port
lsof -ti:8000 | xargs kill -9
```

## Test Status Indicators

- ✅ **PASS** - Test executed successfully
- ❌ **FAIL** - Test failed, needs investigation
- ⚠️ **WARNING** - Test passed with warnings
- ⏭️ **SKIP** - Test skipped (expected)
- 🔥 **ERROR** - Test couldn't execute

## Current Test Status

**Last Run:** October 4, 2025  
**Status:** ✅ ALL TESTS PASSING

| Test Suite | Status | Pass Rate |
|------------|--------|-----------|
| Unit Tests | ✅ PASS | 18/18 (100%) |
| E2E Tests | ✅ PASS | 18/18 (100%) |
| Integration | ⏭️ SKIP | Requires server |
| Performance | ⏭️ SKIP | Manual execution |

## CI/CD Integration

Tests are automatically run in GitHub Actions:
- On every pull request
- On push to main branch
- On scheduled basis (optional)

Check workflow: `.github/workflows/ci-cd.yml`

## Test Coverage Goals

- **Unit Tests:** ≥80% code coverage ✅
- **Integration Tests:** Critical workflows covered 🔄
- **Performance Tests:** Baseline established 🔄
- **Security Tests:** Core vulnerabilities checked ✅

## Adding New Tests

### Unit Test Template
```python
def test_new_feature(client):
    """Test description."""
    response = client.get("/new-endpoint")
    assert response.status_code == 200
    assert "expected" in response.json()
```

### Integration Test Template
```python
def test_new_workflow():
    """Test complete workflow."""
    # Setup
    data = create_test_data()
    
    # Execute
    result = perform_workflow(data)
    
    # Verify
    assert result.success == True
    
    # Cleanup
    cleanup_test_data()
```

## Best Practices

1. ✅ **Run tests before committing**
2. ✅ **Write tests for new features**
3. ✅ **Keep tests isolated and independent**
4. ✅ **Use descriptive test names**
5. ✅ **Clean up test data automatically**
6. ✅ **Mock external dependencies**
7. ✅ **Test both success and failure cases**

## Test Maintenance

- Review and update tests quarterly
- Remove obsolete tests
- Add tests for reported bugs
- Keep test data current
- Update mocks when APIs change

## Getting Help

- Check test output for error messages
- Review test logs in `tests/` directory
- Consult `COMPREHENSIVE_TEST_REPORT.md` for detailed analysis
- Check GitHub Actions logs for CI failures

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Locust documentation](https://docs.locust.io/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Repository README](../README.md)

---

*Last Updated: October 4, 2025*
