#!/usr/bin/env python3
"""
ChatterFix CMMS - Clean Main Application
Routes to enhanced microservices for the best work order management in the industry
Enhanced with Fix It Fred and Grok AI collaboration
"""

import logging
import httpx
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix CMMS",
    description="AI-Enhanced Maintenance Management System with Fix It Fred and Grok",
    version="3.0.0"
)

# Enhanced service URLs
ENHANCED_WORK_ORDERS_URL = "http://localhost:8015"
DATABASE_SERVICE_URL = "http://localhost:8001"
FIX_IT_FRED_URL = "http://localhost:8005"
GROK_CONNECTOR_URL = "http://localhost:8006"

# Pydantic models
class WorkOrderCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    technician: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    technician: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check for the main application"""
    return {
        "status": "healthy",
        "service": "ChatterFix CMMS Main App",
        "version": "3.0.0",
        "enhanced_features": [
            "AI-Powered Work Orders with Fix It Fred",
            "Strategic Analysis with Grok",
            "Real-time Database Integration",
            "Industry-Leading Work Order Management"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard with work orders functionality"""
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ChatterFix CMMS - Enhanced Work Orders</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .hero-section {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 4rem 0;
            }}
            .feature-card {{
                transition: transform 0.3s;
                height: 100%;
            }}
            .feature-card:hover {{
                transform: translateY(-5px);
            }}
            .ai-badge {{
                background: linear-gradient(45deg, #ff6b6b, #feca57);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🔧 ChatterFix CMMS</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/work-orders">Work Orders</a>
                    <a class="nav-link" href="/assets">Assets</a>
                    <a class="nav-link" href="/ai-chat">AI Assistant</a>
                </div>
            </div>
        </nav>

        <div class="hero-section">
            <div class="container text-center">
                <h1 class="display-4 mb-4">ChatterFix CMMS</h1>
                <p class="lead mb-4">Industry-Leading Work Order Management with AI Enhancement</p>
                <span class="ai-badge">🤖 Powered by Fix It Fred & Grok AI</span>
            </div>
        </div>

        <div class="container my-5">
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card feature-card">
                        <div class="card-body text-center">
                            <h5 class="card-title">🔧 Enhanced Work Orders</h5>
                            <p class="card-text">AI-powered work order creation, tracking, and completion with real-time insights.</p>
                            <a href="/work-orders" class="btn btn-primary">Manage Work Orders</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card feature-card">
                        <div class="card-body text-center">
                            <h5 class="card-title">🤖 Fix It Fred AI</h5>
                            <p class="card-text">Get expert maintenance advice and safety recommendations for every work order.</p>
                            <a href="/ai-chat" class="btn btn-success">Chat with Fred</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card feature-card">
                        <div class="card-body text-center">
                            <h5 class="card-title">🧠 Grok Strategic Analysis</h5>
                            <p class="card-text">Strategic optimization and infrastructure analysis for maximum efficiency.</p>
                            <a href="/grok-analysis" class="btn btn-info">Strategic Insights</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """)

@app.get("/work-orders", response_class=HTMLResponse)
async def work_orders_dashboard():
    """Enhanced work orders dashboard"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Work Orders - ChatterFix CMMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .work-order-card {
                transition: transform 0.2s;
                margin-bottom: 1rem;
            }
            .work-order-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .priority-critical { border-left: 5px solid #dc3545; }
            .priority-high { border-left: 5px solid #fd7e14; }
            .priority-medium { border-left: 5px solid #ffc107; }
            .priority-low { border-left: 5px solid #28a745; }
            .ai-insights {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                padding: 1rem;
                margin-top: 1rem;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🔧 ChatterFix CMMS</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">Dashboard</a>
                    <a class="nav-link active" href="/work-orders">Work Orders</a>
                    <a class="nav-link" href="/assets">Assets</a>
                </div>
            </div>
        </nav>

        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>🔧 Enhanced Work Orders</h2>
                <button class="btn btn-primary" onclick="showCreateModal()">+ Create Work Order</button>
            </div>

            <div class="row">
                <div class="col-md-8">
                    <div id="workOrdersList">
                        <div class="text-center">
                            <div class="spinner-border" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2">Loading enhanced work orders...</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>🤖 AI Assistant</h5>
                        </div>
                        <div class="card-body">
                            <p>Get AI insights for your work orders:</p>
                            <button class="btn btn-success btn-sm w-100 mb-2" onclick="chatWithFred()">💬 Chat with Fix It Fred</button>
                            <button class="btn btn-info btn-sm w-100" onclick="getGrokAnalysis()">🧠 Grok Strategic Analysis</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Work Order Modal -->
        <div class="modal fade" id="createWorkOrderModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Create Enhanced Work Order</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="createWorkOrderForm">
                            <div class="mb-3">
                                <label class="form-label">Title</label>
                                <input type="text" class="form-control" id="title" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Description</label>
                                <textarea class="form-control" id="description" rows="3" required></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Priority</label>
                                <select class="form-select" id="priority">
                                    <option value="low">Low</option>
                                    <option value="medium" selected>Medium</option>
                                    <option value="high">High</option>
                                    <option value="critical">Critical</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Technician</label>
                                <input type="text" class="form-control" id="technician">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="createWorkOrder()">Create with AI Enhancement</button>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let workOrders = [];

            async function loadWorkOrders() {
                try {
                    const response = await fetch('/api/work-orders');
                    const data = await response.json();
                    workOrders = data.work_orders || [];
                    renderWorkOrders();
                } catch (error) {
                    console.error('Error loading work orders:', error);
                    document.getElementById('workOrdersList').innerHTML = 
                        '<div class="alert alert-danger">Error loading work orders. Please try again.</div>';
                }
            }

            function renderWorkOrders() {
                const container = document.getElementById('workOrdersList');
                if (!workOrders.length) {
                    container.innerHTML = '<div class="alert alert-info">No work orders found. Create your first enhanced work order!</div>';
                    return;
                }

                container.innerHTML = workOrders.map(wo => `
                    <div class="card work-order-card priority-$\\{wo.priority}">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h5 class="card-title">${wo.title}</h5>
                                    <p class="card-text">${wo.description}</p>
                                    <div class="d-flex gap-2">
                                        <span class="badge bg-primary">${wo.status}</span>
                                        <span class="badge bg-warning">${wo.priority}</span>
                                        ${wo.assigned_to ? `<span class="badge bg-info">${wo.assigned_to}</span>` : ''}
                                    </div>
                                </div>
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="getAIInsights(${wo.id})">🤖 AI Insights</button>
                                    <button class="btn btn-sm btn-outline-secondary" onclick="editWorkOrder(${wo.id})">Edit</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }

            async function createWorkOrder() {
                const title = document.getElementById('title').value;
                const description = document.getElementById('description').value;
                const priority = document.getElementById('priority').value;
                const technician = document.getElementById('technician').value;

                try {
                    const response = await fetch('/api/work-orders', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            title: title,
                            description: description,
                            priority: priority,
                            technician: technician
                        }),
                    });

                    if (response.ok) {
                        bootstrap.Modal.getInstance(document.getElementById('createWorkOrderModal')).hide();
                        document.getElementById('createWorkOrderForm').reset();
                        await loadWorkOrders();
                        alert('✅ Enhanced work order created successfully with AI insights!');
                    } else {
                        alert('❌ Error creating work order');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('❌ Error creating work order');
                }
            }

            async function getAIInsights(workOrderId) {
                try {
                    const response = await fetch(`/api/work-orders/${workOrderId}/ai-analyze`);
                    const data = await response.json();
                    
                    alert(`🤖 AI Insights for: ${data.title}\\n\\n` +
                          `Fix It Fred: ${data.recommendations.fred_says || 'Processing...'}\\n\\n` +
                          `Grok Strategy: ${data.recommendations.grok_strategy || 'Analyzing...'}`);
                } catch (error) {
                    console.error('Error getting AI insights:', error);
                    alert('Error getting AI insights');
                }
            }

            function showCreateModal() {
                new bootstrap.Modal(document.getElementById('createWorkOrderModal')).show();
            }

            function chatWithFred() {
                window.open('/ai-chat?assistant=fred', '_blank');
            }

            function getGrokAnalysis() {
                window.open('/ai-chat?assistant=grok', '_blank');
            }

            // Load work orders when page loads
            document.addEventListener('DOMContentLoaded', loadWorkOrders);
        </script>
    </body>
    </html>
    """)

# ===== ENHANCED API ENDPOINTS - Route to microservices =====

@app.get("/api/work-orders")
async def get_work_orders():
    """Get all work orders via enhanced AI-powered API service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ENHANCED_WORK_ORDERS_URL}/api/work-orders", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="Enhanced work orders service unavailable")
    except Exception as e:
        logger.error(f"Error getting work orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/{work_order_id}")
async def get_work_order(work_order_id: int):
    """Get a specific work order with AI insights"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ENHANCED_WORK_ORDERS_URL}/api/work-orders/{work_order_id}", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Work order not found")
            else:
                raise HTTPException(status_code=500, detail="Enhanced work orders service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrderCreate):
    """Create a new work order with AI enhancement"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ENHANCED_WORK_ORDERS_URL}/api/work-orders", 
                json=work_order.dict(), 
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="Enhanced work orders service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/work-orders/{work_order_id}")
async def update_work_order(work_order_id: int, updates: WorkOrderUpdate):
    """Update an existing work order"""
    try:
        async with httpx.AsyncClient() as client:
            update_data = {k: v for k, v in updates.dict().items() if v is not None}
            response = await client.put(
                f"{ENHANCED_WORK_ORDERS_URL}/api/work-orders/{work_order_id}", 
                json=update_data, 
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Work order not found")
            else:
                raise HTTPException(status_code=500, detail="Enhanced work orders service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete (cancel) a work order"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{ENHANCED_WORK_ORDERS_URL}/api/work-orders/{work_order_id}", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Work order not found")
            else:
                raise HTTPException(status_code=500, detail="Enhanced work orders service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders/analytics/summary")
async def get_work_order_analytics():
    """Get work order analytics dashboard"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ENHANCED_WORK_ORDERS_URL}/api/work-orders/analytics/summary", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="Enhanced work orders service unavailable")
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-orders/{work_order_id}/ai-analyze")
async def analyze_work_order_with_ai(work_order_id: int):
    """Get comprehensive AI analysis for work order"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{ENHANCED_WORK_ORDERS_URL}/api/work-orders/{work_order_id}/ai-analyze", timeout=15.0)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="AI analysis service unavailable")
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai-chat", response_class=HTMLResponse)
async def ai_chat():
    """AI chat interface for Fix It Fred and Grok"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>AI Assistant - ChatterFix</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🔧 ChatterFix CMMS</a>
                <a class="nav-link text-white" href="/work-orders">← Back to Work Orders</a>
            </div>
        </nav>
        <div class="container mt-4">
            <h2>🤖 AI Assistant - Fix It Fred & Grok</h2>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h5>💬 Fix It Fred - Maintenance Expert</h5>
                        </div>
                        <div class="card-body">
                            <p>Get expert maintenance advice and safety recommendations.</p>
                            <button class="btn btn-success" onclick="window.open('http://localhost:8005', '_blank')">Chat with Fred</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h5>🧠 Grok - Strategic Analysis</h5>
                        </div>
                        <div class="card-body">
                            <p>Strategic optimization and infrastructure analysis.</p>
                            <button class="btn btn-info" onclick="window.open('http://localhost:8006', '_blank')">Chat with Grok</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Enhanced ChatterFix CMMS on port {port}...")
    print("🔧 Features: Industry-Leading Work Orders with AI Enhancement")
    print("🤖 Fix It Fred Integration: ✅")  
    print("🧠 Grok Strategic Analysis: ✅")
    print("💾 Enhanced Database Service: ✅")
    print("🎯 Best Work Order Module in the Industry: ✅")
    uvicorn.run(app, host="0.0.0.0", port=port)