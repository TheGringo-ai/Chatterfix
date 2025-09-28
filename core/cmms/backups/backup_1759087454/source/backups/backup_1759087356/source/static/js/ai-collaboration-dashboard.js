/**
 * ChatterFix CMMS - AI Collaboration Dashboard
 * JavaScript for managing AI collaboration system interface
 */

class AICollaborationDashboard {
    constructor() {
        this.currentAI = 'claude'; // Default AI model
        this.currentSession = null;
        this.refreshInterval = 30000; // 30 seconds
        this.autoRefreshTimer = null;
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing AI Collaboration Dashboard...');
        
        // Initialize UI components
        this.setupEventListeners();
        await this.loadSystemStatus();
        await this.loadAvailableAIModels();
        
        // Start auto-refresh
        this.startAutoRefresh();
        
        console.log('✅ AI Collaboration Dashboard ready');
    }
    
    setupEventListeners() {
        // AI Model Selection
        const aiSelect = document.getElementById('ai-model-select');
        if (aiSelect) {
            aiSelect.addEventListener('change', (e) => {
                this.currentAI = e.target.value;
                this.onAIModelChanged();
            });
        }
        
        // Session Management
        const startSessionBtn = document.getElementById('start-session-btn');
        if (startSessionBtn) {
            startSessionBtn.addEventListener('click', () => this.startSession());
        }
        
        const endSessionBtn = document.getElementById('end-session-btn');
        if (endSessionBtn) {
            endSessionBtn.addEventListener('click', () => this.endSession());
        }
        
        // Task Management
        const createTaskBtn = document.getElementById('create-task-btn');
        if (createTaskBtn) {
            createTaskBtn.addEventListener('click', () => this.showCreateTaskModal());
        }
        
        const refreshBtn = document.getElementById('refresh-dashboard-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshDashboard());
        }
        
        // Knowledge Query
        const queryForm = document.getElementById('knowledge-query-form');
        if (queryForm) {
            queryForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.queryKnowledge();
            });
        }
        
        // Deployment Safety
        const safetyCheckBtn = document.getElementById('deployment-safety-btn');
        if (safetyCheckBtn) {
            safetyCheckBtn.addEventListener('click', () => this.runDeploymentSafetyCheck());
        }
        
        // Context Management
        const captureContextBtn = document.getElementById('capture-context-btn');
        if (captureContextBtn) {
            captureContextBtn.addEventListener('click', () => this.captureCurrentContext());
        }
    }
    
    async loadAvailableAIModels() {
        try {
            const response = await fetch('/api/ai-collaboration/ai-models');
            const data = await response.json();
            
            if (data.success) {
                this.populateAIModelSelect(data.available_models);
            }
        } catch (error) {
            console.error('Error loading AI models:', error);
            this.showNotification('Error loading AI models', 'error');
        }
    }
    
    populateAIModelSelect(models) {
        const select = document.getElementById('ai-model-select');
        if (!select) return;
        
        select.innerHTML = '';
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.model;
            option.textContent = `${model.model.toUpperCase()} - ${model.role}`;
            option.title = model.description;
            select.appendChild(option);
        });
        
        // Set current AI
        select.value = this.currentAI;
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/ai-collaboration/status');
            const data = await response.json();
            
            this.updateSystemStatusDisplay(data);
        } catch (error) {
            console.error('Error loading system status:', error);
            this.showNotification('Error loading system status', 'error');
        }
    }
    
    updateSystemStatusDisplay(statusData) {
        // Update system health indicators
        this.updateElement('system-health-status', 
            statusData.system_health?.deployment_status || 'Unknown');
        
        // Update active sessions
        const activeSessions = statusData.active_sessions || {};
        this.updateElement('active-sessions-count', 
            Object.values(activeSessions).reduce((a, b) => a + b, 0));
        
        // Update task summary
        const taskSummary = statusData.task_summary || {};
        this.updateElement('pending-tasks-count', taskSummary.pending || 0);
        this.updateElement('in-progress-tasks-count', taskSummary.in_progress || 0);
        this.updateElement('completed-tasks-count', taskSummary.completed || 0);
        
        // Update pending handoffs
        this.updateElement('pending-handoffs-count', statusData.pending_handoffs || 0);
        
        // Update knowledge base size
        this.updateElement('knowledge-entries-count', statusData.knowledge_base_entries || 0);
        
        // Update last updated timestamp
        this.updateElement('last-updated', new Date().toLocaleTimeString());
    }
    
    async onAIModelChanged() {
        console.log(`🔄 Switched to AI model: ${this.currentAI}`);
        
        // Load tasks for the new AI model
        await this.loadAITasks();
        await this.loadTaskRecommendations();
        
        // Update UI to reflect current AI
        this.updateCurrentAIDisplay();
    }
    
    updateCurrentAIDisplay() {
        this.updateElement('current-ai-display', this.currentAI.toUpperCase());
        
        // Update AI-specific UI elements
        const aiInfo = document.getElementById('current-ai-info');
        if (aiInfo) {
            const roles = {
                'claude': 'Architecture & Code Quality',
                'chatgpt': 'Frontend & User Experience',
                'grok': 'Debugging & Performance',
                'llama': 'Data & Analytics'
            };
            aiInfo.textContent = roles[this.currentAI] || 'General AI Assistant';
        }
    }
    
    async startSession() {
        try {
            const contextNotes = prompt('Enter context notes for this session (optional):') || '';
            
            const response = await fetch('/api/ai-collaboration/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ai_model: this.currentAI,
                    context_notes: contextNotes
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session_id;
                this.showNotification(`Session started for ${this.currentAI.toUpperCase()}`, 'success');
                this.updateSessionUI(true);
                
                // Display session data
                this.displaySessionData(data.session_data);
            } else {
                this.showNotification('Failed to start session', 'error');
            }
        } catch (error) {
            console.error('Error starting session:', error);
            this.showNotification('Error starting session', 'error');
        }
    }
    
    async endSession() {
        if (!this.currentSession) {
            this.showNotification('No active session to end', 'warning');
            return;
        }
        
        try {
            const handoffNotes = prompt('Enter handoff notes (optional):') || '';
            const nextAI = prompt('Hand off to which AI? (claude/chatgpt/grok/llama, or leave empty):') || null;
            
            const response = await fetch('/api/ai-collaboration/session/end', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession,
                    handoff_notes: handoffNotes,
                    next_ai: nextAI
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Session ended for ${this.currentAI.toUpperCase()}`, 'success');
                this.currentSession = null;
                this.updateSessionUI(false);
                
                if (data.session_summary.handoff_initiated) {
                    this.showNotification(`Handoff initiated to ${nextAI}`, 'info');
                }
            } else {
                this.showNotification('Failed to end session', 'error');
            }
        } catch (error) {
            console.error('Error ending session:', error);
            this.showNotification('Error ending session', 'error');
        }
    }
    
    updateSessionUI(sessionActive) {
        const startBtn = document.getElementById('start-session-btn');
        const endBtn = document.getElementById('end-session-btn');
        
        if (startBtn) startBtn.disabled = sessionActive;
        if (endBtn) endBtn.disabled = !sessionActive;
        
        const sessionStatus = document.getElementById('session-status');
        if (sessionStatus) {
            sessionStatus.textContent = sessionActive ? 'Active' : 'Inactive';
            sessionStatus.className = sessionActive ? 'status-active' : 'status-inactive';
        }
    }
    
    async loadAITasks() {
        try {
            const response = await fetch(`/api/ai-collaboration/tasks/${this.currentAI}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayTasks(data.tasks);
            }
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    }
    
    displayTasks(tasks) {
        const tasksContainer = document.getElementById('ai-tasks-list');
        if (!tasksContainer) return;
        
        tasksContainer.innerHTML = '';
        
        if (tasks.length === 0) {
            tasksContainer.innerHTML = '<p class=\"no-tasks\">No active tasks for this AI model.</p>';
            return;
        }
        
        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            tasksContainer.appendChild(taskElement);
        });
    }
    
    createTaskElement(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task-item priority-${task.priority}`;
        taskDiv.innerHTML = `
            <div class="task-header">
                <h4>${task.title}</h4>
                <span class="task-status status-${task.status}">${task.status.replace('_', ' ')}</span>
            </div>
            <div class="task-details">
                <p>${task.description}</p>
                <div class="task-meta">
                    <span class="priority">Priority: ${task.priority}</span>
                    <span class="effort">Effort: ${task.estimated_effort}h</span>
                    ${task.due_date ? `<span class="due-date">Due: ${new Date(task.due_date).toLocaleDateString()}</span>` : ''}
                </div>
            </div>
            <div class="task-actions">
                <button onclick="aiDashboard.updateTaskStatus('${task.task_id}', 'in_progress')" 
                        class="btn btn-sm btn-primary">Start</button>
                <button onclick="aiDashboard.updateTaskStatus('${task.task_id}', 'completed')" 
                        class="btn btn-sm btn-success">Complete</button>
                <button onclick="aiDashboard.viewTaskDetails('${task.task_id}')" 
                        class="btn btn-sm btn-secondary">Details</button>
            </div>
        `;
        
        return taskDiv;
    }
    
    async updateTaskStatus(taskId, newStatus) {
        try {
            const notes = prompt('Add notes for this status update (optional):') || '';
            
            const response = await fetch('/api/ai-collaboration/task/update', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_id: taskId,
                    status: newStatus,
                    notes: notes
                }),
                params: new URLSearchParams({ ai_model: this.currentAI })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Task updated successfully', 'success');
                await this.loadAITasks(); // Refresh tasks
            } else {
                this.showNotification('Failed to update task', 'error');
            }
        } catch (error) {
            console.error('Error updating task:', error);
            this.showNotification('Error updating task', 'error');
        }
    }
    
    async loadTaskRecommendations() {
        try {
            const response = await fetch(`/api/ai-collaboration/tasks/${this.currentAI}/recommendations`);
            const data = await response.json();
            
            if (data.success) {
                this.displayRecommendations(data.recommendations);
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
        }
    }
    
    displayRecommendations(recommendations) {
        const container = document.getElementById('recommendations-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (recommendations.length === 0) {
            container.innerHTML = '<p class=\"no-recommendations\">No recommendations at this time.</p>';
            return;
        }
        
        recommendations.forEach(rec => {
            const recElement = document.createElement('div');
            recElement.className = `recommendation-item type-${rec.type}`;
            recElement.innerHTML = `
                <div class="recommendation-content">
                    <strong>${rec.type.replace('_', ' ').toUpperCase()}:</strong>
                    <span>${rec.message}</span>
                </div>
                ${rec.action ? `<button onclick="aiDashboard.executeRecommendation('${rec.action}')" class="btn btn-sm btn-outline">Execute</button>` : ''}
            `;
            container.appendChild(recElement);
        });
    }
    
    async queryKnowledge() {
        const queryInput = document.getElementById('knowledge-query-input');
        if (!queryInput) return;
        
        const query = queryInput.value.trim();
        if (!query) {
            this.showNotification('Please enter a query', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/ai-collaboration/knowledge/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query
                }),
                params: new URLSearchParams({ ai_model: this.currentAI })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayKnowledgeResults(data.results);
                queryInput.value = ''; // Clear input
            } else {
                this.showNotification('Failed to query knowledge base', 'error');
            }
        } catch (error) {
            console.error('Error querying knowledge:', error);
            this.showNotification('Error querying knowledge base', 'error');
        }
    }
    
    displayKnowledgeResults(results) {
        const container = document.getElementById('knowledge-results');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (results.length === 0) {
            container.innerHTML = '<p class=\"no-results\">No knowledge found for your query.</p>';
            return;
        }
        
        results.forEach(result => {
            const resultElement = document.createElement('div');
            resultElement.className = 'knowledge-result';
            resultElement.innerHTML = `
                <div class="result-header">
                    <strong>${result.topic}</strong>
                    <span class="result-category">${result.category}</span>
                </div>
                <div class="result-content">
                    <p>${result.content}</p>
                </div>
                <div class="result-meta">
                    <span class="confidence">Confidence: ${(result.confidence_score * 100).toFixed(0)}%</span>
                    <span class="source">Source: ${result.source_ai}</span>
                </div>
            `;
            container.appendChild(resultElement);
        });
    }
    
    async runDeploymentSafetyCheck() {
        try {
            const description = prompt('Enter deployment description:') || '';
            
            this.showNotification('Running deployment safety checks...', 'info');
            
            const response = await fetch('/api/ai-collaboration/deploy/safety-check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description: description
                }),
                params: new URLSearchParams({ ai_model: this.currentAI })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayDeploymentResults(data.deployment_result);
            } else {
                this.showNotification('Deployment safety check failed', 'error');
            }
        } catch (error) {
            console.error('Error running deployment safety check:', error);
            this.showNotification('Error running deployment safety check', 'error');
        }
    }
    
    displayDeploymentResults(results) {
        const container = document.getElementById('deployment-results');
        if (!container) return;
        
        container.innerHTML = `
            <div class="deployment-result">
                <h4>Deployment Safety Check Results</h4>
                <div class="result-status status-${results.deployment_status}">
                    Status: ${results.deployment_status.toUpperCase()}
                </div>
                <div class="result-details">
                    <p><strong>Backup ID:</strong> ${results.backup_id}</p>
                    <p><strong>Test Status:</strong> ${results.test_results.overall_status}</p>
                    <p><strong>Message:</strong> ${results.message}</p>
                </div>
                ${results.required_actions ? `
                    <div class="required-actions">
                        <strong>Required Actions:</strong>
                        <ul>
                            ${results.required_actions.map(action => `<li>${action}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${results.rollback_available ? `
                    <button onclick="aiDashboard.rollbackDeployment('${results.backup_id}')" 
                            class="btn btn-warning">Rollback to Backup</button>
                ` : ''}
            </div>
        `;
    }
    
    async rollbackDeployment(backupId) {
        if (!confirm(`Are you sure you want to rollback to backup ${backupId}?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/ai-collaboration/deploy/rollback/${backupId}`, {
                method: 'POST',
                params: new URLSearchParams({ ai_model: this.currentAI })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Deployment rolled back successfully', 'success');
            } else {
                this.showNotification('Rollback failed', 'error');
            }
        } catch (error) {
            console.error('Error rolling back deployment:', error);
            this.showNotification('Error rolling back deployment', 'error');
        }
    }
    
    async captureCurrentContext() {
        try {
            const response = await fetch('/api/ai-collaboration/context/current');
            const data = await response.json();
            
            if (data.success) {
                this.displayCurrentContext(data.context);
                this.showNotification('Context captured successfully', 'success');
            } else {
                this.showNotification('Failed to capture context', 'error');
            }
        } catch (error) {
            console.error('Error capturing context:', error);
            this.showNotification('Error capturing context', 'error');
        }
    }
    
    displayCurrentContext(context) {
        const container = document.getElementById('current-context-display');
        if (!container) return;
        
        container.innerHTML = `
            <div class="context-info">
                <h4>Current Project Context</h4>
                <div class="context-item">
                    <strong>Context ID:</strong> ${context.context_id}
                </div>
                <div class="context-item">
                    <strong>Timestamp:</strong> ${new Date(context.timestamp).toLocaleString()}
                </div>
                <div class="context-item">
                    <strong>Deployment Status:</strong> ${context.deployment_status}
                </div>
                <div class="context-item">
                    <strong>Active Features:</strong> ${context.active_features.length} features
                </div>
                <div class="context-item">
                    <strong>Known Issues:</strong> ${context.known_issues.length} issues
                </div>
                <div class="context-item">
                    <strong>Technical Debt:</strong> ${context.technical_debt.length} items
                </div>
            </div>
        `;
    }
    
    async refreshDashboard() {
        this.showNotification('Refreshing dashboard...', 'info');
        
        try {
            await Promise.all([
                this.loadSystemStatus(),
                this.loadAITasks(),
                this.loadTaskRecommendations()
            ]);
            
            this.showNotification('Dashboard refreshed', 'success');
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            this.showNotification('Error refreshing dashboard', 'error');
        }
    }
    
    startAutoRefresh() {
        this.autoRefreshTimer = setInterval(() => {
            this.loadSystemStatus();
        }, this.refreshInterval);
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
        }
    }
    
    // Utility methods
    updateElement(elementId, content) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = content;
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="notification-close">&times;</button>
        `;
        
        // Add to notification container
        let container = document.getElementById('notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
        
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
    
    displaySessionData(sessionData) {
        const container = document.getElementById('session-data-display');
        if (!container) return;
        
        container.innerHTML = `
            <div class="session-info">
                <h4>Active Session Data</h4>
                <div class="session-item">
                    <strong>Session ID:</strong> ${sessionData.session_id}
                </div>
                <div class="session-item">
                    <strong>Active Tasks:</strong> ${sessionData.active_tasks.length}
                </div>
                <div class="session-item">
                    <strong>Recommendations:</strong> ${sessionData.recommendations.length}
                </div>
                <div class="session-item">
                    <strong>Pending Handoffs:</strong> ${sessionData.pending_handoffs.length}
                </div>
            </div>
        `;
    }
}

// Initialize dashboard when page loads
let aiDashboard;

document.addEventListener('DOMContentLoaded', () => {
    aiDashboard = new AICollaborationDashboard();
});

// Export for global access
window.AICollaborationDashboard = AICollaborationDashboard;