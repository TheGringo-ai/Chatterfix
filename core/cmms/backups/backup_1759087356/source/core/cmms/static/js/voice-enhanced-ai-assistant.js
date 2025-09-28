/**
 * Voice-Enhanced Global AI Assistant for ChatterFix CMMS
 * Adds voice command capabilities to the floating AI chat
 */

let aiAssistantOpen = false;
let aiAssistantInitialized = false;
let isRecording = false;
let recognition = null;

function loadVoiceEnhancedAIAssistant() {
    if (aiAssistantInitialized) return;
    
    // Create the floating AI assistant button
    const aiButton = document.createElement('div');
    aiButton.id = 'global-ai-button';
    aiButton.innerHTML = '🤖';
    aiButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        z-index: 9998;
        transition: all 0.3s ease;
        border: 2px solid rgba(255,255,255,0.2);
        animation: aiPulse 2s infinite;
    `;
    
    // Create the AI assistant popup with voice capabilities
    const aiPopup = document.createElement('div');
    aiPopup.id = 'global-ai-popup';
    aiPopup.style.cssText = `
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 400px;
        height: 500px;
        background: rgba(10, 10, 10, 0.95);
        border-radius: 20px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        backdrop-filter: blur(20px);
        z-index: 9999;
        display: none;
        flex-direction: column;
        overflow: hidden;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    `;
    
    aiPopup.innerHTML = `
        <div id="ai-popup-header" style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 15px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: white;
            font-weight: bold;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">🤖</span>
                <span>ChatterFix AI Assistant</span>
                <div id="ai-status-dot" style="
                    width: 8px;
                    height: 8px;
                    background: #38ef7d;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                "></div>
            </div>
            <button id="ai-popup-close" style="
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">×</button>
        </div>
        
        <div id="ai-chat-messages" style="
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background: rgba(0,0,0,0.2);
            color: white;
            max-height: 350px;
        ">
            <div class="ai-message" style="
                background: linear-gradient(135deg, rgba(56, 239, 125, 0.2), rgba(102, 126, 234, 0.2));
                padding: 12px 15px;
                border-radius: 15px;
                margin-bottom: 10px;
                font-size: 14px;
                line-height: 1.4;
            ">
                👋 Hi! I'm your AI maintenance assistant. I can help you:
                <br>• Create work orders with voice commands
                <br>• Troubleshoot equipment issues  
                <br>• Answer maintenance questions
                <br>• Schedule preventive maintenance
                <br><br>Try saying: <em>"Emergency pump leak in Building A"</em>
            </div>
        </div>
        
        <div id="ai-input-container" style="
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-top: 1px solid rgba(102, 126, 234, 0.2);
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <input 
                    type="text" 
                    id="ai-text-input" 
                    placeholder="Type your message or use voice..." 
                    style="
                        flex: 1;
                        padding: 10px 15px;
                        border: 1px solid rgba(102, 126, 234, 0.3);
                        border-radius: 20px;
                        background: rgba(0,0,0,0.5);
                        color: white;
                        outline: none;
                        font-size: 14px;
                    "
                />
                <button 
                    id="voice-button" 
                    style="
                        width: 40px;
                        height: 40px;
                        border: none;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        font-size: 18px;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: all 0.3s ease;
                        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
                    "
                    title="Voice Command"
                >🎤</button>
                <button 
                    id="send-button" 
                    style="
                        width: 40px;
                        height: 40px;
                        border: none;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #38ef7d, #11998e);
                        color: white;
                        font-size: 16px;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: all 0.3s ease;
                    "
                    title="Send Message"
                >➤</button>
            </div>
            
            <div id="voice-status" style="
                margin-top: 8px;
                font-size: 12px;
                color: #38ef7d;
                text-align: center;
                display: none;
            ">
                🎤 Listening... Speak your command
            </div>
            
            <div id="voice-examples" style="
                margin-top: 10px;
                font-size: 11px;
                color: rgba(255,255,255,0.6);
                line-height: 1.3;
            ">
                <strong>Voice Examples:</strong><br>
                • "Emergency pump leak in Building A"<br>
                • "Schedule motor maintenance"<br>
                • "HVAC making noise in office"
            </div>
        </div>
    `;
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes aiPulse {
            0%, 100% { transform: scale(1); box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); }
            50% { transform: scale(1.05); box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes voiceRecording {
            0%, 100% { background: linear-gradient(135deg, #ff6b6b, #ee5a52); }
            50% { background: linear-gradient(135deg, #ff8e8e, #ff6b6b); }
        }
        
        .voice-recording {
            animation: voiceRecording 1s infinite !important;
        }
        
        #ai-chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        
        #ai-chat-messages::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.1);
        }
        
        #ai-chat-messages::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.5);
            border-radius: 3px;
        }
    `;
    document.head.appendChild(style);
    
    // Add elements to page
    document.body.appendChild(aiButton);
    document.body.appendChild(aiPopup);
    
    // Initialize Web Speech API
    initializeVoiceRecognition();
    
    // Event listeners
    aiButton.addEventListener('click', toggleAIAssistant);
    document.getElementById('ai-popup-close').addEventListener('click', toggleAIAssistant);
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('voice-button').addEventListener('click', toggleVoiceRecording);
    document.getElementById('ai-text-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    aiAssistantInitialized = true;
}

function initializeVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            isRecording = true;
            const voiceButton = document.getElementById('voice-button');
            const voiceStatus = document.getElementById('voice-status');
            
            voiceButton.classList.add('voice-recording');
            voiceButton.innerHTML = '🔴';
            voiceStatus.style.display = 'block';
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            const confidence = event.results[0][0].confidence;
            
            console.log('Voice transcript:', transcript, 'Confidence:', confidence);
            
            // Add voice transcript to input
            document.getElementById('ai-text-input').value = transcript;
            
            // Auto-send if confidence is high
            if (confidence > 0.7) {
                setTimeout(() => sendMessage(), 500);
            }
        };
        
        recognition.onerror = function(event) {
            console.error('Voice recognition error:', event.error);
            stopVoiceRecording();
            
            addMessageToChat('system', `Voice recognition error: ${event.error}. Please try typing instead.`);
        };
        
        recognition.onend = function() {
            stopVoiceRecording();
        };
    } else {
        console.warn('Speech recognition not supported in this browser');
        // Hide voice button if not supported
        const voiceButton = document.getElementById('voice-button');
        if (voiceButton) {
            voiceButton.style.display = 'none';
        }
    }
}

function toggleVoiceRecording() {
    if (!recognition) {
        addMessageToChat('system', 'Voice recognition is not available in this browser.');
        return;
    }
    
    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function stopVoiceRecording() {
    isRecording = false;
    const voiceButton = document.getElementById('voice-button');
    const voiceStatus = document.getElementById('voice-status');
    
    if (voiceButton) {
        voiceButton.classList.remove('voice-recording');
        voiceButton.innerHTML = '🎤';
    }
    
    if (voiceStatus) {
        voiceStatus.style.display = 'none';
    }
}

function toggleAIAssistant() {
    const popup = document.getElementById('global-ai-popup');
    aiAssistantOpen = !aiAssistantOpen;
    
    if (aiAssistantOpen) {
        popup.style.display = 'flex';
        document.getElementById('ai-text-input').focus();
    } else {
        popup.style.display = 'none';
        if (isRecording) {
            recognition.stop();
        }
    }
}

async function sendMessage() {
    const input = document.getElementById('ai-text-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Add thinking indicator
    const thinkingId = addMessageToChat('ai', '🤔 Processing...', true);
    
    try {
        // Send to AI assistant API
        const response = await fetch('/global-ai/process-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                type: 'voice_command'
            })
        });
        
        const data = await response.json();
        
        // Remove thinking indicator
        removeMessage(thinkingId);
        
        if (data.success) {
            addMessageToChat('ai', data.response);
            
            // If actions were generated, show them
            if (data.actions && data.actions.length > 0) {
                data.actions.forEach(action => {
                    addMessageToChat('system', `Action: ${action}`);
                });
            }
        } else {
            addMessageToChat('ai', 'Sorry, I encountered an error processing your request. Please try again.');
        }
        
    } catch (error) {
        console.error('AI request error:', error);
        removeMessage(thinkingId);
        addMessageToChat('ai', 'Connection error. Please check your internet connection and try again.');
    }
}

function addMessageToChat(type, message, temporary = false) {
    const chatContainer = document.getElementById('ai-chat-messages');
    const messageDiv = document.createElement('div');
    const messageId = temporary ? 'temp-' + Date.now() : null;
    
    if (messageId) {
        messageDiv.id = messageId;
    }
    
    const styles = {
        user: `
            background: linear-gradient(135deg, #667eea, #764ba2);
            margin-left: 20px;
            text-align: right;
        `,
        ai: `
            background: linear-gradient(135deg, rgba(56, 239, 125, 0.2), rgba(102, 126, 234, 0.2));
            margin-right: 20px;
        `,
        system: `
            background: rgba(255, 193, 7, 0.2);
            margin: 0 10px;
            font-size: 12px;
            font-style: italic;
        `
    };
    
    messageDiv.style.cssText = `
        padding: 12px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        font-size: 14px;
        line-height: 1.4;
        color: white;
        word-wrap: break-word;
        ${styles[type]}
    `;
    
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageId;
}

function removeMessage(messageId) {
    if (messageId) {
        const element = document.getElementById(messageId);
        if (element) {
            element.remove();
        }
    }
}

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadVoiceEnhancedAIAssistant();
});

// Also initialize if called directly
loadVoiceEnhancedAIAssistant();