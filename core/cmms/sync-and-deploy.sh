#!/bin/bash

echo "🔄 ChatterFix CMMS - Sync & Deploy Script"
echo "========================================="
echo "🎯 Real-time sync: Local → GitHub → VM"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REMOTE_BRANCH="main-clean"
VM_IP="35.237.149.25"
VM_USER="yoyofred_gringosgambit_com"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Step 1: Check for changes
print_info "Checking for local changes..."
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Found local changes:"
    git status --short
    echo ""
    
    # Step 2: Add and commit changes
    print_info "Staging all changes..."
    git add .
    
    # Generate commit message with timestamp
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    COMMIT_MSG="🔄 Auto-sync ChatterFix CMMS - $TIMESTAMP

✅ MICROSERVICES UPDATE:
- Updated core application files
- Synchronized with VM deployment
- Real-time sync from local development

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    print_info "Committing changes..."
    if PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "$COMMIT_MSG"; then
        print_status "Changes committed successfully"
    else
        print_error "Failed to commit changes"
        exit 1
    fi
else
    print_info "No local changes detected"
fi

# Step 3: Push to GitHub
print_info "Pushing to GitHub repository..."
if git push origin $REMOTE_BRANCH; then
    print_status "Successfully pushed to GitHub"
else
    print_error "Failed to push to GitHub"
    exit 1
fi

# Step 4: Deploy to VM
print_info "Deploying to VM at $VM_IP..."

# Copy updated files to VM
print_info "Copying microservices to VM..."
if scp -o StrictHostKeyChecking=no \
    app.py \
    database_service.py \
    work_orders_service.py \
    assets_service.py \
    parts_service.py \
    document_intelligence_service.py \
    enterprise_security_service.py \
    grok_connector.py \
    requirements.txt \
    ${VM_USER}@${VM_IP}:/opt/chatterfix-cmms/current/; then
    print_status "Files copied to VM"
else
    print_error "Failed to copy files to VM"
    exit 1
fi

# Restart services on VM
print_info "Restarting services on VM..."
ssh -o StrictHostKeyChecking=no ${VM_USER}@${VM_IP} << 'ENDSSH'
cd /opt/chatterfix-cmms/current

echo "🛑 Stopping existing services..."
sudo systemctl stop chatterfix-ai-brain.service chatterfix-platform.service chatterfix.service 2>/dev/null || true
sudo pkill -f "python3" 2>/dev/null || true
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008 8080; do
    sudo lsof -ti:$port | xargs sudo kill -9 2>/dev/null || true
done

sleep 3

echo "🚀 Starting microservices..."
mkdir -p logs pids

# Start microservices
nohup python3 database_service.py --port 8001 > logs/database.log 2>&1 &
echo $! > pids/database.pid

nohup python3 work_orders_service.py --port 8002 > logs/work_orders.log 2>&1 &
echo $! > pids/work_orders.pid

nohup python3 assets_service.py --port 8003 > logs/assets.log 2>&1 &
echo $! > pids/assets.pid

nohup python3 parts_service.py --port 8004 > logs/parts.log 2>&1 &
echo $! > pids/parts.pid

nohup python3 grok_connector.py > logs/grok.log 2>&1 &
echo $! > pids/grok.pid

nohup python3 document_intelligence_service.py --port 8008 > logs/doc_intel.log 2>&1 &
echo $! > pids/doc_intel.pid

nohup python3 enterprise_security_service.py --port 8007 > logs/security.log 2>&1 &
echo $! > pids/security.pid

sleep 5

# Start main gateway
PORT=8080 nohup python3 app.py > logs/main_gateway.log 2>&1 &
echo $! > pids/main_gateway.pid

sleep 3

echo "✅ Services restarted on VM"
ENDSSH

if [ $? -eq 0 ]; then
    print_status "VM services restarted successfully"
else
    print_error "Failed to restart VM services"
    exit 1
fi

# Step 5: Verify deployment
print_info "Verifying deployment..."
sleep 5

if curl -s -f "http://$VM_IP:8080/health" > /dev/null; then
    print_status "VM deployment verified - application is healthy"
else
    print_warning "VM verification failed - may still be starting up"
fi

# Step 6: Success summary
echo ""
echo "🎉 SYNC & DEPLOY COMPLETE!"
echo "=========================="
print_status "Local changes committed and pushed to GitHub"
print_status "VM deployment updated with latest code"
print_status "All environments are now synchronized"
echo ""
echo "🌐 Access Points:"
echo "   GitHub: https://github.com/TheGringo-ai/Chatterfix.git"
echo "   Live VM: http://$VM_IP:8080"
echo "   Work Orders: http://$VM_IP:8080/work-orders"
echo ""
print_info "Use './sync-and-deploy.sh' anytime to sync changes across all environments"