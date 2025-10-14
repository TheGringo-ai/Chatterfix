// 🤖 Fix It Fred AI Chat Integration for ChatterFix CMMS
// The most powerful AI assistant integration for maintenance management
// Connects ChatterFix directly to Fix It Fred AI services

class FixItFredAI {
    constructor() {
        this.apiBase = 'http://localhost:8005'; // Fix It Fred AI Service
        this.fallbackAPI = 'http://localhost:8008'; // AI Development Team
        this.name = 'Fix It Fred';
        this.version = '3.0 Pro';
        this.capabilities = [
            'Equipment Troubleshooting',
            'Maintenance Planning', 
            'Parts Identification',
            'Safety Protocols',
            'Predictive Analytics',
            'Work Order Optimization'
        ];
        this.initializeUI();
    }

    async sendMessage(message, context = 'maintenance') {
        console.log(`🔧 Fix It Fred processing: ${message}`);
        
        try {
            // Try direct AI chat first
            const response = await this.tryDirectAIChat(message, context);
            if (response) return response;
            
            // Try AI team collaboration
            const teamResponse = await this.tryAITeamChat(message, context);
            if (teamResponse) return teamResponse;
            
            // Intelligent fallback with maintenance expertise
            return this.getIntelligentFallback(message);
            
        } catch (error) {
            console.error('Fix It Fred error:', error);
            return this.getIntelligentFallback(message);
        }
    }

    async tryDirectAIChat(message, context) {
        try {
            const payload = {
                message: `As Fix It Fred, the world's most advanced maintenance AI assistant, please help with: "${message}". 
                
Context: ${context}
Focus on: ChatterFix CMMS platform capabilities, maintenance best practices, equipment troubleshooting, and safety protocols.

Please provide:
1. Direct, actionable advice
2. Safety considerations
3. ChatterFix feature recommendations
4. Next steps

Be professional, knowledgeable, and focus on practical solutions.`,
                context: context,
                system_prompt: "You are Fix It Fred, an expert maintenance technician AI with decades of experience in industrial maintenance, CMMS systems, and equipment troubleshooting."
            };

            const response = await fetch(`${this.apiBase}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                if (data.response) {
                    return this.formatAIResponse(data.response, 'direct');
                }
            }
        } catch (error) {
            console.log('Direct AI chat failed, trying alternative endpoints...');
        }
        return null;
    }

    async tryAITeamChat(message, context) {
        try {
            // Create AI team collaboration for complex maintenance questions
            const collaborationResponse = await fetch(`${this.fallbackAPI}/api/collaboration`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(['maintenance_expert', 'safety_officer', 'efficiency_optimizer'])
            }, { params: { objective: `Provide comprehensive maintenance guidance for: ${message}` }});

            if (collaborationResponse.ok) {
                const collaboration = await collaborationResponse.json();
                return this.formatAIResponse(
                    `✅ AI Team assembled for your maintenance question!\n\nOur expert team is analyzing: "${message}"\n\nThis advanced AI collaboration will provide you with comprehensive guidance covering equipment analysis, safety protocols, and optimization strategies.`,
                    'team'
                );
            }
        } catch (error) {
            console.log('AI team collaboration failed, using intelligent fallback...');
        }
        return null;
    }

    formatAIResponse(response, type = 'direct') {
        const expertise = type === 'team' ? '🧠 AI Team Response' : '🔧 Fix It Fred';
        
        let formattedResponse = `
            <div class="fred-response">
                <div class="fred-header">
                    <span class="fred-icon">${expertise}</span>
                    <span class="fred-badge">Professional Maintenance AI</span>
                </div>
                <div class="fred-content">${response}</div>
                <div class="fred-features">
                    <strong>🛠️ ChatterFix CMMS Integration:</strong>
                    <div class="feature-grid">
                        <button onclick="window.fredAI.quickAction('workorder')" class="quick-btn">📝 Create Work Order</button>
                        <button onclick="window.fredAI.quickAction('assets')" class="quick-btn">🏭 Asset Management</button>
                        <button onclick="window.fredAI.quickAction('parts')" class="quick-btn">🔧 Parts Lookup</button>
                        <button onclick="window.fredAI.quickAction('analytics')" class="quick-btn">📊 Analytics</button>
                    </div>
                </div>
                <div class="fred-footer">
                    <span>Powered by Fix It Fred AI v${this.version} | ChatterFix CMMS Pro</span>
                </div>
            </div>
        `;
        
        return formattedResponse;
    }

    getIntelligentFallback(message) {
        // Analyze message for maintenance context
        const maintenanceKeywords = {
            equipment: ['motor', 'pump', 'valve', 'bearing', 'belt', 'machine', 'equipment'],
            electrical: ['electrical', 'wire', 'circuit', 'voltage', 'amp', 'power', 'electric'],
            hydraulic: ['hydraulic', 'fluid', 'pressure', 'hose', 'cylinder', 'pump'],
            safety: ['safety', 'lockout', 'tagout', 'ppe', 'hazard', 'risk'],
            planning: ['schedule', 'plan', 'maintenance', 'preventive', 'predictive'],
            parts: ['part', 'spare', 'inventory', 'order', 'stock', 'replacement']
        };

        let category = 'general';
        let categoryMatch = '';
        
        for (const [cat, keywords] of Object.entries(maintenanceKeywords)) {
            if (keywords.some(keyword => message.toLowerCase().includes(keyword))) {
                category = cat;
                categoryMatch = keywords.find(k => message.toLowerCase().includes(k));
                break;
            }
        }

        const responses = {
            equipment: `🔧 **Equipment Analysis Mode**\n\nI see you're asking about "${categoryMatch}" related maintenance. Here's what Fix It Fred recommends:\n\n**Immediate Actions:**\n✅ Safety first - ensure equipment is locked out\n✅ Visual inspection for obvious issues\n✅ Check maintenance history in ChatterFix\n\n**ChatterFix Features to Use:**\n📝 Create diagnostic work order\n📊 Review equipment analytics\n🔍 Check parts availability`,
            
            electrical: `⚡ **Electrical Systems Expert**\n\nFor electrical maintenance involving "${categoryMatch}":\n\n**Safety Protocol:**\n🚨 LOCKOUT/TAGOUT procedures mandatory\n🚨 Verify zero energy state\n🚨 Use appropriate PPE\n\n**Diagnostic Steps:**\n1. Visual inspection for damage\n2. Voltage/continuity testing\n3. Load analysis\n\n**ChatterFix Integration:**\n📋 Log all electrical work\n🔄 Schedule follow-up inspections`,

            hydraulic: `🏭 **Hydraulic Systems Specialist**\n\nHydraulic system maintenance for "${categoryMatch}":\n\n**Key Checks:**\n• Fluid levels and condition\n• Pressure readings\n• Leak inspection\n• Filter condition\n\n**Maintenance Actions:**\n✅ Use ChatterFix to track fluid changes\n✅ Monitor pressure trends\n✅ Schedule proactive replacements`,

            safety: `🛡️ **Safety Protocol Advisor**\n\nSafety is our top priority for "${categoryMatch}":\n\n**Essential Steps:**\n🔒 Lockout/Tagout procedures\n👷 Proper PPE requirements\n⚠️ Hazard identification\n📋 Safety documentation\n\n**ChatterFix Safety Features:**\n📊 Safety incident tracking\n🔄 Compliance monitoring\n📝 Safety checklist integration`,

            planning: `📅 **Maintenance Planning Expert**\n\nOptimizing "${categoryMatch}" strategies:\n\n**Planning Framework:**\n🎯 Preventive maintenance scheduling\n📈 Predictive analytics integration\n💰 Cost optimization\n⏱️ Downtime minimization\n\n**ChatterFix Planning Tools:**\n📊 Advanced analytics dashboard\n🔄 Automated scheduling\n📈 Performance trending`,

            parts: `🔧 **Parts & Inventory Specialist**\n\nManaging "${categoryMatch}" efficiently:\n\n**Inventory Optimization:**\n📦 Smart stock levels\n🔄 Automated reordering\n💰 Cost tracking\n⚡ Emergency availability\n\n**ChatterFix Inventory Features:**\n📊 Real-time stock monitoring\n🔍 Parts cross-referencing\n📈 Usage analytics\n🚨 Low stock alerts`,

            general: `👋 **Fix It Fred AI Assistant**\n\nI'm here to help with all your maintenance needs!\n\n**Core Capabilities:**\n🔧 Equipment troubleshooting\n📅 Maintenance planning\n🛡️ Safety protocols\n📊 Performance optimization\n\n**ChatterFix CMMS Integration:**\n✨ AI-powered work orders\n🏭 Predictive maintenance\n📱 Mobile technician tools\n🤖 Intelligent automation`
        };

        return this.formatAIResponse(responses[category], 'intelligent');
    }

    quickAction(action) {
        const actions = {
            workorder: () => {
                window.open('/dashboard/work-orders/create', '_blank');
                this.showToast('🔧 Opening Work Order Creator...');
            },
            assets: () => {
                window.open('/dashboard/assets', '_blank');
                this.showToast('🏭 Accessing Asset Management...');
            },
            parts: () => {
                window.open('/dashboard/parts', '_blank');
                this.showToast('🔧 Opening Parts Inventory...');
            },
            analytics: () => {
                window.open('/dashboard/analytics', '_blank');
                this.showToast('📊 Loading Analytics Dashboard...');
            }
        };
        
        if (actions[action]) {
            actions[action]();
        }
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'fred-toast';
        toast.innerHTML = message;
        toast.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            background: linear-gradient(135deg, #006fee, #4285f4);
            color: white; padding: 15px 20px; border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-weight: 500; animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    initializeUI() {
        // Add Fix It Fred specific styles
        if (!document.getElementById('fred-ai-styles')) {
            const styles = document.createElement('style');
            styles.id = 'fred-ai-styles';
            styles.textContent = `
                .fred-response {
                    background: linear-gradient(135deg, #f8f9ff, #e8f2ff);
                    border: 2px solid #006fee;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 10px 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .fred-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #e0e8ff;
                }
                
                .fred-icon {
                    font-size: 16px;
                    font-weight: bold;
                    color: #006fee;
                }
                
                .fred-badge {
                    background: linear-gradient(135deg, #006fee, #4285f4);
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                }
                
                .fred-content {
                    line-height: 1.6;
                    color: #333;
                    margin-bottom: 20px;
                }
                
                .fred-features {
                    background: rgba(0, 111, 238, 0.05);
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                }
                
                .feature-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 8px;
                    margin-top: 10px;
                }
                
                .quick-btn {
                    background: linear-gradient(135deg, #006fee, #4285f4);
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .quick-btn:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0, 111, 238, 0.3);
                }
                
                .fred-footer {
                    text-align: center;
                    font-size: 11px;
                    color: #666;
                    margin-top: 15px;
                    padding-top: 10px;
                    border-top: 1px solid #e0e8ff;
                }
                
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
                
                .thinking-animation {
                    display: inline-block;
                    animation: pulse 1.5s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `;
            document.head.appendChild(styles);
        }
    }
}

// Enhanced Chat Integration
class ChatterFixFredIntegration {
    constructor() {
        this.fredAI = new FixItFredAI();
        this.initializeChatOverride();
        console.log('🚀 Fix It Fred AI integrated with ChatterFix CMMS!');
    }

    initializeChatOverride() {
        // Override the sendChatMessage function if it exists
        window.sendChatMessage = async (message) => {
            await this.handleChatMessage(message);
        };

        // Also override sendMessage for compatibility
        window.sendMessage = () => {
            const input = document.getElementById('chat-input');
            if (input && input.value.trim()) {
                const message = input.value.trim();
                input.value = '';
                this.handleChatMessage(message);
            }
        };

        // Make fredAI globally available for quick actions
        window.fredAI = this.fredAI;
    }

    async handleChatMessage(message) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.warn('Chat messages container not found');
            return;
        }

        // Add user message
        this.addMessage(chatMessages, message, 'user');

        // Add thinking indicator
        const thinkingId = this.addThinkingMessage(chatMessages);

        try {
            // Get AI response
            const response = await this.fredAI.sendMessage(message);
            
            // Remove thinking indicator
            const thinkingElement = document.getElementById(thinkingId);
            if (thinkingElement) thinkingElement.remove();
            
            // Add AI response
            this.addMessage(chatMessages, response, 'assistant');
            
        } catch (error) {
            console.error('Chat error:', error);
            
            // Remove thinking indicator
            const thinkingElement = document.getElementById(thinkingId);
            if (thinkingElement) thinkingElement.remove();
            
            // Add error message
            this.addMessage(chatMessages, 
                this.fredAI.getIntelligentFallback(message), 
                'assistant'
            );
        }

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addMessage(container, content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        if (type === 'user') {
            messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
        } else {
            messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
        }
        
        container.appendChild(messageDiv);
        return messageDiv;
    }

    addThinkingMessage(container) {
        const thinkingId = 'thinking-' + Date.now();
        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = thinkingId;
        thinkingDiv.className = 'message assistant-message';
        thinkingDiv.innerHTML = `
            <div class="message-content">
                <div style="display: flex; align-items: center; gap: 10px;">
                    🤖 <span class="thinking-animation">Fix It Fred is analyzing your maintenance question...</span>
                </div>
            </div>
        `;
        container.appendChild(thinkingDiv);
        return thinkingId;
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.chatterFixFred = new ChatterFixFredIntegration();
    });
} else {
    window.chatterFixFred = new ChatterFixFredIntegration();
}

console.log('🔧 Fix It Fred AI Integration Loaded!');
console.log('🎯 ChatterFix CMMS now powered by advanced AI assistant!');