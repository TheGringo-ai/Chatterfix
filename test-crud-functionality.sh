#!/bin/bash
# Test CRUD functionality on both URLs

echo "🧪 Testing CRUD Functionality"
echo "=============================="

# URLs to test
DOMAIN_URL="https://chatterfix.com"
DIRECT_URL="https://chatterfix-unified-gateway-650169261019.us-central1.run.app"

echo ""
echo "🔍 Testing chatterfix.com:"
echo "------------------------"

# Test Work Orders
echo "Work Orders Modal Count: $(curl -s $DOMAIN_URL | grep -c 'workOrderModal')"
echo "Work Order Function Type: $(curl -s $DOMAIN_URL | grep -A 1 'showCreateWorkOrderModal' | tail -1 | grep -o 'alert\|async')"

# Test Assets  
echo "Assets Modal Count: $(curl -s $DOMAIN_URL | grep -c 'assetModal')"
echo "Asset Function Type: $(curl -s $DOMAIN_URL | grep -A 1 'showCreateAssetModal' | tail -1 | grep -o 'alert\|async')"

# Test Parts
echo "Parts Modal Count: $(curl -s $DOMAIN_URL | grep -c 'partModal')"
echo "Part Function Type: $(curl -s $DOMAIN_URL | grep -A 1 'showCreatePartModal' | tail -1 | grep -o 'alert\|async')"

echo ""
echo "🔍 Testing direct service URL:"
echo "-----------------------------"

# Test Work Orders
echo "Work Orders Modal Count: $(curl -s $DIRECT_URL | grep -c 'workOrderModal')"
echo "Work Order Function Type: $(curl -s $DIRECT_URL | grep -A 1 'showCreateWorkOrderModal' | tail -1 | grep -o 'alert\|async')"

# Test Assets
echo "Assets Modal Count: $(curl -s $DIRECT_URL | grep -c 'assetModal')"
echo "Asset Function Type: $(curl -s $DIRECT_URL | grep -A 1 'showCreateAssetModal' | tail -1 | grep -o 'alert\|async')"

# Test Parts  
echo "Parts Modal Count: $(curl -s $DIRECT_URL | grep -c 'partModal')"
echo "Part Function Type: $(curl -s $DIRECT_URL | grep -A 1 'showCreatePartModal' | tail -1 | grep -o 'alert\|async')"

echo ""
echo "📊 Summary:"
echo "----------"
echo "✅ Enhanced = async functions + modal templates"
echo "❌ Old = alert functions + no modals"