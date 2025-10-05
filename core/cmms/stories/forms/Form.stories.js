import { fn } from '@storybook/test';

// Define form field components
const FormField = ({ 
  type = 'text', 
  label = 'Label', 
  placeholder = '', 
  value = '', 
  required = false,
  disabled = false,
  options = [],
  id = null,
  onChange = null,
  ...args 
}) => {
  const fieldId = id || `field-${Math.random().toString(36).substr(2, 9)}`;
  const container = document.createElement('div');
  container.className = 'form-group';
  
  let fieldHTML = `<label for="${fieldId}" class="form-label">${label}${required ? ' *' : ''}</label>`;
  
  if (type === 'select') {
    fieldHTML += `<select id="${fieldId}" class="form-input" ${disabled ? 'disabled' : ''}>`;
    if (placeholder) {
      fieldHTML += `<option value="">${placeholder}</option>`;
    }
    options.forEach(option => {
      const selected = option.value === value ? 'selected' : '';
      fieldHTML += `<option value="${option.value}" ${selected}>${option.label}</option>`;
    });
    fieldHTML += '</select>';
  } else if (type === 'textarea') {
    fieldHTML += `<textarea id="${fieldId}" class="form-input" placeholder="${placeholder}" ${disabled ? 'disabled' : ''}>${value}</textarea>`;
  } else {
    fieldHTML += `<input type="${type}" id="${fieldId}" class="form-input" placeholder="${placeholder}" value="${value}" ${required ? 'required' : ''} ${disabled ? 'disabled' : ''}>`;
  }
  
  container.innerHTML = fieldHTML;
  
  // Add event listeners
  const input = container.querySelector('.form-input');
  if (onChange && typeof onChange === 'function') {
    input.addEventListener('change', onChange);
  }
  
  return container;
};

// Work Order Form Component
const WorkOrderForm = ({ onSubmit = null, ...args }) => {
  const form = document.createElement('form');
  form.className = 'chatterfix-form';
  form.style.maxWidth = '600px';
  form.style.margin = '0 auto';
  
  // Form header
  const header = document.createElement('div');
  header.style.marginBottom = '2rem';
  header.innerHTML = `
    <h2 style="color: var(--text-primary); margin-bottom: 0.5rem;">Create Work Order</h2>
    <p style="color: var(--text-secondary);">Fill out the form below to create a new work order</p>
  `;
  form.appendChild(header);
  
  // Form fields
  const fields = [
    { type: 'text', label: 'Work Order Title', placeholder: 'Enter work order title', required: true },
    { 
      type: 'select', 
      label: 'Priority', 
      placeholder: 'Select priority',
      options: [
        { value: 'low', label: 'Low' },
        { value: 'medium', label: 'Medium' },
        { value: 'high', label: 'High' },
        { value: 'critical', label: 'Critical' }
      ],
      required: true 
    },
    { 
      type: 'select', 
      label: 'Asset', 
      placeholder: 'Select asset',
      options: [
        { value: 'pump-001', label: 'Pump System A1' },
        { value: 'conveyor-002', label: 'Conveyor Belt B2' },
        { value: 'hvac-003', label: 'HVAC Unit C3' },
        { value: 'generator-004', label: 'Backup Generator D4' }
      ]
    },
    { type: 'text', label: 'Assigned Technician', placeholder: 'Enter technician name' },
    { type: 'textarea', label: 'Description', placeholder: 'Describe the work to be performed...', required: true },
    { type: 'date', label: 'Due Date', required: true },
    { type: 'number', label: 'Estimated Hours', placeholder: '0' }
  ];
  
  fields.forEach(fieldConfig => {
    const field = FormField(fieldConfig);
    form.appendChild(field);
  });
  
  // Form actions
  const actions = document.createElement('div');
  actions.style.display = 'flex';
  actions.style.gap = '12px';
  actions.style.marginTop = '2rem';
  actions.style.justifyContent = 'flex-end';
  
  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.className = 'btn-primary';
  submitBtn.textContent = 'Create Work Order';
  
  const cancelBtn = document.createElement('button');
  cancelBtn.type = 'button';
  cancelBtn.className = 'btn-secondary';
  cancelBtn.textContent = 'Cancel';
  
  actions.appendChild(cancelBtn);
  actions.appendChild(submitBtn);
  form.appendChild(actions);
  
  // Event handlers
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (onSubmit && typeof onSubmit === 'function') onSubmit(e);
  });
  
  return form;
};

// Asset Form Component
const AssetForm = ({ onSubmit = null, ...args }) => {
  const form = document.createElement('form');
  form.className = 'chatterfix-form';
  form.style.maxWidth = '600px';
  form.style.margin = '0 auto';
  
  // Form header
  const header = document.createElement('div');
  header.style.marginBottom = '2rem';
  header.innerHTML = `
    <h2 style="color: var(--text-primary); margin-bottom: 0.5rem;">Add Asset</h2>
    <p style="color: var(--text-secondary);">Register a new asset in the system</p>
  `;
  form.appendChild(header);
  
  // Form fields
  const fields = [
    { type: 'text', label: 'Asset Name', placeholder: 'Enter asset name', required: true },
    { type: 'text', label: 'Asset ID/Tag', placeholder: 'Enter unique asset identifier', required: true },
    { 
      type: 'select', 
      label: 'Asset Type', 
      placeholder: 'Select asset type',
      options: [
        { value: 'pump', label: 'Pump' },
        { value: 'motor', label: 'Motor' },
        { value: 'conveyor', label: 'Conveyor' },
        { value: 'hvac', label: 'HVAC System' },
        { value: 'generator', label: 'Generator' },
        { value: 'compressor', label: 'Compressor' }
      ],
      required: true 
    },
    { type: 'text', label: 'Location', placeholder: 'Building, Floor, Room', required: true },
    { type: 'text', label: 'Manufacturer', placeholder: 'Equipment manufacturer' },
    { type: 'text', label: 'Model Number', placeholder: 'Model number' },
    { type: 'date', label: 'Installation Date' },
    { type: 'text', label: 'Serial Number', placeholder: 'Serial number' },
    { type: 'textarea', label: 'Description', placeholder: 'Additional asset details...' }
  ];
  
  fields.forEach(fieldConfig => {
    const field = FormField(fieldConfig);
    form.appendChild(field);
  });
  
  // Form actions
  const actions = document.createElement('div');
  actions.style.display = 'flex';
  actions.style.gap = '12px';
  actions.style.marginTop = '2rem';
  actions.style.justifyContent = 'flex-end';
  
  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.className = 'btn-primary';
  submitBtn.textContent = 'Add Asset';
  
  const cancelBtn = document.createElement('button');
  cancelBtn.type = 'button';
  cancelBtn.className = 'btn-secondary';
  cancelBtn.textContent = 'Cancel';
  
  actions.appendChild(cancelBtn);
  actions.appendChild(submitBtn);
  form.appendChild(actions);
  
  // Event handlers
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (onSubmit && typeof onSubmit === 'function') onSubmit(e);
  });
  
  return form;
};

// Export default story configuration
export default {
  title: 'ChatterFix CMMS/Forms',
  render: (args) => FormField(args),
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Form components for data entry in the ChatterFix CMMS platform. Includes form fields, validation, and complete form layouts.',
      },
    },
  },
  argTypes: {
    onSubmit: {
      action: 'submitted',
      description: 'Form submission handler',
    },
    onChange: {
      action: 'changed',
      description: 'Field change handler',
    },
  },
  args: {
    onSubmit: fn(),
    onChange: fn(),
  },
};

// Individual form field stories
export const TextInput = {
  render: (args) => FormField({
    type: 'text',
    label: 'Asset Name',
    placeholder: 'Enter asset name',
    required: true,
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Basic text input field with ChatterFix styling.',
      },
    },
  },
};

export const SelectDropdown = {
  render: (args) => FormField({
    type: 'select',
    label: 'Work Order Priority',
    placeholder: 'Select priority level',
    options: [
      { value: 'low', label: 'Low Priority' },
      { value: 'medium', label: 'Medium Priority' },
      { value: 'high', label: 'High Priority' },
      { value: 'critical', label: 'Critical Priority' }
    ],
    required: true,
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Select dropdown field for choosing from predefined options.',
      },
    },
  },
};

export const TextArea = {
  render: (args) => FormField({
    type: 'textarea',
    label: 'Work Description',
    placeholder: 'Describe the maintenance work required...',
    required: true,
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Textarea field for longer text input.',
      },
    },
  },
};

export const DateInput = {
  render: (args) => FormField({
    type: 'date',
    label: 'Due Date',
    required: true,
    ...args
  }),
  parameters: {
    docs: {
      description: {
        story: 'Date input field for scheduling.',
      },
    },
  },
};

// Complete form stories
export const WorkOrderForm_Story = {
  render: (args) => WorkOrderForm(args),
  parameters: {
    docs: {
      description: {
        story: 'Complete work order creation form with all necessary fields.',
      },
    },
  },
};

export const AssetForm_Story = {
  render: (args) => AssetForm(args),
  parameters: {
    docs: {
      description: {
        story: 'Complete asset registration form for adding new equipment.',
      },
    },
  },
};

// Form field states
export const FieldStates = {
  render: () => {
    const container = document.createElement('div');
    container.style.display = 'grid';
    container.style.gap = '24px';
    container.style.maxWidth = '400px';
    
    const states = [
      { label: 'Normal State', value: 'Normal input' },
      { label: 'Required Field', value: 'Required input', required: true },
      { label: 'Disabled Field', value: 'Disabled input', disabled: true },
      { label: 'With Error', value: 'Invalid input', error: true }
    ];
    
    states.forEach(state => {
      const field = FormField({
        type: 'text',
        label: state.label,
        value: state.value,
        required: state.required,
        disabled: state.disabled,
        placeholder: 'Enter value...'
      });
      
      if (state.error) {
        const input = field.querySelector('.form-input');
        input.style.borderColor = '#ef4444';
        input.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.1)';
      }
      
      container.appendChild(field);
    });
    
    return container;
  },
  parameters: {
    docs: {
      description: {
        story: 'Different states of form fields including normal, required, disabled, and error states.',
      },
    },
  },
};