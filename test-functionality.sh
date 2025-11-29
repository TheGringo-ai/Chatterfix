#!/bin/bash

# ChatterFix Functionality Test Script
# Tests all interactive cards and signup flow

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing ChatterFix Functionality${NC}"
echo "===================================="

SITE_URL="https://chatterfix.com"

echo -e "${YELLOW}📋 Testing Interactive Card Navigation...${NC}"

# Test card destinations from dashboard.html
CARD_ROUTES=(
    "/work-orders"
    "/demo/diagnostics" 
    "/demo/inventory"
    "/demo/planner"
    "/demo/reports"
)

for route in "${CARD_ROUTES[@]}"; do
    echo -n "Testing $route: "
    if curl -s -o /dev/null -w "%{http_code}" "$SITE_URL$route" | grep -q "200"; then
        echo -e "${GREEN}✅ Working${NC}"
    else
        echo -e "${RED}❌ Failed${NC}"
    fi
done

echo
echo -e "${YELLOW}🔐 Testing Authentication Endpoints...${NC}"

# Test auth endpoints
AUTH_ROUTES=(
    "/landing"
    "/signup" 
    "/auth/login"
)

for route in "${AUTH_ROUTES[@]}"; do
    echo -n "Testing $route: "
    if curl -s -o /dev/null -w "%{http_code}" "$SITE_URL$route" | grep -q -E "(200|302)"; then
        echo -e "${GREEN}✅ Working${NC}"
    else
        echo -e "${RED}❌ Failed${NC}"
    fi
done

echo
echo -e "${YELLOW}🎯 Testing JavaScript Functions...${NC}"

# Check if voiceWorkflow function exists
echo -n "Testing Voice Workflow function: "
if curl -s "$SITE_URL" | grep -q "voiceWorkflow"; then
    echo -e "${GREEN}✅ Function found${NC}"
else
    echo -e "${RED}❌ Function missing${NC}"
fi

echo
echo -e "${BLUE}📊 Test Summary${NC}"
echo "All interactive cards should:"
echo "• Have working onclick handlers"
echo "• Navigate to functional pages"  
echo "• Show proper content when clicked"
echo
echo "Signup flow should:"
echo "• Create user account"
echo "• Set session cookie"
echo "• Redirect to dashboard with welcome message"
echo "• Grant access to full app features"