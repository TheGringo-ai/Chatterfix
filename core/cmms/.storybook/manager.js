import { addons } from '@storybook/manager-api';
import { create } from '@storybook/theming/create';

const theme = create({
  base: 'dark',
  brandTitle: 'ChatterFix CMMS Design System',
  brandUrl: 'https://chatterfix.ai',
  brandImage: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjQwIiB2aWV3Qm94PSIwIDAgMjAwIDQwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8dGV4dCB4PSIxMCIgeT0iMjYiIGZvbnQtZmFtaWx5PSJJbnRlciwgc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjcwMCIgZm9udC1zaXplPSIyMCIgZmlsbD0idXJsKCNncmFkaWVudCkiPkNoYXR0ZXJGaXggQ01NUzwvdGV4dD4KPGR1ZnM+CjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZGllbnQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjAlIj4KPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzY2N2VlYTtzdG9wLW9wYWNpdHk6MSIgLz4KPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojNzY0YmEyO3N0b3Atb3BhY2l0eToxIiAvPgo8L2xpbmVhckdyYWRpZW50Pgo8L2RlZnM+Cjwvc3ZnPgo=',
  brandTarget: '_self',

  // Typography
  fontBase: '"Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif',
  fontCode: 'monospace',

  // Colors
  colorPrimary: '#667eea',
  colorSecondary: '#764ba2',

  // UI
  appBg: '#0a0a0a',
  appContentBg: '#16213e',
  appBorderColor: 'rgba(255, 255, 255, 0.1)',
  appBorderRadius: 8,

  // Text colors
  textColor: '#ffffff',
  textInverseColor: '#0a0a0a',

  // Toolbar default and active colors
  barTextColor: '#b0b0b0',
  barSelectedColor: '#667eea',
  barBg: 'rgba(10, 10, 10, 0.8)',

  // Form colors
  inputBg: 'rgba(255, 255, 255, 0.05)',
  inputBorder: 'rgba(255, 255, 255, 0.1)',
  inputTextColor: '#ffffff',
  inputBorderRadius: 8,
});

addons.setConfig({
  theme,
  panelPosition: 'bottom',
  showNav: true,
  showPanel: true,
  sidebar: {
    showRoots: false,
    collapsedRoots: ['other'],
  },
});