#!/bin/bash
"""
🔍 ChatterFix DNS & HTTPS Monitor
Real-time monitoring of DNS propagation and HTTPS status
"""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN="chatterfix.com"
EXPECTED_IP="216.239.32.21"

echo -e "${BLUE}🔍 ChatterFix DNS & HTTPS Monitor${NC}"
echo "=================================="
echo "Domain: $DOMAIN"
echo "Target IP: $EXPECTED_IP"
echo "Started: $(date)"
echo ""

while true; do
    echo -e "${BLUE}$(date '+%H:%M:%S') - Checking DNS...${NC}"
    
    # Check DNS resolution
    CURRENT_IP=$(nslookup $DOMAIN | grep -A 1 "Non-authoritative answer:" | grep "Address:" | tail -1 | awk '{print $2}')
    
    if [ "$CURRENT_IP" = "$EXPECTED_IP" ]; then
        echo -e "${GREEN}✅ DNS Updated: $CURRENT_IP${NC}"
        
        # Test HTTP
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/health 2>/dev/null)
        echo -e "HTTP Status: $HTTP_STATUS"
        
        # Test HTTPS
        HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health 2>/dev/null)
        
        if [ "$HTTPS_STATUS" = "200" ]; then
            echo -e "${GREEN}🎉 HTTPS Working: $HTTPS_STATUS${NC}"
            echo ""
            echo -e "${GREEN}🚀 ChatterFix is LIVE at https://$DOMAIN${NC}"
            echo ""
            echo "Testing API endpoints..."
            
            # Test key endpoints
            for endpoint in "health" "api/work-orders" "api/assets" "api/parts"; do
                status=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/$endpoint 2>/dev/null)
                if [ "$status" = "200" ]; then
                    echo -e "${GREEN}✅ /$endpoint: $status${NC}"
                else
                    echo -e "${YELLOW}⚠️ /$endpoint: $status${NC}"
                fi
            done
            
            echo ""
            echo -e "${GREEN}🎉 SETUP COMPLETE! 🎉${NC}"
            echo "Your ChatterFix CMMS is now live at:"
            echo "🌐 https://$DOMAIN"
            echo "📊 https://$DOMAIN/api/work-orders"
            echo "🔧 https://$DOMAIN/health"
            break
            
        elif [ "$HTTPS_STATUS" = "000" ]; then
            echo -e "${YELLOW}⏳ HTTPS: SSL certificate still provisioning...${NC}"
        else
            echo -e "${YELLOW}⚠️ HTTPS Status: $HTTPS_STATUS${NC}"
        fi
        
    else
        echo -e "${YELLOW}⏳ DNS: $CURRENT_IP (waiting for $EXPECTED_IP)${NC}"
    fi
    
    echo ""
    sleep 30
done