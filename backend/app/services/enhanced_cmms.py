#!/usr/bin/env python3
"""
Enhanced ChatterFix CMMS App with AI Integration
Full-featured with Fix It Fred AI chat widget and rich styling
"""

from flask import Flask, render_template_string, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import uuid
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for AI access

# Fix It Fred AI Service URL
FRED_AI_URL = "http://localhost:8005"

# Sample data with more realistic content
assets_data = [
    {
        "id": "1", 
        "name": "Main Production Server",
        "description": "Primary server for production workloads",
        "asset_type": "equipment",
        "location": "Data Center A", 
        "status": "operational",
        "manufacturer": "Dell",
        "model": "PowerEdge R750",
        "created_at": "2024-01-15T10:00:00"
    },
    {
        "id": "2",
        "name": "Backup Generator", 
        "description": "Emergency power backup system",
        "asset_type": "equipment",
        "location": "Building B",
        "status": "active",
        "manufacturer": "Cummins",
        "model": "C175 D5",
        "created_at": "2023-08-20T14:30:00"
    },
    {
        "id": "3",
        "name": "HVAC Unit #1", 
        "description": "Main building air conditioning system",
        "asset_type": "equipment",
        "location": "Roof - North",
        "status": "active",
        "manufacturer": "Carrier",
        "model": "30XA1002",
        "created_at": "2022-06-10T09:15:00"
    }
]

work_orders_data = [
    {
        "id": "1",
        "title": "Server Maintenance",
        "description": "Routine server maintenance and performance check",
        "status": "in_progress", 
        "priority": "medium",
        "asset_id": "1",
        "assigned_to": "John Smith",
        "created_at": "2024-10-16T08:00:00",
        "due_date": "2024-10-18T17:00:00"
    },
    {
        "id": "2",
        "title": "Generator Fuel Check",
        "description": "Weekly fuel level and system check",
        "status": "open", 
        "priority": "high",
        "asset_id": "2",
        "assigned_to": "Jane Doe",
        "created_at": "2024-10-17T06:30:00",
        "due_date": "2024-10-17T18:00:00"
    },
    {
        "id": "3",
        "title": "HVAC Filter Replacement",
        "description": "Replace air filters in main HVAC unit",
        "status": "completed", 
        "priority": "medium",
        "asset_id": "3",
        "assigned_to": "Bob Wilson",
        "created_at": "2024-10-15T10:00:00",
        "due_date": "2024-10-16T16:00:00"
    }
]

parts_data = [
    {
        "id": "1",
        "name": "Air Filter - HVAC",
        "part_number": "AF-HVAC-001",
        "category": "filters",
        "current_stock": 8,
        "min_stock_level": 5,
        "unit_cost": 25.50,
        "supplier": "FilterCorp"
    },
    {
        "id": "2", 
        "name": "Server RAM - 32GB",
        "part_number": "RAM-32GB-DDR4",
        "category": "computer_parts",
        "current_stock": 2,
        "min_stock_level": 3,
        "unit_cost": 180.00,
        "supplier": "TechSupply"
    }
]

@app.route('/')
def dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>ChatterFix CMMS - Professional Maintenance Management</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            /* Primary Brand Colors */
            --primary-blue: #006fee;
            --primary-blue-dark: #0056b3;
            --primary-blue-light: #4285f4;
            
            /* Secondary Colors */
            --success-green: #28a745;
            --warning-orange: #fd7e14;
            --danger-red: #dc3545;
            --info-blue: #17a2b8;
            
            /* Neutral Colors */
            --gray-100: #f8f9fa;
            --gray-200: #e9ecef;
            --gray-300: #dee2e6;
            --gray-800: #343a40;
            --gray-900: #212529;
            
            /* Status Colors */
            --status-open: #17a2b8;
            --status-in-progress: #fd7e14;
            --status-completed: #28a745;
            
            /* Priority Colors */
            --priority-low: #28a745;
            --priority-medium: #ffc107;
            --priority-high: #fd7e14;
            --priority-critical: #dc3545;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            min-height: 100vh;
        }

        .navbar {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light)) !important;
            box-shadow: 0 2px 10px rgba(0, 111, 238, 0.3);
        }

        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
        }

        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            transition: all 0.3s ease;
            background: white;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .card-header {
            background: linear-gradient(135deg, var(--gray-100), white);
            border-bottom: 1px solid var(--gray-200);
            border-radius: 12px 12px 0 0 !important;
            font-weight: 600;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
            border: none;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 111, 238, 0.4);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--success-green), #20c997);
            border: none;
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--warning-orange), #ffc107);
            border: none;
        }

        .stats-card {
            background: linear-gradient(135deg, white, var(--gray-100));
            border-left: 4px solid var(--primary-blue);
        }

        .status-badge {
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-open { background: var(--status-open); color: white; }
        .status-in-progress { background: var(--status-in-progress); color: white; }
        .status-completed { background: var(--status-completed); color: white; }

        .priority-high { color: var(--priority-high); }
        .priority-medium { color: var(--priority-medium); }
        .priority-low { color: var(--priority-low); }

        /* AI Chat Widget Styles */
        .ai-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            max-height: 500px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
            z-index: 1000;
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .ai-chat-widget.minimized {
            height: 60px;
            width: 280px;
        }

        .chat-header {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
            color: white;
            padding: 12px 16px;
            display: flex;
            justify-content: between;
            align-items: center;
            cursor: pointer;
        }

        .chat-body {
            height: 300px;
            overflow-y: auto;
            padding: 16px;
            background: #f8f9fa;
        }

        .chat-message {
            margin-bottom: 12px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }

        .chat-message.user {
            flex-direction: row-reverse;
        }

        .message-content {
            background: white;
            padding: 10px 14px;
            border-radius: 12px;
            max-width: 80%;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .chat-message.user .message-content {
            background: var(--primary-blue);
            color: white;
        }

        .chat-input-area {
            padding: 12px;
            background: white;
            border-top: 1px solid var(--gray-200);
        }

        .icon-box {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            margin-bottom: 1rem;
        }

        .icon-assets { background: linear-gradient(135deg, #17a2b8, #20c997); }
        .icon-work-orders { background: linear-gradient(135deg, #fd7e14, #ffc107); }
        .icon-parts { background: linear-gradient(135deg, #6f42c1, #e83e8c); }
        .icon-ai { background: linear-gradient(135deg, #dc3545, #fd7e14); }

        @media (max-width: 768px) {
            .ai-chat-widget {
                width: 300px;
                right: 10px;
                bottom: 10px;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-tools me-2"></i>ChatterFix CMMS
            </a>
            <span class="navbar-text text-white-50">
                <i class="fas fa-robot me-1"></i>AI-Enhanced Maintenance
            </span>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container mt-4">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body text-center">
                        <h1 class="display-6 mb-3">
                            <i class="fas fa-industry text-primary me-3"></i>
                            Maintenance Management Dashboard
                        </h1>
                        <p class="lead text-muted">Professional CMMS with AI-powered assistance</p>
                        <div class="row mt-4">
                            <div class="col-md-4">
                                <div class="badge bg-success fs-6 p-2">
                                    <i class="fas fa-check-circle me-1"></i>All Systems Operational
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="badge bg-info fs-6 p-2">
                                    <i class="fas fa-robot me-1"></i>Fix It Fred AI: Active
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="badge bg-primary fs-6 p-2">
                                    <i class="fas fa-server me-1"></i>8 Microservices Running
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Statistics Cards -->
        <div class="row mb-4">
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card stats-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="icon-box icon-assets">
                                <i class="fas fa-industry"></i>
                            </div>
                            <div class="ms-3">
                                <h3 class="mb-0">{{ assets|length }}</h3>
                                <p class="text-muted mb-0">Active Assets</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card stats-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="icon-box icon-work-orders">
                                <i class="fas fa-clipboard-list"></i>
                            </div>
                            <div class="ms-3">
                                <h3 class="mb-0">{{ work_orders|length }}</h3>
                                <p class="text-muted mb-0">Work Orders</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card stats-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="icon-box icon-parts">
                                <i class="fas fa-cogs"></i>
                            </div>
                            <div class="ms-3">
                                <h3 class="mb-0">{{ parts|length }}</h3>
                                <p class="text-muted mb-0">Parts in Stock</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card stats-card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="icon-box icon-ai">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="ms-3">
                                <h3 class="mb-0">AI</h3>
                                <p class="text-muted mb-0">Assistant Ready</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="row">
            <!-- Assets Card -->
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <i class="fas fa-industry me-2"></i>Asset Management
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Monitor and manage your industrial assets</p>
                        <div class="mb-3">
                            {% for asset in assets[:2] %}
                            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                                <div>
                                    <strong>{{ asset.name }}</strong>
                                    <br><small class="text-muted">{{ asset.location }}</small>
                                </div>
                                <span class="badge bg-success">{{ asset.status }}</span>
                            </div>
                            {% endfor %}
                        </div>
                        <a href="/assets" class="btn btn-primary">
                            <i class="fas fa-arrow-right me-1"></i>Manage Assets
                        </a>
                        <button class="btn btn-success ms-2" onclick="askAI('Tell me about asset management best practices')">
                            <i class="fas fa-robot me-1"></i>Ask AI
                        </button>
                    </div>
                </div>
            </div>

            <!-- Work Orders Card -->
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <i class="fas fa-clipboard-list me-2"></i>Work Order Management
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Track and assign maintenance tasks</p>
                        <div class="mb-3">
                            {% for wo in work_orders[:2] %}
                            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                                <div>
                                    <strong>{{ wo.title }}</strong>
                                    <br><small class="text-muted">{{ wo.assigned_to }}</small>
                                </div>
                                <span class="status-badge status-{{ wo.status }}">{{ wo.status }}</span>
                            </div>
                            {% endfor %}
                        </div>
                        <a href="/work_orders" class="btn btn-warning">
                            <i class="fas fa-arrow-right me-1"></i>Manage Work Orders
                        </a>
                        <button class="btn btn-success ms-2" onclick="askAI('How should I prioritize work orders?')">
                            <i class="fas fa-robot me-1"></i>Ask AI
                        </button>
                    </div>
                </div>
            </div>

            <!-- Parts Inventory -->
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <i class="fas fa-boxes me-2"></i>Parts Inventory
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Monitor parts stock and reorder levels</p>
                        <div class="mb-3">
                            {% for part in parts %}
                            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                                <div>
                                    <strong>{{ part.name }}</strong>
                                    <br><small class="text-muted">Stock: {{ part.current_stock }}</small>
                                </div>
                                {% if part.current_stock <= part.min_stock_level %}
                                <span class="badge bg-danger">Low Stock</span>
                                {% else %}
                                <span class="badge bg-success">In Stock</span>
                                {% endif %}
                            </div>
                            {% endfor %}
                        </div>
                        <a href="/parts" class="btn btn-info">
                            <i class="fas fa-arrow-right me-1"></i>Manage Parts
                        </a>
                    </div>
                </div>
            </div>

            <!-- AI Assistant Card -->
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <i class="fas fa-robot me-2"></i>Fix It Fred AI Assistant
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Get intelligent maintenance recommendations</p>
                        <div class="mb-3">
                            <div class="alert alert-info">
                                <i class="fas fa-lightbulb me-2"></i>
                                <strong>AI Recommendation:</strong> Schedule preventive maintenance for assets with high usage hours.
                            </div>
                        </div>
                        <button class="btn btn-primary me-2" onclick="toggleChat()">
                            <i class="fas fa-comments me-1"></i>Open Chat
                        </button>
                        <button class="btn btn-secondary" onclick="showAISettings()">
                            <i class="fas fa-cog me-1"></i>AI Settings
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- AI Chat Widget -->
    <div id="aiChatWidget" class="ai-chat-widget minimized">
        <div class="chat-header" onclick="toggleChat()">
            <div>
                <i class="fas fa-robot me-2"></i>
                <span>Fix It Fred AI</span>
            </div>
            <div>
                <i id="chatToggleIcon" class="fas fa-chevron-up"></i>
            </div>
        </div>
        <div id="chatBody" class="chat-body" style="display: none;">
            <div class="chat-message">
                <div class="message-content">
                    <i class="fas fa-robot me-1"></i>
                    Hi! I'm Fix It Fred, your AI maintenance assistant. How can I help you today?
                </div>
            </div>
        </div>
        <div id="chatInputArea" class="chat-input-area" style="display: none;">
            <div class="input-group">
                <input type="text" id="chatInput" class="form-control" 
                       placeholder="Ask about maintenance, safety, or equipment..."
                       onkeypress="handleChatEnter(event)">
                <button class="btn btn-primary" onclick="sendChatMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>

    <!-- AI Settings Modal -->
    <div class="modal fade" id="aiSettingsModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-robot me-2"></i>Fix It Fred AI Settings
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">AI Provider</label>
                        <select id="aiProvider" class="form-select">
                            <option value="ollama">Ollama (Local)</option>
                            <option value="openai">OpenAI GPT</option>
                            <option value="anthropic">Anthropic Claude</option>
                            <option value="google">Google Gemini</option>
                            <option value="xai">xAI Grok</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Model</label>
                        <select id="aiModel" class="form-select">
                            <option value="mistral:latest">Mistral Latest</option>
                            <option value="llama3:latest">Llama 3 Latest</option>
                            <option value="qwen2.5-coder:7b">Qwen 2.5 Coder</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Temperature (Creativity)</label>
                        <input type="range" class="form-range" id="aiTemperature" min="0" max="1" step="0.1" value="0.7">
                        <small class="text-muted">Lower = More focused, Higher = More creative</small>
                    </div>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-1"></i>
                        Current Status: <span id="aiStatus">Loading...</span>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="saveAISettings()">Save Settings</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let chatExpanded = false;

        function toggleChat() {
            const widget = document.getElementById('aiChatWidget');
            const body = document.getElementById('chatBody');
            const input = document.getElementById('chatInputArea');
            const icon = document.getElementById('chatToggleIcon');
            
            chatExpanded = !chatExpanded;
            
            if (chatExpanded) {
                widget.classList.remove('minimized');
                body.style.display = 'block';
                input.style.display = 'block';
                icon.className = 'fas fa-chevron-down';
            } else {
                widget.classList.add('minimized');
                body.style.display = 'none';
                input.style.display = 'none';
                icon.className = 'fas fa-chevron-up';
            }
        }

        function addChatMessage(content, isUser = false) {
            const chatBody = document.getElementById('chatBody');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${isUser ? 'user' : ''}`;
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${isUser ? '' : '<i class="fas fa-robot me-1"></i>'}
                    ${content}
                </div>
            `;
            
            chatBody.appendChild(messageDiv);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addChatMessage(message, true);
            input.value = '';
            
            // Add thinking message
            addChatMessage('<i class="fas fa-spinner fa-spin me-1"></i>Thinking...');
            
            // Send to Fix It Fred AI
            fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                // Remove thinking message
                const chatBody = document.getElementById('chatBody');
                chatBody.removeChild(chatBody.lastChild);
                
                if (data.success) {
                    addChatMessage(data.fred_response);
                } else {
                    addChatMessage('Sorry, I encountered an error. Please try again.');
                }
            })
            .catch(error => {
                console.error('Chat error:', error);
                const chatBody = document.getElementById('chatBody');
                chatBody.removeChild(chatBody.lastChild);
                addChatMessage('Connection error. Please check that Fix It Fred AI is running.');
            });
        }

        function handleChatEnter(event) {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        }

        function askAI(question) {
            if (!chatExpanded) {
                toggleChat();
            }
            document.getElementById('chatInput').value = question;
            setTimeout(() => sendChatMessage(), 300);
        }

        function showAISettings() {
            // Load current AI status
            fetch('/api/ai/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('aiStatus').textContent = data.status || 'Unknown';
                })
                .catch(() => {
                    document.getElementById('aiStatus').textContent = 'Connection Error';
                });
            
            const modal = new bootstrap.Modal(document.getElementById('aiSettingsModal'));
            modal.show();
        }

        function saveAISettings() {
            const provider = document.getElementById('aiProvider').value;
            const model = document.getElementById('aiModel').value;
            const temperature = document.getElementById('aiTemperature').value;
            
            // In a real implementation, this would save to the AI service
            alert(`Settings saved: Provider: ${provider}, Model: ${model}, Temperature: ${temperature}`);
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('aiSettingsModal'));
            modal.hide();
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            // Auto-expand chat on first visit
            setTimeout(() => {
                if (!chatExpanded) {
                    toggleChat();
                    setTimeout(() => toggleChat(), 2000); // Auto-minimize after 2 seconds
                }
            }, 1000);
        });
    </script>
</body>
</html>
    ''', assets=assets_data, work_orders=work_orders_data, parts=parts_data)

@app.route('/assets')
def assets_page():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Assets - ChatterFix CMMS</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-blue: #006fee;
            --primary-blue-light: #4285f4;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }
        .navbar {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light)) !important;
        }
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-tools me-2"></i>ChatterFix CMMS
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h3><i class="fas fa-industry me-2"></i>Asset Management</h3>
                        <div>
                            <a href="/" class="btn btn-secondary me-2">
                                <i class="fas fa-arrow-left me-1"></i>Dashboard
                            </a>
                            <button onclick="addAsset()" class="btn btn-success">
                                <i class="fas fa-plus me-1"></i>Add Asset
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead class="table-light">
                                    <tr>
                                        <th>Asset</th>
                                        <th>Type</th>
                                        <th>Location</th>
                                        <th>Manufacturer</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for asset in assets %}
                                    <tr>
                                        <td>
                                            <strong>{{ asset.name }}</strong>
                                            <br><small class="text-muted">{{ asset.description }}</small>
                                        </td>
                                        <td>{{ asset.asset_type|title }}</td>
                                        <td>{{ asset.location }}</td>
                                        <td>{{ asset.manufacturer }} {{ asset.model }}</td>
                                        <td>
                                            <span class="badge bg-success">{{ asset.status|title }}</span>
                                        </td>
                                        <td>
                                            <button class="btn btn-sm btn-primary" onclick="editAsset('{{ asset.id }}')">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function addAsset() {
            const name = prompt('Asset Name:');
            if (!name) return;
            
            const description = prompt('Description:');
            const location = prompt('Location:');
            
            const data = {
                name: name,
                description: description || '',
                asset_type: 'equipment',
                location: location || '',
                status: 'active'
            };
            
            fetch('/api/assets', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(result => {
                if (result.success) {
                    alert('✅ Asset created successfully!');
                    location.reload();
                } else {
                    alert('❌ Error: ' + result.message);
                }
            })
            .catch(e => alert('❌ Error: ' + e.message));
        }
        
        function editAsset(id) {
            alert('Edit functionality - Asset ID: ' + id);
        }
    </script>
</body>
</html>
    ''', assets=assets_data)

@app.route('/work_orders')
def work_orders_page():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Work Orders - ChatterFix CMMS</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-blue: #006fee;
            --primary-blue-light: #4285f4;
            --status-open: #17a2b8;
            --status-in-progress: #fd7e14;
            --status-completed: #28a745;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }
        .navbar {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light)) !important;
        }
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        }
        .status-open { background: var(--status-open) !important; }
        .status-in-progress { background: var(--status-in-progress) !important; }
        .status-completed { background: var(--status-completed) !important; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-tools me-2"></i>ChatterFix CMMS
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h3><i class="fas fa-clipboard-list me-2"></i>Work Order Management</h3>
                        <div>
                            <a href="/" class="btn btn-secondary me-2">
                                <i class="fas fa-arrow-left me-1"></i>Dashboard
                            </a>
                            <button onclick="addWorkOrder()" class="btn btn-success">
                                <i class="fas fa-plus me-1"></i>Create Work Order
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead class="table-light">
                                    <tr>
                                        <th>Work Order</th>
                                        <th>Asset</th>
                                        <th>Assigned To</th>
                                        <th>Priority</th>
                                        <th>Status</th>
                                        <th>Due Date</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for wo in work_orders %}
                                    <tr>
                                        <td>
                                            <strong>{{ wo.title }}</strong>
                                            <br><small class="text-muted">{{ wo.description }}</small>
                                        </td>
                                        <td>Asset #{{ wo.asset_id }}</td>
                                        <td>{{ wo.assigned_to }}</td>
                                        <td>
                                            <span class="badge bg-{% if wo.priority == 'high' %}danger{% elif wo.priority == 'medium' %}warning{% else %}success{% endif %}">
                                                {{ wo.priority|title }}
                                            </span>
                                        </td>
                                        <td>
                                            <span class="badge status-{{ wo.status }}">{{ wo.status|title }}</span>
                                        </td>
                                        <td>{{ wo.due_date[:10] if wo.due_date else 'Not set' }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-primary" onclick="editWorkOrder('{{ wo.id }}')">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function addWorkOrder() {
            alert('Work order creation - functionality available via API');
        }
        
        function editWorkOrder(id) {
            alert('Edit work order - ID: ' + id);
        }
    </script>
</body>
</html>
    ''', work_orders=work_orders_data)

@app.route('/parts')
def parts_page():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Parts Inventory - ChatterFix CMMS</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --primary-blue: #006fee; --primary-blue-light: #4285f4; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }
        .navbar { background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light)) !important; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-tools me-2"></i>ChatterFix CMMS
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3><i class="fas fa-boxes me-2"></i>Parts Inventory</h3>
                <a href="/" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-1"></i>Dashboard
                </a>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead class="table-light">
                            <tr>
                                <th>Part</th>
                                <th>Part Number</th>
                                <th>Category</th>
                                <th>Stock</th>
                                <th>Cost</th>
                                <th>Supplier</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for part in parts %}
                            <tr>
                                <td><strong>{{ part.name }}</strong></td>
                                <td>{{ part.part_number }}</td>
                                <td>{{ part.category|title }}</td>
                                <td>{{ part.current_stock }} / {{ part.min_stock_level }}</td>
                                <td>${{ "%.2f"|format(part.unit_cost) }}</td>
                                <td>{{ part.supplier }}</td>
                                <td>
                                    {% if part.current_stock <= part.min_stock_level %}
                                    <span class="badge bg-danger">Low Stock</span>
                                    {% else %}
                                    <span class="badge bg-success">In Stock</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', parts=parts_data)

# API Endpoints
@app.route('/api/assets', methods=['GET'])
def get_assets():
    return jsonify(assets_data)

@app.route('/api/assets', methods=['POST'])
def create_asset():
    try:
        data = request.get_json()
        new_asset = {
            "id": str(uuid.uuid4())[:8],
            "name": data.get('name', ''),
            "description": data.get('description', ''),
            "asset_type": data.get('asset_type', 'equipment'),
            "location": data.get('location', ''),
            "status": data.get('status', 'active'),
            "manufacturer": data.get('manufacturer', ''),
            "model": data.get('model', ''),
            "created_at": datetime.now().isoformat()
        }
        assets_data.append(new_asset)
        return jsonify({"success": True, "message": "Asset created", "asset": new_asset})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/work_orders', methods=['GET'])
def get_work_orders():
    return jsonify(work_orders_data)

@app.route('/api/parts', methods=['GET'])
def get_parts():
    return jsonify(parts_data)

# Fix It Fred AI Integration
@app.route('/api/ai/health', methods=['GET'])
def ai_health():
    """Fix It Fred AI health check"""
    try:
        response = requests.get(f"{FRED_AI_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "service": "Fix It Fred AI",
                "status": "healthy",
                "fred_status": data.get("status"),
                "providers": data.get("providers", {}),
                "ollama_status": data.get("ollama_status"),
                "timestamp": data.get("timestamp")
            })
        else:
            return jsonify({"service": "Fix It Fred AI", "status": "unhealthy"}), 503
    except Exception as e:
        return jsonify({"service": "Fix It Fred AI", "status": "error", "message": str(e)}), 503

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat endpoint for Fix It Fred AI"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Forward to Fix It Fred AI Service
        response = requests.post(
            f"{FRED_AI_URL}/api/chat",
            json={
                "message": message,
                "provider": data.get("provider", "ollama"),
                "context": "cmms_maintenance"
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            fred_response = response.json()
            return jsonify({
                "success": True,
                "fred_response": fred_response.get("response", ""),
                "provider": fred_response.get("provider", "unknown"),
                "model": fred_response.get("model", "unknown"),
                "timestamp": fred_response.get("timestamp")
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Fix It Fred returned status {response.status_code}"
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Connection to Fix It Fred failed",
            "message": str(e)
        }), 503

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "ChatterFix CMMS Enhanced",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "assets_count": len(assets_data),
        "work_orders_count": len(work_orders_data),
        "parts_count": len(parts_data),
        "features": [
            "AI Chat Widget",
            "Rich Bootstrap Styling", 
            "Microservices Integration",
            "Real-time AI Assistant"
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)