#!/usr/bin/env python3
"""
ChatterFix CMMS - UI Gateway Service
Clean microservices gateway with Universal AI styling
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix CMMS UI Gateway", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Microservice URLs
SERVICES = {
    "database": "https://chatterfix-database-650169261019.us-central1.run.app",
    "work_orders": "https://chatterfix-work-orders-650169261019.us-central1.run.app", 
    "assets": "https://chatterfix-assets-650169261019.us-central1.run.app",
    "parts": "https://chatterfix-parts-650169261019.us-central1.run.app",
    "ai_brain": "https://chatterfix-ai-brain-650169261019.us-central1.run.app"
}

@app.get("/health")
async def health_check():
    """Health check that tests all microservices"""
    status = {"status": "healthy", "service": "ui-gateway", "microservices": {}}
    
    async with httpx.AsyncClient() as client:
        for service_name, url in SERVICES.items():
            try:
                response = await client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    status["microservices"][service_name] = {
                        "status": "healthy",
                        "url": url
                    }
                else:
                    status["microservices"][service_name] = {
                        "status": "error",
                        "code": response.status_code,
                        "url": url
                    }
            except Exception as e:
                status["microservices"][service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "url": url
                }
    
    return status

@app.get("/", response_class=HTMLResponse)
async def main_dashboard():
    """Main ChatterFix CMMS Dashboard with Universal AI styling"""
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS - Universal AI Command Center</title>
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
            background-attachment: fixed;
            color: white;
            min-height: 100vh;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, #eee, transparent),
                radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.5), transparent),
                radial-gradient(1px 1px at 90px 40px, #fff, transparent),
                radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.3), transparent),
                radial-gradient(2px 2px at 160px 120px, #fff, transparent);
            background-repeat: repeat;
            background-size: 200px 150px;
            z-index: -1;
            opacity: 0.3;
        }
        .header {
            background: rgba(0,0,0,0.3);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            background: linear-gradient(45deg, #4CAF50, #2196F3, #f39c12);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .service-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            cursor: pointer;
            text-align: center;
        }
        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
            background: rgba(76, 175, 80, 0.1);
        }
        .service-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .service-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #4CAF50;
        }
        .service-description {
            color: #ccc;
            line-height: 1.5;
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #4CAF50;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
            margin-top: 1rem;
        }
        .footer {
            margin-top: 4rem;
            padding: 2rem;
            text-align: center;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #888;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 ChatterFix CMMS</h1>
    </div>
    
    <div class="container">
        <div class="dashboard">
            <div class="service-card" onclick="window.open('/work-orders', '_blank')">
                <div class="service-icon">🛠️</div>
                <div class="service-title">Work Orders</div>
                <div class="service-description">Complete work order management with AI scheduling and optimization</div>
                <div class="status-badge">✅ Live</div>
            </div>
            
            <div class="service-card" onclick="window.open('/assets', '_blank')">
                <div class="service-icon">🏭</div>
                <div class="service-title">Assets</div>
                <div class="service-description">Asset lifecycle management with predictive maintenance insights</div>
                <div class="status-badge">✅ Live</div>
            </div>
            
            <div class="service-card" onclick="window.open('/parts', '_blank')">
                <div class="service-icon">🔧</div>
                <div class="service-title">Parts Inventory</div>
                <div class="service-description">Smart inventory management with automated procurement workflows</div>
                <div class="status-badge">✅ Live</div>
            </div>
            
            <div class="service-card" onclick="window.open('/pm-scheduling', '_blank')">
                <div class="service-icon">📅</div>
                <div class="service-title">PM Scheduling</div>
                <div class="service-description">Preventive maintenance scheduling with AI-powered optimization</div>
                <div class="status-badge">✅ Live</div>
            </div>
            
            <div class="service-card" onclick="window.open('/ai-brain', '_blank')">
                <div class="service-icon">🧠</div>
                <div class="service-title">AI Brain</div>
                <div class="service-description">Advanced AI with multi-provider orchestration and analytics</div>
                <div class="status-badge">✅ Live</div>
            </div>
            
            <div class="service-card" onclick="checkMicroservicesHealth()">
                <div class="service-icon">📊</div>
                <div class="service-title">System Health</div>
                <div class="service-description">Real-time monitoring of all microservices and system status</div>
                <div class="status-badge">🔄 Check Status</div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>🤖 ChatterFix CMMS - Powered by Universal AI Command Center</p>
        <p>Microservices Architecture | Cloud-Native | AI-Enhanced</p>
    </div>
    
    <script>
        async function checkMicroservicesHealth() {
            try {
                const response = await fetch('/health');
                const health = await response.json();
                
                let statusMessage = 'Microservices Status:\\n\\n';
                for (const [service, status] of Object.entries(health.microservices)) {
                    const statusIcon = status.status === 'healthy' ? '✅' : '❌';
                    statusMessage += `${statusIcon} ${service}: ${status.status}\\n`;
                }
                
                alert(statusMessage);
            } catch (error) {
                alert('Error checking health: ' + error.message);
            }
        }
        
        // Auto-check health on load
        window.addEventListener('load', () => {
            console.log('ChatterFix CMMS UI Gateway loaded successfully');
        });
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html_content)

# Proxy routes to microservices
@app.get("/work-orders")
async def work_orders_proxy():
    """Proxy to work orders service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['work_orders']}/", timeout=10.0)
            return HTMLResponse(content=response.text)
        except Exception as e:
            return HTMLResponse(content=f"<h1>Work Orders Service Unavailable</h1><p>Error: {str(e)}</p>")

@app.get("/assets")
async def assets_proxy():
    """Proxy to assets service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['assets']}/", timeout=10.0)
            return HTMLResponse(content=response.text)
        except Exception as e:
            return HTMLResponse(content=f"<h1>Assets Service Unavailable</h1><p>Error: {str(e)}</p>")

@app.get("/parts")
async def parts_proxy():
    """Proxy to parts service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['parts']}/", timeout=10.0)
            return HTMLResponse(content=response.text)
        except Exception as e:
            return HTMLResponse(content=f"<h1>Parts Service Unavailable</h1><p>Error: {str(e)}</p>")

@app.get("/ai-brain")
async def ai_brain_proxy():
    """Proxy to AI brain service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['ai_brain']}/", timeout=10.0)
            return HTMLResponse(content=response.text)
        except Exception as e:
            return HTMLResponse(content=f"<h1>AI Brain Service Unavailable</h1><p>Error: {str(e)}</p>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)