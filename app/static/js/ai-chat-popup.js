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
        this.init();
    }

    init() {
        this.createChatButton();
        this.createChatWindow();
        this.setupEventListeners();
        this.showWelcomePrompt();
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
            
            <div class="ai-quick-actions">
                <div class="quick-action" data-action="features">
                    <i class="fas fa-magic"></i>
                    Request Feature
                </div>
                <div class="quick-action" data-action="help">
                    <i class="fas fa-question-circle"></i>
                    Get Help
                </div>
                <div class="quick-action" data-action="analytics">
                    <i class="fas fa-chart-bar"></i>
                    Analytics
                </div>
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
        
        // Close and minimize buttons
        document.getElementById('ai-close').addEventListener('click', () => this.closeChat());
        document.getElementById('ai-minimize').addEventListener('click', () => this.minimizeChat());
        
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
                // Use enhanced AI team collaboration for complex questions/analysis
                const response = await fetch('/ai-team/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        prompt: message,
                        context: "ChatterFix CMMS user interaction via chat popup - provide helpful, concise responses",
                        task_type: "USER_ASSISTANCE",
                        max_iterations: 2
                    })
                });

                const result = await response.json();
                this.showTyping(false);
                
                if (result.success && result.final_result) {
                    let aiResponse = result.final_result;
                    
                    // Show confidence if high
                    if (result.confidence_score && result.confidence_score > 0.8) {
                        aiResponse += "\n\n🎯 Confidence: " + (result.confidence_score * 100).toFixed(0) + "%";
                    }
                    
                    this.addMessage(aiResponse, 'bot');
                    
                    // Show collaboration summary if available
                    if (result.collaboration_summary && result.model_responses?.length > 1) {
                        setTimeout(() => {
                            this.addMessage("💡 " + result.collaboration_summary, 'bot');
                        }, 1000);
                    }
                } else {
                    this.addMessage("I'm analyzing your request and will provide you with comprehensive assistance. Let me think about this...", 'bot');
                }
            }
            
        } catch (error) {
            this.showTyping(false);
            this.addMessage("I'm having trouble connecting right now. Please try again in a moment! 🔧", 'bot');
        }
    }

    addMessage(text, sender) {
        const messagesContainer = document.getElementById('ai-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ai-message-${sender}`;
        
        const avatar = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        
        messageDiv.innerHTML = `
            <div class="ai-message-avatar">${avatar}</div>
            <div class="ai-message-content">
                <div class="ai-message-text">${text.replace(/\n/g, '<br>')}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
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

    handleQuickAction(action) {
        const actions = {
            'features': 'I want to request a new feature for ChatterFix',
            'help': 'How do I use ChatterFix CMMS effectively for my maintenance management?',
            'analytics': 'What insights and analytics can you provide about my maintenance data and performance?'
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