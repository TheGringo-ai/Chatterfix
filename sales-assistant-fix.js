// Fixed Sales Assistant JavaScript for chatterfix.com
// This fixes the click handler issue on the live site

function toggleSalesChat() {
    const chatWindow = document.getElementById('salesChatWindow');
    const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
    
    console.log('Toggle clicked! Current display:', chatWindow.style.display);
    console.log('Chat window:', chatWindow);
    console.log('Chat toggle:', chatToggle);
    
    // Check if window is currently hidden (handles both 'none' and empty string)
    const isHidden = chatWindow.style.display === 'none' || 
                     chatWindow.style.display === '' || 
                     window.getComputedStyle(chatWindow).display === 'none';
    
    if (isHidden) {
        // Show chat window
        chatWindow.style.display = 'flex';
        chatWindow.style.visibility = 'visible';
        chatToggle.style.display = 'none';
        console.log('Showing chat window');
    } else {
        // Hide chat window
        chatWindow.style.display = 'none';
        chatWindow.style.visibility = 'hidden';
        chatToggle.style.display = 'flex';
        console.log('Hiding chat window');
    }
}

// Also add some debugging to see what's happening
document.addEventListener('DOMContentLoaded', function() {
    const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
    const chatWindow = document.getElementById('salesChatWindow');
    
    console.log('DOM loaded. Chat elements:', {
        toggle: chatToggle,
        window: chatWindow,
        windowDisplay: chatWindow ? chatWindow.style.display : 'not found'
    });
    
    // Make sure the click handler is properly attached
    if (chatToggle) {
        chatToggle.addEventListener('click', function(e) {
            console.log('Click event triggered!');
            e.preventDefault();
            e.stopPropagation();
            toggleSalesChat();
        });
        console.log('Click handler attached to chat toggle');
    } else {
        console.error('Chat toggle not found!');
    }
});

// Quick test function to verify everything works
function testSalesChat() {
    console.log('Testing sales chat...');
    const chatWindow = document.getElementById('salesChatWindow');
    const chatToggle = document.querySelector('#ai-sales-chat .chat-toggle');
    
    console.log('Elements found:', {
        chatWindow: !!chatWindow,
        chatToggle: !!chatToggle,
        windowDisplay: chatWindow ? chatWindow.style.display : 'N/A',
        computedDisplay: chatWindow ? window.getComputedStyle(chatWindow).display : 'N/A'
    });
    
    if (chatWindow && chatToggle) {
        toggleSalesChat();
        return 'Toggle attempted';
    } else {
        return 'Elements not found';
    }
}

// Make functions globally available
window.toggleSalesChat = toggleSalesChat;
window.testSalesChat = testSalesChat;