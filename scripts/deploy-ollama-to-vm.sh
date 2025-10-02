#!/bin/bash
# Deploy and configure Ollama on ChatterFix Production VM
# This script ensures Ollama runs on the VM, not locally

set -e

VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
PROJECT="fredfix"

echo "🚀 Deploying Ollama to production VM: $VM_NAME"

# Check if we can connect to VM
echo "🔍 Checking VM connectivity..."
if ! gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT >/dev/null 2>&1; then
    echo "❌ Cannot access VM $VM_NAME"
    exit 1
fi

echo "✅ VM is accessible"

# Copy the optimization script to VM
echo "📁 Copying Ollama optimization script to VM..."
gcloud compute scp scripts/optimize-ollama.sh $VM_NAME:/tmp/optimize-ollama.sh --zone=$ZONE --project=$PROJECT

# Execute the optimization script on VM
echo "🔧 Running Ollama optimization on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="
    chmod +x /tmp/optimize-ollama.sh
    echo '🤖 Starting Ollama setup on VM...'
    sudo /tmp/optimize-ollama.sh
    echo '✅ Ollama optimization complete on VM'
"

# Verify Ollama is running on VM
echo "🏥 Verifying Ollama service on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="
    echo '📊 Ollama service status:'
    sudo systemctl status ollama --no-pager || true
    echo ''
    echo '🔍 Testing Ollama API on VM:'
    curl -s http://localhost:11434/api/tags || echo 'Ollama API not yet responding'
    echo ''
    echo '🤖 Testing LLaMA model:'
    sudo -u ollama ollama list || echo 'Models not yet available'
"

# Update CMMS application to use VM Ollama
echo "🔄 Updating CMMS to use VM-based Ollama..."
gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="
    cd /opt/chatterfix-cmms
    echo '🔧 Updating Ollama URL configuration...'
    
    # Check if there's a config file to update
    if [ -f app.py ]; then
        # Update any localhost:11434 references to ensure they point to the VM
        sudo sed -i 's/localhost:11434/127.0.0.1:11434/g' app.py || true
        echo '✅ Updated app.py Ollama configuration'
    fi
    
    # Restart the CMMS service
    echo '🔄 Restarting CMMS service...'
    sudo systemctl restart chatterfix-cmms || true
    echo '✅ CMMS service restarted'
"

# Final verification
echo "🎯 Final verification..."
gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command="
    echo '🏥 Final health check:'
    
    # Check Ollama is responding
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo '✅ Ollama API is responding on VM'
    else
        echo '⚠️ Ollama API not responding - may need more time to start'
    fi
    
    # Check if LLaMA model is available
    if sudo -u ollama ollama list | grep -q llama; then
        echo '✅ LLaMA model is available on VM'
    else
        echo '📥 LLaMA model may still be downloading...'
    fi
    
    # Check CMMS service
    if systemctl is-active --quiet chatterfix-cmms; then
        echo '✅ CMMS service is running'
    else
        echo '⚠️ CMMS service needs attention'
    fi
"

echo ""
echo "🎉 Ollama deployment to VM complete!"
echo "🔗 Your AI assistant should now be using VM-based LLaMA"
echo "🌐 Test at: https://chatterfix.com"
echo ""
echo "📋 To monitor:"
echo "  - VM Ollama logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='journalctl -u ollama -f'"
echo "  - CMMS logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='journalctl -u chatterfix-cmms -f'"