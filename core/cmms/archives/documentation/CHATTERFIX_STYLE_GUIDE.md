# ChatterFix CMMS Style Guide

## Official Design Standards for All ChatterFix Services

This style guide ensures consistent branding across all ChatterFix microservices and future development. All services must adhere to these standards to maintain the professional, modern, AI-focused aesthetic of the ChatterFix platform.

## 🎨 Color Palette

### Primary Colors
```css
:root {
  --primary-dark: #0a0a0a;
  --secondary-dark: #16213e;
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-secondary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --accent-purple: #667eea;
  --accent-purple-dark: #764ba2;
}
```

### Text Colors
```css
:root {
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --text-muted: #808080;
  --text-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### Background Colors
```css
:root {
  --bg-primary: #0a0a0a;
  --bg-secondary: #16213e;
  --bg-card: rgba(255, 255, 255, 0.05);
  --bg-gradient: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
  --bg-blur: rgba(255, 255, 255, 0.1);
}
```

## 📝 Typography

### Font Stack
```css
:root {
  --font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

### Font Weights
```css
:root {
  --font-light: 300;
  --font-regular: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  --font-extrabold: 800;
}
```

### Font Sizes
```css
:root {
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  --text-5xl: 3rem;      /* 48px */
}
```

### Heading Styles
```css
h1 {
  font-size: var(--text-5xl);
  font-weight: var(--font-extrabold);
  background: var(--text-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
}

h2 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  line-height: 1.3;
}

h3 {
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  line-height: 1.4;
}
```

## 🔘 Button Styles

### Primary Button
```css
.btn-primary {
  background: var(--gradient-primary);
  color: var(--text-primary);
  border: none;
  border-radius: 50px;
  padding: 12px 32px;
  font-weight: var(--font-semibold);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}
```

### Secondary Button
```css
.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 2px solid var(--accent-purple);
  border-radius: 50px;
  padding: 10px 30px;
  font-weight: var(--font-semibold);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: var(--gradient-primary);
  border-color: transparent;
  transform: translateY(-2px);
}
```

### Danger Button
```css
.btn-danger {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  color: var(--text-primary);
  border: none;
  border-radius: 50px;
  padding: 12px 32px;
  font-weight: var(--font-semibold);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
}
```

## 📝 Form Styles

### Input Fields
```css
.form-input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 16px;
  color: var(--text-primary);
  font-family: var(--font-family);
  font-size: var(--text-base);
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-purple);
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
}

.form-input::placeholder {
  color: var(--text-muted);
}
```

### Select Fields
```css
.form-select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 16px;
  color: var(--text-primary);
  font-family: var(--font-family);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.form-select:focus {
  outline: none;
  border-color: var(--accent-purple);
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
}
```

### Labels
```css
.form-label {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  margin-bottom: 8px;
  display: block;
}
```

## 📊 Table Styles

### Table Container
```css
.table-container {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin: 24px 0;
}
```

### Table Styles
```css
.chatterfix-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-family);
}

.chatterfix-table th {
  background: rgba(102, 126, 234, 0.1);
  color: var(--text-primary);
  font-weight: var(--font-semibold);
  padding: 16px;
  text-align: left;
  border-bottom: 2px solid var(--accent-purple);
}

.chatterfix-table td {
  padding: 16px;
  color: var(--text-secondary);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.chatterfix-table tr:hover {
  background: rgba(102, 126, 234, 0.05);
}
```

## 🎯 Card Styles

### Standard Card
```css
.card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  border-color: rgba(102, 126, 234, 0.3);
}
```

### Feature Card
```css
.feature-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 32px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
  border-color: var(--accent-purple);
}
```

## 🔄 Animation Patterns

### Hover Animations
```css
.hover-lift {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.hover-lift:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
}
```

### Loading Animations
```css
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.loading {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

### Gradient Animation
```css
@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.animated-gradient {
  background: linear-gradient(-45deg, #667eea, #764ba2, #667eea, #764ba2);
  background-size: 400% 400%;
  animation: gradient-shift 4s ease infinite;
}
```

## 📱 Responsive Design

### Breakpoints
```css
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}
```

### Container Styles
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

@media (max-width: 768px) {
  .container {
    padding: 0 16px;
  }
}
```

### Grid System
```css
.grid {
  display: grid;
  gap: 24px;
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

@media (max-width: 768px) {
  .grid-2,
  .grid-3 {
    grid-template-columns: 1fr;
  }
}
```

## 🎨 Spacing System

### Padding and Margin
```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;
}
```

## 🔧 Navigation Styles

### Top Navigation
```css
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: rgba(10, 10, 10, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px 0;
  z-index: 1000;
}

.navbar-brand {
  background: var(--text-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: var(--font-bold);
  font-size: var(--text-xl);
}

.navbar-nav a {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: var(--font-medium);
  transition: color 0.3s ease;
}

.navbar-nav a:hover {
  color: var(--text-primary);
}
```

## 🎯 Status Indicators

### Success States
```css
.status-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}
```

### Warning States
```css
.status-warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}
```

### Error States
```css
.status-error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}
```

## 📋 Modal Styles

### Modal Overlay
```css
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
```

### Modal Content
```css
.modal-content {
  background: var(--bg-primary);
  border-radius: 20px;
  padding: 32px;
  max-width: 600px;
  width: 90%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}
```

## 🏗️ Layout Patterns

### Page Header
```css
.page-header {
  padding: var(--space-24) 0 var(--space-16);
  text-align: center;
  background: var(--bg-gradient);
}
```

### Section Spacing
```css
.section {
  padding: var(--space-20) 0;
}

.section-lg {
  padding: var(--space-24) 0;
}
```

## 🎨 Implementation Guidelines

### 1. All HTML Templates Must Include:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatterFix CMMS</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* ChatterFix CSS Variables and Styles */
        /* Include relevant sections from this style guide */
    </style>
</head>
```

### 2. CSS Organization:
- Include CSS variables at the top of each file
- Use consistent naming conventions
- Group related styles together
- Include responsive breakpoints where needed

### 3. Accessibility Requirements:
- Maintain sufficient color contrast
- Include focus states for all interactive elements
- Use semantic HTML elements
- Provide alt text for images

### 4. Performance Considerations:
- Use CSS transforms for animations
- Minimize use of backdrop-filter on mobile
- Optimize images and use appropriate formats
- Minimize CSS bundle size

## 🚀 Future Development Standards

### New Feature Requirements:
1. All new features must use the ChatterFix design system
2. Include responsive design from the start
3. Follow accessibility guidelines
4. Use established animation patterns
5. Maintain consistent spacing and typography

### AI Team Collaboration:
1. Reference this style guide for all UI changes
2. Test designs across all breakpoints
3. Validate color contrast and accessibility
4. Document any new patterns or components
5. Maintain backward compatibility

### Quality Checklist:
- [ ] Uses ChatterFix color palette
- [ ] Implements proper typography hierarchy
- [ ] Includes hover and focus states
- [ ] Responsive across all devices
- [ ] Follows spacing system
- [ ] Maintains accessibility standards
- [ ] Uses consistent animation patterns
- [ ] Passes visual quality review

---

**Note**: This style guide is the definitive source for ChatterFix design standards. All microservices, dashboards, and future features must adhere to these specifications to maintain brand consistency and professional quality across the platform.