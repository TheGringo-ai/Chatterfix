#!/bin/bash

# ChatterFix Custom Domain Deployment Script
# Deploy ChatterFix to chatterfix.com

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌐 ChatterFix Custom Domain Deployment${NC}"
echo "==========================================="

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"chatterfix-cmms"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="chatterfix-cmms"
DOMAIN="chatterfix.com"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Domain: $DOMAIN"
echo

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Verify domain ownership (if not done already)
echo -e "${YELLOW}🔍 Checking domain verification...${NC}"
VERIFIED=$(gcloud domains list-user-verified --filter="domain:$DOMAIN" --format="value(domain)" 2>/dev/null || echo "")

if [ -z "$VERIFIED" ]; then
    echo -e "${YELLOW}⚠️  Domain $DOMAIN not verified in Google Search Console.${NC}"
    echo "Please verify your domain ownership first:"
    echo "1. Go to: https://search.google.com/search-console"
    echo "2. Add and verify $DOMAIN"
    echo "3. Run this script again"
    echo
    read -p "Have you verified the domain? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please verify the domain and try again."
        exit 1
    fi
fi

# Deploy the service first (if not already deployed)
echo -e "${BLUE}🚀 Deploying ChatterFix service...${NC}"
if ! gcloud run services describe $SERVICE_NAME --region=$REGION &>/dev/null; then
    echo -e "${YELLOW}Service not found. Deploying first...${NC}"
    ./deploy-gcp.sh
fi

# Create domain mapping
echo -e "${BLUE}🔗 Creating domain mapping...${NC}"
gcloud run domain-mappings create \
    --service=$SERVICE_NAME \
    --domain=$DOMAIN \
    --region=$REGION \
    --platform=managed

# Get the required DNS records
echo -e "${BLUE}📋 Getting DNS configuration...${NC}"
DNS_RECORDS=$(gcloud run domain-mappings describe $DOMAIN --region=$REGION --format="value(status.resourceRecords[].name,status.resourceRecords[].rrdata)" 2>/dev/null)

echo -e "${GREEN}✅ Domain mapping created!${NC}"
echo "==========================================="
echo
echo -e "${YELLOW}📋 DNS Configuration Required:${NC}"
echo "Please add these DNS records to your domain provider:"
echo

if [ ! -z "$DNS_RECORDS" ]; then
    echo "$DNS_RECORDS" | while IFS=$'\t' read -r name rrdata; do
        if [[ $name == *"_acme-challenge"* ]]; then
            echo -e "${BLUE}TXT Record:${NC}"
            echo "Name: $name"
            echo "Value: $rrdata"
        else
            echo -e "${BLUE}CNAME Record:${NC}"
            echo "Name: $name (or @)"
            echo "Value: $rrdata"
        fi
        echo
    done
else
    echo -e "${YELLOW}⚠️  DNS records not ready yet. Run this command to check:${NC}"
    echo "gcloud run domain-mappings describe $DOMAIN --region=$REGION"
fi

# Set up SSL certificate
echo -e "${BLUE}🔒 Setting up SSL certificate...${NC}"
echo "Google Cloud Run automatically provisions SSL certificates for custom domains."
echo "The certificate will be issued once DNS records are properly configured."

# Create a health check script for the custom domain
cat > check-domain-status.sh << EOF
#!/bin/bash
echo "🔍 Checking domain mapping status..."
gcloud run domain-mappings describe $DOMAIN --region=$REGION --format="table(status.conditions[].type,status.conditions[].status,status.conditions[].reason)"
echo
echo "🌐 Testing domain accessibility..."
if curl -Is https://$DOMAIN/health | head -n 1 | grep "200 OK" > /dev/null; then
    echo "✅ $DOMAIN is accessible and healthy!"
else
    echo "⏳ $DOMAIN not ready yet. Check DNS propagation."
fi
EOF

chmod +x check-domain-status.sh

echo -e "${GREEN}🎉 Custom domain setup initiated!${NC}"
echo "==========================================="
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Add the DNS records shown above to your domain provider"
echo "2. Wait for DNS propagation (5-60 minutes)"
echo "3. Run: ./check-domain-status.sh to monitor progress"
echo "4. Once ready, access your app at: https://$DOMAIN"
echo
echo -e "${YELLOW}📚 Documentation:${NC}"
echo "Domain mapping: https://cloud.google.com/run/docs/mapping-custom-domains"
echo "SSL certificates: https://cloud.google.com/run/docs/securing/using-https"
echo
echo -e "${BLUE}🔧 Monitoring Commands:${NC}"
echo "Check domain status: ./check-domain-status.sh"
echo "View service logs: gcloud run logs read --service=$SERVICE_NAME --region=$REGION"
echo "Test health: curl https://$DOMAIN/health"