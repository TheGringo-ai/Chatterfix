/**
 * ChatterFix Ultimate Interactive Demo System
 * The most compelling CMMS demo experience on the web.
 *
 * Features:
 * - Multi-page guided tours with state persistence
 * - Animated spotlight highlighting
 * - Progress tracking with visual indicators
 * - Voice-guided option (text-to-speech)
 * - Interactive feature demonstrations
 * - Celebration effects on completion
 */

class ChatterFixDemoSystem {
    constructor() {
        this.isActive = false;
        this.currentModuleIndex = 0;
        this.currentStepIndex = 0;
        this.voiceEnabled = false;
        this.autoAdvance = false;
        this.speechSynth = window.speechSynthesis;

        // Inject demo styles
        this.injectStyles();

        // Define comprehensive Demo Modules and Steps
        this.modules = [
            // ========== MODULE 1: WELCOME & DASHBOARD ==========
            {
                id: 'welcome',
                title: 'Welcome',
                icon: '🏠',
                path: '/demo',
                steps: [
                    {
                        selector: null, // Full screen welcome
                        title: '🚀 Welcome to ChatterFix',
                        description: 'The AI-powered CMMS built FOR THE TECHNICIAN. Experience hands-free maintenance management with voice commands, OCR scanning, and predictive AI.',
                        position: 'center',
                        highlight: 'pulse',
                        duration: 5000
                    },
                    {
                        selector: '.navbar-brand, .logo-container, header',
                        title: '📊 Command Center Dashboard',
                        description: 'Your mission control for maintenance operations. Real-time KPIs, AI predictions, and instant access to everything you need.',
                        position: 'bottom',
                        highlight: 'glow'
                    },
                    {
                        selector: '.nav-tabs-scroll, .nav-tabs, .sidebar-nav',
                        title: '🧭 Intuitive Navigation',
                        description: 'Every module is one click away. Work Orders, Assets, Inventory, Team, Analytics, and AI-powered tools all within reach.',
                        position: 'bottom',
                        highlight: 'outline'
                    },
                    {
                        selector: '.kpi-card, .stat-card, .metric-card, .dashboard-stats',
                        title: '📈 Live KPI Metrics',
                        description: 'Real-time visibility into your operation: Open work orders, completion rates, equipment uptime, and cost tracking.',
                        position: 'bottom',
                        highlight: 'glow'
                    }
                ]
            },

            // ========== MODULE 2: AI FEATURES ==========
            {
                id: 'ai_features',
                title: 'AI Power',
                icon: '🤖',
                path: '/demo',
                steps: [
                    {
                        selector: '.ai-fab, .ai-widget, .ai-button, [onclick*="toggleAI"]',
                        title: '🤖 AI Assistant',
                        description: 'Your intelligent maintenance companion. Ask questions naturally: "Show me critical work orders" or "What\'s the status of Pump Station B?"',
                        position: 'left',
                        highlight: 'pulse',
                        demo: 'ai-chat'
                    },
                    {
                        selector: null,
                        title: '🎤 Voice Commands',
                        description: 'Go completely hands-free! Speak to create work orders, check out parts, or get AI insights while you work. Perfect for technicians on the floor.',
                        position: 'center',
                        highlight: 'pulse',
                        demo: 'voice'
                    },
                    {
                        selector: null,
                        title: '📷 OCR Document Scanning',
                        description: 'Point your camera at equipment labels, serial numbers, or paperwork. ChatterFix automatically captures and organizes the data.',
                        position: 'center',
                        highlight: 'scan',
                        demo: 'ocr'
                    },
                    {
                        selector: null,
                        title: '🔮 Predictive Maintenance',
                        description: 'AI analyzes equipment patterns to predict failures BEFORE they happen. Reduce downtime by up to 45% with proactive maintenance alerts.',
                        position: 'center',
                        highlight: 'glow'
                    }
                ]
            },

            // ========== MODULE 3: WORK ORDERS ==========
            {
                id: 'work_orders',
                title: 'Work Orders',
                icon: '📋',
                path: '/demo/work-orders',
                steps: [
                    {
                        selector: '.kanban-board, .kanban-container, .work-orders-container',
                        title: '📋 Smart Work Order Management',
                        description: 'Visualize your entire workflow at a glance. Drag-and-drop cards between columns to update status instantly.',
                        position: 'bottom',
                        highlight: 'outline'
                    },
                    {
                        selector: '.filter-bar, .filter-section, .search-box, input[type="search"]',
                        title: '🔍 Powerful Search & Filters',
                        description: 'Find any work order instantly. Filter by priority, technician, asset, date, or use natural language search.',
                        position: 'bottom',
                        highlight: 'glow'
                    },
                    {
                        selector: '.priority-urgent, .priority-high, .badge-danger, .urgent',
                        title: '🚨 Priority Management',
                        description: 'Critical tasks are highlighted automatically. AI can even suggest priority adjustments based on equipment health data.',
                        position: 'right',
                        highlight: 'pulse'
                    },
                    {
                        selector: 'button[onclick*="create"], .btn-primary, .add-button, .create-wo',
                        title: '➕ Quick Work Order Creation',
                        description: 'Create work orders in seconds. Voice-enabled: just say "Create urgent work order for HVAC unit 3" and it\'s done.',
                        position: 'bottom',
                        highlight: 'glow'
                    }
                ]
            },

            // ========== MODULE 4: ASSETS ==========
            {
                id: 'assets',
                title: 'Assets',
                icon: '🏭',
                path: '/demo/assets',
                steps: [
                    {
                        selector: '.asset-grid, .asset-list, .assets-container, .card-grid',
                        title: '🏭 Complete Asset Registry',
                        description: 'Every piece of equipment catalogued with full history, specifications, manuals, and real-time health scores.',
                        position: 'bottom',
                        highlight: 'outline'
                    },
                    {
                        selector: '.health-indicator, .health-score, .asset-status',
                        title: '💚 Real-Time Health Scores',
                        description: 'AI continuously monitors each asset. Green means healthy, yellow needs attention, red requires immediate action.',
                        position: 'right',
                        highlight: 'pulse'
                    },
                    {
                        selector: '.qr-code, .barcode, .scan-button, [onclick*="scan"]',
                        title: '📱 QR/Barcode Scanning',
                        description: 'Scan any asset tag to instantly pull up equipment details, maintenance history, and create work orders.',
                        position: 'left',
                        highlight: 'scan'
                    },
                    {
                        selector: '.maintenance-history, .history-tab, .timeline',
                        title: '📚 Complete Maintenance History',
                        description: 'Every repair, inspection, and part replacement logged with timestamps and technician notes.',
                        position: 'bottom',
                        highlight: 'glow'
                    }
                ]
            },

            // ========== MODULE 5: INVENTORY ==========
            {
                id: 'inventory',
                title: 'Inventory',
                icon: '📦',
                path: '/demo/inventory',
                steps: [
                    {
                        selector: '.inventory-list, .parts-grid, .inventory-table',
                        title: '📦 Smart Inventory Management',
                        description: 'Track every part, supply, and consumable. Real-time stock levels with automatic reorder alerts.',
                        position: 'bottom',
                        highlight: 'outline'
                    },
                    {
                        selector: '.low-stock, .stock-alert, .reorder-point',
                        title: '⚠️ Low Stock Alerts',
                        description: 'Never run out of critical parts. AI predicts usage patterns and suggests optimal reorder quantities.',
                        position: 'right',
                        highlight: 'pulse'
                    },
                    {
                        selector: '.part-lookup, .search-parts, input[placeholder*="part"]',
                        title: '🔎 Instant Part Lookup',
                        description: 'Find any part by name, number, or description. Cross-reference with compatible assets and vendors.',
                        position: 'bottom',
                        highlight: 'glow'
                    }
                ]
            },

            // ========== MODULE 6: TEAM ==========
            {
                id: 'team',
                title: 'Team',
                icon: '👥',
                path: '/demo/team',
                steps: [
                    {
                        selector: '.technician-grid, .team-list, .staff-cards',
                        title: '👥 Workforce Management',
                        description: 'Track your entire maintenance team. Skills, certifications, current workload, and availability at a glance.',
                        position: 'bottom',
                        highlight: 'outline'
                    },
                    {
                        selector: '.workload-chart, .assignment-count, .task-count',
                        title: '⚖️ Workload Balancing',
                        description: 'AI suggests optimal task assignments based on skills, location, and current workload. Prevent burnout and improve efficiency.',
                        position: 'right',
                        highlight: 'glow'
                    },
                    {
                        selector: '.skills-badge, .certification, .training-status',
                        title: '🎓 Skills & Training Tracking',
                        description: 'Monitor certifications, track training progress, and ensure the right technician is assigned to each job.',
                        position: 'bottom',
                        highlight: 'pulse'
                    }
                ]
            },

            // ========== MODULE 7: PURCHASING ==========
            {
                id: 'purchasing',
                title: 'Purchasing',
                icon: '🛒',
                path: '/demo/purchasing',
                steps: [
                    {
                        selector: '.purchase-orders, .po-list, .orders-container',
                        title: '🛒 Streamlined Purchasing',
                        description: 'From requisition to receipt, manage the entire procurement workflow in one place.',
                        position: 'bottom',
                        highlight: 'outline'
                    },
                    {
                        selector: '.vendor-list, .suppliers, .vendor-card',
                        title: '🤝 Vendor Management',
                        description: 'Track all your suppliers, compare prices, and maintain vendor relationships.',
                        position: 'right',
                        highlight: 'glow'
                    },
                    {
                        selector: '.auto-reorder, .smart-order, .ai-suggestion',
                        title: '🤖 AI-Powered Ordering',
                        description: 'AI predicts part usage and automatically generates purchase suggestions before you run out.',
                        position: 'bottom',
                        highlight: 'pulse'
                    }
                ]
            },

            // ========== MODULE 8: ANALYTICS ==========
            {
                id: 'analytics',
                title: 'Analytics',
                icon: '📊',
                path: '/demo/analytics',
                steps: [
                    {
                        selector: '.analytics-dashboard, .charts-container, .reports-section',
                        title: '📊 Deep Analytics & Insights',
                        description: 'Transform maintenance data into actionable insights. Costs, downtime, efficiency trends, and more.',
                        position: 'bottom',
                        highlight: 'outline'
                    },
                    {
                        selector: '.chart, .graph, canvas, .chart-container',
                        title: '📈 Visual Data Stories',
                        description: 'Interactive charts reveal patterns in your maintenance operations. Drill down into any metric.',
                        position: 'bottom',
                        highlight: 'glow'
                    },
                    {
                        selector: '.export-btn, .report-download, [onclick*="export"]',
                        title: '📄 Custom Reports',
                        description: 'Generate professional reports in seconds. Schedule automatic delivery to stakeholders.',
                        position: 'left',
                        highlight: 'pulse'
                    }
                ]
            },

            // ========== MODULE 9: FIX-IT FRED ==========
            {
                id: 'fix_it_fred',
                title: 'Fix-it-Fred',
                icon: '🔧',
                path: '/demo/fix-it-fred',
                steps: [
                    {
                        selector: '.fred-interface, .ai-expert, .fred-container',
                        title: '🔧 Meet Fix-it-Fred',
                        description: 'Your AI maintenance expert. Fred combines decades of maintenance knowledge with real-time equipment data.',
                        position: 'bottom',
                        highlight: 'pulse'
                    },
                    {
                        selector: '.chat-interface, .conversation, .message-list',
                        title: '💬 Natural Conversations',
                        description: 'Ask Fred anything: troubleshooting tips, maintenance procedures, part recommendations. He learns your equipment.',
                        position: 'right',
                        highlight: 'glow'
                    },
                    {
                        selector: '.expertise-cards, .capabilities, .skills-section',
                        title: '🧠 Expert Knowledge Base',
                        description: 'Fred knows HVAC, electrical, plumbing, hydraulics, and more. Constantly learning from industry best practices.',
                        position: 'bottom',
                        highlight: 'outline'
                    }
                ]
            },

            // ========== MODULE 10: COMPLETION ==========
            {
                id: 'completion',
                title: 'Complete',
                icon: '🎉',
                path: null, // Stay on current page
                steps: [
                    {
                        selector: null,
                        title: '🎉 Demo Complete!',
                        description: 'You\'ve experienced the power of ChatterFix CMMS. Ready to transform your maintenance operations?',
                        position: 'center',
                        highlight: 'celebrate',
                        isCompletion: true
                    }
                ]
            }
        ];

        // Create UI Elements
        this.createUIElements();

        // Check for active demo state on load
        this.checkAutoStart();

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    injectStyles() {
        if (document.getElementById('demo-system-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'demo-system-styles';
        styles.textContent = `
            /* Demo System Overlay */
            .demo-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.75);
                z-index: 99998;
                backdrop-filter: blur(4px);
                opacity: 0;
                transition: opacity 0.4s ease;
                pointer-events: none;
            }
            .demo-overlay.active {
                opacity: 1;
                pointer-events: auto;
            }

            /* Spotlight Effect */
            .demo-spotlight {
                position: absolute;
                z-index: 99999;
                border-radius: 12px;
                pointer-events: none;
                transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8);
            }
            .demo-spotlight.pulse {
                animation: spotlight-pulse 2s infinite;
            }
            .demo-spotlight.glow {
                box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8), 0 0 30px rgba(52, 152, 219, 0.6), inset 0 0 20px rgba(52, 152, 219, 0.3);
            }
            .demo-spotlight.outline {
                border: 3px solid #3498db;
                box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8), 0 0 20px rgba(52, 152, 219, 0.4);
            }
            .demo-spotlight.scan {
                animation: spotlight-scan 1.5s infinite;
                border: 2px dashed #2ecc71;
            }

            @keyframes spotlight-pulse {
                0%, 100% { box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8), 0 0 20px rgba(52, 152, 219, 0.4); }
                50% { box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8), 0 0 40px rgba(52, 152, 219, 0.8); }
            }

            @keyframes spotlight-scan {
                0%, 100% { border-color: #2ecc71; box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8), 0 0 20px rgba(46, 204, 113, 0.4); }
                50% { border-color: #27ae60; box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8), 0 0 40px rgba(46, 204, 113, 0.8); }
            }

            /* Demo Tooltip */
            .demo-tooltip {
                position: fixed;
                z-index: 100000;
                background: linear-gradient(145deg, rgba(30, 40, 55, 0.98), rgba(20, 30, 45, 0.98));
                padding: 0;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(52, 152, 219, 0.2);
                width: 380px;
                max-width: 90vw;
                color: #fff;
                backdrop-filter: blur(20px);
                transform: translateY(20px);
                opacity: 0;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                overflow: hidden;
            }
            .demo-tooltip.active {
                transform: translateY(0);
                opacity: 1;
            }
            .demo-tooltip.center {
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%);
            }
            .demo-tooltip.center.active {
                transform: translate(-50%, -50%);
            }

            .demo-tooltip-header {
                background: linear-gradient(135deg, #3498db, #2980b9);
                padding: 20px 25px;
                position: relative;
                overflow: hidden;
            }
            .demo-tooltip-header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
                animation: header-shine 3s infinite;
            }
            @keyframes header-shine {
                0%, 100% { transform: rotate(0deg); }
                50% { transform: rotate(180deg); }
            }

            .demo-tooltip-title {
                font-size: 1.3rem;
                font-weight: 700;
                margin: 0;
                position: relative;
                z-index: 1;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }

            .demo-tooltip-body {
                padding: 25px;
            }

            .demo-tooltip-description {
                font-size: 1rem;
                line-height: 1.7;
                color: rgba(255, 255, 255, 0.9);
                margin-bottom: 20px;
            }

            /* Progress Bar */
            .demo-progress-container {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                height: 8px;
                margin-bottom: 20px;
                overflow: hidden;
            }
            .demo-progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #3498db, #2ecc71);
                border-radius: 10px;
                transition: width 0.5s ease;
            }
            .demo-progress-text {
                display: flex;
                justify-content: space-between;
                font-size: 0.8rem;
                color: rgba(255, 255, 255, 0.6);
                margin-bottom: 8px;
            }

            /* Navigation Buttons */
            .demo-nav-buttons {
                display: flex;
                gap: 10px;
                justify-content: space-between;
            }
            .demo-btn {
                padding: 12px 24px;
                border-radius: 10px;
                font-size: 0.95rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                border: none;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .demo-btn-exit {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .demo-btn-exit:hover {
                background: rgba(231, 76, 60, 0.3);
                color: #e74c3c;
                border-color: #e74c3c;
            }
            .demo-btn-back {
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .demo-btn-back:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            .demo-btn-back:disabled {
                opacity: 0.3;
                cursor: not-allowed;
            }
            .demo-btn-next {
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: #fff;
                flex: 1;
                justify-content: center;
            }
            .demo-btn-next:hover {
                background: linear-gradient(135deg, #2980b9, #1f6dad);
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(52, 152, 219, 0.4);
            }

            /* Module Progress Dots */
            .demo-module-dots {
                display: flex;
                justify-content: center;
                gap: 8px;
                padding: 15px 25px;
                background: rgba(0, 0, 0, 0.2);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            .demo-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .demo-dot:hover {
                background: rgba(255, 255, 255, 0.4);
            }
            .demo-dot.active {
                background: #3498db;
                transform: scale(1.3);
            }
            .demo-dot.completed {
                background: #2ecc71;
            }

            /* Feature Demo Animations */
            .demo-feature-showcase {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .demo-feature-icon {
                font-size: 2rem;
                animation: feature-bounce 2s infinite;
            }
            @keyframes feature-bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-5px); }
            }

            /* Celebration Effect */
            .demo-confetti {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 100001;
                overflow: hidden;
            }
            .confetti-piece {
                position: absolute;
                width: 10px;
                height: 10px;
                top: -10px;
                animation: confetti-fall 4s linear forwards;
            }
            @keyframes confetti-fall {
                0% { transform: translateY(0) rotate(0deg); opacity: 1; }
                100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
            }

            /* Keyboard Hint */
            .demo-keyboard-hint {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.8);
                color: rgba(255, 255, 255, 0.7);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.8rem;
                z-index: 100002;
                display: flex;
                gap: 15px;
            }
            .demo-keyboard-hint kbd {
                background: rgba(255, 255, 255, 0.1);
                padding: 2px 8px;
                border-radius: 4px;
                margin: 0 3px;
            }

            /* Mobile Responsive */
            @media (max-width: 768px) {
                .demo-tooltip {
                    width: 95vw;
                    max-width: 95vw;
                    left: 2.5vw !important;
                    right: 2.5vw !important;
                    bottom: 20px !important;
                    top: auto !important;
                }
                .demo-tooltip.center {
                    top: auto !important;
                    bottom: 20px !important;
                    left: 2.5vw !important;
                    transform: none;
                }
                .demo-tooltip.center.active {
                    transform: none;
                }
                .demo-keyboard-hint {
                    display: none;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    createUIElements() {
        // Overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'demo-overlay';
        this.overlay.onclick = () => {}; // Prevent clicks through
        document.body.appendChild(this.overlay);

        // Spotlight
        this.spotlight = document.createElement('div');
        this.spotlight.className = 'demo-spotlight';
        document.body.appendChild(this.spotlight);

        // Tooltip
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'demo-tooltip';
        document.body.appendChild(this.tooltip);

        // Keyboard Hint
        this.keyboardHint = document.createElement('div');
        this.keyboardHint.className = 'demo-keyboard-hint';
        this.keyboardHint.innerHTML = '<span><kbd>→</kbd> Next</span><span><kbd>←</kbd> Back</span><span><kbd>Esc</kbd> Exit</span>';
        this.keyboardHint.style.display = 'none';
        document.body.appendChild(this.keyboardHint);
    }

    handleKeyboard(e) {
        if (!this.isActive) return;

        switch(e.key) {
            case 'ArrowRight':
            case 'Enter':
            case ' ':
                e.preventDefault();
                this.nextStep();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.previousStep();
                break;
            case 'Escape':
                e.preventDefault();
                this.stopDemo();
                break;
        }
    }

    loadState() {
        try {
            const state = JSON.parse(localStorage.getItem('chatterfix_demo_state') || '{}');
            if (state.active) {
                this.isActive = true;
                this.currentModuleIndex = state.moduleIndex || 0;
                this.currentStepIndex = state.stepIndex || 0;
            }
        } catch (e) {
            console.log('Demo state storage not available');
        }
    }

    saveState() {
        try {
            localStorage.setItem('chatterfix_demo_state', JSON.stringify({
                active: this.isActive,
                moduleIndex: this.currentModuleIndex,
                stepIndex: this.currentStepIndex
            }));
        } catch (e) {
            console.log('Demo state storage not available');
        }
    }

    clearState() {
        try {
            localStorage.removeItem('chatterfix_demo_state');
        } catch (e) {}
    }

    checkAutoStart() {
        this.loadState();
        if (this.isActive) {
            const currentModule = this.modules[this.currentModuleIndex];
            if (currentModule.path && window.location.pathname !== currentModule.path) {
                window.location.href = currentModule.path;
            } else {
                setTimeout(() => this.showStep(), 500);
            }
        }
    }

    // Main entry point - called by button
    startFullDemo() {
        this.startDemo();
    }

    startDemo() {
        // Hide demo bar
        const demoBar = document.getElementById('demoBar');
        if (demoBar) demoBar.style.display = 'none';

        this.isActive = true;
        this.currentModuleIndex = 0;
        this.currentStepIndex = 0;
        this.saveState();

        // Navigate to start if needed
        const firstModule = this.modules[0];
        if (firstModule.path && window.location.pathname !== firstModule.path) {
            window.location.href = firstModule.path;
        } else {
            this.showStep();
        }
    }

    stopDemo() {
        this.isActive = false;
        this.clearState();

        this.overlay.classList.remove('active');
        this.spotlight.style.display = 'none';
        this.tooltip.classList.remove('active', 'center');
        this.keyboardHint.style.display = 'none';

        setTimeout(() => {
            this.overlay.style.display = 'none';
        }, 400);

        // Show demo bar again
        const demoBar = document.getElementById('demoBar');
        if (demoBar) demoBar.style.display = 'block';

        // Stop any speech
        if (this.speechSynth) {
            this.speechSynth.cancel();
        }
    }

    navigateToModule(moduleIndex) {
        if (moduleIndex >= this.modules.length) {
            this.completeDemo();
            return;
        }

        this.currentModuleIndex = moduleIndex;
        this.currentStepIndex = 0;
        this.saveState();

        const nextModule = this.modules[moduleIndex];
        if (nextModule.path && window.location.pathname !== nextModule.path) {
            window.location.href = nextModule.path;
        } else {
            this.showStep();
        }
    }

    nextStep() {
        const currentModule = this.modules[this.currentModuleIndex];
        const currentStep = currentModule.steps[this.currentStepIndex];

        // Check for completion step
        if (currentStep.isCompletion) {
            this.completeDemo();
            return;
        }

        if (this.currentStepIndex < currentModule.steps.length - 1) {
            this.currentStepIndex++;
            this.saveState();
            this.showStep();
        } else {
            // Move to next module
            this.navigateToModule(this.currentModuleIndex + 1);
        }
    }

    previousStep() {
        if (this.currentStepIndex > 0) {
            this.currentStepIndex--;
            this.saveState();
            this.showStep();
        } else if (this.currentModuleIndex > 0) {
            this.currentModuleIndex--;
            const prevModule = this.modules[this.currentModuleIndex];
            this.currentStepIndex = prevModule.steps.length - 1;
            this.saveState();

            if (prevModule.path && window.location.pathname !== prevModule.path) {
                window.location.href = prevModule.path;
            } else {
                this.showStep();
            }
        }
    }

    showStep() {
        if (!this.isActive) return;

        const currentModule = this.modules[this.currentModuleIndex];
        const step = currentModule.steps[this.currentStepIndex];

        // Show overlay
        this.overlay.style.display = 'block';
        setTimeout(() => this.overlay.classList.add('active'), 10);

        // Show keyboard hint
        this.keyboardHint.style.display = 'flex';

        // Find target element
        let target = null;
        if (step.selector) {
            target = document.querySelector(step.selector);
        }

        if (target) {
            this.highlightElement(target, step);
        } else {
            this.showCenterModal(step);
        }

        // Voice narration if enabled
        if (this.voiceEnabled && this.speechSynth) {
            this.speechSynth.cancel();
            const utterance = new SpeechSynthesisUtterance(step.description);
            utterance.rate = 0.9;
            this.speechSynth.speak(utterance);
        }
    }

    highlightElement(element, step) {
        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Position spotlight
        setTimeout(() => {
            const newRect = element.getBoundingClientRect();
            this.spotlight.style.display = 'block';
            this.spotlight.style.width = (newRect.width + 24) + 'px';
            this.spotlight.style.height = (newRect.height + 24) + 'px';
            this.spotlight.style.left = (newRect.left + window.scrollX - 12) + 'px';
            this.spotlight.style.top = (newRect.top + window.scrollY - 12) + 'px';
            this.spotlight.className = 'demo-spotlight ' + (step.highlight || 'glow');

            // Position tooltip
            this.positionTooltip(newRect, step);
        }, 300);
    }

    positionTooltip(targetRect, step) {
        this.tooltip.classList.remove('center');
        this.tooltip.innerHTML = this.renderTooltipContent(step);

        const tooltipWidth = 380;
        const tooltipHeight = this.tooltip.offsetHeight || 300;
        const padding = 20;

        let top, left;

        // Position based on step.position or auto-detect
        const position = step.position || 'bottom';

        switch(position) {
            case 'bottom':
                top = targetRect.bottom + window.scrollY + padding;
                left = targetRect.left + window.scrollX + (targetRect.width / 2) - (tooltipWidth / 2);
                break;
            case 'top':
                top = targetRect.top + window.scrollY - tooltipHeight - padding;
                left = targetRect.left + window.scrollX + (targetRect.width / 2) - (tooltipWidth / 2);
                break;
            case 'left':
                top = targetRect.top + window.scrollY + (targetRect.height / 2) - (tooltipHeight / 2);
                left = targetRect.left + window.scrollX - tooltipWidth - padding;
                break;
            case 'right':
                top = targetRect.top + window.scrollY + (targetRect.height / 2) - (tooltipHeight / 2);
                left = targetRect.right + window.scrollX + padding;
                break;
        }

        // Keep on screen
        left = Math.max(10, Math.min(left, window.innerWidth - tooltipWidth - 10));
        top = Math.max(10 + window.scrollY, top);

        this.tooltip.style.top = top + 'px';
        this.tooltip.style.left = left + 'px';

        setTimeout(() => this.tooltip.classList.add('active'), 50);
    }

    showCenterModal(step) {
        this.spotlight.style.display = 'none';
        this.tooltip.innerHTML = this.renderTooltipContent(step);
        this.tooltip.classList.add('center');
        setTimeout(() => this.tooltip.classList.add('active'), 50);
    }

    renderTooltipContent(step) {
        const totalSteps = this.modules.reduce((sum, m) => sum + m.steps.length, 0);
        const currentStepNum = this.modules.slice(0, this.currentModuleIndex).reduce((sum, m) => sum + m.steps.length, 0) + this.currentStepIndex + 1;
        const progress = Math.round((currentStepNum / totalSteps) * 100);

        const currentModule = this.modules[this.currentModuleIndex];
        const isFirstStep = this.currentModuleIndex === 0 && this.currentStepIndex === 0;
        const isCompletion = step.isCompletion;

        // Feature showcase for special demos
        let featureShowcase = '';
        if (step.demo === 'voice') {
            featureShowcase = `
                <div class="demo-feature-showcase">
                    <div class="demo-feature-icon">🎤</div>
                    <div>
                        <strong>Try saying:</strong><br>
                        <em>"Create a work order for HVAC unit maintenance"</em>
                    </div>
                </div>
            `;
        } else if (step.demo === 'ocr') {
            featureShowcase = `
                <div class="demo-feature-showcase">
                    <div class="demo-feature-icon">📷</div>
                    <div>
                        <strong>Point & Capture:</strong><br>
                        <em>Automatically reads serial numbers, barcodes & text</em>
                    </div>
                </div>
            `;
        } else if (step.demo === 'ai-chat') {
            featureShowcase = `
                <div class="demo-feature-showcase">
                    <div class="demo-feature-icon">💬</div>
                    <div>
                        <strong>Natural Language:</strong><br>
                        <em>"What work orders are due this week?"</em>
                    </div>
                </div>
            `;
        }

        // Module navigation dots
        let moduleDots = this.modules.map((m, idx) => {
            let dotClass = 'demo-dot';
            if (idx < this.currentModuleIndex) dotClass += ' completed';
            if (idx === this.currentModuleIndex) dotClass += ' active';
            return `<div class="${dotClass}" title="${m.title}" onclick="window.demoSystem.navigateToModule(${idx})"></div>`;
        }).join('');

        return `
            <div class="demo-tooltip-header">
                <h3 class="demo-tooltip-title">${step.title}</h3>
            </div>
            <div class="demo-tooltip-body">
                <p class="demo-tooltip-description">${step.description}</p>
                ${featureShowcase}
                <div class="demo-progress-text">
                    <span>${currentModule.icon} ${currentModule.title}</span>
                    <span>${progress}% Complete</span>
                </div>
                <div class="demo-progress-container">
                    <div class="demo-progress-bar" style="width: ${progress}%"></div>
                </div>
                <div class="demo-nav-buttons">
                    <button class="demo-btn demo-btn-exit" onclick="window.demoSystem.stopDemo()">
                        <i class="fas fa-times"></i> Exit
                    </button>
                    <div style="display: flex; gap: 10px; flex: 1; justify-content: flex-end;">
                        <button class="demo-btn demo-btn-back" onclick="window.demoSystem.previousStep()" ${isFirstStep ? 'disabled' : ''}>
                            <i class="fas fa-arrow-left"></i> Back
                        </button>
                        <button class="demo-btn demo-btn-next" onclick="window.demoSystem.nextStep()">
                            ${isCompletion ? 'Finish' : 'Next'} <i class="fas fa-arrow-right"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="demo-module-dots">
                ${moduleDots}
            </div>
        `;
    }

    completeDemo() {
        this.stopDemo();
        this.showCelebration();
    }

    showCelebration() {
        // Confetti effect
        const confettiContainer = document.createElement('div');
        confettiContainer.className = 'demo-confetti';
        document.body.appendChild(confettiContainer);

        const colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c'];
        for (let i = 0; i < 100; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti-piece';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 2 + 's';
            confetti.style.animationDuration = (3 + Math.random() * 2) + 's';
            confettiContainer.appendChild(confetti);
        }

        setTimeout(() => confettiContainer.remove(), 5000);

        // Celebration modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 100001;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
            animation: fadeIn 0.5s ease;
        `;
        modal.innerHTML = `
            <div style="
                background: linear-gradient(145deg, rgba(30, 40, 55, 0.98), rgba(20, 30, 45, 0.98));
                padding: 50px;
                border-radius: 30px;
                text-align: center;
                max-width: 500px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                box-shadow: 0 30px 80px rgba(0, 0, 0, 0.5), 0 0 60px rgba(52, 152, 219, 0.3);
                color: #fff;
            ">
                <div style="font-size: 5rem; margin-bottom: 20px; animation: bounce 1s infinite;">🎉</div>
                <h2 style="font-size: 2rem; margin-bottom: 15px; background: linear-gradient(135deg, #3498db, #2ecc71); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Tour Complete!</h2>
                <p style="font-size: 1.1rem; line-height: 1.7; color: rgba(255, 255, 255, 0.8); margin-bottom: 30px;">
                    You've experienced the power of ChatterFix CMMS. Ready to transform your maintenance operations with AI-powered, hands-free workflows?
                </p>
                <div style="display: flex; flex-direction: column; gap: 15px;">
                    <a href="/landing" style="
                        display: block;
                        padding: 18px 40px;
                        background: linear-gradient(135deg, #2ecc71, #27ae60);
                        color: white;
                        text-decoration: none;
                        border-radius: 12px;
                        font-size: 1.2rem;
                        font-weight: 700;
                        box-shadow: 0 10px 30px rgba(46, 204, 113, 0.4);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                        🚀 Start Free Trial
                    </a>
                    <button onclick="window.demoSystem.startDemo()" style="
                        padding: 15px 30px;
                        background: transparent;
                        border: 2px solid rgba(255, 255, 255, 0.3);
                        color: white;
                        border-radius: 12px;
                        font-size: 1rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    " onmouseover="this.style.borderColor='#3498db'" onmouseout="this.style.borderColor='rgba(255,255,255,0.3)'">
                        🔄 Restart Tour
                    </button>
                    <button onclick="this.closest('div').parentElement.parentElement.remove()" style="
                        padding: 10px;
                        background: none;
                        border: none;
                        color: rgba(255, 255, 255, 0.5);
                        cursor: pointer;
                        font-size: 0.9rem;
                        text-decoration: underline;
                    ">
                        Continue Exploring
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Add keyframe animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    // Also expose as dismissDemoBar for compatibility
    dismissDemoBar() {
        const demoBar = document.getElementById('demoBar');
        if (demoBar) demoBar.style.display = 'none';

        try {
            const state = JSON.parse(localStorage.getItem('chatterfix_demo_state') || '{}');
            state.dismissed = true;
            localStorage.setItem('chatterfix_demo_state', JSON.stringify(state));
        } catch (e) {}
    }
}

// Global instance
window.demoSystem = new ChatterFixDemoSystem();
