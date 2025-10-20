#!/bin/bash
# Complete ChatterFix CMMS + All AI Providers Deployment to VM
set -e

echo "🚀 Complete ChatterFix CMMS Deployment with All AI Providers"
echo "============================================================"
echo "🤖 Deploying: Ollama + OpenAI + Anthropic + Google + xAI Grok"
echo ""

# Create complete deployment package
rm -rf complete-deployment
mkdir -p complete-deployment
cd complete-deployment

echo "📦 Creating complete deployment package..."

# Copy all enhanced files
cp ../core/cmms/enhanced_cmms_app.py ./
cp ../fix_it_fred_ai_service.py ./
cp ../core/cmms/database_service.py ./
cp ../core/cmms/work_orders_service.py ./
cp ../core/cmms/assets_service.py ./
cp ../core/cmms/parts_service.py ./

# Create enhanced app with all AI provider support
cat > enhanced_cmms_full_ai.py << 'EOF'
#!/usr/bin/env python3
"""
Complete ChatterFix CMMS with Full AI Provider Support
Ollama + OpenAI + Anthropic + Google + xAI Grok
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
import json
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# AI Service configuration
FRED_AI_URL = "http://localhost:8005"

@app.route('/')
def dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>ChatterFix CMMS - Complete AI-Enhanced Platform</title>
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
            --info-blue: #17a2b8;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light)) !important;
            box-shadow: 0 4px 15px rgba(0, 111, 238, 0.3);
        }
        
        .card {
            border: none;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }
        
        .card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
            border: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 111, 238, 0.4);
        }
        
        .ai-provider-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            margin: 0.25rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .ai-ollama { background: linear-gradient(135deg, #FF6B6B, #FF8E8E); color: white; }
        .ai-openai { background: linear-gradient(135deg, #00A67E, #00C896); color: white; }
        .ai-anthropic { background: linear-gradient(135deg, #FF7A00, #FF9500); color: white; }
        .ai-google { background: linear-gradient(135deg, #4285F4, #34A853); color: white; }
        .ai-grok { background: linear-gradient(135deg, #1DA1F2, #14171A); color: white; }
        
        .ai-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px;
            max-height: 600px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            overflow: hidden;
            border: 2px solid var(--primary-blue-light);
        }
        
        .chat-header {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
            color: white;
            padding: 16px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-body {
            height: 350px;
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
            padding: 12px 16px;
            border-radius: 16px;
            max-width: 80%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid #e9ecef;
        }
        
        .chat-message.user .message-content {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light));
            color: white;
            border: none;
        }
        
        .provider-selector {
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #e9ecef;
        }
        
        .chat-input-area {
            padding: 16px;
            background: white;
            border-top: 1px solid #e9ecef;
        }
        
        .floating-badge {
            position: absolute;
            top: -8px;
            right: -8px;
            background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot me-2"></i>ChatterFix CMMS
            </a>
            <span class="navbar-text text-white-50">
                <i class="fas fa-brain me-1"></i>Complete AI Platform • www.chatterfix.com
            </span>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body text-center">
                        <h1 class="display-5 mb-3">
                            <i class="fas fa-industry text-primary me-3"></i>
                            Complete AI-Enhanced CMMS
                        </h1>
                        <p class="lead text-muted mb-4">Professional maintenance management with 5 AI providers</p>
                        
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="mb-3">🤖 Available AI Providers</h5>
                                <div class="d-flex flex-wrap justify-content-center">
                                    <span class="ai-provider-badge ai-ollama">
                                        <i class="fas fa-desktop me-1"></i>Ollama Local
                                    </span>
                                    <span class="ai-provider-badge ai-openai">
                                        <i class="fas fa-brain me-1"></i>OpenAI GPT
                                    </span>
                                    <span class="ai-provider-badge ai-anthropic">
                                        <i class="fas fa-robot me-1"></i>Claude
                                    </span>
                                    <span class="ai-provider-badge ai-google">
                                        <i class="fab fa-google me-1"></i>Gemini
                                    </span>
                                    <span class="ai-provider-badge ai-grok">
                                        <i class="fab fa-twitter me-1"></i>Grok
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-3">
                                <div class="badge bg-success fs-6 p-2">
                                    <i class="fas fa-check-circle me-1"></i>VM Deployed
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="badge bg-info fs-6 p-2">
                                    <i class="fas fa-server me-1"></i>Microservices
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="badge bg-warning fs-6 p-2">
                                    <i class="fas fa-globe me-1"></i>HTTPS Ready
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="badge bg-primary fs-6 p-2">
                                    <i class="fas fa-magic me-1"></i>AI Enhanced
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-4 mb-4">
                <div class="card h-100 position-relative">
                    <div class="floating-badge">3</div>
                    <div class="card-header bg-primary text-white">
                        <i class="fas fa-industry me-2"></i>Smart Asset Management
                    </div>
                    <div class="card-body">
                        <h5>AI-Powered Asset Tracking</h5>
                        <p class="text-muted">Monitor equipment with AI recommendations</p>
                        <div class="d-grid gap-2">
                            <a href="/assets" class="btn btn-primary">
                                <i class="fas fa-cogs me-1"></i>Manage Assets
                            </a>
                            <button class="btn btn-outline-success" onclick="askAI('What are best practices for asset management?', 'openai')">
                                <i class="fas fa-brain me-1"></i>Ask GPT-4
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-4 mb-4">
                <div class="card h-100 position-relative">
                    <div class="floating-badge">5</div>
                    <div class="card-header bg-warning text-white">
                        <i class="fas fa-clipboard-list me-2"></i>Intelligent Work Orders
                    </div>
                    <div class="card-body">
                        <h5>AI-Optimized Workflows</h5>
                        <p class="text-muted">Smart scheduling and prioritization</p>
                        <div class="d-grid gap-2">
                            <a href="/work_orders" class="btn btn-warning">
                                <i class="fas fa-tasks me-1"></i>Manage Work Orders
                            </a>
                            <button class="btn btn-outline-info" onclick="askAI('How should I prioritize maintenance work orders?', 'anthropic')">
                                <i class="fas fa-robot me-1"></i>Ask Claude
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-4 mb-4">
                <div class="card h-100 position-relative">
                    <div class="floating-badge">AI</div>
                    <div class="card-header bg-info text-white">
                        <i class="fas fa-brain me-2"></i>Multi-AI Assistant
                    </div>
                    <div class="card-body">
                        <h5>Choose Your AI Expert</h5>
                        <p class="text-muted">5 AI providers for every maintenance need</p>
                        <div class="d-grid gap-2">
                            <button class="btn btn-info" onclick="showChat()">
                                <i class="fas fa-comments me-1"></i>Open AI Chat
                            </button>
                            <button class="btn btn-outline-primary" onclick="testAllProviders()">
                                <i class="fas fa-flask me-1"></i>Test All AIs
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
                        <i class="fas fa-chart-pulse me-2"></i>System Status & AI Performance
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>🚀 Deployment Features:</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-check text-success me-2"></i>Enhanced CMMS v3.0</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Bootstrap 5.3+ Advanced Styling</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Multi-AI Provider Support</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Real-time AI Chat Widget</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Microservices Architecture</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>🤖 AI Provider Status:</h6>
                                <div id="aiStatus" class="mb-3">
                                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                                    Checking AI providers...
                                </div>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-sm btn-outline-primary" onclick="checkAllAI()">
                                        <i class="fas fa-heartbeat me-1"></i>Health Check All AI
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Enhanced AI Chat Widget -->
    <div id="aiChat" class="ai-chat-widget" style="display: none;">
        <div class="chat-header" onclick="toggleChat()">
            <div>
                <i class="fas fa-brain me-2"></i>Fix It Fred AI
                <small class="d-block opacity-75">Multi-AI Assistant</small>
            </div>
            <div>
                <i id="chatToggleIcon" class="fas fa-chevron-down"></i>
            </div>
        </div>
        
        <div class="provider-selector">
            <label class="form-label small mb-1">Choose AI Provider:</label>
            <select id="aiProvider" class="form-select form-select-sm">
                <option value="ollama">🖥️ Ollama (Local)</option>
                <option value="openai">🧠 OpenAI GPT-4</option>
                <option value="anthropic">🤖 Anthropic Claude</option>
                <option value="google">🌟 Google Gemini</option>
                <option value="xai">🚀 xAI Grok</option>
            </select>
        </div>
        
        <div class="chat-body" id="chatMessages">
            <div class="chat-message">
                <div class="message-content">
                    <i class="fas fa-brain me-1"></i>
                    Hi! I'm Fix It Fred with access to 5 AI providers. Choose your preferred AI above and ask me anything about maintenance!
                </div>
            </div>
        </div>
        
        <div class="chat-input-area">
            <div class="input-group">
                <input type="text" id="chatInput" class="form-control" 
                       placeholder="Ask any AI about maintenance..."
                       onkeypress="handleChatEnter(event)">
                <button class="btn btn-primary" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let chatExpanded = false;
        
        function showChat() {
            document.getElementById('aiChat').style.display = 'block';
            chatExpanded = true;
        }
        
        function toggleChat() {
            const chat = document.getElementById('aiChat');
            if (chatExpanded) {
                chat.style.display = 'none';
                chatExpanded = false;
            } else {
                showChat();
            }
        }
        
        function addMessage(content, isUser = false, provider = '') {
            const messages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${isUser ? 'user' : ''}`;
            
            const providerIcon = {
                'ollama': '🖥️',
                'openai': '🧠', 
                'anthropic': '🤖',
                'google': '🌟',
                'xai': '🚀'
            };
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${isUser ? '' : (providerIcon[provider] || '<i class="fas fa-brain me-1"></i>')}
                    ${content}
                    ${provider && !isUser ? `<div class="small text-muted mt-1">via ${provider}</div>` : ''}
                </div>
            `;
            
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('chatInput');
            const provider = document.getElementById('aiProvider').value;
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, true);
            input.value = '';
            
            addMessage('<i class="fas fa-cog fa-spin me-1"></i>AI thinking...', false, provider);
            
            fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    provider: provider,
                    context: 'maintenance'
                })
            })
            .then(response => response.json())
            .then(data => {
                const messages = document.getElementById('chatMessages');
                messages.removeChild(messages.lastChild);
                
                if (data.success) {
                    addMessage(data.fred_response, false, provider);
                } else {
                    addMessage(`${provider} AI is not available right now. Try another provider.`, false, provider);
                }
            })
            .catch(error => {
                const messages = document.getElementById('chatMessages');
                messages.removeChild(messages.lastChild);
                addMessage('Connection error. AI services may be starting up.', false, provider);
            });
        }
        
        function askAI(question, provider = 'ollama') {
            showChat();
            document.getElementById('aiProvider').value = provider;
            document.getElementById('chatInput').value = question;
            setTimeout(() => sendMessage(), 500);
        }
        
        function handleChatEnter(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function checkAllAI() {
            fetch('/api/ai/health')
                .then(response => response.json())
                .then(data => {
                    const providers = data.providers || {};
                    const status = Object.entries(providers)
                        .map(([name, enabled]) => `${name}: ${enabled ? '✅' : '❌'}`)
                        .join('\\n');
                    alert(`AI Provider Status:\\n${status}\\n\\nOllama: ${data.ollama_status || 'unknown'}`);
                })
                .catch(error => {
                    alert('AI health check failed. Services may be starting up.');
                });
        }
        
        function testAllProviders() {
            showChat();
            const providers = ['ollama', 'openai', 'anthropic', 'google', 'xai'];
            let currentProvider = 0;
            
            function testNext() {
                if (currentProvider < providers.length) {
                    const provider = providers[currentProvider];
                    document.getElementById('aiProvider').value = provider;
                    document.getElementById('chatInput').value = `Test ${provider} AI provider`;
                    setTimeout(() => {
                        sendMessage();
                        currentProvider++;
                        setTimeout(testNext, 3000);
                    }, 1000);
                }
            }
            testNext();
        }
        
        // Auto-load AI status on page load
        document.addEventListener('DOMContentLoaded', function() {
            checkAIStatus();
        });
        
        function checkAIStatus() {
            fetch('/api/ai/health')
                .then(response => response.json())
                .then(data => {
                    const providers = data.providers || {};
                    const enabledCount = Object.values(providers).filter(Boolean).length;
                    const statusEl = document.getElementById('aiStatus');
                    
                    statusEl.innerHTML = `
                        <div class="text-success">
                            <i class="fas fa-check-circle me-1"></i>
                            ${enabledCount}/5 AI providers active
                        </div>
                        <small class="text-muted">
                            Ollama: ${data.ollama_status === 'running' ? '✅' : '❌'} | 
                            Cloud AIs: ${enabledCount - 1}/4 enabled
                        </small>
                    `;
                })
                .catch(error => {
                    document.getElementById('aiStatus').innerHTML = `
                        <div class="text-warning">
                            <i class="fas fa-exclamation-triangle me-1"></i>
                            AI services starting up...
                        </div>
                    `;
                });
        }
    </script>
</body>
</html>
    ''')

@app.route('/assets')
def assets():
    return render_template_string('''
    <div class="container mt-4">
        <h1><i class="fas fa-industry me-2"></i>Asset Management</h1>
        <p class="lead">AI-enhanced asset tracking and management</p>
        <a href="/" class="btn btn-primary">Back to Dashboard</a>
    </div>
    ''')

@app.route('/work_orders')
def work_orders():
    return render_template_string('''
    <div class="container mt-4">
        <h1><i class="fas fa-clipboard-list me-2"></i>Work Order Management</h1>
        <p class="lead">Intelligent work order processing with AI assistance</p>
        <a href="/" class="btn btn-primary">Back to Dashboard</a>
    </div>
    ''')

@app.route('/api/ai/health')
def ai_health():
    try:
        response = requests.get(f"{FRED_AI_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "unhealthy", "service": "Fix It Fred AI"}, 503
    except:
        return {
            "status": "offline", 
            "service": "Fix It Fred AI", 
            "providers": {
                "ollama": False,
                "openai": False, 
                "anthropic": False,
                "google": False,
                "xai": False
            },
            "message": "AI services starting up..."
        }, 503

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        provider = data.get('provider', 'ollama')
        context = data.get('context', 'maintenance')
        
        response = requests.post(
            f"{FRED_AI_URL}/api/chat",
            json={
                "message": message, 
                "provider": provider,
                "context": context
            },
            timeout=45
        )
        
        if response.status_code == 200:
            fred_response = response.json()
            return {
                "success": True,
                "fred_response": fred_response.get("response", "AI response received"),
                "provider": fred_response.get("provider", provider),
                "model": fred_response.get("model", "unknown")
            }
        else:
            return {
                "success": False, 
                "error": f"{provider} AI service unavailable",
                "message": "Try another AI provider"
            }, 503
            
    except Exception as e:
        return {
            "success": False, 
            "error": f"AI connection failed: {str(e)}",
            "message": "AI services may be starting up"
        }, 503

@app.route('/health')
def health():
    return {
        "status": "ok",
        "service": "ChatterFix CMMS Complete AI Platform",
        "version": "3.0.0-VM-COMPLETE",
        "timestamp": datetime.now().isoformat(),
        "deployment": "VM Production with Full AI Suite",
        "features": [
            "Complete AI Integration",
            "5 AI Providers (Ollama, OpenAI, Anthropic, Google, xAI)",
            "Enhanced Bootstrap UI",
            "Real-time Multi-AI Chat",
            "Microservices Architecture",
            "Professional CMMS Platform"
        ],
        "ai_providers": ["Ollama", "OpenAI", "Anthropic", "Google Gemini", "xAI Grok"]
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
EOF

# Create VM deployment script
cat > deploy-to-vm.sh << 'EOF'
#!/bin/bash
# VM Deployment Script for Complete ChatterFix AI Platform
set -e

echo "🚀 Deploying Complete ChatterFix CMMS + All AI Providers to VM"
echo "============================================================="

# Setup directories
sudo mkdir -p /var/www/chatterfix
sudo mkdir -p /var/log/chatterfix
sudo chown -R $USER:$USER /var/www/chatterfix /var/log/chatterfix

# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip nginx curl

# Install Python dependencies
pip3 install fastapi uvicorn flask flask-cors requests pydantic python-dotenv

# Copy application files
cp *.py /var/www/chatterfix/
cd /var/www/chatterfix

# Create environment file with API keys
cat > .env << 'ENV_EOF'
# AI Provider API Keys - UPDATE THESE
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
XAI_API_KEY=your_xai_grok_key_here

# Service Configuration
PORT=8080
FRED_AI_PORT=8005
DATABASE_URL=sqlite:///chatterfix.db
ENV_EOF

echo "⚠️  IMPORTANT: Update API keys in /var/www/chatterfix/.env"

# Create systemd service for main app
sudo tee /etc/systemd/system/chatterfix-main.service > /dev/null << 'MAIN_EOF'
[Unit]
Description=ChatterFix CMMS Main Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8080
ExecStart=/usr/bin/python3 enhanced_cmms_full_ai.py
Restart=always
RestartSec=3
EnvironmentFile=/var/www/chatterfix/.env

[Install]
WantedBy=multi-user.target
MAIN_EOF

# Create systemd service for Fix It Fred AI
sudo tee /etc/systemd/system/chatterfix-ai.service > /dev/null << 'AI_EOF'
[Unit]
Description=Fix It Fred AI Service with All Providers
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8005
ExecStart=/usr/bin/python3 fix_it_fred_ai_service.py
Restart=always
RestartSec=3
EnvironmentFile=/var/www/chatterfix/.env

[Install]
WantedBy=multi-user.target
AI_EOF

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/chatterfix > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    listen 443 ssl http2;
    server_name chatterfix.com www.chatterfix.com;
    
    # SSL Configuration (update with your certificates)
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Main application
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # AI API endpoints
    location /api/ai/ {
        proxy_pass http://localhost:8005/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }
    
    # Health checks
    location /health {
        proxy_pass http://localhost:8080/health;
        proxy_set_header Host $host;
    }
    
    # Static files and caching
    location /static/ {
        alias /var/www/chatterfix/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
NGINX_EOF

# Enable Nginx site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/chatterfix /etc/nginx/sites-enabled/
sudo nginx -t

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload

# Start AI service first
sudo systemctl enable chatterfix-ai
sudo systemctl start chatterfix-ai
sleep 3

# Start main application
sudo systemctl enable chatterfix-main
sudo systemctl start chatterfix-main
sleep 2

# Start Nginx
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check status
echo "🔍 Service Status:"
echo "=================="
sudo systemctl status chatterfix-main --no-pager -l | head -10
echo ""
sudo systemctl status chatterfix-ai --no-pager -l | head -10
echo ""
sudo systemctl status nginx --no-pager -l | head -5

echo ""
echo "✅ Complete ChatterFix AI Platform Deployed!"
echo "============================================="
echo "🌐 Access at: https://www.chatterfix.com"
echo "🤖 AI Providers: Ollama + OpenAI + Anthropic + Google + xAI Grok"
echo ""
echo "📊 Quick Health Check:"
curl -s http://localhost:8080/health | jq . || echo "Main app: Starting..."
echo ""
curl -s http://localhost:8005/health | jq . || echo "AI service: Starting..."

echo ""
echo "⚠️  Next Steps:"
echo "1. Update API keys in /var/www/chatterfix/.env"
echo "2. Restart services: sudo systemctl restart chatterfix-*"
echo "3. Configure SSL certificates for HTTPS"
echo "4. Test all AI providers at www.chatterfix.com"

EOF

chmod +x deploy-to-vm.sh

echo "✅ Complete deployment package created!"
echo ""
echo "📦 Package Contents:"
ls -la
echo ""
echo "🚀 Features Included:"
echo "- Enhanced CMMS with Bootstrap 5.3+ styling"
echo "- Complete Fix It Fred AI with 5 providers:"
echo "  🖥️  Ollama (Local AI)"
echo "  🧠 OpenAI GPT-4/3.5"
echo "  🤖 Anthropic Claude"
echo "  🌟 Google Gemini"
echo "  🚀 xAI Grok"
echo "- Advanced AI chat widget with provider selection"
echo "- Microservices architecture"
echo "- Professional UI with animations and gradients"
echo "- Real-time AI status monitoring"
echo ""
echo "🚀 Ready for VM deployment!"
echo "Copy files to VM and run: ./deploy-to-vm.sh"