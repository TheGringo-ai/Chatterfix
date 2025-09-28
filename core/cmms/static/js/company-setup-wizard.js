/**
 * ChatterFix CMMS Company Setup Wizard
 * Guided setup for new companies switching to production mode
 * Features: Multi-step wizard, validation, data migration
 */

class CompanySetupWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.setupData = {
            company_info: {},
            facilities: [],
            preferences: {},
            migration_options: {}
        };
        
        this.steps = [
            {
                id: 'company_info',
                title: 'Company Information',
                description: 'Tell us about your company',
                template: 'companyInfoTemplate'
            },
            {
                id: 'facilities',
                title: 'Facilities & Locations',
                description: 'Add your facilities and locations',
                template: 'facilitiesTemplate'
            },
            {
                id: 'preferences',
                title: 'System Preferences',
                description: 'Configure system settings',
                template: 'preferencesTemplate'
            },
            {
                id: 'review',
                title: 'Review & Complete',
                description: 'Review your setup and complete',
                template: 'reviewTemplate'
            }
        ];
    }
    
    async show() {
        try {
            // Load wizard data from API
            await this.loadWizardData();
            
            // Create modal
            this.createWizardModal();
            
            // Show first step
            this.showStep(1);
            
            // Bind events
            this.bindEvents();
            
        } catch (error) {
            console.error('❌ Error showing company setup wizard:', error);
            this.showNotification('Failed to load setup wizard', 'error');
        }
    }
    
    async loadWizardData() {
        try {
            const response = await fetch('/api/admin/company-setup');
            const data = await response.json();
            
            if (data.success) {
                this.wizardData = data.wizard;
                this.setupData = { ...this.setupData, ...data.wizard.current_setup };
            } else {
                throw new Error(data.error || 'Failed to load wizard data');
            }
        } catch (error) {
            console.error('Error loading wizard data:', error);
            throw error;
        }
    }
    
    createWizardModal() {
        const modal = document.createElement('div');
        modal.className = 'modal company-setup-wizard';
        modal.innerHTML = `
            <div class="modal-content wizard-content">
                <div class="modal-header">
                    <h3 class="modal-title">🏢 Company Setup Wizard</h3>
                    <button class="modal-close">&times;</button>
                </div>
                
                <div class="wizard-progress">
                    ${this.steps.map((step, index) => `
                        <div class="progress-step ${index === 0 ? 'active' : ''}" data-step="${index + 1}">
                            <div class="step-number">${index + 1}</div>
                            <div class="step-info">
                                <div class="step-title">${step.title}</div>
                                <div class="step-description">${step.description}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="wizard-body">
                    <div class="step-content">
                        <!-- Step content will be populated here -->
                    </div>
                </div>
                
                <div class="wizard-footer">
                    <button class="btn btn-secondary wizard-prev" style="display: none;">
                        ← Previous
                    </button>
                    <div class="wizard-actions">
                        <button class="btn btn-secondary wizard-cancel">Cancel</button>
                        <button class="btn btn-primary wizard-next">
                            Next →
                        </button>
                        <button class="btn btn-success wizard-complete" style="display: none;">
                            🚀 Complete Setup
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.modal = modal;
        this.showModal();
    }
    
    showStep(stepNumber) {
        this.currentStep = stepNumber;
        const step = this.steps[stepNumber - 1];
        
        // Update progress indicators
        this.updateProgressIndicators();
        
        // Update step content
        this.updateStepContent(step);
        
        // Update navigation buttons
        this.updateNavigationButtons();
    }
    
    updateProgressIndicators() {
        const steps = this.modal.querySelectorAll('.progress-step');
        steps.forEach((stepEl, index) => {
            stepEl.classList.remove('active', 'completed');
            
            if (index + 1 === this.currentStep) {
                stepEl.classList.add('active');
            } else if (index + 1 < this.currentStep) {
                stepEl.classList.add('completed');
            }
        });
    }
    
    updateStepContent(step) {
        const contentEl = this.modal.querySelector('.step-content');
        
        switch (step.id) {
            case 'company_info':
                contentEl.innerHTML = this.getCompanyInfoTemplate();
                break;
            case 'facilities':
                contentEl.innerHTML = this.getFacilitiesTemplate();
                break;
            case 'preferences':
                contentEl.innerHTML = this.getPreferencesTemplate();
                break;
            case 'review':
                contentEl.innerHTML = this.getReviewTemplate();
                break;
        }
        
        // Populate existing data
        this.populateStepData(step.id);
        
        // Bind step-specific events
        this.bindStepEvents(step.id);
    }
    
    getCompanyInfoTemplate() {
        return `
            <div class="step-form company-info-form">
                <h4>📋 Company Information</h4>
                <p class="step-description">
                    Provide basic information about your company to configure the CMMS system.
                </p>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="company-name">Company Name *</label>
                        <input type="text" id="company-name" name="company_name" required 
                               placeholder="Enter your company name">
                    </div>
                    
                    <div class="form-group">
                        <label for="industry">Industry *</label>
                        <select id="industry" name="industry" required>
                            <option value="">Select your industry</option>
                            ${this.wizardData?.options?.industries?.map(industry => 
                                `<option value="${industry}">${industry}</option>`
                            ).join('') || ''}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="employee-count">Employee Count</label>
                        <select id="employee-count" name="employee_count">
                            <option value="">Select employee range</option>
                            ${this.wizardData?.options?.employee_ranges?.map(range => 
                                `<option value="${range.value}">${range.label}</option>`
                            ).join('') || ''}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="website">Website</label>
                        <input type="url" id="website" name="website" 
                               placeholder="https://your-company.com">
                    </div>
                    
                    <div class="form-group full-width">
                        <label for="description">Company Description</label>
                        <textarea id="description" name="description" rows="3"
                                  placeholder="Brief description of your company and operations"></textarea>
                    </div>
                </div>
            </div>
        `;
    }
    
    getFacilitiesTemplate() {
        return `
            <div class="step-form facilities-form">
                <h4>🏭 Facilities & Locations</h4>
                <p class="step-description">
                    Add your facilities and locations where the CMMS will be used.
                </p>
                
                <div class="facilities-list">
                    <div id="facilities-container">
                        <!-- Facilities will be added here -->
                    </div>
                    
                    <button type="button" class="btn btn-outline add-facility">
                        ➕ Add Facility
                    </button>
                </div>
                
                <div class="facility-template" style="display: none;">
                    <div class="facility-item">
                        <div class="facility-header">
                            <h5>Facility</h5>
                            <button type="button" class="btn-remove-facility">❌</button>
                        </div>
                        
                        <div class="form-grid">
                            <div class="form-group">
                                <label>Facility Name *</label>
                                <input type="text" name="name" required 
                                       placeholder="e.g., Main Manufacturing Plant">
                            </div>
                            
                            <div class="form-group">
                                <label>Facility Type</label>
                                <select name="type">
                                    ${this.wizardData?.options?.facility_types?.map(type => 
                                        `<option value="${type}">${type}</option>`
                                    ).join('') || ''}
                                </select>
                            </div>
                            
                            <div class="form-group full-width">
                                <label>Address</label>
                                <input type="text" name="address" 
                                       placeholder="Street address">
                            </div>
                            
                            <div class="form-group">
                                <label>City</label>
                                <input type="text" name="city" placeholder="City">
                            </div>
                            
                            <div class="form-group">
                                <label>State/Province</label>
                                <input type="text" name="state" placeholder="State">
                            </div>
                            
                            <div class="form-group">
                                <label>ZIP/Postal Code</label>
                                <input type="text" name="zip" placeholder="ZIP">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getPreferencesTemplate() {
        return `
            <div class="step-form preferences-form">
                <h4>⚙️ System Preferences</h4>
                <p class="step-description">
                    Configure system settings and preferences for your organization.
                </p>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="timezone">Time Zone</label>
                        <select id="timezone" name="timezone">
                            <option value="America/New_York">Eastern Time (UTC-5)</option>
                            <option value="America/Chicago">Central Time (UTC-6)</option>
                            <option value="America/Denver">Mountain Time (UTC-7)</option>
                            <option value="America/Los_Angeles">Pacific Time (UTC-8)</option>
                            <option value="UTC">UTC</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="currency">Currency</label>
                        <select id="currency" name="currency">
                            <option value="USD">US Dollar (USD)</option>
                            <option value="EUR">Euro (EUR)</option>
                            <option value="GBP">British Pound (GBP)</option>
                            <option value="CAD">Canadian Dollar (CAD)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="units">Unit System</label>
                        <select id="units" name="units">
                            <option value="imperial">Imperial (feet, pounds)</option>
                            <option value="metric">Metric (meters, kilograms)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="work-week">Work Week</label>
                        <select id="work-week" name="work_week">
                            <option value="5">5 days (Mon-Fri)</option>
                            <option value="6">6 days (Mon-Sat)</option>
                            <option value="7">7 days (Daily operations)</option>
                        </select>
                    </div>
                </div>
                
                <div class="preferences-section">
                    <h5>📧 Notification Preferences</h5>
                    <div class="checkbox-group">
                        <label class="checkbox-label">
                            <input type="checkbox" name="email_notifications" checked>
                            Enable email notifications
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" name="urgent_alerts" checked>
                            Urgent alerts for critical work orders
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" name="maintenance_reminders">
                            Preventive maintenance reminders
                        </label>
                    </div>
                </div>
                
                <div class="preferences-section">
                    <h5>🔧 Maintenance Settings</h5>
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="default-priority">Default Work Order Priority</label>
                            <select id="default-priority" name="default_priority">
                                <option value="Low">Low</option>
                                <option value="Medium" selected>Medium</option>
                                <option value="High">High</option>
                                <option value="Critical">Critical</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="auto-assign">Auto-assign Work Orders</label>
                            <select id="auto-assign" name="auto_assign">
                                <option value="false">Manual assignment</option>
                                <option value="true">Auto-assign by skill</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getReviewTemplate() {
        return `
            <div class="step-form review-form">
                <h4>📋 Review & Complete Setup</h4>
                <p class="step-description">
                    Review your configuration and complete the setup process.
                </p>
                
                <div class="review-sections">
                    <div class="review-section">
                        <h5>🏢 Company Information</h5>
                        <div class="review-grid" id="review-company-info">
                            <!-- Company info will be populated here -->
                        </div>
                    </div>
                    
                    <div class="review-section">
                        <h5>🏭 Facilities</h5>
                        <div class="review-facilities" id="review-facilities">
                            <!-- Facilities will be populated here -->
                        </div>
                    </div>
                    
                    <div class="review-section">
                        <h5>⚙️ Preferences</h5>
                        <div class="review-grid" id="review-preferences">
                            <!-- Preferences will be populated here -->
                        </div>
                    </div>
                </div>
                
                <div class="migration-options">
                    <h5>📊 Data Migration Options</h5>
                    <div class="migration-choice">
                        <label class="radio-label">
                            <input type="radio" name="migration_type" value="fresh" checked>
                            <div class="radio-content">
                                <strong>Fresh Start</strong>
                                <p>Start with empty production database (recommended for new implementations)</p>
                            </div>
                        </label>
                        
                        <label class="radio-label">
                            <input type="radio" name="migration_type" value="copy_demo">
                            <div class="radio-content">
                                <strong>Copy Demo Data</strong>
                                <p>Copy current demo data as a starting template (useful for testing)</p>
                            </div>
                        </label>
                    </div>
                </div>
                
                <div class="setup-warning">
                    <div class="warning-icon">⚠️</div>
                    <div class="warning-content">
                        <strong>Important:</strong> Completing this setup will switch the system to production mode 
                        and configure your company data. Make sure all information is correct.
                    </div>
                </div>
            </div>
        `;
    }
    
    populateStepData(stepId) {
        switch (stepId) {
            case 'company_info':
                this.populateCompanyInfo();
                break;
            case 'facilities':
                this.populateFacilities();
                break;
            case 'preferences':
                this.populatePreferences();
                break;
            case 'review':
                this.populateReview();
                break;
        }
    }
    
    populateCompanyInfo() {
        const data = this.setupData.company_info || {};
        
        Object.keys(data).forEach(key => {
            const element = this.modal.querySelector(`[name="${key}"]`);
            if (element) {
                element.value = data[key] || '';
            }
        });
    }
    
    populateFacilities() {
        const container = this.modal.querySelector('#facilities-container');
        const facilities = this.setupData.facilities || [];
        
        // Clear existing facilities
        container.innerHTML = '';
        
        // Add existing facilities
        facilities.forEach((facility, index) => {
            this.addFacilityForm(facility);
        });
        
        // Add one empty facility if none exist
        if (facilities.length === 0) {
            this.addFacilityForm();
        }
    }
    
    populatePreferences() {
        const data = this.setupData.preferences || {};
        
        Object.keys(data).forEach(key => {
            const element = this.modal.querySelector(`[name="${key}"]`);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = data[key] || false;
                } else {
                    element.value = data[key] || '';
                }
            }
        });
    }
    
    populateReview() {
        // Populate company info review
        const companyInfoEl = this.modal.querySelector('#review-company-info');
        companyInfoEl.innerHTML = this.generateReviewItems(this.setupData.company_info);
        
        // Populate facilities review
        const facilitiesEl = this.modal.querySelector('#review-facilities');
        facilitiesEl.innerHTML = this.setupData.facilities?.map(facility => `
            <div class="review-facility">
                <strong>${facility.name || 'Unnamed Facility'}</strong>
                <span>${facility.type || 'N/A'}</span>
                <span>${facility.address || 'No address'}</span>
            </div>
        `).join('') || '<p>No facilities added</p>';
        
        // Populate preferences review
        const preferencesEl = this.modal.querySelector('#review-preferences');
        preferencesEl.innerHTML = this.generateReviewItems(this.setupData.preferences);
    }
    
    generateReviewItems(data) {
        if (!data || Object.keys(data).length === 0) {
            return '<p>No data provided</p>';
        }
        
        return Object.entries(data).map(([key, value]) => `
            <div class="review-item">
                <span class="review-label">${this.formatLabel(key)}:</span>
                <span class="review-value">${value || 'Not specified'}</span>
            </div>
        `).join('');
    }
    
    formatLabel(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    bindStepEvents(stepId) {
        switch (stepId) {
            case 'facilities':
                this.bindFacilitiesEvents();
                break;
        }
    }
    
    bindFacilitiesEvents() {
        // Add facility button
        const addBtn = this.modal.querySelector('.add-facility');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.addFacilityForm();
            });
        }
    }
    
    addFacilityForm(facilityData = {}) {
        const container = this.modal.querySelector('#facilities-container');
        const template = this.modal.querySelector('.facility-template').innerHTML;
        
        const facilityEl = document.createElement('div');
        facilityEl.innerHTML = template;
        
        // Populate data if provided
        Object.keys(facilityData).forEach(key => {
            const input = facilityEl.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = facilityData[key] || '';
            }
        });
        
        // Bind remove button
        const removeBtn = facilityEl.querySelector('.btn-remove-facility');
        removeBtn.addEventListener('click', () => {
            facilityEl.remove();
        });
        
        container.appendChild(facilityEl);
    }
    
    updateNavigationButtons() {
        const prevBtn = this.modal.querySelector('.wizard-prev');
        const nextBtn = this.modal.querySelector('.wizard-next');
        const completeBtn = this.modal.querySelector('.wizard-complete');
        
        // Show/hide previous button
        if (this.currentStep > 1) {
            prevBtn.style.display = 'block';
        } else {
            prevBtn.style.display = 'none';
        }
        
        // Show/hide next vs complete button
        if (this.currentStep < this.totalSteps) {
            nextBtn.style.display = 'block';
            completeBtn.style.display = 'none';
        } else {
            nextBtn.style.display = 'none';
            completeBtn.style.display = 'block';
        }
    }
    
    bindEvents() {
        // Navigation buttons
        this.modal.querySelector('.wizard-prev').addEventListener('click', () => {
            this.previousStep();
        });
        
        this.modal.querySelector('.wizard-next').addEventListener('click', () => {
            this.nextStep();
        });
        
        this.modal.querySelector('.wizard-complete').addEventListener('click', () => {
            this.completeSetup();
        });
        
        this.modal.querySelector('.wizard-cancel').addEventListener('click', () => {
            this.cancel();
        });
        
        this.modal.querySelector('.modal-close').addEventListener('click', () => {
            this.cancel();
        });
        
        // Form inputs - save data on change
        this.modal.addEventListener('change', (e) => {
            if (e.target.matches('input, select, textarea')) {
                this.saveStepData();
            }
        });
    }
    
    previousStep() {
        if (this.currentStep > 1) {
            this.saveStepData();
            this.showStep(this.currentStep - 1);
        }
    }
    
    nextStep() {
        if (this.validateCurrentStep()) {
            this.saveStepData();
            if (this.currentStep < this.totalSteps) {
                this.showStep(this.currentStep + 1);
            }
        }
    }
    
    validateCurrentStep() {
        const stepId = this.steps[this.currentStep - 1].id;
        
        switch (stepId) {
            case 'company_info':
                return this.validateCompanyInfo();
            case 'facilities':
                return this.validateFacilities();
            case 'preferences':
                return this.validatePreferences();
            case 'review':
                return true;
            default:
                return true;
        }
    }
    
    validateCompanyInfo() {
        const companyName = this.modal.querySelector('#company-name').value.trim();
        const industry = this.modal.querySelector('#industry').value;
        
        if (!companyName) {
            this.showNotification('Company name is required', 'error');
            return false;
        }
        
        if (!industry) {
            this.showNotification('Please select an industry', 'error');
            return false;
        }
        
        return true;
    }
    
    validateFacilities() {
        const facilities = this.modal.querySelectorAll('.facility-item');
        
        for (let facility of facilities) {
            const name = facility.querySelector('[name="name"]').value.trim();
            if (!name) {
                this.showNotification('All facilities must have a name', 'error');
                return false;
            }
        }
        
        return true;
    }
    
    validatePreferences() {
        return true; // All preferences are optional
    }
    
    saveStepData() {
        const stepId = this.steps[this.currentStep - 1].id;
        
        switch (stepId) {
            case 'company_info':
                this.saveCompanyInfo();
                break;
            case 'facilities':
                this.saveFacilities();
                break;
            case 'preferences':
                this.savePreferences();
                break;
        }
    }
    
    saveCompanyInfo() {
        const form = this.modal.querySelector('.company-info-form');
        const formData = new FormData(form);
        
        this.setupData.company_info = {};
        for (let [key, value] of formData.entries()) {
            this.setupData.company_info[key] = value;
        }
    }
    
    saveFacilities() {
        const facilityItems = this.modal.querySelectorAll('.facility-item');
        this.setupData.facilities = [];
        
        facilityItems.forEach(item => {
            const facility = {};
            const inputs = item.querySelectorAll('input, select');
            
            inputs.forEach(input => {
                if (input.name && input.value.trim()) {
                    facility[input.name] = input.value.trim();
                }
            });
            
            if (facility.name) {
                this.setupData.facilities.push(facility);
            }
        });
    }
    
    savePreferences() {
        const form = this.modal.querySelector('.preferences-form');
        const formData = new FormData(form);
        
        this.setupData.preferences = {};
        for (let [key, value] of formData.entries()) {
            this.setupData.preferences[key] = value;
        }
        
        // Handle checkboxes
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            this.setupData.preferences[checkbox.name] = checkbox.checked;
        });
        
        // Handle migration type
        const migrationRadio = this.modal.querySelector('input[name="migration_type"]:checked');
        if (migrationRadio) {
            this.setupData.migration_options = {
                type: migrationRadio.value
            };
        }
    }
    
    async completeSetup() {
        try {
            // Save current step data
            this.saveStepData();
            
            // Show loading
            this.setLoading(true);
            
            // Submit setup data
            const response = await fetch('/api/admin/company-setup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    setup: this.setupData
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                this.showNotification('Company setup completed successfully!', 'success');
                
                // Close wizard
                this.hideModal();
                
                // Optionally switch to production mode
                if (this.setupData.migration_options?.type === 'copy_demo') {
                    await this.switchToProductionWithData();
                } else {
                    await this.switchToProductionMode();
                }
                
            } else {
                throw new Error(result.error || 'Setup failed');
            }
            
        } catch (error) {
            console.error('❌ Error completing setup:', error);
            this.showNotification(`Setup failed: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    async switchToProductionMode() {
        try {
            const response = await fetch('/api/admin/switch-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: 'production',
                    backup: true
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Switched to production mode successfully!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                throw new Error(result.error || 'Mode switch failed');
            }
            
        } catch (error) {
            console.error('❌ Error switching to production mode:', error);
            this.showNotification(`Failed to switch to production mode: ${error.message}`, 'error');
        }
    }
    
    async switchToProductionWithData() {
        // This would involve data migration logic
        await this.switchToProductionMode();
    }
    
    cancel() {
        if (confirm('Are you sure you want to cancel the setup? Your progress will be lost.')) {
            this.hideModal();
            document.body.removeChild(this.modal);
        }
    }
    
    setLoading(loading) {
        const completeBtn = this.modal.querySelector('.wizard-complete');
        const nextBtn = this.modal.querySelector('.wizard-next');
        
        if (loading) {
            completeBtn.disabled = true;
            completeBtn.innerHTML = '⏳ Setting up...';
            nextBtn.disabled = true;
        } else {
            completeBtn.disabled = false;
            completeBtn.innerHTML = '🚀 Complete Setup';
            nextBtn.disabled = false;
        }
    }
    
    showModal() {
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        setTimeout(() => {
            this.modal.classList.add('show');
        }, 10);
    }
    
    hideModal() {
        this.modal.classList.remove('show');
        document.body.style.overflow = '';
        
        setTimeout(() => {
            this.modal.style.display = 'none';
        }, 300);
    }
    
    showNotification(message, type = 'info') {
        // Use the same notification system as data mode toggle
        if (window.dataModeToggle && window.dataModeToggle.showNotification) {
            window.dataModeToggle.showNotification(message, type);
        } else {
            alert(message); // Fallback
        }
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CompanySetupWizard;
} else {
    window.CompanySetupWizard = CompanySetupWizard;
}