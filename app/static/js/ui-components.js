/**
 * 🎨 CHATTERFIX CMMS - ENHANCED UI COMPONENTS LIBRARY
 *
 * This file contains Alpine.js components, GSAP animations, and modern UI patterns
 * for creating compelling user experiences with integrated frontend-backend logic.
 */

// 🛡️ Safe Storage Utility (handles Safari private browsing restrictions)
const SafeStorage = {
    get(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(key);
            return value !== null ? value : defaultValue;
        } catch (e) {
            console.log('Storage access restricted');
            return defaultValue;
        }
    },
    set(key, value) {
        try {
            localStorage.setItem(key, value);
            return true;
        } catch (e) {
            console.log('Storage access restricted');
            return false;
        }
    },
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            return false;
        }
    },
    getJSON(key, defaultValue = {}) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch (e) {
            return defaultValue;
        }
    },
    setJSON(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            return false;
        }
    }
};

// 🚀 Alpine.js Global Data Store
document.addEventListener('alpine:init', () => {

    // ========================================
    // 🎯 Alpine.data() COMPONENT REGISTRATIONS
    // These allow x-data="componentName" usage in templates
    // ========================================

    // User Preferences Component (wraps store)
    Alpine.data('userPreferences', () => ({
        get animationsEnabled() { return Alpine.store('userPreferences')?.animationsEnabled ?? true; },
        set animationsEnabled(val) { if (Alpine.store('userPreferences')) Alpine.store('userPreferences').animationsEnabled = val; },
        showSettings: false,
        toggleAnimations() {
            const store = Alpine.store('userPreferences');
            if (store) store.toggleAnimations();
        },
        init() {
            console.log('✅ userPreferences component initialized');
        }
    }));

    // AI System Component (wraps store)
    Alpine.data('aiSystem', () => ({
        get learningMode() { return Alpine.store('aiSystem')?.learningMode ?? false; },
        set learningMode(val) { if (Alpine.store('aiSystem')) Alpine.store('aiSystem').learningMode = val; },
        get analyzing() { return Alpine.store('aiSystem')?.analyzing ?? false; },
        get predicting() { return Alpine.store('aiSystem')?.predicting ?? false; },
        get optimizing() { return Alpine.store('aiSystem')?.optimizing ?? false; },
        get reporting() { return Alpine.store('aiSystem')?.reporting ?? false; },
        get lastOptimization() { return Alpine.store('aiSystem')?.lastOptimization ?? null; },
        get systemDescription() { return Alpine.store('aiSystem')?.systemDescription ?? 'AI System Ready'; },
        get metrics() { return Alpine.store('aiSystem')?.metrics ?? { processed: 0, accuracy: 0, suggestions: 0, efficiency: 0 }; },
        get recentActivities() { return Alpine.store('aiSystem')?.recentActivities ?? []; },
        toggleLearningMode() {
            const store = Alpine.store('aiSystem');
            if (store) store.toggleLearningMode();
        },
        runFleetAnalysis() {
            const store = Alpine.store('aiSystem');
            if (store) store.runFleetAnalysis();
        },
        generatePredictiveInsights() {
            const store = Alpine.store('aiSystem');
            if (store) store.generatePredictiveInsights();
        },
        optimizeOperations() {
            const store = Alpine.store('aiSystem');
            if (store) store.optimizeOperations();
        },
        generateAIReport() {
            const store = Alpine.store('aiSystem');
            if (store) store.generateAIReport();
        },
        init() {
            console.log('✅ aiSystem component initialized');
        }
    }));

    // Predictive Analytics Component (NEW)
    Alpine.data('predictiveAnalytics', () => ({
        filterBy: 'all',
        generating: false,
        lastUpdated: new Date().toLocaleTimeString(),
        selectedPrediction: null,
        predictions: [
            { id: 1, equipment: 'HVAC Unit #3', issue: 'bearing failure', risk: 87, priority: 'critical', icon: '🔴', timeframe: '3 days', recommendation: 'Schedule immediate bearing inspection' },
            { id: 2, equipment: 'Conveyor Belt A', issue: 'motor overheating', risk: 72, priority: 'high', icon: '🟠', timeframe: '7 days', recommendation: 'Check motor cooling system' },
            { id: 3, equipment: 'Pump Station B', issue: 'seal degradation', risk: 65, priority: 'high', icon: '🟠', timeframe: '10 days', recommendation: 'Order replacement seals' },
            { id: 4, equipment: 'Generator #1', issue: 'fuel filter clog', risk: 45, priority: 'low', icon: '🟢', timeframe: '14 days', recommendation: 'Schedule routine filter replacement' }
        ],
        get filteredPredictions() {
            if (this.filterBy === 'all') return this.predictions;
            return this.predictions.filter(p => p.priority === this.filterBy);
        },
        get criticalCount() {
            return this.predictions.filter(p => p.priority === 'critical').length;
        },
        selectPrediction(prediction) {
            this.selectedPrediction = prediction;
            console.log('Selected prediction:', prediction);
        },
        async createWorkOrder(prediction) {
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification(`Creating work order for ${prediction.equipment}...`, 'info');
            }
            // Simulate work order creation
            await new Promise(resolve => setTimeout(resolve, 1000));
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification(`Work order created for ${prediction.equipment}!`, 'success');
            }
        },
        async generateNewPredictions() {
            this.generating = true;
            await new Promise(resolve => setTimeout(resolve, 2500));
            // Add a new random prediction
            const newPrediction = {
                id: Date.now(),
                equipment: `Equipment ${Math.floor(Math.random() * 100)}`,
                issue: 'anomaly detected',
                risk: Math.floor(Math.random() * 40) + 60,
                priority: Math.random() > 0.5 ? 'high' : 'critical',
                icon: Math.random() > 0.5 ? '🟠' : '🔴',
                timeframe: `${Math.floor(Math.random() * 10) + 2} days`,
                recommendation: 'AI-generated recommendation pending review'
            };
            this.predictions.unshift(newPrediction);
            this.lastUpdated = new Date().toLocaleTimeString();
            this.generating = false;
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification('New predictions generated!', 'success');
            }
        },
        refreshPredictions() {
            this.lastUpdated = new Date().toLocaleTimeString();
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification('Predictions refreshed!', 'info');
            }
        },
        init() {
            console.log('✅ predictiveAnalytics component initialized');
        }
    }));

    // Operations Monitor Component (wraps store)
    Alpine.data('operationsMonitor', () => ({
        refreshing: false,
        autoRefresh: true,
        showActivityFeed: false,
        highlightedMetric: null,
        suggestionsIncrement: 5,
        get liveMetrics() {
            return Alpine.store('operationsMonitor')?.liveMetrics ?? { fleetHealth: 94.7, activeWorkOrders: 12, aiSuggestions: 47, efficiency: 89 };
        },
        get achievements() {
            return Alpine.store('operationsMonitor')?.achievements ?? [
                { id: 1, text: 'Prevented HVAC failure - saved $12,400', impact: '+$12.4K', positive: true },
                { id: 2, text: 'Optimized technician routes - 23% faster', impact: '+23%', positive: true },
                { id: 3, text: 'Auto-ordered 5 critical parts', impact: '5 parts', positive: true }
            ];
        },
        get recentActivity() {
            return Alpine.store('operationsMonitor')?.recentActivity ?? [
                { time: '14:32', message: 'Work order #1234 completed', timestamp: Date.now() },
                { time: '14:28', message: 'New prediction generated', timestamp: Date.now() }
            ];
        },
        getMetricStyle(metric) {
            if (this.highlightedMetric === metric) {
                return 'color: var(--accent-color); transform: scale(1.1);';
            }
            return '';
        },
        getHealthStatus(health) {
            if (health >= 90) return 'Excellent';
            if (health >= 75) return 'Good';
            if (health >= 50) return 'Fair';
            return 'Needs Attention';
        },
        getWorkOrderStatus() {
            const wo = this.liveMetrics.activeWorkOrders;
            if (wo <= 5) return 'Light workload';
            if (wo <= 15) return 'Normal workload';
            return 'Heavy workload';
        },
        getEfficiencyTrend() {
            return this.liveMetrics.efficiency >= 85 ? '↑ Trending up' : '→ Stable';
        },
        highlightMetric(metric) {
            this.highlightedMetric = metric;
        },
        clearHighlight() {
            this.highlightedMetric = null;
        },
        drillDown(metric) {
            console.log('Drilling down into:', metric);
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification(`Opening ${metric} details...`, 'info');
            }
        },
        async refreshMetrics() {
            this.refreshing = true;
            const store = Alpine.store('operationsMonitor');
            if (store && store.refreshMetrics) {
                await store.refreshMetrics();
            } else {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            this.refreshing = false;
        },
        toggleAutoRefresh() {
            this.autoRefresh = !this.autoRefresh;
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification(`Auto-refresh ${this.autoRefresh ? 'enabled' : 'disabled'}`, 'info');
            }
        },
        exportMetrics() {
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification('Exporting metrics to CSV...', 'info');
            }
        },
        setAlerts() {
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification('Alert configuration coming soon!', 'info');
            }
        },
        viewDetailedReport() {
            if (typeof ModernComponents !== 'undefined') {
                ModernComponents.showNotification('Opening detailed report...', 'info');
            }
        },
        init() {
            console.log('✅ operationsMonitor component initialized');
        }
    }));

    // ========================================
    // 🎛️ User Preferences Store
    Alpine.store('userPreferences', {
        // Visual Effects Settings
        animationsEnabled: SafeStorage.get('animationsEnabled') !== 'false', // Default to true
        showSettings: false, // Settings panel visibility

        toggleAnimations() {
            this.animationsEnabled = !this.animationsEnabled;
            SafeStorage.set('animationsEnabled', this.animationsEnabled);

            // Apply setting to GSAP
            if (this.animationsEnabled) {
                gsap.globalTimeline.timeScale(1);
            } else {
                gsap.globalTimeline.timeScale(0.01); // Nearly instant animations
            }

            ModernComponents.showNotification(
                `Animations ${this.animationsEnabled ? 'enabled' : 'disabled'}`,
                'info',
                2000
            );
        },

        init() {
            // Apply animation settings
            if (!this.animationsEnabled) {
                gsap.globalTimeline.timeScale(0.01);
            }

            console.log('✅ User preferences initialized');
        }
    });
    
    // 📊 Dashboard Reactive Data
    Alpine.store('dashboard', {
        metrics: {
            efficiency: 89,
            workOrders: 12,
            fleetHealth: 94.7,
            aiSuggestions: 47
        },
        
        async updateMetrics() {
            try {
                const response = await fetch('/quick-stats');

                // Check if response is OK before parsing
                if (!response.ok) {
                    console.log('📊 Quick stats not available (requires auth)');
                    return; // Silently fail - use default metrics
                }

                const data = await response.json();

                // Animate metric changes with GSAP
                if (data.workload?.active !== undefined) {
                    gsap.to(this.metrics, {
                        workOrders: data.workload.active,
                        duration: 1,
                        ease: "power2.out"
                    });
                }

                if (data.performance?.completion_rate !== undefined) {
                    gsap.to(this.metrics, {
                        efficiency: Math.round(data.performance.completion_rate),
                        duration: 1,
                        ease: "power2.out"
                    });
                }

                console.log('✅ Metrics updated with animation');
            } catch (error) {
                // Silently handle errors - use default metrics
                console.log('📊 Using default metrics');
            }
        }
    });
    
    // 🤖 AI System Store - Fully Interactive
    Alpine.store('aiSystem', {
        // System Status
        learningMode: true,
        analyzing: false,
        predicting: false,
        optimizing: false,
        reporting: false,
        lastOptimization: null,
        autoOptimization: true,
        
        // System Description
        systemDescription: 'Orchestrating intelligent maintenance operations across your entire facility',
        
        // Real-time Metrics
        metrics: {
            processed: 247,
            accuracy: 94.7,
            suggestions: 23,
            efficiency: 89.2
        },
        
        // Live Activity Feed
        recentActivities: [
            { id: 1, timestamp: '14:32', message: 'Fleet analysis completed for Building A' },
            { id: 2, timestamp: '14:28', message: 'Predictive maintenance alert: HVAC Unit #3' },
            { id: 3, timestamp: '14:25', message: 'Optimization reduced energy usage by 12%' },
            { id: 4, timestamp: '14:20', message: 'New work order auto-generated for Pump #7' }
        ],
        
        // Interactive Functions
        toggleLearningMode() {
            this.learningMode = !this.learningMode;
            this.addActivity(
                this.learningMode ? 'Learning mode activated' : 'Learning mode deactivated'
            );
            
            // Update metrics based on learning mode
            if (this.learningMode) {
                this.metrics.accuracy = Math.min(99.9, this.metrics.accuracy + 2);
                this.systemDescription = 'AI actively learning and adapting to optimize maintenance operations';
            } else {
                this.systemDescription = 'AI operating in standard mode with existing knowledge base';
            }
            
            ModernComponents.showNotification(
                `Learning mode ${this.learningMode ? 'activated' : 'deactivated'}`,
                'info'
            );
        },
        
        async runFleetAnalysis() {
            this.analyzing = true;
            this.addActivity('Fleet analysis initiated...');
            
            try {
                // Simulate API call
                await this.simulateAPICall(3000);
                
                // Update metrics
                this.metrics.processed += Math.floor(Math.random() * 10) + 5;
                this.metrics.suggestions += Math.floor(Math.random() * 3) + 1;
                
                this.addActivity('Fleet analysis complete: Found 3 optimization opportunities');
                
                ModernComponents.showNotification(
                    '🔍 Fleet analysis completed! Found 3 optimization opportunities.',
                    'success'
                );
                
                // Animate the metrics
                this.animateMetricUpdate('processed');
                
            } catch (error) {
                this.addActivity('Fleet analysis failed: ' + error.message);
                ModernComponents.showNotification('Fleet analysis failed. Please try again.', 'error');
            } finally {
                this.analyzing = false;
            }
        },
        
        async generatePredictiveInsights() {
            this.predicting = true;
            this.addActivity('Generating predictive insights...');
            
            try {
                await this.simulateAPICall(2500);
                
                // Update suggestions
                this.metrics.suggestions += Math.floor(Math.random() * 5) + 2;
                this.metrics.accuracy = Math.min(99.9, this.metrics.accuracy + 0.3);
                
                this.addActivity('Predictive insights ready: 5 maintenance alerts generated');
                
                ModernComponents.showNotification(
                    '📊 Predictive insights generated! 5 new maintenance alerts created.',
                    'success'
                );
                
                this.animateMetricUpdate('suggestions');
                
            } catch (error) {
                this.addActivity('Predictive insights failed: ' + error.message);
                ModernComponents.showNotification('Failed to generate insights. Please try again.', 'error');
            } finally {
                this.predicting = false;
            }
        },
        
        async optimizeOperations() {
            this.optimizing = true;
            this.lastOptimization = 'running';
            this.addActivity('Operations optimization in progress...');
            
            try {
                await this.simulateAPICall(4000);
                
                // Significant efficiency boost
                const improvement = Math.random() * 5 + 2; // 2-7% improvement
                this.metrics.efficiency = Math.min(99.9, this.metrics.efficiency + improvement);
                this.metrics.processed += Math.floor(Math.random() * 15) + 10;
                
                this.lastOptimization = 'success';
                this.addActivity(`Operations optimized: ${improvement.toFixed(1)}% efficiency increase`);
                
                ModernComponents.showNotification(
                    `⚡ Operations optimized! Efficiency increased by ${improvement.toFixed(1)}%`,
                    'success'
                );
                
                this.animateMetricUpdate('efficiency');
                
            } catch (error) {
                this.lastOptimization = 'failed';
                this.addActivity('Optimization failed: ' + error.message);
                ModernComponents.showNotification('Optimization failed. Please try again.', 'error');
            } finally {
                this.optimizing = false;
                setTimeout(() => { this.lastOptimization = null; }, 3000);
            }
        },
        
        async generateAIReport() {
            this.reporting = true;
            this.addActivity('Generating executive report...');
            
            try {
                await this.simulateAPICall(3500);
                
                this.metrics.processed += 1;
                this.addActivity('Executive report generated and sent to dashboard');
                
                // Create a downloadable report
                this.createDownloadableReport();
                
                ModernComponents.showNotification(
                    '📑 Executive report generated and ready for download!',
                    'success'
                );
                
            } catch (error) {
                this.addActivity('Report generation failed: ' + error.message);
                ModernComponents.showNotification('Report generation failed. Please try again.', 'error');
            } finally {
                this.reporting = false;
            }
        },
        
        // Utility Functions
        addActivity(message) {
            const now = new Date();
            const timestamp = now.getHours().toString().padStart(2, '0') + ':' + 
                            now.getMinutes().toString().padStart(2, '0');
            
            this.recentActivities.unshift({
                id: Date.now(),
                timestamp: timestamp,
                message: message
            });
            
            // Keep only last 10 activities
            if (this.recentActivities.length > 10) {
                this.recentActivities = this.recentActivities.slice(0, 10);
            }
        },
        
        async simulateAPICall(duration = 2000) {
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    // 95% success rate
                    if (Math.random() > 0.05) {
                        resolve();
                    } else {
                        reject(new Error('Network timeout'));
                    }
                }, duration);
            });
        },
        
        animateMetricUpdate(metricName) {
            // Find the metric element and animate it
            setTimeout(() => {
                const elements = document.querySelectorAll('[x-text*="metrics.' + metricName + '"]');
                elements.forEach(el => {
                    if (typeof UIAnimations !== 'undefined') {
                        gsap.fromTo(el, 
                            { scale: 1 },
                            { 
                                scale: 1.2, 
                                duration: 0.3,
                                ease: "power2.out",
                                yoyo: true,
                                repeat: 1
                            }
                        );
                    }
                });
            }, 100);
        },
        
        createDownloadableReport() {
            const reportData = {
                timestamp: new Date().toISOString(),
                metrics: this.metrics,
                recentActivities: this.recentActivities.slice(0, 5),
                systemStatus: {
                    learningMode: this.learningMode,
                    autoOptimization: this.autoOptimization
                }
            };
            
            const blob = new Blob([JSON.stringify(reportData, null, 2)], { 
                type: 'application/json' 
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chatterfix-ai-report-${new Date().toISOString().slice(0, 10)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }),
    
    // 🤖 AI Chat Store
    Alpine.store('aiChat', {
        isOpen: false,
        messages: [],
        isTyping: false,
        
        toggle() {
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                // Focus input after animation
                setTimeout(() => {
                    const input = document.getElementById('ai-chat-input');
                    if (input) input.focus();
                }, 300);
            }
        },
        
        async sendMessage(message) {
            if (!message.trim()) return;
            
            // Add user message
            this.messages.push({
                type: 'user',
                content: message,
                timestamp: new Date()
            });
            
            this.isTyping = true;
            
            try {
                const response = await fetch('/ai/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, context: '' })
                });
                
                const data = await response.json();
                
                // Add AI response
                this.messages.push({
                    type: 'ai',
                    content: data.response || 'I understand your request.',
                    timestamp: new Date()
                });
                
                // Sound notification
                this.playNotificationSound();
                
            } catch (error) {
                this.messages.push({
                    type: 'ai',
                    content: 'I\'m having trouble connecting. Please try again.',
                    timestamp: new Date()
                });
            } finally {
                this.isTyping = false;
            }
        },
        
        playNotificationSound() {
            // Create subtle notification sound with Web Audio API
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.exponentialRampToValueAtTime(600, audioContext.currentTime + 0.1);
                
                gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                gainNode.gain.linearRampToValueAtTime(0.05, audioContext.currentTime + 0.05);
                gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.2);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.2);
            } catch (e) {
                // Ignore audio errors
            }
        }
    });
    
    // 📋 Work Orders Store
    Alpine.store('workOrders', {
        items: [],
        loading: false,
        filter: 'all',
        
        async fetch() {
            this.loading = true;
            try {
                const response = await fetch('/api/work-orders');

                // Check if response is OK before parsing
                if (!response.ok) {
                    console.log('📋 Work orders API not available');
                    this.items = []; // Use empty array as fallback
                    return;
                }

                this.items = await response.json();

                // Animate list appearance
                gsap.fromTo('.work-order-item',
                    { opacity: 0, y: 20 },
                    { opacity: 1, y: 0, duration: 0.3, stagger: 0.1 }
                );
            } catch (error) {
                console.log('📋 Using default work orders data');
                this.items = []; // Use empty array as fallback
            } finally {
                this.loading = false;
            }
        },
        
        get filteredItems() {
            if (this.filter === 'all') return this.items;
            return this.items.filter(item => item.status === this.filter);
        }
    });
    
    // 📊 Analytics Store
    Alpine.store('analytics', {
        chartConfigs: {},
        
        createApexChart(elementId, config) {
            const chart = new ApexCharts(document.querySelector(elementId), config);
            chart.render();
            this.chartConfigs[elementId] = chart;
            return chart;
        },
        
        updateChart(elementId, newData) {
            const chart = this.chartConfigs[elementId];
            if (chart) {
                chart.updateSeries(newData);
            }
        }
    });
});

// 🎨 Enhanced GSAP Animation Utilities with ScrollTrigger and Advanced Effects
const UIAnimations = {

    // Check if GSAP is available
    isGsapAvailable() {
        return typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined';
    },

    // Initialize ScrollTrigger
    init() {
        if (!this.isGsapAvailable()) {
            console.warn('⚠️ GSAP not available, skipping animations');
            return;
        }
        gsap.registerPlugin(ScrollTrigger, TextPlugin);
        this.setupScrollAnimations();
        this.setupParallaxEffects();
        this.setupTextAnimations();
    },

    // Simple card hover effects (tilt/rotation removed)
    enhanceCards() {
        if (!this.isGsapAvailable()) return;
        gsap.utils.toArray('.cmms-card, .capability-card, .kpi-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                gsap.to(card, {
                    y: -4,
                    duration: 0.3,
                    ease: "power2.out",
                    boxShadow: "0 8px 16px rgba(0,0,0,0.15)"
                });
            });

            card.addEventListener('mouseleave', () => {
                gsap.to(card, {
                    y: 0,
                    duration: 0.3,
                    ease: "power2.out",
                    boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
                });
            });
        });
    },
    
    // Scroll-triggered animations
    setupScrollAnimations() {
        // Fade in elements as they scroll into view
        gsap.utils.toArray('.fade-in-scroll').forEach(element => {
            gsap.fromTo(element, 
                { opacity: 0, y: 50 },
                {
                    opacity: 1,
                    y: 0,
                    duration: 1,
                    ease: "power2.out",
                    scrollTrigger: {
                        trigger: element,
                        start: "top 80%",
                        end: "bottom 20%",
                        toggleActions: "play none none reverse"
                    }
                }
            );
        });
        
        // Slide in from left
        gsap.utils.toArray('.slide-in-left').forEach(element => {
            gsap.fromTo(element,
                { x: -100, opacity: 0 },
                {
                    x: 0,
                    opacity: 1,
                    duration: 1,
                    ease: "power3.out",
                    scrollTrigger: {
                        trigger: element,
                        start: "top 80%"
                    }
                }
            );
        });
        
        // Slide in from right
        gsap.utils.toArray('.slide-in-right').forEach(element => {
            gsap.fromTo(element,
                { x: 100, opacity: 0 },
                {
                    x: 0,
                    opacity: 1,
                    duration: 1,
                    ease: "power3.out",
                    scrollTrigger: {
                        trigger: element,
                        start: "top 80%"
                    }
                }
            );
        });
    },
    
    // Parallax scrolling effects
    setupParallaxEffects() {
        gsap.utils.toArray('.parallax-slow').forEach(element => {
            gsap.to(element, {
                yPercent: -50,
                ease: "none",
                scrollTrigger: {
                    trigger: element,
                    start: "top bottom",
                    end: "bottom top",
                    scrub: true
                }
            });
        });
        
        gsap.utils.toArray('.parallax-fast').forEach(element => {
            gsap.to(element, {
                yPercent: -100,
                ease: "none",
                scrollTrigger: {
                    trigger: element,
                    start: "top bottom",
                    end: "bottom top",
                    scrub: true
                }
            });
        });
    },
    
    // Text animation effects
    setupTextAnimations() {
        gsap.utils.toArray('.typewriter').forEach(element => {
            const text = element.textContent;
            element.textContent = "";
            
            gsap.to(element, {
                text: text,
                duration: text.length * 0.1,
                ease: "none",
                scrollTrigger: {
                    trigger: element,
                    start: "top 80%"
                }
            });
        });
        
        // Split text animations
        gsap.utils.toArray('.split-text').forEach(element => {
            const text = new SplitText(element, {type: "chars,words"});
            
            gsap.fromTo(text.chars, 
                { opacity: 0, y: 20 },
                {
                    opacity: 1,
                    y: 0,
                    duration: 0.1,
                    stagger: 0.02,
                    ease: "power2.out",
                    scrollTrigger: {
                        trigger: element,
                        start: "top 80%"
                    }
                }
            );
        });
    },
    
    // Enhanced page transitions
    pageEnter() {
        const tl = gsap.timeline();
        
        // Main content animation
        tl.fromTo('.dashboard-grid > *', 
            { opacity: 0, y: 30, scale: 0.95 },
            { 
                opacity: 1, 
                y: 0, 
                scale: 1,
                duration: 0.8, 
                stagger: 0.1, 
                ease: "power3.out" 
            }
        )
        // Navigation animation
        .fromTo('.nav-tabs .nav-tab',
            { opacity: 0, x: -20 },
            { opacity: 1, x: 0, duration: 0.6, stagger: 0.03 },
            "-=0.5"
        )
        // Header animation
        .fromTo('.nav-header',
            { opacity: 0, y: -20 },
            { opacity: 1, y: 0, duration: 0.6 },
            "-=0.8"
        );
        
        return tl;
    },
    
    // Page exit transition
    pageExit() {
        const tl = gsap.timeline();
        
        tl.to('.dashboard-grid > *', {
            opacity: 0,
            y: -20,
            scale: 0.95,
            duration: 0.4,
            stagger: 0.05,
            ease: "power2.in"
        });
        
        return tl;
    },
    
    // Enhanced metric counter animations with formatting
    animateMetric(element, newValue, options = {}) {
        const { 
            duration = 1.5,
            prefix = '',
            suffix = '',
            decimals = 0,
            ease = "power2.out"
        } = options;
        
        const obj = { value: parseFloat(element.textContent.replace(/[^0-9.-]+/g, '')) || 0 };
        
        gsap.to(obj, {
            value: newValue,
            duration,
            ease,
            onUpdate: function() {
                const formattedValue = obj.value.toFixed(decimals);
                element.textContent = `${prefix}${formattedValue}${suffix}`;
            },
            onComplete: function() {
                // Add pulse effect on completion
                gsap.fromTo(element, 
                    { scale: 1 },
                    { 
                        scale: 1.1, 
                        duration: 0.2,
                        ease: "power2.out",
                        yoyo: true,
                        repeat: 1
                    }
                );
            }
        });
    },
    
    // Morphing loader animations
    showLoader(element, type = 'spinner') {
        let loader;
        
        switch(type) {
            case 'dots':
                loader = document.createElement('div');
                loader.className = 'flex space-x-1 justify-center items-center';
                loader.innerHTML = `
                    <div class="dot w-2 h-2 bg-accent rounded-full"></div>
                    <div class="dot w-2 h-2 bg-accent rounded-full"></div>
                    <div class="dot w-2 h-2 bg-accent rounded-full"></div>
                `;
                
                // Animate dots
                gsap.to(loader.querySelectorAll('.dot'), {
                    y: -10,
                    duration: 0.6,
                    ease: "power2.inOut",
                    stagger: 0.1,
                    repeat: -1,
                    yoyo: true
                });
                break;
                
            case 'pulse':
                loader = document.createElement('div');
                loader.className = 'w-8 h-8 bg-accent rounded-full';
                
                gsap.to(loader, {
                    scale: 1.2,
                    opacity: 0.7,
                    duration: 1,
                    ease: "power2.inOut",
                    repeat: -1,
                    yoyo: true
                });
                break;
                
            default: // spinner
                loader = document.createElement('div');
                loader.className = 'inline-flex items-center space-x-2';
                loader.innerHTML = `
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-accent"></div>
                    <span class="text-sm text-gray-600">Loading...</span>
                `;
        }
        
        // Fade in loader
        gsap.fromTo(loader, 
            { opacity: 0, scale: 0.8 },
            { opacity: 1, scale: 1, duration: 0.3 }
        );
        
        element.appendChild(loader);
        return loader;
    },
    
    hideLoader(loader) {
        gsap.to(loader, {
            opacity: 0,
            scale: 0.8,
            duration: 0.3,
            onComplete: () => loader.remove()
        });
    },
    
    // Morphing button states
    morphButton(button, newState) {
        const tl = gsap.timeline();
        
        tl.to(button, {
            scale: 0.95,
            duration: 0.1,
            ease: "power2.in"
        })
        .call(() => {
            // Change button content/state
            if (newState.text) button.textContent = newState.text;
            if (newState.icon) {
                const icon = button.querySelector('i');
                if (icon) {
                    icon.className = newState.icon;
                }
            }
            if (newState.class) {
                button.className = newState.class;
            }
        })
        .to(button, {
            scale: 1,
            duration: 0.2,
            ease: "power2.out"
        });
        
        return tl;
    },
    
    // Stagger reveal animation for lists/grids
    staggerReveal(selector, options = {}) {
        const {
            stagger = 0.1,
            from = 'bottom',
            duration = 0.6
        } = options;
        
        const elements = gsap.utils.toArray(selector);
        
        let fromVars, toVars;
        
        switch(from) {
            case 'left':
                fromVars = { x: -50, opacity: 0 };
                toVars = { x: 0, opacity: 1 };
                break;
            case 'right':
                fromVars = { x: 50, opacity: 0 };
                toVars = { x: 0, opacity: 1 };
                break;
            case 'top':
                fromVars = { y: -50, opacity: 0 };
                toVars = { y: 0, opacity: 1 };
                break;
            default: // bottom
                fromVars = { y: 50, opacity: 0 };
                toVars = { y: 0, opacity: 1 };
        }
        
        gsap.fromTo(elements, fromVars, {
            ...toVars,
            duration,
            stagger,
            ease: "power3.out"
        });
    }
};

// 📱 Enhanced Modern UI Components with Headless UI Integration
const ModernComponents = {
    
    // Initialize all form components
    init() {
        this.initializeDatePickers();
        this.initializeSelectComponents();
        this.initializeFormValidation();
        this.setupAutoComplete();
    },
    
    // Enhanced date/time pickers with Flatpickr
    initializeDatePickers() {
        // Standard date picker
        document.querySelectorAll('.date-picker').forEach(input => {
            flatpickr(input, {
                theme: document.documentElement.classList.contains('dark-mode') ? 'dark' : 'light',
                dateFormat: "Y-m-d",
                allowInput: true,
                clickOpens: true,
                animate: true
            });
        });
        
        // Date range picker
        document.querySelectorAll('.date-range-picker').forEach(input => {
            flatpickr(input, {
                mode: "range",
                theme: document.documentElement.classList.contains('dark-mode') ? 'dark' : 'light',
                dateFormat: "Y-m-d",
                allowInput: true,
                animate: true
            });
        });
        
        // Date and time picker
        document.querySelectorAll('.datetime-picker').forEach(input => {
            flatpickr(input, {
                enableTime: true,
                theme: document.documentElement.classList.contains('dark-mode') ? 'dark' : 'light',
                dateFormat: "Y-m-d H:i",
                allowInput: true,
                animate: true,
                time_24hr: false
            });
        });
    },
    
    // Enhanced select components with Choices.js
    initializeSelectComponents() {
        document.querySelectorAll('.enhanced-select').forEach(select => {
            new Choices(select, {
                searchEnabled: true,
                removeItemButton: true,
                classNames: {
                    containerOuter: 'choices glass-effect',
                    containerInner: 'choices__inner glass-input',
                    input: 'choices__input glass-input-field',
                    inputCloned: 'choices__input--cloned glass-input-field',
                    list: 'choices__list',
                    listItems: 'choices__list--multiple',
                    listSingle: 'choices__list--single',
                    listDropdown: 'choices__list--dropdown glass-dropdown',
                    item: 'choices__item glass-item',
                    itemSelectable: 'choices__item--selectable',
                    itemDisabled: 'choices__item--disabled',
                    itemChoice: 'choices__item--choice',
                    placeholder: 'choices__placeholder',
                    group: 'choices__group',
                    groupHeading: 'choices__heading',
                    button: 'choices__button',
                },
                callbackOnInit: function() {
                    // Apply glassmorphism styling after initialization
                    const container = this.containerOuter;
                    container.style.background = 'var(--bg-glass)';
                    container.style.backdropFilter = 'blur(10px)';
                    container.style.border = 'var(--border-glass)';
                }
            });
        });
        
        // Multi-select with tags
        document.querySelectorAll('.tag-select').forEach(select => {
            new Choices(select, {
                removeItemButton: true,
                maxItemCount: -1,
                searchResultLimit: 20,
                renderChoiceLimit: -1,
                placeholder: true,
                placeholderValue: 'Select or add tags...',
                addItems: true,
                addItemFilter: null,
                duplicateItemsAllowed: false,
                delimiter: ',',
                paste: true,
                searchFields: ['label', 'value'],
                callbackOnCreateTemplates: function() {
                    return {
                        item: ({ classNames }, data) => {
                            return `
                                <div class="${classNames.item} ${data.highlighted ? classNames.itemHighlight : classNames.itemSelectable}" data-item data-id="${data.id}" data-value="${data.value}" ${data.active ? 'aria-selected="true"' : ''} ${data.disabled ? 'aria-disabled="true"' : ''}>
                                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-accent/20 text-accent border border-accent/30">
                                        ${data.label}
                                        <button type="button" class="${classNames.button} ml-2" aria-label="Remove item" data-button="">
                                            <i class="fas fa-times text-xs"></i>
                                        </button>
                                    </span>
                                </div>
                            `;
                        }
                    };
                }
            });
        });
    },
    
    // Form validation with real-time feedback
    initializeFormValidation() {
        document.querySelectorAll('.validate-form').forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                input.addEventListener('blur', () => this.validateField(input));
                input.addEventListener('input', () => this.clearFieldError(input));
            });
            
            form.addEventListener('submit', (e) => {
                let isValid = true;
                inputs.forEach(input => {
                    if (!this.validateField(input)) {
                        isValid = false;
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    this.showNotification('Please fix the highlighted errors', 'error');
                }
            });
        });
    },
    
    validateField(field) {
        const value = field.value.trim();
        const rules = field.dataset.validate ? field.dataset.validate.split('|') : [];
        let isValid = true;
        
        // Clear previous errors
        this.clearFieldError(field);
        
        // Required validation
        if (rules.includes('required') && !value) {
            this.showFieldError(field, 'This field is required');
            isValid = false;
        }
        
        // Email validation
        if (rules.includes('email') && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            this.showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        }
        
        // Min length validation
        const minLength = rules.find(rule => rule.startsWith('min:'));
        if (minLength && value.length < parseInt(minLength.split(':')[1])) {
            this.showFieldError(field, `Minimum ${minLength.split(':')[1]} characters required`);
            isValid = false;
        }
        
        // Custom validation patterns
        const pattern = field.dataset.pattern;
        if (pattern && value && !new RegExp(pattern).test(value)) {
            this.showFieldError(field, field.dataset.patternMessage || 'Invalid format');
            isValid = false;
        }
        
        return isValid;
    },
    
    showFieldError(field, message) {
        field.classList.add('border-red-500', 'border-2');
        field.classList.remove('border-gray-300');
        
        let errorDiv = field.parentNode.querySelector('.field-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-red-500 text-sm mt-1 flex items-center';
            field.parentNode.appendChild(errorDiv);
        }
        
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle mr-1"></i>
            ${message}
        `;
        
        // Animate error appearance
        gsap.fromTo(errorDiv, 
            { opacity: 0, y: -10 },
            { opacity: 1, y: 0, duration: 0.3 }
        );
    },
    
    clearFieldError(field) {
        field.classList.remove('border-red-500', 'border-2');
        field.classList.add('border-gray-300');
        
        const errorDiv = field.parentNode.querySelector('.field-error');
        if (errorDiv) {
            gsap.to(errorDiv, {
                opacity: 0,
                y: -10,
                duration: 0.3,
                onComplete: () => errorDiv.remove()
            });
        }
    },
    
    // Auto-complete component
    setupAutoComplete() {
        document.querySelectorAll('.autocomplete').forEach(input => {
            let currentFocus = -1;
            let suggestions = JSON.parse(input.dataset.suggestions || '[]');
            
            input.addEventListener('input', function() {
                const val = this.value;
                closeAllLists();
                
                if (!val) return false;
                
                currentFocus = -1;
                
                const listContainer = document.createElement('div');
                listContainer.className = 'autocomplete-items glass-dropdown absolute z-50 w-full mt-1 max-h-60 overflow-y-auto rounded-lg border border-white/20 backdrop-blur-xl';
                listContainer.style.background = 'var(--bg-glass-heavy)';
                
                this.parentNode.appendChild(listContainer);
                
                suggestions.forEach((suggestion, index) => {
                    if (suggestion.toLowerCase().includes(val.toLowerCase())) {
                        const item = document.createElement('div');
                        item.className = 'autocomplete-item px-4 py-2 cursor-pointer hover:bg-accent/20 transition-colors';
                        
                        const matchIndex = suggestion.toLowerCase().indexOf(val.toLowerCase());
                        const beforeMatch = suggestion.substring(0, matchIndex);
                        const match = suggestion.substring(matchIndex, matchIndex + val.length);
                        const afterMatch = suggestion.substring(matchIndex + val.length);
                        
                        item.innerHTML = `${beforeMatch}<strong class="text-accent">${match}</strong>${afterMatch}`;
                        
                        item.addEventListener('click', function() {
                            input.value = suggestion;
                            closeAllLists();
                            input.dispatchEvent(new Event('autocomplete-select'));
                        });
                        
                        listContainer.appendChild(item);
                    }
                });
                
                // Animate dropdown appearance
                gsap.fromTo(listContainer,
                    { opacity: 0, y: -10 },
                    { opacity: 1, y: 0, duration: 0.3 }
                );
            });
            
            input.addEventListener('keydown', function(e) {
                const items = this.parentNode.querySelectorAll('.autocomplete-item');
                
                if (e.keyCode === 40) { // Down arrow
                    currentFocus++;
                    addActive(items);
                } else if (e.keyCode === 38) { // Up arrow
                    currentFocus--;
                    addActive(items);
                } else if (e.keyCode === 13) { // Enter
                    e.preventDefault();
                    if (currentFocus > -1 && items[currentFocus]) {
                        items[currentFocus].click();
                    }
                }
            });
            
            function addActive(items) {
                removeActive(items);
                if (currentFocus >= items.length) currentFocus = 0;
                if (currentFocus < 0) currentFocus = items.length - 1;
                if (items[currentFocus]) {
                    items[currentFocus].classList.add('bg-accent/30');
                }
            }
            
            function removeActive(items) {
                items.forEach(item => item.classList.remove('bg-accent/30'));
            }
            
            function closeAllLists() {
                document.querySelectorAll('.autocomplete-items').forEach(list => list.remove());
            }
            
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.autocomplete')) {
                    closeAllLists();
                }
            });
        });
    },
    
    // Enhanced notification system with animations
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `
            fixed top-4 right-4 z-50 max-w-sm
            backdrop-blur-xl bg-glass-light border border-white/20 
            rounded-2xl p-4 shadow-glass
            transform translate-x-full transition-transform duration-300
        `;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const colors = {
            success: 'border-green-400',
            error: 'border-red-400',
            warning: 'border-yellow-400',
            info: 'border-blue-400'
        };
        
        notification.classList.add(colors[type]);
        
        notification.innerHTML = `
            <div class="flex items-start space-x-3">
                <span class="text-2xl">${icons[type]}</span>
                <div class="flex-1">
                    <p class="text-white font-medium">${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        class="text-white/60 hover:text-white transition-colors">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in with GSAP
        gsap.fromTo(notification,
            { x: 400, opacity: 0 },
            { x: 0, opacity: 1, duration: 0.5, ease: "power3.out" }
        );
        
        // Auto remove with animation
        setTimeout(() => {
            gsap.to(notification, {
                x: 400,
                opacity: 0,
                duration: 0.3,
                ease: "power2.in",
                onComplete: () => notification.remove()
            });
        }, duration);
        
        return notification;
    },
    
    // Enhanced modal system with better Alpine.js integration
    createModal(content, options = {}) {
        const { size = 'md', backdrop = true, keyboard = true } = options;
        
        const sizeClasses = {
            sm: 'max-w-sm',
            md: 'max-w-md',
            lg: 'max-w-lg',
            xl: 'max-w-xl',
            '2xl': 'max-w-2xl'
        };
        
        return `
            <div x-data="{ open: false }" 
                 x-show="open" 
                 x-transition:enter="transition ease-out duration-300"
                 x-transition:enter-start="opacity-0"
                 x-transition:enter-end="opacity-100"
                 x-transition:leave="transition ease-in duration-200"
                 x-transition:leave-start="opacity-100"
                 x-transition:leave-end="opacity-0"
                 class="fixed inset-0 z-50 overflow-y-auto"
                 ${keyboard ? '@keydown.escape.window="open = false"' : ''}
                 @modal-open.window="open = true"
                 @modal-close.window="open = false">
                
                <div class="flex items-center justify-center min-h-screen px-4">
                    ${backdrop ? '<div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="open = false"></div>' : ''}
                    
                    <div class="relative bg-glass-light backdrop-blur-xl border border-white/20 
                               rounded-3xl shadow-glass ${sizeClasses[size]} w-full p-6
                               transform transition-all duration-300"
                         x-transition:enter="transition ease-out duration-300 delay-75"
                         x-transition:enter-start="opacity-0 scale-90"
                         x-transition:enter-end="opacity-100 scale-100"
                         x-transition:leave="transition ease-in duration-200"
                         x-transition:leave-start="opacity-100 scale-100"
                         x-transition:leave-end="opacity-0 scale-90">
                        
                        ${content}
                        
                        <button @click="open = false" 
                                class="absolute top-4 right-4 text-white/60 hover:text-white transition-colors">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    },
    
    // Advanced dropdown component
    createDropdown(trigger, items, options = {}) {
        const { position = 'bottom-left', animation = 'slide' } = options;
        
        return `
            <div x-data="{ open: false }" class="relative inline-block">
                <button @click="open = !open" 
                        @click.away="open = false"
                        class="dropdown-trigger ${trigger.class || ''}">
                    ${trigger.content}
                    <i class="fas fa-chevron-down ml-2 transition-transform duration-200" 
                       :class="open ? 'rotate-180' : ''"></i>
                </button>
                
                <div x-show="open"
                     x-transition:enter="transition ease-out duration-200"
                     x-transition:enter-start="opacity-0 ${animation === 'slide' ? 'translate-y-1' : 'scale-95'}"
                     x-transition:enter-end="opacity-100 ${animation === 'slide' ? 'translate-y-0' : 'scale-100'}"
                     x-transition:leave="transition ease-in duration-150"
                     x-transition:leave-start="opacity-100 ${animation === 'slide' ? 'translate-y-0' : 'scale-100'}"
                     x-transition:leave-end="opacity-0 ${animation === 'slide' ? 'translate-y-1' : 'scale-95'}"
                     class="absolute z-50 ${this.getPositionClasses(position)} mt-2 w-56 
                            rounded-lg shadow-lg bg-glass-heavy backdrop-blur-xl border border-white/20">
                    
                    <div class="py-1">
                        ${items.map(item => `
                            <a href="${item.href || '#'}" 
                               @click="${item.action || ''}"
                               class="flex items-center px-4 py-2 text-sm text-white hover:bg-accent/20 transition-colors">
                                ${item.icon ? `<i class="${item.icon} mr-3"></i>` : ''}
                                ${item.label}
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    },
    
    getPositionClasses(position) {
        const positions = {
            'top-left': 'bottom-full right-0',
            'top-right': 'bottom-full left-0',
            'bottom-left': 'top-full right-0',
            'bottom-right': 'top-full left-0'
        };
        return positions[position] || positions['bottom-left'];
    },
    
    // Toast notification queue
    toastQueue: [],
    showingToast: false,
    
    showToast(message, type = 'info', duration = 3000) {
        this.toastQueue.push({ message, type, duration });
        if (!this.showingToast) {
            this.processToastQueue();
        }
    },
    
    processToastQueue() {
        if (this.toastQueue.length === 0) {
            this.showingToast = false;
            return;
        }
        
        this.showingToast = true;
        const toast = this.toastQueue.shift();
        
        const notification = this.showNotification(toast.message, toast.type, toast.duration);
        
        setTimeout(() => {
            this.processToastQueue();
        }, toast.duration + 500);
    }
};

// 🔄 Real-time Data Integration
class RealTimeUpdates {
    constructor() {
        this.intervals = new Map();
        this.init();
    }
    
    init() {
        // Update dashboard metrics every 30 seconds
        this.startInterval('dashboard-metrics', () => {
            Alpine.store('dashboard').updateMetrics();
        }, 30000);
        
        // Update work orders every 60 seconds
        this.startInterval('work-orders', () => {
            Alpine.store('workOrders').fetch();
        }, 60000);
    }
    
    startInterval(key, callback, interval) {
        if (this.intervals.has(key)) {
            clearInterval(this.intervals.get(key));
        }
        
        const id = setInterval(callback, interval);
        this.intervals.set(key, id);
    }
    
    stopInterval(key) {
        if (this.intervals.has(key)) {
            clearInterval(this.intervals.get(key));
            this.intervals.delete(key);
        }
    }
    
    destroy() {
        this.intervals.forEach(id => clearInterval(id));
        this.intervals.clear();
    }
}

// 📊 Advanced Chart Configurations
const ChartConfigs = {
    
    // Modern efficiency chart with ApexCharts
    efficiencyChart: {
        chart: {
            type: 'area',
            height: 300,
            toolbar: { show: false },
            background: 'transparent',
            animations: { enabled: true, speed: 800 }
        },
        series: [{
            name: 'Efficiency',
            data: [85, 87, 89, 91, 88, 92, 89, 94, 91, 89]
        }],
        xaxis: {
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
            labels: { style: { colors: '#ffffff' } }
        },
        yaxis: {
            labels: { style: { colors: '#ffffff' } }
        },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                colorStops: [
                    { offset: 0, color: '#667eea', opacity: 0.8 },
                    { offset: 100, color: '#764ba2', opacity: 0.1 }
                ]
            }
        },
        stroke: {
            curve: 'smooth',
            width: 3,
            colors: ['#667eea']
        },
        grid: {
            borderColor: 'rgba(255,255,255,0.1)',
            strokeDashArray: 5
        }
    },
    
    // Work orders status donut
    workOrdersChart: {
        chart: {
            type: 'donut',
            height: 250,
            background: 'transparent'
        },
        series: [44, 55, 13, 33],
        labels: ['Completed', 'In Progress', 'Critical', 'Scheduled'],
        colors: ['#27ae60', '#3498db', '#e74c3c', '#f39c12'],
        legend: {
            labels: { colors: '#ffffff' }
        },
        plotOptions: {
            pie: {
                donut: {
                    size: '60%',
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            color: '#ffffff'
                        }
                    }
                }
            }
        }
    },
    
    // Theme-aware component updates
    updateThemeBasedComponents() {
        const isDark = document.documentElement.classList.contains('dark-mode');
        
        // Update flatpickr theme
        document.querySelectorAll('.flatpickr-input').forEach(input => {
            if (input._flatpickr) {
                input._flatpickr.set('theme', isDark ? 'dark' : 'light');
            }
        });
        
        // Update chart themes
        if (window.ApexCharts) {
            Object.values(Alpine.store('analytics').chartConfigs).forEach(chart => {
                chart.updateOptions({
                    theme: { mode: isDark ? 'dark' : 'light' },
                    xaxis: { labels: { style: { colors: isDark ? '#ffffff' : '#374151' } } },
                    yaxis: { labels: { style: { colors: isDark ? '#ffffff' : '#374151' } } }
                });
            });
        }
        
        console.log(`🎨 Theme updated: ${isDark ? 'Dark' : 'Light'} mode`);
    },
    
    // Responsive component updates
    updateResponsiveComponents() {
        const breakpoint = document.body.getAttribute('data-breakpoint');
        
        // Update component behaviors based on breakpoint
        document.querySelectorAll('.enhanced-select').forEach(select => {
            if (select.choices) {
                select.choices.config.searchResultLimit = breakpoint === 'mobile' ? 5 : 10;
            }
        });
        
        // Adjust animation performance
        if (breakpoint === 'mobile') {
            gsap.config({ force3D: false });
        } else {
            gsap.config({ force3D: true });
        }
        
        console.log(`📱 Responsive update: ${breakpoint} breakpoint`);
    }
};

// 📊 Enhanced Chart.js Configurations
const ChartJSConfigs = {
    
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    color: 'var(--text-primary)',
                    font: {
                        family: "'Outfit', sans-serif",
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'var(--bg-glass-heavy)',
                titleColor: 'var(--text-primary)',
                bodyColor: 'var(--text-primary)',
                borderColor: 'var(--border-glass)',
                borderWidth: 1,
                cornerRadius: 10,
                displayColors: false,
                titleFont: {
                    family: "'Outfit', sans-serif",
                    weight: '600'
                },
                bodyFont: {
                    family: "'Outfit', sans-serif"
                }
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(255,255,255,0.1)',
                    borderColor: 'var(--border-color)'
                },
                ticks: {
                    color: 'var(--text-primary)',
                    font: {
                        family: "'Outfit', sans-serif"
                    }
                }
            },
            y: {
                grid: {
                    color: 'rgba(255,255,255,0.1)',
                    borderColor: 'var(--border-color)'
                },
                ticks: {
                    color: 'var(--text-primary)',
                    font: {
                        family: "'Outfit', sans-serif"
                    }
                }
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        }
    },
    
    // Initialize Chart.js chart
    initializeChart(element) {
        const type = element.dataset.chartType || 'line';
        const data = JSON.parse(element.dataset.chartData || '{}');
        const options = { ...this.defaultOptions, ...(JSON.parse(element.dataset.chartOptions || '{}')) };
        
        try {
            new Chart(element, {
                type,
                data,
                options
            });
        } catch (error) {
            console.error('Chart.js initialization error:', error);
        }
    },
    
    // Efficiency trend line chart
    efficiencyTrend: {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Efficiency %',
                data: [85, 87, 89, 91, 88, 92],
                borderColor: 'var(--accent-color)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'var(--accent-color)',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        }
    },
    
    // Work orders donut chart
    workOrdersDonut: {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'In Progress', 'Critical', 'Scheduled'],
            datasets: [{
                data: [44, 55, 13, 33],
                backgroundColor: [
                    'var(--cmms-green)',
                    'var(--cmms-blue)',
                    'var(--cmms-red)',
                    'var(--cmms-orange)'
                ],
                borderWidth: 0,
                hoverBorderWidth: 2,
                hoverBorderColor: '#ffffff'
            }]
        },
        options: {
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    }
};

// 🚀 Enhanced Initialization System
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 Enhanced UI Components Library Initializing...');
    
    try {
        // Initialize GSAP plugins and animations
        UIAnimations.init();
        UIAnimations.enhanceCards();
        UIAnimations.pageEnter();
        
        // Initialize modern components
        ModernComponents.init();
        
        // Start real-time updates
        window.realTimeUpdates = new RealTimeUpdates();
        
        // Initialize charts with error handling
        setTimeout(() => {
            try {
                const efficiencyEl = document.querySelector('#efficiency-chart');
                if (efficiencyEl && typeof ApexCharts !== 'undefined') {
                    Alpine.store('analytics').createApexChart('#efficiency-chart', ChartConfigs.efficiencyChart);
                }
                
                const workOrdersEl = document.querySelector('#work-orders-chart');
                if (workOrdersEl && typeof ApexCharts !== 'undefined') {
                    Alpine.store('analytics').createApexChart('#work-orders-chart', ChartConfigs.workOrdersChart);
                }
                
                // Initialize Chart.js charts as fallback
                const chartjsElements = document.querySelectorAll('.chartjs-chart');
                chartjsElements.forEach(el => {
                    ChartJSConfigs.initializeChart(el);
                });
                
            } catch (error) {
                console.warn('⚠️ Chart initialization warning:', error);
            }
        }, 500);
        
        // Theme-aware component updates
        const themeObserver = new MutationObserver(() => {
            ModernComponents.updateThemeBasedComponents();
        });
        themeObserver.observe(document.documentElement, { 
            attributes: true, 
            attributeFilter: ['class'] 
        });
        
        // Setup responsive breakpoint handling
        setupResponsiveHandlers();
        
        // Expose enhanced utilities globally for AI team
        window.UIAnimations = UIAnimations;
        window.ModernComponents = ModernComponents;
        window.ChartConfigs = ChartConfigs;
        window.ChartJSConfigs = ChartJSConfigs;
        
        console.log('✅ Enhanced UI Components Library Ready!');
        console.log('🚀 Phase 2: GSAP animations and Headless UI components - COMPLETED');

        // Only show startup toast on desktop (not mobile) to reduce notification noise
        const isMobile = window.innerWidth <= 768 || /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        if (!isMobile) {
            setTimeout(() => {
                ModernComponents.showToast(
                    '🚀 Enhanced UI system loaded successfully!',
                    'success',
                    2000
                );
            }, 1000);
        }

    } catch (error) {
        console.error('❌ UI Components initialization error:', error);
        // Fallback initialization - silent on mobile
        UIAnimations.enhanceCards();
        window.UIAnimations = UIAnimations;
        window.ModernComponents = ModernComponents;
    }
});

// Responsive breakpoint handlers
function setupResponsiveHandlers() {
    const breakpoints = {
        mobile: window.matchMedia('(max-width: 768px)'),
        tablet: window.matchMedia('(min-width: 769px) and (max-width: 1024px)'),
        desktop: window.matchMedia('(min-width: 1025px)')
    };
    
    Object.entries(breakpoints).forEach(([name, mediaQuery]) => {
        mediaQuery.addEventListener('change', (e) => {
            if (e.matches) {
                document.body.setAttribute('data-breakpoint', name);
                handleBreakpointChange(name);
            }
        });
        
        // Set initial breakpoint
        if (mediaQuery.matches) {
            document.body.setAttribute('data-breakpoint', name);
        }
    });
}

function handleBreakpointChange(breakpoint) {
    switch (breakpoint) {
        case 'mobile':
            // Optimize animations for mobile
            gsap.globalTimeline.timeScale(0.8);
            break;
        case 'tablet':
            gsap.globalTimeline.timeScale(0.9);
            break;
        case 'desktop':
            gsap.globalTimeline.timeScale(1);
            break;
    }
    
    // Re-initialize components that need responsive updates
    ModernComponents.updateResponsiveComponents();
}

// Enhanced error boundary for UI components
// Track errors to avoid spamming notifications
const uiErrorsShown = new Set();

window.addEventListener('error', (event) => {
    if (event.filename && event.filename.includes('ui-components')) {
        // Create a unique error key
        const errorKey = `${event.message}-${event.lineno}`;

        // Log to console for debugging (always)
        console.error('🚨 UI Components Error:', event.error || event.message);

        // Only show notification once per unique error, and only for critical errors
        const isCriticalError = event.message && (
            event.message.includes('is not defined') ||
            event.message.includes('Cannot read') ||
            event.message.includes('TypeError')
        );

        if (isCriticalError && !uiErrorsShown.has(errorKey)) {
            uiErrorsShown.add(errorKey);
            // Don't show intrusive notifications - just log to console
            console.warn('⚠️ A UI component error occurred. Check console for details.');
        }
    }
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const timing = performance.timing;
            const loadTime = timing.loadEventEnd - timing.navigationStart;
            console.log(`📊 UI Components Load Time: ${loadTime}ms`);
            
            if (loadTime > 3000) {
                console.warn('⚠️ UI Components loaded slowly. Consider optimizing.');
            }
        }, 0);
    });
}

// 🧪 Frontend-Backend Integration Testing Utilities
const IntegrationTesting = {
    
    async testEndpoint(url, expectedStatus = 200) {
        try {
            const response = await fetch(url);
            const success = response.status === expectedStatus;
            
            ModernComponents.showNotification(
                `${url} - ${success ? 'PASSED' : 'FAILED'} (${response.status})`,
                success ? 'success' : 'error'
            );
            
            return success;
        } catch (error) {
            ModernComponents.showNotification(
                `${url} - FAILED (${error.message})`,
                'error'
            );
            return false;
        }
    },
    
    async testFeature(featureName, tests) {
        console.log(`🧪 Testing feature: ${featureName}`);
        let passed = 0;
        let total = tests.length;
        
        for (const test of tests) {
            if (await test()) passed++;
        }
        
        const success = passed === total;
        ModernComponents.showNotification(
            `${featureName}: ${passed}/${total} tests passed`,
            success ? 'success' : 'warning'
        );
        
        return success;
    }
};

// Export for AI team use
window.IntegrationTesting = IntegrationTesting;

// Operations Monitor Alpine.js Store
document.addEventListener('alpine:init', () => {
    Alpine.store('operationsMonitor', {
        // Live Metrics
        liveMetrics: {
            fleetHealth: 94.7,
            activeWorkOrders: 12,
            aiSuggestions: 47,
            efficiency: 89.2
        },
        
        // Control States
        refreshing: false,
        autoRefresh: true,
        autoRefreshInterval: null,
        showActivityFeed: false,
        highlightedMetric: null,
        
        // Achievements Data
        achievements: [
            { 
                id: 1, 
                text: "• Prevented 2 equipment failures", 
                impact: "↗ $12,400 saved", 
                positive: true 
            },
            { 
                id: 2, 
                text: "• Optimized 8 maintenance schedules", 
                impact: "↗ 15% efficiency", 
                positive: true 
            },
            { 
                id: 3, 
                text: "• Saved $3,247 in emergency repairs", 
                impact: "↗ Cost reduction", 
                positive: true 
            },
            { 
                id: 4, 
                text: "• Improved efficiency by 7.3%", 
                impact: "↗ Performance", 
                positive: true 
            }
        ],
        
        // Activity Feed
        recentActivity: [
            { timestamp: Date.now() - 300000, message: "Fleet health check completed", time: "2 min ago" },
            { timestamp: Date.now() - 600000, message: "AI detected maintenance opportunity", time: "5 min ago" },
            { timestamp: Date.now() - 900000, message: "Work order WO-2024-0156 completed", time: "8 min ago" },
            { timestamp: Date.now() - 1200000, message: "Efficiency optimization applied", time: "12 min ago" },
            { timestamp: Date.now() - 1500000, message: "Predictive analysis updated", time: "15 min ago" }
        ],
        
        // Additional metrics for calculations
        suggestionsIncrement: 12,
        
        init() {
            // Start auto-refresh if enabled
            if (this.autoRefresh) {
                this.startAutoRefresh();
            }
            
            // Initialize real-time activity simulation
            this.simulateActivity();
            
            console.log('Operations Monitor initialized');
        },
        
        // Metric Management
        async refreshMetrics() {
            this.refreshing = true;
            
            try {
                // Simulate API call
                await this.delay(800);
                
                // Update metrics with slight variations
                this.liveMetrics.fleetHealth = Math.min(100, Math.max(85, this.liveMetrics.fleetHealth + (Math.random() - 0.5) * 2));
                this.liveMetrics.activeWorkOrders = Math.max(0, this.liveMetrics.activeWorkOrders + Math.floor((Math.random() - 0.3) * 3));
                this.liveMetrics.aiSuggestions += Math.floor(Math.random() * 3);
                this.liveMetrics.efficiency = Math.min(100, Math.max(75, this.liveMetrics.efficiency + (Math.random() - 0.5) * 1.5));
                
                this.addActivity('Metrics refreshed successfully');
                
            } catch (error) {
                console.error('Failed to refresh metrics:', error);
                this.addActivity('Metrics refresh failed - retrying...');
            } finally {
                this.refreshing = false;
            }
        },
        
        // Auto-refresh functionality
        toggleAutoRefresh() {
            this.autoRefresh = !this.autoRefresh;
            
            if (this.autoRefresh) {
                this.startAutoRefresh();
                this.addActivity('Auto-refresh enabled');
            } else {
                this.stopAutoRefresh();
                this.addActivity('Auto-refresh disabled');
            }
        },
        
        startAutoRefresh() {
            if (this.autoRefreshInterval) return;
            
            this.autoRefreshInterval = setInterval(() => {
                if (!this.refreshing) {
                    this.refreshMetrics();
                }
            }, 30000); // 30 seconds
        },
        
        stopAutoRefresh() {
            if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
                this.autoRefreshInterval = null;
            }
        },
        
        // Metric Interaction
        highlightMetric(metricType) {
            this.highlightedMetric = metricType;
        },
        
        clearHighlight() {
            this.highlightedMetric = null;
        },
        
        getMetricStyle(metricType) {
            const isHighlighted = this.highlightedMetric === metricType;
            return {
                transform: isHighlighted ? 'scale(1.05)' : 'scale(1)',
                color: isHighlighted ? '#00f5ff' : 'inherit',
                textShadow: isHighlighted ? '0 0 10px rgba(0, 245, 255, 0.5)' : 'none'
            };
        },
        
        // Drill-down functionality
        drillDown(metricType) {
            this.addActivity(`Drilling down into ${metricType} details`);
            
            const drillDownData = {
                'fleet-health': 'Fleet Health: 94.7% (32 vehicles healthy, 2 needs attention)',
                'work-orders': `Active Work Orders: ${this.liveMetrics.activeWorkOrders} (3 urgent, 5 scheduled, 4 in-progress)`,
                'ai-suggestions': `AI Suggestions: ${this.liveMetrics.aiSuggestions} today (12 maintenance, 8 optimization, 27 efficiency)`,
                'efficiency': `Efficiency: ${this.liveMetrics.efficiency}% (↑2.1% from last week)`
            };
            
            // Show detailed information (in real app, would open modal or navigate)
            alert(drillDownData[metricType] || 'Detailed view coming soon!');
        },
        
        // Status calculation methods
        getHealthStatus(health) {
            if (health >= 95) return "Excellent";
            if (health >= 90) return "Good"; 
            if (health >= 80) return "Fair";
            return "Needs Attention";
        },
        
        getWorkOrderStatus() {
            const count = this.liveMetrics.activeWorkOrders;
            if (count <= 5) return "Light Load";
            if (count <= 15) return "Normal";
            if (count <= 25) return "Busy";
            return "Overloaded";
        },
        
        getEfficiencyTrend() {
            const eff = this.liveMetrics.efficiency;
            if (eff >= 90) return "↗ Trending Up";
            if (eff >= 80) return "→ Stable";
            return "↘ Needs Improvement";
        },
        
        // Action functions
        async exportMetrics() {
            this.addActivity('Exporting metrics data...');
            
            const metricsData = {
                timestamp: new Date().toISOString(),
                metrics: this.liveMetrics,
                achievements: this.achievements,
                recentActivity: this.recentActivity.slice(-10)
            };
            
            // Create and download file
            const blob = new Blob([JSON.stringify(metricsData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `operations-metrics-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.addActivity('Metrics exported successfully');
        },
        
        setAlerts() {
            this.addActivity('Opening alert configuration...');
            
            // In real app, would open alert configuration modal
            const alertTypes = [
                'Fleet Health < 85%',
                'Work Orders > 20',
                'Efficiency < 80%',
                'Critical Equipment Issues'
            ];
            
            alert('Alert Configuration:\n\n' + alertTypes.join('\n') + '\n\n(Feature coming soon!)');
        },
        
        viewDetailedReport() {
            this.addActivity('Generating detailed achievement report...');
            
            // Simulate report generation
            setTimeout(() => {
                const report = this.achievements.map(a => a.text + ' - ' + a.impact).join('\n');
                alert('Detailed AI Achievements Report:\n\n' + report + '\n\nTotal Value Generated: $15,647\nEfficiency Improvements: 22.3%');
            }, 500);
        },
        
        // Activity management
        addActivity(message) {
            const now = new Date();
            
            this.recentActivity.push({
                timestamp: now.getTime(),
                message: message,
                time: 'Just now'
            });
            
            // Update time strings for existing activities
            this.updateActivityTimes();
            
            // Keep only last 20 activities
            if (this.recentActivity.length > 20) {
                this.recentActivity.shift();
            }
        },
        
        updateActivityTimes() {
            const now = Date.now();
            this.recentActivity.forEach(activity => {
                const diffMinutes = Math.floor((now - activity.timestamp) / 60000);
                if (diffMinutes < 1) {
                    activity.time = 'Just now';
                } else if (diffMinutes < 60) {
                    activity.time = `${diffMinutes} min ago`;
                } else {
                    const diffHours = Math.floor(diffMinutes / 60);
                    activity.time = `${diffHours}h ago`;
                }
            });
        },
        
        simulateActivity() {
            // Add random activities periodically
            const activities = [
                'Equipment sensor data updated',
                'Maintenance prediction calculated',
                'Work order priority adjusted',
                'AI optimization applied',
                'Performance metric updated',
                'Fleet status synchronized',
                'Efficiency threshold checked',
                'Predictive model refined'
            ];
            
            setInterval(() => {
                if (Math.random() < 0.3) { // 30% chance every 15 seconds
                    const randomActivity = activities[Math.floor(Math.random() * activities.length)];
                    this.addActivity(randomActivity);
                }
            }, 15000);
            
            // Update activity times every minute
            setInterval(() => {
                this.updateActivityTimes();
            }, 60000);
        },
        
        // Utility
        delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
    });
});

// 🎤 Voice Commands Store - ChatterFix Competitive Advantage
document.addEventListener('alpine:init', () => {
    Alpine.store('voiceCommands', {
        // Voice Recognition State
        isListening: false,
        isSupported: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
        recognition: null,
        lastCommand: '',
        confidence: 0,
        
        // Voice Command Categories
        commands: {
            workOrders: [
                'create work order', 'new work order', 'add work order',
                'close work order', 'complete work order', 'finish work order',
                'assign work order', 'update work order', 'priority high', 'priority low'
            ],
            assets: [
                'scan asset', 'check asset', 'asset status', 'asset history',
                'maintenance schedule', 'add asset', 'update asset'
            ],
            navigation: [
                'go to dashboard', 'open work orders', 'show analytics', 'open planner',
                'go to assets', 'show inventory', 'open team', 'go to purchasing'
            ],
            ai: [
                'ask ai team', 'fix it fred', 'get suggestions', 'analyze problem',
                'predict maintenance', 'optimize schedule', 'generate report'
            ]
        },
        
        // Voice Feedback
        voiceEnabled: SafeStorage.get('voiceEnabled') !== 'false',
        speechSynthesis: window.speechSynthesis,
        
        init() {
            if (this.isSupported) {
                this.setupSpeechRecognition();
                console.log('🎤 Voice Commands initialized');
            } else {
                console.warn('⚠️ Speech recognition not supported in this browser');
            }
        },
        
        setupSpeechRecognition() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isListening = true;
                this.showVoiceIndicator();
                console.log('🎤 Voice recognition started');
            };
            
            this.recognition.onresult = (event) => {
                const result = event.results[0];
                const command = result[0].transcript.toLowerCase().trim();
                this.confidence = result[0].confidence;
                this.lastCommand = command;
                
                console.log(`🎤 Voice command: "${command}" (confidence: ${(this.confidence * 100).toFixed(1)}%)`);
                this.processVoiceCommand(command);
            };
            
            this.recognition.onerror = (event) => {
                console.error('🎤 Speech recognition error:', event.error);
                this.isListening = false;
                this.hideVoiceIndicator();
                
                if (event.error === 'not-allowed') {
                    this.speak('Microphone access denied. Please allow microphone permissions.');
                }
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                this.hideVoiceIndicator();
                console.log('🎤 Voice recognition ended');
            };
        },
        
        toggleListening() {
            if (!this.isSupported) {
                alert('Voice commands are not supported in this browser. Please use Chrome, Edge, or Safari.');
                return;
            }
            
            if (this.isListening) {
                this.recognition.stop();
            } else {
                this.recognition.start();
            }
        },
        
        processVoiceCommand(command) {
            console.log(`🤖 Processing command: "${command}"`);
            
            // Work Order Commands
            if (this.matchCommand(command, this.commands.workOrders)) {
                this.handleWorkOrderCommand(command);
            }
            // Asset Commands  
            else if (this.matchCommand(command, this.commands.assets)) {
                this.handleAssetCommand(command);
            }
            // Navigation Commands
            else if (this.matchCommand(command, this.commands.navigation)) {
                this.handleNavigationCommand(command);
            }
            // AI Commands
            else if (this.matchCommand(command, this.commands.ai)) {
                this.handleAICommand(command);
            }
            // Natural Language Processing
            else {
                this.handleNaturalLanguageCommand(command);
            }
            
            // Show command feedback
            this.showCommandFeedback(command);
        },
        
        matchCommand(input, commandList) {
            return commandList.some(cmd => input.includes(cmd));
        },
        
        handleWorkOrderCommand(command) {
            if (command.includes('create') || command.includes('new') || command.includes('add')) {
                this.speak('Creating new work order');
                window.location.href = '/demo/work-orders#create';
            } else if (command.includes('close') || command.includes('complete') || command.includes('finish')) {
                this.speak('Opening work order completion dialog');
                this.showWorkOrderCompletion();
            } else if (command.includes('priority high')) {
                this.speak('Setting work order priority to high');
                this.setPriority('high');
            } else if (command.includes('priority low')) {
                this.speak('Setting work order priority to low');
                this.setPriority('low');
            }
        },
        
        handleAssetCommand(command) {
            if (command.includes('scan')) {
                this.speak('Opening asset scanner');
                this.openAssetScanner();
            } else if (command.includes('status') || command.includes('check')) {
                this.speak('Checking asset status');
                window.location.href = '/demo/assets';
            } else if (command.includes('history')) {
                this.speak('Opening asset maintenance history');
                this.showAssetHistory();
            }
        },
        
        handleNavigationCommand(command) {
            const routes = {
                'dashboard': '/demo',
                'work orders': '/demo/work-orders',
                'analytics': '/demo/analytics',
                'planner': '/demo/planner',
                'assets': '/demo/assets',
                'inventory': '/inventory',
                'team': '/demo/team',
                'purchasing': '/demo/purchasing'
            };
            
            for (const [page, route] of Object.entries(routes)) {
                if (command.includes(page)) {
                    this.speak(`Navigating to ${page}`);
                    window.location.href = route;
                    return;
                }
            }
        },
        
        handleAICommand(command) {
            if (command.includes('ai team') || command.includes('ask ai')) {
                this.speak('Activating AI team collaboration');
                this.activateAIChat();
            } else if (command.includes('fix it fred')) {
                this.speak('Summoning Fix-it Fred for autonomous problem solving');
                this.activateFixItFred();
            } else if (command.includes('suggestions') || command.includes('optimize')) {
                this.speak('Generating AI maintenance suggestions');
                this.generateAISuggestions();
            } else if (command.includes('predict')) {
                this.speak('Running predictive maintenance analysis');
                this.runPredictiveAnalysis();
            }
        },
        
        handleNaturalLanguageCommand(command) {
            // Send to AI team for natural language processing
            this.speak('Processing your request with the AI team');
            
            fetch('/ai-team/natural-language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    command: command,
                    confidence: this.confidence,
                    context: 'voice_command'
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.action) {
                    this.executeAIAction(result);
                } else {
                    this.speak(result.response || 'I did not understand that command. Please try again.');
                }
            })
            .catch(error => {
                console.error('AI processing error:', error);
                this.speak('Sorry, I could not process that command. Please try again.');
            });
        },
        
        // Voice Actions
        speak(text) {
            if (!this.voiceEnabled || !this.speechSynthesis) return;
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 0.8;
            
            this.speechSynthesis.speak(utterance);
        },
        
        showVoiceIndicator() {
            // Create or show voice indicator
            let indicator = document.getElementById('voice-indicator');
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'voice-indicator';
                indicator.innerHTML = `
                    <div class="voice-pulse">
                        <i class="fas fa-microphone"></i>
                        <span>Listening...</span>
                    </div>
                `;
                indicator.style.cssText = `
                    position: fixed; 
                    top: 50%; 
                    left: 50%; 
                    transform: translate(-50%, -50%); 
                    z-index: 9999; 
                    background: var(--bg-glass-heavy); 
                    border: 2px solid var(--accent); 
                    border-radius: 20px; 
                    padding: 20px; 
                    text-align: center;
                    backdrop-filter: blur(20px);
                    box-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
                `;
                document.body.appendChild(indicator);
                
                // Add CSS for pulse animation
                const style = document.createElement('style');
                style.textContent = `
                    .voice-pulse {
                        animation: voicePulse 1.5s infinite;
                        color: var(--accent);
                    }
                    @keyframes voicePulse {
                        0%, 100% { opacity: 1; transform: scale(1); }
                        50% { opacity: 0.7; transform: scale(1.1); }
                    }
                `;
                document.head.appendChild(style);
            } else {
                indicator.style.display = 'block';
            }
        },
        
        hideVoiceIndicator() {
            const indicator = document.getElementById('voice-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        },
        
        showCommandFeedback(command) {
            ModernComponents.showNotification(
                `🎤 Voice command: "${command}"`,
                'info',
                3000
            );
        },
        
        // Integration Functions
        activateAIChat() {
            const aiChatButton = document.querySelector('.ai-chat-toggle');
            if (aiChatButton) {
                aiChatButton.click();
            }
        },
        
        activateFixItFred() {
            // Navigate to Fix-it Fred or trigger autonomous fixing
            window.location.href = '/fix-it-fred';
        },
        
        generateAISuggestions() {
            if (Alpine.store('aiSystem')) {
                Alpine.store('aiSystem').generateSuggestions();
            }
        },
        
        runPredictiveAnalysis() {
            if (Alpine.store('aiSystem')) {
                Alpine.store('aiSystem').runFleetAnalysis();
            }
        },
        
        openAssetScanner() {
            this.speak('Opening QR code asset scanner');
            if (Alpine.store('qrScanner')) {
                Alpine.store('qrScanner').startScanning();
            }
        },
        
        showWorkOrderCompletion() {
            // Show work order completion modal
            ModernComponents.showNotification('Work Order Completion: Feature coming soon!', 'info');
        },
        
        setPriority(level) {
            // Set work order priority
            ModernComponents.showNotification(`Priority set to ${level}`, 'success');
        },
        
        showAssetHistory() {
            window.location.href = '/demo/assets#history';
        },
        
        executeAIAction(action) {
            // Execute AI-generated actions
            if (action.navigate) {
                window.location.href = action.navigate;
            } else if (action.function) {
                // Execute specific function
                eval(action.function);
            }
            
            if (action.speak) {
                this.speak(action.speak);
            }
        },
        
        toggleVoiceEnabled() {
            this.voiceEnabled = !this.voiceEnabled;
            SafeStorage.set('voiceEnabled', this.voiceEnabled);
            
            ModernComponents.showNotification(
                `Voice feedback ${this.voiceEnabled ? 'enabled' : 'disabled'}`,
                'info'
            );
        }
    });
});

// Initialize all stores when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Ensure Alpine.js stores are available
    if (window.Alpine) {
        // Initialize user preferences first
        if (Alpine.store('userPreferences')) {
            Alpine.store('userPreferences').init();
        }
        
        // Initialize voice commands
        if (Alpine.store('voiceCommands')) {
            Alpine.store('voiceCommands').init();
        }
        
        // Initialize QR scanner
        if (Alpine.store('qrScanner')) {
            Alpine.store('qrScanner').init();
        }
        
        // Then initialize operations monitor
        if (Alpine.store('operationsMonitor')) {
            Alpine.store('operationsMonitor').init();
        }
        
        console.log('✅ All Alpine.js stores initialized');
    }
});

// 📱 QR Code Scanner Store - Industry Standard Feature
document.addEventListener('alpine:init', () => {
    Alpine.store('qrScanner', {
        // Scanner State
        isActive: false,
        isSupported: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
        stream: null,
        video: null,
        canvas: null,
        context: null,
        
        // Scan Results
        lastScannedCode: '',
        scanHistory: SafeStorage.getJSON('qrScanHistory', []),
        
        // Asset Data
        currentAsset: null,
        assetHistory: [],
        
        init() {
            console.log('📱 QR Scanner initialized');
            this.loadJSQR(); // Load QR code library
        },
        
        async loadJSQR() {
            // Load jsQR library dynamically
            if (!window.jsQR) {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js';
                script.onload = () => {
                    console.log('📱 jsQR library loaded');
                };
                document.head.appendChild(script);
            }
        },
        
        async startScanning() {
            if (!this.isSupported) {
                alert('Camera access is not supported in this browser.');
                return;
            }
            
            try {
                // Request camera permissions
                this.stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: 'environment', // Use back camera if available
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                });
                
                this.isActive = true;
                this.showScannerModal();
                this.startVideoStream();
                
            } catch (error) {
                console.error('Camera access error:', error);
                alert('Camera access denied or not available. Please check your browser permissions.');
            }
        },
        
        stopScanning() {
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }
            
            if (this.video) {
                this.video.srcObject = null;
            }
            
            this.isActive = false;
            this.hideScannerModal();
            console.log('📱 QR Scanner stopped');
        },
        
        showScannerModal() {
            // Create scanner modal
            const modal = document.createElement('div');
            modal.id = 'qr-scanner-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.9);
                z-index: 10000;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 20px;
            `;
            
            modal.innerHTML = `
                <div style="text-align: center; color: white; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 10px 0;">
                        <i class="fas fa-qrcode"></i> Scan Asset QR Code
                    </h3>
                    <p style="margin: 0; opacity: 0.8;">Position the QR code within the frame</p>
                </div>
                
                <div class="scanner-container" style="position: relative; border-radius: 20px; overflow: hidden; box-shadow: 0 0 30px rgba(0,245,255,0.5);">
                    <video id="qr-video" style="width: 100%; max-width: 400px; height: auto; display: block;"></video>
                    <canvas id="qr-canvas" style="display: none;"></canvas>
                    
                    <!-- Scanning Overlay -->
                    <div class="scan-overlay" style="
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        border: 3px solid var(--accent);
                        border-radius: 20px;
                        pointer-events: none;
                    ">
                        <div class="scan-line" style="
                            position: absolute;
                            top: 50%;
                            left: 10%;
                            right: 10%;
                            height: 2px;
                            background: var(--accent);
                            animation: scanPulse 2s linear infinite;
                            box-shadow: 0 0 10px var(--accent);
                        "></div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; display: flex; gap: 15px;">
                    <button onclick="Alpine.store('qrScanner').stopScanning()" 
                            class="glass-button btn btn-outline-light" 
                            style="padding: 10px 20px;">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button onclick="Alpine.store('qrScanner').toggleFlashlight()" 
                            class="glass-button btn btn-outline-light" 
                            style="padding: 10px 20px;">
                        <i class="fas fa-flashlight"></i> Flash
                    </button>
                </div>
                
                <div id="scan-status" style="margin-top: 15px; color: var(--accent); text-align: center; font-size: 14px;">
                    Ready to scan...
                </div>
            `;
            
            // Add scanning animation CSS
            const style = document.createElement('style');
            style.textContent = `
                @keyframes scanPulse {
                    0% { transform: translateY(-100px); opacity: 0; }
                    50% { opacity: 1; }
                    100% { transform: translateY(100px); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(modal);
        },
        
        hideScannerModal() {
            const modal = document.getElementById('qr-scanner-modal');
            if (modal) {
                modal.remove();
            }
        },
        
        startVideoStream() {
            this.video = document.getElementById('qr-video');
            this.canvas = document.getElementById('qr-canvas');
            this.context = this.canvas.getContext('2d');
            
            this.video.srcObject = this.stream;
            this.video.play();
            
            this.video.onloadedmetadata = () => {
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
                this.scanFrame();
            };
        },
        
        scanFrame() {
            if (!this.isActive) return;
            
            if (this.video.readyState === this.video.HAVE_ENOUGH_DATA && window.jsQR) {
                this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
                const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
                
                const code = jsQR(imageData.data, imageData.width, imageData.height);
                
                if (code) {
                    this.handleQRCodeDetected(code);
                    return;
                }
            }
            
            requestAnimationFrame(() => this.scanFrame());
        },
        
        async handleQRCodeDetected(code) {
            const qrData = code.data;
            this.lastScannedCode = qrData;
            
            // Update scan status
            const status = document.getElementById('scan-status');
            if (status) {
                status.textContent = 'QR Code detected! Processing...';
                status.style.color = '#00ff96';
            }
            
            // Add to scan history
            this.addToScanHistory(qrData);
            
            // Process the QR code
            await this.processAssetQR(qrData);
            
            // Stop scanning after successful scan
            setTimeout(() => {
                this.stopScanning();
            }, 1000);
        },
        
        addToScanHistory(qrData) {
            const scanEntry = {
                code: qrData,
                timestamp: new Date().toISOString(),
                location: window.location.href
            };
            
            this.scanHistory.unshift(scanEntry);
            
            // Keep only last 50 scans
            if (this.scanHistory.length > 50) {
                this.scanHistory = this.scanHistory.slice(0, 50);
            }

            SafeStorage.setJSON('qrScanHistory', this.scanHistory);
        },
        
        async processAssetQR(qrData) {
            try {
                // Check if QR code matches asset ID format
                let assetData = null;
                
                if (qrData.startsWith('ASSET-') || qrData.startsWith('asset-')) {
                    // Standard asset QR code
                    assetData = await this.fetchAssetData(qrData);
                } else if (qrData.startsWith('http')) {
                    // URL-based QR code
                    assetData = await this.fetchAssetFromUrl(qrData);
                } else {
                    // Try to interpret as asset ID
                    assetData = await this.fetchAssetData(`ASSET-${qrData}`);
                }
                
                if (assetData) {
                    this.currentAsset = assetData;
                    this.showAssetDetails(assetData);
                } else {
                    this.showCreateAssetDialog(qrData);
                }
                
            } catch (error) {
                console.error('Error processing QR code:', error);
                ModernComponents.showNotification(
                    `Error processing QR code: ${error.message}`,
                    'error'
                );
            }
        },
        
        async fetchAssetData(assetId) {
            try {
                const response = await fetch(`/api/assets/${assetId}`);
                if (response.ok) {
                    return await response.json();
                }
                return null;
            } catch (error) {
                console.error('Error fetching asset:', error);
                return null;
            }
        },
        
        async fetchAssetFromUrl(url) {
            try {
                // Extract asset ID from URL if it follows our pattern
                const match = url.match(/\/assets\/([^\/]+)/);
                if (match) {
                    return await this.fetchAssetData(match[1]);
                }
                return null;
            } catch (error) {
                console.error('Error parsing asset URL:', error);
                return null;
            }
        },
        
        showAssetDetails(asset) {
            // Create asset details modal
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 10001;
                background: var(--bg-glass-heavy);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 20px;
                padding: 25px;
                max-width: 400px;
                width: 90%;
                backdrop-filter: blur(20px);
                box-shadow: 0 0 30px rgba(0,0,0,0.5);
            `;
            
            modal.innerHTML = `
                <div style="text-align: center; margin-bottom: 20px;">
                    <h3 style="color: var(--accent); margin: 0 0 10px 0;">
                        <i class="fas fa-cog"></i> Asset Found
                    </h3>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <div style="margin-bottom: 10px;">
                        <strong>ID:</strong> ${asset.id || 'Unknown'}
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Name:</strong> ${asset.name || 'Unnamed Asset'}
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Type:</strong> ${asset.type || 'Unknown Type'}
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Status:</strong> 
                        <span style="color: ${asset.status === 'active' ? '#00ff96' : '#ff6b6b'};">
                            ${asset.status || 'Unknown'}
                        </span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Location:</strong> ${asset.location || 'Not specified'}
                    </div>
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button onclick="this.parentElement.parentElement.remove()" 
                            class="glass-button btn btn-outline-secondary" 
                            style="flex: 1;">
                        Close
                    </button>
                    <button onclick="Alpine.store('qrScanner').viewAssetDetails('${asset.id}')" 
                            class="glass-button btn btn-primary" 
                            style="flex: 1;">
                        View Details
                    </button>
                    <button onclick="Alpine.store('qrScanner').createWorkOrder('${asset.id}')" 
                            class="glass-button btn btn-accent" 
                            style="flex: 1;">
                        Work Order
                    </button>
                </div>
            `;
            
            document.body.appendChild(modal);
        },
        
        showCreateAssetDialog(qrData) {
            ModernComponents.showNotification(
                `QR Code "${qrData}" not found. Would you like to create a new asset?`,
                'info',
                5000
            );
            
            // Could implement asset creation flow here
        },
        
        viewAssetDetails(assetId) {
            // Close modal first
            const modal = document.querySelector('[style*="z-index: 10001"]');
            if (modal) modal.remove();
            
            // Navigate to asset details
            window.location.href = `/demo/assets/${assetId}`;
        },
        
        createWorkOrder(assetId) {
            // Close modal first
            const modal = document.querySelector('[style*="z-index: 10001"]');
            if (modal) modal.remove();
            
            // Navigate to work order creation with asset pre-filled
            window.location.href = `/demo/work-orders/create?asset=${assetId}`;
        },
        
        toggleFlashlight() {
            // Toggle flashlight if supported
            if (this.stream) {
                const track = this.stream.getVideoTracks()[0];
                const capabilities = track.getCapabilities();
                
                if (capabilities.torch) {
                    track.applyConstraints({
                        advanced: [{ torch: !track.getSettings().torch }]
                    });
                } else {
                    ModernComponents.showNotification('Flashlight not supported on this device', 'warning');
                }
            }
        },
        
        getScanHistory() {
            return this.scanHistory;
        },
        
        clearScanHistory() {
            this.scanHistory = [];
            SafeStorage.remove('qrScanHistory');
            ModernComponents.showNotification('Scan history cleared', 'success');
        }
    });
});

// Global voice command function for easy access
window.voiceWorkflow = function() {
    if (Alpine.store('voiceCommands')) {
        Alpine.store('voiceCommands').toggleListening();
    }
};

// Global QR scanner function for easy access
window.scanAssetQR = function() {
    if (Alpine.store('qrScanner')) {
        Alpine.store('qrScanner').startScanning();
    }
};