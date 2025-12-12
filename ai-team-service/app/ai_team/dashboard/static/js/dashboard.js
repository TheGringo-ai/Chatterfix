/* 🚀 AI Team Dashboard JavaScript */
class AITeamDashboard {
    constructor() {
        this.websocket = null;
        this.reconnectInterval = null;
        this.updateInterval = null;
        this.currentSection = 'overview';
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing AI Team Dashboard...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize WebSocket connection
        this.initWebSocket();
        
        // Load initial data
        await this.loadInitialData();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        console.log('✅ AI Team Dashboard initialized successfully');
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.showSection(section);
            });
        });
        
        // Quick actions
        const quickActions = {
            'refresh-data': () => this.refreshAllData(),
            'run-collaboration': () => this.startTeamCollaboration(),
            'search-memory': () => this.showMemorySearch(),
            'analyze-patterns': () => this.analyzePatterns(),
            'export-data': () => this.exportData()
        };
        
        Object.entries(quickActions).forEach(([id, handler]) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('click', handler.bind(this));
            }
        });
        
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        }
    }
    
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔗 WebSocket connected');
                this.updateConnectionStatus(true);
                this.clearReconnectInterval();
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.scheduleReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('❌ Failed to initialize WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status_update':
                this.updateSystemStatus(data.data);
                break;
            case 'new_interaction':
                this.addNewInteraction(data.data);
                break;
            case 'pattern_learned':
                this.showPatternLearnedNotification(data.data);
                break;
            default:
                console.log('📨 Received WebSocket message:', data);
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectInterval) return;
        
        this.reconnectInterval = setInterval(() => {
            console.log('🔄 Attempting to reconnect WebSocket...');
            this.initWebSocket();
        }, 5000);
    }
    
    clearReconnectInterval() {
        if (this.reconnectInterval) {
            clearInterval(this.reconnectInterval);
            this.reconnectInterval = null;
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-wifi"></i> Connected';
            statusElement.style.background = 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)';
        } else {
            statusElement.innerHTML = '<i class="fas fa-wifi-slash"></i> Disconnected';
            statusElement.style.background = 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)';
        }
    }
    
    async loadInitialData() {
        console.log('📊 Loading initial dashboard data...');
        
        try {
            // Load system status
            await this.loadSystemStatus();
            
            // Load recent interactions
            await this.loadRecentInteractions();
            
            console.log('✅ Initial data loaded successfully');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.updateSystemStatus(status);
        } catch (error) {
            console.error('❌ Error loading system status:', error);
        }
    }
    
    updateSystemStatus(status) {
        // Update status cards
        this.updateElement('memory-conversations', status.memory_system?.total_conversations || 0);
        this.updateElement('patterns-learned', status.memory_system?.patterns_learned || 0);
        this.updateElement('mistakes-prevented', status.memory_system?.mistakes_prevented || 0);
        this.updateElement('platform-effectiveness', `${status.platform?.effectiveness || 0}%`);
        
        // Update uptime
        this.updateElement('system-uptime', status.uptime || '00:00:00');
        
        // Update status badge
        const statusBadge = document.getElementById('status-badge');
        if (statusBadge) {
            statusBadge.textContent = status.status === 'online' ? 'ONLINE' : 'OFFLINE';
            statusBadge.className = status.status === 'online' ? 'badge bg-success ms-2' : 'badge bg-danger ms-2';
        }
        
        console.log('📊 System status updated');
    }
    
    async loadRecentInteractions() {
        try {
            const response = await fetch('/api/interactions?limit=5');
            const interactions = await response.json();
            
            this.updateRecentActivity(interactions);
        } catch (error) {
            console.error('❌ Error loading recent interactions:', error);
        }
    }
    
    updateRecentActivity(interactions) {
        const activityContainer = document.getElementById('recent-activity');
        if (!activityContainer) return;
        
        // Clear existing activities (except first one which is static)
        const existingItems = activityContainer.querySelectorAll('.activity-item:not(:first-child)');
        existingItems.forEach(item => item.remove());
        
        // Add new interactions
        interactions.forEach((interaction, index) => {
            if (index === 0) return; // Skip first one to avoid duplicating static item
            
            const activityItem = this.createActivityItem(interaction);
            activityContainer.appendChild(activityItem);
        });
    }
    
    createActivityItem(interaction) {
        const item = document.createElement('div');
        item.className = 'activity-item';
        
        const iconClass = this.getActivityIconClass(interaction.application);
        const timeAgo = this.formatTimeAgo(new Date(interaction.timestamp));
        
        item.innerHTML = `
            <div class="activity-icon ${iconClass}">
                <i class="fas fa-${this.getActivityIcon(interaction.application)}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${interaction.application} interaction</div>
                <div class="activity-description">${interaction.user_request}</div>
                <div class="activity-time">${timeAgo}</div>
            </div>
        `;
        
        return item;
    }
    
    getActivityIconClass(application) {
        const iconClasses = {
            'ChatterFix': 'learning',
            'Fix it Fred': 'prevention', 
            'LineSmart': 'platform'
        };
        return iconClasses[application] || 'learning';
    }
    
    getActivityIcon(application) {
        const icons = {
            'ChatterFix': 'tools',
            'Fix it Fred': 'wrench',
            'LineSmart': 'comments'
        };
        return icons[application] || 'robot';
    }
    
    formatTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    }
    
    showSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${sectionName}-section`).classList.add('active');
        
        this.currentSection = sectionName;
        
        // Load section-specific data
        this.loadSectionData(sectionName);
    }
    
    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'analytics':
                await this.loadAnalytics();
                break;
            case 'memory':
                await this.loadMemoryData();
                break;
            case 'interactions':
                await this.loadInteractionsData();
                break;
        }
    }
    
    async loadAnalytics() {
        try {
            const response = await fetch('/api/analytics');
            const analytics = await response.json();
            
            console.log('📈 Analytics loaded:', analytics);
            // Update analytics UI here
        } catch (error) {
            console.error('❌ Error loading analytics:', error);
        }
    }
    
    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            this.loadSystemStatus();
            
            if (this.currentSection === 'interactions') {
                this.loadRecentInteractions();
            }
        }, 30000); // Update every 30 seconds
    }
    
    async refreshAllData() {
        const refreshBtn = document.getElementById('refresh-data');
        const originalContent = refreshBtn.innerHTML;
        
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        refreshBtn.disabled = true;
        
        try {
            await this.loadInitialData();
            await this.loadSectionData(this.currentSection);
            
            this.showNotification('Data refreshed successfully', 'success');
        } catch (error) {
            console.error('❌ Error refreshing data:', error);
            this.showNotification('Failed to refresh data', 'error');
        } finally {
            refreshBtn.innerHTML = originalContent;
            refreshBtn.disabled = false;
        }
    }
    
    async startTeamCollaboration() {
        const prompt = prompt('Enter a task for the AI team to collaborate on:');
        if (!prompt) return;
        
        try {
            const response = await fetch('/api/team/collaborate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    prompt: prompt,
                    context: 'Dashboard collaboration request',
                    models: ['claude', 'gpt-4']
                })
            });
            
            const result = await response.json();
            this.showNotification('Team collaboration started', 'success');
            console.log('🤝 Collaboration result:', result);
        } catch (error) {
            console.error('❌ Error starting collaboration:', error);
            this.showNotification('Failed to start collaboration', 'error');
        }
    }
    
    showMemorySearch() {
        const query = prompt('Enter search query for AI team memory:');
        if (!query) return;
        
        this.searchMemory(query);
    }
    
    async searchMemory(query) {
        try {
            const response = await fetch('/api/memory/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: query,
                    limit: 10
                })
            });
            
            const results = await response.json();
            console.log('🔍 Search results:', results);
            this.showNotification(`Found ${results.results?.length || 0} results`, 'info');
        } catch (error) {
            console.error('❌ Error searching memory:', error);
            this.showNotification('Search failed', 'error');
        }
    }
    
    analyzePatterns() {
        this.showNotification('Pattern analysis started', 'info');
        console.log('📊 Analyzing patterns...');
    }
    
    exportData() {
        this.showNotification('Data export started', 'info');
        console.log('📥 Exporting data...');
    }
    
    toggleTheme() {
        const body = document.body;
        const isDark = body.classList.contains('dark-theme');
        
        if (isDark) {
            body.classList.remove('dark-theme');
            body.classList.add('light-theme');
            localStorage.setItem('ai-dashboard-theme', 'light');
        } else {
            body.classList.remove('light-theme');
            body.classList.add('dark-theme');
            localStorage.setItem('ai-dashboard-theme', 'dark');
        }
        
        // Update theme toggle icon
        const themeIcon = document.querySelector('#theme-toggle i');
        themeIcon.className = isDark ? 'fas fa-moon' : 'fas fa-sun';
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            ${message}
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show animation
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    addNewInteraction(interaction) {
        const activityContainer = document.getElementById('recent-activity');
        if (!activityContainer) return;
        
        const newItem = this.createActivityItem(interaction);
        activityContainer.insertBefore(newItem, activityContainer.firstChild);
        
        // Remove oldest item if too many
        const items = activityContainer.querySelectorAll('.activity-item');
        if (items.length > 10) {
            items[items.length - 1].remove();
        }
        
        this.showNotification(`New ${interaction.application} interaction`, 'info');
    }
    
    showPatternLearnedNotification(pattern) {
        this.showNotification(`New pattern learned: ${pattern.name}`, 'success');
    }
}

// Additional CSS for notifications
const notificationStyles = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 9999;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
    min-width: 300px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.notification.show {
    opacity: 1;
    transform: translateX(0);
}

.notification-success {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.notification-error {
    background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
}

.notification-warning {
    background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
}

.notification-info {
    background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
}

.notification i {
    margin-right: 0.5rem;
}
`;

// Inject notification styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Apply saved theme
    const savedTheme = localStorage.getItem('ai-dashboard-theme') || 'dark';
    document.body.className = `${savedTheme}-theme`;
    
    // Initialize dashboard
    window.dashboard = new AITeamDashboard();
});