# Error Monitoring and Import Tracking

This document describes the error monitoring and import tracking setup for ChatterFix CMMS.

## Overview

ChatterFix includes comprehensive error monitoring to track and respond to application errors, with special emphasis on import-related issues that can cause service unavailability.

## Components

### 1. Error Tracking Middleware

The `ErrorTrackingMiddleware` in `app/middleware/error_tracking.py` provides:

- **Structured Logging**: All errors are logged with context (timestamp, request info, environment)
- **Import Error Detection**: Special handling for import-related errors with critical log level
- **User-Friendly Responses**: Returns appropriate HTTP status codes and messages
- **External Monitoring Integration**: Supports Sentry and other monitoring services

#### Usage

The middleware is automatically configured in `main.py`. To enable Sentry integration:

```python
from app.middleware import ErrorTrackingMiddleware

# Add middleware to your FastAPI app
app.add_middleware(
    ErrorTrackingMiddleware,
    sentry_dsn="your-sentry-dsn",  # Optional
    environment="production"
)
```

#### Configuration

Set the following environment variables:

- `SENTRY_DSN`: Your Sentry DSN for error tracking (optional)
- `ENVIRONMENT`: Current environment (development, staging, production)

### 2. Import Validation Tests

The test suite in `tests/test_imports.py` validates:

- All router modules can be imported without errors
- All routers have the required `router` attribute
- Critical routers (team, landing) are specifically tested
- All dependencies are available
- Middleware can be instantiated correctly

#### Running Import Tests

```bash
# Run all import validation tests
pytest tests/test_imports.py -v

# Run specific test
pytest tests/test_imports.py::TestRouterImports::test_import_all_routers -v

# Run with detailed output
pytest tests/test_imports.py -vv
```

### 3. Linting Configuration

Import linting is configured through multiple tools:

#### Flake8 (`.flake8`)

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501, C901
per-file-ignores =
    __init__.py:F401
    main.py:E402
import-order-style = google
application-import-names = app
```

#### isort (`pyproject.toml`)

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["app"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]
```

#### Pylint

Pylint is configured to catch additional import issues. Run with:

```bash
pylint app/ --disable=all --enable=import-error,cyclic-import,relative-beyond-top-level
```

### 4. Pre-commit Hooks

Pre-commit hooks (`.pre-commit-config.yaml`) automatically check:

- Import ordering (isort)
- Import errors (flake8)
- Code formatting (black)
- Type checking (mypy)
- Security issues (bandit)
- Tests pass (pytest)

#### Installing Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

## Monitoring Services Integration

### Sentry

To integrate with Sentry:

1. Install the Sentry SDK:
   ```bash
   pip install sentry-sdk[fastapi]
   ```

2. Set your Sentry DSN:
   ```bash
   export SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"
   ```

3. The middleware will automatically initialize Sentry and send errors

### Google Cloud Logging

For Google Cloud Platform deployments:

1. Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set
2. Structured logs are automatically sent to Cloud Logging
3. Use log filtering to find import errors:
   ```
   severity >= ERROR
   jsonPayload.error_details.is_import_error = true
   ```

### Custom Monitoring

To add custom monitoring integration, modify the `_send_to_monitoring` method in `ErrorTrackingMiddleware`:

```python
def _send_to_monitoring(self, exc: Exception, error_details: dict) -> None:
    # Add your custom monitoring logic here
    if error_details.get("is_import_error"):
        # Send alert for import errors
        custom_monitoring_client.send_alert(
            severity="critical",
            message=error_details["error_message"]
        )
```

## Error Response Format

### Production Mode

```json
{
  "error": true,
  "message": "An unexpected error occurred. Our team has been notified.",
  "timestamp": "2025-12-07T02:38:35.180Z"
}
```

### Development Mode

```json
{
  "error": true,
  "message": "An unexpected error occurred.",
  "timestamp": "2025-12-07T02:38:35.180Z",
  "debug": {
    "error_type": "ImportError",
    "error_message": "cannot import name 'missing_module'",
    "path": "/api/endpoint"
  }
}
```

## Log Format

Structured logs include:

```json
{
  "timestamp": "2025-12-07T02:38:35.180Z",
  "environment": "production",
  "error_type": "ImportError",
  "error_message": "cannot import name 'missing_module'",
  "is_import_error": true,
  "traceback": "...",
  "request": {
    "method": "GET",
    "url": "https://example.com/api/endpoint",
    "path": "/api/endpoint",
    "headers": {...},
    "client": "192.168.1.1"
  }
}
```

## Troubleshooting Import Errors

### Common Import Errors

1. **ModuleNotFoundError**: Missing dependency
   ```bash
   # Solution: Install the missing package
   pip install package-name
   ```

2. **ImportError: cannot import name**: Incorrect import statement or circular dependency
   ```bash
   # Solution: Check import paths and refactor circular dependencies
   # Use tools to detect cycles:
   pytest tests/test_imports.py -v
   ```

3. **Relative import beyond top-level package**: Incorrect relative import
   ```bash
   # Solution: Use absolute imports from 'app' package
   from app.routers import module  # Good
   from ..routers import module    # Bad (if beyond top level)
   ```

### Debugging Steps

1. **Check import validation tests**:
   ```bash
   pytest tests/test_imports.py -vv
   ```

2. **Run linters**:
   ```bash
   flake8 app/ --select=E,F,I
   isort app/ --check-only
   pylint app/ --disable=all --enable=import-error
   ```

3. **Check application logs**:
   ```bash
   # Look for import errors in logs
   grep "IMPORT ERROR" logs/chatterfix.log
   ```

4. **Test imports manually**:
   ```bash
   python -c "from app.routers import team, landing"
   ```

### Prevention Checklist

- ✅ Run import validation tests before deploying
- ✅ Enable pre-commit hooks to catch issues early
- ✅ Review CI/CD pipeline logs for import warnings
- ✅ Monitor error tracking dashboard for import errors
- ✅ Keep dependencies up to date and documented
- ✅ Use absolute imports consistently
- ✅ Avoid circular dependencies

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/test-and-lint.yml`) includes:

1. **Import validation**: Runs import tests on every push/PR
2. **Linting**: Checks code style and import order
3. **Type checking**: Validates type hints including imports
4. **Security scanning**: Checks for vulnerable dependencies

### Viewing CI Results

- Import test failures will show which modules failed to import
- Linting failures will show import order or style issues
- The workflow fails fast on critical errors to prevent deployment

## Best Practices

1. **Always use absolute imports** from the `app` package
2. **Keep imports organized** using isort
3. **Run tests locally** before committing
4. **Monitor error logs** regularly for import issues
5. **Document new dependencies** in requirements files
6. **Use type hints** to catch import issues at type-checking time
7. **Test critical paths** with integration tests

## Support

For issues or questions:

1. Check the logs: `logs/chatterfix.log`
2. Run import tests: `pytest tests/test_imports.py -vv`
3. Review Sentry dashboard (if configured)
4. Contact the development team

---

**Last Updated**: 2025-12-07
**Version**: 2.1.0
