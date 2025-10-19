/**
 * Fix It Fred SDK - JavaScript/TypeScript
 * Universal AI Assistant Integration for Web Applications
 */

class FixItFredSDK {
    /**
     * Initialize Fix It Fred SDK
     * @param {string} baseUrl - Base URL of Fix It Fred service
     * @param {string} appId - Your application ID (optional)
     * @param {string} apiKey - Your API key (optional)
     */
    constructor(baseUrl = 'http://localhost:8005', appId = null, apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.appId = appId;
        this.apiKey = apiKey;
        
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'User-Agent': 'FixItFred-SDK-JS/1.0'
        };
        
        if (this.apiKey) {
            this.defaultHeaders['Authorization'] = `Bearer ${this.apiKey}`;
        }
    }
    
    /**
     * Send a chat message to Fix It Fred
     * @param {Object} options - Chat options
     * @param {string} options.message - The message to send
     * @param {string} options.provider - AI provider ('anthropic', 'openai', 'xai', 'google', 'ollama')
     * @param {string} options.context - Additional context
     * @param {string} options.conversationId - Conversation ID for tracking
     * @param {string} options.model - Specific model to use
     * @param {number} options.temperature - Response randomness (0.0-1.0)
     * @param {number} options.maxTokens - Maximum response length
     * @returns {Promise<Object>} Response object
     */
    async chat({
        message,
        provider = 'anthropic',
        context = null,
        conversationId = null,
        model = null,
        temperature = 0.7,
        maxTokens = 2000
    }) {
        const endpoint = this.appId 
            ? `${this.baseUrl}/api/apps/${this.appId}/chat`
            : `${this.baseUrl}/api/universal/chat`;
            
        const payload = {
            message,
            provider,
            context,
            conversation_id: conversationId,
            model,
            temperature,
            max_tokens: maxTokens
        };
        
        // Remove null values
        Object.keys(payload).forEach(key => {
            if (payload[key] === null || payload[key] === undefined) {
                delete payload[key];
            }
        });
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            return {
                success: false,
                error: error.message,
                response: `❌ Error connecting to Fix It Fred: ${error.message}`
            };
        }
    }
    
    /**
     * Register your application with Fix It Fred
     * @param {Object} config - Registration configuration
     * @returns {Promise<Object>} Registration result
     */
    async registerApp({
        appName,
        webhookUrl = null,
        allowedProviders = ['anthropic', 'openai'],
        defaultProvider = 'anthropic',
        customInstructions = null
    }) {
        if (!this.appId) {
            this.appId = this.generateUUID();
        }
        
        const payload = {
            app_id: this.appId,
            app_name: appName,
            webhook_url: webhookUrl,
            allowed_providers: allowedProviders,
            default_provider: defaultProvider,
            custom_instructions: customInstructions
        };
        
        try {
            const response = await fetch(`${this.baseUrl}/api/integrations/register`, {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.appId = result.app_id;
            }
            
            return result;
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get all available AI providers
     * @returns {Promise<Object>} Providers information
     */
    async getProviders() {
        try {
            const response = await fetch(`${this.baseUrl}/api/providers`, {
                headers: this.defaultHeaders
            });
            return await response.json();
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get conversation history
     * @param {string} conversationId - Conversation ID
     * @returns {Promise<Object>} Conversation data
     */
    async getConversation(conversationId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/conversations/${conversationId}`, {
                headers: this.defaultHeaders
            });
            return await response.json();
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Clear conversation history
     * @param {string} conversationId - Conversation ID
     * @returns {Promise<Object>} Success status
     */
    async clearConversation(conversationId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/conversations/${conversationId}`, {
                method: 'DELETE',
                headers: this.defaultHeaders
            });
            return await response.json();
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Check service health
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                headers: this.defaultHeaders
            });
            return await response.json();
        } catch (error) {
            return {
                status: 'unhealthy',
                error: error.message
            };
        }
    }
    
    /**
     * Get service statistics
     * @returns {Promise<Object>} Usage statistics
     */
    async getStats() {
        try {
            const response = await fetch(`${this.baseUrl}/api/stats`, {
                headers: this.defaultHeaders
            });
            return await response.json();
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Generate a simple UUID
     * @returns {string} UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

/**
 * Simple chat interface for Fix It Fred
 */
class FixItFredChat {
    /**
     * Initialize simple chat interface
     * @param {string} provider - Default AI provider
     * @param {string} baseUrl - Base URL of service
     */
    constructor(provider = 'anthropic', baseUrl = 'http://localhost:8005') {
        this.sdk = new FixItFredSDK(baseUrl);
        this.provider = provider;
        this.conversationId = this.sdk.generateUUID();
    }
    
    /**
     * Ask Fix It Fred a question
     * @param {string} message - Question or message
     * @param {string} context - Additional context
     * @returns {Promise<string>} Response text
     */
    async ask(message, context = null) {
        const result = await this.sdk.chat({
            message,
            context,
            provider: this.provider,
            conversationId: this.conversationId
        });
        
        if (result.success) {
            return result.response || 'No response received';
        } else {
            return `Error: ${result.error || 'Unknown error'}`;
        }
    }
    
    /**
     * Switch AI provider
     * @param {string} provider - New provider to use
     */
    switchProvider(provider) {
        this.provider = provider;
    }
    
    /**
     * Start a new conversation
     */
    newConversation() {
        this.conversationId = this.sdk.generateUUID();
    }
}

/**
 * React Hook for Fix It Fred integration
 */
function useFixItFred(provider = 'anthropic', baseUrl = 'http://localhost:8005') {
    if (typeof React === 'undefined') {
        throw new Error('React is required for useFixItFred hook');
    }
    
    const [fred] = React.useState(() => new FixItFredChat(provider, baseUrl));
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    
    const ask = React.useCallback(async (message, context = null) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fred.ask(message, context);
            setLoading(false);
            return response;
        } catch (err) {
            setError(err.message);
            setLoading(false);
            return `Error: ${err.message}`;
        }
    }, [fred]);
    
    const switchProvider = React.useCallback((newProvider) => {
        fred.switchProvider(newProvider);
    }, [fred]);
    
    const newConversation = React.useCallback(() => {
        fred.newConversation();
        setError(null);
    }, [fred]);
    
    return {
        ask,
        switchProvider,
        newConversation,
        loading,
        error,
        provider: fred.provider
    };
}

/**
 * Web Component for Fix It Fred Chat
 */
class FixItFredChatComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.fred = new FixItFredChat();
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                }
                .chat-container {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    height: 400px;
                    display: flex;
                    flex-direction: column;
                }
                .messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                }
                .message {
                    margin-bottom: 12px;
                }
                .user-message {
                    text-align: right;
                }
                .ai-message {
                    text-align: left;
                }
                .message-bubble {
                    display: inline-block;
                    padding: 8px 12px;
                    border-radius: 16px;
                    max-width: 70%;
                }
                .user-bubble {
                    background: #007bff;
                    color: white;
                }
                .ai-bubble {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                }
                .input-area {
                    padding: 16px;
                    border-top: 1px solid #ddd;
                    display: flex;
                    gap: 8px;
                }
                .message-input {
                    flex: 1;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .send-button {
                    padding: 8px 16px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .send-button:hover {
                    background: #0056b3;
                }
                .send-button:disabled {
                    background: #6c757d;
                    cursor: not-allowed;
                }
            </style>
            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message ai-message">
                        <div class="message-bubble ai-bubble">
                            Hello! I'm Fix It Fred. How can I help you today?
                        </div>
                    </div>
                </div>
                <div class="input-area">
                    <input type="text" class="message-input" id="messageInput" 
                           placeholder="Type your message..." />
                    <button class="send-button" id="sendButton">Send</button>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        const messageInput = this.shadowRoot.getElementById('messageInput');
        const sendButton = this.shadowRoot.getElementById('sendButton');
        const messages = this.shadowRoot.getElementById('messages');
        
        const sendMessage = async () => {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message
            this.addMessage(message, 'user');
            messageInput.value = '';
            sendButton.disabled = true;
            
            // Add loading message
            const loadingId = this.addMessage('Thinking...', 'ai', true);
            
            try {
                const response = await this.fred.ask(message);
                this.removeMessage(loadingId);
                this.addMessage(response, 'ai');
            } catch (error) {
                this.removeMessage(loadingId);
                this.addMessage(`Error: ${error.message}`, 'ai');
            }
            
            sendButton.disabled = false;
            messageInput.focus();
        };
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    addMessage(text, type, isLoading = false) {
        const messages = this.shadowRoot.getElementById('messages');
        const messageId = `msg-${Date.now()}`;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.id = messageId;
        
        const bubbleClass = type === 'user' ? 'user-bubble' : 'ai-bubble';
        const icon = isLoading ? '🤔' : (type === 'user' ? '👤' : '🤖');
        
        messageDiv.innerHTML = `
            <div class="message-bubble ${bubbleClass}">
                ${icon} ${text}
            </div>
        `;
        
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
        
        return messageId;
    }
    
    removeMessage(messageId) {
        const message = this.shadowRoot.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
}

// Register web component
if (typeof customElements !== 'undefined') {
    customElements.define('fix-it-fred-chat', FixItFredChatComponent);
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = { FixItFredSDK, FixItFredChat };
} else if (typeof define === 'function' && define.amd) {
    // AMD
    define([], function() {
        return { FixItFredSDK, FixItFredChat };
    });
} else if (typeof window !== 'undefined') {
    // Browser global
    window.FixItFredSDK = FixItFredSDK;
    window.FixItFredChat = FixItFredChat;
    window.useFixItFred = useFixItFred;
}

// Usage examples:

/*
// Basic usage
const fred = new FixItFredChat();
const response = await fred.ask("What's the weather like?");
console.log(response);

// Advanced SDK usage
const sdk = new FixItFredSDK();
await sdk.registerApp({
    appName: "My Web App",
    customInstructions: "Provide helpful responses for web application users"
});

const result = await sdk.chat({
    message: "Help me with JavaScript",
    provider: "anthropic",
    context: "User is learning web development"
});

// React Hook usage
function MyComponent() {
    const { ask, loading, error } = useFixItFred();
    
    const handleSubmit = async (message) => {
        const response = await ask(message);
        console.log(response);
    };
    
    return (
        <div>
            {loading && <p>Loading...</p>}
            {error && <p>Error: {error}</p>}
            <button onClick={() => handleSubmit("Hello!")}>
                Ask Fix It Fred
            </button>
        </div>
    );
}

// Web Component usage
// Just add <fix-it-fred-chat></fix-it-fred-chat> to your HTML
*/