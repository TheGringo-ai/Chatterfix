/**
 * Universal AI Assistant Initializer
 * Add this ONE script tag to any page to ensure AI assistant loads
 * Usage: <script src="/static/js/ai-universal-init.js"></script>
 */

(function() {
    'use strict';
    
    console.log('🤖 Universal AI Initializer loaded on:', window.location.pathname);
    
    // Prevent multiple initializations
    if (window.aiUniversalLoaded) {
        console.log('🔄 Universal AI already loaded, skipping...');
        return;
    }
    window.aiUniversalLoaded = true;
    
    // Configuration
    const AI_SCRIPT_URL = '/static/js/global-ai-assistant.js';
    const FALLBACK_ENABLED = true;
    const DEBUG_MODE = true;
    
    // Debug logging
    function debugLog(message, data = null) {
        if (DEBUG_MODE) {
            console.log(`🤖 [AI-Universal] ${message}`, data || '');
        }
    }
    
    // Check if AI assistant script already exists
    function isAIScriptLoaded() {
        return document.querySelector(`script[src="${AI_SCRIPT_URL}"]`) !== null ||
               typeof loadGlobalAIAssistant === 'function' ||
               window.aiAssistantInitialized;
    }
    
    // Load AI assistant script dynamically
    function loadAIScript() {
        debugLog('Loading AI assistant script...');
        
        const script = document.createElement('script');
        script.src = AI_SCRIPT_URL;
        script.async = true;
        
        script.onload = function() {
            debugLog('AI script loaded successfully');
            initializeAI();
        };
        
        script.onerror = function() {
            debugLog('AI script failed to load, creating fallback');
            if (FALLBACK_ENABLED) {
                createFallbackAI();
            }
        };
        
        document.head.appendChild(script);
    }
    
    // Initialize AI assistant after script loads
    function initializeAI() {
        if (typeof loadGlobalAIAssistant === 'function') {
            try {
                loadGlobalAIAssistant();
                debugLog('AI assistant initialized successfully');
            } catch (error) {
                debugLog('AI initialization failed:', error);
                if (FALLBACK_ENABLED) {
                    createFallbackAI();
                }
            }
        } else {
            debugLog('loadGlobalAIAssistant function not found');
            if (FALLBACK_ENABLED) {
                createFallbackAI();
            }
        }
    }
    
    // Create fallback AI button when main script fails
    function createFallbackAI() {
        debugLog('Creating fallback AI button');
        
        // Remove any existing fallback
        const existing = document.getElementById('ai-fallback-button');
        if (existing) {
            existing.remove();
        }
        
        const button = document.createElement('div');
        button.id = 'ai-fallback-button';
        button.innerHTML = '🤖';
        button.title = 'AI Assistant - Click to access';
        
        // Style the fallback button
        button.style.cssText = `
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
        `;
        
        // Add hover effect
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
            this.style.boxShadow = '0 6px 25px rgba(102, 126, 234, 0.6)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.4)';
        });
        
        // Handle click - open simple modal or redirect
        button.addEventListener('click', function() {
            debugLog('Fallback AI button clicked');
            openSimpleAIModal();
        });
        
        document.body.appendChild(button);
        debugLog('Fallback AI button created');
    }
    
    // Simple AI modal for fallback
    function openSimpleAIModal() {
        // Remove existing modal
        const existing = document.getElementById('ai-fallback-modal');
        if (existing) {
            existing.remove();
            return;
        }
        
        const modal = document.createElement('div');
        modal.id = 'ai-fallback-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000000;
        `;
        
        modal.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea, #764ba2);
                padding: 30px;
                border-radius: 20px;
                max-width: 400px;
                width: 90%;
                color: white;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            ">
                <div style="font-size: 48px; margin-bottom: 20px;">🤖</div>
                <h2 style="margin: 0 0 15px 0; font-size: 24px;">ChatterFix AI Assistant</h2>
                <p style="margin: 0 0 20px 0; opacity: 0.9; line-height: 1.5;">
                    I'm here to help with maintenance tasks, work orders, and technical questions.
                </p>
                <div style="margin: 20px 0;">
                    <input type="text" id="ai-fallback-input" placeholder="Ask me about maintenance..." style="
                        width: 100%;
                        padding: 12px 15px;
                        border: none;
                        border-radius: 25px;
                        font-size: 16px;
                        margin-bottom: 15px;
                        box-sizing: border-box;
                    ">
                    <button onclick="sendFallbackMessage()" style="
                        background: white;
                        color: #667eea;
                        border: none;
                        padding: 12px 30px;
                        border-radius: 25px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        margin-right: 10px;
                    ">Send</button>
                    <button onclick="closeFallbackModal()" style="
                        background: transparent;
                        color: white;
                        border: 2px solid white;
                        padding: 10px 20px;
                        border-radius: 25px;
                        font-size: 16px;
                        cursor: pointer;
                    ">Close</button>
                </div>
                <div id="ai-fallback-response" style="
                    margin-top: 20px;
                    padding: 15px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    display: none;
                "></div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Focus input
        const input = document.getElementById('ai-fallback-input');
        if (input) {
            input.focus();
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendFallbackMessage();
                }
            });
        }
        
        // Close on background click
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeFallbackModal();
            }
        });
    }
    
    // Global functions for fallback modal
    window.sendFallbackMessage = function() {
        const input = document.getElementById('ai-fallback-input');
        const response = document.getElementById('ai-fallback-response');
        
        if (input && response) {
            const message = input.value.trim();
            if (!message) return;
            
            response.style.display = 'block';
            response.innerHTML = '🤔 Processing...';
            
            // Send to AI API
            fetch('/global-ai/process-message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    response.innerHTML = `<strong>AI:</strong> ${data.response}`;
                } else {
                    response.innerHTML = '<strong>Error:</strong> Unable to process request.';
                }
            })
            .catch(error => {
                response.innerHTML = '<strong>Error:</strong> Connection failed. Please try again.';
            });
            
            input.value = '';
        }
    };
    
    window.closeFallbackModal = function() {
        const modal = document.getElementById('ai-fallback-modal');
        if (modal) {
            modal.remove();
        }
    };
    
    // Add responsive CSS
    function addResponsiveCSS() {
        const style = document.createElement('style');
        style.textContent = `
            @media (max-width: 768px) {
                #ai-fallback-button {
                    width: 50px !important;
                    height: 50px !important;
                    font-size: 20px !important;
                    bottom: 15px !important;
                    right: 15px !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Main initialization logic
    function initializeUniversalAI() {
        debugLog('Starting universal AI initialization...');
        
        addResponsiveCSS();
        
        if (isAIScriptLoaded()) {
            debugLog('AI already loaded, attempting to initialize...');
            initializeAI();
        } else {
            debugLog('AI not loaded, loading script...');
            loadAIScript();
        }
    }
    
    // Start initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeUniversalAI);
    } else {
        initializeUniversalAI();
    }
    
    debugLog('Universal AI Initializer setup complete');
    
})();