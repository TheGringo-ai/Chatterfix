# ChatterFix CMMS Storybook Component Library

This Storybook contains the complete component library for the ChatterFix CMMS platform, showcasing all UI components, patterns, and design guidelines for building consistent maintenance management interfaces.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- npm or yarn package manager

### Installation
```bash
# Install dependencies
npm install

# Start Storybook development server
npm run storybook

# Build static Storybook for deployment
npm run build-storybook
```

## 📚 Component Library Structure

### Core Components
- **Buttons** (`/stories/buttons/`) - Primary, secondary, and danger actions
- **Cards** (`/stories/cards/`) - Content containers with various styles
- **Forms** (`/stories/forms/`) - Input fields, selects, and complete form layouts
- **Navigation** (`/stories/navigation/`) - Navbar, breadcrumbs, tabs, and side navigation

### CMMS-Specific Components
- **Work Order Management** (`/stories/components/`) - Lists, tables, and management interfaces
- **Asset Management** - Grid views and detail cards for equipment
- **Parts Inventory** - Stock levels, reorder alerts, and inventory management
- **Maintenance Scheduling** - Calendar and list views for PM planning
- **KPI Dashboards** - Metrics and performance indicator displays

## 🎨 Design System

### Color Palette
```css
/* Primary Colors */
--accent-purple: #667eea
--accent-purple-dark: #764ba2

/* Status Colors */
--status-success: #10b981
--status-warning: #f59e0b  
--status-error: #ef4444
--status-info: #3b82f6

/* Background Colors */
--bg-primary: #0a0a0a
--bg-secondary: #16213e
--bg-card: rgba(255, 255, 255, 0.05)
```

### Typography
- **Font Family**: Inter (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700, 800
- **Primary Text**: #ffffff
- **Secondary Text**: #b0b0b0
- **Muted Text**: #808080

### Component Classes
```css
/* Buttons */
.btn-primary    /* Main actions */
.btn-secondary  /* Secondary actions */
.btn-danger     /* Destructive actions */

/* Cards */
.card           /* Basic content container */
.feature-card   /* Feature showcase */
.stat-card      /* Statistics display */
.service-card   /* Service navigation */

/* Status Badges */
.status-badge   /* Base badge */
.status-success /* Green status */
.status-warning /* Yellow/orange status */
.status-error   /* Red status */
.status-info    /* Blue status */

/* Forms */
.form-group     /* Field container */
.form-label     /* Field labels */
.form-input     /* Input fields */

/* Tables */
.chatterfix-table    /* Data tables */
.table-container     /* Table wrapper */
```

## 🔧 Development Guidelines

### Creating New Components

1. **Create Story File**: Add to appropriate category in `/stories/`
2. **Define Component**: Create reusable component function
3. **Add Stories**: Create multiple story variations
4. **Document Props**: Use argTypes for interactive controls
5. **Add Documentation**: Include description and usage examples

### Story Template
```javascript
import { fn } from '@storybook/test';

const MyComponent = ({ prop1, prop2, ...args }) => {
  const element = document.createElement('div');
  // Component logic here
  return element;
};

export default {
  title: 'ChatterFix CMMS/Category/ComponentName',
  parameters: {
    docs: {
      description: {
        component: 'Component description here.',
      },
    },
  },
  argTypes: {
    prop1: {
      control: 'text',
      description: 'Description of prop1',
    },
  },
  args: {
    onClick: fn(),
  },
};

export const Default = {
  args: {
    prop1: 'default value',
  },
};
```

### CSS Styling
- Use CSS custom properties (variables) for consistency
- Follow BEM methodology for custom classes
- Ensure dark theme compatibility
- Include hover and focus states
- Maintain responsive design principles

## 📱 Responsive Design

All components follow mobile-first design principles:

```css
/* Mobile: Default styles */
/* Tablet: 768px+ */
@media (min-width: 768px) {
  /* Tablet styles */
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  /* Desktop styles */
}
```

## ♿ Accessibility

### Guidelines
- Maintain WCAG AA compliance
- Use semantic HTML elements
- Provide keyboard navigation
- Include ARIA labels where needed
- Ensure sufficient color contrast (4.5:1 minimum)

### Testing
- Test with keyboard navigation
- Verify screen reader compatibility
- Check color contrast ratios
- Validate HTML semantics

## 🎯 CMMS-Specific Patterns

### Work Order Components
- Priority indicators (color-coded)
- Status badges with clear meanings
- Quick action buttons
- Assignee information display

### Asset Management
- Status indicators (operational, maintenance, down)
- Maintenance schedule displays
- Location and type information
- Action buttons for common tasks

### Parts Inventory
- Stock level indicators
- Low stock alerts
- Reorder functionality
- Cost and location information

### Maintenance Scheduling
- Calendar views
- Priority-based sorting
- Time and date displays
- Asset association

## 🚀 Deployment

### Static Build
```bash
# Build static Storybook
npm run build-storybook

# Output will be in ./storybook-static/
```

### Docker Deployment
```dockerfile
FROM nginx:alpine
COPY storybook-static /usr/share/nginx/html
EXPOSE 80
```

### Cloud Run Deployment
```bash
# Build container
docker build -t chatterfix-storybook .

# Tag for Google Cloud Registry
docker tag chatterfix-storybook gcr.io/PROJECT_ID/chatterfix-storybook

# Push to registry
docker push gcr.io/PROJECT_ID/chatterfix-storybook

# Deploy to Cloud Run
gcloud run deploy chatterfix-storybook \
  --image gcr.io/PROJECT_ID/chatterfix-storybook \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔍 Usage Examples

### In FastAPI Templates
```html
<!-- Use component classes in your templates -->
<div class="card">
  <h3>Work Order WO-2024-001</h3>
  <span class="status-badge status-warning">High Priority</span>
  <div class="card-actions">
    <button class="btn-primary">Assign</button>
    <button class="btn-secondary">View Details</button>
  </div>
</div>
```

### In JavaScript/Frontend
```javascript
// Import and use components
import { Button, Card, WorkOrderList } from './components';

// Create work order card
const card = Card({
  title: 'Pump Maintenance',
  status: { type: 'warning', label: 'High Priority' },
  actions: [
    { label: 'Assign', variant: 'primary' },
    { label: 'Details', variant: 'secondary' }
  ]
});

document.body.appendChild(card);
```

## 📖 Additional Resources

- [Storybook Documentation](https://storybook.js.org/docs)
- [ChatterFix CMMS Documentation](./CHATTERFIX_AI_PLATFORM_DOCUMENTATION.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE_MILESTONE.md)
- [Design System Guidelines](http://localhost:6006/?path=/docs/chatterfix-cmms-introduction--docs)

## 🤝 Contributing

1. Create feature branch from `main`
2. Add/modify components and stories
3. Test responsive behavior
4. Verify accessibility compliance
5. Update documentation
6. Create pull request

## 📞 Support

For questions or issues with the component library:
- Review existing stories for patterns
- Check design system documentation
- Refer to ChatterFix CMMS platform documentation
- Contact: yoyofred@gringosgambit.com

---

**Built for maintenance teams worldwide with ❤️**