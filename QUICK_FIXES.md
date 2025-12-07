# Quick Fixes Guide for ChatterFix CMMS

This document provides immediate, actionable fixes for the most critical issues found in the repository review.

---

## 🔴 CRITICAL - Fix Immediately (15 minutes)

### 1. Fix XSS Vulnerability in Jinja2

**File:** `app/routers/demo.py` (line 214)

**Current Code:**
```python
env = Environment(
    loader=FileSystemLoader("app/templates"), 
    auto_reload=True, 
    cache_size=0
)
```

**Fixed Code:**
```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader("app/templates"),
    auto_reload=True,
    cache_size=0,
    autoescape=select_autoescape(['html', 'xml'])
)
```

**Risk:** XSS (Cross-Site Scripting) attacks  
**Severity:** HIGH

---

## 🟡 HIGH PRIORITY - Fix Today (1-2 hours)

### 2. Fix SQL Injection Vulnerabilities

**Affected Files:**
- `app/services/gemini_service.py:307`
- `app/services/openai_service.py:325`
- `app/services/computer_vision.py:301`

**Problem:** Dynamic SQL with f-strings

**Current Pattern:**
```python
conn.execute(
    f"UPDATE work_orders SET {', '.join(updates)} WHERE id = ?", 
    params
)
```

**Fixed Pattern:**
```python
# Build parameterized query
update_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
values = list(updates.values()) + [work_order_id]
conn.execute(
    f"UPDATE work_orders SET {update_clause} WHERE id = ?",
    values
)
```

**Severity:** MEDIUM (but important)

---

### 3. Secure Temporary Directory Usage

**File:** `app/services/health_monitor.py:68`

**Current Code:**
```python
def __init__(self, data_dir: str = "/tmp/chatterfix-health"):
    self.data_dir = Path(data_dir)
```

**Fixed Code:**
```python
import tempfile
from pathlib import Path

def __init__(self, data_dir: str = None):
    if data_dir is None:
        # Use secure temp directory with proper permissions
        data_dir = tempfile.mkdtemp(prefix="chatterfix-health-")
    self.data_dir = Path(data_dir)
    # Ensure secure permissions (owner-only)
    self.data_dir.chmod(0o700)
```

**Risk:** Insecure temp file usage  
**Severity:** MEDIUM

---

### 4. Fix Linting Issues (5 minutes)

**Commands to run:**
```bash
# From repository root
cd /path/to/Chatterfix

# Fix import ordering
isort app/ main.py mcp_server.py --profile=black

# Fix code formatting
black app/ main.py mcp_server.py

# Verify fixes
flake8 app/ main.py
```

**Impact:** Improves code consistency and readability

---

### 5. Fix Unused Imports and Variables

**File:** `app/routers/manager.py`

**Remove these unused imports:**
```python
# Lines 14-23 - Remove if not used:
from typing import Any, Dict, List, Optional  # Lines 14
from fastapi import HTTPException  # Line 16
from fastapi.responses import RedirectResponse  # Line 17
from app.services.gemini_service import gemini_service  # Line 22
from app.services.notification_service import notification_service  # Line 23
```

**Fix unused variable (line 246):**
```python
# Remove or use:
onboarding_data = ...  # Either use it or remove the assignment
```

**File:** `app/routers/auth.py`

**Remove unused variables (lines 268-269):**
```python
# Remove or use:
username = ...  # Line 268
full_name = ...  # Line 269
```

---

### 6. Fix Trailing Whitespace (automated)

**Command:**
```bash
# Remove trailing whitespace from Python files
find app/ -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} \;
```

**Files affected:**
- `app/routers/manager.py` (multiple lines)
- `app/routers/landing.py:104`
- `app/routers/auth.py:270, 273, 276, 286, 295, 305`

---

## 🟢 MEDIUM PRIORITY - Fix This Week

### 7. Fix Failing Tests

**Problem:** Static files not mounted in test configuration

**Test failures:**
```
❌ test_training_center_* - No route exists for name "static"
❌ test_module_detail - Static file routing issue
```

**Solution:** Update test configuration in `tests/conftest.py`:

```python
from fastapi.staticfiles import StaticFiles

@pytest.fixture
def client():
    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    with TestClient(app) as client:
        yield client
```

---

### 8. Fix Test Expectation Mismatches

**File:** `tests/test_main.py`

**Issue 1:** App title mismatch (line 31)
```python
# Current test expects:
assert app.title == "ChatterFix CMMS"

# But app has:
app.title = "ChatterFix CMMS API"

# Fix: Update test
assert app.title == "ChatterFix CMMS API"
```

**Issue 2:** API docs 404 (lines 19, 25)
```python
# Investigate why /docs returns 404
# Ensure docs are enabled in production
```

---

### 9. Add Missing Docstrings

**Priority files:**
- Large modules (>500 lines):
  - `app/services/predictive_engine.py`
  - `app/services/pm_automation_engine.py`
  - `app/services/health_monitor.py`

**Example format:**
```python
def function_name(param1: str, param2: int) -> dict:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception occurs
    """
    pass
```

---

## 🏃 Quick Commands to Run Now

```bash
# 1. Run security fix verification
bandit -r app/ -ll -f txt

# 2. Fix formatting issues
make format

# 3. Run linting
make lint

# 4. Run tests
make test

# 5. Full quality check
make check-all
```

---

## ✅ Verification Checklist

After applying fixes, verify:

- [ ] No HIGH severity security issues in Bandit scan
- [ ] Flake8 passes with no errors
- [ ] All tests pass (27/27)
- [ ] Black formatting applied
- [ ] isort import ordering applied
- [ ] No trailing whitespace in modified files
- [ ] Unused imports removed
- [ ] Docstrings added to public functions

---

## 📊 Expected Results After Fixes

**Before:**
- Bandit: 1 HIGH, 5 MEDIUM, 47 LOW severity issues
- Flake8: ~50 violations
- Tests: 19/27 passing (70%)

**After:**
- Bandit: 0 HIGH, <5 MEDIUM (legitimate), <47 LOW
- Flake8: 0 violations
- Tests: 27/27 passing (100%)

---

## 🔄 Continuous Improvement

**Enable Pre-commit Hooks:**
```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

This will automatically check code before each commit, preventing issues from entering the codebase.

---

## 📚 Additional Resources

- [REPOSITORY_REVIEW.md](REPOSITORY_REVIEW.md) - Full repository analysis
- [MONITORING.md](MONITORING.md) - Error tracking setup
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment procedures
- [README.md](README.md) - General documentation

---

**Last Updated:** December 7, 2025  
**Priority:** Start with CRITICAL fixes, then work through HIGH priority items.
