#!/usr/bin/env python3
"""
ChatterFix CMMS - Status Dashboard
Shows current deployment status and working services
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import asyncio

app = FastAPI(title="ChatterFix CMMS Status")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
async def status_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 ChatterFix CMMS - Restoration Status</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .header { text-align: center; margin-bottom: 3rem; }
            .header h1 { font-size: 3rem; margin-bottom: 1rem; }
            .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-bottom: 3rem; }
            .status-card { background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2); }
            .status-card h3 { margin-bottom: 1rem; font-size: 1.5rem; }
            .status { padding: 0.5rem 1rem; border-radius: 25px; font-weight: bold; display: inline-block; margin-bottom: 1rem; }
            .status.healthy { background: #28a745; }
            .status.warning { background: #ffc107; color: #333; }
            .status.error { background: #dc3545; }
            .features { background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2); }
            .features h2 { margin-bottom: 1.5rem; text-align: center; }
            .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; }
            .feature { background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 10px; }
            .competitive { background: rgba(0,255,0,0.1); border-left: 4px solid #28a745; padding: 1.5rem; margin: 2rem 0; border-radius: 8px; }
            .pulse { animation: pulse 2s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
        </style>
        <script>
            async function checkServices() {
                const services = [
                    { name: 'Database', url: 'https://chatterfix-database-650169261019.us-central1.run.app/health' },
                    { name: 'Assets', url: 'https://chatterfix-assets-650169261019.us-central1.run.app/health' },
                    { name: 'Parts', url: 'https://chatterfix-parts-650169261019.us-central1.run.app/health' },
                    { name: 'Work Orders', url: 'https://chatterfix-work-orders-650169261019.us-central1.run.app/health' }
                ];
                
                for (let service of services) {
                    try {
                        const response = await fetch(service.url);
                        const statusEl = document.getElementById(service.name.toLowerCase().replace(' ', '-') + '-status');
                        if (response.ok) {
                            statusEl.className = 'status healthy';
                            statusEl.textContent = '✅ Healthy';
                        } else {
                            statusEl.className = 'status warning';
                            statusEl.textContent = '⚠️ Issues';
                        }
                    } catch (error) {
                        const statusEl = document.getElementById(service.name.toLowerCase().replace(' ', '-') + '-status');
                        statusEl.className = 'status error';
                        statusEl.textContent = '❌ Down';
                    }
                }
            }
            
            // Check services on load and every 30 seconds
            document.addEventListener('DOMContentLoaded', checkServices);
            setInterval(checkServices, 30000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 ChatterFix CMMS</h1>
                <p>PostgreSQL-Powered CMMS Platform - Restoration in Progress</p>
            </div>
            
            <div class="competitive">
                <h3>🎯 Competitive Status vs UpKeep & MaintainX</h3>
                <p><strong>✅ PostgreSQL Database:</strong> Production-grade database restored and operational</p>
                <p><strong>✅ Microservices Architecture:</strong> Scalable, enterprise-ready infrastructure</p>
                <p><strong>✅ Cost Optimization:</strong> 90% cheaper than competitors ($5-25/user vs $50-200)</p>
                <p><strong>✅ AI-First Approach:</strong> Built-in predictive maintenance and optimization</p>
            </div>
            
            <div class="status-grid">
                <div class="status-card">
                    <h3>📊 Database Service</h3>
                    <div id="database-status" class="status pulse">🔄 Checking...</div>
                    <p>PostgreSQL database with all tables initialized</p>
                    <p><small>URL: chatterfix-database-*.run.app</small></p>
                </div>
                
                <div class="status-card">
                    <h3>🏭 Assets Service</h3>
                    <div id="assets-status" class="status pulse">🔄 Checking...</div>
                    <p>Complete asset lifecycle management</p>
                    <p><small>URL: chatterfix-assets-*.run.app</small></p>
                </div>
                
                <div class="status-card">
                    <h3>🔧 Parts Service</h3>
                    <div id="parts-status" class="status pulse">🔄 Checking...</div>
                    <p>Smart inventory management</p>
                    <p><small>URL: chatterfix-parts-*.run.app</small></p>
                </div>
                
                <div class="status-card">
                    <h3>🛠️ Work Orders Service</h3>
                    <div id="work-orders-status" class="status pulse">🔄 Checking...</div>
                    <p>Complete work order lifecycle</p>
                    <p><small>URL: chatterfix-work-orders-*.run.app</small></p>
                </div>
            </div>
            
            <div class="features">
                <h2>🎯 Competitive Advantages Over UpKeep & MaintainX</h2>
                <div class="feature-grid">
                    <div class="feature">
                        <h4>💰 Cost Leadership</h4>
                        <p>$5-25/user/month vs competitors' $50-200/user/month</p>
                    </div>
                    <div class="feature">
                        <h4>🤖 AI-First Design</h4>
                        <p>Built-in predictive maintenance, not an afterthought</p>
                    </div>
                    <div class="feature">
                        <h4>🗣️ Natural Language</h4>
                        <p>Voice and chat-based work order creation</p>
                    </div>
                    <div class="feature">
                        <h4>📱 Multi-Modal Input</h4>
                        <p>Photos, voice, text, IoT sensor integration</p>
                    </div>
                    <div class="feature">
                        <h4>⚡ Real-Time Intelligence</h4>
                        <p>Live asset monitoring and predictive alerts</p>
                    </div>
                    <div class="feature">
                        <h4>🏢 SMB Focus</h4>
                        <p>Enterprise features at small business prices</p>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 3rem; padding: 2rem; background: rgba(255,255,255,0.1); border-radius: 15px;">
                <h3>🚀 Platform Status: Restoration Complete</h3>
                <p>PostgreSQL database restored with microservices architecture.</p>
                <p>Ready to dominate the CMMS market!</p>
                <p style="margin-top: 1rem; opacity: 0.8;">
                    <strong>Next:</strong> Full UI deployment and feature enhancement
                </p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ChatterFix CMMS Status"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)