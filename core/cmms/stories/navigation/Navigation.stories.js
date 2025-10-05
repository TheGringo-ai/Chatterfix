import { fn } from '@storybook/test';

// Define navigation components
const Navbar = ({ 
  brand = 'ChatterFix CMMS', 
  links = [],
  showBackButton = false,
  backUrl = '/',
  onLinkClick = null,
  onBackClick = null,
  ...args 
}) => {
  const nav = document.createElement('nav');
  nav.className = 'navbar';
  
  const content = document.createElement('div');
  content.className = 'navbar-content';
  
  // Brand/Logo
  const brandEl = document.createElement('div');
  brandEl.className = 'navbar-brand';
  brandEl.textContent = brand;
  content.appendChild(brandEl);
  
  // Navigation links
  const navLinks = document.createElement('div');
  navLinks.className = 'navbar-nav';
  
  links.forEach(link => {
    const a = document.createElement('a');
    a.href = link.href || '#';
    a.textContent = link.label;
    if (link.active) {
      a.style.color = 'var(--text-primary)';
    }
    if (onLinkClick && typeof onLinkClick === 'function') {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        onLinkClick(link);
      });
    }
    navLinks.appendChild(a);
  });
  
  content.appendChild(navLinks);
  
  // Back button (if needed)
  if (showBackButton) {
    const backBtn = document.createElement('a');
    backBtn.href = backUrl;
    backBtn.className = 'nav-back';
    backBtn.textContent = '← Back';
    backBtn.style.marginLeft = 'auto';
    if (onBackClick && typeof onBackClick === 'function') {
      backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        onBackClick();
      });
    }
    content.appendChild(backBtn);
  }
  
  nav.appendChild(content);
  return nav;
};

// Breadcrumb component
const Breadcrumb = ({ 
  items = [],
  separator = '/',
  onItemClick = null,
  ...args 
}) => {
  const breadcrumb = document.createElement('nav');
  breadcrumb.style.padding = '16px 0';
  breadcrumb.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
  
  const list = document.createElement('div');
  list.style.display = 'flex';
  list.style.alignItems = 'center';
  list.style.gap = '8px';
  list.style.color = 'var(--text-secondary)';
  
  items.forEach((item, index) => {
    if (index > 0) {
      const sep = document.createElement('span');
      sep.textContent = separator;
      sep.style.color = 'var(--text-muted)';
      list.appendChild(sep);
    }
    
    if (item.href && index < items.length - 1) {
      const link = document.createElement('a');
      link.href = item.href;
      link.textContent = item.label;
      link.style.color = 'var(--accent-purple)';
      link.style.textDecoration = 'none';
      link.addEventListener('mouseover', () => {
        link.style.textDecoration = 'underline';
      });
      link.addEventListener('mouseout', () => {
        link.style.textDecoration = 'none';
      });
      if (onItemClick && typeof onItemClick === 'function') {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          onItemClick(item);
        });
      }
      list.appendChild(link);
    } else {
      const span = document.createElement('span');
      span.textContent = item.label;
      if (index === items.length - 1) {
        span.style.color = 'var(--text-primary)';
        span.style.fontWeight = '500';
      }
      list.appendChild(span);
    }
  });
  
  breadcrumb.appendChild(list);
  return breadcrumb;
};

// Tab navigation component
const TabNavigation = ({ 
  tabs = [],
  activeTab = null,
  onTabClick = null,
  ...args 
}) => {
  const tabContainer = document.createElement('div');
  tabContainer.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
  tabContainer.style.marginBottom = '24px';
  
  const tabList = document.createElement('div');
  tabList.style.display = 'flex';
  tabList.style.gap = '32px';
  
  tabs.forEach(tab => {
    const tabButton = document.createElement('button');
    tabButton.style.background = 'none';
    tabButton.style.border = 'none';
    tabButton.style.color = tab.id === activeTab ? 'var(--accent-purple)' : 'var(--text-secondary)';
    tabButton.style.fontSize = '1rem';
    tabButton.style.fontWeight = '500';
    tabButton.style.padding = '16px 0';
    tabButton.style.cursor = 'pointer';
    tabButton.style.borderBottom = tab.id === activeTab ? '2px solid var(--accent-purple)' : '2px solid transparent';
    tabButton.style.transition = 'all 0.3s ease';
    tabButton.textContent = tab.label;
    
    tabButton.addEventListener('mouseover', () => {
      if (tab.id !== activeTab) {
        tabButton.style.color = 'var(--text-primary)';
      }
    });
    
    tabButton.addEventListener('mouseout', () => {
      if (tab.id !== activeTab) {
        tabButton.style.color = 'var(--text-secondary)';
      }
    });
    
    if (onTabClick && typeof onTabClick === 'function') {
      tabButton.addEventListener('click', () => {
        onTabClick(tab);
      });
    }
    
    tabList.appendChild(tabButton);
  });
  
  tabContainer.appendChild(tabList);
  return tabContainer;
};

// Side navigation component
const SideNavigation = ({ 
  items = [],
  title = 'Navigation',
  onItemClick = null,
  ...args 
}) => {
  const sideNav = document.createElement('nav');
  sideNav.style.width = '250px';
  sideNav.style.background = 'var(--bg-card)';
  sideNav.style.borderRadius = '16px';
  sideNav.style.padding = '24px';
  sideNav.style.backdropFilter = 'blur(20px)';
  sideNav.style.border = '1px solid rgba(255, 255, 255, 0.1)';
  
  const titleEl = document.createElement('h3');
  titleEl.textContent = title;
  titleEl.style.color = 'var(--text-primary)';
  titleEl.style.marginBottom = '16px';
  titleEl.style.fontSize = '1.1rem';
  sideNav.appendChild(titleEl);
  
  const list = document.createElement('ul');
  list.style.listStyle = 'none';
  list.style.padding = '0';
  list.style.margin = '0';
  
  items.forEach(item => {
    const listItem = document.createElement('li');
    listItem.style.marginBottom = '8px';
    
    const link = document.createElement('a');
    link.href = item.href || '#';
    link.textContent = `${item.icon || ''} ${item.label}`;
    link.style.display = 'block';
    link.style.padding = '12px 16px';
    link.style.color = item.active ? 'var(--accent-purple)' : 'var(--text-secondary)';
    link.style.textDecoration = 'none';
    link.style.borderRadius = '8px';
    link.style.transition = 'all 0.3s ease';
    link.style.background = item.active ? 'rgba(102, 126, 234, 0.1)' : 'transparent';
    
    link.addEventListener('mouseover', () => {
      if (!item.active) {
        link.style.background = 'rgba(255, 255, 255, 0.05)';
        link.style.color = 'var(--text-primary)';
      }
    });
    
    link.addEventListener('mouseout', () => {
      if (!item.active) {
        link.style.background = 'transparent';
        link.style.color = 'var(--text-secondary)';
      }
    });
    
    if (onItemClick && typeof onItemClick === 'function') {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        onItemClick(item);
      });
    }
    
    listItem.appendChild(link);
    list.appendChild(listItem);
  });
  
  sideNav.appendChild(list);
  return sideNav;
};

// Export default story configuration
export default {
  title: 'ChatterFix CMMS/Navigation',
  render: (args) => Navbar(args),
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Navigation components for the ChatterFix CMMS platform including navbar, breadcrumbs, tabs, and side navigation.',
      },
    },
  },
  argTypes: {
    onLinkClick: {
      action: 'link-clicked',
      description: 'Navigation link click handler',
    },
    onTabClick: {
      action: 'tab-clicked',
      description: 'Tab click handler',
    },
    onItemClick: {
      action: 'item-clicked',
      description: 'Navigation item click handler',
    },
  },
  args: {
    onLinkClick: fn(),
    onTabClick: fn(),
    onItemClick: fn(),
  },
};

// Main navbar
export const MainNavbar = {
  render: (args) => Navbar({
    brand: 'ChatterFix CMMS',
    links: [
      { label: 'Dashboard', href: '/dashboard', active: true },
      { label: 'Work Orders', href: '/work-orders' },
      { label: 'Assets', href: '/assets' },
      { label: 'Parts', href: '/parts' },
      { label: 'Reports', href: '/reports' },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Main navigation bar with ChatterFix branding and primary navigation links.',
      },
    },
  },
};

// Dashboard navbar with back button
export const DashboardNavbar = {
  render: (args) => Navbar({
    brand: 'ChatterFix CMMS',
    showBackButton: true,
    backUrl: '/',
    links: [
      { label: 'Services', href: '#services' },
      { label: 'Settings', href: '#settings' },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Navigation bar with back button for sub-pages.',
      },
    },
  },
};

// Breadcrumb navigation
export const BreadcrumbNavigation = {
  render: (args) => Breadcrumb({
    items: [
      { label: 'Dashboard', href: '/dashboard' },
      { label: 'Work Orders', href: '/work-orders' },
      { label: 'WO-2024-001' },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Breadcrumb navigation showing current page location.',
      },
    },
  },
};

// Tab navigation
export const Tabs = {
  render: (args) => TabNavigation({
    tabs: [
      { id: 'overview', label: 'Overview' },
      { id: 'details', label: 'Details' },
      { id: 'history', label: 'History' },
      { id: 'attachments', label: 'Attachments' },
    ],
    activeTab: 'overview',
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Tab navigation for switching between different views of content.',
      },
    },
  },
};

// Side navigation
export const SideNav = {
  render: (args) => SideNavigation({
    title: 'Work Orders',
    items: [
      { label: 'All Work Orders', icon: '📋', active: true },
      { label: 'Open Tasks', icon: '🔓' },
      { label: 'In Progress', icon: '⚡' },
      { label: 'Completed', icon: '✅' },
      { label: 'Overdue', icon: '⚠️' },
      { label: 'Scheduled', icon: '📅' },
    ],
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Side navigation for filtering and organizing content.',
      },
    },
  },
};

// CMMS-specific navigation combinations
export const CMRSNavigation = {
  render: () => {
    const container = document.createElement('div');
    container.style.minHeight = '100vh';
    container.style.background = 'var(--bg-gradient)';
    
    // Main navbar
    const navbar = Navbar({
      brand: 'ChatterFix CMMS',
      links: [
        { label: 'Dashboard', href: '/dashboard', active: true },
        { label: 'Work Orders', href: '/work-orders' },
        { label: 'Assets', href: '/assets' },
        { label: 'Parts', href: '/parts' },
      ]
    });
    
    // Content area with breadcrumbs and tabs
    const content = document.createElement('div');
    content.style.padding = '24px';
    content.style.marginTop = '80px'; // Account for fixed navbar
    
    const breadcrumb = Breadcrumb({
      items: [
        { label: 'Dashboard', href: '/dashboard' },
        { label: 'Work Orders', href: '/work-orders' },
        { label: 'Create New' },
      ]
    });
    
    const tabs = TabNavigation({
      tabs: [
        { id: 'basic', label: 'Basic Info' },
        { id: 'details', label: 'Details' },
        { id: 'scheduling', label: 'Scheduling' },
        { id: 'parts', label: 'Parts' },
      ],
      activeTab: 'basic'
    });
    
    content.appendChild(breadcrumb);
    content.appendChild(tabs);
    
    // Sample content
    const sampleContent = document.createElement('div');
    sampleContent.style.padding = '24px';
    sampleContent.style.background = 'var(--bg-card)';
    sampleContent.style.borderRadius = '16px';
    sampleContent.style.border = '1px solid rgba(255, 255, 255, 0.1)';
    sampleContent.innerHTML = `
      <h3 style="color: var(--text-primary); margin-bottom: 16px;">Create Work Order - Basic Information</h3>
      <p style="color: var(--text-secondary);">This demonstrates how navigation components work together in the ChatterFix CMMS interface.</p>
    `;
    content.appendChild(sampleContent);
    
    container.appendChild(navbar);
    container.appendChild(content);
    
    return container;
  },
  parameters: {
    docs: {
      description: {
        story: 'Complete navigation system showing how different navigation components work together in a typical CMMS workflow.',
      },
    },
  },
};