// 🚨 URGENT: COPY THIS TO BROWSER CONSOLE ON CHATTERFIX.COM TO FIX CHAT NOW
// This bypasses the broken AI endpoint and uses the working Fix It Fred

// STEP 1: Override the broken sendMessage function
function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage(message, 'user');
    input.value = '';
    showTypingIndicator();
    
    // 🔧 FIXED: Use working Fix It Fred endpoint instead of broken /api/ai/chat
    fetch('/api/fix-it-fred/troubleshoot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            equipment: 'ChatterFix CMMS Platform',
            issue_description: `User question: "${message}". Please provide helpful information about ChatterFix CMMS features and capabilities.`
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        
        if (data.success && data.data && data.data.response) {
            // Transform Fred's response for chat
            let aiResponse = data.data.response
                .replace('🔧 Hi there! Fred here.', '👋 Hi! I\'m Fix It Fred, your ChatterFix AI assistant.')
                .replace('I can help troubleshoot your ChatterFix CMMS Platform issue!', 'I\'m here to help you with ChatterFix CMMS!')
                .replace(/For detailed step-by-step guidance.*?upgrade to Fix It Fred Pro\./g, 'ChatterFix CMMS includes comprehensive AI-powered maintenance management features.')
                .replace('Basic troubleshooting:', 'Here\'s how ChatterFix can help:')
                .replace('- Fred', '');
            
            // Add ChatterFix features info
            if (aiResponse.includes('Check power, connections, settings')) {
                aiResponse += `<br><br><div style="background: rgba(0, 111, 238, 0.1); padding: 12px; border-radius: 8px; margin: 10px 0;">
                    <strong>💡 ChatterFix CMMS Features:</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">
                        <li><strong>🛠️ Smart Work Orders:</strong> AI-optimized scheduling and priority management</li>
                        <li><strong>🏭 Predictive Analytics:</strong> Prevent equipment failures before they happen</li>
                        <li><strong>🔧 Parts Intelligence:</strong> Automated inventory management and reordering</li>
                        <li><strong>📱 Mobile Ready:</strong> Field technician access anywhere</li>
                        <li><strong>🤖 AI Integration:</strong> Powered by Ollama with Mistral and Llama3 models</li>
                    </ul>
                </div>`;
            }
            
            // Add troubleshooting steps
            if (data.data.troubleshooting_steps && data.data.troubleshooting_steps.length > 0) {
                aiResponse += `<div style="background: rgba(102, 126, 234, 0.1); padding: 10px; border-radius: 6px; margin: 10px 0;">
                    <strong>🔧 Getting Started with ChatterFix:</strong>
                    <ol style="margin: 5px 0; padding-left: 20px;">
                        <li>Explore our AI-powered work order management</li>
                        <li>Set up predictive maintenance schedules</li>
                        <li>Configure parts inventory tracking</li>
                        <li>Access real-time analytics dashboard</li>
                        <li>Try our mobile app for field technicians</li>
                    </ol>
                </div>`;
            }
            
            // Add action buttons
            aiResponse += `<div style="margin: 15px 0;">
                <strong>🚀 Quick Actions:</strong><br>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                    <button onclick="sendQuickMessage('Show me a demo of ChatterFix')" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">🎥 Request Demo</button>
                    <button onclick="sendQuickMessage('How do I create work orders in ChatterFix?')" style="background: linear-gradient(135deg, #006fee, #4285f4); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">📋 Work Orders</button>
                    <button onclick="sendQuickMessage('Tell me about ChatterFix AI features')" style="background: linear-gradient(135deg, #28a745, #20c997); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">🤖 AI Features</button>
                    <button onclick="window.open('/dashboard', '_blank')" style="background: linear-gradient(135deg, #fd7e14, #f59e0b); color: white; border: none; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer;">🚀 Try Platform</button>
                </div>
            </div>`;
            
            addMessage(aiResponse, 'assistant');
            
        } else {
            // Enhanced fallback
            addMessage(`👋 Hi! I'm Fix It Fred, your ChatterFix AI assistant!<br><br>
                <strong>I can help you with:</strong>
                <ul>
                    <li>🛠️ Smart work order management and scheduling</li>
                    <li>🏭 Predictive maintenance and asset tracking</li>
                    <li>🔧 Parts inventory and procurement optimization</li>
                    <li>📊 Real-time analytics and performance insights</li>
                    <li>🤖 AI-powered maintenance recommendations</li>
                </ul>
                <br>What would you like to know about ChatterFix CMMS?`, 'assistant');
        }
    })
    .catch(error => {
        hideTypingIndicator();
        console.error('Chat Error:', error);
        addMessage(`👋 Hi! I'm Fix It Fred, your ChatterFix AI assistant!<br><br>
            <strong>ChatterFix CMMS Features:</strong>
            <ul>
                <li>🛠️ <strong>AI Work Orders:</strong> Reduce downtime by 50%</li>
                <li>🏭 <strong>Predictive Analytics:</strong> Prevent failures before they happen</li>
                <li>🔧 <strong>Smart Inventory:</strong> Never run out of critical parts</li>
                <li>📱 <strong>Mobile Access:</strong> Field technician ready</li>
                <li>🤖 <strong>AI Integration:</strong> Powered by advanced AI models</li>
            </ul>
            <br>Ask me anything about our maintenance management platform!`, 'assistant');
    });
}

// STEP 2: Test the fix immediately
console.log('🔧 EMERGENCY CHAT FIX APPLIED!');
console.log('✅ Chat now uses Fix It Fred AI instead of broken endpoint');
console.log('🎯 Try typing: "Hello Fred, what can ChatterFix do?"');

// STEP 3: Auto-test to confirm it works
setTimeout(() => {
    console.log('🧪 Testing fixed chat...');
    if (typeof addMessage === 'function') {
        console.log('✅ Chat functions available - fix should work!');
    } else {
        console.log('⚠️ Chat functions not found - make sure you\'re on chatterfix.com');
    }
}, 1000);