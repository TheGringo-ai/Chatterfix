#!/bin/bash
# 🔍 ChatterFix DNS Health Check
# Monitors DNS resolution and service availability

echo "🔍 ChatterFix DNS Health Check - $(date)"
echo "============================================="

# Expected Cloud Run IPs
EXPECTED_IPS=("216.239.32.21" "216.239.34.21" "216.239.36.21" "216.239.38.21")

# 1. Check DNS Resolution
echo "📡 Checking DNS resolution..."
RESOLVED_IPS=$(dig +short chatterfix.com @8.8.8.8 | sort)
EXPECTED_IPS_SORTED=$(printf "%s\n" "${EXPECTED_IPS[@]}" | sort)

if [ "$RESOLVED_IPS" = "$EXPECTED_IPS_SORTED" ]; then
    echo "✅ DNS: All IPs resolve correctly"
else
    echo "❌ DNS: IP mismatch detected"
    echo "   Expected: ${EXPECTED_IPS[*]}"
    echo "   Resolved: $RESOLVED_IPS"
fi

# 2. Check HTTPS Connectivity
echo "🔒 Checking HTTPS connectivity..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://chatterfix.com --max-time 10)
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ HTTPS: Service responding (200 OK)"
elif [ "$HTTP_STATUS" = "000" ]; then
    echo "⏳ HTTPS: SSL certificate still provisioning"
else
    echo "❌ HTTPS: Service returned $HTTP_STATUS"
fi

# 3. Check Work Order Modal Fix
echo "🛠️  Checking Work Order modal fix..."
MODAL_CHECK=$(curl -s https://chatterfix.com 2>/dev/null | grep -c "modal.show()" || echo "0")
ALERT_CHECK=$(curl -s https://chatterfix.com 2>/dev/null | grep -c "alert.*Work Order creation modal" || echo "0")

if [ "$MODAL_CHECK" -gt "0" ] && [ "$ALERT_CHECK" -eq "0" ]; then
    echo "✅ Modal: Enhanced Work Order modal detected"
elif [ "$ALERT_CHECK" -gt "0" ]; then
    echo "❌ Modal: Still showing placeholder alert"
else
    echo "⏳ Modal: Unable to verify (SSL provisioning?)"
fi

# 4. Check Service Health
echo "🏥 Checking service health..."
HEALTH_STATUS=$(curl -s https://chatterfix.com/api/health/all 2>/dev/null | jq -r '.overall_status' 2>/dev/null || echo "unknown")
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ Health: All services operational"
elif [ "$HEALTH_STATUS" = "degraded" ]; then
    echo "⚠️  Health: Some services degraded"
else
    echo "❓ Health: Status unknown or unreachable"
fi

echo "============================================="
echo "🏁 Health check completed at $(date)"