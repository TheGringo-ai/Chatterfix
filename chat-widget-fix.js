// 🔧 Fix It Fred Chat Widget Enhancement
// This fixes the chat widget to use the working Fix It Fred AI instead of generic fallbacks

// Enhanced chat function that uses Fix It Fred's AI capabilities
async function sendChatMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    
    // Add user message to chat
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.innerHTML = `<div class="message-content">${message}</div>`;
    chatMessages.appendChild(userMessage);
    
    // Add thinking indicator
    const thinkingMessage = document.createElement('div');
    thinkingMessage.className = 'message assistant-message thinking';
    thinkingMessage.innerHTML = `
        <div class="message-content">
            <div class="thinking-animation">
                🤖 Fix It Fred is thinking...
                <div class="dots">
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(thinkingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        // Use Fix It Fred for intelligent responses
        const response = await fetch('/api/fix-it-fred/troubleshoot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                equipment: 'ChatterFix CMMS Platform',
                issue_description: `User inquiry: ${message}. Please provide helpful information about ChatterFix CMMS features and capabilities.`
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Remove thinking indicator
            thinkingMessage.remove();
            
            if (data.success && data.data && data.data.response) {
                let aiResponse = data.data.response;
                
                // Enhance Fred's response for chat context
                aiResponse = aiResponse
                    .replace('🔧 Hi there! Fred here.', '👋 Hi! I\'m Fix It Fred, your ChatterFix AI assistant.')
                    .replace('I can help troubleshoot your ChatterFix CMMS Platform issue!', 'I can help you with ChatterFix CMMS!')
                    .replace('For detailed step-by-step guidance specific to your equipment model and real-time AI analysis, upgrade to Fix It Fred Pro.', 'ChatterFix CMMS includes comprehensive AI-powered features for maintenance management.');
                
                // Add assistant response
                const assistantMessage = document.createElement('div');
                assistantMessage.className = 'message assistant-message';
                assistantMessage.innerHTML = `
                    <div class="message-content">
                        ${aiResponse}
                        <br><br>
                        <div class="ai-suggestions">
                            <strong>💡 I can help you with:</strong>
                            <ul>
                                <li>Work order management</li>
                                <li>Asset tracking and maintenance</li>
                                <li>Parts inventory optimization</li>
                                <li>Predictive maintenance insights</li>
                                <li>Equipment troubleshooting</li>
                            </ul>
                        </div>
                        ${data.data.troubleshooting_steps ? `
                        <div class="troubleshooting-steps">
                            <strong>🔧 Recommended steps:</strong>
                            <ol>
                                ${data.data.troubleshooting_steps.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        </div>
                        ` : ''}
                    </div>
                `;
                chatMessages.appendChild(assistantMessage);
                
                return true;
            }
        }
    } catch (error) {
        console.error('Fix It Fred Error:', error);
    }
    
    // Remove thinking indicator and show fallback
    thinkingMessage.remove();
    
    // Enhanced fallback with ChatterFix context
    const fallbackMessage = document.createElement('div');
    fallbackMessage.className = 'message assistant-message';
    fallbackMessage.innerHTML = `
        <div class="message-content">
            👋 Hi! I'm your ChatterFix AI assistant. I'm here to help you with:
            <br><br>
            <div class="feature-highlights">
                <strong>🎯 ChatterFix CMMS Features:</strong>
                <ul>
                    <li><strong>🛠️ Smart Work Orders:</strong> AI-optimized scheduling and prioritization</li>
                    <li><strong>🏭 Asset Management:</strong> Predictive analytics and lifecycle tracking</li>
                    <li><strong>🔧 Parts Intelligence:</strong> Smart inventory with automated reordering</li>
                    <li><strong>🤖 AI Integration:</strong> Powered by Ollama with Mistral and Llama3</li>
                    <li><strong>📱 Mobile Ready:</strong> Responsive design for field technicians</li>
                </ul>
            </div>
            <br>
            <div class="quick-actions">
                <strong>🚀 Quick Actions:</strong>
                <div class="action-buttons">
                    <button onclick="askAbout('work orders')" class="action-btn">Learn about Work Orders</button>
                    <button onclick="askAbout('AI features')" class="action-btn">Explore AI Features</button>
                    <button onclick="askAbout('getting started')" class="action-btn">Get Started Guide</button>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(fallbackMessage);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return false;
}

// Helper function for quick action buttons
function askAbout(topic) {
    const input = document.getElementById('chat-input');
    const queries = {
        'work orders': 'How do I create and manage work orders in ChatterFix?',
        'AI features': 'What AI features does ChatterFix CMMS include?',
        'getting started': 'How do I get started with ChatterFix CMMS?'
    };
    
    if (queries[topic]) {
        input.value = queries[topic];
        sendMessage();
    }
}

// Enhanced sendMessage function with better UX
function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (message) {
        input.value = '';
        sendChatMessage(message);
    }
}

// Add CSS for enhanced chat styling
const chatEnhancementCSS = `
<style>
.thinking-animation {
    display: flex;
    align-items: center;
    gap: 10px;
}

.dots {
    display: flex;
    gap: 2px;
}

.dots span {
    opacity: 0;
    animation: thinking 1.4s infinite;
}

.dots span:nth-child(1) { animation-delay: 0s; }
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes thinking {
    0%, 60%, 100% { opacity: 0; }
    30% { opacity: 1; }
}

.ai-suggestions, .troubleshooting-steps, .feature-highlights {
    margin: 10px 0;
    padding: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    border-left: 3px solid #006fee;
}

.ai-suggestions ul, .troubleshooting-steps ol, .feature-highlights ul {
    margin: 5px 0;
    padding-left: 20px;
}

.ai-suggestions li, .feature-highlights li {
    margin: 3px 0;
}

.action-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
}

.action-btn {
    background: linear-gradient(135deg, #006fee, #4285f4);
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 12px;
    cursor: pointer;
    transition: transform 0.2s ease;
}

.action-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 111, 238, 0.3);
}

.quick-actions {
    margin-top: 10px;
}
</style>
`;

// Inject enhanced CSS
if (!document.getElementById('chat-enhancement-css')) {
    const style = document.createElement('div');
    style.id = 'chat-enhancement-css';
    style.innerHTML = chatEnhancementCSS;
    document.head.appendChild(style);
}

console.log('🔧 Fix It Fred Chat Enhancement Loaded!');
console.log('Chat widget now uses Fix It Fred AI for intelligent responses.');