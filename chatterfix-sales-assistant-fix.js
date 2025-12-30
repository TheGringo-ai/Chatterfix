// ChatterFix.com Sales Assistant Fix
// This script fixes the broken click handler on the live site
// Inject this script or update the live site with this corrected function

(function() {
    'use strict';
    
    console.log('🔧 ChatterFix Sales Assistant Fix Loading...');
    
    // Fixed toggle function that properly handles the initial state
    function fixedToggleSalesChat() {
        const chatWindow = document.getElementById('salesChatWindow');
        const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
        
        if (!chatWindow || !chatToggle) {
            console.error('Sales chat elements not found!');
            return;
        }
        
        // Better check that handles both 'none' and empty string cases
        const currentDisplay = window.getComputedStyle(chatWindow).display;
        const isHidden = currentDisplay === 'none';
        
        console.log('Toggle clicked. Currently hidden:', isHidden);
        
        if (isHidden) {
            // Show chat window
            chatWindow.style.display = 'flex';
            chatWindow.style.visibility = 'visible';
            chatToggle.style.display = 'none';
            console.log('✅ Chat window opened');
        } else {
            // Hide chat window  
            chatWindow.style.display = 'none';
            chatWindow.style.visibility = 'hidden';
            chatToggle.style.display = 'flex';
            console.log('✅ Chat window closed');
        }
    }
    
    // Replace the global function
    window.toggleSalesChat = fixedToggleSalesChat;
    
    // Also add a more robust click handler as backup
    function addBackupClickHandler() {
        const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
        const chatClose = document.querySelector('.chat-close');
        
        if (chatToggle) {
            // Remove existing onclick and add new event listener
            chatToggle.removeAttribute('onclick');
            chatToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                fixedToggleSalesChat();
            });
            console.log('✅ Fixed click handler attached to chat toggle');
        }
        
        if (chatClose) {
            chatClose.removeAttribute('onclick');
            chatClose.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                fixedToggleSalesChat();
            });
            console.log('✅ Fixed click handler attached to close button');
        }
    }
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addBackupClickHandler);
    } else {
        addBackupClickHandler();
    }
    
    // Test function to verify the fix works
    window.testSalesAssistantFix = function() {
        console.log('🧪 Testing sales assistant fix...');
        const chatWindow = document.getElementById('salesChatWindow');
        const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
        
        if (chatWindow && chatToggle) {
            console.log('Elements found:', {
                chatWindow: !!chatWindow,
                chatToggle: !!chatToggle,
                currentDisplay: window.getComputedStyle(chatWindow).display,
                styleDisplay: chatWindow.style.display
            });
            
            // Test the toggle
            fixedToggleSalesChat();
            return 'Fix test completed - check console for details';
        } else {
            return 'Elements not found - fix may not be applicable';
        }
    };
    
    console.log('✅ ChatterFix Sales Assistant Fix Loaded Successfully!');
    console.log('💡 Test the fix by calling: testSalesAssistantFix()');
    
})();