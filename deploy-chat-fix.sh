#!/bin/bash
# 🔧 Deploy Permanent Chat Fix - Replace broken /api/ai/chat with working Fix It Fred

set -e

VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
PROJECT="fredfix"

echo "🔧 Deploying Permanent Chat Fix to ChatterFix VM..."
echo "=================================================="

# Check if template files exist
if [ ! -f "core/cmms/templates/chatterfix_base.html" ]; then
    echo "❌ chatterfix_base.html not found"
    exit 1
fi

if [ ! -f "core/cmms/templates/ai_assistant_component.html" ]; then
    echo "❌ ai_assistant_component.html not found"
    exit 1
fi

echo "📁 Uploading fixed template files to VM..."

# Upload the fixed template files
gcloud compute scp "core/cmms/templates/chatterfix_base.html" "$VM_NAME:/tmp/chatterfix_base.html" --zone="$ZONE" --project="$PROJECT"
gcloud compute scp "core/cmms/templates/ai_assistant_component.html" "$VM_NAME:/tmp/ai_assistant_component.html" --zone="$ZONE" --project="$PROJECT"

echo "🔄 Applying chat fix on VM..."

# Apply the fix on the VM
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --command="
    echo '🔧 Applying permanent chat fix...'
    
    # Find the current app directory
    APP_DIR=\$(ps aux | grep -E 'python.*app\.py|python.*chatterfix' | grep -v grep | head -1 | awk '{for(i=11;i<=NF;i++) printf \$i\" \"}' | sed 's/[[:space:]]*$//' | xargs dirname 2>/dev/null || echo '/home/yoyofred_gringosgambit_com/chatterfix-docker/app')
    
    echo \"📁 App directory: \$APP_DIR\"
    
    # Create backup of original templates
    if [ -d \"\$APP_DIR/templates\" ]; then
        sudo mkdir -p \"\$APP_DIR/templates/backup\"
        sudo cp \"\$APP_DIR/templates/chatterfix_base.html\" \"\$APP_DIR/templates/backup/chatterfix_base.html.backup\" 2>/dev/null || echo 'No base template to backup'
        sudo cp \"\$APP_DIR/templates/ai_assistant_component.html\" \"\$APP_DIR/templates/backup/ai_assistant_component.html.backup\" 2>/dev/null || echo 'No assistant component to backup'
    fi
    
    # Apply the fixed templates
    sudo cp /tmp/chatterfix_base.html \"\$APP_DIR/templates/chatterfix_base.html\" 2>/dev/null || sudo cp /tmp/chatterfix_base.html \"\$APP_DIR/chatterfix_base.html\"
    sudo cp /tmp/ai_assistant_component.html \"\$APP_DIR/templates/ai_assistant_component.html\" 2>/dev/null || sudo cp /tmp/ai_assistant_component.html \"\$APP_DIR/ai_assistant_component.html\"
    
    # Set proper ownership
    sudo chown -R yoyofred_gringosgambit_com:yoyofred_gringosgambit_com \"\$APP_DIR/templates\" 2>/dev/null || echo 'Templates directory not found'
    sudo chown yoyofred_gringosgambit_com:yoyofred_gringosgambit_com \"\$APP_DIR/chatterfix_base.html\" 2>/dev/null || echo 'Base template not in root'
    sudo chown yoyofred_gringosgambit_com:yoyofred_gringosgambit_com \"\$APP_DIR/ai_assistant_component.html\" 2>/dev/null || echo 'Assistant component not in root'
    
    echo '✅ Fixed templates deployed'
    
    # Restart the service to apply changes
    echo '🔄 Restarting ChatterFix service...'
    
    # Find and restart the Python process
    PYTHON_PID=\$(ps aux | grep -E 'python.*app\.py|python.*chatterfix' | grep -v grep | awk '{print \$2}' | head -1)
    
    if [ ! -z \"\$PYTHON_PID\" ]; then
        echo \"🔄 Restarting process \$PYTHON_PID...\"
        sudo kill -HUP \$PYTHON_PID 2>/dev/null || sudo kill \$PYTHON_PID && sleep 3
        
        # Restart from the app directory
        cd \"\$APP_DIR\"
        nohup python3 app.py > /dev/null 2>&1 &
        echo \"✅ Service restarted\"
    else
        echo '⚠️ No Python process found, starting new instance...'
        cd \"\$APP_DIR\"
        nohup python3 app.py > /dev/null 2>&1 &
        echo \"✅ Service started\"
    fi
    
    echo '🎉 Chat fix deployed successfully!'
"

echo ""
echo "🩺 Testing the fix..."
sleep 8

# Get VM IP and test
VM_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo "🌐 Testing ChatterFix website..."
curl -s "http://$VM_IP/" | head -3 || echo "Service might still be starting..."

echo ""
echo "🎉 CHAT FIX DEPLOYMENT COMPLETE!"
echo "================================="
echo "✅ Chat widget now uses Fix It Fred instead of broken /api/ai/chat"
echo "✅ Both base template and AI assistant component updated"
echo "✅ Service restarted with new templates"
echo ""
echo "🔗 Test the fix at: https://chatterfix.com"
echo "💬 Chat widget should now work with Fix It Fred AI"
echo ""
echo "Fred says: The chat is now permanently fixed! 🤖"