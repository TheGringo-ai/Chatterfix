#!/usr/bin/env python3
"""
ChatterFix Professional Blue Dashboard
Enhanced Enterprise Theme by Fix It Fred AI
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="ChatterFix CMMS - Professional Blue")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ChatterFix CMMS - Enterprise Platform</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Fix It Fred's Enhanced Enterprise Blue Theme */
        
        :root {
            --primary-blue: #032B44;
            --secondary-blue: #1A3C55;
            --accent-blue: #3498db;
            --text-light: #FFFFFF;
            --text-gray: #e1e5e9;
            --border-blue: #4a90e2;
            --success-green: #10b981;
            --warning-orange: #f59e0b;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Open Sans', Arial, sans-serif;
            background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
            color: var(--text-light);
            min-height: 100vh;
            padding: 20px;
            overflow-x: hidden;
        }
        
        .gradient-background {
            background-image: linear-gradient(to bottom, #032B44, #1A3C55);
        }
        
        .glassmorphism-effect {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        
        .header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 80px;
            display: flex;
            justify-content: center;
            align-items: center;
            background-image: linear-gradient(to bottom, #032B44, #1A3C55);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 1000;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            color: var(--text-light);
            font-size: 2.5em;
            font-weight: 300;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        
        .container {
            max-width: 1400px;
            margin: 100px auto 0;
            padding: 40px 20px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 35px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.05), transparent);
            transform: rotate(45deg);
            transition: all 0.6s ease;
            opacity: 0;
        }
        
        .card:hover::before {
            opacity: 1;
            transform: rotate(45deg) translate(50%, 50%);
        }
        
        .card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 15px 50px rgba(0,0,0,0.4);
            border-color: var(--accent-blue);
        }
        
        .card h3 {
            font-size: 2em;
            margin-bottom: 20px;
            color: var(--accent-blue);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .card p {
            color: var(--text-gray);
            line-height: 1.7;
            margin-bottom: 25px;
            font-size: 1.1em;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 10px rgba(255,255,255,0.3);
        }
        
        .status-online { 
            background: var(--success-green);
            box-shadow: 0 0 15px var(--success-green);
        }
        
        .status-warning { 
            background: var(--warning-orange);
            box-shadow: 0 0 15px var(--warning-orange);
        }
        
        .nav-links {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 25px;
        }
        
        .nav-link {
            color: var(--text-light);
            text-decoration: none;
            font-weight: 500;
            padding: 12px 24px;
            border-radius: 8px;
            border: 1px solid var(--accent-blue);
            background: rgba(52, 152, 219, 0.2);
            transition: all 0.3s ease;
            display: inline-block;
            font-size: 0.95em;
        }
        
        .nav-link:hover {
            background: var(--accent-blue);
            color: var(--primary-blue);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
        }
        
        .ai-assistant {
            background: linear-gradient(135deg, rgba(52, 152, 219, 0.3), rgba(26, 60, 85, 0.4));
            border: 2px solid var(--accent-blue);
            position: relative;
        }
        
        .ai-assistant::after {
            content: '🤖';
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 3em;
            opacity: 0.3;
        }
        
        .footer {
            text-align: center;
            margin-top: 60px;
            padding: 40px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .footer p {
            color: var(--text-gray);
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 2em; }
            .dashboard-grid { grid-template-columns: 1fr; }
            .container { margin-top: 90px; padding: 20px 10px; }
            .card { padding: 25px; }
        }
    </style>
</head>
<body class="gradient-background">
    <div class="header glassmorphism-effect">
        <h1>🔧 ChatterFix CMMS</h1>
    </div>
    
    <div class="container">
        <div class="dashboard-grid">
            <div class="card ai-assistant pulse">
                <h3>🤖 Fix It Fred AI</h3>
                <p><span class="status-indicator status-online"></span>Your intelligent maintenance assistant powered by advanced AI. Ready for troubleshooting, repairs, and technical guidance.</p>
                <div class="nav-links">
                    <a href="http://localhost:8005/health" class="nav-link">AI Health Check</a>
                    <a href="#" class="nav-link" onclick="testFixItFred()">Test AI Assistant</a>
                </div>
            </div>
            
            <div class="card glassmorphism-effect">
                <h3>📋 Work Orders</h3>
                <p><span class="status-indicator status-online"></span>Comprehensive work order management system. Track maintenance requests, assign technicians, and monitor progress.</p>
                <div class="nav-links">
                    <a href="/work-orders" class="nav-link">View All Orders</a>
                    <a href="/work-orders/new" class="nav-link">Create New Order</a>
                    <a href="/work-orders/active" class="nav-link">Active Jobs</a>
                </div>
            </div>
            
            <div class="card glassmorphism-effect">
                <h3>🏭 Asset Management</h3>
                <p><span class="status-indicator status-online"></span>Complete asset lifecycle management. Monitor equipment health, track maintenance history, and optimize performance.</p>
                <div class="nav-links">
                    <a href="/assets" class="nav-link">Asset Registry</a>
                    <a href="/assets/maintenance" class="nav-link">Maintenance Logs</a>
                    <a href="/assets/analytics" class="nav-link">Performance Analytics</a>
                </div>
            </div>
            
            <div class="card glassmorphism-effect">
                <h3>📦 Parts & Inventory</h3>
                <p><span class="status-indicator status-warning"></span>Smart inventory management with automated reordering. Track spare parts, manage stock levels, and optimize procurement.</p>
                <div class="nav-links">
                    <a href="/parts" class="nav-link">Current Inventory</a>
                    <a href="/parts/orders" class="nav-link">Purchase Orders</a>
                    <a href="/parts/suppliers" class="nav-link">Supplier Management</a>
                </div>
            </div>
            
            <div class="card glassmorphism-effect">
                <h3>📊 Analytics Dashboard</h3>
                <p><span class="status-indicator status-online"></span>Advanced analytics and reporting. KPI tracking, cost analysis, and predictive maintenance insights.</p>
                <div class="nav-links">
                    <a href="/analytics" class="nav-link">Live Dashboard</a>
                    <a href="/analytics/reports" class="nav-link">Custom Reports</a>
                    <a href="/analytics/predictions" class="nav-link">Predictive Analytics</a>
                </div>
            </div>
            
            <div class="card glassmorphism-effect">
                <h3>⚙️ System Administration</h3>
                <p><span class="status-indicator status-online"></span>Enterprise platform management. API documentation, system monitoring, and configuration settings.</p>
                <div class="nav-links">
                    <a href="/docs" class="nav-link">API Documentation</a>
                    <a href="/admin/system" class="nav-link">System Status</a>
                    <a href="/admin/users" class="nav-link">User Management</a>
                </div>
            </div>
        </div>
        
        <div class="footer glassmorphism-effect">
            <p>🤖 <strong>Powered by Fix It Fred AI</strong> • Enterprise-Grade CMMS Platform</p>
            <p>Professional Blue Theme • Designed for Fortune 500 Operations</p>
            <p>Enhanced Glassmorphism Effects • Enterprise Security Enabled</p>
        </div>
    </div>
    
    <script>
        async function testFixItFred() {
            try {
                const response = await fetch('http://localhost:8005/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: 'Fix It Fred, can you confirm the professional blue dashboard is working properly? How does it look?',
                        provider: 'ollama',
                        model: 'llama3.2:latest',
                        context: 'dashboard_validation'
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('🤖 Fix It Fred says:\\n\\n' + data.response.substring(0, 300) + '...');
                } else {
                    alert('❌ Fix It Fred AI connection failed');
                }
            } catch (error) {
                alert('❌ Error connecting to Fix It Fred: ' + error.message);
            }
        }
        
        // Auto-test Fix It Fred on page load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                console.log('🤖 Fix It Fred Professional Blue Dashboard loaded successfully!');
            }, 1000);
        });
    </script>
</body>
</html>
    """

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "ChatterFix CMMS Professional Blue", 
        "theme": "Fix It Fred Enterprise Blue",
        "features": ["Glassmorphism", "Gradient Backgrounds", "Backdrop Filter"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)