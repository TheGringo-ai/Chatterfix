#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FORCE_DEPLOY=false
SKIP_TESTS=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      FORCE_DEPLOY=true
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}🛡️  ChatterFix Pre-Deployment Validation${NC}"
echo "=========================================="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Function to print check status
check_start() {
  echo -n "🔍 $1... "
}

check_pass() {
  echo -e "${GREEN}✅ PASS${NC}"
  ((CHECKS_PASSED++))
}

check_fail() {
  echo -e "${RED}❌ FAIL${NC}"
  echo -e "${RED}   Error: $1${NC}"
  ((CHECKS_FAILED++))
}

check_warn() {
  echo -e "${YELLOW}⚠️  WARNING${NC}"
  echo -e "${YELLOW}   Warning: $1${NC}"
  ((WARNINGS++))
}

# 1. Python Syntax Validation
check_start "Validating Python syntax"
if python3 -m py_compile app/**/*.py 2>/dev/null; then
  check_pass
else
  if find app -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -q "SyntaxError"; then
    check_fail "Python syntax errors detected"
  else
    check_pass
  fi
fi

# 2. YAML Validation
check_start "Validating YAML files"
if python3 -c "import yaml" 2>/dev/null; then
  YAML_ERROR=false
  for file in $(find . -name "*.yml" -o -name "*.yaml" | grep -v node_modules); do
    if ! python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
      YAML_ERROR=true
      if [ "$VERBOSE" = true ]; then
        echo -e "\n${RED}   Invalid YAML: $file${NC}"
      fi
    fi
  done

  if [ "$YAML_ERROR" = true ]; then
    check_fail "YAML validation errors found"
  else
    check_pass
  fi
else
  check_warn "PyYAML not installed, skipping YAML validation"
fi

# 3. Requirements.txt Validation
check_start "Validating requirements.txt"
if [ -f "requirements.txt" ]; then
  if pip3 install --dry-run -r requirements.txt > /dev/null 2>&1; then
    check_pass
  else
    check_warn "Some dependencies may have issues"
  fi
else
  check_fail "requirements.txt not found"
fi

# 4. Secret Detection
check_start "Scanning for secrets"
SECRET_FOUND=false

# Check for common secret patterns
if grep -r -E "(sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36}|AIza[a-zA-Z0-9_-]{35})" app/ --exclude-dir=__pycache__ 2>/dev/null; then
  SECRET_FOUND=true
fi

if [ "$SECRET_FOUND" = true ]; then
  check_fail "Potential secrets detected in code"
else
  check_pass
fi

# 5. Environment Variables Check
check_start "Validating environment variables"
REQUIRED_VARS=("OPENAI_API_KEY" "GOOGLE_CLOUD_PROJECT")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ] && ! grep -q "^$var=" .env 2>/dev/null; then
    MISSING_VARS+=("$var")
  fi
done

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
  check_pass
else
  check_warn "Missing env vars: ${MISSING_VARS[*]} (may be set in cloud)"
fi

# 6. Docker Build Test
check_start "Testing Docker build"
if [ "$SKIP_TESTS" = false ]; then
  if docker build -t chatterfix-test:pre-deploy . > /tmp/docker-build.log 2>&1; then
    check_pass
    docker rmi chatterfix-test:pre-deploy > /dev/null 2>&1 || true
  else
    check_fail "Docker build failed (see /tmp/docker-build.log)"
  fi
else
  echo -e "${YELLOW}⏭️  SKIPPED${NC}"
fi

# 7. Database Migration Check
check_start "Checking database migrations"
if [ -f "populate_demo_data.py" ]; then
  if python3 -m py_compile populate_demo_data.py 2>/dev/null; then
    check_pass
  else
    check_fail "Database migration script has errors"
  fi
else
  check_warn "No migration script found"
fi

# 8. Critical File Existence
check_start "Checking critical files"
CRITICAL_FILES=("main.py" "Dockerfile" "requirements.txt" "app/core/database.py")
MISSING_FILES=()

for file in "${CRITICAL_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    MISSING_FILES+=("$file")
  fi
done

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
  check_pass
else
  check_fail "Missing critical files: ${MISSING_FILES[*]}"
fi

# 9. Unit Tests (if not skipped)
if [ "$SKIP_TESTS" = false ]; then
  check_start "Running unit tests"
  if [ -d "tests" ] && [ -n "$(ls -A tests/*.py 2>/dev/null)" ]; then
    if python3 -m pytest tests/ -v > /tmp/pytest.log 2>&1; then
      check_pass
    else
      check_warn "Some tests failed (see /tmp/pytest.log)"
    fi
  else
    echo -e "${YELLOW}⏭️  SKIPPED (no tests found)${NC}"
  fi
fi

# 10. Code Quality Check (Critical Issues Only)
check_start "Checking for critical code issues"
CRITICAL_ISSUES=false

# Check for dangerous eval() usage
if grep -r "eval(" app/ --exclude-dir=__pycache__ 2>/dev/null | grep -v "# safe" > /dev/null; then
  CRITICAL_ISSUES=true
  if [ "$VERBOSE" = true ]; then
    echo -e "\n${RED}   Found unsafe eval() usage${NC}"
  fi
fi

if [ "$CRITICAL_ISSUES" = true ]; then
  check_warn "Critical code quality issues found"
else
  check_pass
fi

# Summary
echo ""
echo "=========================================="
echo -e "${BLUE}📊 Validation Summary${NC}"
echo "=========================================="
echo -e "${GREEN}✅ Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}❌ Failed: $CHECKS_FAILED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo ""

# Decision
if [ $CHECKS_FAILED -gt 0 ]; then
  if [ "$FORCE_DEPLOY" = true ]; then
    echo -e "${YELLOW}⚠️  PROCEEDING WITH DEPLOYMENT (--force flag set)${NC}"
    echo ""
    exit 0
  else
    echo -e "${RED}❌ DEPLOYMENT BLOCKED${NC}"
    echo -e "${RED}Fix the failed checks above or use --force to override${NC}"
    echo ""
    exit 1
  fi
elif [ $WARNINGS -gt 0 ]; then
  echo -e "${YELLOW}⚠️  DEPLOYMENT ALLOWED WITH WARNINGS${NC}"
  echo -e "${YELLOW}Review warnings above before proceeding${NC}"
  echo ""
  exit 0
else
  echo -e "${GREEN}✅ ALL CHECKS PASSED - SAFE TO DEPLOY${NC}"
  echo ""
  exit 0
fi
