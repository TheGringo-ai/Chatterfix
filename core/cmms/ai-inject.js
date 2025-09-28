/**
 * ChatterFix CMMS - Mars-Level AI Assistant Injector
 * 🚀 Advanced floating AI assistant with multi-provider support
 */

// Create the floating button with Mars-level styling
const createFloatingButton = () => {
    const button = document.createElement('div');
    button.id = 'chatterfix-ai-button';
    button.innerHTML = '🤖'; // AI Robot icon
    button.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(45deg, #FF6B35, #F7931E, #FFD23F);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 8px 20px rgba(255, 107, 53, 0.4);
        z-index: 10000;
        font-size: 24px;
        transition: all 0.3s ease;
        border: 3px solid rgba(255, 255, 255, 0.2);
        animation: pulse 2s infinite;
    `;
    
    // Add hover effects
    button.addEventListener('mouseenter', () => {
        button.style.transform = 'scale(1.1)';
        button.style.boxShadow = '0 12px 30px rgba(255, 107, 53, 0.6)';
    });
    
    button.addEventListener('mouseleave', () => {
        button.style.transform = 'scale(1)';
        button.style.boxShadow = '0 8px 20px rgba(255, 107, 53, 0.4)';
    });
    
    document.body.appendChild(button);
    return button;
};

// Create the Mars-level chat interface
const createChatInterface = () => {
    const chatBox = document.createElement('div');
    chatBox.id = 'chatterfix-ai-interface';
    chatBox.style.cssText = `
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 350px;
        height: 500px;
        background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
        border: 2px solid #FF6B35;
        border-radius: 15px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        display: none;
        z-index: 10000;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        overflow: hidden;
    `;
    
    chatBox.innerHTML = `
        <div id="chatterfix-ai-header" style="
            background: linear-gradient(45deg, #FF6B35, #F7931E);
            color: white;
            padding: 15px;
            border-radius: 13px 13px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
        ">
            <div style="display: flex; align-items: center; gap: 8px;">
                🚀 ChatterFix AI Assistant
                <span style="font-size: 10px; background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 10px;">MARS-LEVEL</span>
            </div>
            <span id="close-chatterfix-ai" style="cursor: pointer; font-size: 18px; opacity: 0.8; hover: opacity: 1;">✖</span>
        </div>
        
        <div id="ai-provider-selector" style="
            background: rgba(255, 107, 53, 0.1);
            padding: 10px;
            display: flex;
            gap: 5px;
            justify-content: center;
        ">
            <button class="ai-provider-btn" data-provider="ollama" style="
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 15px;
                cursor: pointer;
                font-size: 10px;
                font-weight: bold;
            ">🦙 LLAMA</button>
            <button class="ai-provider-btn" data-provider="openai" style="
                background: linear-gradient(45deg, #00D4AA, #00B894);
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 15px;
                cursor: pointer;
                font-size: 10px;
                font-weight: bold;
            ">🧠 ChatGPT</button>
            <button class="ai-provider-btn" data-provider="grok" style="
                background: linear-gradient(45deg, #E17055, #D63031);
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 15px;
                cursor: pointer;
                font-size: 10px;
                font-weight: bold;
            ">⚡ Grok</button>
        </div>
        
        <div id="chatterfix-ai-messages" style="
            height: 340px;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            scrollbar-width: thin;
            scrollbar-color: #FF6B35 transparent;
            scroll-behavior: smooth;
            max-height: 340px;
            position: relative;
        ">
            <div id="scroll-to-top" style="
                position: absolute;
                top: 10px;
                right: 10px;
                width: 30px;
                height: 30px;
                background: rgba(255, 107, 53, 0.8);
                border-radius: 50%;
                display: none;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 1000;
                font-size: 14px;
                color: white;
                transition: all 0.3s ease;
            " title="Scroll to top">↑</div>
            <div id="scroll-to-bottom" style="
                position: absolute;
                bottom: 10px;
                right: 10px;
                width: 30px;
                height: 30px;
                background: rgba(255, 107, 53, 0.8);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 1000;
                font-size: 14px;
                color: white;
                transition: all 0.3s ease;
            " title="Scroll to bottom">↓</div>
        </div>
        
        <div style="padding: 15px; background: rgba(0, 0, 0, 0.2);">
            <div style="display: flex; gap: 10px;">
                <input id="chatterfix-ai-input" placeholder="Ask ChatterFix AI anything..." style="
                    flex: 1;
                    padding: 12px;
                    border: 2px solid #FF6B35;
                    border-radius: 25px;
                    background: rgba(255, 255, 255, 0.9);
                    color: #333;
                    outline: none;
                    font-size: 14px;
                ">
                <button id="send-message-btn" style="
                    background: linear-gradient(45deg, #FF6B35, #F7931E);
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-weight: bold;
                ">🚀</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(chatBox);
    return chatBox;
};

// Add CSS animations
const addAnimations = () => {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { box-shadow: 0 8px 20px rgba(255, 107, 53, 0.4); }
            50% { box-shadow: 0 8px 20px rgba(255, 107, 53, 0.8); }
            100% { box-shadow: 0 8px 20px rgba(255, 107, 53, 0.4); }
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .ai-message {
            animation: slideIn 0.3s ease;
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: linear-gradient(45deg, #FF6B35, #F7931E);
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .ai-response {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border: 1px solid rgba(255, 107, 53, 0.3);
        }
        
        .ai-provider-btn:hover {
            transform: scale(1.05);
            transition: transform 0.2s ease;
        }
        
        #chatterfix-ai-messages::-webkit-scrollbar {
            width: 8px;
        }
        
        #chatterfix-ai-messages::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }
        
        #chatterfix-ai-messages::-webkit-scrollbar-thumb {
            background: linear-gradient(45deg, #FF6B35, #F7931E);
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        #chatterfix-ai-messages::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(45deg, #F7931E, #FFD23F);
        }
        
        .scroll-button:hover {
            background: rgba(255, 107, 53, 1) !important;
            transform: scale(1.1);
        }
        
        .chat-scroll-indicator {
            position: absolute;
            right: 45px;
            bottom: 15px;
            background: rgba(255, 107, 53, 0.9);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            z-index: 1001;
            display: none;
        }
    `;
    document.head.appendChild(style);
};

let selectedProvider = 'grok'; // Default to Grok
let autoScrollEnabled = true; // Auto-scroll to bottom when new messages arrive
let userHasScrolled = false; // Track if user manually scrolled

// Enhanced scroll management
const setupScrollHandlers = () => {
    const messagesContainer = document.getElementById('chatterfix-ai-messages');
    const scrollToTop = document.getElementById('scroll-to-top');
    const scrollToBottom = document.getElementById('scroll-to-bottom');
    
    if (!messagesContainer || !scrollToTop || !scrollToBottom) return;
    
    // Scroll event handler
    messagesContainer.addEventListener('scroll', () => {
        const { scrollTop, scrollHeight, clientHeight } = messagesContainer;
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 20;
        const isAtTop = scrollTop <= 20;
        
        // Show/hide scroll buttons based on position
        scrollToTop.style.display = isAtTop ? 'none' : 'flex';
        scrollToBottom.style.display = isAtBottom ? 'none' : 'flex';
        
        // Disable auto-scroll if user scrolled up manually
        if (!isAtBottom) {
            userHasScrolled = true;
            autoScrollEnabled = false;
        } else {
            userHasScrolled = false;
            autoScrollEnabled = true;
        }
    });
    
    // Scroll to top handler
    scrollToTop.addEventListener('click', () => {
        messagesContainer.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        userHasScrolled = true;
        autoScrollEnabled = false;
    });
    
    // Scroll to bottom handler
    scrollToBottom.addEventListener('click', () => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
        userHasScrolled = false;
        autoScrollEnabled = true;
    });
    
    // Add hover effects
    [scrollToTop, scrollToBottom].forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.background = 'rgba(255, 107, 53, 1)';
            btn.style.transform = 'scale(1.1)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.background = 'rgba(255, 107, 53, 0.8)';
            btn.style.transform = 'scale(1)';
        });
    });
};

// Enhanced auto-scroll function
const smartScroll = (messagesContainer) => {
    if (autoScrollEnabled && !userHasScrolled) {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    } else {
        // Show a subtle indicator that there's a new message
        const scrollToBottom = document.getElementById('scroll-to-bottom');
        if (scrollToBottom && scrollToBottom.style.display !== 'none') {
            scrollToBottom.style.background = 'rgba(255, 107, 53, 1)';
            scrollToBottom.innerHTML = '↓ New';
            setTimeout(() => {
                scrollToBottom.style.background = 'rgba(255, 107, 53, 0.8)';
                scrollToBottom.innerHTML = '↓';
            }, 2000);
        }
    }
};

// Send a message to the AI and receive a response
const sendMessage = async (message) => {
    const messagesContainer = document.getElementById('chatterfix-ai-messages');
    
    // Add user message
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'ai-message user-message';
    userMessageDiv.textContent = message;
    messagesContainer.appendChild(userMessageDiv);
    
    // Add typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-message ai-response';
    typingDiv.innerHTML = '🤖 ChatterFix AI is thinking... <span style="animation: pulse 1s infinite;">💭</span>';
    messagesContainer.appendChild(typingDiv);
    
    // Use enhanced scroll
    smartScroll(messagesContainer);
    
    try {
        const response = await fetch('/global-ai/process-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                providers: [selectedProvider]
            }),
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        messagesContainer.removeChild(typingDiv);
        
        // Add AI response
        const aiResponseDiv = document.createElement('div');
        aiResponseDiv.className = 'ai-message ai-response';
        
        if (data.success) {
            aiResponseDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 5px;">
                    <span style="font-size: 12px; opacity: 0.8;">🤖 ${selectedProvider.toUpperCase()}</span>
                </div>
                ${data.response}
            `;
        } else {
            aiResponseDiv.innerHTML = `
                <div style="color: #ff6b6b;">
                    ❌ Error: ${data.error || 'AI service temporarily unavailable'}
                </div>
            `;
        }
        
        messagesContainer.appendChild(aiResponseDiv);
        smartScroll(messagesContainer);
        
    } catch (error) {
        // Remove typing indicator
        messagesContainer.removeChild(typingDiv);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'ai-message ai-response';
        errorDiv.innerHTML = `<div style="color: #ff6b6b;">❌ Connection error: ${error.message}</div>`;
        messagesContainer.appendChild(errorDiv);
        smartScroll(messagesContainer);
    }
};

// Initialize the Mars-level chat assistant
const initChatterFixAI = () => {
    // Add animations first
    addAnimations();
    
    const button = createFloatingButton();
    const chatInterface = createChatInterface();
    
    // Welcome message
    const welcomeMessage = () => {
        const messagesContainer = document.getElementById('chatterfix-ai-messages');
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'ai-message ai-response';
        welcomeDiv.innerHTML = `
            <div style="text-align: center; padding: 10px;">
                🚀 <strong>Welcome to ChatterFix AI!</strong><br>
                <small style="opacity: 0.8;">Mars-level AI assistant for your CMMS needs</small><br><br>
                Ask me about:
                • Work orders & maintenance
                • Asset management
                • Parts inventory
                • Reports & analytics
                • General CMMS help
            </div>
        `;
        messagesContainer.appendChild(welcomeDiv);
    };
    
    // Toggle chat interface
    button.onclick = () => {
        const isVisible = chatInterface.style.display === 'block';
        chatInterface.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            // Show welcome message on first open
            const messagesContainer = document.getElementById('chatterfix-ai-messages');
            if (messagesContainer.children.length === 0) {
                welcomeMessage();
            }
            // Setup scroll handlers after opening
            setTimeout(setupScrollHandlers, 100);
        }
    };

    // Close chat
    document.getElementById('close-chatterfix-ai').onclick = () => {
        chatInterface.style.display = 'none';
    };

    // Provider selection
    document.querySelectorAll('.ai-provider-btn').forEach(btn => {
        btn.onclick = () => {
            // Update selection
            document.querySelectorAll('.ai-provider-btn').forEach(b => b.style.opacity = '0.6');
            btn.style.opacity = '1';
            selectedProvider = btn.dataset.provider;
            
            // Add selection message
            const messagesContainer = document.getElementById('chatterfix-ai-messages');
            const selectionDiv = document.createElement('div');
            selectionDiv.className = 'ai-message ai-response';
            selectionDiv.innerHTML = `<div style="text-align: center; font-size: 12px; opacity: 0.8;">🔄 Switched to ${selectedProvider.toUpperCase()} AI</div>`;
            messagesContainer.appendChild(selectionDiv);
            smartScroll(messagesContainer);
        };
    });

    // Keyboard shortcuts for better UX
    document.addEventListener('keydown', (e) => {
        const chatInterface = document.getElementById('chatterfix-ai-interface');
        const messagesContainer = document.getElementById('chatterfix-ai-messages');
        const input = document.getElementById('chatterfix-ai-input');
        
        // Only handle shortcuts when chat is open
        if (chatInterface && chatInterface.style.display === 'block') {
            // Ctrl/Cmd + Up Arrow: Scroll to top
            if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowUp') {
                e.preventDefault();
                messagesContainer.scrollTo({ top: 0, behavior: 'smooth' });
                userHasScrolled = true;
                autoScrollEnabled = false;
            }
            
            // Ctrl/Cmd + Down Arrow: Scroll to bottom
            if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowDown') {
                e.preventDefault();
                messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: 'smooth' });
                userHasScrolled = false;
                autoScrollEnabled = true;
            }
            
            // Page Up/Page Down for scroll navigation
            if (e.key === 'PageUp' && input !== document.activeElement) {
                e.preventDefault();
                messagesContainer.scrollBy({ top: -200, behavior: 'smooth' });
                userHasScrolled = true;
                autoScrollEnabled = false;
            }
            
            if (e.key === 'PageDown' && input !== document.activeElement) {
                e.preventDefault();
                messagesContainer.scrollBy({ top: 200, behavior: 'smooth' });
            }
            
            // Home/End keys for quick navigation
            if (e.key === 'Home' && input !== document.activeElement) {
                e.preventDefault();
                messagesContainer.scrollTo({ top: 0, behavior: 'smooth' });
                userHasScrolled = true;
                autoScrollEnabled = false;
            }
            
            if (e.key === 'End' && input !== document.activeElement) {
                e.preventDefault();
                messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: 'smooth' });
                userHasScrolled = false;
                autoScrollEnabled = true;
            }
        }
    });

    // Send message on Enter key
    const input = document.getElementById('chatterfix-ai-input');
    input.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && input.value.trim()) {
            sendMessage(input.value.trim());
            input.value = '';
        }
    });

    // Send message on button click
    document.getElementById('send-message-btn').onclick = () => {
        if (input.value.trim()) {
            sendMessage(input.value.trim());
            input.value = '';
        }
    };

    console.log('🚀 ChatterFix Mars-Level AI Assistant initialized!');
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatterFixAI);
} else {
    initChatterFixAI();
}