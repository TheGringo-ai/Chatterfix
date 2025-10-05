import { fn } from '@storybook/test';

// Work Order List Component
const WorkOrderList = ({ 
  workOrders = [],
  onItemClick = null,
  showActions = true,
  ...args 
}) => {
  const container = document.createElement('div');
  container.className = 'table-container';
  
  const table = document.createElement('table');
  table.className = 'chatterfix-table';
  
  // Table header
  const thead = document.createElement('thead');
  thead.innerHTML = `
    <tr>
      <th>Work Order</th>
      <th>Asset</th>
      <th>Priority</th>
      <th>Status</th>
      <th>Assigned To</th>
      <th>Due Date</th>
      ${showActions ? '<th>Actions</th>' : ''}
    </tr>
  `;
  table.appendChild(thead);
  
  // Table body
  const tbody = document.createElement('tbody');
  
  workOrders.forEach(wo => {
    const row = document.createElement('tr');
    
    const priorityBadge = `<span class="status-badge status-${wo.priority === 'high' ? 'error' : wo.priority === 'medium' ? 'warning' : 'info'}">${wo.priority}</span>`;
    const statusBadge = `<span class="status-badge status-${wo.status === 'completed' ? 'success' : wo.status === 'in-progress' ? 'warning' : 'info'}">${wo.status}</span>`;
    
    row.innerHTML = `
      <td><strong>${wo.id}</strong><br><small style="color: var(--text-muted);">${wo.title}</small></td>
      <td>${wo.asset || 'N/A'}</td>
      <td>${priorityBadge}</td>
      <td>${statusBadge}</td>
      <td>${wo.assignedTo || 'Unassigned'}</td>
      <td>${wo.dueDate || 'Not set'}</td>
      ${showActions ? `<td>
        <button class="btn-secondary" style="font-size: 0.75rem; padding: 4px 8px; margin-right: 4px;">View</button>
        <button class="btn-primary" style="font-size: 0.75rem; padding: 4px 8px;">Edit</button>
      </td>` : ''}
    `;
    
    if (onItemClick && typeof onItemClick === 'function') {
      row.style.cursor = 'pointer';
      row.addEventListener('click', () => onItemClick(wo));
    }
    
    tbody.appendChild(row);
  });
  
  table.appendChild(tbody);
  container.appendChild(table);
  
  return container;
};

// Asset Card Grid Component
const AssetGrid = ({ 
  assets = [],
  onAssetClick = null,
  ...args 
}) => {
  const grid = document.createElement('div');
  grid.style.display = 'grid';
  grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
  grid.style.gap = '24px';
  
  assets.forEach(asset => {
    const card = document.createElement('div');
    card.className = 'card asset-card';
    
    const statusColor = asset.status === 'operational' ? 'success' : 
                       asset.status === 'maintenance' ? 'warning' : 
                       asset.status === 'down' ? 'error' : 'info';
    
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
        <h3 style="color: var(--text-primary); margin: 0;">${asset.name}</h3>
        <span class="status-badge status-${statusColor}">${asset.status}</span>
      </div>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">${asset.description}</p>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.875rem;">
        <div><strong>Location:</strong> ${asset.location}</div>
        <div><strong>Type:</strong> ${asset.type}</div>
        <div><strong>Last PM:</strong> ${asset.lastMaintenance}</div>
        <div><strong>Next PM:</strong> ${asset.nextMaintenance}</div>
      </div>
      <div style="margin-top: 16px; display: flex; gap: 8px;">
        <button class="btn-primary" style="font-size: 0.875rem; padding: 8px 16px;">Schedule PM</button>
        <button class="btn-secondary" style="font-size: 0.875rem; padding: 8px 16px;">View Details</button>
      </div>
    `;
    
    if (onAssetClick && typeof onAssetClick === 'function') {
      card.style.cursor = 'pointer';
      card.addEventListener('click', () => onAssetClick(asset));
    }
    
    grid.appendChild(card);
  });
  
  return grid;
};

// KPI Dashboard Component
const KPIDashboard = ({ 
  kpis = [],
  ...args 
}) => {
  const dashboard = document.createElement('div');
  dashboard.className = 'stats-grid';
  
  kpis.forEach(kpi => {
    const card = document.createElement('div');
    card.className = 'stat-card';
    
    const trendIcon = kpi.trend === 'up' ? '📈' : kpi.trend === 'down' ? '📉' : '➡️';
    const trendColor = kpi.trend === 'up' ? 'var(--status-success)' : 
                      kpi.trend === 'down' ? 'var(--status-error)' : 'var(--text-muted)';
    
    card.innerHTML = `
      <div class="stat-number">${kpi.value}</div>
      <div class="stat-label">${kpi.label}</div>
      <div style="margin-top: 8px; font-size: 0.875rem; color: ${trendColor};">
        ${trendIcon} ${kpi.change || 'No change'}
      </div>
    `;
    
    dashboard.appendChild(card);
  });
  
  return dashboard;
};

// Parts Inventory Component
const PartsInventory = ({ 
  parts = [],
  showLowStock = false,
  onPartClick = null,
  ...args 
}) => {
  const container = document.createElement('div');
  
  // Filter parts if showing low stock only
  const displayParts = showLowStock ? parts.filter(part => part.quantity <= part.minStock) : parts;
  
  if (showLowStock && displayParts.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 48px; color: var(--text-secondary);">
        <div style="font-size: 3rem; margin-bottom: 16px;">✅</div>
        <h3>All Parts Adequately Stocked</h3>
        <p>No parts are currently below minimum stock levels.</p>
      </div>
    `;
    return container;
  }
  
  const grid = document.createElement('div');
  grid.style.display = 'grid';
  grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(280px, 1fr))';
  grid.style.gap = '16px';
  
  displayParts.forEach(part => {
    const isLowStock = part.quantity <= part.minStock;
    const stockPercentage = (part.quantity / (part.minStock * 2)) * 100;
    
    const card = document.createElement('div');
    card.className = 'card';
    card.style.padding = '16px';
    
    card.innerHTML = `
      <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 12px;">
        <div style="flex: 1;">
          <h4 style="color: var(--text-primary); margin: 0 0 4px 0;">${part.name}</h4>
          <p style="color: var(--text-muted); font-size: 0.875rem; margin: 0;">${part.partNumber}</p>
        </div>
        ${isLowStock ? '<span class="status-badge status-error">Low Stock</span>' : ''}
      </div>
      
      <div style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
          <span style="font-size: 0.875rem;">Stock Level</span>
          <span style="font-size: 0.875rem; font-weight: 600;">${part.quantity} / ${part.minStock} min</span>
        </div>
        <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 6px; overflow: hidden;">
          <div style="background: ${isLowStock ? '#ef4444' : '#10b981'}; height: 100%; width: ${Math.min(stockPercentage, 100)}%; transition: width 0.3s ease;"></div>
        </div>
      </div>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.875rem; margin-bottom: 12px;">
        <div><strong>Location:</strong> ${part.location}</div>
        <div><strong>Unit Cost:</strong> $${part.unitCost}</div>
      </div>
      
      <div style="display: flex; gap: 8px;">
        <button class="btn-primary" style="font-size: 0.75rem; padding: 6px 12px; flex: 1;">Reorder</button>
        <button class="btn-secondary" style="font-size: 0.75rem; padding: 6px 12px;">Details</button>
      </div>
    `;
    
    if (onPartClick && typeof onPartClick === 'function') {
      card.style.cursor = 'pointer';
      card.addEventListener('click', () => onPartClick(part));
    }
    
    grid.appendChild(card);
  });
  
  container.appendChild(grid);
  return container;
};

// Maintenance Schedule Component
const MaintenanceSchedule = ({ 
  schedules = [],
  viewMode = 'list',
  onScheduleClick = null,
  ...args 
}) => {
  const container = document.createElement('div');
  
  if (viewMode === 'calendar') {
    // Simple calendar view
    const calendar = document.createElement('div');
    calendar.style.display = 'grid';
    calendar.style.gridTemplateColumns = 'repeat(7, 1fr)';
    calendar.style.gap = '1px';
    calendar.style.background = 'rgba(255,255,255,0.1)';
    calendar.style.borderRadius = '8px';
    calendar.style.overflow = 'hidden';
    
    // Calendar header
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => {
      const dayHeader = document.createElement('div');
      dayHeader.style.padding = '12px';
      dayHeader.style.background = 'var(--bg-secondary)';
      dayHeader.style.textAlign = 'center';
      dayHeader.style.fontWeight = '600';
      dayHeader.style.color = 'var(--text-primary)';
      dayHeader.textContent = day;
      calendar.appendChild(dayHeader);
    });
    
    // Calendar days (simplified)
    for (let i = 1; i <= 35; i++) {
      const dayCell = document.createElement('div');
      dayCell.style.minHeight = '80px';
      dayCell.style.padding = '8px';
      dayCell.style.background = 'var(--bg-card)';
      dayCell.style.borderRight = '1px solid rgba(255,255,255,0.05)';
      dayCell.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
      
      const dayNumber = i <= 31 ? i : '';
      if (dayNumber) {
        dayCell.innerHTML = `<div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 4px;">${dayNumber}</div>`;
        
        // Add sample events for some days
        if ([5, 12, 18, 25].includes(i)) {
          const event = document.createElement('div');
          event.style.background = 'var(--accent-purple)';
          event.style.color = 'white';
          event.style.padding = '2px 4px';
          event.style.borderRadius = '3px';
          event.style.fontSize = '0.75rem';
          event.style.marginBottom = '2px';
          event.textContent = 'PM Schedule';
          dayCell.appendChild(event);
        }
      }
      
      calendar.appendChild(dayCell);
    }
    
    container.appendChild(calendar);
  } else {
    // List view
    const list = document.createElement('div');
    list.style.display = 'flex';
    list.style.flexDirection = 'column';
    list.style.gap = '12px';
    
    schedules.forEach(schedule => {
      const item = document.createElement('div');
      item.className = 'card';
      item.style.padding = '16px';
      item.style.display = 'flex';
      item.style.alignItems = 'center';
      item.style.gap = '16px';
      
      const priorityColor = schedule.priority === 'high' ? '#ef4444' : 
                           schedule.priority === 'medium' ? '#f59e0b' : '#10b981';
      
      item.innerHTML = `
        <div style="width: 4px; height: 40px; background: ${priorityColor}; border-radius: 2px;"></div>
        <div style="flex: 1;">
          <h4 style="color: var(--text-primary); margin: 0 0 4px 0;">${schedule.title}</h4>
          <p style="color: var(--text-secondary); margin: 0; font-size: 0.875rem;">${schedule.asset} • ${schedule.type}</p>
        </div>
        <div style="text-align: right;">
          <div style="color: var(--text-primary); font-weight: 600;">${schedule.date}</div>
          <div style="color: var(--text-muted); font-size: 0.875rem;">${schedule.time}</div>
        </div>
        <button class="btn-primary" style="font-size: 0.875rem; padding: 8px 16px;">Schedule</button>
      `;
      
      if (onScheduleClick && typeof onScheduleClick === 'function') {
        item.style.cursor = 'pointer';
        item.addEventListener('click', () => onScheduleClick(schedule));
      }
      
      list.appendChild(item);
    });
    
    container.appendChild(list);
  }
  
  return container;
};

// Export default story configuration
export default {
  title: 'ChatterFix CMMS/Components',
  render: (args) => WorkOrderList(args),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Complex CMMS-specific components for work orders, assets, parts inventory, and maintenance scheduling.',
      },
    },
  },
  argTypes: {
    onItemClick: { action: 'item-clicked' },
    onAssetClick: { action: 'asset-clicked' },
    onPartClick: { action: 'part-clicked' },
    onScheduleClick: { action: 'schedule-clicked' },
  },
  args: {
    onItemClick: fn(),
    onAssetClick: fn(),
    onPartClick: fn(),
    onScheduleClick: fn(),
  },
};

// Work Order List
export const WorkOrderTable = {
  render: (args) => WorkOrderList({
    workOrders: [
      {
        id: 'WO-2024-001',
        title: 'Pump Maintenance',
        asset: 'Cooling Pump A1',
        priority: 'high',
        status: 'open',
        assignedTo: 'John Smith',
        dueDate: '2024-10-15'
      },
      {
        id: 'WO-2024-002',
        title: 'Belt Replacement',
        asset: 'Conveyor B2',
        priority: 'medium',
        status: 'in-progress',
        assignedTo: 'Sarah Johnson',
        dueDate: '2024-10-18'
      },
      {
        id: 'WO-2024-003',
        title: 'Filter Change',
        asset: 'HVAC Unit C3',
        priority: 'low',
        status: 'completed',
        assignedTo: 'Mike Davis',
        dueDate: '2024-10-10'
      },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Work order list component with status badges, priority indicators, and action buttons.',
      },
    },
  },
};

// Asset Management Grid
export const AssetManagement = {
  render: (args) => AssetGrid({
    assets: [
      {
        name: 'Cooling Pump A1',
        description: 'Primary cooling system pump for production line A',
        location: 'Building 1, Floor 2',
        type: 'Pump',
        status: 'operational',
        lastMaintenance: '2024-09-15',
        nextMaintenance: '2024-12-15'
      },
      {
        name: 'Conveyor Belt B2',
        description: 'Main conveyor system for packaging line',
        location: 'Building 2, Floor 1',
        type: 'Conveyor',
        status: 'maintenance',
        lastMaintenance: '2024-08-20',
        nextMaintenance: '2024-10-20'
      },
      {
        name: 'Generator D4',
        description: 'Emergency backup power generator',
        location: 'Building 1, Basement',
        type: 'Generator',
        status: 'down',
        lastMaintenance: '2024-07-10',
        nextMaintenance: '2024-10-10'
      },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Asset management grid showing equipment status, maintenance schedules, and quick actions.',
      },
    },
  },
};

// KPI Dashboard
export const Dashboard = {
  render: (args) => KPIDashboard({
    kpis: [
      {
        label: 'Open Work Orders',
        value: '24',
        trend: 'down',
        change: '↓ 15% from last week'
      },
      {
        label: 'Assets Operational',
        value: '156',
        trend: 'up',
        change: '↑ 98.7% uptime'
      },
      {
        label: 'Avg Response Time',
        value: '2.3h',
        trend: 'down',
        change: '↓ 0.5h improvement'
      },
      {
        label: 'Parts Below Min Stock',
        value: '8',
        trend: 'up',
        change: '↑ 3 items need reorder'
      },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'KPI dashboard with key metrics, trends, and performance indicators.',
      },
    },
  },
};

// Parts Inventory Management
export const PartsInventoryNormal = {
  render: (args) => PartsInventory({
    parts: [
      {
        name: 'Pump Bearing',
        partNumber: 'PB-001',
        quantity: 15,
        minStock: 5,
        location: 'Warehouse A1',
        unitCost: 25.99
      },
      {
        name: 'Belt Drive',
        partNumber: 'BD-002',
        quantity: 3,
        minStock: 10,
        location: 'Warehouse A2',
        unitCost: 45.50
      },
      {
        name: 'Air Filter',
        partNumber: 'AF-003',
        quantity: 25,
        minStock: 15,
        location: 'Warehouse B1',
        unitCost: 12.75
      },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Parts inventory management with stock levels, reorder points, and pricing.',
      },
    },
  },
};

// Low Stock Alert
export const LowStockAlert = {
  render: (args) => PartsInventory({
    parts: [
      {
        name: 'Pump Bearing',
        partNumber: 'PB-001',
        quantity: 15,
        minStock: 5,
        location: 'Warehouse A1',
        unitCost: 25.99
      },
      {
        name: 'Belt Drive',
        partNumber: 'BD-002',
        quantity: 3,
        minStock: 10,
        location: 'Warehouse A2',
        unitCost: 45.50
      },
      {
        name: 'Air Filter',
        partNumber: 'AF-003',
        quantity: 25,
        minStock: 15,
        location: 'Warehouse B1',
        unitCost: 12.75
      },
    ],
    showLowStock: true,
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Parts inventory filtered to show only items below minimum stock levels.',
      },
    },
  },
};

// Maintenance Schedule List
export const MaintenanceScheduleList = {
  render: (args) => MaintenanceSchedule({
    schedules: [
      {
        title: 'Quarterly Pump Inspection',
        asset: 'Cooling Pump A1',
        type: 'Preventive Maintenance',
        priority: 'high',
        date: 'Oct 15, 2024',
        time: '09:00 AM'
      },
      {
        title: 'Belt Tension Check',
        asset: 'Conveyor B2',
        type: 'Routine Check',
        priority: 'medium',
        date: 'Oct 18, 2024',
        time: '02:00 PM'
      },
      {
        title: 'Filter Replacement',
        asset: 'HVAC Unit C3',
        type: 'Preventive Maintenance',
        priority: 'low',
        date: 'Oct 22, 2024',
        time: '10:30 AM'
      },
    ],
    viewMode: 'list',
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Maintenance schedule in list view with priorities and timing.',
      },
    },
  },
};

// Maintenance Schedule Calendar
export const MaintenanceCalendar = {
  render: (args) => MaintenanceSchedule({
    schedules: [],
    viewMode: 'calendar',
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Maintenance schedule in calendar view for visual planning.',
      },
    },
  },
};