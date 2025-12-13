# ChatterFix Testing Workflow

Run comprehensive tests and analyze results.

## Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: API endpoint testing
3. **UI Tests**: Frontend functionality
4. **Security Tests**: Vulnerability scanning

## Execution Steps

1. Run the full test suite with coverage:
   ```bash
   python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
   ```

2. Run specific test categories if needed:
   ```bash
   # API tests only
   python -m pytest tests/test_api/ -v

   # Service tests only
   python -m pytest tests/test_services/ -v
   ```

3. Check for type errors:
   ```bash
   python -m mypy app/ --ignore-missing-imports
   ```

4. Run linting:
   ```bash
   python -m flake8 app/ --max-line-length=120
   ```

## Analysis

After running tests:

1. **Failed Tests**: Investigate root cause, check if related to known patterns
2. **Coverage Gaps**: Identify untested critical paths
3. **Performance**: Note any slow tests that may indicate issues
4. **Flaky Tests**: Flag tests that fail intermittently

## ChatterFix-Specific Tests

Ensure these critical paths are tested:
- Work order creation and updates
- Asset management CRUD operations
- Inventory tracking and part checkout
- User authentication flows
- Voice command processing
- Firebase/Firestore operations
- AI service integrations

## Post-Test Actions

If tests fail:
1. Do NOT deploy
2. Fix issues immediately
3. Re-run tests
4. Document any new patterns learned
