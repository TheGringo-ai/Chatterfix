#!/bin/bash

# Master Safe Deployment Script for ChatterFix CMMS
# This ensures ALL deployments are correct and safe

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VM_HOST="${1:-chatterfix-prod}"

echo -e "${BLUE}🚀 ChatterFix CMMS Safe Deployment System${NC}"
echo "=============================================="
echo "VM Target: $VM_HOST"
echo "Timestamp: $(date)"
echo ""

# Step 1: Pre-deployment validation
echo -e "${YELLOW}🔍 STEP 1: Pre-deployment validation${NC}"
if ./pre-deployment-check.sh; then
    echo -e "${GREEN}✅ Pre-deployment checks passed${NC}"
else
    echo -e "${RED}❌ Pre-deployment checks failed - STOPPING${NC}"
    exit 1
fi
echo ""

# Step 2: Run validated deployment
echo -e "${YELLOW}🚀 STEP 2: Validated deployment${NC}"
if ./validate-deployment.sh "$VM_HOST"; then
    echo -e "${GREEN}✅ Deployment successful${NC}"
else
    echo -e "${RED}❌ Deployment failed - Already rolled back${NC}"
    exit 1
fi
echo ""

# Step 3: Post-deployment health check
echo -e "${YELLOW}🔍 STEP 3: Post-deployment health verification${NC}"
sleep 5  # Give service time to fully initialize

if ./health-monitor.sh "$VM_HOST" check; then
    echo -e "${GREEN}✅ Health verification passed${NC}"
else
    echo -e "${RED}❌ Health verification failed${NC}"
    echo "Check deployment manually or run rollback"
    exit 1
fi
echo ""

# Step 4: Final verification of interactive features
echo -e "${YELLOW}🎯 STEP 4: Interactive features verification${NC}"

RESPONSE=$(ssh $VM_HOST "curl -s http://localhost:8000/cmms/workorders/dashboard")

# Check for required JavaScript functions
if echo "$RESPONSE" | grep -q "window.viewWorkOrder" && \
   echo "$RESPONSE" | grep -q "window.editWorkOrder" && \
   echo "$RESPONSE" | grep -q "onclick="; then
    echo -e "${GREEN}✅ Interactive work order features confirmed${NC}"
else
    echo -e "${RED}❌ Interactive features missing or broken${NC}"
    echo "Rolling back deployment..."
    ssh $VM_HOST "
    sudo systemctl stop chatterfix-cmms
    if [ -d '/opt/chatterfix-cmms-backup' ]; then
        sudo rm -rf /opt/chatterfix-cmms
        sudo mv /opt/chatterfix-cmms-backup /opt/chatterfix-cmms
        sudo systemctl start chatterfix-cmms
        echo 'Rollback completed'
    fi
    "
    exit 1
fi
echo ""

# Success summary
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo "=============================================="
echo -e "${GREEN}✅ All validation checks passed${NC}"
echo -e "${GREEN}✅ Service is running and healthy${NC}"
echo -e "${GREEN}✅ All endpoints are accessible${NC}"
echo -e "${GREEN}✅ Interactive features are working${NC}"
echo ""
echo "🌐 Access URLs:"
echo "  • Main Dashboard: https://chatterfix.com/cmms/dashboard/main"
echo "  • Work Orders: https://chatterfix.com/cmms/workorders/dashboard"
echo ""
echo "📋 Management Commands:"
echo "  • Health Check: ./health-monitor.sh $VM_HOST check"
echo "  • Monitor: ./health-monitor.sh $VM_HOST monitor"
echo "  • Service Status: ssh $VM_HOST 'sudo systemctl status chatterfix-cmms'"
echo "  • View Logs: ssh $VM_HOST 'sudo journalctl -u chatterfix-cmms -f'"
echo ""
echo -e "${BLUE}🔍 Starting 60-second health monitoring...${NC}"
timeout 60 ./health-monitor.sh "$VM_HOST" monitor || echo ""
echo -e "${GREEN}✅ Deployment verified - System is stable${NC}"