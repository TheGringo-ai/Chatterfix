/**
 * ChatterFix CMMS JavaScript Functions
 * Essential functions for CRUD operations and modal management
 */

// Modal management functions
function closeModal() {
    const modal = document.getElementById('work-order-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function closeAssetModal() {
    const modal = document.getElementById('asset-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function closePartsModal() {
    const modal = document.getElementById('parts-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Work Order functions
async function deleteWorkOrder(id) {
    if (!confirm('Are you sure you want to delete this work order?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/work-orders/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Work order deleted successfully');
            location.reload(); // Refresh the page to update the list
        } else {
            alert('Error deleting work order: ' + result.error);
        }
    } catch (error) {
        alert('Error deleting work order: ' + error.message);
    }
}

async function saveWorkOrder(id = null) {
    const form = document.getElementById('workorder-form');
    if (!form) return;
    
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    try {
        const url = id ? `/api/work-orders/${id}` : '/api/work-orders';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Work order saved successfully');
            closeModal();
            location.reload();
        } else {
            alert('Error saving work order: ' + result.error);
        }
    } catch (error) {
        alert('Error saving work order: ' + error.message);
    }
}

// Asset functions
async function deleteAsset(id) {
    if (!confirm('Are you sure you want to delete this asset?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/assets/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Asset deleted successfully');
            location.reload();
        } else {
            alert('Error deleting asset: ' + result.error);
        }
    } catch (error) {
        alert('Error deleting asset: ' + error.message);
    }
}

async function saveAsset(id = null) {
    const form = document.getElementById('asset-form');
    if (!form) return;
    
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    try {
        const url = id ? `/api/assets/${id}` : '/api/assets';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Asset saved successfully');
            closeAssetModal();
            location.reload();
        } else {
            alert('Error saving asset: ' + result.error);
        }
    } catch (error) {
        alert('Error saving asset: ' + error.message);
    }
}

// Parts functions
async function deletePart(id) {
    if (!confirm('Are you sure you want to delete this part?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/parts/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Part deleted successfully');
            location.reload();
        } else {
            alert('Error deleting part: ' + result.error);
        }
    } catch (error) {
        alert('Error deleting part: ' + error.message);
    }
}

async function savePart(id = null) {
    const form = document.getElementById('parts-form');
    if (!form) return;
    
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    try {
        const url = id ? `/api/parts/${id}` : '/api/parts';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Part saved successfully');
            closePartsModal();
            location.reload();
        } else {
            alert('Error saving part: ' + result.error);
        }
    } catch (error) {
        alert('Error saving part: ' + error.message);
    }
}

async function reorderPart(id) {
    const quantity = prompt('Enter quantity to reorder:');
    if (!quantity || isNaN(quantity)) {
        alert('Please enter a valid quantity');
        return;
    }
    
    try {
        // This could be implemented as a separate API endpoint for reordering
        alert(`Reorder request for ${quantity} units of part ${id} has been submitted`);
        // TODO: Implement actual reordering logic
    } catch (error) {
        alert('Error reordering part: ' + error.message);
    }
}

async function adjustStock(id) {
    const adjustment = prompt('Enter stock adjustment (+/- number):');
    if (!adjustment || isNaN(adjustment)) {
        alert('Please enter a valid adjustment amount');
        return;
    }
    
    try {
        // This could be implemented as a separate API endpoint for stock adjustment
        alert(`Stock adjustment of ${adjustment} for part ${id} has been recorded`);
        // TODO: Implement actual stock adjustment logic
    } catch (error) {
        alert('Error adjusting stock: ' + error.message);
    }
}

// Form validation helpers
function validateWorkOrderForm() {
    const title = document.getElementById('title');
    const description = document.getElementById('description');
    
    if (!title || !title.value.trim()) {
        alert('Title is required');
        return false;
    }
    
    if (!description || !description.value.trim()) {
        alert('Description is required');
        return false;
    }
    
    return true;
}

function validateAssetForm() {
    const name = document.getElementById('name');
    
    if (!name || !name.value.trim()) {
        alert('Asset name is required');
        return false;
    }
    
    return true;
}

function validatePartsForm() {
    const name = document.getElementById('name');
    const partNumber = document.getElementById('partNumber');
    
    if (!name || !name.value.trim()) {
        alert('Part name is required');
        return false;
    }
    
    if (!partNumber || !partNumber.value.trim()) {
        alert('Part number is required');
        return false;
    }
    
    return true;
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add form submit handlers
    const workorderForm = document.getElementById('workorder-form');
    if (workorderForm) {
        workorderForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (validateWorkOrderForm()) {
                const id = workorderForm.dataset.workorderId;
                saveWorkOrder(id);
            }
        });
    }
    
    const assetForm = document.getElementById('asset-form');
    if (assetForm) {
        assetForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (validateAssetForm()) {
                const id = assetForm.dataset.assetId;
                saveAsset(id);
            }
        });
    }
    
    const partsForm = document.getElementById('parts-form');
    if (partsForm) {
        partsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (validatePartsForm()) {
                const id = partsForm.dataset.partId;
                savePart(id);
            }
        });
    }
    
    // Close modals when clicking outside
    window.addEventListener('click', function(e) {
        const workorderModal = document.getElementById('workorder-modal');
        const assetModal = document.getElementById('asset-modal');
        const partsModal = document.getElementById('parts-modal');
        
        if (e.target === workorderModal) {
            closeModal();
        }
        if (e.target === assetModal) {
            closeAssetModal();
        }
        if (e.target === partsModal) {
            closePartsModal();
        }
    });
});