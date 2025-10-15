// 🔧 IMMEDIATE FIX: Replace the broken sendMessage function with Fix It Fred integration
// Copy and paste this directly into browser console on chatterfix.com to fix chat immediately

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // 🔧 FIX: Use Fix It Fred instead of broken /api/ai/chat
    fetch('/api/fix-it-fred/troubleshoot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            equipment: 'ChatterFix CMMS Platform',
            issue_description: `User inquiry about ChatterFix CMMS: "${message}". Please provide helpful, detailed information about ChatterFix features, capabilities, and how it can help with maintenance management.`
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        if (data.success && data.data && data.data.response) {
            // Transform Fred's response for chat context
            let aiResponse = data.data.response
                .replace(/🔧 Hi there! Fred here\./g, '👋 Hi! I\'m Fix It Fred, your ChatterFix AI assistant.')
                .replace(/I can help troubleshoot your ChatterFix CMMS Platform issue!/g, 'I\'m here to help you with ChatterFix CMMS!')
                .replace(/For detailed step-by-step guidance.*?upgrade to Fix It Fred Pro\./g, 'ChatterFix CMMS includes comprehensive AI-powered maintenance management features.')
                .replace(/Basic troubleshooting:/g, 'Here\'s how ChatterFix can help:')
                .replace(/- Fred$/g, '');
            
            // Add ChatterFix context if generic response
            if (aiResponse.includes('Check power, connections, settings')) {
                aiResponse += `<br><br><div style="background: rgba(0, 111, 238, 0.1); padding: 12px; border-radius: 8px; margin: 10px 0;">
                    <strong>💡 ChatterFix CMMS Features:</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">
                        <li><strong>🛠️ Smart Work Orders:</strong> AI-optimized scheduling</li>
                        <li><strong>🏭 Predictive Analytics:</strong> Prevent equipment failures</li>
                        <li><strong>🔧 Parts Intelligence:</strong> Automated inventory</li>
                        <li><strong>📱 Mobile Ready:</strong> Field technician access</li>
                        <li><strong>🤖 AI Integration:</strong> Powered by Ollama + Fix It Fred</li>
                    </ul>
                </div>`;
            }
            
            // Add troubleshooting steps if available
            if (data.data.troubleshooting_steps && data.data.troubleshooting_steps.length > 0) {
                aiResponse += `<div style="background: rgba(102, 126, 234, 0.1); padding: 10px; border-radius: 6px; margin: 10px 0;">
                    <strong>🔧 Recommended Steps:</strong>
                    <ol style="margin: 5px 0; padding-left: 20px;">
                        ${data.data.troubleshooting_steps.map(step => `<li style="margin: 3px 0;">${step}</li>`).join('')}
                    </ol>
                </div>`;
            }
            
            // Add quick actions
            aiResponse += `<div style="margin: 15px 0;">
                <strong>🚀 Try These:</strong><br>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                    <button onclick="sendQuickMessage('Show me a demo')" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">🎥 Demo</button>
                    <button onclick="sendQuickMessage('How do I create work orders?')" style="background: linear-gradient(135deg, #006fee, #4285f4); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">📋 Work Orders</button>
                    <button onclick="window.open('/dashboard', '_blank')" style="background: linear-gradient(135deg, #28a745, #20c997); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">🚀 Try Platform</button>
                </div>
            </div>`;
            
            addMessage(aiResponse, 'assistant');
        } else {
            addMessage('I\'m Fix It Fred, your ChatterFix AI assistant! How can I help you learn about our AI-powered maintenance management platform?', 'assistant');
        }
    })
    .catch(error => {
        hideTypingIndicator();
        addMessage('👋 Hi! I\'m Fix It Fred. I\'m here to help you with ChatterFix CMMS - our AI-powered maintenance management platform. What would you like to know?', 'assistant');
    });
}

console.log('🔧 Fix It Fred Chat Integration Applied!');
console.log('💬 Chat now uses Fix It Fred AI instead of broken endpoint!');
console.log('🎉 Try asking: "What can ChatterFix do for me?"');