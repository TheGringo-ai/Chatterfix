#!/usr/bin/env python3
"""
AI Assistant Injector for ChatterFix CMMS
Ensures the AI assistant is available on all pages by injecting the script
"""

import re
from typing import Optional


class AIAssistantInjector:
    """Injects AI assistant script into HTML responses"""
    
    def __init__(self):
        self.ai_script_tag = '''
<!-- Universal AI Assistant Loader -->
<script>
(function() {
    'use strict';
    
    // Check if AI assistant is already loaded
    if (window.aiAssistantInitialized) {
        return;
    }
    
    // Mark as loading to prevent multiple loads
    window.aiAssistantLoading = true;
    
    console.log('🤖 Loading Universal AI Assistant...');
    
    // Load the global AI assistant script
    const script = document.createElement('script');
    script.src = '/static/js/global-ai-assistant.js';
    script.async = true;
    
    script.onload = function() {
        console.log('✅ Global AI Assistant script loaded');
        
        // Initialize the AI assistant if the function exists
        if (typeof loadGlobalAIAssistant === 'function') {
            loadGlobalAIAssistant();
            console.log('✅ AI Assistant initialized on page:', window.location.pathname);
        } else {
            console.warn('⚠️ loadGlobalAIAssistant function not found');
        }
        
        window.aiAssistantLoading = false;
    };
    
    script.onerror = function() {
        console.error('❌ Failed to load AI Assistant script');
        window.aiAssistantLoading = false;
        
        // Create a fallback AI button
        createFallbackAIButton();
    };
    
    // Add script to page
    document.head.appendChild(script);
    
    // Fallback AI button for when script loading fails
    function createFallbackAIButton() {
        const fallbackButton = document.createElement('div');
        fallbackButton.id = 'fallback-ai-button';
        fallbackButton.innerHTML = '🤖';
        fallbackButton.style.cssText = `
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
            z-index: 9998;
            transition: all 0.3s ease;
            border: 2px solid rgba(255,255,255,0.2);
            animation: aiPulse 2s infinite;
        `;
        
        fallbackButton.onclick = function() {
            // Redirect to main dashboard where AI works
            const currentPage = window.location.pathname;
            const message = encodeURIComponent(`I was on ${currentPage} and wanted to use the AI assistant`);
            window.location.href = `/dashboard?ai_message=${message}`;
        };
        
        fallbackButton.title = 'AI Assistant (click to access)';
        document.body.appendChild(fallbackButton);
        
        console.log('🔄 Fallback AI button created');
    }
    
    // Add CSS for AI assistant
    const style = document.createElement('style');
    style.textContent = `
        @keyframes aiPulse {
            0%, 100% { transform: scale(1); box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); }
            50% { transform: scale(1.05); box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6); }
        }
        
        #global-ai-button, #fallback-ai-button {
            z-index: 999999 !important;
        }
        
        #global-ai-popup {
            z-index: 1000000 !important;
        }
        
        @media (max-width: 768px) {
            #global-ai-button, #fallback-ai-button {
                width: 50px !important;
                height: 50px !important;
                font-size: 20px !important;
                bottom: 15px !important;
                right: 15px !important;
            }
            
            #global-ai-popup {
                width: calc(100vw - 20px) !important;
                height: 400px !important;
                right: 10px !important;
                bottom: 80px !important;
            }
        }
    `;
    document.head.appendChild(style);
    
})();

// Ensure AI assistant loads even on dynamic pages
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            if (!window.aiAssistantInitialized && !window.aiAssistantLoading) {
                console.log('🔄 AI Assistant not loaded, initializing fallback...');
                if (typeof createFallbackAIButton === 'function') {
                    createFallbackAIButton();
                }
            }
        }, 2000);
    });
}
</script>
<!-- End Universal AI Assistant Loader -->
'''

    def inject_ai_assistant(self, html_content: str) -> str:
        """
        Inject AI assistant script into HTML content
        
        Args:
            html_content: The HTML content to inject into
            
        Returns:
            HTML content with AI assistant script injected
        """
        
        # Check if AI assistant is already present
        if 'global-ai-assistant' in html_content or 'aiAssistantInitialized' in html_content:
            return html_content
        
        # Try to inject before closing </head> tag
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{self.ai_script_tag}\n</head>')
            return html_content
        
        # Fallback: inject before closing </body> tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{self.ai_script_tag}\n</body>')
            return html_content
        
        # Last resort: append to end of HTML
        if '</html>' in html_content:
            html_content = html_content.replace('</html>', f'{self.ai_script_tag}\n</html>')
            return html_content
        
        # If no proper HTML structure, just append
        return html_content + self.ai_script_tag

    def should_inject_ai(self, path: str, content_type: str = 'text/html') -> bool:
        """
        Determine if AI assistant should be injected into this response
        
        Args:
            path: Request path
            content_type: Response content type
            
        Returns:
            True if AI should be injected
        """
        
        # Only inject into HTML responses
        if 'text/html' not in content_type:
            return False
        
        # Skip API endpoints
        if path.startswith('/api/'):
            return False
        
        # Skip static files
        if any(path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.ico', '.woff', '.svg']):
            return False
        
        # Skip health checks and probes
        if path in ['/health', '/favicon.ico', '/robots.txt']:
            return False
        
        # Include all dashboard and CMMS pages
        include_patterns = [
            '/dashboard',
            '/cmms',
            '/work-orders',
            '/assets', 
            '/parts',
            '/maintenance',
            '/reports',
            '/admin',
            '/ai-dashboard',
            '/settings'
        ]
        
        # Check if path matches any include pattern
        for pattern in include_patterns:
            if path.startswith(pattern):
                return True
        
        # Include root and main pages
        if path in ['/', '/index', '/home']:
            return True
        
        return False


# Middleware function for FastAPI
def ai_assistant_middleware(request, response, html_content: str) -> str:
    """
    Middleware function to inject AI assistant into HTML responses
    
    Args:
        request: FastAPI request object
        response: FastAPI response object  
        html_content: HTML content to process
        
    Returns:
        Processed HTML content with AI assistant
    """
    
    injector = AIAssistantInjector()
    
    # Get request path and content type
    path = request.url.path
    content_type = response.headers.get('content-type', '')
    
    # Check if we should inject AI assistant
    if injector.should_inject_ai(path, content_type):
        html_content = injector.inject_ai_assistant(html_content)
        print(f"🤖 AI Assistant injected into {path}")
    
    return html_content


# Example usage for testing
if __name__ == "__main__":
    # Test the injector
    injector = AIAssistantInjector()
    
    # Test HTML without AI assistant
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CMMS Dashboard</title>
    </head>
    <body>
        <h1>Work Orders</h1>
        <div>Content here</div>
    </body>
    </html>
    """
    
    # Inject AI assistant
    enhanced_html = injector.inject_ai_assistant(test_html)
    
    # Check if injection worked
    if 'aiAssistantInitialized' in enhanced_html:
        print("✅ AI Assistant injection test passed")
    else:
        print("❌ AI Assistant injection test failed")
    
    # Test path checking
    test_paths = [
        ('/dashboard', True),
        ('/work-orders', True), 
        ('/api/health', False),
        ('/static/css/style.css', False),
        ('/cmms/assets', True)
    ]
    
    for path, expected in test_paths:
        result = injector.should_inject_ai(path, 'text/html')
        status = "✅" if result == expected else "❌"
        print(f"{status} Path {path}: {result} (expected {expected})")