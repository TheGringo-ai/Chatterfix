/** @type { import('@storybook/html').Preview } */

// Inject ChatterFix CSS variables and base styles
const style = document.createElement('style');
style.textContent = `
  /* ChatterFix CMMS Design System CSS Variables */
  :root {
    --primary-dark: #0a0a0a;
    --secondary-dark: #16213e;
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --accent-purple: #667eea;
    --accent-purple-dark: #764ba2;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --text-muted: #808080;
    --text-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --bg-primary: #0a0a0a;
    --bg-secondary: #16213e;
    --bg-card: rgba(255, 255, 255, 0.05);
    --bg-gradient: linear-gradient(135deg, #0a0a0a 0%, #16213e 100%);
    --bg-blur: rgba(255, 255, 255, 0.1);
    --font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  /* Base styles for Storybook */
  body {
    font-family: var(--font-family) !important;
    background: var(--bg-gradient) !important;
    color: var(--text-primary) !important;
    margin: 0;
    padding: 0;
  }

  /* Button Styles */
  .btn-primary {
    background: var(--gradient-primary);
    color: var(--text-primary);
    border: none;
    border-radius: 50px;
    padding: 12px 32px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    text-decoration: none;
    display: inline-block;
    font-family: var(--font-family);
  }

  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  }

  .btn-secondary {
    background: transparent;
    color: var(--text-primary);
    border: 2px solid var(--accent-purple);
    border-radius: 50px;
    padding: 10px 30px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-block;
    font-family: var(--font-family);
  }

  .btn-secondary:hover {
    background: var(--gradient-primary);
    border-color: transparent;
    transform: translateY(-2px);
  }

  .btn-danger {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
    color: var(--text-primary);
    border: none;
    border-radius: 50px;
    padding: 12px 32px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-block;
    font-family: var(--font-family);
  }

  .btn-danger:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
  }

  /* Card Styles */
  .card {
    background: var(--bg-card);
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

  .feature-card {
    background: var(--bg-card);
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

  .stat-card {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    text-align: center;
    transition: all 0.3s ease;
  }

  .stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    border-color: rgba(102, 126, 234, 0.3);
  }

  .stat-number {
    font-size: 2.5rem;
    font-weight: 700;
    background: var(--text-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: block;
    margin-bottom: 8px;
  }

  .service-card {
    background: var(--bg-card);
    border-radius: 20px;
    padding: 32px;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
  }

  .service-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
    border-color: var(--accent-purple);
  }

  /* Status Badges */
  .status-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
  }

  .status-success {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
  }

  .status-warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
  }

  .status-error {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
  }

  .status-info {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
  }

  /* Form Styles */
  .form-group {
    margin-bottom: 20px;
  }

  .form-label {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 8px;
    display: block;
  }

  .form-input {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 12px 16px;
    color: var(--text-primary);
    font-family: var(--font-family);
    font-size: 1rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    width: 100%;
    box-sizing: border-box;
  }

  .form-input:focus {
    outline: none;
    border-color: var(--accent-purple);
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
  }

  .form-input::placeholder {
    color: var(--text-muted);
  }

  /* Navigation Styles */
  .navbar {
    background: rgba(10, 10, 10, 0.8);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 16px 0;
  }

  .navbar-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .navbar-brand {
    background: var(--text-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 1.25rem;
  }

  .navbar-nav {
    display: flex;
    gap: 24px;
  }

  .navbar-nav a {
    color: var(--text-secondary);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s ease;
  }

  .navbar-nav a:hover {
    color: var(--text-primary);
  }

  /* Table Styles */
  .table-container {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin: 24px 0;
    overflow-x: auto;
  }

  .chatterfix-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-family);
  }

  .chatterfix-table th {
    background: rgba(102, 126, 234, 0.1);
    color: var(--text-primary);
    font-weight: 600;
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

  /* Utility Classes */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 24px;
    margin-bottom: 48px;
  }

  /* Google Fonts Import */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
`;
document.head.appendChild(style);

const preview = {
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'chatterfix-dark',
      values: [
        {
          name: 'chatterfix-dark',
          value: 'linear-gradient(135deg, #0a0a0a 0%, #16213e 100%)',
        },
        {
          name: 'light',
          value: '#ffffff',
        },
      ],
    },
    docs: {
      story: {
        inline: true,
      },
      theme: {
        base: 'dark',
        brandTitle: 'ChatterFix CMMS Design System',
        colorPrimary: '#667eea',
        colorSecondary: '#764ba2',
        appBg: '#0a0a0a',
        appContentBg: '#16213e',
        textColor: '#ffffff',
      }
    },
    layout: 'padded',
  },
  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'ChatterFix theme',
      defaultValue: 'dark',
      toolbar: {
        icon: 'paintbrush',
        items: [
          { value: 'dark', title: 'Dark (Default)' },
          { value: 'light', title: 'Light' },
        ],
        dynamicTitle: true,
      },
    },
  },
};

export default preview;