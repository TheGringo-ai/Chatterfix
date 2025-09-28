/**
 * ChatterFix CMMS Data Mode Toggle System
 * Professional toggle component for switching between Demo and Production modes
 * Features: Professional UI, confirmation dialogs, loading states, AI recommendations
 */

class DataModeToggle {
    constructor() {
        this.currentMode = null;
        this.isLoading = false;
        this.user = null;
        this.recommendations = [];
        this.confirmationModal = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Load current system status
            await this.loadSystemStatus();
            
            // Create toggle component
            this.createToggleComponent();
            
            // Create confirmation modal
            this.createConfirmationModal();
            
            // Create company setup wizard modal
            this.createCompanySetupWizard();
            
            // Bind event listeners
            this.bindEvents();
            
            // Start periodic status updates
            this.startStatusUpdates();
            
            console.log('🔄 Data Mode Toggle System initialized');
        } catch (error) {
            console.error('❌ Error initializing Data Mode Toggle:', error);
        }
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/admin/system-status');
            const data = await response.json();
            
            if (data.success) {
                this.currentMode = data.status.current_mode;
                this.user = data.user;
                this.recommendations = data.status.recommendations || [];
                
                // Update environment variable for immediate effect
                window.SYSTEM_MODE = this.currentMode;
                
                console.log(`📊 System status loaded: ${this.currentMode} mode`);
            } else {
                throw new Error(data.error || 'Failed to load system status');
            }
        } catch (error) {
            console.error('❌ Error loading system status:', error);
            // Fallback to production mode
            this.currentMode = 'production';
        }
    }
    
    createToggleComponent() {
        const header = document.querySelector('.header, .navbar, header') || document.body;
        
        // Create toggle container
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'data-mode-toggle-container';
        toggleContainer.innerHTML = `
            <div class="data-mode-toggle">
                <div class="mode-indicator ${this.currentMode}">
                    <span class="mode-icon">${this.currentMode === 'demo' ? '🧪' : '🚀'}</span>
                    <span class="mode-text">${this.currentMode === 'demo' ? 'Demo Mode' : 'Production Mode'}</span>
                    <span class="mode-badge ${this.currentMode}">${this.currentMode.toUpperCase()}</span>
                </div>
                
                <div class="toggle-switch" ${!this.canSwitchMode() ? 'disabled' : ''}>
                    <input type="checkbox" id="dataModeSwitcher" ${this.currentMode === 'production' ? 'checked' : ''} 
                           ${!this.canSwitchMode() ? 'disabled' : ''}>
                    <label for="dataModeSwitcher" class="switch-label">
                        <span class="switch-slider">
                            <span class="switch-text demo">DEMO</span>
                            <span class="switch-text production">PROD</span>
                        </span>
                    </label>
                </div>
                
                <div class="mode-actions">
                    <button class="btn-mode-info" title="System Information">
                        <span class="icon">ℹ️</span>
                    </button>
                    <button class="btn-recommendations" title="AI Recommendations" ${this.recommendations.length === 0 ? 'style="display:none"' : ''}>
                        <span class="icon">🤖</span>
                        <span class="badge">${this.recommendations.length}</span>
                    </button>
                    ${this.currentMode === 'demo' ? `
                        <button class="btn-reset-demo" title="Reset Demo Data">
                            <span class="icon">🔄</span>
                        </button>
                    ` : ''}
                    ${!this.getCompanySetup().completed ? `
                        <button class="btn-company-setup" title="Company Setup">
                            <span class="icon">🏢</span>
                        </button>
                    ` : ''}
                </div>
            </div>
            
            <div class="loading-overlay" style="display: none;">
                <div class="loading-spinner"></div>
                <div class="loading-text">Switching modes...</div>
            </div>
        `;
        
        // Insert at the beginning of header
        if (header.firstChild) {
            header.insertBefore(toggleContainer, header.firstChild);
        } else {
            header.appendChild(toggleContainer);
        }
    }
    
    createConfirmationModal() {
        const modal = document.createElement('div');
        modal.className = 'modal data-mode-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title"></h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="mode-comparison">
                        <div class="mode-card demo">
                            <div class="mode-card-header">
                                <span class="mode-icon">🧪</span>
                                <h4>Demo Mode</h4>
                            </div>
                            <div class="mode-features">
                                <ul>
                                    <li>✅ TechFlow Manufacturing Corp data</li>
                                    <li>✅ Full CRUD operations</li>
                                    <li>✅ Workflow testing</li>
                                    <li>✅ Report generation</li>
                                    <li>✅ Training environment</li>
                                    <li>⚠️ Sample data only</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="mode-card production">
                            <div class="mode-card-header">
                                <span class="mode-icon">🚀</span>
                                <h4>Production Mode</h4>
                            </div>
                            <div class="mode-features">
                                <ul>
                                    <li>✅ Real company data</li>
                                    <li>✅ Live operations</li>
                                    <li>✅ Data persistence</li>
                                    <li>✅ Backup systems</li>
                                    <li>✅ Security features</li>
                                    <li>⚠️ Affects real operations</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mode-warning">
                        <div class="warning-icon">⚠️</div>
                        <div class="warning-text"></div>
                    </div>
                    
                    <div class="backup-option">
                        <label class="checkbox-label">
                            <input type="checkbox" id="createBackup" checked>
                            Create backup before switching
                        </label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary modal-cancel">Cancel</button>
                    <button class="btn btn-primary modal-confirm">Switch Mode</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.confirmationModal = modal;
    }
    
    createCompanySetupWizard() {
        const modal = document.createElement('div');
        modal.className = 'modal company-setup-modal';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3 class="modal-title">🏢 Company Setup Wizard</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="setup-progress">
                        <div class="progress-step active" data-step="1">
                            <div class="step-number">1</div>
                            <div class="step-title">Company Info</div>
                        </div>
                        <div class="progress-step" data-step="2">
                            <div class="step-number">2</div>
                            <div class="step-title">Facilities</div>
                        </div>
                        <div class="progress-step" data-step="3">
                            <div class="step-number">3</div>
                            <div class="step-title">Preferences</div>
                        </div>
                        <div class="progress-step" data-step="4">
                            <div class="step-number">4</div>
                            <div class="step-title">Review</div>
                        </div>
                    </div>
                    
                    <div class="setup-content">
                        <!-- Setup steps will be dynamically populated -->
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary setup-prev" style="display: none;">Previous</button>
                    <button class="btn btn-secondary setup-cancel">Cancel</button>
                    <button class="btn btn-primary setup-next">Next</button>
                    <button class="btn btn-success setup-complete" style="display: none;">Complete Setup</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.companySetupModal = modal;
    }
    
    bindEvents() {
        // Toggle switch event
        const switcher = document.getElementById('dataModeSwitcher');
        if (switcher && !switcher.disabled) {
            switcher.addEventListener('change', (e) => {
                const targetMode = e.target.checked ? 'production' : 'demo';
                this.showConfirmationDialog(targetMode);
            });
        }
        
        // Mode info button
        const infoBtn = document.querySelector('.btn-mode-info');
        if (infoBtn) {
            infoBtn.addEventListener('click', () => {
                this.showSystemInformation();
            });
        }
        
        // Recommendations button
        const recBtn = document.querySelector('.btn-recommendations');
        if (recBtn) {
            recBtn.addEventListener('click', () => {
                this.showRecommendations();
            });
        }
        
        // Reset demo button
        const resetBtn = document.querySelector('.btn-reset-demo');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.showResetDemoDialog();
            });
        }
        
        // Company setup button
        const setupBtn = document.querySelector('.btn-company-setup');
        if (setupBtn) {
            setupBtn.addEventListener('click', () => {
                this.showCompanySetupDialog();
            });
        }
        
        // Modal events
        this.bindModalEvents();
    }
    
    bindModalEvents() {
        // Confirmation modal events
        if (this.confirmationModal) {
            const modal = this.confirmationModal;
            
            modal.querySelector('.modal-close').addEventListener('click', () => {
                this.hideModal(modal);
                this.resetToggleSwitch();
            });
            
            modal.querySelector('.modal-cancel').addEventListener('click', () => {
                this.hideModal(modal);
                this.resetToggleSwitch();
            });
            
            modal.querySelector('.modal-confirm').addEventListener('click', () => {
                this.executeModeSwitchFromModal();
            });
            
            // Close on background click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal);
                    this.resetToggleSwitch();
                }
            });
        }
        
        // Company setup modal events
        if (this.companySetupModal) {
            const modal = this.companySetupModal;
            
            modal.querySelector('.modal-close').addEventListener('click', () => {
                this.hideModal(modal);
            });
            
            modal.querySelector('.setup-cancel').addEventListener('click', () => {
                this.hideModal(modal);
            });
            
            modal.querySelector('.setup-next').addEventListener('click', () => {
                this.nextSetupStep();
            });
            
            modal.querySelector('.setup-prev').addEventListener('click', () => {
                this.prevSetupStep();
            });
            
            modal.querySelector('.setup-complete').addEventListener('click', () => {
                this.completeCompanySetup();
            });
        }
    }
    
    showConfirmationDialog(targetMode) {
        if (!this.canSwitchMode()) {
            this.showNotification('Insufficient permissions to switch data mode', 'error');
            this.resetToggleSwitch();
            return;
        }
        
        const modal = this.confirmationModal;
        const title = modal.querySelector('.modal-title');
        const warningText = modal.querySelector('.warning-text');
        
        title.textContent = `Switch to ${targetMode.charAt(0).toUpperCase() + targetMode.slice(1)} Mode?`;
        
        if (targetMode === 'production') {
            warningText.innerHTML = `
                <strong>You are switching to Production Mode.</strong><br>
                This will use your real company data and affect live operations.
                Make sure you have completed company setup and are ready for live use.
            `;
        } else {
            warningText.innerHTML = `
                <strong>You are switching to Demo Mode.</strong><br>
                This will use TechFlow Manufacturing Corp sample data for testing and training.
                All operations will be performed on mock data only.
            `;
        }
        
        modal.targetMode = targetMode;
        this.showModal(modal);
    }
    
    async executeModeSwitchFromModal() {
        const modal = this.confirmationModal;
        const targetMode = modal.targetMode;
        const createBackup = modal.querySelector('#createBackup').checked;
        
        try {
            this.setLoading(true);
            this.hideModal(modal);
            
            const response = await fetch('/api/admin/switch-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: targetMode,
                    backup: createBackup
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentMode = targetMode;
                window.SYSTEM_MODE = targetMode;
                this.updateToggleDisplay();
                this.showNotification(data.message, 'success');
                
                // Reload page after brief delay to ensure all components update
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to switch mode');
            }
            
        } catch (error) {
            console.error('❌ Error switching mode:', error);
            this.showNotification(`Failed to switch mode: ${error.message}`, 'error');
            this.resetToggleSwitch();
        } finally {
            this.setLoading(false);
        }
    }
    
    async showResetDemoDialog() {
        const confirmed = await this.showConfirmDialog(
            'Reset Demo Data?',
            'This will reset the demo database to fresh TechFlow Manufacturing Corp data. All current demo changes will be lost.',
            'Reset Data',
            'destructive'
        );
        
        if (confirmed) {
            await this.resetDemoData();
        }
    }
    
    async resetDemoData() {
        try {
            this.setLoading(true);
            
            const response = await fetch('/api/admin/reset-demo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ confirm: true })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Demo data reset successfully', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to reset demo data');
            }
            
        } catch (error) {
            console.error('❌ Error resetting demo data:', error);
            this.showNotification(`Failed to reset demo data: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    showSystemInformation() {
        // Create system info modal dynamically
        const infoModal = document.createElement('div');
        infoModal.className = 'modal system-info-modal';
        infoModal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3 class="modal-title">📊 System Information</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Loading system information...</div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary modal-close">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(infoModal);
        this.showModal(infoModal);
        
        // Load system information
        this.loadSystemInformation(infoModal);
        
        // Bind close events
        infoModal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.hideModal(infoModal);
                document.body.removeChild(infoModal);
            });
        });
    }
    
    async loadSystemInformation(modal) {
        try {
            const response = await fetch('/api/admin/system-overview');
            const data = await response.json();
            
            if (data.success) {
                const overview = data.overview;
                const body = modal.querySelector('.modal-body');
                
                body.innerHTML = `
                    <div class="system-overview">
                        <div class="overview-section">
                            <h4>Current System Status</h4>
                            <div class="status-grid">
                                <div class="status-item">
                                    <span class="label">Mode:</span>
                                    <span class="value mode-${overview.current_mode}">${overview.current_mode.toUpperCase()}</span>
                                </div>
                                <div class="status-item">
                                    <span class="label">Company Setup:</span>
                                    <span class="value ${overview.settings.company_setup.completed ? 'completed' : 'pending'}">
                                        ${overview.settings.company_setup.completed ? 'Completed' : 'Pending'}
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="overview-section">
                            <h4>Database Information</h4>
                            <div class="db-grid">
                                <div class="db-card demo">
                                    <h5>🧪 Demo Database</h5>
                                    <div class="db-stats">
                                        <div class="stat">
                                            <span class="label">Size:</span>
                                            <span class="value">${overview.demo_mode.database_size_mb} MB</span>
                                        </div>
                                        <div class="stat">
                                            <span class="label">Records:</span>
                                            <span class="value">${this.getTotalRecords(overview.demo_mode.record_counts)}</span>
                                        </div>
                                        <div class="stat">
                                            <span class="label">Status:</span>
                                            <span class="value ${overview.demo_mode.database_exists ? 'active' : 'inactive'}">
                                                ${overview.demo_mode.database_exists ? 'Active' : 'Not Found'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="db-card production">
                                    <h5>🚀 Production Database</h5>
                                    <div class="db-stats">
                                        <div class="stat">
                                            <span class="label">Size:</span>
                                            <span class="value">${overview.production_mode.database_size_mb} MB</span>
                                        </div>
                                        <div class="stat">
                                            <span class="label">Records:</span>
                                            <span class="value">${this.getTotalRecords(overview.production_mode.record_counts)}</span>
                                        </div>
                                        <div class="stat">
                                            <span class="label">Status:</span>
                                            <span class="value ${overview.production_mode.database_exists ? 'active' : 'inactive'}">
                                                ${overview.production_mode.database_exists ? 'Active' : 'Not Found'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${overview.mode_switch_history.length > 0 ? `
                            <div class="overview-section">
                                <h4>Recent Mode Switches</h4>
                                <div class="history-list">
                                    ${overview.mode_switch_history.slice(0, 5).map(entry => `
                                        <div class="history-item">
                                            <span class="timestamp">${new Date(entry.timestamp).toLocaleString()}</span>
                                            <span class="change">${entry.old_mode} → ${entry.new_mode}</span>
                                            <span class="user">User ${entry.user_id}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
            } else {
                throw new Error(data.error || 'Failed to load system information');
            }
            
        } catch (error) {
            console.error('❌ Error loading system information:', error);
            modal.querySelector('.modal-body').innerHTML = `
                <div class="error-message">
                    <span class="error-icon">❌</span>
                    <span class="error-text">Failed to load system information: ${error.message}</span>
                </div>
            `;
        }
    }
    
    showRecommendations() {
        if (this.recommendations.length === 0) {
            this.showNotification('No recommendations available', 'info');
            return;
        }
        
        // Create recommendations modal
        const recModal = document.createElement('div');
        recModal.className = 'modal recommendations-modal';
        recModal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">🤖 AI Recommendations</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="recommendations-list">
                        ${this.recommendations.map(rec => `
                            <div class="recommendation-item ${rec.priority}">
                                <div class="rec-icon">${rec.icon}</div>
                                <div class="rec-content">
                                    <h4 class="rec-title">${rec.title}</h4>
                                    <p class="rec-description">${rec.description}</p>
                                    <div class="rec-priority">Priority: ${rec.priority.toUpperCase()}</div>
                                </div>
                                <div class="rec-actions">
                                    <button class="btn btn-sm btn-primary" data-action="${rec.action}">
                                        Take Action
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary modal-close">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(recModal);
        this.showModal(recModal);
        
        // Bind events
        recModal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.hideModal(recModal);
                document.body.removeChild(recModal);
            });
        });
        
        recModal.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.executeRecommendationAction(e.target.dataset.action);
                this.hideModal(recModal);
                document.body.removeChild(recModal);
            });
        });
    }
    
    executeRecommendationAction(action) {
        switch (action) {
            case 'switch_to_production':
                document.getElementById('dataModeSwitcher').checked = true;
                document.getElementById('dataModeSwitcher').dispatchEvent(new Event('change'));
                break;
            case 'switch_to_demo':
                document.getElementById('dataModeSwitcher').checked = false;
                document.getElementById('dataModeSwitcher').dispatchEvent(new Event('change'));
                break;
            case 'create_backup':
                this.createBackup();
                break;
            case 'reset_demo_data':
                this.showResetDemoDialog();
                break;
            default:
                this.showNotification(`Action not implemented: ${action}`, 'warning');
        }
    }
    
    async createBackup() {
        try {
            this.setLoading(true);
            
            const response = await fetch('/api/admin/create-backup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: this.currentMode,
                    reason: 'manual_backup'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Backup created successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to create backup');
            }
            
        } catch (error) {
            console.error('❌ Error creating backup:', error);
            this.showNotification(`Failed to create backup: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    updateToggleDisplay() {
        const indicator = document.querySelector('.mode-indicator');
        const switcher = document.getElementById('dataModeSwitcher');
        const badge = document.querySelector('.mode-badge');
        const icon = document.querySelector('.mode-icon');
        const text = document.querySelector('.mode-text');
        
        if (indicator) {
            indicator.className = `mode-indicator ${this.currentMode}`;
        }
        
        if (switcher) {
            switcher.checked = this.currentMode === 'production';
        }
        
        if (badge) {
            badge.textContent = this.currentMode.toUpperCase();
            badge.className = `mode-badge ${this.currentMode}`;
        }
        
        if (icon) {
            icon.textContent = this.currentMode === 'demo' ? '🧪' : '🚀';
        }
        
        if (text) {
            text.textContent = this.currentMode === 'demo' ? 'Demo Mode' : 'Production Mode';
        }
    }
    
    resetToggleSwitch() {
        const switcher = document.getElementById('dataModeSwitcher');
        if (switcher) {
            switcher.checked = this.currentMode === 'production';
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const overlay = document.querySelector('.loading-overlay');
        const switcher = document.getElementById('dataModeSwitcher');
        
        if (overlay) {
            overlay.style.display = loading ? 'flex' : 'none';
        }
        
        if (switcher) {
            switcher.disabled = loading;
        }
    }
    
    showModal(modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Animate in
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }
    
    hideModal(modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getNotificationIcon(type)}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add to page
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
    
    getNotificationIcon(type) {
        switch (type) {
            case 'success': return '✅';
            case 'error': return '❌';
            case 'warning': return '⚠️';
            case 'info': 
            default: return 'ℹ️';
        }
    }
    
    canSwitchMode() {
        if (!this.user) return false;
        
        const allowedRoles = ['Administrator', 'Manager'];
        return allowedRoles.includes(this.user.role);
    }
    
    getCompanySetup() {
        // This would normally come from the API, but for now return a default
        return { completed: false };
    }
    
    getTotalRecords(recordCounts) {
        if (!recordCounts || typeof recordCounts !== 'object') return 0;
        return Object.values(recordCounts).reduce((sum, count) => sum + (count || 0), 0);
    }
    
    async showConfirmDialog(title, message, confirmText = 'Confirm', type = 'default') {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'modal confirm-dialog';
            dialog.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">${title}</h3>
                    </div>
                    <div class="modal-body">
                        <p class="confirm-message">${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary confirm-cancel">Cancel</button>
                        <button class="btn ${type === 'destructive' ? 'btn-danger' : 'btn-primary'} confirm-ok">
                            ${confirmText}
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(dialog);
            this.showModal(dialog);
            
            dialog.querySelector('.confirm-cancel').addEventListener('click', () => {
                this.hideModal(dialog);
                setTimeout(() => document.body.removeChild(dialog), 300);
                resolve(false);
            });
            
            dialog.querySelector('.confirm-ok').addEventListener('click', () => {
                this.hideModal(dialog);
                setTimeout(() => document.body.removeChild(dialog), 300);
                resolve(true);
            });
        });
    }
    
    startStatusUpdates() {
        // Periodically check for system updates
        setInterval(async () => {
            try {
                await this.loadSystemStatus();
                this.updateToggleDisplay();
            } catch (error) {
                console.debug('Status update failed:', error);
            }
        }, 30000); // Every 30 seconds
    }
    
    showCompanySetupDialog() {
        // Show the company setup wizard
        if (window.CompanySetupWizard) {
            const wizard = new window.CompanySetupWizard();
            wizard.show();
        } else {
            // Load the wizard script dynamically if not available
            this.loadCompanySetupWizard();
        }
    }
    
    async loadCompanySetupWizard() {
        try {
            // Load the company setup wizard script
            const script = document.createElement('script');
            script.src = '/static/js/company-setup-wizard.js';
            script.onload = () => {
                const wizard = new window.CompanySetupWizard();
                wizard.show();
            };
            script.onerror = () => {
                this.showNotification('Failed to load company setup wizard', 'error');
            };
            document.head.appendChild(script);
        } catch (error) {
            console.error('Error loading company setup wizard:', error);
            this.showNotification('Failed to load company setup wizard', 'error');
        }
    }
    
    nextSetupStep() {
        // Company setup wizard step navigation
        console.log('Next setup step');
    }
    
    prevSetupStep() {
        // Company setup wizard step navigation
        console.log('Previous setup step');
    }
    
    completeCompanySetup() {
        // Complete company setup
        console.log('Complete company setup');
    }
}

// Initialize the data mode toggle when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're not in a modal or popup
    if (window.self === window.top) {
        window.dataModeToggle = new DataModeToggle();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataModeToggle;
}