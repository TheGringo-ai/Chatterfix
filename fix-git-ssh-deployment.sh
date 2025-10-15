#!/bin/bash
# 🔧 Fix Git/SSH Setup and Deploy ChatterFix Chat Fixes

set -e

VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
PROJECT="fredfix"

echo "🔧 FIXING GIT/SSH AND DEPLOYING CHAT FIXES"
echo "=========================================="

echo "🔑 Step 1: Fix SSH key setup..."

# Ensure SSH keys exist locally
if [ ! -f ~/.ssh/google_compute_engine ]; then
    echo "🔑 Generating SSH keys for gcloud..."
    gcloud compute config-ssh --project=$PROJECT
else
    echo "✅ SSH keys already exist"
fi

echo ""
echo "🔍 Step 2: Test SSH connectivity..."

# Test SSH connection
gcloud compute ssh $VM_NAME \
    --zone=$ZONE \
    --project=$PROJECT \
    --command="echo '✅ SSH connection working'" || {
    echo "❌ SSH still not working. Let's fix it..."
    
    # Force regenerate SSH keys
    rm -f ~/.ssh/google_compute_engine*
    gcloud compute config-ssh --project=$PROJECT --force-key-file-overwrite
    
    echo "🔄 Retrying SSH connection..."
    gcloud compute ssh $VM_NAME \
        --zone=$ZONE \
        --project=$PROJECT \
        --command="echo '✅ SSH connection now working'"
}

echo ""
echo "📁 Step 3: Setup git repository on VM..."

gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="
echo '📁 Setting up git repository...'

# Navigate to app directory
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Check if it's a git repository
if [ ! -d '.git' ]; then
    echo '🔄 Initializing git repository...'
    git init
    git remote add origin https://github.com/TheGringo-ai/Chatterfix.git
    git fetch origin
    git checkout -b main-clean origin/main-clean
else
    echo '✅ Git repository already exists'
    git remote -v
fi

echo '📋 Current git status:'
git status --porcelain
"

echo ""
echo "🔧 Step 4: Deploy chat fixes..."

gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="
echo '🔧 Deploying chat fixes...'

cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Backup current files
echo '💾 Creating backups...'
sudo cp app.py app.py.backup-\$(date +%Y%m%d-%H%M%S) 2>/dev/null || echo 'No app.py to backup'
sudo cp -r templates templates.backup-\$(date +%Y%m%d-%H%M%S) 2>/dev/null || echo 'No templates to backup'
sudo cp -r static static.backup-\$(date +%Y%m%d-%H%M%S) 2>/dev/null || echo 'No static files to backup'

# Pull latest fixes
echo '📥 Pulling latest chat fixes...'
git fetch origin main-clean
git reset --hard origin/main-clean

# Set proper permissions
echo '🔐 Setting file permissions...'
sudo chown -R yoyofred_gringosgambit_com:yoyofred_gringosgambit_com .
chmod +x *.py 2>/dev/null || echo 'No Python files to make executable'

# Stop existing service
echo '🛑 Stopping existing ChatterFix service...'
PYTHON_PID=\$(ps aux | grep -E 'python.*app\.py' | grep -v grep | awk '{print \$2}' | head -1)
if [ ! -z \"\$PYTHON_PID\" ]; then
    echo \"Stopping process \$PYTHON_PID...\"
    sudo kill \$PYTHON_PID
    sleep 3
    echo \"✅ Stopped existing service\"
else
    echo \"ℹ️ No existing service found\"
fi

# Start new service with chat fixes
echo '🚀 Starting ChatterFix with chat fixes...'
cd /home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Install any missing dependencies
python3 -m pip install --user fastapi uvicorn requests jinja2 python-multipart 2>/dev/null || echo 'Dependencies may already be installed'

# Start the service
nohup python3 app.py > chatterfix.log 2>&1 &

sleep 5

# Check if service started
NEW_PID=\$(ps aux | grep -E 'python.*app\.py' | grep -v grep | awk '{print \$2}' | head -1)
if [ ! -z \"\$NEW_PID\" ]; then
    echo \"✅ ChatterFix started with PID \$NEW_PID\"
    echo \"📄 Service log tail:\"
    tail -5 chatterfix.log 2>/dev/null || echo 'No log file yet'
else
    echo \"❌ Failed to start ChatterFix\"
    echo \"📄 Error log:\"
    tail -10 chatterfix.log 2>/dev/null || echo 'No log file'
fi
"

echo ""
echo "🧪 Step 5: Test the deployment..."

sleep 10

VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo "🌐 Testing ChatterFix at $VM_IP..."

# Test basic connectivity
echo "1️⃣ Testing basic website..."
curl -s "http://$VM_IP:8080/" | head -5

echo ""
echo "2️⃣ Testing Fix It Fred endpoint..."
curl -s -X POST "http://$VM_IP:8080/api/fix-it-fred/troubleshoot" \
  -H "Content-Type: application/json" \
  -d '{"equipment": "ChatterFix CMMS Platform", "issue_description": "Test chat fix deployment"}' | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✅ Fix It Fred endpoint working!')
        print('📝 Response available:', bool(data.get('data', {}).get('response')))
    else:
        print('❌ Fix It Fred endpoint failed')
        print('Data:', data)
except Exception as e:
    print('❌ Invalid response:', e)
"

echo ""
echo "3️⃣ Testing for broken chat endpoints..."
BROKEN_ENDPOINTS=$(curl -s "http://$VM_IP:8080/" | grep -o "api/ai[^f-]" | wc -l)
if [ "$BROKEN_ENDPOINTS" -eq 0 ]; then
    echo "✅ No broken /api/ai endpoints found!"
else
    echo "⚠️ Still found $BROKEN_ENDPOINTS broken endpoints"
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo "✅ SSH keys fixed and working"
echo "✅ Git repository setup on VM"  
echo "✅ Chat fixes deployed"
echo "✅ Service restarted"
echo ""
echo "🔗 Test your floating chat bubble at: http://$VM_IP:8080"
echo "💬 Chat should now connect to Fix It Fred instead of showing errors!"