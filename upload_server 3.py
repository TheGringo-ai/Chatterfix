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
