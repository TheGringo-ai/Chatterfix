import { fn } from '@storybook/test';

// Define the card component
const Card = ({ 
  title = 'Card Title', 
  content = 'Card content goes here...', 
  type = 'default',
  status = null,
  actions = [],
  icon = null,
  stats = null,
  onClick,
  ...args 
}) => {
  const card = document.createElement('div');
  
  // Determine card classes based on type
  const cardClasses = {
    'default': 'card',
    'feature': 'feature-card',
    'stat': 'stat-card',
    'work-order': 'card work-order-card',
    'asset': 'card asset-card',
    'service': 'service-card'
  };
  
  card.className = cardClasses[type] || 'card';
  
  // Build card content
  let cardHTML = '';
  
  // Add icon if provided
  if (icon) {
    cardHTML += `<div class="card-icon" style="font-size: 2rem; margin-bottom: 1rem;">${icon}</div>`;
  }
  
  // Add title
  if (title) {
    const titleTag = type === 'stat' ? 'h3' : 'h2';
    cardHTML += `<${titleTag} class="card-title">${title}</${titleTag}>`;
  }
  
  // Add status badge if provided
  if (status) {
    const statusClass = status.type || 'info';
    cardHTML += `<span class="status-badge status-${statusClass}">${status.label}</span>`;
  }
  
  // Add stats if provided (for stat cards)
  if (stats) {
    cardHTML += `<div class="stat-number">${stats.number}</div>`;
    cardHTML += `<div class="stat-label">${stats.label}</div>`;
  } else {
    // Add content
    cardHTML += `<div class="card-content">${content}</div>`;
  }
  
  // Add actions if provided
  if (actions && actions.length > 0) {
    cardHTML += '<div class="card-actions" style="margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">';
    actions.forEach(action => {
      cardHTML += `<button class="btn-${action.variant || 'secondary'}" style="font-size: 0.875rem; padding: 8px 16px;">${action.label}</button>`;
    });
    cardHTML += '</div>';
  }
  
  card.innerHTML = cardHTML;
  
  // Add click handler if provided
  if (onClick && typeof onClick === 'function') {
    card.addEventListener('click', onClick);
    card.style.cursor = 'pointer';
  }
  
  return card;
};

// Export default story configuration
export default {
  title: 'ChatterFix CMMS/Cards',
  render: (args) => Card(args),
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Card components for displaying information in the ChatterFix CMMS platform. Cards support various types including work orders, assets, statistics, and features.',
      },
    },
  },
  argTypes: {
    title: {
      control: 'text',
      description: 'Card title',
    },
    content: {
      control: 'text',
      description: 'Card content',
    },
    type: {
      control: { type: 'select' },
      options: ['default', 'feature', 'stat', 'work-order', 'asset', 'service'],
      description: 'Card type/style',
    },
    status: {
      control: 'object',
      description: 'Status badge object with type and label',
    },
    icon: {
      control: 'text',
      description: 'Icon emoji or symbol',
    },
    onClick: {
      action: 'clicked',
      description: 'Click handler',
    },
  },
  args: {
    onClick: fn(),
  },
};

// Basic card
export const Default = {
  args: {
    title: 'Equipment Maintenance',
    content: 'Regular maintenance schedule for production equipment. Next service due in 7 days.',
  },
  parameters: {
    docs: {
      description: {
        story: 'Default card with basic content and hover effects.',
      },
    },
  },
};

// Feature card
export const Feature = {
  args: {
    type: 'feature',
    title: 'Smart Work Order Management',
    content: 'AI-powered scheduling and optimization that automatically prioritizes tasks based on criticality, resource availability, and maintenance history.',
    icon: '🛠️',
  },
  parameters: {
    docs: {
      description: {
        story: 'Feature card with icon, used for showcasing platform capabilities.',
      },
    },
  },
};

// Stat card
export const Statistics = {
  args: {
    type: 'stat',
    title: 'Open Work Orders',
    stats: {
      number: '24',
      label: 'Pending Tasks'
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Statistics card for displaying metrics and KPIs.',
      },
    },
  },
};

// Work Order card
export const WorkOrder = {
  args: {
    type: 'work-order',
    title: 'WO-2024-001: Pump Maintenance',
    content: 'Routine maintenance required for cooling system pump. Estimated duration: 4 hours.',
    status: {
      type: 'warning',
      label: 'High Priority'
    },
    actions: [
      { label: 'Assign', variant: 'primary' },
      { label: 'View Details', variant: 'secondary' },
    ],
  },
  parameters: {
    docs: {
      description: {
        story: 'Work order card with status badge and action buttons.',
      },
    },
  },
};

// Asset card
export const Asset = {
  args: {
    type: 'asset',
    title: 'Conveyor Belt System A1',
    content: 'Main production line conveyor. Last maintenance: 2024-09-15. Next scheduled: 2024-10-15.',
    status: {
      type: 'success',
      label: 'Operational'
    },
    actions: [
      { label: 'Schedule PM', variant: 'primary' },
      { label: 'View History', variant: 'secondary' },
    ],
  },
  parameters: {
    docs: {
      description: {
        story: 'Asset management card with operational status and maintenance actions.',
      },
    },
  },
};

// Service card (from dashboard)
export const Service = {
  args: {
    type: 'service',
    title: 'Work Orders',
    content: 'Complete work order management with Advanced AI scheduling and optimization',
    icon: '🛠️',
    status: {
      type: 'success',
      label: 'Active'
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Service card used in the main dashboard for navigation.',
      },
    },
  },
};

// Card variations showcase
export const CardVariations = {
  render: () => {
    const container = document.createElement('div');
    container.style.display = 'grid';
    container.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
    container.style.gap = '24px';
    container.style.maxWidth = '1200px';
    
    const cards = [
      {
        type: 'stat',
        title: 'Active Assets',
        stats: { number: '156', label: 'Equipment Items' }
      },
      {
        type: 'stat',
        title: 'Pending Work Orders',
        stats: { number: '24', label: 'Open Tasks' }
      },
      {
        type: 'stat',
        title: 'Parts in Stock',
        stats: { number: '1,247', label: 'Inventory Items' }
      },
      {
        type: 'work-order',
        title: 'Emergency Repair',
        content: 'Critical system failure in production line B.',
        status: { type: 'error', label: 'Urgent' },
        actions: [{ label: 'Respond', variant: 'danger' }]
      }
    ];
    
    cards.forEach(cardConfig => {
      const card = Card(cardConfig);
      container.appendChild(card);
    });
    
    return container;
  },
  parameters: {
    docs: {
      description: {
        story: 'Various card types used together in a dashboard layout.',
      },
    },
  },
};

// CMMS Dashboard Grid
export const DashboardGrid = {
  render: () => {
    const container = document.createElement('div');
    container.style.display = 'grid';
    container.style.gridTemplateColumns = 'repeat(auto-fit, minmax(250px, 1fr))';
    container.style.gap = '24px';
    container.style.maxWidth = '1000px';
    
    const services = [
      { title: 'Work Orders', icon: '🛠️', content: 'Complete work order management with Advanced AI scheduling' },
      { title: 'Assets', icon: '🏭', content: 'Asset lifecycle management with predictive analytics' },
      { title: 'Parts Inventory', icon: '🔧', content: 'Smart inventory control and automated procurement' },
      { title: 'AI Insights', icon: '🧠', content: 'Real-time analytics and maintenance recommendations' },
    ];
    
    services.forEach(service => {
      const card = Card({
        type: 'service',
        ...service,
        status: { type: 'success', label: 'Active' }
      });
      container.appendChild(card);
    });
    
    return container;
  },
  parameters: {
    docs: {
      description: {
        story: 'Service cards arranged in a dashboard grid layout.',
      },
    },
  },
};