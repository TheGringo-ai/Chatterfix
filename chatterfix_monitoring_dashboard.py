#!/usr/bin/env python3
"""
ChatterFix CMMS - Comprehensive Monitoring Dashboard
Phase 1: Foundation Solidification - Never Go Off Track
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(
    title="ChatterFix Monitoring Dashboard",
    description="Comprehensive monitoring to prevent going off track",
    version="1.0.0"
)

# Services to monitor
MONITORED_SERVICES = {
    "platform_gateway": {
        "url": "http://localhost:8000",
        "critical": True,
        "expected_response_time": 200,
        "role": "API Gateway"
    },
    "database_service": {
        "url": "http://localhost:8001", 
        "critical": True,
        "expected_response_time": 100,
        "role": "Data Management"
    },
    "work_orders": {
        "url": "http://localhost:8002",
        "critical": True,
        "expected_response_time": 150,
        "role": "Work Order Management"
    },
    "assets": {
        "url": "http://localhost:8003",
        "critical": True,
        "expected_response_time": 150,
        "role": "Asset Tracking"
    },
    "parts": {
        "url": "http://localhost:8004",
        "critical": True,
        "expected_response_time": 150,
        "role": "Parts Inventory"
    },
    "enterprise_security": {
        "url": "http://localhost:8007",
        "critical": False,
        "expected_response_time": 300,
        "role": "Security & Compliance"
    },
    "ai_development_team": {
        "url": "http://localhost:8008",
        "critical": False,
        "expected_response_time": 500,
        "role": "Development Coordination"
    },
    "ai_self_healing": {
        "url": "http://localhost:8010",
        "critical": False,
        "expected_response_time": 200,
        "role": "System Monitoring"
    },
    "ai_brain": {
        "url": "http://localhost:9000",
        "critical": True,
        "expected_response_time": 1000,
        "role": "Predictive Intelligence"
    },
    "production_gateway": {
        "url": "http://35.237.149.25:8080",
        "critical": True,
        "expected_response_time": 500,
        "role": "Production ChatterFix"
    }
}

# Global monitoring state
monitoring_data = {
    "last_check": None,
    "service_status": {},
    "alerts": [],
    "performance_history": {},
    "system_health": "unknown"
}

async def check_service_health(service_name: str, service_config: Dict) -> Dict:
    """Check individual service health with response time"""
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{service_config['url']}/health", timeout=10) as response:
                response_time = (time.time() - start_time) * 1000  # ms
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "response_time": round(response_time, 2),
                        "details": data,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "response_time": round(response_time, 2),
                        "error": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
    except asyncio.TimeoutError:
        return {
            "status": "timeout",
            "response_time": 10000,  # timeout
            "error": "Request timeout",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unreachable",
            "response_time": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/monitor/status")
async def get_monitoring_status():
    """Get comprehensive monitoring status"""
    # Check all services
    service_results = {}
    alerts = []
    
    for service_name, service_config in MONITORED_SERVICES.items():
        result = await check_service_health(service_name, service_config)
        service_results[service_name] = result
        
        # Generate alerts for critical services
        if service_config["critical"]:
            if result["status"] != "healthy":
                alerts.append({
                    "severity": "critical",
                    "service": service_name,
                    "message": f"Critical service {service_name} is {result['status']}: {result.get('error', '')}",
                    "timestamp": datetime.now().isoformat()
                })
            elif result["response_time"] and result["response_time"] > service_config["expected_response_time"] * 2:
                alerts.append({
                    "severity": "warning",
                    "service": service_name,
                    "message": f"Service {service_name} response time high: {result['response_time']}ms",
                    "timestamp": datetime.now().isoformat()
                })
    
    # Calculate overall system health
    critical_services = [name for name, config in MONITORED_SERVICES.items() if config["critical"]]
    healthy_critical = [name for name in critical_services if service_results[name]["status"] == "healthy"]
    
    if len(healthy_critical) == len(critical_services):
        system_health = "healthy"
    elif len(healthy_critical) >= len(critical_services) * 0.8:
        system_health = "degraded"
    else:
        system_health = "critical"
    
    # Update global state
    monitoring_data.update({
        "last_check": datetime.now().isoformat(),
        "service_status": service_results,
        "alerts": alerts,
        "system_health": system_health
    })
    
    return {
        "system_health": system_health,
        "last_check": monitoring_data["last_check"],
        "services": service_results,
        "alerts": alerts,
        "summary": {
            "total_services": len(MONITORED_SERVICES),
            "healthy_services": len([s for s in service_results.values() if s["status"] == "healthy"]),
            "critical_services": len(critical_services),
            "healthy_critical": len(healthy_critical)
        }
    }

@app.get("/monitor/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard():
    """Rich HTML monitoring dashboard"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS - Monitoring Dashboard</title>
    <style>
        :root {
            --success: #00c851;
            --warning: #ff9800;
            --error: #f44336;
            --info: #2196f3;
            --bg-dark: #1a1a1a;
            --bg-card: #2d2d2d;
            --text-light: #ffffff;
            --text-muted: #b0b0b0;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', sans-serif;
            background: var(--bg-dark);
            color: var(--text-light);
            line-height: 1.6;
        }
        
        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(45deg, var(--success), var(--info));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .status-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            border-left: 4px solid var(--info);
        }
        
        .status-card.healthy { border-left-color: var(--success); }
        .status-card.warning { border-left-color: var(--warning); }
        .status-card.error { border-left-color: var(--error); }
        
        .service-name {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .service-role {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .metrics {
            display: flex;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        
        .metric {
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        
        .alerts {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid;
        }
        
        .alert.critical {
            background: rgba(244, 67, 54, 0.1);
            border-left-color: var(--error);
        }
        
        .alert.warning {
            background: rgba(255, 152, 0, 0.1);
            border-left-color: var(--warning);
        }
        
        .refresh-btn {
            background: var(--info);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
        }
        
        .refresh-btn:hover {
            background: #1976d2;
        }
        
        .system-status {
            text-align: center;
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 12px;
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        .system-status.healthy {
            background: rgba(0, 200, 81, 0.1);
            border: 2px solid var(--success);
            color: var(--success);
        }
        
        .system-status.degraded {
            background: rgba(255, 152, 0, 0.1);
            border: 2px solid var(--warning);
            color: var(--warning);
        }
        
        .system-status.critical {
            background: rgba(244, 67, 54, 0.1);
            border: 2px solid var(--error);
            color: var(--error);
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🎯 ChatterFix CMMS Monitoring</h1>
            <p>Real-time system health and performance monitoring</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Status</button>
        </div>
        
        <div class="system-status" id="systemStatus">
            Loading system status...
        </div>
        
        <div class="alerts" id="alertsSection">
            <h3>🚨 Active Alerts</h3>
            <div id="alertsList">Loading alerts...</div>
        </div>
        
        <div class="status-grid" id="servicesGrid">
            Loading services...
        </div>
    </div>

    <script>
        async function loadMonitoringData() {
            try {
                const response = await fetch('/monitor/status');
                const data = await response.json();
                
                // Update system status
                const systemStatus = document.getElementById('systemStatus');
                systemStatus.className = `system-status ${data.system_health}`;
                systemStatus.innerHTML = `
                    System Health: ${data.system_health.toUpperCase()}
                    <br><small>Last Updated: ${new Date(data.last_check).toLocaleString()}</small>
                `;
                
                // Update alerts
                const alertsList = document.getElementById('alertsList');
                if (data.alerts.length === 0) {
                    alertsList.innerHTML = '<p>✅ No active alerts</p>';
                } else {
                    alertsList.innerHTML = data.alerts.map(alert => `
                        <div class="alert ${alert.severity}">
                            <strong>${alert.severity.toUpperCase()}:</strong> ${alert.message}
                            <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                        </div>
                    `).join('');
                }
                
                // Update services grid
                const servicesGrid = document.getElementById('servicesGrid');
                servicesGrid.innerHTML = Object.entries(data.services).map(([name, status]) => `
                    <div class="status-card ${status.status === 'healthy' ? 'healthy' : 'error'}">
                        <div class="service-name">${name.replace('_', ' ').toUpperCase()}</div>
                        <div class="service-role">${getServiceRole(name)}</div>
                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-value ${getStatusColor(status.status)}">${status.status.toUpperCase()}</div>
                                <div class="metric-label">Status</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${status.response_time || 'N/A'}</div>
                                <div class="metric-label">Response (ms)</div>
                            </div>
                        </div>
                        ${status.error ? `<div style="color: var(--error); font-size: 0.9rem;">Error: ${status.error}</div>` : ''}
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Failed to load monitoring data:', error);
            }
        }
        
        function getServiceRole(serviceName) {
            const roles = {
                'platform_gateway': 'API Orchestration',
                'database_service': 'Data Management',
                'work_orders': 'Work Order Management',
                'assets': 'Asset Tracking',
                'parts': 'Inventory Management',
                'enterprise_security': 'Security & Compliance',
                'ai_development_team': 'Development Coordination',
                'ai_self_healing': 'System Monitoring',
                'ai_brain': 'Predictive Intelligence',
                'production_gateway': 'Production ChatterFix'
            };
            return roles[serviceName] || 'Unknown Service';
        }
        
        function getStatusColor(status) {
            return status === 'healthy' ? 'color: var(--success)' : 'color: var(--error)';
        }
        
        function refreshData() {
            loadMonitoringData();
        }
        
        // Load data on page load
        loadMonitoringData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadMonitoringData, 30000);
    </script>
</body>
</html>
"""

@app.get("/monitor/anti_drift")
async def anti_drift_check():
    """Anti-drift mechanism - ensures we stay on track"""
    
    # Check if core ChatterFix functionality is still working
    core_checks = {
        "chat_widget": False,
        "production_gateway": False,
        "microservices": False
    }
    
    try:
        # Test production chat widget
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://35.237.149.25:8080/api/chat",
                json={"message": "Health check test"},
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    core_checks["chat_widget"] = data.get("success", False)
    except:
        pass
    
    # Test production gateway
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://35.237.149.25:8080/health", timeout=10) as response:
                core_checks["production_gateway"] = response.status == 200
    except:
        pass
    
    # Test local microservices
    critical_services = ["work_orders", "assets", "parts", "ai_brain"]
    healthy_count = 0
    for service in critical_services:
        if service in MONITORED_SERVICES:
            result = await check_service_health(service, MONITORED_SERVICES[service])
            if result["status"] == "healthy":
                healthy_count += 1
    
    core_checks["microservices"] = healthy_count >= len(critical_services) * 0.75
    
    # Calculate drift risk
    working_systems = sum(core_checks.values())
    drift_risk = "low" if working_systems == 3 else "medium" if working_systems >= 2 else "high"
    
    return {
        "anti_drift_status": "monitoring",
        "drift_risk": drift_risk,
        "core_functionality": core_checks,
        "recommendations": [
            "Focus on maintaining current working features",
            "Complete Phase 1 objectives before advancing",
            "Monitor service health continuously",
            "Address any failing core systems immediately"
        ],
        "stay_on_track_metrics": {
            "chat_widget_operational": core_checks["chat_widget"],
            "production_stable": core_checks["production_gateway"],
            "microservices_healthy": core_checks["microservices"]
        }
    }

@app.get("/health")
async def health_check():
    """Health check for the monitoring service itself"""
    return {
        "status": "healthy",
        "service": "chatterfix-monitoring",
        "timestamp": datetime.now().isoformat(),
        "monitoring": f"{len(MONITORED_SERVICES)} services"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8889)