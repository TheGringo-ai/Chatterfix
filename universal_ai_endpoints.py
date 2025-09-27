#!/usr/bin/env python3
"""
Universal AI Assistant Endpoints for ChatterFix CMMS
Provides endpoints that inject AI assistant into ALL pages automatically
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
import re
from typing import Optional


def add_universal_ai_endpoints(app: FastAPI):
    """Add universal AI assistant endpoints to the FastAPI app"""
    
    @app.get("/ai-inject.js", response_class=PlainTextResponse)
    async def serve_ai_injector_script():
        """Serve a self-contained AI assistant script that works on any page"""
        
        return '''
/**
 * Universal AI Assistant for ChatterFix CMMS
 * Self-contained script that works on ANY page
 * Just add: <script src="/ai-inject.js"></script>
 */

(function() {
    'use strict';
    
    // Prevent multiple loads
    if (window.chatterFixAILoaded) return;
    window.chatterFixAILoaded = true;
    
    console.log('🤖 ChatterFix Universal AI Assistant Loading...');
    
    // Create the floating AI assistant
    function createAIAssistant() {
        // Remove any existing assistant
        const existing = document.getElementById('universal-ai-assistant');
        if (existing) existing.remove();
        
        // Create AI button
        const aiButton = document.createElement('div');
        aiButton.id = 'universal-ai-assistant';
        aiButton.innerHTML = '🤖';
        aiButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
            z-index: 999999;
            transition: all 0.3s ease;
            border: 2px solid rgba(255,255,255,0.2);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            animation: aiPulse 2s infinite;
        `;
        
        // Create AI modal
        const aiModal = document.createElement('div');
        aiModal.id = 'universal-ai-modal';
        aiModal.style.cssText = `
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 400px;
            height: 500px;
            background: rgba(10, 10, 10, 0.95);
            border-radius: 20px;
            border: 1px solid rgba(102, 126, 234, 0.3);
            backdrop-filter: blur(20px);
            z-index: 1000000;
            display: none;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        `;
        
        aiModal.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea, #764ba2);
                padding: 15px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                color: white;
                font-weight: bold;
            ">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">🤖</span>
                    <span>ChatterFix AI Assistant</span>
                    <div style="
                        width: 8px;
                        height: 8px;
                        background: #38ef7d;
                        border-radius: 50%;
                        animation: pulse 2s infinite;
                    "></div>
                </div>
                <button onclick="closeAIModal()" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                ">×</button>
            </div>
            
            <div id="ai-messages" style="
                flex: 1;
                padding: 15px;
                overflow-y: auto;
                background: rgba(0,0,0,0.2);
                max-height: 350px;
            ">
                <div style="
                    background: linear-gradient(135deg, rgba(56, 239, 125, 0.2), rgba(102, 126, 234, 0.2));
                    padding: 12px 15px;
                    border-radius: 15px;
                    margin-bottom: 10px;
                    font-size: 14px;
                    line-height: 1.4;
                ">
                    👋 Hi! I'm your AI maintenance assistant. I can help you:
                    <br>• Create work orders with voice commands
                    <br>• Troubleshoot equipment issues  
                    <br>• Answer maintenance questions
                    <br>• Schedule preventive maintenance
                    <br><br>Try: <em>"Emergency pump leak in Building A"</em>
                </div>
            </div>
            
            <div style="
                padding: 15px;
                background: rgba(0,0,0,0.3);
                border-top: 1px solid rgba(102, 126, 234, 0.2);
            ">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input 
                        type="text" 
                        id="ai-input" 
                        placeholder="Type your maintenance question..." 
                        style="
                            flex: 1;
                            padding: 10px 15px;
                            border: 1px solid rgba(102, 126, 234, 0.3);
                            border-radius: 20px;
                            background: rgba(0,0,0,0.5);
                            color: white;
                            outline: none;
                            font-size: 14px;
                        "
                    />
                    <button 
                        onclick="sendAIMessage()" 
                        style="
                            width: 40px;
                            height: 40px;
                            border: none;
                            border-radius: 50%;
                            background: linear-gradient(135deg, #38ef7d, #11998e);
                            color: white;
                            font-size: 16px;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        "
                    >➤</button>
                </div>
                
                <div style="
                    margin-top: 10px;
                    font-size: 11px;
                    color: rgba(255,255,255,0.6);
                    line-height: 1.3;
                ">
                    <strong>Examples:</strong><br>
                    • "Emergency pump leak in Building A"<br>
                    • "Schedule motor maintenance"<br>
                    • "HVAC making noise in office"
                </div>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(aiButton);
        document.body.appendChild(aiModal);
        
        // Event listeners
        aiButton.onclick = toggleAIModal;
        
        // Enter key support
        const input = document.getElementById('ai-input');
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendAIMessage();
                }
            });
        }
        
        console.log('✅ Universal AI Assistant created');
    }
    
    // Global functions
    window.toggleAIModal = function() {
        const modal = document.getElementById('universal-ai-modal');
        if (modal) {
            const isVisible = modal.style.display === 'flex';
            modal.style.display = isVisible ? 'none' : 'flex';
            
            if (!isVisible) {
                const input = document.getElementById('ai-input');
                if (input) input.focus();
            }
        }
    };
    
    window.closeAIModal = function() {
        const modal = document.getElementById('universal-ai-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    };
    
    window.sendAIMessage = async function() {
        const input = document.getElementById('ai-input');
        const messagesDiv = document.getElementById('ai-messages');
        
        if (!input || !messagesDiv) return;
        
        const message = input.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage('user', message);
        input.value = '';
        
        // Add thinking message
        const thinkingId = addMessage('ai', '🤔 Processing...', true);
        
        try {
            const response = await fetch('/global-ai/process-message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    page: window.location.pathname,
                    context: 'universal_ai'
                })
            });
            
            const data = await response.json();
            
            // Remove thinking message
            removeMessage(thinkingId);
            
            if (data.success) {
                addMessage('ai', data.response);
                
                // Show actions if any
                if (data.actions && data.actions.length > 0) {
                    data.actions.forEach(action => {
                        addMessage('system', `Action: ${action}`);
                    });
                }
            } else {
                addMessage('ai', 'Sorry, I encountered an error. Please try again.');
            }
            
        } catch (error) {
            removeMessage(thinkingId);
            addMessage('ai', 'Connection error. Please check your connection and try again.');
        }
    };
    
    function addMessage(type, text, temporary = false) {
        const messagesDiv = document.getElementById('ai-messages');
        if (!messagesDiv) return null;
        
        const messageDiv = document.createElement('div');
        const messageId = temporary ? 'temp-' + Date.now() : null;
        
        if (messageId) messageDiv.id = messageId;
        
        const styles = {
            user: 'background: linear-gradient(135deg, #667eea, #764ba2); margin-left: 20px; text-align: right;',
            ai: 'background: linear-gradient(135deg, rgba(56, 239, 125, 0.2), rgba(102, 126, 234, 0.2)); margin-right: 20px;',
            system: 'background: rgba(255, 193, 7, 0.2); margin: 0 10px; font-size: 12px; font-style: italic;'
        };
        
        messageDiv.style.cssText = `
            padding: 12px 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            font-size: 14px;
            line-height: 1.4;
            word-wrap: break-word;
            ${styles[type]}
        `;
        
        messageDiv.textContent = text;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        return messageId;
    }
    
    function removeMessage(messageId) {
        if (messageId) {
            const element = document.getElementById(messageId);
            if (element) element.remove();
        }
    }
    
    // Add CSS animations
    function addCSS() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes aiPulse {
                0%, 100% { 
                    transform: scale(1); 
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); 
                }
                50% { 
                    transform: scale(1.05); 
                    box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6); 
                }
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            /* Mobile responsive */
            @media (max-width: 768px) {
                #universal-ai-assistant {
                    width: 50px !important;
                    height: 50px !important;
                    font-size: 20px !important;
                    bottom: 15px !important;
                    right: 15px !important;
                }
                
                #universal-ai-modal {
                    width: calc(100vw - 20px) !important;
                    height: 400px !important;
                    right: 10px !important;
                    bottom: 80px !important;
                }
            }
            
            /* Scrollbar styling */
            #ai-messages::-webkit-scrollbar {
                width: 6px;
            }
            
            #ai-messages::-webkit-scrollbar-track {
                background: rgba(0,0,0,0.1);
            }
            
            #ai-messages::-webkit-scrollbar-thumb {
                background: rgba(102, 126, 234, 0.5);
                border-radius: 3px;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Initialize everything
    function initialize() {
        addCSS();
        createAIAssistant();
        
        console.log('🎉 Universal AI Assistant ready on:', window.location.pathname);
        
        // Debug info
        console.log('🔍 Page context:', {
            page: window.location.pathname,
            title: document.title,
            timestamp: new Date().toISOString()
        });
    }
    
    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
})();
        '''
    
    @app.middleware("http")
    async def inject_ai_assistant_middleware(request: Request, call_next):
        """Middleware to inject AI assistant into HTML responses"""
        
        response = await call_next(request)
        
        # Only process HTML responses
        if (response.headers.get("content-type", "").startswith("text/html") and
            hasattr(response, 'body')):
            
            # Get the response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Decode the HTML
            try:
                html_content = body.decode('utf-8')
                
                # Check if this is an HTML page that should have AI assistant
                if should_inject_ai(request.url.path, html_content):
                    # Inject the AI assistant script
                    html_content = inject_ai_script(html_content)
                    
                    # Update the response
                    response = Response(
                        content=html_content,
                        status_code=response.status_code,
                        headers=response.headers,
                        media_type="text/html"
                    )
                    
                    print(f"🤖 AI Assistant injected into {request.url.path}")
                
            except UnicodeDecodeError:
                # If we can't decode, return original response
                pass
        
        return response


def should_inject_ai(path: str, html_content: str) -> bool:
    """Determine if AI assistant should be injected into this page"""
    
    # Skip if AI assistant script is already present (check for specific markers)
    if ('chatterFixAILoaded' in html_content or 
        'universal-ai-assistant' in html_content or
        'ai-inject.js' in html_content):
        return False
    
    # Skip API endpoints and static files
    if (path.startswith('/api/') or 
        path.startswith('/static/') or
        path in ['/health', '/favicon.ico', '/robots.txt'] or
        any(path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.ico', '.woff', '.svg'])):
        return False
    
    # Include dashboard and CMMS pages
    include_patterns = [
        '/dashboard', '/cmms', '/work-orders', '/assets', '/parts',
        '/maintenance', '/reports', '/admin', '/settings', '/ai-dashboard'
    ]
    
    # Include if path matches patterns or is main page
    return (any(path.startswith(pattern) for pattern in include_patterns) or 
            path in ['/', '/index', '/home'] or
            '<html' in html_content.lower())


def inject_ai_script(html_content: str) -> str:
    """Inject AI assistant script into HTML content"""
    
    ai_script = '<script src="/ai-inject.js" async></script>'
    
    # Try to inject before closing </head> tag
    if '</head>' in html_content:
        return html_content.replace('</head>', f'{ai_script}\n</head>')
    
    # Fallback: inject before closing </body> tag
    if '</body>' in html_content:
        return html_content.replace('</body>', f'{ai_script}\n</body>')
    
    # Last resort: append to end
    if '</html>' in html_content:
        return html_content.replace('</html>', f'{ai_script}\n</html>')
    
    # If no proper HTML structure, just append
    return html_content + ai_script


# Example usage for FastAPI app
if __name__ == "__main__":
    from fastapi import FastAPI
    
    app = FastAPI()
    add_universal_ai_endpoints(app)
    
    print("✅ Universal AI endpoints added to FastAPI app")
    print("🤖 AI assistant will be available on ALL pages")
    print("📱 Responsive design included for mobile users")
    print("🎯 Voice commands ready for production use")