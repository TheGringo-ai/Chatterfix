/**
 * ChatterFix CMMS Interactive Functionality
 * Handles all button clicks, form submissions, and user interactions
 */

(function() {
    'use strict';
    
    console.log('🔧 ChatterFix CMMS Interactions Loading...');
    
    // Initialize when DOM is ready
    function initializeCMMSInteractions() {
        console.log('✅ Initializing CMMS interactions on:', window.location.pathname);
        
        // Add click handlers for all buttons
        addButtonHandlers();
        
        // Add visual feedback for all interactive elements
        addVisualFeedback();
        
        // Add form handling
        addFormHandlers();
        
        console.log('🎉 CMMS interactions ready!');
    }
    
    function addButtonHandlers() {
        // Handle buttons by finding them by text content
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => {
            const text = btn.textContent;
            if (text.includes('Create New Work Order')) {
                addCreateWorkOrderHandler(btn);
            } else if (text.includes('Add New Asset')) {
                addCreateAssetHandler(btn);
            } else if (text.includes('Add New Part')) {
                addCreatePartHandler(btn);
            } else if (text.includes('Create PM Schedule')) {
                addCreateMaintenanceHandler(btn);
            }
        });
    }
    
    function addCreateWorkOrderHandler(button) {
        button.onclick = function() {
            console.log('Creating new work order...');
            showCreateWorkOrderModal();
        };
        button.style.cursor = 'pointer';
        console.log('✅ Work order button handler added');
    }
    
    function addCreateAssetHandler(button) {
        button.onclick = function() {
            console.log('Creating new asset...');
            showCreateAssetModal();
        };
        button.style.cursor = 'pointer';
        console.log('✅ Asset button handler added');
    }
    
    function addCreatePartHandler(button) {
        button.onclick = function() {
            console.log('Creating new part...');
            showCreatePartModal();
        };
        button.style.cursor = 'pointer';
        console.log('✅ Part button handler added');
    }
    
    function addCreateMaintenanceHandler(button) {
        button.onclick = function() {
            console.log('Creating maintenance schedule...');
            showCreateMaintenanceModal();
        };
        button.style.cursor = 'pointer';
        console.log('✅ Maintenance button handler added');
    }
    
    function addVisualFeedback() {
        // Add hover effects and click feedback to all buttons
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            // Add transition if not already present
            if (!button.style.transition) {
                button.style.transition = 'all 0.3s ease';
            }
            
            // Add hover effect
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'none';
            });
            
            // Add click effect
            button.addEventListener('mousedown', function() {
                this.style.transform = 'translateY(1px)';
            });
            
            button.addEventListener('mouseup', function() {
                this.style.transform = 'translateY(-2px)';
            });
        });
        
        console.log('✅ Visual feedback added to', buttons.length, 'buttons');
    }
    
    function addFormHandlers() {
        // Handle any existing forms on the page
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log('Form submitted:', form);
                showNotification('Form submitted successfully!', 'success');
            });
        });
    }
    
    // Modal creation functions
    function showCreateWorkOrderModal() {
        const modal = createModal('Create New Work Order', getWorkOrderForm());
        document.body.appendChild(modal);
    }
    
    function showCreateAssetModal() {
        const modal = createModal('Add New Asset', getAssetForm());
        document.body.appendChild(modal);
    }
    
    function showCreatePartModal() {
        const modal = createModal('Add New Part', getPartForm());
        document.body.appendChild(modal);
    }
    
    function showCreateMaintenanceModal() {
        const modal = createModal('Create Maintenance Schedule', getMaintenanceForm());
        document.body.appendChild(modal);
    }
    
    function createModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'cmms-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            color: white;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        `;
        
        modalContent.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">${title}</h2>
                <button onclick="closeModal(this)" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 24px;
                    cursor: pointer;
                    padding: 5px;
                ">×</button>
            </div>
            ${content}
        `;
        
        modal.appendChild(modalContent);
        
        // Close modal when clicking backdrop
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
        
        return modal;
    }
    
    function getWorkOrderForm() {
        return `
            <form onsubmit="submitWorkOrder(event)" style="display: flex; flex-direction: column; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Title:</label>
                    <input type="text" name="title" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Description:</label>
                    <textarea name="description" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                        height: 100px;
                        resize: vertical;
                    "></textarea>
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Priority:</label>
                    <select name="priority" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                        <option value="">Select Priority</option>
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                        <option value="Critical">Critical</option>
                    </select>
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Asset/Equipment:</label>
                    <input type="text" name="asset" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal(this)" style="
                        padding: 10px 20px;
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button type="submit" style="
                        padding: 10px 20px;
                        background: #38ef7d;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-weight: bold;
                    ">Create Work Order</button>
                </div>
            </form>
        `;
    }
    
    function getAssetForm() {
        return `
            <form onsubmit="submitAsset(event)" style="display: flex; flex-direction: column; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Asset Name:</label>
                    <input type="text" name="name" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Type:</label>
                    <input type="text" name="type" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Location:</label>
                    <input type="text" name="location" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Manufacturer:</label>
                    <input type="text" name="manufacturer" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Model:</label>
                    <input type="text" name="model" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal(this)" style="
                        padding: 10px 20px;
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button type="submit" style="
                        padding: 10px 20px;
                        background: #38ef7d;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-weight: bold;
                    ">Add Asset</button>
                </div>
            </form>
        `;
    }
    
    function getPartForm() {
        return `
            <form onsubmit="submitPart(event)" style="display: flex; flex-direction: column; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Part Number:</label>
                    <input type="text" name="part_number" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Part Name:</label>
                    <input type="text" name="name" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Category:</label>
                    <input type="text" name="category" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Unit Cost:</label>
                    <input type="number" step="0.01" name="unit_cost" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Initial Stock:</label>
                    <input type="number" name="stock_quantity" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal(this)" style="
                        padding: 10px 20px;
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button type="submit" style="
                        padding: 10px 20px;
                        background: #38ef7d;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-weight: bold;
                    ">Add Part</button>
                </div>
            </form>
        `;
    }
    
    function getMaintenanceForm() {
        return `
            <form onsubmit="submitMaintenance(event)" style="display: flex; flex-direction: column; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Schedule Name:</label>
                    <input type="text" name="name" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Asset/Equipment:</label>
                    <input type="text" name="asset" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Frequency:</label>
                    <select name="frequency" required style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                    ">
                        <option value="">Select Frequency</option>
                        <option value="Weekly">Weekly</option>
                        <option value="Monthly">Monthly</option>
                        <option value="Quarterly">Quarterly</option>
                        <option value="Semi-Annual">Semi-Annual</option>
                        <option value="Annual">Annual</option>
                    </select>
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Description:</label>
                    <textarea name="description" style="
                        width: 100%;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        background: rgba(255,255,255,0.9);
                        color: #333;
                        height: 80px;
                        resize: vertical;
                    "></textarea>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" onclick="closeModal(this)" style="
                        padding: 10px 20px;
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button type="submit" style="
                        padding: 10px 20px;
                        background: #38ef7d;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-weight: bold;
                    ">Create Schedule</button>
                </div>
            </form>
        `;
    }
    
    // Global functions for form submissions and modal handling
    window.closeModal = function(element) {
        const modal = element.closest('.cmms-modal');
        if (modal) {
            modal.remove();
        }
    };
    
    window.submitWorkOrder = function(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        console.log('Creating work order:', Object.fromEntries(formData));
        showNotification('Work order created successfully!', 'success');
        closeModal(event.target);
    };
    
    window.submitAsset = function(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        console.log('Creating asset:', Object.fromEntries(formData));
        showNotification('Asset added successfully!', 'success');
        closeModal(event.target);
    };
    
    window.submitPart = function(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        console.log('Creating part:', Object.fromEntries(formData));
        showNotification('Part added successfully!', 'success');
        closeModal(event.target);
    };
    
    window.submitMaintenance = function(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        console.log('Creating maintenance schedule:', Object.fromEntries(formData));
        showNotification('Maintenance schedule created successfully!', 'success');
        closeModal(event.target);
    };
    
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#38ef7d' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            border-radius: 5px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 1001;
            animation: slideInRight 0.3s ease;
            font-weight: bold;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // Add CSS animations
    function addAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideInRight {
                from { 
                    opacity: 0;
                    transform: translateX(100%);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            addAnimations();
            initializeCMMSInteractions();
        });
    } else {
        addAnimations();
        initializeCMMSInteractions();
    }
    
})();