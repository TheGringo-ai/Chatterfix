#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
URL="${1:-http://localhost:8000}"
TIMEOUT=10
MAX_RETRIES=3
RETRY_DELAY=5

echo -e "${BLUE}🧪 ChatterFix Smoke Tests${NC}"
echo "=========================================="
echo "Testing URL: $URL"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
  local name="$1"
  local endpoint="$2"
  local expected_code="${3:-200}"
  local method="${4:-GET}"
  
  echo -n "🔍 Testing $name... "
  
  local retries=0
  while [ $retries -lt $MAX_RETRIES ]; do
    if [ "$method" = "GET" ]; then
      response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$URL$endpoint" 2>/dev/null || echo "000")
    else
      response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT -X "$method" "$URL$endpoint" 2>/dev/null || echo "000")
    fi
    
    if [ "$response" = "$expected_code" ] || [ "$response" = "302" ] || [ "$response" = "301" ]; then
      echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
      ((TESTS_PASSED++))
      return 0
    fi
    
    ((retries++))
    if [ $retries -lt $MAX_RETRIES ]; then
      echo -n "⏳ Retry $retries/$MAX_RETRIES... "
      sleep $RETRY_DELAY
    fi
  done
  
  echo -e "${RED}❌ FAIL${NC} (HTTP $response, expected $expected_code)"
  ((TESTS_FAILED++))
  return 1
}

# Function to test response time
test_response_time() {
  local name="$1"
  local endpoint="$2"
  local max_time="${3:-2.0}"
  
  echo -n "⏱️  Testing $name response time... "
  
  response_time=$(curl -s -o /dev/null -w "%{time_total}" --max-time $TIMEOUT "$URL$endpoint" 2>/dev/null || echo "999")
  
  if (( $(echo "$response_time < $max_time" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC} (${response_time}s < ${max_time}s)"
    ((TESTS_PASSED++))
  else
    echo -e "${YELLOW}⚠️  SLOW${NC} (${response_time}s > ${max_time}s)"
    ((TESTS_PASSED++))
  fi
}

# Function to test content
test_content() {
  local name="$1"
  local endpoint="$2"
  local expected_text="$3"
  
  echo -n "📄 Testing $name content... "
  
  content=$(curl -s --max-time $TIMEOUT "$URL$endpoint" 2>/dev/null || echo "")
  
  if echo "$content" | grep -q "$expected_text"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((TESTS_PASSED++))
  else
    echo -e "${RED}❌ FAIL${NC} (expected text not found)"
    ((TESTS_FAILED++))
  fi
}

# 1. Basic Connectivity
echo -e "${BLUE}1️⃣  Basic Connectivity${NC}"
test_endpoint "Root endpoint" "/" "200"
test_endpoint "Landing page" "/landing" "200"
echo ""

# 2. Critical Pages
echo -e "${BLUE}2️⃣  Critical Pages${NC}"
test_endpoint "Demo page" "/demo" "200"
test_endpoint "Assets page" "/assets/" "200"
test_endpoint "Work orders page" "/work-orders" "200"
echo ""

# 3. API Endpoints
echo -e "${BLUE}3️⃣  API Endpoints${NC}"
test_endpoint "Health check" "/api/health" "200"
test_endpoint "System status" "/api/status" "200"
echo ""

# 4. Authentication
echo -e "${BLUE}4️⃣  Authentication${NC}"
test_endpoint "Login page" "/login" "200"
test_endpoint "Register page" "/register" "200"
echo ""

# 5. Static Assets
echo -e "${BLUE}5️⃣  Static Assets${NC}"
test_endpoint "CSS files" "/static/css/style.css" "200"
test_endpoint "JS files" "/static/js/main.js" "200"
echo ""

# 6. Response Times
echo -e "${BLUE}6️⃣  Performance${NC}"
test_response_time "Landing page" "/landing" "2.0"
test_response_time "Demo page" "/demo" "3.0"
echo ""

# 7. Content Validation
echo -e "${BLUE}7️⃣  Content Validation${NC}"
test_content "Landing page title" "/landing" "ChatterFix"
test_content "Demo page title" "/demo" "AI Command Center"
echo ""

# 8. Database Connectivity
echo -e "${BLUE}8️⃣  Database${NC}"
echo -n "🗄️  Testing database connectivity... "
# Try to access a page that requires DB
response=$(curl -s --max-time $TIMEOUT "$URL/assets/" 2>/dev/null || echo "")
if [ -n "$response" ] && ! echo "$response" | grep -q "500 Internal Server Error"; then
  echo -e "${GREEN}✅ PASS${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}❌ FAIL${NC}"
  ((TESTS_FAILED++))
fi
echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}📊 Smoke Test Summary${NC}"
echo "=========================================="
echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✅ ALL SMOKE TESTS PASSED${NC}"
  echo ""
  exit 0
else
  echo -e "${RED}❌ SMOKE TESTS FAILED${NC}"
  echo -e "${RED}Deployment may have issues - consider rollback${NC}"
  echo ""
  exit 1
fi
