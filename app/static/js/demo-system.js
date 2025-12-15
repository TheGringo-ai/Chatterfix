/**
 * ChatterFix Enhanced Interactive Demo System
 * Handles multi-page guided tours with state persistence.
 */

class ChatterFixDemoSystem {
    constructor() {
        this.isActive = false;
        this.currentModuleIndex = 0;
        this.currentStepIndex = 0;
        
        // Define the Demo Modules and Steps
        this.modules = [
            {
                id: 'dashboard',
                path: '/demo', // Maps to the URL path
                steps: [
                    {
                        selector: '.navbar',
                        title: 'Welcome to ChatterFix CMMS',
                        description: 'Your intelligent, all-in-one maintenance solution. Let\'s take a tour of the capabilities.',
                        position: 'bottom'
                    },
                    {
                        selector: '.ai-brain',
                        title: 'AI Command Center',
                        description: 'The neural core of your operations. Here, AI analyzes millions of data points to predict failures before they happen.',
                        position: 'bottom'
                    },
                    {
                        selector: '.predictions',
                        title: 'Predictive Analytics',
                        description: 'View real-time failure predictions. ChatterFix warns you days in advance about critical equipment issues.',
                        position: 'left'
                    },
                    {
                        selector: '.ai-assistant',
                        title: 'AI Assistant',
                        description: 'Chat naturally with your data. Ask "Show me critical work orders" or "How is pump B performing?"',
                        position: 'left'
                    }
                ]
            },
            {
                id: 'drivers_dashboard',
                path: '/demo', // Staying on dashboard for this part
                steps: [
                    {
                        selector: '.realtime-monitor',
                        title: 'Real-time Operations',
                        description: 'Track fleet health, active work orders, and efficiency scores in real-time.',
                        position: 'right'
                    },
                    {
                        selector: '.demo-bar',
                        title: 'Next: Work Order Management',
                        description: 'Let\'s see how easy it is to manage tasks. Taking you to Work Orders...',
                        action: () => this.navigateToModule(1) // Index of work_orders
                    }
                ]
            },
            {
                id: 'work_orders',
                path: '/demo/work-orders',
                steps: [
                    {
                        selector: '.kanban-board',
                        title: 'Smart Kanban Board',
                        description: 'Visualize your workflow. Drag and drop cards to update status instantly.',
                        position: 'bottom'
                    },
                    {
                        selector: '.filter-bar',
                        title: 'Advanced Filtering',
                        description: 'Quickly find tasks by priority, technician, or asset.',
                        position: 'bottom'
                    },
                    {
                        selector: '.demo-bar',
                        title: 'Next: Asset Management',
                        description: 'See how we track equipment lifecycles. Moving to Assets...',
                        action: () => this.navigateToModule(3)
                    }
                ]
            },
            {
                id: 'assets',
                path: '/demo/assets',
                steps: [
                    {
                        selector: '.asset-grid', 
                        title: 'Asset Fleet View',
                        description: 'Complete visibility of all your machinery and equipment with health indicators.',
                        position: 'bottom'
                    },
                    {
                         selector: '.card:first-child', // Assuming first card exists
                         title: 'Asset Health Score',
                         description: 'Every asset gets a real-time health score based on sensor data and maintenance history.',
                         position: 'right'
                    },
                    {
                        selector: '.demo-bar',
                        title: 'Next: Analytics',
                        description: 'Let\'s dive into the numbers. Going to Analytics...',
                        action: () => this.navigateToModule(4)
                    }
                ]
            },
            {
                id: 'analytics',
                path: '/analytics/dashboard',
                steps: [
                    {
                        selector: '.analytics-header',
                        title: 'Deep Insights',
                        description: 'Visualize costs, downtime, and performance trends over time.',
                        position: 'bottom'
                    },
                    {
                        selector: '.chart-container:first-child',
                        title: 'Cost Analysis',
                        description: 'Identify your most expensive assets and optimize spending.',
                        position: 'right'
                    },
                     {
                        selector: '.demo-bar',
                        title: 'Next: Team Management',
                        description: 'Manage your workforce efficiently. Moving to Team...',
                        action: () => this.navigateToModule(5)
                    }
                ]
            },
            {
                id: 'team',
                path: '/demo/team',
                steps: [
                    {
                        selector: '.technician-grid',
                        title: 'Workforce Management',
                        description: 'Track technician availability, skills, and current workload.',
                        position: 'bottom'
                     },
                     {
                        selector: '.demo-bar',
                        title: 'Next: Purchasing',
                        description: 'Automate your inventory. Going to Purchasing...',
                        action: () => this.navigateToModule(6)
                     }
                ]
            },
             {
                id: 'purchasing',
                path: '/demo/purchasing',
                steps: [
                    {
                        selector: '.inventory-alert', // Might need to ensure this selector exists or use generic
                        title: 'Smart Reordering',
                        description: 'AI predicts part usage and suggests orders before you run out.',
                        position: 'bottom'
                     },
                     {
                        selector: '.demo-bar',
                        title: 'Demo Complete!',
                        description: 'You\'ve seen the power of ChatterFix. Ready to transform your operations?',
                        action: () => this.completeDemo()
                     }
                ]
            }
        ];

        // UI Elements
        this.overlay = this.createOverlay();
        this.spotlight = this.createSpotlight();
        this.tooltip = this.createTooltip();
        
        // Check for active demo state on load
        this.checkAutoStart();
    }

    createOverlay() {
        let el = document.querySelector('.demo-overlay');
        if (!el) {
            el = document.createElement('div');
            el.className = 'demo-overlay';
            el.style.cssText = 'display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9998; backdrop-filter:blur(3px);';
            document.body.appendChild(el);
        }
        return el;
    }

    createSpotlight() {
        let el = document.querySelector('.demo-spotlight');
        if (!el) {
            el = document.createElement('div');
            el.className = 'demo-spotlight';
            el.style.cssText = 'display:none; position:absolute; border:2px solid #3498db; box-shadow: 0 0 0 9999px rgba(0,0,0,0.8); z-index:9999; border-radius:8px; pointer-events:none; transition: all 0.5s ease;';
            document.body.appendChild(el);
        }
        return el;
    }

    createTooltip() {
        let el = document.querySelector('.demo-tooltip');
        if (!el) {
            el = document.createElement('div');
            el.className = 'demo-tooltip';
            el.style.cssText = 'display:none; position:absolute; background:var(--bg-glass-heavy, #fff); padding:1rem; border-radius:12px; border:1px solid rgba(255,255,255,0.2); box-shadow:0 10px 30px rgba(0,0,0,0.3); z-index:10000; width:300px; max-width:90vw; color: var(--text-primary, #333); backdrop-filter: blur(15px); transition: all 0.3s ease;';
            document.body.appendChild(el);
        }
        return el;
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
            // localStorage may be restricted (Safari private browsing)
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
            // localStorage may be restricted (Safari private browsing)
            console.log('Demo state storage not available');
        }
    }

    clearState() {
        try {
            localStorage.removeItem('chatterfix_demo_state');
        } catch (e) {
            // localStorage may be restricted (Safari private browsing)
        }
    }

    checkAutoStart() {
        this.loadState();
        if (this.isActive) {
            // Verify we are on the correct page for the current module
            const currentModule = this.modules[this.currentModuleIndex];
            
            if (window.location.pathname !== currentModule.path) {
                // Wrong page? Redirect.
                window.location.href = currentModule.path;
            } else {
                // Right page, show step
                // Slight delay to allow DOM to settle
                setTimeout(() => this.showStep(), 500);
            }
        }
    }

    startDemo() {
        // Find the demo bar and hide it
        const demoBar = document.getElementById('demoBar');
        if(demoBar) demoBar.style.display = 'none';

        this.isActive = true;
        this.currentModuleIndex = 0;
        this.currentStepIndex = 0;
        this.saveState();
        
        // Ensure we start at dashboard
        if (window.location.pathname !== '/demo') {
            window.location.href = '/demo';
        } else {
            this.showStep();
        }
    }

    stopDemo() {
        this.isActive = false;
        this.clearState();
        this.overlay.style.display = 'none';
        this.spotlight.style.display = 'none';
        this.tooltip.style.display = 'none';
        
        // Show demo bar again if applicable
        const demoBar = document.getElementById('demoBar');
        if(demoBar) demoBar.style.display = 'block';
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
        window.location.href = nextModule.path;
    }

    nextStep() {
        const currentModule = this.modules[this.currentModuleIndex];
        
        if (this.currentStepIndex < currentModule.steps.length - 1) {
            this.currentStepIndex++;
            this.saveState();
            this.showStep();
        } else {
            // End of module, check if there's an action or move to next module
            const currentStep = currentModule.steps[this.currentStepIndex];
            if (currentStep.action) {
                currentStep.action();
            } else {
                // Default behavior: move to next module
                this.navigateToModule(this.currentModuleIndex + 1);
            }
        }
    }

    previousStep() {
        if (this.currentStepIndex > 0) {
            this.currentStepIndex--;
            this.showStep();
        } else if (this.currentModuleIndex > 0) {
            // Go to end of previous module
            this.currentModuleIndex--;
            this.currentStepIndex = this.modules[this.currentModuleIndex].steps.length - 1;
            this.saveState();
            
            // Redirect if needed
             const prevModule = this.modules[this.currentModuleIndex];
             if (window.location.pathname !== prevModule.path) {
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
        
        // If step has an action but NOT as the transition (e.g. at start), run it? 
        // Our structure defines action usually as "Next..." logic. 
        // Let's assume actions are for transitions.
        // But for display, we need to highlight.

        let target = null;
        if (step.selector) {
            target = document.querySelector(step.selector);
        }
        
        // Fallback if target not found (e.g. dynamic content not loaded)
        // Try again in a moment, or show generic center modal
        if (!target && step.selector) {
            console.warn(`Demo target ${step.selector} not found. Retrying in 500ms...`);
            setTimeout(() => {
                target = document.querySelector(step.selector);
                if (target) this.renderHighlight(target, step);
                else this.renderModal(step); // Fallback to modal
            }, 500);
            return;
        }

        if (target) {
            this.renderHighlight(target, step);
        } else {
            this.renderModal(step);
        }
    }

    renderHighlight(element, step) {
        const rect = element.getBoundingClientRect();
        const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
        const scrollY = window.pageYOffset || document.documentElement.scrollTop;
        
        // Scroll into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Update spotlight
        this.overlay.style.display = 'block';
        this.spotlight.style.display = 'block';
        this.spotlight.style.width = (rect.width + 20) + 'px';
        this.spotlight.style.height = (rect.height + 20) + 'px';
        this.spotlight.style.left = (rect.left + scrollX - 10) + 'px';
        this.spotlight.style.top = (rect.top + scrollY - 10) + 'px';

        // Update Tooltip
        this.tooltip.style.display = 'block';
        let top = rect.bottom + scrollY + 20;
        let left = rect.left + scrollX;
        
        // Simple position logic correction
        if (top + 200 > document.documentElement.scrollHeight) {
            top = rect.top + scrollY - 220; // Flip to top
        }
        
        // Constrain left
        if (left + 300 > document.documentElement.clientWidth) {
            left = document.documentElement.clientWidth - 320;
        }

        this.tooltip.style.top = top + 'px';
        this.tooltip.style.left = left + 'px';
        
        this.renderTooltipContent(step);
    }
    
    renderModal(step) {
        // Fallback when no element to highlight - just center the tooltip
        this.overlay.style.display = 'block';
        this.spotlight.style.display = 'none'; // No spotlight
        
        this.tooltip.style.display = 'block';
        this.tooltip.style.top = '50%';
        this.tooltip.style.left = '50%';
        this.tooltip.style.transform = 'translate(-50%, -50%)';
        
        this.renderTooltipContent(step);
    }

    renderTooltipContent(step) {
        const totalModules = this.modules.length;
        // Global progress approx
        const progress = Math.round(((this.currentModuleIndex + 1) / totalModules) * 100);

        this.tooltip.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <h3 style="margin:0; font-size:1.1rem; font-weight:700;">${step.title}</h3>
                <span style="font-size:0.8rem; background:var(--accent-color, #3498db); color:white; padding:2px 8px; border-radius:10px;">${progress}%</span>
            </div>
            <p style="font-size:0.95rem; line-height:1.5; margin-bottom:20px; color:inherit;">${step.description}</p>
            <div style="display:flex; justify-content:space-between; gap:10px;">
                <button onclick="window.demoSystem.stopDemo()" class="cmms-btn-secondary" style="background:transparent; border:1px solid currentColor; padding:5px 10px; border-radius:5px; cursor:pointer; color:inherit; font-size:0.8rem;">Exit</button>
                <div style="display:flex; gap:5px;">
                     <button onclick="window.demoSystem.previousStep()" style="padding:5px 15px; border-radius:5px; cursor:pointer; border:1px solid currentColor; background:transparent; color:inherit; font-size:0.8rem;" ${this.currentModuleIndex === 0 && this.currentStepIndex === 0 ? 'disabled' : ''}>Back</button>
                    <button onclick="window.demoSystem.nextStep()" class="cmms-btn" style="padding:5px 20px; border-radius:5px; cursor:pointer; border:none; background:var(--accent-gradient, #3498db); color:white; font-size:0.8rem;">Next</button>
                </div>
            </div>
        `;
    }

    completeDemo() {
        this.stopDemo();
        // Show celebration modal
        const modal = document.createElement('div');
        modal.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:10001; display:flex; align-items:center; justify-content:center; backdrop-filter:blur(5px);';
        modal.innerHTML = `
            <div style="background:var(--bg-glass-heavy, #fff); padding:40px; border-radius:20px; text-align:center; max-width:500px; border:var(--card-border); color:var(--text-primary);">
                <div style="font-size:3rem; margin-bottom:20px;">🎉</div>
                <h2 style="margin-bottom:15px;">Demo Completed!</h2>
                <p style="margin-bottom:30px;">You've mastered the basics of ChatterFix. You're ready to revolutionize your maintenance operations.</p>
                <button onclick="window.location.href='/landing'" class="cmms-btn" style="padding:15px 30px; font-size:1.1rem; width:100%;">Get Started / Sign Up</button>
                <br><br>
                <button onclick="this.closest('div').parentElement.remove()" style="background:none; border:none; color:var(--text-secondary); cursor:pointer; text-decoration:underline;">Close</button>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// Global instance
window.demoSystem = new ChatterFixDemoSystem();
