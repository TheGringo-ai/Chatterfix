/**
 * Universal AI Assistant Loader for ChatterFix CMMS
 * Ensures the AI assistant loads on ALL pages across the application
 */

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
        `;
        
        fallbackButton.onclick = function() {
            // Redirect to main dashboard where AI works
            const currentPage = window.location.pathname;
            const message = encodeURIComponent(`I was on ${currentPage} and wanted to use the AI assistant`);
            window.location.href = `/dashboard?ai_message=${message}`;
        };
        
        fallbackButton.title = 'AI Assistant (click to go to main dashboard)';
        document.body.appendChild(fallbackButton);
        
        console.log('🔄 Fallback AI button created');
    }
    
    // Enhanced page detection for better AI context
    function detectPageContext() {
        const path = window.location.pathname;
        const contexts = {
            '/work-orders': 'work_orders',
            '/assets': 'assets',
            '/parts': 'parts', 
            '/maintenance': 'maintenance',
            '/reports': 'reports',
            '/dashboard': 'main_dashboard',
            '/cmms': 'cmms_dashboard',
            '/admin': 'admin',
            '/settings': 'settings'
        };
        
        for (const [pathPattern, context] of Object.entries(contexts)) {
            if (path.includes(pathPattern)) {
                return context;
            }
        }
        
        return 'general';
    }
    
    // Store page context for AI assistant
    window.chatterFixPageContext = detectPageContext();
    
    // Add CSS for better AI assistant appearance across all pages
    const style = document.createElement('style');
    style.textContent = `
        /* Ensure AI assistant appears above all other elements */
        #global-ai-button, #fallback-ai-button {
            z-index: 999999 !important;
        }
        
        #global-ai-popup {
            z-index: 1000000 !important;
        }
        
        /* Responsive adjustments for mobile */
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
        
        /* Animation for AI button */
        @keyframes universalAiPulse {
            0%, 100% { 
                transform: scale(1); 
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); 
            }
            50% { 
                transform: scale(1.05); 
                box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6); 
            }
        }
        
        #global-ai-button, #fallback-ai-button {
            animation: universalAiPulse 2s infinite;
        }
    `;
    document.head.appendChild(style);
    
    // Debug information
    console.log('🔍 Universal AI Loader initialized on:', {
        page: window.location.pathname,
        context: window.chatterFixPageContext,
        timestamp: new Date().toISOString()
    });
    
})();

// Ensure AI assistant loads even if page loads after DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Additional check after DOM is ready
        setTimeout(function() {
            if (!window.aiAssistantInitialized && !window.aiAssistantLoading) {
                console.log('🔄 AI Assistant not loaded, retrying...');
                window.location.reload();
            }
        }, 3000);
    });
}