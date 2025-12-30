#!/usr/bin/env python3
"""
Enhanced ChatterFix CMMS Frontend with Full CRUD Functionality
This file contains the enhanced modal templates and JavaScript functions
to be integrated into the existing unified gateway
"""

# Modal HTML Templates to be added before closing </body> tag
MODAL_TEMPLATES = '''
<!-- Work Order Modal -->
<div class="modal fade" id="workOrderModal" tabindex="-1" aria-labelledby="workOrderModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="workOrderModalLabel">Work Order</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="workOrderForm">
                    <input type="hidden" id="workOrderId" name="id">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="mb-3">
                                <label for="workOrderTitle" class="form-label">Title *</label>
                                <input type="text" class="form-control" id="workOrderTitle" name="title" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderPriority" class="form-label">Priority</label>
                                <select class="form-select" id="workOrderPriority" name="priority">
                                    <option value="Low">Low</option>
                                    <option value="Medium" selected>Medium</option>
                                    <option value="High">High</option>
                                    <option value="Critical">Critical</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="workOrderDescription" class="form-label">Description *</label>
                        <textarea class="form-control" id="workOrderDescription" name="description" rows="3" required></textarea>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderAssignedTo" class="form-label">Assigned To</label>
                                <select class="form-select" id="workOrderAssignedTo" name="assigned_to">
                                    <option value="">Unassigned</option>
                                    <option value="John Smith">John Smith</option>
                                    <option value="Sarah Johnson">Sarah Johnson</option>
                                    <option value="Mike Wilson">Mike Wilson</option>
                                    <option value="Emily Davis">Emily Davis</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderDueDate" class="form-label">Due Date</label>
                                <input type="datetime-local" class="form-control" id="workOrderDueDate" name="due_date">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderAssetId" class="form-label">Asset</label>
                                <select class="form-select" id="workOrderAssetId" name="asset_id">
                                    <option value="">No Asset</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderStatus" class="form-label">Status</label>
                                <select class="form-select" id="workOrderStatus" name="status">
                                    <option value="Open">Open</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="Completed">Completed</option>
                                    <option value="Cancelled">Cancelled</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="deleteWorkOrderBtn" onclick="deleteWorkOrder()" style="display: none;">Delete</button>
                <button type="button" class="btn btn-primary" onclick="saveWorkOrder()">Save Work Order</button>
            </div>
        </div>
    </div>
</div>

<!-- Asset Modal -->
<div class="modal fade" id="assetModal" tabindex="-1" aria-labelledby="assetModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="assetModalLabel">Asset</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="assetForm">
                    <input type="hidden" id="assetId" name="id">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="mb-3">
                                <label for="assetName" class="form-label">Asset Name *</label>
                                <input type="text" class="form-control" id="assetName" name="name" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetType" class="form-label">Type</label>
                                <select class="form-select" id="assetType" name="type">
                                    <option value="Equipment">Equipment</option>
                                    <option value="Facility">Facility</option>
                                    <option value="Vehicle">Vehicle</option>
                                    <option value="Tool">Tool</option>
                                    <option value="Infrastructure">Infrastructure</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetLocation" class="form-label">Location</label>
                                <input type="text" class="form-control" id="assetLocation" name="location">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetStatus" class="form-label">Status</label>
                                <select class="form-select" id="assetStatus" name="status">
                                    <option value="Active">Active</option>
                                    <option value="Inactive">Inactive</option>
                                    <option value="Maintenance">Under Maintenance</option>
                                    <option value="Retired">Retired</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetManufacturer" class="form-label">Manufacturer</label>
                                <input type="text" class="form-control" id="assetManufacturer" name="manufacturer">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetModel" class="form-label">Model</label>
                                <input type="text" class="form-control" id="assetModel" name="model">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetSerialNumber" class="form-label">Serial Number</label>
                                <input type="text" class="form-control" id="assetSerialNumber" name="serial_number">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetInstallDate" class="form-label">Install Date</label>
                                <input type="date" class="form-control" id="assetInstallDate" name="install_date">
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="assetDescription" class="form-label">Description</label>
                        <textarea class="form-control" id="assetDescription" name="description" rows="3"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="deleteAssetBtn" onclick="deleteAsset()" style="display: none;">Delete</button>
                <button type="button" class="btn btn-primary" onclick="saveAsset()">Save Asset</button>
            </div>
        </div>
    </div>
</div>

<!-- Part Modal -->
<div class="modal fade" id="partModal" tabindex="-1" aria-labelledby="partModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="partModalLabel">Part</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="partForm">
                    <input type="hidden" id="partId" name="id">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="mb-3">
                                <label for="partName" class="form-label">Part Name *</label>
                                <input type="text" class="form-control" id="partName" name="name" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partNumber" class="form-label">Part Number</label>
                                <input type="text" class="form-control" id="partNumber" name="part_number">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partCategory" class="form-label">Category</label>
                                <select class="form-select" id="partCategory" name="category">
                                    <option value="Electrical">Electrical</option>
                                    <option value="Mechanical">Mechanical</option>
                                    <option value="HVAC">HVAC</option>
                                    <option value="Plumbing">Plumbing</option>
                                    <option value="Safety">Safety</option>
                                    <option value="General">General</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partUnit" class="form-label">Unit</label>
                                <select class="form-select" id="partUnit" name="unit">
                                    <option value="Each">Each</option>
                                    <option value="Box">Box</option>
                                    <option value="Case">Case</option>
                                    <option value="Foot">Foot</option>
                                    <option value="Meter">Meter</option>
                                    <option value="Gallon">Gallon</option>
                                    <option value="Liter">Liter</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partQuantity" class="form-label">Current Stock</label>
                                <input type="number" class="form-control" id="partQuantity" name="quantity" min="0">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partReorderPoint" class="form-label">Reorder Point</label>
                                <input type="number" class="form-control" id="partReorderPoint" name="reorder_point" min="0">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partCost" class="form-label">Unit Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="partCost" name="cost" min="0">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partSupplier" class="form-label">Supplier</label>
                                <input type="text" class="form-control" id="partSupplier" name="supplier">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partLocation" class="form-label">Storage Location</label>
                                <input type="text" class="form-control" id="partLocation" name="location">
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="partDescription" class="form-label">Description</label>
                        <textarea class="form-control" id="partDescription" name="description" rows="3"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="deletePartBtn" onclick="deletePart()" style="display: none;">Delete</button>
                <button type="button" class="btn btn-primary" onclick="savePart()">Save Part</button>
            </div>
        </div>
    </div>
</div>
'''

# Enhanced JavaScript Functions
ENHANCED_JAVASCRIPT = '''
// Enhanced CRUD Functions for ChatterFix CMMS

// Global variables for data caching
let assetsCache = [];
let workOrdersCache = [];
let partsCache = [];

// Work Order Functions
async function showCreateWorkOrderModal() {
    document.getElementById('workOrderModalLabel').textContent = 'Create New Work Order';
    document.getElementById('workOrderForm').reset();
    document.getElementById('workOrderId').value = '';
    document.getElementById('deleteWorkOrderBtn').style.display = 'none';
    
    // Load assets for dropdown
    await loadAssetsForDropdown();
    
    const modal = new bootstrap.Modal(document.getElementById('workOrderModal'));
    modal.show();
}

async function viewWorkOrder(id) {
    await editWorkOrder(id, true); // View mode
}

async function editWorkOrder(id, viewOnly = false) {
    try {
        const response = await fetch(`/api/work-orders/${id}`);
        if (response.ok) {
            const workOrder = await response.json();
            
            document.getElementById('workOrderModalLabel').textContent = viewOnly ? 'View Work Order' : 'Edit Work Order';
            document.getElementById('workOrderId').value = workOrder.id;
            document.getElementById('workOrderTitle').value = workOrder.title || '';
            document.getElementById('workOrderDescription').value = workOrder.description || '';
            document.getElementById('workOrderPriority').value = workOrder.priority || 'Medium';
            document.getElementById('workOrderAssignedTo').value = workOrder.assigned_to || '';
            document.getElementById('workOrderStatus').value = workOrder.status || 'Open';
            document.getElementById('workOrderAssetId').value = workOrder.asset_id || '';
            
            if (workOrder.due_date) {
                const dueDate = new Date(workOrder.due_date);
                document.getElementById('workOrderDueDate').value = dueDate.toISOString().slice(0, 16);
            }
            
            await loadAssetsForDropdown();
            
            if (viewOnly) {
                // Disable all form inputs for view mode
                const inputs = document.querySelectorAll('#workOrderForm input, #workOrderForm select, #workOrderForm textarea');
                inputs.forEach(input => input.disabled = true);
                document.querySelector('#workOrderModal .btn-primary').style.display = 'none';
            } else {
                document.getElementById('deleteWorkOrderBtn').style.display = 'inline-block';
            }
            
            const modal = new bootstrap.Modal(document.getElementById('workOrderModal'));
            modal.show();
        }
    } catch (error) {
        console.error('Error loading work order:', error);
        alert('Error loading work order details');
    }
}

async function saveWorkOrder() {
    const form = document.getElementById('workOrderForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Remove empty values
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            delete data[key];
        }
    });
    
    try {
        const isEdit = data.id && data.id !== '';
        const url = isEdit ? `/api/work-orders/${data.id}` : '/api/work-orders';
        const method = isEdit ? 'PUT' : 'POST';
        
        if (isEdit) {
            delete data.id; // Don't send ID in body for PUT
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('workOrderModal'));
            modal.hide();
            await loadWorkOrdersContent();
            showSuccessMessage(isEdit ? 'Work order updated successfully!' : 'Work order created successfully!');
        } else {
            throw new Error('Failed to save work order');
        }
    } catch (error) {
        console.error('Error saving work order:', error);
        alert('Error saving work order');
    }
}

async function deleteWorkOrder() {
    const id = document.getElementById('workOrderId').value;
    if (!id) return;
    
    if (confirm('Are you sure you want to delete this work order?')) {
        try {
            const response = await fetch(`/api/work-orders/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('workOrderModal'));
                modal.hide();
                await loadWorkOrdersContent();
                showSuccessMessage('Work order deleted successfully!');
            } else {
                throw new Error('Failed to delete work order');
            }
        } catch (error) {
            console.error('Error deleting work order:', error);
            alert('Error deleting work order');
        }
    }
}

// Asset Functions
async function showCreateAssetModal() {
    document.getElementById('assetModalLabel').textContent = 'Create New Asset';
    document.getElementById('assetForm').reset();
    document.getElementById('assetId').value = '';
    document.getElementById('deleteAssetBtn').style.display = 'none';
    
    const modal = new bootstrap.Modal(document.getElementById('assetModal'));
    modal.show();
}

async function viewAsset(id) {
    await editAsset(id, true);
}

async function editAsset(id, viewOnly = false) {
    try {
        const response = await fetch(`/api/assets/${id}`);
        if (response.ok) {
            const asset = await response.json();
            
            document.getElementById('assetModalLabel').textContent = viewOnly ? 'View Asset' : 'Edit Asset';
            document.getElementById('assetId').value = asset.id;
            document.getElementById('assetName').value = asset.name || '';
            document.getElementById('assetType').value = asset.type || 'Equipment';
            document.getElementById('assetLocation').value = asset.location || '';
            document.getElementById('assetStatus').value = asset.status || 'Active';
            document.getElementById('assetManufacturer').value = asset.manufacturer || '';
            document.getElementById('assetModel').value = asset.model || '';
            document.getElementById('assetSerialNumber').value = asset.serial_number || '';
            document.getElementById('assetDescription').value = asset.description || '';
            
            if (asset.install_date) {
                document.getElementById('assetInstallDate').value = asset.install_date.split('T')[0];
            }
            
            if (viewOnly) {
                const inputs = document.querySelectorAll('#assetForm input, #assetForm select, #assetForm textarea');
                inputs.forEach(input => input.disabled = true);
                document.querySelector('#assetModal .btn-primary').style.display = 'none';
            } else {
                document.getElementById('deleteAssetBtn').style.display = 'inline-block';
            }
            
            const modal = new bootstrap.Modal(document.getElementById('assetModal'));
            modal.show();
        }
    } catch (error) {
        console.error('Error loading asset:', error);
        alert('Error loading asset details');
    }
}

async function saveAsset() {
    const form = document.getElementById('assetForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            delete data[key];
        }
    });
    
    try {
        const isEdit = data.id && data.id !== '';
        const url = isEdit ? `/api/assets/${data.id}` : '/api/assets';
        const method = isEdit ? 'PUT' : 'POST';
        
        if (isEdit) {
            delete data.id;
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('assetModal'));
            modal.hide();
            await loadAssetsContent();
            showSuccessMessage(isEdit ? 'Asset updated successfully!' : 'Asset created successfully!');
        } else {
            throw new Error('Failed to save asset');
        }
    } catch (error) {
        console.error('Error saving asset:', error);
        alert('Error saving asset');
    }
}

async function deleteAsset() {
    const id = document.getElementById('assetId').value;
    if (!id) return;
    
    if (confirm('Are you sure you want to delete this asset?')) {
        try {
            const response = await fetch(`/api/assets/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('assetModal'));
                modal.hide();
                await loadAssetsContent();
                showSuccessMessage('Asset deleted successfully!');
            } else {
                throw new Error('Failed to delete asset');
            }
        } catch (error) {
            console.error('Error deleting asset:', error);
            alert('Error deleting asset');
        }
    }
}

// Part Functions
async function showCreatePartModal() {
    document.getElementById('partModalLabel').textContent = 'Create New Part';
    document.getElementById('partForm').reset();
    document.getElementById('partId').value = '';
    document.getElementById('deletePartBtn').style.display = 'none';
    
    const modal = new bootstrap.Modal(document.getElementById('partModal'));
    modal.show();
}

async function viewPart(id) {
    await editPart(id, true);
}

async function editPart(id, viewOnly = false) {
    try {
        const response = await fetch(`/api/parts/${id}`);
        if (response.ok) {
            const part = await response.json();
            
            document.getElementById('partModalLabel').textContent = viewOnly ? 'View Part' : 'Edit Part';
            document.getElementById('partId').value = part.id;
            document.getElementById('partName').value = part.name || '';
            document.getElementById('partNumber').value = part.part_number || '';
            document.getElementById('partCategory').value = part.category || 'General';
            document.getElementById('partUnit').value = part.unit || 'Each';
            document.getElementById('partQuantity').value = part.quantity || 0;
            document.getElementById('partReorderPoint').value = part.reorder_point || 0;
            document.getElementById('partCost').value = part.cost || 0;
            document.getElementById('partSupplier').value = part.supplier || '';
            document.getElementById('partLocation').value = part.location || '';
            document.getElementById('partDescription').value = part.description || '';
            
            if (viewOnly) {
                const inputs = document.querySelectorAll('#partForm input, #partForm select, #partForm textarea');
                inputs.forEach(input => input.disabled = true);
                document.querySelector('#partModal .btn-primary').style.display = 'none';
            } else {
                document.getElementById('deletePartBtn').style.display = 'inline-block';
            }
            
            const modal = new bootstrap.Modal(document.getElementById('partModal'));
            modal.show();
        }
    } catch (error) {
        console.error('Error loading part:', error);
        alert('Error loading part details');
    }
}

async function savePart() {
    const form = document.getElementById('partForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            delete data[key];
        }
    });
    
    try {
        const isEdit = data.id && data.id !== '';
        const url = isEdit ? `/api/parts/${data.id}` : '/api/parts';
        const method = isEdit ? 'PUT' : 'POST';
        
        if (isEdit) {
            delete data.id;
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('partModal'));
            modal.hide();
            await loadPartsContent();
            showSuccessMessage(isEdit ? 'Part updated successfully!' : 'Part created successfully!');
        } else {
            throw new Error('Failed to save part');
        }
    } catch (error) {
        console.error('Error saving part:', error);
        alert('Error saving part');
    }
}

async function deletePart() {
    const id = document.getElementById('partId').value;
    if (!id) return;
    
    if (confirm('Are you sure you want to delete this part?')) {
        try {
            const response = await fetch(`/api/parts/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('partModal'));
                modal.hide();
                await loadPartsContent();
                showSuccessMessage('Part deleted successfully!');
            } else {
                throw new Error('Failed to delete part');
            }
        } catch (error) {
            console.error('Error deleting part:', error);
            alert('Error deleting part');
        }
    }
}

// Helper Functions
async function loadAssetsForDropdown() {
    try {
        const response = await fetch('/api/assets');
        if (response.ok) {
            const assets = await response.json();
            const dropdown = document.getElementById('workOrderAssetId');
            dropdown.innerHTML = '<option value="">No Asset</option>';
            
            assets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset.id;
                option.textContent = `${asset.name} (${asset.location || 'No location'})`;
                dropdown.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading assets for dropdown:', error);
    }
}

function showSuccessMessage(message) {
    // Create a temporary success alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 3000);
}

// Enhanced table generation with clickable rows
function generateWorkOrdersTable(workOrders) {
    if (!workOrders || workOrders.length === 0) {
        return '<p class="text-muted">No work orders found</p>';
    }
    
    return `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Assigned To</th>
                        <th>Due Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${workOrders.map(wo => `
                        <tr style="cursor: pointer;" onclick="viewWorkOrder(${wo.id})">
                            <td>${wo.id}</td>
                            <td>${wo.title}</td>
                            <td><span class="badge bg-${getStatusColor(wo.status)}">${wo.status}</span></td>
                            <td><span class="badge bg-${getPriorityColor(wo.priority)}">${wo.priority}</span></td>
                            <td>${wo.assigned_to || 'Unassigned'}</td>
                            <td>${wo.due_date ? new Date(wo.due_date).toLocaleDateString() : 'No due date'}</td>
                            <td onclick="event.stopPropagation();">
                                <button class="btn btn-sm btn-outline-primary me-1" onclick="editWorkOrder(${wo.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-info" onclick="viewWorkOrder(${wo.id})">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}
'''

print("Enhanced CRUD frontend components ready for integration!")