#!/bin/bash
# Quick update script for live changes

echo "🔄 Quick Update to ChatterFix VM"
echo "================================"

# Check if file argument provided
if [ -z "$1" ]; then
    echo "Usage: ./quick-update.sh <file-to-update>"
    echo "Example: ./quick-update.sh app.py"
    exit 1
fi

FILE=$1
VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"

if [ ! -f "$FILE" ]; then
    echo "❌ File $FILE not found"
    exit 1
fi

echo "📁 Uploading $FILE to VM..."
gcloud compute scp "$FILE" "$VM_NAME:/tmp/$FILE" --zone="$ZONE"

echo "🔄 Updating file on VM..."
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="
    sudo cp /tmp/$FILE /opt/chatterfix-cmms/current/$FILE
    sudo chown chatterfix:chatterfix /opt/chatterfix-cmms/current/$FILE
    sudo systemctl restart chatterfix-cmms
    echo '✅ Service restarted with new $FILE'
"

echo "🩺 Checking health..."
sleep 5
VM_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
curl -s "http://$VM_IP:8000/health" | head -3

echo "✅ Quick update complete!"
echo "🌐 Check: http://$VM_IP or chatterfix.com"