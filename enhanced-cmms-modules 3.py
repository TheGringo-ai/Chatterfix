#!/usr/bin/env python3
"""
ChatterFix CMMS - Enhanced Upkeep-Style Modules
Comprehensive CMMS platform with advanced features
"""

# Enhanced HTML Templates for Comprehensive CMMS

ENHANCED_MODALS = '''
<!-- Enhanced Work Order Modal -->
<div class="modal fade" id="workOrderModal" tabindex="-1" aria-labelledby="workOrderModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="workOrderModalLabel">Work Order</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="workOrderForm">
                    <input type="hidden" id="workOrderId" name="id">
                    
                    <!-- Basic Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-info-circle me-2"></i>Basic Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-8">
                            <div class="mb-3">
                                <label for="workOrderTitle" class="form-label">Work Order Title *</label>
                                <input type="text" class="form-control" id="workOrderTitle" name="title" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderNumber" class="form-label">Work Order Number</label>
                                <input type="text" class="form-control" id="workOrderNumber" name="work_order_number" placeholder="Auto-generated">
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="workOrderDescription" class="form-label">Description *</label>
                                <textarea class="form-control" id="workOrderDescription" name="description" rows="3" required></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Priority & Status -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-exclamation-triangle me-2"></i>Priority & Status</h6>
                            <hr>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="workOrderPriority" class="form-label">Priority</label>
                                <select class="form-select" id="workOrderPriority" name="priority">
                                    <option value="Low">Low</option>
                                    <option value="Medium" selected>Medium</option>
                                    <option value="High">High</option>
                                    <option value="Critical">Critical</option>
                                    <option value="Emergency">Emergency</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="workOrderStatus" class="form-label">Status</label>
                                <select class="form-select" id="workOrderStatus" name="status">
                                    <option value="Open">Open</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="On Hold">On Hold</option>
                                    <option value="Completed">Completed</option>
                                    <option value="Cancelled">Cancelled</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="workOrderType" class="form-label">Work Order Type</label>
                                <select class="form-select" id="workOrderType" name="work_order_type">
                                    <option value="Preventive">Preventive Maintenance</option>
                                    <option value="Corrective">Corrective Maintenance</option>
                                    <option value="Emergency">Emergency Repair</option>
                                    <option value="Inspection">Inspection</option>
                                    <option value="Installation">Installation</option>
                                    <option value="Calibration">Calibration</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="workOrderCategory" class="form-label">Category</label>
                                <select class="form-select" id="workOrderCategory" name="category">
                                    <option value="Electrical">Electrical</option>
                                    <option value="Mechanical">Mechanical</option>
                                    <option value="HVAC">HVAC</option>
                                    <option value="Plumbing">Plumbing</option>
                                    <option value="Safety">Safety</option>
                                    <option value="Cleaning">Cleaning</option>
                                    <option value="IT">IT/Technology</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Assignment & Scheduling -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-user-cog me-2"></i>Assignment & Scheduling</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderAssignedTo" class="form-label">Assigned Technician</label>
                                <select class="form-select" id="workOrderAssignedTo" name="assigned_to">
                                    <option value="">Unassigned</option>
                                    <option value="John Smith">John Smith (Electrical)</option>
                                    <option value="Sarah Johnson">Sarah Johnson (HVAC)</option>
                                    <option value="Mike Wilson">Mike Wilson (Mechanical)</option>
                                    <option value="Emily Davis">Emily Davis (General)</option>
                                    <option value="Robert Brown">Robert Brown (Plumbing)</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderRequestedBy" class="form-label">Requested By</label>
                                <input type="text" class="form-control" id="workOrderRequestedBy" name="requested_by">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderDepartment" class="form-label">Department</label>
                                <select class="form-select" id="workOrderDepartment" name="department">
                                    <option value="">Select Department</option>
                                    <option value="Maintenance">Maintenance</option>
                                    <option value="Production">Production</option>
                                    <option value="Facilities">Facilities</option>
                                    <option value="Safety">Safety</option>
                                    <option value="Quality">Quality Control</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderDueDate" class="form-label">Due Date</label>
                                <input type="datetime-local" class="form-control" id="workOrderDueDate" name="due_date">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderEstimatedHours" class="form-label">Estimated Hours</label>
                                <input type="number" step="0.5" class="form-control" id="workOrderEstimatedHours" name="estimated_hours">
                            </div>
                        </div>
                    </div>

                    <!-- Asset & Location -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-map-marker-alt me-2"></i>Asset & Location</h6>
                            <hr>
                        </div>
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
                                <label for="workOrderLocation" class="form-label">Location</label>
                                <input type="text" class="form-control" id="workOrderLocation" name="location" placeholder="Building, Floor, Room">
                            </div>
                        </div>
                    </div>

                    <!-- Cost & Resources -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-dollar-sign me-2"></i>Cost & Resources</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderEstimatedCost" class="form-label">Estimated Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="workOrderEstimatedCost" name="estimated_cost">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderActualCost" class="form-label">Actual Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="workOrderActualCost" name="actual_cost">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="workOrderLaborCost" class="form-label">Labor Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="workOrderLaborCost" name="labor_cost">
                            </div>
                        </div>
                    </div>

                    <!-- Parts & Materials -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-box me-2"></i>Parts & Materials</h6>
                            <hr>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="workOrderParts" class="form-label">Required Parts</label>
                                <textarea class="form-control" id="workOrderParts" name="required_parts" rows="2" placeholder="List parts and quantities needed"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Instructions & Notes -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-clipboard me-2"></i>Instructions & Notes</h6>
                            <hr>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="workOrderInstructions" class="form-label">Work Instructions</label>
                                <textarea class="form-control" id="workOrderInstructions" name="instructions" rows="3" placeholder="Detailed work instructions and procedures"></textarea>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="workOrderNotes" class="form-label">Additional Notes</label>
                                <textarea class="form-control" id="workOrderNotes" name="notes" rows="2" placeholder="Any additional notes or comments"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Safety & Compliance -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-shield-alt me-2"></i>Safety & Compliance</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderSafetyRequirements" class="form-label">Safety Requirements</label>
                                <textarea class="form-control" id="workOrderSafetyRequirements" name="safety_requirements" rows="2" placeholder="PPE, lockout/tagout, permits required"></textarea>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="workOrderComplianceNotes" class="form-label">Compliance Notes</label>
                                <textarea class="form-control" id="workOrderComplianceNotes" name="compliance_notes" rows="2" placeholder="Regulatory requirements, standards"></textarea>
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

<!-- Enhanced Asset Modal -->
<div class="modal fade" id="assetModal" tabindex="-1" aria-labelledby="assetModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="assetModalLabel">Asset Management</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="assetForm">
                    <input type="hidden" id="assetId" name="id">
                    
                    <!-- Basic Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-info-circle me-2"></i>Basic Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetName" class="form-label">Asset Name *</label>
                                <input type="text" class="form-control" id="assetName" name="name" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetTag" class="form-label">Asset Tag/ID</label>
                                <input type="text" class="form-control" id="assetTag" name="asset_tag">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetType" class="form-label">Asset Type</label>
                                <select class="form-select" id="assetType" name="type">
                                    <option value="Equipment">Equipment</option>
                                    <option value="Machinery">Machinery</option>
                                    <option value="Vehicle">Vehicle</option>
                                    <option value="Tool">Tool</option>
                                    <option value="Facility">Facility</option>
                                    <option value="Infrastructure">Infrastructure</option>
                                    <option value="IT Hardware">IT Hardware</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetCategory" class="form-label">Category</label>
                                <select class="form-select" id="assetCategory" name="category">
                                    <option value="Production">Production</option>
                                    <option value="HVAC">HVAC</option>
                                    <option value="Electrical">Electrical</option>
                                    <option value="Mechanical">Mechanical</option>
                                    <option value="Safety">Safety</option>
                                    <option value="Office">Office</option>
                                    <option value="Facility">Facility</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetStatus" class="form-label">Status</label>
                                <select class="form-select" id="assetStatus" name="status">
                                    <option value="Active">Active</option>
                                    <option value="Inactive">Inactive</option>
                                    <option value="Under Maintenance">Under Maintenance</option>
                                    <option value="Out of Service">Out of Service</option>
                                    <option value="Retired">Retired</option>
                                    <option value="Disposed">Disposed</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Location & Details -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-map-marker-alt me-2"></i>Location & Details</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetBuilding" class="form-label">Building</label>
                                <input type="text" class="form-control" id="assetBuilding" name="building">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetFloor" class="form-label">Floor</label>
                                <input type="text" class="form-control" id="assetFloor" name="floor">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetRoom" class="form-label">Room/Area</label>
                                <input type="text" class="form-control" id="assetRoom" name="room">
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="assetLocation" class="form-label">Full Location</label>
                                <input type="text" class="form-control" id="assetLocation" name="location" placeholder="Complete location description">
                            </div>
                        </div>
                    </div>

                    <!-- Manufacturer & Technical Info -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-cogs me-2"></i>Manufacturer & Technical Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetManufacturer" class="form-label">Manufacturer</label>
                                <input type="text" class="form-control" id="assetManufacturer" name="manufacturer">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetModel" class="form-label">Model</label>
                                <input type="text" class="form-control" id="assetModel" name="model">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetSerialNumber" class="form-label">Serial Number</label>
                                <input type="text" class="form-control" id="assetSerialNumber" name="serial_number">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetSpecifications" class="form-label">Technical Specifications</label>
                                <textarea class="form-control" id="assetSpecifications" name="specifications" rows="3" placeholder="Power, capacity, dimensions, etc."></textarea>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetDescription" class="form-label">Description</label>
                                <textarea class="form-control" id="assetDescription" name="description" rows="3"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Dates & Lifecycle -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-calendar me-2"></i>Dates & Lifecycle</h6>
                            <hr>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="assetPurchaseDate" class="form-label">Purchase Date</label>
                                <input type="date" class="form-control" id="assetPurchaseDate" name="purchase_date">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="assetInstallDate" class="form-label">Install Date</label>
                                <input type="date" class="form-control" id="assetInstallDate" name="install_date">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="assetWarrantyExpiry" class="form-label">Warranty Expiry</label>
                                <input type="date" class="form-control" id="assetWarrantyExpiry" name="warranty_expiry">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="assetLifeExpectancy" class="form-label">Life Expectancy (years)</label>
                                <input type="number" class="form-control" id="assetLifeExpectancy" name="life_expectancy">
                            </div>
                        </div>
                    </div>

                    <!-- Financial Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-dollar-sign me-2"></i>Financial Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetPurchaseCost" class="form-label">Purchase Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="assetPurchaseCost" name="purchase_cost">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetCurrentValue" class="form-label">Current Value ($)</label>
                                <input type="number" step="0.01" class="form-control" id="assetCurrentValue" name="current_value">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="assetDepreciationRate" class="form-label">Depreciation Rate (%)</label>
                                <input type="number" step="0.01" class="form-control" id="assetDepreciationRate" name="depreciation_rate">
                            </div>
                        </div>
                    </div>

                    <!-- Vendor & Support -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-handshake me-2"></i>Vendor & Support</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetVendor" class="form-label">Primary Vendor</label>
                                <input type="text" class="form-control" id="assetVendor" name="vendor">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="assetVendorContact" class="form-label">Vendor Contact</label>
                                <input type="text" class="form-control" id="assetVendorContact" name="vendor_contact" placeholder="Phone, email, name">
                            </div>
                        </div>
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

<!-- Enhanced Parts Modal -->
<div class="modal fade" id="partModal" tabindex="-1" aria-labelledby="partModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="partModalLabel">Parts & Inventory Management</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="partForm">
                    <input type="hidden" id="partId" name="id">
                    
                    <!-- Basic Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-info-circle me-2"></i>Basic Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partName" class="form-label">Part Name *</label>
                                <input type="text" class="form-control" id="partName" name="name" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partNumber" class="form-label">Part Number</label>
                                <input type="text" class="form-control" id="partNumber" name="part_number">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partCategory" class="form-label">Category</label>
                                <select class="form-select" id="partCategory" name="category">
                                    <option value="Electrical">Electrical Components</option>
                                    <option value="Mechanical">Mechanical Parts</option>
                                    <option value="HVAC">HVAC Components</option>
                                    <option value="Plumbing">Plumbing Supplies</option>
                                    <option value="Safety">Safety Equipment</option>
                                    <option value="Filters">Filters</option>
                                    <option value="Lubricants">Lubricants & Oils</option>
                                    <option value="Fasteners">Fasteners</option>
                                    <option value="Tools">Tools</option>
                                    <option value="General">General Supplies</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partSubcategory" class="form-label">Subcategory</label>
                                <input type="text" class="form-control" id="partSubcategory" name="subcategory" placeholder="Bearings, Motors, Sensors, etc.">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partUnit" class="form-label">Unit of Measure</label>
                                <select class="form-select" id="partUnit" name="unit">
                                    <option value="Each">Each</option>
                                    <option value="Box">Box</option>
                                    <option value="Case">Case</option>
                                    <option value="Foot">Foot</option>
                                    <option value="Meter">Meter</option>
                                    <option value="Gallon">Gallon</option>
                                    <option value="Liter">Liter</option>
                                    <option value="Pound">Pound</option>
                                    <option value="Kilogram">Kilogram</option>
                                    <option value="Set">Set</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="partDescription" class="form-label">Description</label>
                                <textarea class="form-control" id="partDescription" name="description" rows="2" placeholder="Detailed part description and specifications"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Inventory Management -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-warehouse me-2"></i>Inventory Management</h6>
                            <hr>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partQuantity" class="form-label">Current Stock</label>
                                <input type="number" class="form-control" id="partQuantity" name="quantity" min="0">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partMinimumStock" class="form-label">Minimum Stock Level</label>
                                <input type="number" class="form-control" id="partMinimumStock" name="minimum_stock" min="0">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partMaximumStock" class="form-label">Maximum Stock Level</label>
                                <input type="number" class="form-control" id="partMaximumStock" name="maximum_stock" min="0">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partReorderPoint" class="form-label">Reorder Point</label>
                                <input type="number" class="form-control" id="partReorderPoint" name="reorder_point" min="0">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partStorageLocation" class="form-label">Storage Location</label>
                                <input type="text" class="form-control" id="partStorageLocation" name="storage_location" placeholder="Warehouse, Bin, Shelf">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partBarcode" class="form-label">Barcode/SKU</label>
                                <input type="text" class="form-control" id="partBarcode" name="barcode">
                            </div>
                        </div>
                    </div>

                    <!-- Cost & Pricing -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-dollar-sign me-2"></i>Cost & Pricing</h6>
                            <hr>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partUnitCost" class="form-label">Unit Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="partUnitCost" name="unit_cost" min="0">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partAverageCost" class="form-label">Average Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="partAverageCost" name="average_cost" min="0">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partLastCost" class="form-label">Last Purchase Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="partLastCost" name="last_cost" min="0">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label for="partTotalValue" class="form-label">Total Value ($)</label>
                                <input type="number" step="0.01" class="form-control" id="partTotalValue" name="total_value" readonly>
                            </div>
                        </div>
                    </div>

                    <!-- Supplier Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-truck me-2"></i>Supplier Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partPrimarySupplier" class="form-label">Primary Supplier</label>
                                <input type="text" class="form-control" id="partPrimarySupplier" name="primary_supplier">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partSupplierPartNumber" class="form-label">Supplier Part Number</label>
                                <input type="text" class="form-control" id="partSupplierPartNumber" name="supplier_part_number">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="partLeadTime" class="form-label">Lead Time (days)</label>
                                <input type="number" class="form-control" id="partLeadTime" name="lead_time" min="0">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partAlternativeSuppliers" class="form-label">Alternative Suppliers</label>
                                <textarea class="form-control" id="partAlternativeSuppliers" name="alternative_suppliers" rows="2" placeholder="List backup suppliers"></textarea>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partSupplierContact" class="form-label">Supplier Contact</label>
                                <textarea class="form-control" id="partSupplierContact" name="supplier_contact" rows="2" placeholder="Contact information"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Compatibility & Usage -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-puzzle-piece me-2"></i>Compatibility & Usage</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partCompatibleAssets" class="form-label">Compatible Assets</label>
                                <textarea class="form-control" id="partCompatibleAssets" name="compatible_assets" rows="2" placeholder="List assets this part is used with"></textarea>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="partUsageNotes" class="form-label">Usage Notes</label>
                                <textarea class="form-control" id="partUsageNotes" name="usage_notes" rows="2" placeholder="Installation notes, precautions, etc."></textarea>
                            </div>
                        </div>
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

# Add new modules for Technicians, Managers, Scheduler, and Buyer
NEW_MODULES = '''
<!-- Technician Management Modal -->
<div class="modal fade" id="technicianModal" tabindex="-1" aria-labelledby="technicianModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="technicianModalLabel">Technician Management</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="technicianForm">
                    <input type="hidden" id="technicianId" name="id">
                    
                    <!-- Personal Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-user me-2"></i>Personal Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianFirstName" class="form-label">First Name *</label>
                                <input type="text" class="form-control" id="technicianFirstName" name="first_name" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianLastName" class="form-label">Last Name *</label>
                                <input type="text" class="form-control" id="technicianLastName" name="last_name" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianEmployeeId" class="form-label">Employee ID</label>
                                <input type="text" class="form-control" id="technicianEmployeeId" name="employee_id">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="technicianEmail" class="form-label">Email</label>
                                <input type="email" class="form-control" id="technicianEmail" name="email">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="technicianPhone" class="form-label">Phone</label>
                                <input type="tel" class="form-control" id="technicianPhone" name="phone">
                            </div>
                        </div>
                    </div>

                    <!-- Job Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-briefcase me-2"></i>Job Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianJobTitle" class="form-label">Job Title</label>
                                <input type="text" class="form-control" id="technicianJobTitle" name="job_title">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianDepartment" class="form-label">Department</label>
                                <select class="form-select" id="technicianDepartment" name="department">
                                    <option value="">Select Department</option>
                                    <option value="Maintenance">Maintenance</option>
                                    <option value="Electrical">Electrical</option>
                                    <option value="Mechanical">Mechanical</option>
                                    <option value="HVAC">HVAC</option>
                                    <option value="Facilities">Facilities</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianSkillLevel" class="form-label">Skill Level</label>
                                <select class="form-select" id="technicianSkillLevel" name="skill_level">
                                    <option value="Apprentice">Apprentice</option>
                                    <option value="Technician">Technician</option>
                                    <option value="Senior Technician">Senior Technician</option>
                                    <option value="Lead Technician">Lead Technician</option>
                                    <option value="Supervisor">Supervisor</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="technicianSkills" class="form-label">Skills & Certifications</label>
                                <textarea class="form-control" id="technicianSkills" name="skills" rows="3" placeholder="List technical skills, certifications, and qualifications"></textarea>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="technicianSpecializations" class="form-label">Specializations</label>
                                <textarea class="form-control" id="technicianSpecializations" name="specializations" rows="3" placeholder="Areas of expertise and specialization"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Availability & Schedule -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-clock me-2"></i>Availability & Schedule</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianShift" class="form-label">Default Shift</label>
                                <select class="form-select" id="technicianShift" name="shift">
                                    <option value="Day">Day Shift</option>
                                    <option value="Evening">Evening Shift</option>
                                    <option value="Night">Night Shift</option>
                                    <option value="Rotating">Rotating</option>
                                    <option value="On-Call">On-Call</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianStatus" class="form-label">Status</label>
                                <select class="form-select" id="technicianStatus" name="status">
                                    <option value="Active">Active</option>
                                    <option value="Inactive">Inactive</option>
                                    <option value="On Leave">On Leave</option>
                                    <option value="Training">Training</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="technicianHourlyRate" class="form-label">Hourly Rate ($)</label>
                                <input type="number" step="0.01" class="form-control" id="technicianHourlyRate" name="hourly_rate">
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="deleteTechnicianBtn" onclick="deleteTechnician()" style="display: none;">Delete</button>
                <button type="button" class="btn btn-primary" onclick="saveTechnician()">Save Technician</button>
            </div>
        </div>
    </div>
</div>

<!-- Schedule Management Modal -->
<div class="modal fade" id="scheduleModal" tabindex="-1" aria-labelledby="scheduleModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="scheduleModalLabel">Schedule Management</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="scheduleForm">
                    <input type="hidden" id="scheduleId" name="id">
                    
                    <!-- Schedule Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-calendar me-2"></i>Schedule Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="scheduleTitle" class="form-label">Schedule Title *</label>
                                <input type="text" class="form-control" id="scheduleTitle" name="title" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="scheduleType" class="form-label">Schedule Type</label>
                                <select class="form-select" id="scheduleType" name="schedule_type">
                                    <option value="Preventive Maintenance">Preventive Maintenance</option>
                                    <option value="Inspection">Inspection</option>
                                    <option value="Calibration">Calibration</option>
                                    <option value="Training">Training</option>
                                    <option value="Meeting">Meeting</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="scheduleStartDate" class="form-label">Start Date *</label>
                                <input type="datetime-local" class="form-control" id="scheduleStartDate" name="start_date" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="scheduleEndDate" class="form-label">End Date</label>
                                <input type="datetime-local" class="form-control" id="scheduleEndDate" name="end_date">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="scheduleDuration" class="form-label">Duration (hours)</label>
                                <input type="number" step="0.5" class="form-control" id="scheduleDuration" name="duration">
                            </div>
                        </div>
                    </div>

                    <!-- Recurrence -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-repeat me-2"></i>Recurrence</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="scheduleRecurrence" class="form-label">Recurrence Pattern</label>
                                <select class="form-select" id="scheduleRecurrence" name="recurrence_pattern">
                                    <option value="None">None</option>
                                    <option value="Daily">Daily</option>
                                    <option value="Weekly">Weekly</option>
                                    <option value="Monthly">Monthly</option>
                                    <option value="Quarterly">Quarterly</option>
                                    <option value="Annually">Annually</option>
                                    <option value="Custom">Custom</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="scheduleInterval" class="form-label">Interval</label>
                                <input type="number" class="form-control" id="scheduleInterval" name="interval" min="1" placeholder="Every X periods">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="scheduleEndRecurrence" class="form-label">End Recurrence</label>
                                <input type="date" class="form-control" id="scheduleEndRecurrence" name="end_recurrence">
                            </div>
                        </div>
                    </div>

                    <!-- Assignment -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-users me-2"></i>Assignment</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="scheduleAssignedTechnicians" class="form-label">Assigned Technicians</label>
                                <select class="form-select" id="scheduleAssignedTechnicians" name="assigned_technicians" multiple>
                                    <option value="john_smith">John Smith</option>
                                    <option value="sarah_johnson">Sarah Johnson</option>
                                    <option value="mike_wilson">Mike Wilson</option>
                                    <option value="emily_davis">Emily Davis</option>
                                </select>
                                <small class="form-text text-muted">Hold Ctrl to select multiple technicians</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="scheduleAsset" class="form-label">Related Asset</label>
                                <select class="form-select" id="scheduleAsset" name="asset_id">
                                    <option value="">No Asset</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Details -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-clipboard me-2"></i>Details</h6>
                            <hr>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="scheduleDescription" class="form-label">Description</label>
                                <textarea class="form-control" id="scheduleDescription" name="description" rows="3"></textarea>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="scheduleInstructions" class="form-label">Instructions</label>
                                <textarea class="form-control" id="scheduleInstructions" name="instructions" rows="3" placeholder="Detailed instructions for the scheduled task"></textarea>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="deleteScheduleBtn" onclick="deleteSchedule()" style="display: none;">Delete</button>
                <button type="button" class="btn btn-primary" onclick="saveSchedule()">Save Schedule</button>
            </div>
        </div>
    </div>
</div>

<!-- Buyer/Procurement Modal -->
<div class="modal fade" id="buyerModal" tabindex="-1" aria-labelledby="buyerModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="buyerModalLabel">Procurement Management</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <form id="buyerForm">
                    <input type="hidden" id="buyerId" name="id">
                    
                    <!-- Purchase Request Information -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-shopping-cart me-2"></i>Purchase Request Information</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerRequestTitle" class="form-label">Request Title *</label>
                                <input type="text" class="form-control" id="buyerRequestTitle" name="request_title" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerRequestNumber" class="form-label">Request Number</label>
                                <input type="text" class="form-control" id="buyerRequestNumber" name="request_number" placeholder="Auto-generated">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerRequestType" class="form-label">Request Type</label>
                                <select class="form-select" id="buyerRequestType" name="request_type">
                                    <option value="Emergency">Emergency Purchase</option>
                                    <option value="Standard">Standard Purchase</option>
                                    <option value="Capital">Capital Expenditure</option>
                                    <option value="Service">Service Contract</option>
                                    <option value="Maintenance">Maintenance Supplies</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerPriority" class="form-label">Priority</label>
                                <select class="form-select" id="buyerPriority" name="priority">
                                    <option value="Low">Low</option>
                                    <option value="Medium">Medium</option>
                                    <option value="High">High</option>
                                    <option value="Emergency">Emergency</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerRequestedBy" class="form-label">Requested By</label>
                                <input type="text" class="form-control" id="buyerRequestedBy" name="requested_by">
                            </div>
                        </div>
                    </div>

                    <!-- Items & Specifications -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-list me-2"></i>Items & Specifications</h6>
                            <hr>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="buyerItemDescription" class="form-label">Item Description *</label>
                                <textarea class="form-control" id="buyerItemDescription" name="item_description" rows="3" required placeholder="Detailed description of items to be purchased"></textarea>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerQuantity" class="form-label">Quantity</label>
                                <input type="number" class="form-control" id="buyerQuantity" name="quantity" min="1">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerUnit" class="form-label">Unit</label>
                                <input type="text" class="form-control" id="buyerUnit" name="unit" placeholder="Each, Box, Case, etc.">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerEstimatedCost" class="form-label">Estimated Cost ($)</label>
                                <input type="number" step="0.01" class="form-control" id="buyerEstimatedCost" name="estimated_cost">
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="buyerSpecifications" class="form-label">Technical Specifications</label>
                                <textarea class="form-control" id="buyerSpecifications" name="specifications" rows="3" placeholder="Technical requirements, standards, certifications"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Vendor & Sourcing -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-handshake me-2"></i>Vendor & Sourcing</h6>
                            <hr>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerPreferredVendor" class="form-label">Preferred Vendor</label>
                                <input type="text" class="form-control" id="buyerPreferredVendor" name="preferred_vendor">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerAlternativeVendors" class="form-label">Alternative Vendors</label>
                                <input type="text" class="form-control" id="buyerAlternativeVendors" name="alternative_vendors" placeholder="Comma-separated list">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerQuoteRequired" class="form-label">Quote Required</label>
                                <select class="form-select" id="buyerQuoteRequired" name="quote_required">
                                    <option value="No">No</option>
                                    <option value="Yes">Yes</option>
                                    <option value="Multiple">Multiple Quotes</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerBudgetCode" class="form-label">Budget/Account Code</label>
                                <input type="text" class="form-control" id="buyerBudgetCode" name="budget_code">
                            </div>
                        </div>
                    </div>

                    <!-- Delivery & Timeline -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-truck me-2"></i>Delivery & Timeline</h6>
                            <hr>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerRequiredDate" class="form-label">Required Date</label>
                                <input type="date" class="form-control" id="buyerRequiredDate" name="required_date">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerDeliveryLocation" class="form-label">Delivery Location</label>
                                <input type="text" class="form-control" id="buyerDeliveryLocation" name="delivery_location">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="buyerStatus" class="form-label">Status</label>
                                <select class="form-select" id="buyerStatus" name="status">
                                    <option value="Draft">Draft</option>
                                    <option value="Submitted">Submitted</option>
                                    <option value="Approved">Approved</option>
                                    <option value="Ordered">Ordered</option>
                                    <option value="Received">Received</option>
                                    <option value="Completed">Completed</option>
                                    <option value="Cancelled">Cancelled</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="buyerDeliveryInstructions" class="form-label">Delivery Instructions</label>
                                <textarea class="form-control" id="buyerDeliveryInstructions" name="delivery_instructions" rows="2" placeholder="Special delivery requirements or instructions"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Justification & Approval -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <h6 class="text-primary"><i class="fas fa-check-circle me-2"></i>Justification & Approval</h6>
                            <hr>
                        </div>
                        <div class="col-12">
                            <div class="mb-3">
                                <label for="buyerJustification" class="form-label">Business Justification</label>
                                <textarea class="form-control" id="buyerJustification" name="justification" rows="3" placeholder="Why is this purchase necessary? Business impact, urgency, etc."></textarea>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerApprover" class="form-label">Approver</label>
                                <input type="text" class="form-control" id="buyerApprover" name="approver">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="buyerApprovalDate" class="form-label">Approval Date</label>
                                <input type="date" class="form-control" id="buyerApprovalDate" name="approval_date">
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="deleteBuyerBtn" onclick="deleteBuyer()" style="display: none;">Delete</button>
                <button type="button" class="btn btn-primary" onclick="saveBuyer()">Save Request</button>
            </div>
        </div>
    </div>
</div>
'''

print("Enhanced CMMS modules with Upkeep-style comprehensive forms created!")
print("Includes: Enhanced Work Orders, Assets, Parts, Technicians, Scheduler, and Buyer/Procurement")