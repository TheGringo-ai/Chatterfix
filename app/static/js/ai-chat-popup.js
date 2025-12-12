/**
 * 🤖 AI CHAT POPUP - Enhanced AI Assistant with AutoGen Integration
 * 
 * Floating, prominent AI chat window that integrates with the autonomous AI team
 * Makes AI assistance highly discoverable and easy to access
 */

class AIChat {
    constructor() {
        this.isOpen = false;
        this.isMinimized = false;
        this.messages = [];
        this.isTyping = false;
        this.conversationId = this.generateConversationId();
        this.init();
        this.loadChatHistory();
    }

    init() {
        this.createChatButton();
        this.createChatWindow();
        this.setupEventListeners();
        this.updateContextualSuggestions();
        // Only show welcome if no chat history
        if (this.messages.length === 0) {
            this.showWelcomePrompt();
        }
    }

    createChatButton() {
        // Floating chat button - highly visible
        const button = document.createElement('div');
        button.id = 'ai-chat-button';
        button.innerHTML = `
            <div class="ai-chat-btn-content">
                <i class="fas fa-robot ai-icon"></i>
                <span class="ai-text">Ask AI</span>
                <div class="ai-pulse"></div>
            </div>
            <div class="notification-badge" id="ai-notification">1</div>
        `;
        
        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
            cursor: pointer;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            animation: aiPulse 3s infinite;
        `;
        
        document.body.appendChild(button);
        this.button = button;

        // Add styles
        this.addStyles();
    }

    createChatWindow() {
        const chatWindow = document.createElement('div');
        chatWindow.id = 'ai-chat-window';
        chatWindow.innerHTML = `
            <div class="ai-chat-header">
                <div class="ai-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="ai-info">
                    <h4>ChatterFix AI Team</h4>
                    <span class="ai-status">🟢 Online - Powered by AutoGen</span>
                </div>
                <div class="ai-controls">
                    <button id="ai-clear-history" class="ai-control-btn" title="Clear Chat History">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button id="ai-minimize" class="ai-control-btn">
                        <i class="fas fa-minus"></i>
                    </button>
                    <button id="ai-close" class="ai-control-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            
            <div class="ai-chat-body" id="ai-messages">
                <div class="ai-welcome-message">
                    <div class="ai-message ai-message-bot">
                        <div class="ai-message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="ai-message-content">
                            <div class="ai-message-text">
                                👋 Hi! I'm your ChatterFix AI assistant powered by our autonomous AI team!
                                <br><br>
                                I can help you with:
                                <ul>
                                    <li>🔧 Maintenance planning & scheduling</li>
                                    <li>📊 Performance analytics & insights</li>
                                    <li>🤖 Autonomous feature requests</li>
                                    <li>💡 Equipment troubleshooting</li>
                                    <li>📈 Predictive maintenance guidance</li>
                                </ul>
                                What would you like assistance with?
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="ai-quick-actions" id="ai-quick-actions">
                <!-- Dynamic suggestions will be populated here -->
            </div>
            
            <div class="ai-input-container">
                <div class="ai-input-wrapper">
                    <textarea 
                        id="ai-input" 
                        placeholder="Ask me anything about maintenance, analytics, or request new features..."
                        rows="1"
                    ></textarea>
                    <button id="ai-send" class="ai-send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
                <div class="ai-typing" id="ai-typing" style="display: none;">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    AI Team is thinking...
                </div>
            </div>
        `;
        
        chatWindow.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 400px;
            height: 600px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            z-index: 9999;
            display: none;
            flex-direction: column;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            border: 1px solid #e1e8ed;
            overflow: hidden;
        `;
        
        document.body.appendChild(chatWindow);
        this.chatWindow = chatWindow;
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes aiPulse {
                0% { transform: scale(1); box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4); }
                50% { transform: scale(1.05); box-shadow: 0 12px 40px rgba(102, 126, 234, 0.6); }
                100% { transform: scale(1); box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4); }
            }
            
            .ai-chat-btn-content {
                display: flex;
                flex-direction: column;
                align-items: center;
                color: white;
            }
            
            .ai-icon {
                font-size: 24px;
                margin-bottom: 2px;
            }
            
            .ai-text {
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .notification-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: #ff4757;
                color: white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
                animation: bounce 2s infinite;
            }
            
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-10px); }
                60% { transform: translateY(-5px); }
            }
            
            .ai-chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .ai-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }
            
            .ai-info h4 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .ai-status {
                font-size: 12px;
                opacity: 0.9;
            }
            
            .ai-controls {
                margin-left: auto;
                display: flex;
                gap: 8px;
            }
            
            .ai-control-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 6px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            
            .ai-control-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            .ai-chat-body {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
                background: #f8f9fa;
            }
            
            .ai-message {
                display: flex;
                margin-bottom: 16px;
                align-items: flex-start;
                gap: 12px;
            }
            
            .ai-message-bot {
                flex-direction: row;
            }
            
            .ai-message-user {
                flex-direction: row-reverse;
            }
            
            .ai-message-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: #667eea;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                flex-shrink: 0;
            }
            
            .ai-message-user .ai-message-avatar {
                background: #28a745;
            }
            
            .ai-message-content {
                max-width: 70%;
            }
            
            .ai-message-text {
                background: white;
                padding: 12px 16px;
                border-radius: 18px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                font-size: 14px;
                line-height: 1.4;
            }
            
            .ai-message-user .ai-message-text {
                background: #007bff;
                color: white;
            }
            
            .ai-quick-actions {
                display: flex;
                gap: 8px;
                padding: 12px 16px;
                background: white;
                border-top: 1px solid #e1e8ed;
            }
            
            .quick-action {
                flex: 1;
                padding: 8px;
                background: #f8f9fa;
                border-radius: 8px;
                text-align: center;
                font-size: 11px;
                cursor: pointer;
                transition: background 0.2s;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 4px;
            }
            
            .quick-action:hover {
                background: #e9ecef;
            }
            
            .quick-action i {
                font-size: 16px;
                color: #667eea;
            }
            
            .ai-input-container {
                background: white;
                border-top: 1px solid #e1e8ed;
                padding: 16px;
            }
            
            .ai-input-wrapper {
                display: flex;
                gap: 8px;
                align-items: flex-end;
            }
            
            #ai-input {
                flex: 1;
                border: 1px solid #e1e8ed;
                border-radius: 20px;
                padding: 12px 16px;
                resize: none;
                font-family: inherit;
                font-size: 14px;
                outline: none;
                max-height: 100px;
                min-height: 44px;
            }
            
            #ai-input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .ai-send-btn {
                width: 44px;
                height: 44px;
                border: none;
                background: #667eea;
                color: white;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            
            .ai-send-btn:hover {
                background: #5a67d8;
            }
            
            .ai-typing {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 12px;
                color: #666;
                margin-top: 8px;
            }
            
            .typing-indicator {
                display: flex;
                gap: 3px;
            }
            
            .typing-indicator span {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #667eea;
                animation: typing 1.4s infinite ease-in-out;
            }
            
            .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
            .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes typing {
                0%, 80%, 100% { 
                    transform: scale(0);
                    opacity: 0.5;
                }
                40% { 
                    transform: scale(1);
                    opacity: 1;
                }
            }
            
            .ai-streaming {
                position: relative;
            }
            
            .streaming-cursor {
                color: #667eea;
                animation: cursorBlink 1s infinite;
                font-weight: bold;
                margin-left: 2px;
            }
            
            @keyframes cursorBlink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
            
            .ai-conversation-divider {
                display: flex;
                align-items: center;
                margin: 20px 0;
                font-size: 12px;
                color: #666;
            }
            
            .conversation-divider-line {
                flex: 1;
                height: 1px;
                background: #e1e8ed;
            }
            
            .conversation-divider-text {
                padding: 0 12px;
                background: #f8f9fa;
                font-weight: 500;
            }
            
            .ai-message-time {
                font-size: 11px;
                color: #999;
                margin-top: 4px;
                text-align: right;
            }
            
            .ai-message-user .ai-message-time {
                text-align: left;
            }
            
            #ai-chat-button:hover {
                transform: scale(1.1);
                box-shadow: 0 12px 40px rgba(102, 126, 234, 0.6);
            }
            
            @media (max-width: 768px) {
                #ai-chat-window {
                    width: calc(100vw - 40px);
                    height: calc(100vh - 40px);
                    bottom: 20px;
                    right: 20px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupEventListeners() {
        // Chat button click
        this.button.addEventListener('click', () => this.toggleChat());
        
        // Close, minimize, and clear buttons
        document.getElementById('ai-close').addEventListener('click', () => this.closeChat());
        document.getElementById('ai-minimize').addEventListener('click', () => this.minimizeChat());
        document.getElementById('ai-clear-history').addEventListener('click', () => this.clearChatHistory());
        
        // Send message
        document.getElementById('ai-send').addEventListener('click', () => this.sendMessage());
        
        // Enter key to send
        document.getElementById('ai-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        document.getElementById('ai-input').addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = (e.target.scrollHeight) + 'px';
        });
        
        // Quick actions
        document.querySelectorAll('.quick-action').forEach(action => {
            action.addEventListener('click', () => {
                const actionType = action.dataset.action;
                this.handleQuickAction(actionType);
            });
        });
    }

    showWelcomePrompt() {
        // Show notification badge and animate button for 10 seconds
        setTimeout(() => {
            document.getElementById('ai-notification').style.display = 'none';
        }, 10000);
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        this.chatWindow.style.display = 'flex';
        this.button.style.display = 'none';
        this.isOpen = true;
        document.getElementById('ai-notification').style.display = 'none';
        
        // Focus input
        setTimeout(() => {
            document.getElementById('ai-input').focus();
        }, 100);
    }

    closeChat() {
        this.chatWindow.style.display = 'none';
        this.button.style.display = 'flex';
        this.isOpen = false;
        this.isMinimized = false;
    }

    minimizeChat() {
        this.closeChat();
    }

    async sendMessage() {
        const input = document.getElementById('ai-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        input.style.height = 'auto';
        
        // Show typing
        this.showTyping(true);
        
        try {
            // Determine which AI service to use
            if (this.isFeatureRequest(message)) {
                // Use autonomous features for direct implementation requests
                const response = await fetch('/autonomous/simple', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ what_you_want: message })
                });

                const data = await response.json();
                this.showTyping(false);
                
                let aiResponse = data.message || "I'm processing your feature request!";
                
                if (data.status === 'implementing') {
                    aiResponse += "\n\n⚡ Status: Implementing\n🕒 Estimated time: " + (data.estimated_time || "2-5 minutes");
                }
                
                if (data.note) {
                    aiResponse += "\n\n📝 " + data.note;
                }
                
                this.addMessage(aiResponse, 'bot');
                
            } else {
                // Use streaming AI team collaboration for real-time responses
                await this.streamAIResponse(message);
            }
            
        } catch (error) {
            this.showTyping(false);
            this.addMessage("I'm having trouble connecting right now. Please try again in a moment! 🔧", 'bot');
        }
    }

    async streamAIResponse(message) {
        try {
            // Create streaming message container
            const streamingMessageId = 'streaming-' + Date.now();
            this.addStreamingMessage('', 'bot', streamingMessageId);
            
            const response = await fetch('/ai-team/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    prompt: message,
                    context: "ChatterFix CMMS user interaction via chat popup - provide helpful, concise responses"
                })
            });
            
            this.showTyping(false);
            
            if (!response.body) {
                this.finalizeStreamingMessage(streamingMessageId, "I'm here to help! Let me process that for you.");
                return;
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';
            let lastUpdate = Date.now();
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'agent_thinking') {
                                this.updateStreamingMessage(streamingMessageId, `🤔 ${data.message}`);
                            } else if (data.type === 'agent_response') {
                                fullResponse += data.response + '\n';
                                this.updateStreamingMessage(streamingMessageId, fullResponse);
                            } else if (data.type === 'complete') {
                                this.finalizeStreamingMessage(streamingMessageId, data.final_answer || fullResponse);
                                return;
                            }
                            
                            // Throttle updates for better performance
                            const now = Date.now();
                            if (now - lastUpdate > 100) {
                                lastUpdate = now;
                                await new Promise(resolve => setTimeout(resolve, 50));
                            }
                        } catch (e) {
                            // Ignore parsing errors for incomplete chunks
                        }
                    }
                }
            }
            
            // Fallback if streaming completes without explicit 'complete' message
            if (fullResponse) {
                this.finalizeStreamingMessage(streamingMessageId, fullResponse);
            } else {
                this.finalizeStreamingMessage(streamingMessageId, "I've processed your request. How else can I help you?");
            }
            
        } catch (error) {
            this.showTyping(false);
            this.addMessage("I'm experiencing some technical difficulties. Let me try to help you through our standard channels.", 'bot');
            console.error('Streaming error:', error);
        }
    }

    addStreamingMessage(text, sender, messageId) {
        const messagesContainer = document.getElementById('ai-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ai-message-${sender}`;
        messageDiv.id = messageId;
        
        const avatar = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        
        messageDiv.innerHTML = `
            <div class="ai-message-avatar">${avatar}</div>
            <div class="ai-message-content">
                <div class="ai-message-text ai-streaming" id="${messageId}-text">
                    <span class="streaming-cursor">▋</span>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    updateStreamingMessage(messageId, text) {
        const messageElement = document.getElementById(`${messageId}-text`);
        if (messageElement) {
            messageElement.innerHTML = text.replace(/\n/g, '<br>') + '<span class="streaming-cursor">▋</span>';
            const messagesContainer = document.getElementById('ai-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    finalizeStreamingMessage(messageId, text) {
        const messageElement = document.getElementById(`${messageId}-text`);
        if (messageElement) {
            messageElement.innerHTML = text.replace(/\n/g, '<br>');
            messageElement.classList.remove('ai-streaming');
        }
    }

    generateConversationId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    saveChatHistory() {
        try {
            const chatData = {
                conversationId: this.conversationId,
                messages: this.messages,
                timestamp: new Date().toISOString(),
                context: {
                    currentPage: window.location.pathname,
                    userAgent: navigator.userAgent
                }
            };
            
            localStorage.setItem('chatterfix_chat_history', JSON.stringify(chatData));
            
            // Also save to recent conversations list
            let recentChats = JSON.parse(localStorage.getItem('chatterfix_recent_chats') || '[]');
            
            // Remove existing conversation if it exists
            recentChats = recentChats.filter(chat => chat.conversationId !== this.conversationId);
            
            // Add current conversation to the beginning
            recentChats.unshift({
                conversationId: this.conversationId,
                timestamp: chatData.timestamp,
                preview: this.messages.length > 0 ? this.messages[this.messages.length - 1].text.substring(0, 50) + '...' : 'New conversation',
                messageCount: this.messages.length
            });
            
            // Keep only last 10 conversations
            recentChats = recentChats.slice(0, 10);
            
            localStorage.setItem('chatterfix_recent_chats', JSON.stringify(recentChats));
        } catch (error) {
            console.warn('Failed to save chat history:', error);
        }
    }

    loadChatHistory() {
        try {
            const savedChat = localStorage.getItem('chatterfix_chat_history');
            if (savedChat) {
                const chatData = JSON.parse(savedChat);
                
                // Only load recent history (within last 24 hours)
                const savedTime = new Date(chatData.timestamp);
                const now = new Date();
                const hoursSinceLastChat = (now - savedTime) / (1000 * 60 * 60);
                
                if (hoursSinceLastChat < 24 && chatData.messages && chatData.messages.length > 0) {
                    this.messages = chatData.messages;
                    this.conversationId = chatData.conversationId;
                    
                    // Restore messages to UI
                    this.restoreChatMessages();
                }
            }
        } catch (error) {
            console.warn('Failed to load chat history:', error);
        }
    }

    restoreChatMessages() {
        const messagesContainer = document.getElementById('ai-messages');
        if (!messagesContainer) return;
        
        // Clear welcome message
        messagesContainer.innerHTML = '';
        
        // Add a "previous conversation" indicator
        if (this.messages.length > 0) {
            const indicatorDiv = document.createElement('div');
            indicatorDiv.className = 'ai-conversation-divider';
            indicatorDiv.innerHTML = `
                <div class="conversation-divider-line"></div>
                <div class="conversation-divider-text">Previous conversation</div>
                <div class="conversation-divider-line"></div>
            `;
            messagesContainer.appendChild(indicatorDiv);
        }
        
        // Restore all messages
        this.messages.forEach(message => {
            this.renderMessage(message.text, message.sender, false);
        });
    }

    clearChatHistory() {
        if (confirm('Clear all chat history? This action cannot be undone.')) {
            this.messages = [];
            this.conversationId = this.generateConversationId();
            
            // Clear from storage
            localStorage.removeItem('chatterfix_chat_history');
            
            // Clear UI
            const messagesContainer = document.getElementById('ai-messages');
            messagesContainer.innerHTML = '';
            
            // Show welcome message
            this.showWelcomeMessage();
        }
    }

    showWelcomeMessage() {
        const messagesContainer = document.getElementById('ai-messages');
        messagesContainer.innerHTML = `
            <div class="ai-welcome-message">
                <div class="ai-message ai-message-bot">
                    <div class="ai-message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="ai-message-content">
                        <div class="ai-message-text">
                            👋 Hi! I'm your ChatterFix AI assistant powered by our autonomous AI team!
                            <br><br>
                            I can help you with:
                            <ul>
                                <li>🔧 Maintenance planning & scheduling</li>
                                <li>📊 Performance analytics & insights</li>
                                <li>🤖 Autonomous feature requests</li>
                                <li>💡 Equipment troubleshooting</li>
                                <li>📈 Predictive maintenance guidance</li>
                            </ul>
                            What would you like assistance with?
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    addMessage(text, sender) {
        this.renderMessage(text, sender, true);
    }

    renderMessage(text, sender, saveToHistory = true) {
        const messagesContainer = document.getElementById('ai-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ai-message-${sender}`;
        
        const avatar = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="ai-message-avatar">${avatar}</div>
            <div class="ai-message-content">
                <div class="ai-message-text">${text.replace(/\n/g, '<br>')}</div>
                <div class="ai-message-time">${timestamp}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Save to conversation history
        if (saveToHistory) {
            this.messages.push({
                text: text,
                sender: sender,
                timestamp: new Date().toISOString()
            });
            
            // Save to localStorage
            this.saveChatHistory();
        }
    }

    showTyping(show) {
        const typing = document.getElementById('ai-typing');
        typing.style.display = show ? 'flex' : 'none';
        
        if (show) {
            const messagesContainer = document.getElementById('ai-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    isFeatureRequest(message) {
        // Enhanced heuristics to detect feature implementation requests
        const featureKeywords = [
            'add', 'create', 'build', 'implement', 'make', 'develop', 'integrate',
            'budget', 'calendar', 'report', 'notification', 'inventory', 'tracking',
            'mobile', 'dashboard', 'feature', 'functionality'
        ];
        
        const requestPhrases = [
            'i need', 'i want', 'can you add', 'can you create', 'can you build',
            'please add', 'please create', 'add a', 'create a', 'build a'
        ];
        
        const lowerMessage = message.toLowerCase();
        
        const hasFeatureKeyword = featureKeywords.some(keyword => lowerMessage.includes(keyword));
        const hasRequestPhrase = requestPhrases.some(phrase => lowerMessage.includes(phrase));
        
        return hasFeatureKeyword && (hasRequestPhrase || lowerMessage.includes('need') || lowerMessage.includes('want'));
    }

    updateContextualSuggestions() {
        const currentPath = window.location.pathname;
        const quickActionsContainer = document.getElementById('ai-quick-actions');
        
        // Determine contextual suggestions based on current page
        let suggestions = this.getContextualSuggestions(currentPath);
        
        // Render suggestions
        quickActionsContainer.innerHTML = suggestions.map(suggestion => `
            <div class="quick-action" data-action="${suggestion.action}">
                <i class="${suggestion.icon}"></i>
                ${suggestion.label}
            </div>
        `).join('');
        
        // Re-attach event listeners for new quick actions
        quickActionsContainer.querySelectorAll('.quick-action').forEach(action => {
            action.addEventListener('click', () => {
                const actionType = action.dataset.action;
                this.handleQuickAction(actionType);
            });
        });
    }
    
    getContextualSuggestions(path) {
        // Context-aware suggestions based on current page
        const suggestions = {
            '/': [
                { action: 'overview', icon: 'fas fa-tachometer-alt', label: 'Dashboard Overview' },
                { action: 'quick-start', icon: 'fas fa-rocket', label: 'Quick Start Guide' },
                { action: 'features', icon: 'fas fa-magic', label: 'Request Feature' }
            ],
            '/dashboard': [
                { action: 'explain-metrics', icon: 'fas fa-chart-line', label: 'Explain Metrics' },
                { action: 'optimize', icon: 'fas fa-cogs', label: 'Optimization Tips' },
                { action: 'alerts', icon: 'fas fa-bell', label: 'Setup Alerts' }
            ],
            '/work-orders': [
                { action: 'create-work-order', icon: 'fas fa-plus', label: 'Create Work Order' },
                { action: 'prioritize', icon: 'fas fa-sort-amount-down', label: 'Priority Help' },
                { action: 'schedule', icon: 'fas fa-calendar', label: 'Schedule Tasks' }
            ],
            '/equipment': [
                { action: 'add-equipment', icon: 'fas fa-wrench', label: 'Add Equipment' },
                { action: 'maintenance-schedule', icon: 'fas fa-clock', label: 'Maintenance Schedule' },
                { action: 'troubleshoot', icon: 'fas fa-bug', label: 'Troubleshoot' }
            ],
            '/inventory': [
                { action: 'add-parts', icon: 'fas fa-box', label: 'Add Parts' },
                { action: 'stock-alerts', icon: 'fas fa-exclamation-triangle', label: 'Stock Alerts' },
                { action: 'supplier-info', icon: 'fas fa-truck', label: 'Supplier Info' }
            ],
            '/reports': [
                { action: 'generate-report', icon: 'fas fa-file-alt', label: 'Generate Report' },
                { action: 'kpi-analysis', icon: 'fas fa-chart-bar', label: 'KPI Analysis' },
                { action: 'export-data', icon: 'fas fa-download', label: 'Export Data' }
            ],
            '/settings': [
                { action: 'system-config', icon: 'fas fa-cog', label: 'System Config' },
                { action: 'user-management', icon: 'fas fa-users', label: 'User Management' },
                { action: 'integrations', icon: 'fas fa-link', label: 'Integrations' }
            ]
        };
        
        // Check for specific page matches
        for (const [pagePath, pageSuggestions] of Object.entries(suggestions)) {
            if (path.includes(pagePath) && pagePath !== '/') {
                return pageSuggestions;
            }
        }
        
        // Default suggestions for home/unknown pages
        return suggestions['/'];
    }

    handleQuickAction(action) {
        const actions = {
            // Dashboard actions
            'overview': 'Give me an overview of my ChatterFix dashboard and what the key metrics mean',
            'explain-metrics': 'Explain what these dashboard metrics mean and how to improve them',
            'optimize': 'What are the best ways to optimize my maintenance operations?',
            'alerts': 'Help me set up smart alerts for critical maintenance issues',
            
            // Work order actions
            'create-work-order': 'I want to create a new work order',
            'prioritize': 'How should I prioritize my work orders for maximum efficiency?',
            'schedule': 'Help me schedule maintenance tasks effectively',
            
            // Equipment actions
            'add-equipment': 'I need to add new equipment to my system',
            'maintenance-schedule': 'Create a maintenance schedule for my equipment',
            'troubleshoot': 'I need help troubleshooting equipment issues',
            
            // Inventory actions
            'add-parts': 'I want to add new parts to my inventory',
            'stock-alerts': 'Set up automatic alerts when stock is running low',
            'supplier-info': 'Help me manage supplier information and contacts',
            
            // Reports actions
            'generate-report': 'Generate a comprehensive maintenance report',
            'kpi-analysis': 'Analyze my key performance indicators and suggest improvements',
            'export-data': 'How do I export my maintenance data?',
            
            // Settings actions
            'system-config': 'Help me configure system settings for optimal performance',
            'user-management': 'I need help with user roles and permissions',
            'integrations': 'What integrations are available and how do I set them up?',
            
            // General actions
            'features': 'I want to request a new feature for ChatterFix',
            'quick-start': 'Give me a quick start guide to using ChatterFix effectively',
            'help': 'How do I use ChatterFix CMMS effectively for my maintenance management?'
        };
        
        if (actions[action]) {
            document.getElementById('ai-input').value = actions[action];
            this.sendMessage();
        }
    }
}

// Initialize AI Chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're not on the autonomous interface page to avoid conflicts
    if (!window.location.pathname.includes('/autonomous/interface')) {
        new AIChat();
    }
});