#!/usr/bin/env python3
"""
ChatterFix CMMS - Complete Interface with Fix It Fred Integration
================================================================
Comprehensive CMMS platform with integrated Fix It Fred AI chat widget
"""

import os
import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(title="ChatterFix CMMS Platform", version="4.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
FIX_IT_FRED_URL = "http://localhost:8011"
WORK_ORDERS_URL = "http://localhost:8013"
ASSETS_URL = "http://localhost:8014"
PARTS_URL = "http://localhost:8016"

@app.get("/", response_class=HTMLResponse)
async def chatterfix_interface(response: Response):
    """Main ChatterFix CMMS interface with Fix It Fred integration"""
    # Add cache-busting headers to force browser to reload fresh content
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS - AI-Powered Maintenance Management (v2.0 Ollama)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        .sidebar {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .content-area {
            background-color: #f8f9fa;
        }
        .nav-link {
            color: rgba(255,255,255,0.8);
            transition: all 0.3s;
        }
        .nav-link:hover, .nav-link.active {
            color: white;
            background-color: rgba(255,255,255,0.1);
        }
        .card {
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: none;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
        }
        .stat-card.warning {
            background: linear-gradient(45deg, #ffc107, #fd7e14);
        }
        .stat-card.danger {
            background: linear-gradient(45deg, #dc3545, #e83e8c);
        }
        
        /* Fix It Fred Chat Widget Styles */
        .fred-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }
        .fred-chat-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .fred-chat-icon:hover {
            transform: scale(1.1);
        }
        .fred-chat-window {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            display: none;
            flex-direction: column;
            z-index: 1001;
        }
        .fred-chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .fred-chat-body {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        .fred-chat-input {
            padding: 15px;
            border-top: 1px solid #eee;
            border-radius: 0 0 10px 10px;
        }
        .fred-message {
            margin-bottom: 15px;
            max-width: 80%;
        }
        .fred-message.user {
            align-self: flex-end;
        }
        .fred-message.ai {
            align-self: flex-start;
        }
        .fred-message-bubble {
            padding: 10px 15px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .fred-message.user .fred-message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .fred-message.ai .fred-message-bubble {
            background: #f1f3f4;
            color: #333;
        }
        .table-container {
            max-height: 400px;
            overflow-y: auto;
        }
        .priority-high { color: #dc3545; font-weight: bold; }
        .priority-medium { color: #ffc107; font-weight: bold; }
        .priority-low { color: #28a745; font-weight: bold; }
        .status-open { color: #dc3545; }
        .status-in-progress { color: #ffc107; }
        .status-completed { color: #28a745; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-2 sidebar p-0">
                <div class="p-3">
                    <h4><i class="fas fa-tools"></i> ChatterFix</h4>
                    <small class="text-light">AI-Powered CMMS</small>
                </div>
                <nav class="nav flex-column px-3">
                    <a class="nav-link active" href="#" onclick="showSection('dashboard')">
                        <i class="fas fa-tachometer-alt"></i> Dashboard
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('work-orders')">
                        <i class="fas fa-clipboard-list"></i> Work Orders
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('assets')">
                        <i class="fas fa-cogs"></i> Assets
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('parts')">
                        <i class="fas fa-boxes"></i> Parts & Inventory
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('reports')">
                        <i class="fas fa-chart-bar"></i> Reports
                    </a>
                    <a class="nav-link" href="#" onclick="showSection('settings')">
                        <i class="fas fa-cog"></i> Settings
                    </a>
                </nav>
                <div class="p-3 mt-auto">
                    <small class="text-light">
                        <i class="fas fa-robot"></i> Fix It Fred AI Ready
                    </small>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="col-md-10 content-area p-4">
                <!-- Dashboard Section -->
                <div id="dashboard" class="content-section">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h2><i class="fas fa-tachometer-alt"></i> Dashboard</h2>
                        <div class="d-flex gap-2">
                            <button class="btn btn-primary" onclick="toggleFredChat()">
                                <i class="fas fa-robot"></i> Ask Fix It Fred
                            </button>
                            <button class="btn btn-success" onclick="createWorkOrder()">
                                <i class="fas fa-plus"></i> New Work Order
                            </button>
                        </div>
                    </div>
                    
                    <!-- Stats Cards -->
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card stat-card">
                                <div class="card-body text-center">
                                    <h3 id="open-wo-count">-</h3>
                                    <p class="mb-0">Open Work Orders</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card stat-card warning">
                                <div class="card-body text-center">
                                    <h3 id="overdue-count">-</h3>
                                    <p class="mb-0">Overdue Tasks</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card stat-card">
                                <div class="card-body text-center">
                                    <h3 id="assets-count">-</h3>
                                    <p class="mb-0">Active Assets</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card stat-card danger">
                                <div class="card-body text-center">
                                    <h3 id="critical-count">-</h3>
                                    <p class="mb-0">Critical Alerts</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Work Orders -->
                    <div class="card">
                        <div class="card-header d-flex justify-content-between">
                            <h5><i class="fas fa-clipboard-list"></i> Recent Work Orders</h5>
                            <button class="btn btn-sm btn-outline-primary" onclick="showSection('work-orders')">
                                View All
                            </button>
                        </div>
                        <div class="card-body">
                            <div class="table-container">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Title</th>
                                            <th>Priority</th>
                                            <th>Status</th>
                                            <th>Assigned To</th>
                                            <th>Created</th>
                                        </tr>
                                    </thead>
                                    <tbody id="recent-work-orders">
                                        <tr>
                                            <td colspan="6" class="text-center">Loading...</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Work Orders Section -->
                <div id="work-orders" class="content-section" style="display: none;">
                    <h2><i class="fas fa-clipboard-list"></i> Work Orders Management</h2>
                    <div class="card">
                        <div class="card-header d-flex justify-content-between">
                            <h5>All Work Orders</h5>
                            <button class="btn btn-success" onclick="createWorkOrder()">
                                <i class="fas fa-plus"></i> Create Work Order
                            </button>
                        </div>
                        <div class="card-body">
                            <div class="table-container">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Title</th>
                                            <th>Description</th>
                                            <th>Priority</th>
                                            <th>Status</th>
                                            <th>Assigned To</th>
                                            <th>Created</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="all-work-orders">
                                        <tr>
                                            <td colspan="8" class="text-center">Loading...</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Assets Section -->
                <div id="assets" class="content-section" style="display: none;">
                    <h2><i class="fas fa-cogs"></i> Asset Management</h2>
                    
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <button class="btn btn-primary" onclick="createAsset()">
                                <i class="fas fa-plus"></i> Create New Asset
                            </button>
                            <button class="btn btn-outline-primary ms-2" onclick="loadAllAssets()">
                                <i class="fas fa-sync"></i> Refresh
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-outline-info" onclick="askFredAbout('asset management')">
                                <i class="fas fa-robot"></i> Ask Fix It Fred
                            </button>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-list"></i> All Assets</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Name</th>
                                            <th>Type</th>
                                            <th>Location</th>
                                            <th>Status</th>
                                            <th>Last Maintenance</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="all-assets">
                                        <tr>
                                            <td colspan="7" class="text-center">Loading assets...</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Parts Section -->
                <div id="parts" class="content-section" style="display: none;">
                    <h2><i class="fas fa-boxes"></i> Parts & Inventory</h2>
                    
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <button class="btn btn-primary" onclick="createPart()">
                                <i class="fas fa-plus"></i> Add New Part
                            </button>
                            <button class="btn btn-outline-primary ms-2" onclick="loadAllParts()">
                                <i class="fas fa-sync"></i> Refresh
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-outline-info" onclick="askFredAbout('inventory management')">
                                <i class="fas fa-robot"></i> Ask Fix It Fred
                            </button>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-list"></i> Inventory</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Part Name</th>
                                            <th>Part Number</th>
                                            <th>Category</th>
                                            <th>Stock Level</th>
                                            <th>Min Stock</th>
                                            <th>Unit Cost</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="all-parts">
                                        <tr>
                                            <td colspan="9" class="text-center">Loading parts...</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Reports Section -->
                <div id="reports" class="content-section" style="display: none;">
                    <h2><i class="fas fa-chart-bar"></i> Reports & Analytics</h2>
                    <div class="card">
                        <div class="card-body">
                            <p>Reporting and analytics dashboard coming soon...</p>
                            <button class="btn btn-primary" onclick="askFredAbout('maintenance reports and analytics')">
                                <i class="fas fa-robot"></i> Ask Fix It Fred about Reports
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Settings Section -->
                <div id="settings" class="content-section" style="display: none;">
                    <h2><i class="fas fa-cog"></i> System Settings</h2>
                    <div class="card">
                        <div class="card-body">
                            <p>System configuration and settings coming soon...</p>
                            <div class="alert alert-info">
                                <i class="fas fa-robot"></i> <strong>Fix It Fred AI Integration:</strong> 
                                Your AI assistant is ready to help with any CMMS questions or tasks.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Fix It Fred Chat Widget -->
    <div class="fred-chat-widget">
        <div class="fred-chat-icon" onclick="toggleFredChat()" title="Chat with Fix It Fred">
            <i class="fas fa-robot fa-lg"></i>
        </div>
        
        <div class="fred-chat-window" id="fredChatWindow">
            <div class="fred-chat-header">
                <div>
                    <strong><i class="fas fa-robot"></i> Fix It Fred</strong>
                    <br><small>Your AI CMMS Assistant</small>
                </div>
                <button class="btn btn-sm btn-link text-white" onclick="toggleFredChat()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="fred-chat-body" id="fredChatBody">
                <div class="fred-message ai">
                    <div class="fred-message-bubble">
                        👋 Hi! I'm Fix It Fred, your AI assistant for ChatterFix CMMS. I can help you with work orders, asset management, maintenance planning, and more!
                        <br><br>
                        Try asking me:
                        <ul class="mt-2 mb-0">
                            <li>"Show me current work orders"</li>
                            <li>"Create a work order for HVAC maintenance"</li>
                            <li>"What are my overdue tasks?"</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="fred-chat-input">
                <div class="input-group">
                    <input type="text" class="form-control" id="fredMessageInput" 
                           placeholder="Ask Fix It Fred anything..." 
                           onkeypress="if(event.key==='Enter') sendFredMessage()">
                    <button class="btn btn-primary" onclick="sendFredMessage()">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let fredChatOpen = false;

        // Navigation
        function showSection(sectionId) {
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });
            
            // Remove active class from all nav links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            // Show selected section
            document.getElementById(sectionId).style.display = 'block';
            
            // Add active class to clicked nav link
            event.target.classList.add('active');
            
            // Load section data
            if (sectionId === 'dashboard') {
                loadDashboardData();
            } else if (sectionId === 'work-orders') {
                loadAllWorkOrders();
            } else if (sectionId === 'assets') {
                loadAllAssets();
            } else if (sectionId === 'parts') {
                loadAllParts();
            }
        }

        // Fix It Fred Chat Functions
        function toggleFredChat() {
            const chatWindow = document.getElementById('fredChatWindow');
            fredChatOpen = !fredChatOpen;
            chatWindow.style.display = fredChatOpen ? 'flex' : 'none';
            
            if (fredChatOpen) {
                document.getElementById('fredMessageInput').focus();
            }
        }

        function sendFredMessage() {
            const input = document.getElementById('fredMessageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addFredMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            addFredMessage('Fix It Fred is thinking...', 'ai', true);
            
            // Send to Fix It Fred API
            fetch('/api/universal/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    provider: 'ollama'
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                removeTypingIndicator();
                
                if (data.success) {
                    addFredMessage(data.response || 'I apologize, but I need API keys to provide responses. The integration is working though!', 'ai');
                } else {
                    addFredMessage('Sorry, I encountered an error. Please try again.', 'ai');
                }
            })
            .catch(error => {
                removeTypingIndicator();
                addFredMessage('Connection error. Please check your connection and try again.', 'ai');
            });
        }

        function addFredMessage(message, sender, isTyping = false) {
            const chatBody = document.getElementById('fredChatBody');
            const messageDiv = document.createElement('div');
            messageDiv.className = `fred-message ${sender}`;
            if (isTyping) messageDiv.id = 'typing-indicator';
            
            messageDiv.innerHTML = `
                <div class="fred-message-bubble">
                    ${message}
                </div>
            `;
            
            chatBody.appendChild(messageDiv);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function removeTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) {
                indicator.remove();
            }
        }

        function askFredAbout(topic) {
            if (!fredChatOpen) {
                toggleFredChat();
            }
            
            setTimeout(() => {
                const input = document.getElementById('fredMessageInput');
                input.value = `Tell me about ${topic} in CMMS`;
                sendFredMessage();
            }, 500);
        }

        // Data Loading Functions
        async function loadDashboardData() {
            try {
                const response = await fetch('/api/work_orders');
                const data = await response.json();
                
                if (data.success) {
                    const workOrders = data.work_orders || [];
                    
                    // Update stats
                    document.getElementById('open-wo-count').textContent = workOrders.filter(wo => wo.status === 'open').length;
                    document.getElementById('overdue-count').textContent = '0'; // Calculate based on due dates
                    document.getElementById('assets-count').textContent = '-';
                    document.getElementById('critical-count').textContent = workOrders.filter(wo => wo.priority === 'high').length;
                    
                    // Load recent work orders
                    loadRecentWorkOrders(workOrders.slice(0, 5));
                }
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }

        function loadRecentWorkOrders(workOrders) {
            const tbody = document.getElementById('recent-work-orders');
            tbody.innerHTML = '';
            
            workOrders.forEach(wo => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${wo.id}</td>
                    <td>${wo.title}</td>
                    <td><span class="priority-${wo.priority}">${wo.priority}</span></td>
                    <td><span class="status-${wo.status.replace(' ', '-')}">${wo.status}</span></td>
                    <td>${wo.assigned_to || 'Unassigned'}</td>
                    <td>${new Date(wo.created_at).toLocaleDateString()}</td>
                `;
                tbody.appendChild(row);
            });
        }

        async function loadAllWorkOrders() {
            try {
                const response = await fetch('/api/work_orders');
                const data = await response.json();
                
                if (data.success) {
                    const tbody = document.getElementById('all-work-orders');
                    tbody.innerHTML = '';
                    
                    data.work_orders.forEach(wo => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${wo.id}</td>
                            <td>${wo.title}</td>
                            <td>${wo.description || 'No description'}</td>
                            <td><span class="priority-${wo.priority}">${wo.priority}</span></td>
                            <td><span class="status-${wo.status.replace(' ', '-')}">${wo.status}</span></td>
                            <td>${wo.assigned_to || 'Unassigned'}</td>
                            <td>${new Date(wo.created_at).toLocaleDateString()}</td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="viewWorkOrder(${wo.id})">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-sm btn-success" onclick="askFredAbout('work order ${wo.id}')">
                                    <i class="fas fa-robot"></i>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('Error loading work orders:', error);
            }
        }

        function createWorkOrder() {
            document.getElementById('workOrderForm').reset();
            document.getElementById('workOrderModalTitle').textContent = 'Create New Work Order';
            document.getElementById('workOrderId').value = '';
            document.getElementById('workOrderModal').style.display = 'block';
        }

        function viewWorkOrder(id) {
            // Load existing work order data
            fetch(`/api/work_orders/${id}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const wo = data.work_order;
                        document.getElementById('workOrderModalTitle').textContent = `Edit Work Order #${wo.id}`;
                        document.getElementById('workOrderId').value = wo.id;
                        document.getElementById('woTitle').value = wo.title;
                        document.getElementById('woDescription').value = wo.description;
                        document.getElementById('woPriority').value = wo.priority;
                        document.getElementById('woStatus').value = wo.status;
                        document.getElementById('woAssignedTo').value = wo.assigned_to || '';
                        document.getElementById('woDueDate').value = wo.due_date || '';
                        document.getElementById('workOrderModal').style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Error loading work order:', error);
                    alert('Error loading work order details');
                });
        }

        function closeWorkOrderModal() {
            document.getElementById('workOrderModal').style.display = 'none';
        }

        async function saveWorkOrder() {
            const formData = {
                title: document.getElementById('woTitle').value,
                description: document.getElementById('woDescription').value,
                priority: document.getElementById('woPriority').value,
                status: document.getElementById('woStatus').value,
                assigned_to: document.getElementById('woAssignedTo').value,
                due_date: document.getElementById('woDueDate').value
            };

            const workOrderId = document.getElementById('workOrderId').value;
            const isEdit = workOrderId !== '';

            try {
                const response = await fetch(`/api/work_orders${isEdit ? '/' + workOrderId : ''}`, {
                    method: isEdit ? 'PUT' : 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                if (result.success) {
                    closeWorkOrderModal();
                    loadAllWorkOrders();
                    loadDashboardData();
                    alert(isEdit ? 'Work order updated successfully!' : 'Work order created successfully!');
                } else {
                    alert('Error saving work order: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error saving work order:', error);
                alert('Error saving work order');
            }
        }

        // Asset Management Functions
        async function loadAllAssets() {
            try {
                const response = await fetch('/api/assets');
                const data = await response.json();
                
                if (data.success) {
                    const tbody = document.getElementById('all-assets');
                    tbody.innerHTML = '';
                    
                    data.assets.forEach(asset => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${asset.id}</td>
                            <td>${asset.name}</td>
                            <td><span class="badge bg-secondary">${asset.type || 'N/A'}</span></td>
                            <td>${asset.location || 'N/A'}</td>
                            <td><span class="status-${asset.status.replace(' ', '-')}">${asset.status}</span></td>
                            <td>${asset.last_maintenance ? new Date(asset.last_maintenance).toLocaleDateString() : 'N/A'}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" onclick="viewAsset(${asset.id})">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-outline-secondary ms-1" onclick="editAsset(${asset.id})">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    const tbody = document.getElementById('all-assets');
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No assets found</td></tr>';
                }
            } catch (error) {
                console.error('Error loading assets:', error);
                const tbody = document.getElementById('all-assets');
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading assets</td></tr>';
            }
        }

        function createAsset() {
            document.getElementById('assetForm').reset();
            document.getElementById('assetModalTitle').textContent = 'Create New Asset';
            document.getElementById('assetId').value = '';
            document.getElementById('assetModal').style.display = 'block';
        }

        function viewAsset(id) {
            editAsset(id, true);
        }

        function editAsset(id, readOnly = false) {
            fetch(`/api/assets/${id}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const asset = data.asset;
                        document.getElementById('assetModalTitle').textContent = readOnly ? `View Asset #${asset.id}` : `Edit Asset #${asset.id}`;
                        document.getElementById('assetId').value = asset.id;
                        document.getElementById('assetName').value = asset.name || '';
                        document.getElementById('assetDescription').value = asset.description || '';
                        document.getElementById('assetType').value = asset.type || 'equipment';
                        document.getElementById('assetStatus').value = asset.status || 'active';
                        document.getElementById('assetLocation').value = asset.location || '';
                        document.getElementById('assetManufacturer').value = asset.manufacturer || '';
                        document.getElementById('assetModel').value = asset.model || '';
                        document.getElementById('assetSerialNumber').value = asset.serial_number || '';
                        document.getElementById('assetPurchaseDate').value = asset.purchase_date || '';
                        document.getElementById('assetWarrantyExpiry').value = asset.warranty_expiry || '';
                        document.getElementById('assetCost').value = asset.cost || '';
                        document.getElementById('assetNotes').value = asset.notes || '';

                        if (readOnly) {
                            const form = document.getElementById('assetForm');
                            form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = true);
                            document.querySelector('#assetModal .btn-primary').style.display = 'none';
                        } else {
                            const form = document.getElementById('assetForm');
                            form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = false);
                            document.querySelector('#assetModal .btn-primary').style.display = 'inline-block';
                        }

                        document.getElementById('assetModal').style.display = 'block';
                    }
                })
                .catch(error => console.error('Error loading asset:', error));
        }

        function closeAssetModal() {
            document.getElementById('assetModal').style.display = 'none';
            const form = document.getElementById('assetForm');
            form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = false);
            document.querySelector('#assetModal .btn-primary').style.display = 'inline-block';
        }

        async function saveAsset() {
            const formData = {
                name: document.getElementById('assetName').value,
                description: document.getElementById('assetDescription').value,
                type: document.getElementById('assetType').value,
                status: document.getElementById('assetStatus').value,
                location: document.getElementById('assetLocation').value,
                manufacturer: document.getElementById('assetManufacturer').value,
                model: document.getElementById('assetModel').value,
                serial_number: document.getElementById('assetSerialNumber').value,
                purchase_date: document.getElementById('assetPurchaseDate').value,
                warranty_expiry: document.getElementById('assetWarrantyExpiry').value,
                cost: document.getElementById('assetCost').value,
                notes: document.getElementById('assetNotes').value
            };

            const assetId = document.getElementById('assetId').value;
            const isEdit = assetId !== '';

            try {
                const response = await fetch(`/api/assets${isEdit ? '/' + assetId : ''}`, {
                    method: isEdit ? 'PUT' : 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                if (result.success) {
                    closeAssetModal();
                    loadAllAssets();
                    alert(isEdit ? 'Asset updated successfully!' : 'Asset created successfully!');
                } else {
                    alert('Error saving asset: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error saving asset:', error);
                alert('Error saving asset');
            }
        }

        // Parts Management Functions
        async function loadAllParts() {
            try {
                const response = await fetch('/api/parts');
                const data = await response.json();
                
                if (data.success) {
                    const tbody = document.getElementById('all-parts');
                    tbody.innerHTML = '';
                    
                    data.parts.forEach(part => {
                        const stockStatus = part.stock_level <= part.min_stock ? 'text-danger' : 'text-success';
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${part.id}</td>
                            <td>${part.name}</td>
                            <td><span class="badge bg-info">${part.part_number}</span></td>
                            <td>${part.category || 'N/A'}</td>
                            <td class="${stockStatus}">${part.stock_level || 0}</td>
                            <td>${part.min_stock || 0}</td>
                            <td>$${part.unit_cost || '0.00'}</td>
                            <td>
                                ${part.stock_level <= part.min_stock ? 
                                    '<span class="badge bg-warning">Low Stock</span>' : 
                                    '<span class="badge bg-success">In Stock</span>'
                                }
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" onclick="viewPart(${part.id})">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-outline-secondary ms-1" onclick="editPart(${part.id})">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    const tbody = document.getElementById('all-parts');
                    tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No parts found</td></tr>';
                }
            } catch (error) {
                console.error('Error loading parts:', error);
                const tbody = document.getElementById('all-parts');
                tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error loading parts</td></tr>';
            }
        }

        function createPart() {
            document.getElementById('partsForm').reset();
            document.getElementById('partsModalTitle').textContent = 'Add New Part';
            document.getElementById('partId').value = '';
            document.getElementById('partsModal').style.display = 'block';
        }

        function viewPart(id) {
            editPart(id, true);
        }

        function editPart(id, readOnly = false) {
            fetch(`/api/parts/${id}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const part = data.part;
                        document.getElementById('partsModalTitle').textContent = readOnly ? `View Part #${part.id}` : `Edit Part #${part.id}`;
                        document.getElementById('partId').value = part.id;
                        document.getElementById('partName').value = part.name || '';
                        document.getElementById('partNumber').value = part.part_number || '';
                        document.getElementById('partCategory').value = part.category || 'mechanical';
                        document.getElementById('partDescription').value = part.description || '';
                        document.getElementById('partStock').value = part.stock_level || 0;
                        document.getElementById('partMinStock').value = part.min_stock || 0;
                        document.getElementById('partMaxStock').value = part.max_stock || '';
                        document.getElementById('partUnitCost').value = part.unit_cost || '';
                        document.getElementById('partUnit').value = part.unit || '';
                        document.getElementById('partSupplier').value = part.supplier || '';
                        document.getElementById('partLocation').value = part.location || '';
                        document.getElementById('partNotes').value = part.notes || '';

                        if (readOnly) {
                            const form = document.getElementById('partsForm');
                            form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = true);
                            document.querySelector('#partsModal .btn-primary').style.display = 'none';
                        } else {
                            const form = document.getElementById('partsForm');
                            form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = false);
                            document.querySelector('#partsModal .btn-primary').style.display = 'inline-block';
                        }

                        document.getElementById('partsModal').style.display = 'block';
                    }
                })
                .catch(error => console.error('Error loading part:', error));
        }

        function closePartsModal() {
            document.getElementById('partsModal').style.display = 'none';
            const form = document.getElementById('partsForm');
            form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = false);
            document.querySelector('#partsModal .btn-primary').style.display = 'inline-block';
        }

        async function savePart() {
            const formData = {
                name: document.getElementById('partName').value,
                part_number: document.getElementById('partNumber').value,
                category: document.getElementById('partCategory').value,
                description: document.getElementById('partDescription').value,
                stock_level: parseInt(document.getElementById('partStock').value) || 0,
                min_stock: parseInt(document.getElementById('partMinStock').value) || 0,
                max_stock: parseInt(document.getElementById('partMaxStock').value) || null,
                unit_cost: parseFloat(document.getElementById('partUnitCost').value) || null,
                unit: document.getElementById('partUnit').value,
                supplier: document.getElementById('partSupplier').value,
                location: document.getElementById('partLocation').value,
                notes: document.getElementById('partNotes').value
            };

            const partId = document.getElementById('partId').value;
            const isEdit = partId !== '';

            try {
                const response = await fetch(`/api/parts${isEdit ? '/' + partId : ''}`, {
                    method: isEdit ? 'PUT' : 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                if (result.success) {
                    closePartsModal();
                    loadAllParts();
                    alert(isEdit ? 'Part updated successfully!' : 'Part added successfully!');
                } else {
                    alert('Error saving part: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error saving part:', error);
                alert('Error saving part');
            }
        }

        // Initialize dashboard on load
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
        });
    </script>

    <!-- Work Order Modal -->
    <div id="workOrderModal" class="modal" style="display: none;">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="workOrderModalTitle">Create New Work Order</h5>
                    <button type="button" class="btn-close" onclick="closeWorkOrderModal()"></button>
                </div>
                <form id="workOrderForm">
                    <div class="modal-body">
                        <input type="hidden" id="workOrderId">
                        
                        <div class="mb-3">
                            <label for="woTitle" class="form-label">Title *</label>
                            <input type="text" class="form-control" id="woTitle" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="woDescription" class="form-label">Description</label>
                            <textarea class="form-control" id="woDescription" rows="3"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="woPriority" class="form-label">Priority</label>
                                    <select class="form-select" id="woPriority">
                                        <option value="low">Low</option>
                                        <option value="medium" selected>Medium</option>
                                        <option value="high">High</option>
                                        <option value="urgent">Urgent</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="woStatus" class="form-label">Status</label>
                                    <select class="form-select" id="woStatus">
                                        <option value="open" selected>Open</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="completed">Completed</option>
                                        <option value="cancelled">Cancelled</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="woAssignedTo" class="form-label">Assigned To</label>
                                    <input type="text" class="form-control" id="woAssignedTo" placeholder="Technician name">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="woDueDate" class="form-label">Due Date</label>
                                    <input type="date" class="form-control" id="woDueDate">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeWorkOrderModal()">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveWorkOrder()">Save Work Order</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Asset Modal -->
    <div id="assetModal" class="modal" style="display: none;">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="assetModalTitle">Create New Asset</h5>
                    <button type="button" class="btn-close" onclick="closeAssetModal()"></button>
                </div>
                <form id="assetForm">
                    <div class="modal-body">
                        <input type="hidden" id="assetId">
                        
                        <div class="mb-3">
                            <label for="assetName" class="form-label">Asset Name *</label>
                            <input type="text" class="form-control" id="assetName" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="assetDescription" class="form-label">Description</label>
                            <textarea class="form-control" id="assetDescription" rows="3"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetType" class="form-label">Asset Type</label>
                                    <select class="form-select" id="assetType">
                                        <option value="equipment">Equipment</option>
                                        <option value="vehicle">Vehicle</option>
                                        <option value="building">Building</option>
                                        <option value="infrastructure">Infrastructure</option>
                                        <option value="tool">Tool</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetStatus" class="form-label">Status</label>
                                    <select class="form-select" id="assetStatus">
                                        <option value="active" selected>Active</option>
                                        <option value="maintenance">Under Maintenance</option>
                                        <option value="retired">Retired</option>
                                        <option value="repair">Needs Repair</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetLocation" class="form-label">Location</label>
                                    <input type="text" class="form-control" id="assetLocation" placeholder="Building, floor, room">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetManufacturer" class="form-label">Manufacturer</label>
                                    <input type="text" class="form-control" id="assetManufacturer">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetModel" class="form-label">Model</label>
                                    <input type="text" class="form-control" id="assetModel">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetSerialNumber" class="form-label">Serial Number</label>
                                    <input type="text" class="form-control" id="assetSerialNumber">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetPurchaseDate" class="form-label">Purchase Date</label>
                                    <input type="date" class="form-control" id="assetPurchaseDate">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="assetWarrantyExpiry" class="form-label">Warranty Expiry</label>
                                    <input type="date" class="form-control" id="assetWarrantyExpiry">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="assetCost" class="form-label">Purchase Cost</label>
                            <input type="number" class="form-control" id="assetCost" step="0.01" placeholder="0.00">
                        </div>
                        
                        <div class="mb-3">
                            <label for="assetNotes" class="form-label">Notes</label>
                            <textarea class="form-control" id="assetNotes" rows="2" placeholder="Additional information..."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeAssetModal()">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveAsset()">Save Asset</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Parts Modal -->
    <div id="partsModal" class="modal" style="display: none;">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="partsModalTitle">Add New Part</h5>
                    <button type="button" class="btn-close" onclick="closePartsModal()"></button>
                </div>
                <form id="partsForm">
                    <div class="modal-body">
                        <input type="hidden" id="partId">
                        
                        <div class="mb-3">
                            <label for="partName" class="form-label">Part Name *</label>
                            <input type="text" class="form-control" id="partName" required>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="partNumber" class="form-label">Part Number *</label>
                                    <input type="text" class="form-control" id="partNumber" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="partCategory" class="form-label">Category</label>
                                    <select class="form-select" id="partCategory">
                                        <option value="mechanical">Mechanical</option>
                                        <option value="electrical">Electrical</option>
                                        <option value="hydraulic">Hydraulic</option>
                                        <option value="pneumatic">Pneumatic</option>
                                        <option value="consumable">Consumable</option>
                                        <option value="tools">Tools</option>
                                        <option value="safety">Safety</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="partDescription" class="form-label">Description</label>
                            <textarea class="form-control" id="partDescription" rows="3"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="partStock" class="form-label">Current Stock</label>
                                    <input type="number" class="form-control" id="partStock" min="0" value="0">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="partMinStock" class="form-label">Minimum Stock</label>
                                    <input type="number" class="form-control" id="partMinStock" min="0" value="0">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="partMaxStock" class="form-label">Maximum Stock</label>
                                    <input type="number" class="form-control" id="partMaxStock" min="0">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="partUnitCost" class="form-label">Unit Cost</label>
                                    <input type="number" class="form-control" id="partUnitCost" step="0.01" placeholder="0.00">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="partUnit" class="form-label">Unit of Measure</label>
                                    <input type="text" class="form-control" id="partUnit" placeholder="each, lb, kg, ft, etc.">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="partSupplier" class="form-label">Supplier</label>
                                    <input type="text" class="form-control" id="partSupplier">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="partLocation" class="form-label">Storage Location</label>
                                    <input type="text" class="form-control" id="partLocation" placeholder="Warehouse, bin, shelf">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="partNotes" class="form-label">Notes</label>
                            <textarea class="form-control" id="partNotes" rows="2" placeholder="Additional information..."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closePartsModal()">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="savePart()">Save Part</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <style>
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            z-index: 1050;
        }
        .modal-dialog {
            position: relative;
            width: auto;
            margin: 1.75rem auto;
            max-width: 500px;
        }
        .modal-lg {
            max-width: 800px;
        }
        .modal-content {
            background-color: #fff;
            border-radius: 0.375rem;
            box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
        }
        .modal-header {
            padding: 1rem;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-body {
            padding: 1rem;
        }
        .modal-footer {
            padding: 1rem;
            border-top: 1px solid #dee2e6;
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
        }
        .btn-close {
            background: none;
            border: none;
            font-size: 1.25rem;
            cursor: pointer;
        }
    </style>

</body>
</html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ChatterFix CMMS Platform",
        "version": "4.0.0",
        "features": [
            "Work Orders Management",
            "Asset Management", 
            "Parts & Inventory",
            "Fix It Fred AI Integration",
            "Real-time Dashboard"
        ],
        "fix_it_fred_status": "integrated",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/work_orders")
async def proxy_work_orders():
    """Proxy work orders from the microservice"""
    try:
        response = requests.get(f"{WORK_ORDERS_URL}/api/work_orders")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/work_orders")
async def proxy_create_work_order(request: Request):
    """Proxy work order creation"""
    try:
        data = await request.json()
        response = requests.post(f"{WORK_ORDERS_URL}/api/work_orders", json=data)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/work_orders/{work_order_id}")
async def proxy_get_work_order(work_order_id: int):
    """Proxy get individual work order"""
    try:
        response = requests.get(f"{WORK_ORDERS_URL}/api/work_orders/{work_order_id}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/work_orders/{work_order_id}")
async def proxy_update_work_order(work_order_id: int, request: Request):
    """Proxy work order update"""
    try:
        data = await request.json()
        response = requests.put(f"{WORK_ORDERS_URL}/api/work_orders/{work_order_id}", json=data)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

# Assets API endpoints
@app.get("/api/assets")
async def proxy_get_assets():
    """Proxy assets list"""
    try:
        response = requests.get(f"{ASSETS_URL}/api/assets")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/assets")
async def proxy_create_asset(request: Request):
    """Proxy asset creation"""
    try:
        data = await request.json()
        response = requests.post(f"{ASSETS_URL}/api/assets", json=data)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/assets/{asset_id}")
async def proxy_get_asset(asset_id: int):
    """Proxy asset details"""
    try:
        response = requests.get(f"{ASSETS_URL}/api/assets/{asset_id}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/assets/{asset_id}")
async def proxy_update_asset(asset_id: int, request: Request):
    """Proxy asset update"""
    try:
        data = await request.json()
        response = requests.put(f"{ASSETS_URL}/api/assets/{asset_id}", json=data)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

# Parts API endpoints
@app.get("/api/parts")
async def proxy_get_parts():
    """Proxy parts list"""
    try:
        response = requests.get(f"{PARTS_URL}/api/parts")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/parts")
async def proxy_create_part(request: Request):
    """Proxy part creation"""
    try:
        data = await request.json()
        response = requests.post(f"{PARTS_URL}/api/parts", json=data)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/parts/{part_id}")
async def proxy_get_part(part_id: int):
    """Proxy part details"""
    try:
        response = requests.get(f"{PARTS_URL}/api/parts/{part_id}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/parts/{part_id}")
async def proxy_update_part(part_id: int, request: Request):
    """Proxy part update"""
    try:
        data = await request.json()
        response = requests.put(f"{PARTS_URL}/api/parts/{part_id}", json=data)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/apps/chatterfix-cmms/chat")
async def chatterfix_ai_chat(request: Request):
    """ChatterFix-specific AI chat endpoint"""
    try:
        data = await request.json()
        response = requests.post(f"{FIX_IT_FRED_URL}/api/universal/chat", json=data, timeout=60)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🔧 Starting ChatterFix CMMS Platform with Fix It Fred integration on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)