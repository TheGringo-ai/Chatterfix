#!/bin/bash
# Quick fix for ChatterFix VM internal server error
set -e

echo "🔧 Quick VM Fix - Deploying Enhanced CMMS"
echo "========================================"

# Create a simple enhanced app that will work on the VM
cat > vm_enhanced_app.py << 'EOF'
#!/usr/bin/env python3
"""
Enhanced ChatterFix CMMS for VM Deployment
Fixed for production environment
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
import json
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
FRED_AI_URL = "http://localhost:8005"

@app.route('/')
def dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>ChatterFix CMMS - Enhanced Maintenance Management</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-blue: #006fee;
            --primary-blue-light: #4285f4;
            --success-green: #28a745;
            --warning-orange: #fd7e14;
            --danger-red: #dc3545;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light)) !important;
            box-shadow: 0 2px 10px rgba(0, 111, 238, 0.3);
        }
        
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
            border: none;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 111, 238, 0.4);
        }
        
        .ai-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 320px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
            z-index: 1000;
        }
        
        .chat-header {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
            color: white;
            padding: 12px 16px;
            border-radius: 16px 16px 0 0;
            cursor: pointer;
        }
        
        .status-badge {
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-tools me-2"></i>ChatterFix CMMS
            </a>
            <span class="navbar-text text-white-50">
                <i class="fas fa-robot me-1"></i>AI-Enhanced • VM Deployed
            </span>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body text-center">
                        <h1 class="display-6 mb-3">
                            <i class="fas fa-industry text-primary me-3"></i>
                            Enhanced CMMS Dashboard
                        </h1>
                        <p class="lead text-muted">Professional maintenance management with AI assistance</p>
                        <div class="row mt-4">
                            <div class="col-md-3">
                                <div class="badge bg-success fs-6 p-2">
                                    <i class="fas fa-check-circle me-1"></i>VM Deployed
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="badge bg-info fs-6 p-2">
                                    <i class="fas fa-robot me-1"></i>Fix It Fred AI
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="badge bg-primary fs-6 p-2">
                                    <i class="fas fa-server me-1"></i>Microservices
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="badge bg-warning fs-6 p-2">
                                    <i class="fas fa-globe me-1"></i>www.chatterfix.com
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-header bg-primary text-white">
                        <i class="fas fa-industry me-2"></i>Asset Management
                    </div>
                    <div class="card-body">
                        <h5>Monitor Your Assets</h5>
                        <p class="text-muted">Track equipment, machinery, and infrastructure</p>
                        <div class="d-grid gap-2">
                            <a href="/assets" class="btn btn-primary">Manage Assets</a>
                            <button class="btn btn-outline-success" onclick="testAI('assets')">
                                <i class="fas fa-robot me-1"></i>Ask AI About Assets
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-header bg-warning text-white">
                        <i class="fas fa-clipboard-list me-2"></i>Work Orders
                    </div>
                    <div class="card-body">
                        <h5>Maintenance Tasks</h5>
                        <p class="text-muted">Create, assign, and track work orders</p>
                        <div class="d-grid gap-2">
                            <a href="/work_orders" class="btn btn-warning">Manage Work Orders</a>
                            <button class="btn btn-outline-success" onclick="testAI('workorders')">
                                <i class="fas fa-robot me-1"></i>Ask AI About Work Orders
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-header bg-info text-white">
                        <i class="fas fa-robot me-2"></i>Fix It Fred AI
                    </div>
                    <div class="card-body">
                        <h5>AI Assistant</h5>
                        <p class="text-muted">Get intelligent maintenance recommendations</p>
                        <div class="d-grid gap-2">
                            <button class="btn btn-info" onclick="showChat()">
                                <i class="fas fa-comments me-1"></i>Open AI Chat
                            </button>
                            <button class="btn btn-outline-primary" onclick="testConnection()">
                                <i class="fas fa-heartbeat me-1"></i>Test AI Connection
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-chart-line me-2"></i>System Status
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Deployment Info:</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-check text-success me-2"></i>Enhanced CMMS v2.0</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Bootstrap 5.3+ Styling</li>
                                    <li><i class="fas fa-check text-success me-2"></i>AI Chat Integration</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Responsive Design</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>Quick Actions:</h6>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-sm btn-outline-primary" onclick="checkHealth()">
                                        <i class="fas fa-heartbeat me-1"></i>Health Check
                                    </button>
                                    <button class="btn btn-sm btn-outline-info" onclick="testAI('general')">
                                        <i class="fas fa-robot me-1"></i>Test AI
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- AI Chat Widget -->
    <div id="aiChat" class="ai-chat-widget" style="display: none;">
        <div class="chat-header" onclick="hideChat()">
            <i class="fas fa-robot me-2"></i>Fix It Fred AI
            <span class="float-end"><i class="fas fa-times"></i></span>
        </div>
        <div class="p-3">
            <div id="chatMessages" style="height: 200px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; margin-bottom: 10px;">
                <div class="text-muted">
                    <i class="fas fa-robot me-1"></i>Hi! I'm Fix It Fred, your AI maintenance assistant.
                </div>
            </div>
            <div class="input-group">
                <input type="text" id="chatInput" class="form-control" placeholder="Ask me anything about maintenance...">
                <button class="btn btn-primary" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showChat() {
            document.getElementById('aiChat').style.display = 'block';
        }
        
        function hideChat() {
            document.getElementById('aiChat').style.display = 'none';
        }
        
        function addMessage(content, isUser = false) {
            const messages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `mb-2 ${isUser ? 'text-end' : ''}`;
            messageDiv.innerHTML = `
                <div class="badge ${isUser ? 'bg-primary' : 'bg-light text-dark'} p-2">
                    ${isUser ? '' : '<i class="fas fa-robot me-1"></i>'}${content}
                </div>
            `;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            input.value = '';
            
            addMessage('<i class="fas fa-spinner fa-spin"></i> Thinking...');
            
            fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                const messages = document.getElementById('chatMessages');
                messages.removeChild(messages.lastChild);
                
                if (data.success) {
                    addMessage(data.fred_response);
                } else {
                    addMessage('Sorry, AI service is not available right now.');
                }
            })
            .catch(error => {
                const messages = document.getElementById('chatMessages');
                messages.removeChild(messages.lastChild);
                addMessage('Connection error. AI service may be starting up.');
            });
        }
        
        function testAI(context) {
            showChat();
            const questions = {
                'assets': 'What are best practices for asset management?',
                'workorders': 'How should I prioritize work orders?',
                'general': 'What maintenance tips do you recommend?'
            };
            document.getElementById('chatInput').value = questions[context] || questions.general;
            setTimeout(() => sendMessage(), 500);
        }
        
        function testConnection() {
            fetch('/api/ai/health')
                .then(response => response.json())
                .then(data => {
                    alert(`AI Status: ${data.status}\\nService: ${data.service}\\nProviders: ${Object.keys(data.providers || {}).join(', ')}`);
                })
                .catch(error => {
                    alert('AI service connection failed. It may be starting up.');
                });
        }
        
        function checkHealth() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    alert(`System Status: ${data.status}\\nService: ${data.service}\\nVersion: ${data.version}\\nFeatures: ${data.features ? data.features.join(', ') : 'Basic'}`);
                })
                .catch(error => {
                    alert('Health check failed');
                });
        }
        
        // Allow Enter key in chat
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
    ''')

@app.route('/assets')
def assets():
    return "<h1>Assets Management</h1><p>Asset management interface coming soon.</p><a href='/'>Back to Dashboard</a>"

@app.route('/work_orders')
def work_orders():
    return "<h1>Work Orders</h1><p>Work order management interface coming soon.</p><a href='/'>Back to Dashboard</a>"

@app.route('/api/ai/health')
def ai_health():
    try:
        response = requests.get(f"{FRED_AI_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "unhealthy", "service": "Fix It Fred AI"}, 503
    except:
        return {"status": "offline", "service": "Fix It Fred AI", "message": "Service not available"}, 503

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        response = requests.post(
            f"{FRED_AI_URL}/api/chat",
            json={"message": message, "provider": "ollama"},
            timeout=30
        )
        
        if response.status_code == 200:
            fred_response = response.json()
            return {
                "success": True,
                "fred_response": fred_response.get("response", "AI response received"),
                "provider": fred_response.get("provider", "unknown")
            }
        else:
            return {"success": False, "error": "AI service unavailable"}, 503
            
    except:
        return {"success": False, "error": "AI connection failed"}, 503

@app.route('/health')
def health():
    return {
        "status": "ok",
        "service": "ChatterFix CMMS Enhanced",
        "version": "2.0.0-VM",
        "timestamp": datetime.now().isoformat(),
        "deployment": "VM Production",
        "features": [
            "Enhanced UI",
            "AI Chat Widget", 
            "Bootstrap 5.3+ Styling",
            "VM Optimized"
        ]
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
EOF

echo "✅ Enhanced VM app created: vm_enhanced_app.py"
echo ""
echo "🚀 To deploy this to your VM:"
echo "1. Copy to VM: scp vm_enhanced_app.py your-vm-user@your-vm-ip:~/"
echo "2. SSH to VM: ssh your-vm-user@your-vm-ip"
echo "3. Stop current service: sudo systemctl stop chatterfix"
echo "4. Replace app: sudo cp vm_enhanced_app.py /var/www/chatterfix/app.py"
echo "5. Restart: sudo systemctl start chatterfix"
echo ""
echo "Or provide VM details to deploy automatically."