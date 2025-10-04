# Database Initialization Fix for Chatterfix CMMS

## Issue
The `app.py` file currently initializes the database at module import time (line 907), which causes:
- PermissionError when running tests in non-privileged environments
- Difficulty running unit tests directly with pytest
- Rigid database path requirements

## Root Cause
```python
# Line 907 in app.py
init_database()  # Called at module level during import
```

This executes when the module is imported, before the application starts, causing permission errors in test environments.

## Recommended Solution

### Option 1: Use FastAPI Startup Event (Recommended)

**Changes needed in app.py:**

```python
# 1. Make DATABASE_PATH configurable (around line 67)
DATABASE_PATH = os.getenv('DATABASE_PATH', '/var/lib/chatterfix/cmms.db')
BACKUP_DATABASE_PATH = os.getenv('BACKUP_DATABASE_PATH', '/opt/chatterfix-cmms/data/cmms.db')

# 2. Remove the module-level call (line 907)
# DELETE: init_database()

# 3. Add startup event handler (after app creation, around line 65)
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # In development, continue anyway
        if os.getenv('ENVIRONMENT') == 'development':
            logger.warning("Continuing in development mode without database")
```

**For tests, set environment variable:**

```bash
export DATABASE_PATH="./test_cmms.db"
pytest tests/unit/ -v
```

Or in `tests/conftest.py`:

```python
import os
os.environ['DATABASE_PATH'] = './test_cmms.db'
```

### Option 2: Lazy Initialization

Modify `ensure_database_dir()` to handle permission errors gracefully:

```python
def ensure_database_dir():
    """Ensure database directory exists with proper permissions"""
    db_dir = os.path.dirname(DATABASE_PATH)
    backup_dir = os.path.dirname(BACKUP_DATABASE_PATH)
    
    for directory in [db_dir, backup_dir]:
        try:
            os.makedirs(directory, exist_ok=True)
        except PermissionError:
            # In test/dev environment, use local directory
            logger.warning(f"Cannot create {directory}, using local path")
            return False
        
    # If main database doesn't exist but backup does, copy it
    if not os.path.exists(DATABASE_PATH) and os.path.exists(BACKUP_DATABASE_PATH):
        try:
            import shutil
            shutil.copy2(BACKUP_DATABASE_PATH, DATABASE_PATH)
            logger.info(f"Copied database from {BACKUP_DATABASE_PATH} to {DATABASE_PATH}")
        except PermissionError:
            logger.warning("Cannot copy backup database")
    
    return True
```

### Option 3: Test-Specific Configuration

In `tests/conftest.py`, mock the database path:

```python
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configure test environment before importing app"""
    os.environ['DATABASE_PATH'] = './test_cmms.db'
    os.environ['BACKUP_DATABASE_PATH'] = './test_cmms_backup.db'
    os.environ['ENVIRONMENT'] = 'test'
    yield
    # Cleanup
    for db_file in ['./test_cmms.db', './test_cmms_backup.db']:
        if os.path.exists(db_file):
            os.remove(db_file)
```

## Impact Analysis

### Before Fix
- ❌ Direct pytest execution fails with PermissionError
- ❌ Requires elevated privileges or specific directory structure
- ❌ Difficult to run tests in CI/CD pipelines
- ✅ Works in production (has proper permissions)

### After Fix
- ✅ Tests run in any environment
- ✅ Configurable database paths
- ✅ Better development experience
- ✅ No impact on production functionality

## Testing the Fix

### 1. Test with environment variable
```bash
cd core/cmms
export DATABASE_PATH="./test_cmms.db"
pytest tests/unit/ -v
```

### 2. Test with E2E suite
```bash
cd core/cmms
python3 comprehensive_e2e_test.py
```

### 3. Test production startup
```bash
# Production environment (with proper permissions)
python3 app.py
```

## Implementation Priority

**Priority: Medium**  
**Effort: 15-30 minutes**  
**Risk: Low (backward compatible)**

This fix improves developer experience and test reliability without affecting production deployments.

## Related Files
- `app.py` (lines 67, 70-82, 84-86, 907)
- `tests/conftest.py` (for test configuration)
- `.env` or environment configuration (for deployment)

## References
- [FastAPI Startup Events](https://fastapi.tiangolo.com/advanced/events/)
- [Python os.environ](https://docs.python.org/3/library/os.html#os.environ)
- Issue discovered during comprehensive E2E testing on 2025-10-04
