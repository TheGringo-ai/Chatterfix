#!/bin/bash
set -e

echo "🔧 Fix ChatterFix VM - Simple Direct Approach"
echo "=============================================="

VM_IP="35.237.149.25"

# Create a simple web server to upload our app
echo "📦 Creating upload server..."
cat > upload_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import cgi
import os
import base64
import json
from urllib.parse import parse_qs

class UploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/upload':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                filename = data['filename']
                content = base64.b64decode(data['content']).decode('utf-8')
                
                with open(filename, 'w') as f:
                    f.write(content)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
                print(f"✅ Uploaded: {filename}")
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                print(f"❌ Upload failed: {e}")

PORT = 8888
with socketserver.TCPServer(("", PORT), UploadHandler) as httpd:
    print(f"🌐 Upload server at http://localhost:{PORT}")
    httpd.serve_forever()
EOF

# Start upload server in background
python3 upload_server.py &
UPLOAD_PID=$!
sleep 2

echo "📤 Uploading ChatterFix to VM..."

# Encode and upload the simple app
python3 -c "
import base64
import json
import requests

# Read the simple app
with open('simple-chatterfix.py', 'r') as f:
    app_content = f.read()

# Encode it
encoded = base64.b64encode(app_content.encode()).decode()

# Upload payload
payload = {
    'filename': 'chatterfix_app.py',
    'content': encoded
}

# Try to upload
try:
    response = requests.post('http://localhost:8888/upload', json=payload, timeout=5)
    print(f'Upload result: {response.status_code}')
except Exception as e:
    print(f'Upload failed: {e}')
"

# Kill upload server
kill $UPLOAD_PID 2>/dev/null || true

echo "🚀 Starting ChatterFix on VM..."

# Create startup command
cat > start_chatterfix.sh << 'EOF'
#!/bin/bash
cd /home/yoyofred_gringosgambit_com
pkill -f chatterfix_app.py || true
nohup python3 chatterfix_app.py > chatterfix.log 2>&1 &
echo "ChatterFix started on port 8080"
sleep 2
curl -s http://localhost:8080/health || echo "Health check failed"
EOF

chmod +x start_chatterfix.sh

echo "📋 Manual Steps (since SSH is locked):"
echo "1. Copy simple-chatterfix.py to your VM as chatterfix_app.py"
echo "2. Run: python3 chatterfix_app.py"
echo "3. Access: http://35.237.149.25:8080"

echo ""
echo "🔧 Quick Fix Commands for VM:"
echo "sudo pkill -f python3"
echo "cd /home/yoyofred_gringosgambit_com"
echo "python3 -m pip install fastapi uvicorn"
echo "python3 chatterfix_app.py"

echo ""
echo "✅ ChatterFix deployment package ready!"
echo "📁 Files created:"
echo "   - simple-chatterfix.py (main app)"
echo "   - start_chatterfix.sh (startup script)"

# Test if we can reach the VM
echo ""
echo "🩺 Testing VM connectivity..."
if curl -s --connect-timeout 5 http://$VM_IP > /dev/null; then
    echo "✅ VM is reachable"
else
    echo "❌ VM not responding - check if it's running"
fi