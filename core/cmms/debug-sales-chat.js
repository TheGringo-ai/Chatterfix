// ChatterFix Sales Chat Debug Script
// Inject this into the browser console to debug the sales chat issue

(function() {
    'use strict';
    
    console.log('🔧 ChatterFix Sales Chat Debug Script Starting...');
    
    // Check if elements exist
    function checkElements() {
        const chatWindow = document.getElementById('salesChatWindow');
        const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
        const aiSalesChat = document.getElementById('ai-sales-chat');
        
        console.log('🔍 Element Check:');
        console.log('  salesChatWindow:', !!chatWindow, chatWindow);
        console.log('  chat-toggle:', !!chatToggle, chatToggle);
        console.log('  ai-sales-chat:', !!aiSalesChat, aiSalesChat);
        
        if (chatWindow) {
            console.log('  Window display:', chatWindow.style.display);
            console.log('  Window computed display:', window.getComputedStyle(chatWindow).display);
            console.log('  Window visibility:', chatWindow.style.visibility);
        }
        
        return { chatWindow, chatToggle, aiSalesChat };
    }
    
    // Check current toggle function
    function checkToggleFunction() {
        console.log('🔍 Function Check:');
        console.log('  toggleSalesChat exists:', typeof window.toggleSalesChat);
        if (typeof window.toggleSalesChat === 'function') {
            console.log('  Function code:', window.toggleSalesChat.toString().substring(0, 200) + '...');
        }
    }
    
    // Test the toggle function
    function testToggle() {
        console.log('🧪 Testing toggle function...');
        const { chatWindow, chatToggle } = checkElements();
        
        if (chatWindow && chatToggle) {
            console.log('Before click - Display:', chatWindow.style.display);
            
            // Try clicking the toggle
            chatToggle.click();
            
            setTimeout(() => {
                console.log('After click - Display:', chatWindow.style.display);
                console.log('After click - Computed:', window.getComputedStyle(chatWindow).display);
            }, 100);
        }
    }
    
    // Inject a fixed version
    function injectFixedVersion() {
        console.log('🔧 Injecting fixed toggle function...');
        
        window.toggleSalesChat = function() {
            console.log('🤖 FIXED SALES CHAT CLICKED');
            
            const chatWindow = document.getElementById('salesChatWindow');
            const chatWidget = document.getElementById('ai-sales-chat');
            
            if (!chatWindow) {
                console.error('❌ Sales chat window not found!');
                return;
            }
            
            // Use computed style for reliable checking
            const currentDisplay = window.getComputedStyle(chatWindow).display;
            const isHidden = currentDisplay === 'none';
            
            console.log('Current display:', currentDisplay, 'Hidden:', isHidden);
            
            if (isHidden) {
                // Show chat window
                chatWindow.style.display = 'flex';
                chatWindow.style.flexDirection = 'column';
                chatWindow.style.position = 'fixed';
                chatWindow.style.bottom = '80px';
                chatWindow.style.right = '20px';
                chatWindow.style.zIndex = '99999';
                chatWindow.style.background = 'white';
                chatWindow.style.border = '1px solid #ccc';
                chatWindow.style.borderRadius = '8px';
                chatWindow.style.width = '350px';
                chatWindow.style.height = '500px';
                chatWindow.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)';
                
                // Hide toggle button
                const toggleBtn = chatWidget.querySelector('.chat-toggle');
                if (toggleBtn) toggleBtn.style.display = 'none';
                
                console.log('✅ Sales chat OPENED');
            } else {
                // Hide chat window
                chatWindow.style.display = 'none';
                
                // Show toggle button
                const toggleBtn = chatWidget.querySelector('.chat-toggle');
                if (toggleBtn) toggleBtn.style.display = 'flex';
                
                console.log('✅ Sales chat CLOSED');
            }
        };
        
        // Add event listeners
        const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
        const chatClose = document.querySelector('.chat-close');
        
        if (chatToggle) {
            chatToggle.removeAttribute('onclick');
            chatToggle.onclick = window.toggleSalesChat;
            console.log('✅ Fixed click handler attached to toggle');
        }
        
        if (chatClose) {
            chatClose.removeAttribute('onclick');
            chatClose.onclick = window.toggleSalesChat;
            console.log('✅ Fixed click handler attached to close button');
        }
    }
    
    // Run diagnostics
    function runDiagnostics() {
        console.log('🔍 Running full diagnostics...');
        checkElements();
        checkToggleFunction();
        
        // Check for errors
        const originalError = console.error;
        let errorCount = 0;
        console.error = function(...args) {
            errorCount++;
            originalError.apply(console, args);
        };
        
        setTimeout(() => {
            console.log('Error count since start:', errorCount);
            console.error = originalError;
        }, 1000);
    }
    
    // Main execution
    console.log('🚀 Starting diagnostics...');
    runDiagnostics();
    
    console.log('🔧 Injecting fixed version...');
    injectFixedVersion();
    
    console.log('🧪 Testing functionality...');
    setTimeout(testToggle, 1000);
    
    // Add global test function
    window.debugSalesChat = function() {
        runDiagnostics();
        testToggle();
    };
    
    window.fixSalesChat = injectFixedVersion;
    
    console.log('✅ Debug script loaded!');
    console.log('💡 Available commands:');
    console.log('  debugSalesChat() - Run diagnostics');
    console.log('  fixSalesChat() - Inject fixed version');
    console.log('  toggleSalesChat() - Test the toggle function');
    
})();