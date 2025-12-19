#!/bin/bash
#
# PM Automation Smoke Test - Bash Wrapper
#
# Usage:
#   ./scripts/smoke-test-pm.sh --org-id YOUR_ORG_ID
#   ./scripts/smoke-test-pm.sh --local --org-id demo_org
#   ./scripts/smoke-test-pm.sh --base-url https://chatterfix.com --org-id org_123
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
BASE_URL="https://chatterfix.com"
ORG_ID=""
AUTH_TOKEN=""
SCHEDULER_SECRET=""
VERBOSE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --local)
            BASE_URL="http://localhost:8000"
            shift
            ;;
        --org-id)
            ORG_ID="$2"
            shift 2
            ;;
        --token)
            AUTH_TOKEN="$2"
            shift 2
            ;;
        --scheduler-secret)
            SCHEDULER_SECRET="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --base-url URL       Base URL (default: https://chatterfix.com)"
            echo "  --local              Use localhost:8000"
            echo "  --org-id ID          Organization ID (required)"
            echo "  --token TOKEN        Auth token"
            echo "  --scheduler-secret   Scheduler secret header"
            echo "  -v, --verbose        Show detailed output"
            echo "  -h, --help           Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required args
if [ -z "$ORG_ID" ]; then
    echo -e "${RED}Error: --org-id is required${NC}"
    exit 1
fi

echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}PM AUTOMATION SMOKE TEST${NC}"
echo -e "${BOLD}========================================${NC}"
echo -e "Base URL: ${BLUE}$BASE_URL${NC}"
echo -e "Org ID:   ${BLUE}$ORG_ID${NC}"
echo ""

# Build headers
AUTH_HEADER=""
if [ -n "$AUTH_TOKEN" ]; then
    AUTH_HEADER="-H \"Authorization: Bearer $AUTH_TOKEN\""
fi

SCHEDULER_HEADER=""
if [ -n "$SCHEDULER_SECRET" ]; then
    SCHEDULER_HEADER="-H \"X-Scheduler-Secret: $SCHEDULER_SECRET\""
fi

# Test counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to log test results
log_step() {
    echo -e "\n${BLUE}${BOLD}[Step $1]${NC} $2"
}

log_success() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

log_failure() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED++))
}

log_warning() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

log_info() {
    echo -e "  → $1"
}

# Step 0: Health check
log_step 0 "Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | tail -1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HEALTH_STATUS" = "200" ]; then
    log_success "Service healthy (HTTP $HEALTH_STATUS)"
    [ -n "$VERBOSE" ] && log_info "Response: $HEALTH_BODY"
else
    log_failure "Service unhealthy (HTTP $HEALTH_STATUS)"
fi

# Step 1: Create meter reading
log_step 1 "Create Meter Reading"
METER_PAYLOAD="{\"organization_id\": \"$ORG_ID\", \"meter_id\": \"smoke_test_meter_$(date +%s)\", \"new_value\": 42.5, \"reading_source\": \"api\", \"create_work_orders\": false}"

METER_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/api/pm/meter-reading" \
    -H "Content-Type: application/json" \
    -d "$METER_PAYLOAD")
METER_STATUS=$(echo "$METER_RESPONSE" | tail -1)
METER_BODY=$(echo "$METER_RESPONSE" | head -n -1)

if [ "$METER_STATUS" = "200" ]; then
    log_success "Meter reading created (HTTP $METER_STATUS)"
elif [ "$METER_STATUS" = "400" ]; then
    log_warning "Meter not found (expected for test meter)"
elif [ "$METER_STATUS" = "401" ]; then
    log_warning "Authentication required"
else
    log_failure "Meter reading failed (HTTP $METER_STATUS)"
fi
[ -n "$VERBOSE" ] && log_info "Response: $METER_BODY"

# Step 2: Generate schedule
log_step 2 "Generate PM Schedule"
SCHEDULE_PAYLOAD="{\"organization_id\": \"$ORG_ID\", \"create_work_orders\": false}"

SCHEDULE_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/api/pm/generate-schedule" \
    -H "Content-Type: application/json" \
    -d "$SCHEDULE_PAYLOAD")
SCHEDULE_STATUS=$(echo "$SCHEDULE_RESPONSE" | tail -1)
SCHEDULE_BODY=$(echo "$SCHEDULE_RESPONSE" | head -n -1)

if [ "$SCHEDULE_STATUS" = "200" ]; then
    log_success "Schedule generation completed (HTTP $SCHEDULE_STATUS)"
    GENERATED=$(echo "$SCHEDULE_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('generated_count', 0))" 2>/dev/null || echo "?")
    log_info "Generated count: $GENERATED"
elif [ "$SCHEDULE_STATUS" = "401" ]; then
    log_warning "Authentication required"
else
    log_failure "Schedule generation failed (HTTP $SCHEDULE_STATUS)"
fi
[ -n "$VERBOSE" ] && log_info "Response: $SCHEDULE_BODY"

# Step 3: Get overview
log_step 3 "Get PM Overview"
OVERVIEW_RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$BASE_URL/api/pm/overview?organization_id=$ORG_ID&days_ahead=30")
OVERVIEW_STATUS=$(echo "$OVERVIEW_RESPONSE" | tail -1)
OVERVIEW_BODY=$(echo "$OVERVIEW_RESPONSE" | head -n -1)

if [ "$OVERVIEW_STATUS" = "200" ]; then
    log_success "Overview fetched (HTTP $OVERVIEW_STATUS)"
    ACTIVE=$(echo "$OVERVIEW_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('overview', {}).get('active_rules', 0))" 2>/dev/null || echo "?")
    log_info "Active rules: $ACTIVE"
elif [ "$OVERVIEW_STATUS" = "401" ]; then
    log_warning "Authentication required"
else
    log_failure "Overview fetch failed (HTTP $OVERVIEW_STATUS)"
fi
[ -n "$VERBOSE" ] && log_info "Response: $OVERVIEW_BODY"

# Step 4: Confirm orders exist
log_step 4 "Confirm Orders Exist"
if [ "$OVERVIEW_STATUS" = "200" ]; then
    ORDERS=$(echo "$OVERVIEW_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('recent_pm_orders', [])))" 2>/dev/null || echo "0")
    RULES=$(echo "$OVERVIEW_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('due_rules', [])))" 2>/dev/null || echo "0")

    if [ "$ORDERS" != "0" ] || [ "$RULES" != "0" ]; then
        log_success "Found $ORDERS orders and $RULES due rules"
    else
        log_warning "No PM orders or due rules found (may be expected)"
    fi
else
    log_warning "Could not check orders (overview failed)"
fi

# Step 5: List rules
log_step 5 "List PM Rules"
RULES_RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$BASE_URL/api/pm/rules?organization_id=$ORG_ID")
RULES_STATUS=$(echo "$RULES_RESPONSE" | tail -1)
RULES_BODY=$(echo "$RULES_RESPONSE" | head -n -1)

if [ "$RULES_STATUS" = "200" ]; then
    RULE_COUNT=$(echo "$RULES_BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('rules', [])))" 2>/dev/null || echo "?")
    log_success "Found $RULE_COUNT rules (HTTP $RULES_STATUS)"
elif [ "$RULES_STATUS" = "401" ]; then
    log_warning "Authentication required"
else
    log_failure "Rules fetch failed (HTTP $RULES_STATUS)"
fi

# Step 6: List meters
log_step 6 "List Asset Meters"
METERS_RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$BASE_URL/api/pm/meters?organization_id=$ORG_ID")
METERS_STATUS=$(echo "$METERS_RESPONSE" | tail -1)
METERS_BODY=$(echo "$METERS_RESPONSE" | head -n -1)

if [ "$METERS_STATUS" = "200" ]; then
    METER_COUNT=$(echo "$METERS_BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('meters', [])))" 2>/dev/null || echo "?")
    log_success "Found $METER_COUNT meters (HTTP $METERS_STATUS)"
elif [ "$METERS_STATUS" = "401" ]; then
    log_warning "Authentication required"
else
    log_failure "Meters fetch failed (HTTP $METERS_STATUS)"
fi

# Summary
echo -e "\n${BOLD}========================================${NC}"
echo -e "${BOLD}TEST SUMMARY${NC}"
echo -e "${BOLD}========================================${NC}"
echo -e "${GREEN}Passed:   $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed:   $FAILED${NC}"
TOTAL=$((PASSED + FAILED + WARNINGS))
echo -e "Total:    $TOTAL"

if [ "$FAILED" -eq 0 ]; then
    echo -e "\n${GREEN}${BOLD}✓ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "\n${RED}${BOLD}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
