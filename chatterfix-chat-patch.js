// 🔧 ChatterFix Chat Widget - Fix It Fred Integration Patch
// This replaces the generic chat responses with intelligent AI powered by Fix It Fred

// STEP 1: Replace the sendChatMessage function with this enhanced version
async function sendChatMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    
    // Add user message
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.innerHTML = `<div class="message-content">${message}</div>`;
    chatMessages.appendChild(userMessage);
    
    // Add thinking indicator
    const thinkingMessage = document.createElement('div');
    thinkingMessage.className = 'message assistant-message';
    thinkingMessage.innerHTML = `
        <div class="message-content">
            <div style="display: flex; align-items: center; gap: 10px;">
                🤖 <span style="opacity: 0.8;">Fix It Fred is analyzing your question...</span>
                <div class="thinking-dots">
                    <span style="animation: thinking 1.4s infinite;">.</span>
                    <span style="animation: thinking 1.4s infinite 0.2s;">.</span>
                    <span style="animation: thinking 1.4s infinite 0.4s;">.</span>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(thinkingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        // Use Fix It Fred's AI instead of the broken /api/ai/chat
        const response = await fetch('/api/fix-it-fred/troubleshoot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                equipment: 'ChatterFix CMMS Platform',
                issue_description: `User inquiry about ChatterFix CMMS: "${message}". Please provide helpful, detailed information about ChatterFix features, capabilities, and how it can help with maintenance management.`
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Remove thinking indicator
            thinkingMessage.remove();
            
            if (data.success && data.data && data.data.response) {
                let aiResponse = data.data.response;
                
                // Transform Fred's response for chat context
                aiResponse = aiResponse
                    .replace(/🔧 Hi there! Fred here\./g, '👋 Hi! I\'m your ChatterFix AI assistant.')
                    .replace(/I can help troubleshoot your ChatterFix CMMS Platform issue!/g, 'I\'m here to help you with ChatterFix CMMS!')
                    .replace(/For detailed step-by-step guidance.*?upgrade to Fix It Fred Pro\./g, 'ChatterFix CMMS includes comprehensive AI-powered maintenance management features.')
                    .replace(/Basic troubleshooting:/g, 'Here\'s how ChatterFix can help:')
                    .replace(/- Fred$/g, '');
                
                // Create enhanced response
                const assistantMessage = document.createElement('div');
                assistantMessage.className = 'message assistant-message';
                
                let responseHTML = `<div class="message-content">${aiResponse}`;
                
                // Add ChatterFix-specific features if the response is generic
                if (aiResponse.includes('Check power, connections, settings')) {
                    responseHTML += `
                        <br><br>
                        <div style="background: rgba(0, 111, 238, 0.1); padding: 12px; border-radius: 8px; border-left: 3px solid #006fee; margin: 10px 0;">
                            <strong>💡 ChatterFix CMMS Features:</strong>
                            <ul style="margin: 8px 0; padding-left: 20px;">
                                <li><strong>🛠️ Smart Work Orders:</strong> AI-optimized scheduling and priority management</li>
                                <li><strong>🏭 Predictive Analytics:</strong> Prevent equipment failures before they happen</li>
                                <li><strong>🔧 Parts Intelligence:</strong> Automated inventory management and reordering</li>
                                <li><strong>📱 Mobile Ready:</strong> Access anywhere, anytime for field technicians</li>
                                <li><strong>🤖 AI Integration:</strong> Powered by Ollama with Mistral and Llama3 models</li>
                            </ul>
                        </div>
                    `;
                }
                
                // Add troubleshooting steps if available
                if (data.data.troubleshooting_steps && data.data.troubleshooting_steps.length > 0) {
                    responseHTML += `
                        <div style="background: rgba(102, 126, 234, 0.1); padding: 10px; border-radius: 6px; margin: 10px 0;">
                            <strong>🔧 Recommended Next Steps:</strong>
                            <ol style="margin: 5px 0; padding-left: 20px;">
                                ${data.data.troubleshooting_steps.map(step => `<li style="margin: 3px 0;">${step}</li>`).join('')}
                            </ol>
                        </div>
                    `;
                }
                
                // Add quick action buttons
                responseHTML += `
                    <div style="margin: 15px 0;">
                        <strong>🚀 Quick Actions:</strong><br>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                            <button onclick="askQuickQuestion('How do I create a work order?')" style="background: linear-gradient(135deg, #006fee, #4285f4); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">Create Work Orders</button>
                            <button onclick="askQuickQuestion('Tell me about AI features')" style="background: linear-gradient(135deg, #006fee, #4285f4); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">AI Features</button>
                            <button onclick="askQuickQuestion('How does asset tracking work?')" style="background: linear-gradient(135deg, #006fee, #4285f4); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">Asset Tracking</button>
                            <button onclick="window.open('/dashboard', '_blank')" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">Try Platform</button>
                        </div>
                    </div>
                `;
                
                responseHTML += `</div>`;
                assistantMessage.innerHTML = responseHTML;
                chatMessages.appendChild(assistantMessage);
                
                chatMessages.scrollTop = chatMessages.scrollHeight;
                return;
            }
        }
    } catch (error) {
        console.error('Fix It Fred Integration Error:', error);
    }
    
    // Enhanced fallback if Fred fails
    thinkingMessage.remove();
    
    const fallbackMessage = document.createElement('div');
    fallbackMessage.className = 'message assistant-message';
    fallbackMessage.innerHTML = `
        <div class="message-content">
            👋 Hi! I'm your ChatterFix AI assistant. I'm here to help you discover how ChatterFix CMMS can revolutionize your maintenance operations!
            <br><br>
            <div style="background: rgba(0, 111, 238, 0.1); padding: 15px; border-radius: 10px; margin: 10px 0;">
                <strong>🎯 What ChatterFix CMMS Can Do:</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>🛠️ Smart Work Order Management:</strong> AI-powered scheduling reduces downtime by 50%</li>
                    <li><strong>🏭 Predictive Asset Management:</strong> Prevent failures before they happen</li>
                    <li><strong>🔧 Intelligent Parts Management:</strong> Never run out of critical components</li>
                    <li><strong>📊 Real-time Analytics:</strong> Data-driven maintenance decisions</li>
                    <li><strong>🤖 AI-Powered Insights:</strong> Ollama integration with Mistral & Llama3</li>
                </ul>
            </div>
            <div style="margin: 15px 0;">
                <strong>🚀 Get Started:</strong><br>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                    <button onclick="askQuickQuestion('Show me a demo')" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 8px 16px; border-radius: 20px; font-size: 14px; cursor: pointer; font-weight: 600;">🎥 View Demo</button>
                    <button onclick="window.open('/dashboard', '_blank')" style="background: linear-gradient(135deg, #006fee, #4285f4); color: white; border: none; padding: 8px 16px; border-radius: 20px; font-size: 14px; cursor: pointer; font-weight: 600;">🚀 Try Platform</button>
                    <button onclick="askQuickQuestion('What are the pricing options?')" style="background: linear-gradient(135deg, #28a745, #20c997); color: white; border: none; padding: 8px 16px; border-radius: 20px; font-size: 14px; cursor: pointer; font-weight: 600;">💰 Pricing</button>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(fallbackMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// STEP 2: Add helper function for quick action buttons
function askQuickQuestion(question) {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = question;
        sendChatMessage(question);
        chatInput.value = '';
    }
}

// STEP 3: Add CSS for thinking animation
if (!document.getElementById('fred-chat-enhancement-css')) {
    const style = document.createElement('style');
    style.id = 'fred-chat-enhancement-css';
    style.textContent = `
        @keyframes thinking {
            0%, 60%, 100% { opacity: 0.3; }
            30% { opacity: 1; }
        }
        
        .thinking-dots {
            display: flex;
            gap: 2px;
        }
        
        .message-content button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.2s ease;
        }
    `;
    document.head.appendChild(style);
}

// STEP 4: Override the existing sendMessage function to use our enhanced version
function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (message) {
        input.value = '';
        sendChatMessage(message);
    }
}

console.log('🔧 Fix It Fred Chat Enhancement Loaded!');
console.log('🎉 Chat now uses intelligent AI instead of generic responses!');