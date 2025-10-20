#!/usr/bin/env python3
"""
Simple mobile server to serve the chat interface
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Mobile Chat Server")

@app.get("/", response_class=HTMLResponse)
async def mobile_chat():
    """Serve the mobile chat interface"""
    # Read the HTML file
    html_path = "mobile_chat.html"
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Mobile Chat Not Found</h1>
                <p>mobile_chat.html file is missing!</p>
            </body>
        </html>
        """)

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "mobile_server"}

if __name__ == "__main__":
    import uvicorn
    print("📱 Mobile Chat Server Starting...")
    print("🔗 Access from iPhone: http://your-ip:8008")
    uvicorn.run(app, host="0.0.0.0", port=8008)