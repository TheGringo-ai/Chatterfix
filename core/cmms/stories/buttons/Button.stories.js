import { fn } from '@storybook/test';

// Define the button component
const Button = ({ variant = 'primary', size = 'medium', label = 'Button', disabled = false, onClick, ...args }) => {
  const sizeClass = size === 'large' ? 'btn-large' : size === 'small' ? 'btn-small' : '';
  const disabledClass = disabled ? 'disabled' : '';
  
  const button = document.createElement('button');
  button.type = 'button';
  button.className = `btn-${variant} ${sizeClass} ${disabledClass}`.trim();
  button.innerText = label;
  button.disabled = disabled;
  
  // Add event listener for onclick only if provided
  if (onClick && typeof onClick === 'function') {
    button.addEventListener('click', onClick);
  }
  
  return button;
};

// Export default story configuration
export default {
  title: 'ChatterFix CMMS/Buttons',
  render: (args) => Button(args),
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Primary UI buttons for ChatterFix CMMS platform. These buttons follow the ChatterFix design system with gradients and consistent styling.',
      },
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'danger'],
      description: 'Button style variant',
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
      description: 'Button size',
    },
    label: {
      control: 'text',
      description: 'Button text label',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
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

// Primary button story
export const Primary = {
  args: {
    variant: 'primary',
    label: 'Create Work Order',
  },
  parameters: {
    docs: {
      description: {
        story: 'Primary button with ChatterFix gradient styling. Used for main actions like creating work orders, saving data, etc.',
      },
    },
  },
};

// Secondary button story
export const Secondary = {
  args: {
    variant: 'secondary',
    label: 'Cancel',
  },
  parameters: {
    docs: {
      description: {
        story: 'Secondary button with transparent background and border. Used for secondary actions.',
      },
    },
  },
};

// Danger button story
export const Danger = {
  args: {
    variant: 'danger',
    label: 'Delete Asset',
  },
  parameters: {
    docs: {
      description: {
        story: 'Danger button with red gradient. Used for destructive actions like deleting records.',
      },
    },
  },
};

// Disabled button story
export const Disabled = {
  args: {
    variant: 'primary',
    label: 'Submit',
    disabled: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Disabled button state. Used when actions are not available.',
      },
    },
  },
};

// Button sizes
export const Large = {
  args: {
    variant: 'primary',
    size: 'large',
    label: 'Schedule Maintenance',
  },
  parameters: {
    docs: {
      description: {
        story: 'Large button for important actions in the CMMS interface.',
      },
    },
  },
};

export const Small = {
  args: {
    variant: 'secondary',
    size: 'small',
    label: 'Edit',
  },
  parameters: {
    docs: {
      description: {
        story: 'Small button for compact interfaces and table actions.',
      },
    },
  },
};

// CMMS-specific use cases
export const WorkOrderActions = {
  render: () => {
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.gap = '12px';
    container.style.flexWrap = 'wrap';
    
    const buttons = [
      { variant: 'primary', label: 'Create Work Order' },
      { variant: 'secondary', label: 'View Details' },
      { variant: 'secondary', label: 'Assign Technician' },
      { variant: 'danger', label: 'Delete' },
    ];
    
    buttons.forEach(btnConfig => {
      const btn = Button(btnConfig);
      container.appendChild(btn);
    });
    
    return container;
  },
  parameters: {
    docs: {
      description: {
        story: 'Common button combinations used in Work Order management.',
      },
    },
  },
};

export const AssetManagement = {
  render: () => {
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.gap = '12px';
    container.style.flexWrap = 'wrap';
    
    const buttons = [
      { variant: 'primary', label: 'Add Asset' },
      { variant: 'secondary', label: 'Import Assets' },
      { variant: 'secondary', label: 'Export Data' },
      { variant: 'secondary', label: 'Generate Report' },
    ];
    
    buttons.forEach(btnConfig => {
      const btn = Button(btnConfig);
      container.appendChild(btn);
    });
    
    return container;
  },
  parameters: {
    docs: {
      description: {
        story: 'Button combinations for Asset Management workflows.',
      },
    },
  },
};