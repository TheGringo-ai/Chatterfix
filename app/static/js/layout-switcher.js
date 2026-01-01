/**
 * ChatterFix Layout Switcher
 * Handles switching between Card, List, Table, and Compact views
 * Persists user preference in localStorage
 */

class LayoutSwitcher {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.storageKey = `chatterfix_layout_${containerId}`;
        this.currentLayout = localStorage.getItem(this.storageKey) || options.defaultLayout || 'card';
        this.onLayoutChange = options.onLayoutChange || null;

        this.layouts = {
            card: {
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7" rx="1"/>
                    <rect x="14" y="3" width="7" height="7" rx="1"/>
                    <rect x="3" y="14" width="7" height="7" rx="1"/>
                    <rect x="14" y="14" width="7" height="7" rx="1"/>
                </svg>`,
                label: 'Card View',
                class: 'layout-card'
            },
            list: {
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="6" x2="21" y2="6"/>
                    <line x1="3" y1="12" x2="21" y2="12"/>
                    <line x1="3" y1="18" x2="21" y2="18"/>
                </svg>`,
                label: 'List View',
                class: 'layout-list'
            },
            table: {
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <line x1="3" y1="9" x2="21" y2="9"/>
                    <line x1="3" y1="15" x2="21" y2="15"/>
                    <line x1="9" y1="3" x2="9" y2="21"/>
                    <line x1="15" y1="3" x2="15" y2="21"/>
                </svg>`,
                label: 'Table View',
                class: 'layout-table'
            },
            compact: {
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="5" height="5" rx="1"/>
                    <rect x="10" y="3" width="5" height="5" rx="1"/>
                    <rect x="17" y="3" width="4" height="5" rx="1"/>
                    <rect x="3" y="10" width="5" height="5" rx="1"/>
                    <rect x="10" y="10" width="5" height="5" rx="1"/>
                    <rect x="17" y="10" width="4" height="5" rx="1"/>
                    <rect x="3" y="17" width="5" height="4" rx="1"/>
                    <rect x="10" y="17" width="5" height="4" rx="1"/>
                    <rect x="17" y="17" width="4" height="4" rx="1"/>
                </svg>`,
                label: 'Compact View',
                class: 'layout-compact'
            }
        };

        this.init();
    }

    init() {
        if (!this.container) {
            console.warn(`Layout switcher: Container #${this.containerId} not found`);
            return;
        }

        // Apply saved layout
        this.applyLayout(this.currentLayout);
    }

    /**
     * Create the layout switcher control HTML
     * @returns {string} HTML string for the switcher
     */
    createSwitcherHTML() {
        let html = `<div class="layout-switcher" id="${this.containerId}-switcher">
            <span class="layout-switcher-label">View:</span>`;

        for (const [key, layout] of Object.entries(this.layouts)) {
            const activeClass = key === this.currentLayout ? 'active' : '';
            html += `
                <button class="layout-btn ${activeClass}"
                        data-layout="${key}"
                        title="${layout.label}"
                        onclick="window.layoutSwitchers['${this.containerId}'].setLayout('${key}')">
                    ${layout.icon}
                </button>`;
        }

        html += `</div>`;
        return html;
    }

    /**
     * Set the layout mode
     * @param {string} layout - Layout type (card, list, table, compact)
     */
    setLayout(layout) {
        if (!this.layouts[layout]) {
            console.warn(`Layout switcher: Unknown layout "${layout}"`);
            return;
        }

        this.currentLayout = layout;
        localStorage.setItem(this.storageKey, layout);
        this.applyLayout(layout);
        this.updateSwitcherButtons();

        if (this.onLayoutChange) {
            this.onLayoutChange(layout);
        }
    }

    /**
     * Apply layout class to container
     * @param {string} layout - Layout type
     */
    applyLayout(layout) {
        if (!this.container) return;

        // Remove all layout classes
        Object.values(this.layouts).forEach(l => {
            this.container.classList.remove(l.class);
        });

        // Add new layout class
        this.container.classList.add(this.layouts[layout].class);

        // Add transition class for animation
        this.container.classList.add('layout-transition');
        setTimeout(() => {
            this.container.classList.remove('layout-transition');
        }, 300);

        // Handle table header visibility
        const tableHeader = this.container.querySelector('.table-header');
        if (tableHeader) {
            tableHeader.style.display = layout === 'table' ? 'grid' : 'none';
        }
    }

    /**
     * Update switcher button active states
     */
    updateSwitcherButtons() {
        const switcher = document.getElementById(`${this.containerId}-switcher`);
        if (!switcher) return;

        switcher.querySelectorAll('.layout-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.layout === this.currentLayout);
        });
    }

    /**
     * Get current layout
     * @returns {string} Current layout type
     */
    getLayout() {
        return this.currentLayout;
    }
}

// Global registry for layout switchers
window.layoutSwitchers = window.layoutSwitchers || {};

/**
 * Initialize a layout switcher for a container
 * @param {string} containerId - ID of the items container
 * @param {Object} options - Configuration options
 * @returns {LayoutSwitcher} The layout switcher instance
 */
function initLayoutSwitcher(containerId, options = {}) {
    const switcher = new LayoutSwitcher(containerId, options);
    window.layoutSwitchers[containerId] = switcher;
    return switcher;
}

/**
 * Render items in the container with current layout
 * @param {string} containerId - Container ID
 * @param {Array} items - Array of item objects
 * @param {Object} config - Rendering configuration
 */
function renderItems(containerId, items, config = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const switcher = window.layoutSwitchers[containerId];
    const layout = switcher ? switcher.getLayout() : 'card';

    // Add table header if table layout
    let html = '';
    if (layout === 'table' && config.tableHeaders) {
        html += `<div class="table-header">
            ${config.tableHeaders.map(h => `<div>${h}</div>`).join('')}
        </div>`;
    }

    // Render items
    if (items.length === 0) {
        html += `<div class="items-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
                <rect x="9" y="3" width="6" height="4" rx="1"/>
            </svg>
            <h3>${config.emptyTitle || 'No items found'}</h3>
            <p>${config.emptyMessage || 'Create your first item to get started'}</p>
        </div>`;
    } else {
        items.forEach(item => {
            html += config.renderItem(item, layout);
        });
    }

    container.innerHTML = html;
}

/**
 * Work Order Item Renderer
 */
function renderWorkOrderItem(item, layout) {
    const priorityClass = `badge-${item.priority}`;
    const statusClass = `badge-${item.status.replace('_', '-')}`;

    if (layout === 'table') {
        return `
            <div class="item-card" data-id="${item.id}">
                <div class="item-id">#${item.id}</div>
                <div class="item-title">${item.title}</div>
                <div><span class="badge ${priorityClass}">${item.priority}</span></div>
                <div><span class="badge ${statusClass}">${item.status.replace('_', ' ')}</span></div>
                <div>${item.assigned_to || 'Unassigned'}</div>
                <div class="table-actions">
                    <button class="btn-action btn-edit" onclick="editWorkOrder(${item.id})">Edit</button>
                    <button class="btn-action btn-delete" onclick="deleteWorkOrder(${item.id})">Del</button>
                </div>
            </div>`;
    }

    return `
        <div class="item-card" data-id="${item.id}">
            <div class="item-header">
                <div>
                    <h3 class="item-title">${item.title}</h3>
                    <span class="item-id">#${item.id}</span>
                </div>
                <span class="badge ${priorityClass}">${item.priority}</span>
            </div>
            <div class="item-body">
                <p class="item-description">${item.description || 'No description'}</p>
                <div class="item-meta">
                    <span class="badge ${statusClass}">${item.status.replace('_', ' ')}</span>
                    ${item.assigned_to ? `<span class="badge">👤 ${item.assigned_to}</span>` : ''}
                    ${item.due_date ? `<span class="badge">📅 ${item.due_date}</span>` : ''}
                </div>
            </div>
            <div class="item-footer">
                <span style="font-size: 0.8rem; color: rgba(255,255,255,0.5);">
                    Created: ${item.created_date || 'N/A'}
                </span>
                <div>
                    <button class="btn-action btn-edit" onclick="editWorkOrder(${item.id})">Edit</button>
                    <button class="btn-action btn-delete" onclick="deleteWorkOrder(${item.id})">Delete</button>
                </div>
            </div>
        </div>`;
}

/**
 * Asset Item Renderer
 */
function renderAssetItem(item, layout) {
    const statusClass = `badge-${item.status}`;
    const criticalityClass = `badge-${item.criticality}`;

    if (layout === 'table') {
        return `
            <div class="item-card" data-id="${item.id}">
                <div class="item-id">${item.id}</div>
                <div class="item-title">${item.name}</div>
                <div>${item.type || 'N/A'}</div>
                <div><span class="badge ${statusClass}">${item.status}</span></div>
                <div>${item.location || 'N/A'}</div>
                <div class="table-actions">
                    <button class="btn-action btn-view" onclick="viewAsset('${item.id}')">View</button>
                    <button class="btn-action btn-edit" onclick="editAsset('${item.id}')">Edit</button>
                </div>
            </div>`;
    }

    return `
        <div class="item-card" data-id="${item.id}">
            <div class="item-header">
                <div>
                    <h3 class="item-title">${item.name}</h3>
                    <span class="item-id">${item.id}</span>
                </div>
                <span class="badge ${criticalityClass}">${item.criticality || 'medium'}</span>
            </div>
            <div class="item-body">
                <p class="item-description">${item.manufacturer || ''} ${item.model || ''}</p>
                <div class="item-meta">
                    <span class="badge ${statusClass}">${item.status}</span>
                    ${item.type ? `<span class="badge">🔧 ${item.type}</span>` : ''}
                    ${item.location ? `<span class="badge">📍 ${item.location}</span>` : ''}
                </div>
            </div>
            <div class="item-footer">
                <span style="font-size: 0.8rem; color: rgba(255,255,255,0.5);">
                    ${item.serial_number || 'No S/N'}
                </span>
                <div>
                    <button class="btn-action btn-view" onclick="viewAsset('${item.id}')">View</button>
                    <button class="btn-action btn-edit" onclick="editAsset('${item.id}')">Edit</button>
                </div>
            </div>
        </div>`;
}

/**
 * Part Item Renderer
 */
function renderPartItem(item, layout) {
    let stockClass = 'badge-in-stock';
    if (item.quantity <= 0) {
        stockClass = 'badge-out-of-stock';
    } else if (item.quantity <= (item.min_quantity || 10)) {
        stockClass = 'badge-low-stock';
    }

    const stockLabel = item.quantity <= 0 ? 'Out of Stock' :
                       item.quantity <= (item.min_quantity || 10) ? 'Low Stock' : 'In Stock';

    if (layout === 'table') {
        return `
            <div class="item-card" data-id="${item.id}">
                <div class="item-id">${item.part_number || item.id}</div>
                <div class="item-title">${item.name}</div>
                <div>${item.category || 'N/A'}</div>
                <div><span class="badge ${stockClass}">${item.quantity} units</span></div>
                <div>$${(item.unit_cost || 0).toFixed(2)}</div>
                <div class="table-actions">
                    <button class="btn-action btn-edit" onclick="editPart('${item.id}')">Edit</button>
                    <button class="btn-action btn-view" onclick="adjustStock('${item.id}')">Stock</button>
                </div>
            </div>`;
    }

    return `
        <div class="item-card" data-id="${item.id}">
            <div class="item-header">
                <div>
                    <h3 class="item-title">${item.name}</h3>
                    <span class="item-id">${item.part_number || item.id}</span>
                </div>
                <span class="badge ${stockClass}">${stockLabel}</span>
            </div>
            <div class="item-body">
                <p class="item-description">${item.description || 'No description'}</p>
                <div class="item-meta">
                    <span class="badge">📦 ${item.quantity} units</span>
                    ${item.category ? `<span class="badge">📁 ${item.category}</span>` : ''}
                    <span class="badge">💰 $${(item.unit_cost || 0).toFixed(2)}</span>
                </div>
            </div>
            <div class="item-footer">
                <span style="font-size: 0.8rem; color: rgba(255,255,255,0.5);">
                    ${item.location || 'No location'}
                </span>
                <div>
                    <button class="btn-action btn-edit" onclick="editPart('${item.id}')">Edit</button>
                    <button class="btn-action btn-view" onclick="adjustStock('${item.id}')">Adjust Stock</button>
                </div>
            </div>
        </div>`;
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LayoutSwitcher, initLayoutSwitcher, renderItems, renderWorkOrderItem, renderAssetItem, renderPartItem };
}
