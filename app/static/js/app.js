/**
 * ChatterFix CMMS - Main Application JavaScript
 * AI Team Enhanced for deployment stability
 */

// Main application namespace
window.ChatterFix = window.ChatterFix || {};

// Application configuration
ChatterFix.config = {
    version: '2.1.0-enterprise-planner',
    environment: 'production',
    api: {
        base: '',
        timeout: 30000
    },
    features: {
        darkMode: true,
        notifications: true,
        analytics: true,
        aiTeam: true
    }
};

// Theme management with localStorage persistence
ChatterFix.theme = {
    init: function() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        this.bindEvents();
    },
    
    setTheme: function(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark-mode');
            document.body.classList.add('dark-mode');
        } else {
            document.documentElement.classList.remove('dark-mode');
            document.body.classList.remove('dark-mode');
        }
        
        localStorage.setItem('theme', theme);
        
        // Update theme toggle buttons
        const toggleBtns = document.querySelectorAll('.theme-toggle');
        toggleBtns.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    icon.className = 'fas fa-sun';
                    btn.title = 'Switch to light mode';
                } else {
                    icon.className = 'fas fa-moon';
                    btn.title = 'Switch to dark mode';
                }
            }
        });
    },
    
    toggle: function() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Analytics tracking
        if (ChatterFix.analytics && ChatterFix.analytics.track) {
            ChatterFix.analytics.track('theme_toggle', { 
                from: currentTheme, 
                to: newTheme 
            });
        }
    },
    
    bindEvents: function() {
        // Bind theme toggle buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.theme-toggle')) {
                e.preventDefault();
                this.toggle();
            }
        });
    }
};

// Notification system
ChatterFix.notifications = {
    show: function(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
    },
    
    success: function(message, duration = 5000) {
        this.show(message, 'success', duration);
    },
    
    error: function(message, duration = 8000) {
        this.show(message, 'danger', duration);
    },
    
    warning: function(message, duration = 6000) {
        this.show(message, 'warning', duration);
    },
    
    info: function(message, duration = 5000) {
        this.show(message, 'info', duration);
    }
};

// API utilities with error handling
ChatterFix.api = {
    request: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: ChatterFix.config.api.timeout
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), mergedOptions.timeout);
            
            const response = await fetch(url, {
                ...mergedOptions,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            
            if (error.name === 'AbortError') {
                ChatterFix.notifications.error('Request timeout - please try again');
            } else {
                ChatterFix.notifications.error(`Request failed: ${error.message}`);
            }
            
            throw error;
        }
    },
    
    get: function(url) {
        return this.request(url, { method: 'GET' });
    },
    
    post: function(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    put: function(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    delete: function(url) {
        return this.request(url, { method: 'DELETE' });
    }
};

// Analytics and error tracking
ChatterFix.analytics = {
    track: function(event, properties = {}) {
        try {
            // Basic analytics tracking
            console.log('Analytics:', event, properties);
            
            // Send to analytics endpoint if available
            if (ChatterFix.config.features.analytics) {
                ChatterFix.api.post('/analytics/track', {
                    event: event,
                    properties: {
                        ...properties,
                        timestamp: new Date().toISOString(),
                        url: window.location.href,
                        user_agent: navigator.userAgent
                    }
                }).catch(err => {
                    // Silent fail for analytics
                    console.debug('Analytics tracking failed:', err);
                });
            }
        } catch (error) {
            console.debug('Analytics error:', error);
        }
    },
    
    error: function(error, context = {}) {
        console.error('Application error:', error, context);
        
        this.track('error', {
            message: error.message,
            stack: error.stack,
            context: context
        });
    }
};

// Global error handling
window.addEventListener('error', (event) => {
    ChatterFix.analytics.error(event.error, {
        filename: event.filename,
        line: event.lineno,
        column: event.colno
    });
});

window.addEventListener('unhandledrejection', (event) => {
    ChatterFix.analytics.error(event.reason, {
        type: 'unhandled_promise_rejection'
    });
});

// Mobile detection and responsive utilities
ChatterFix.mobile = {
    isMobile: function() {
        return window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    isTablet: function() {
        return window.innerWidth <= 1024 && window.innerWidth > 768;
    },
    
    bindResponsiveEvents: function() {
        window.addEventListener('resize', () => {
            // Emit resize event for components to handle
            document.dispatchEvent(new CustomEvent('chatterfix:resize', {
                detail: {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    mobile: this.isMobile(),
                    tablet: this.isTablet()
                }
            }));
        });
    }
};

// Page loading utilities
ChatterFix.page = {
    showLoading: function(message = 'Loading...') {
        let loader = document.getElementById('global-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'global-loader';
            loader.innerHTML = `
                <div class="d-flex justify-content-center align-items-center" style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    z-index: 9999;
                ">
                    <div class="text-center text-white">
                        <div class="spinner-border mb-3" role="status"></div>
                        <div>${message}</div>
                    </div>
                </div>
            `;
            document.body.appendChild(loader);
        }
    },
    
    hideLoading: function() {
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.remove();
        }
    }
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 ChatterFix CMMS initializing...');
    
    try {
        // Initialize core components
        ChatterFix.theme.init();
        ChatterFix.mobile.bindResponsiveEvents();
        
        // Track page load
        ChatterFix.analytics.track('page_load', {
            path: window.location.pathname,
            referrer: document.referrer,
            viewport: `${window.innerWidth}x${window.innerHeight}`
        });
        
        console.log('✅ ChatterFix CMMS initialized successfully');
        
        // Dispatch ready event
        document.dispatchEvent(new CustomEvent('chatterfix:ready'));
        
    } catch (error) {
        console.error('❌ ChatterFix initialization failed:', error);
        ChatterFix.analytics.error(error, { context: 'initialization' });
    }
});

// Export for global access
window.ChatterFix = ChatterFix;