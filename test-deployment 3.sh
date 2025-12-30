#!/bin/bash
# ChatterFix CMMS Deployment Verification Tests

echo "🧪 ChatterFix CMMS Deployment Tests"
echo "===================================="

BASE_URL="https://chatterfix.com"
FAILED_TESTS=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"

    echo -n "Testing $name... "

    if [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url")
        else
            response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url")
        fi
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi

    if [ "$response" = "200" ]; then
        echo "✅ PASS ($response)"
    else
        echo "❌ FAIL ($response)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Core functionality tests
echo "🔧 Core Functionality Tests"
echo "----------------------------"
test_endpoint "Health Check" "$BASE_URL/health"
test_endpoint "Main Dashboard" "$BASE_URL/"
test_endpoint "Assets Page" "$BASE_URL/cmms/assets"
test_endpoint "Work Orders" "$BASE_URL/cmms/workorders"
test_endpoint "Parts" "$BASE_URL/cmms/parts"

# AI Features tests
echo ""
echo "🤖 AI Features Tests"
echo "-------------------"
test_endpoint "AI Predictive Health" "$BASE_URL/ai/predictive/health"
test_endpoint "AI Parts Search" "$BASE_URL/parts/ai-search" "POST" '{"query":"bearing"}'
test_endpoint "Voice Commands" "$BASE_URL/voice/command" "POST"
test_endpoint "NL Work Orders" "$BASE_URL/workorders/create-from-nl" "POST" '{"natural_language_input":"pump is leaking"}'

# Performance tests
echo ""
echo "⚡ Performance Tests"
echo "-------------------"
echo -n "Page load time... "
load_time=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL/")
if (( $(echo "$load_time < 3.0" | bc -l) )); then
    echo "✅ PASS (${load_time}s)"
else
    echo "⚠️ SLOW (${load_time}s)"
fi

# Security tests
echo ""
echo "🔒 Security Tests"
echo "----------------"
test_endpoint "HTTPS Redirect" "http://chatterfix.com/"
echo -n "SSL Certificate... "
ssl_result=$(curl -s -I https://chatterfix.com/ | grep -i "strict-transport-security")
if [ -n "$ssl_result" ]; then
    echo "✅ PASS (HSTS enabled)"
else
    echo "⚠️ WARN (HSTS not detected)"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 All tests passed! ChatterFix is working correctly."
    echo "✅ HTTPS: Working"
    echo "✅ Core Features: Working"
    echo "🤖 AI Features: Partially deployed (gradual activation)"
    echo ""
    echo "🌐 Your CMMS is live at: https://chatterfix.com"
else
    echo "❌ $FAILED_TESTS test(s) failed"
    echo "🔧 Check deployment and try running: ./deploy-production-safe.sh"
fi

exit $FAILED_TESTS
