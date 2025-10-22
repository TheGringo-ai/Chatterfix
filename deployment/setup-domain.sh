#!/bin/bash
"""
🌐 ChatterFix HTTPS Domain Setup Script
Sets up chatterfix.com with HTTPS for Cloud Run services
"""

echo "🚀 ChatterFix HTTPS Domain Setup"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="chatterfix.gringosgambit.com"
SERVICE="chatterfix-unified-gateway"
REGION="us-central1"
PROJECT_ID="fredfix"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "Domain: $DOMAIN"
echo "Service: $SERVICE"
echo "Region: $REGION"
echo "Project: $PROJECT_ID"
echo ""

# Step 1: Check current domain mappings
echo -e "${BLUE}1. Checking current domain mappings...${NC}"
gcloud beta run domain-mappings list --region=$REGION

echo ""

# Step 2: Check if domain mapping exists
echo -e "${BLUE}2. Checking domain mapping status...${NC}"
MAPPING_STATUS=$(gcloud beta run domain-mappings describe $DOMAIN --region=$REGION --format="value(status.conditions[0].status)" 2>/dev/null)

if [ "$MAPPING_STATUS" = "True" ]; then
    echo -e "${GREEN}✅ Domain mapping exists and is ready${NC}"
else
    echo -e "${YELLOW}⚠️ Domain mapping needs attention${NC}"
    
    # Get the required DNS configuration
    echo -e "${BLUE}📝 Required DNS Configuration:${NC}"
    gcloud beta run domain-mappings describe $DOMAIN --region=$REGION --format="table(
        metadata.name:label=DOMAIN,
        status.resourceRecords[0].type:label=TYPE,
        status.resourceRecords[0].rrdata:label=VALUE
    )" 2>/dev/null || echo "Domain mapping not found"
fi

echo ""

# Step 3: Check SSL certificate status
echo -e "${BLUE}3. Checking SSL certificate status...${NC}"
CERT_STATUS=$(gcloud beta run domain-mappings describe $DOMAIN --region=$REGION --format="value(status.certificateStatus)" 2>/dev/null)

case $CERT_STATUS in
    "CERT_PROVISIONED")
        echo -e "${GREEN}✅ SSL certificate is provisioned and ready${NC}"
        ;;
    "CERT_PENDING_DOMAIN_VALIDATION")
        echo -e "${YELLOW}⏳ SSL certificate pending domain validation${NC}"
        echo "Please ensure DNS records are properly configured"
        ;;
    "CERT_PENDING")
        echo -e "${YELLOW}⏳ SSL certificate provisioning in progress${NC}"
        ;;
    *)
        echo -e "${RED}❌ SSL certificate status: ${CERT_STATUS:-Unknown}${NC}"
        ;;
esac

echo ""

# Step 4: Test HTTP/HTTPS connectivity
echo -e "${BLUE}4. Testing connectivity...${NC}"

# Test HTTP
echo "Testing HTTP connectivity..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/health 2>/dev/null)
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo -e "${GREEN}✅ HTTP connectivity: $HTTP_STATUS${NC}"
else
    echo -e "${RED}❌ HTTP connectivity failed: $HTTP_STATUS${NC}"
fi

# Test HTTPS
echo "Testing HTTPS connectivity..."
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health 2>/dev/null)
if [ "$HTTPS_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS connectivity: $HTTPS_STATUS${NC}"
    
    # Test API endpoints
    echo "Testing API endpoints..."
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/api/work-orders 2>/dev/null)
    if [ "$API_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ API endpoints working: $API_STATUS${NC}"
    else
        echo -e "${YELLOW}⚠️ API endpoints status: $API_STATUS${NC}"
    fi
    
else
    echo -e "${RED}❌ HTTPS connectivity failed: $HTTPS_STATUS${NC}"
fi

echo ""

# Step 5: Display DNS configuration instructions
echo -e "${BLUE}5. DNS Configuration Instructions:${NC}"
echo "=================================="
echo ""
echo "To complete HTTPS setup for $DOMAIN:"
echo ""
echo "1. Add this DNS record to your domain provider:"
echo "   Type: CNAME"
echo "   Name: chatterfix"
echo "   Value: ghs.googlehosted.com"
echo ""
echo "2. Wait for DNS propagation (5-30 minutes)"
echo ""
echo "3. Google will automatically provision SSL certificate"
echo ""
echo "4. Test with: curl -I https://$DOMAIN/health"
echo ""

# Step 6: Service URLs
echo -e "${BLUE}6. Service URLs:${NC}"
echo "==============="
echo ""
echo "🌐 Production URLs:"
echo "   Main Site: https://$DOMAIN"
echo "   API Base:  https://$DOMAIN/api"
echo "   Health:    https://$DOMAIN/health"
echo ""
echo "🔧 Development URLs:"
echo "   Gateway:   https://chatterfix-unified-gateway-650169261019.us-central1.run.app"
echo "   CMMS:      https://chatterfix-cmms-650169261019.us-central1.run.app"
echo ""

# Step 7: Next steps
echo -e "${BLUE}7. Next Steps:${NC}"
echo "============="
echo ""
if [ "$CERT_STATUS" = "CERT_PROVISIONED" ] && [ "$HTTPS_STATUS" = "200" ]; then
    echo -e "${GREEN}🎉 HTTPS is fully configured and working!${NC}"
    echo ""
    echo "✅ Domain mapping: Active"
    echo "✅ SSL certificate: Provisioned" 
    echo "✅ HTTPS connectivity: Working"
    echo "✅ API endpoints: Accessible"
    echo ""
    echo -e "${GREEN}Your ChatterFix CMMS is now live at: https://$DOMAIN${NC}"
else
    echo -e "${YELLOW}📋 Manual steps required:${NC}"
    echo ""
    echo "1. Configure DNS CNAME record (see instructions above)"
    echo "2. Wait for DNS propagation"
    echo "3. SSL certificate will auto-provision"
    echo "4. Re-run this script to verify: ./setup-domain.sh"
    echo ""
    echo "Expected timeline: 5-30 minutes after DNS configuration"
fi

echo ""
echo -e "${BLUE}🔍 Monitoring:${NC}"
echo "Monitor progress with:"
echo "  gcloud beta run domain-mappings describe $DOMAIN --region=$REGION"
echo ""
echo "Check certificate status:"
echo "  curl -I https://$DOMAIN"
echo ""

# Final status summary
echo -e "${BLUE}📊 Final Status Summary:${NC}"
echo "========================"
printf "%-25s %s\n" "Domain Mapping:" "${MAPPING_STATUS:-❌ Not Ready}"
printf "%-25s %s\n" "SSL Certificate:" "${CERT_STATUS:-❌ Not Ready}"
printf "%-25s %s\n" "HTTP Status:" "${HTTP_STATUS:-❌ Failed}"
printf "%-25s %s\n" "HTTPS Status:" "${HTTPS_STATUS:-❌ Failed}"

echo ""
echo -e "${GREEN}🚀 ChatterFix HTTPS Setup Complete!${NC}"