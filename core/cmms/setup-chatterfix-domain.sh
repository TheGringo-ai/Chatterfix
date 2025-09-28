#!/bin/bash

# ChatterFix CMMS - Complete Domain Setup Script for chatterfix.com
# Sets up static IP, SSL certificates, and domain configuration

set -e

echo "🌍 Setting up chatterfix.com domain deployment..."

# Configuration
DOMAIN="chatterfix.com"
STATIC_IP="34.8.204.5"
SERVICE_NAME="chatterfix-cmms"
PROJECT_ID="fredfix"
REGION="us-central1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Verify static IP exists
echo "🔍 Verifying static IP..."
if gcloud compute addresses describe chatterfix-static-ip --global --quiet > /dev/null 2>&1; then
    echo_info "Static IP chatterfix-static-ip exists: $STATIC_IP"
else
    echo_error "Static IP not found. Creating..."
    gcloud compute addresses create chatterfix-static-ip --global --description="Static IP for chatterfix.com CMMS deployment"
    STATIC_IP=$(gcloud compute addresses describe chatterfix-static-ip --global --format="value(address)")
    echo_info "Created static IP: $STATIC_IP"
fi

# 2. Create domain mapping for Cloud Run
echo "🌐 Setting up domain mapping..."
cat > domain-mapping.yaml << EOF
apiVersion: serving.knative.dev/v1
kind: DomainMapping
metadata:
  name: $DOMAIN
  namespace: '$PROJECT_ID'
  annotations:
    run.googleapis.com/launch-stage: BETA
spec:
  routeRef:
    name: $SERVICE_NAME
EOF

# Apply domain mapping
if kubectl apply -f domain-mapping.yaml; then
    echo_info "Domain mapping created successfully"
else
    echo_warning "Domain mapping may already exist or failed to create"
fi

# 3. Get required DNS records
echo "📋 Getting DNS configuration..."
echo ""
echo "=== DNS CONFIGURATION REQUIRED ==="
echo "Please add these DNS records to your chatterfix.com domain:"
echo ""
echo "A Record:"
echo "  Name: @ (or leave blank for root domain)"
echo "  Value: $STATIC_IP"
echo "  TTL: 300"
echo ""
echo "CNAME Record:"
echo "  Name: www"
echo "  Value: $DOMAIN"
echo "  TTL: 300"
echo ""

# 4. Create SSL certificate
echo "🔐 Setting up SSL certificate..."
if gcloud compute ssl-certificates describe chatterfix-ssl --global --quiet > /dev/null 2>&1; then
    echo_info "SSL certificate chatterfix-ssl already exists"
else
    echo "Creating managed SSL certificate..."
    gcloud compute ssl-certificates create chatterfix-ssl \
        --description="SSL certificate for chatterfix.com" \
        --domains="$DOMAIN,www.$DOMAIN" \
        --global
    echo_info "SSL certificate created (will take time to provision)"
fi

# 5. Create load balancer
echo "⚖️  Setting up load balancer..."

# Create backend service
if gcloud compute backend-services describe chatterfix-backend --global --quiet > /dev/null 2>&1; then
    echo_info "Backend service already exists"
else
    gcloud compute backend-services create chatterfix-backend \
        --description="Backend service for ChatterFix CMMS" \
        --global \
        --load-balancing-scheme=EXTERNAL \
        --port-name=http
    echo_info "Backend service created"
fi

# Create URL map
if gcloud compute url-maps describe chatterfix-urlmap --quiet > /dev/null 2>&1; then
    echo_info "URL map already exists"
else
    gcloud compute url-maps create chatterfix-urlmap \
        --description="URL map for ChatterFix CMMS" \
        --default-backend-service=chatterfix-backend
    echo_info "URL map created"
fi

# Create HTTP(S) proxy
if gcloud compute target-https-proxies describe chatterfix-https-proxy --quiet > /dev/null 2>&1; then
    echo_info "HTTPS proxy already exists"
else
    gcloud compute target-https-proxies create chatterfix-https-proxy \
        --description="HTTPS proxy for ChatterFix CMMS" \
        --url-map=chatterfix-urlmap \
        --ssl-certificates=chatterfix-ssl
    echo_info "HTTPS proxy created"
fi

# Create forwarding rule
if gcloud compute forwarding-rules describe chatterfix-https-rule --global --quiet > /dev/null 2>&1; then
    echo_info "HTTPS forwarding rule already exists"
else
    gcloud compute forwarding-rules create chatterfix-https-rule \
        --description="HTTPS forwarding rule for ChatterFix CMMS" \
        --global \
        --target-https-proxy=chatterfix-https-proxy \
        --address=chatterfix-static-ip \
        --ports=443
    echo_info "HTTPS forwarding rule created"
fi

# Create HTTP to HTTPS redirect
if gcloud compute target-http-proxies describe chatterfix-http-proxy --quiet > /dev/null 2>&1; then
    echo_info "HTTP proxy already exists"
else
    # Create URL map for HTTP redirect
    gcloud compute url-maps create chatterfix-http-redirect \
        --description="HTTP to HTTPS redirect for ChatterFix" \
        --default-url-redirect-response-code=301 \
        --default-url-redirect-https-redirect
    
    gcloud compute target-http-proxies create chatterfix-http-proxy \
        --description="HTTP proxy for ChatterFix CMMS redirect" \
        --url-map=chatterfix-http-redirect
    
    gcloud compute forwarding-rules create chatterfix-http-rule \
        --description="HTTP forwarding rule for ChatterFix CMMS redirect" \
        --global \
        --target-http-proxy=chatterfix-http-proxy \
        --address=chatterfix-static-ip \
        --ports=80
    echo_info "HTTP to HTTPS redirect configured"
fi

# 6. Deploy the service with the new configuration
echo "🚀 Deploying ChatterFix CMMS to Cloud Run..."

# Build and deploy
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars "ENVIRONMENT=production,DOMAIN=$DOMAIN" \
    --tag production

echo_info "ChatterFix CMMS deployed successfully"

# 7. Update backend service to point to Cloud Run
echo "🔗 Connecting load balancer to Cloud Run..."

# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" | sed 's|https://||')

# Create NEG for Cloud Run
if gcloud compute network-endpoint-groups describe chatterfix-neg --region=$REGION --quiet > /dev/null 2>&1; then
    echo_info "Network endpoint group already exists"
else
    gcloud compute network-endpoint-groups create chatterfix-neg \
        --region=$REGION \
        --network-endpoint-type=serverless \
        --cloud-run-service=$SERVICE_NAME
    echo_info "Network endpoint group created"
fi

# Add NEG to backend service
gcloud compute backend-services add-backend chatterfix-backend \
    --global \
    --network-endpoint-group=chatterfix-neg \
    --network-endpoint-group-region=$REGION

echo_info "Backend service connected to Cloud Run"

# 8. Final status check
echo ""
echo "🎉 ChatterFix CMMS Domain Setup Complete!"
echo ""
echo "=== SETUP SUMMARY ==="
echo "Domain: $DOMAIN"
echo "Static IP: $STATIC_IP"
echo "SSL Certificate: chatterfix-ssl (managed)"
echo "Service: $SERVICE_NAME"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Add the DNS records shown above to your domain registrar"
echo "2. Wait for DNS propagation (5-60 minutes)"
echo "3. Wait for SSL certificate provisioning (10-60 minutes)"
echo "4. Test your site: https://$DOMAIN"
echo ""
echo "=== VERIFICATION COMMANDS ==="
echo "Check SSL certificate status:"
echo "  gcloud compute ssl-certificates describe chatterfix-ssl --global"
echo ""
echo "Check domain mapping:"
echo "  gcloud run domain-mappings describe $DOMAIN --region=$REGION"
echo ""
echo "Test the deployment:"
echo "  curl -I https://$DOMAIN"
echo ""

# Cleanup
rm -f domain-mapping.yaml

echo_info "Setup script completed successfully!"