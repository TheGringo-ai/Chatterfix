#!/usr/bin/env python3
"""
Simple HTTP server to test the asset management UI
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import webbrowser
import threading
import time

class AssetTestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/assets' or self.path == '/assets/':
            # Serve the assets management HTML
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            with open('templates/assets_management.html', 'r') as f:
                content = f.read()
            
            self.wfile.write(content.encode())
        else:
            super().do_GET()

def start_test_server():
    """Start a simple test server for the asset management UI"""
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, AssetTestHandler)
    
    print("Test server starting on http://localhost:8000")
    print("Asset management UI: http://localhost:8000/assets")
    print("Backend API running on http://localhost:8080")
    
    # Open browser automatically
    def open_browser():
        time.sleep(1)
        webbrowser.open('http://localhost:8000/assets')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down test server...")
        httpd.shutdown()

if __name__ == '__main__':
    start_test_server()