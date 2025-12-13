/**
 * 🚀 VITE CONFIGURATION FOR CHATTERFIX CMMS
 * 
 * Modern build system with optimization for Alpine.js, Tailwind CSS, and glassmorphism design
 */

import { defineConfig } from 'vite';
import { resolve } from 'path';
import { VitePWA } from 'vite-plugin-pwa';
import legacy from '@vitejs/plugin-legacy';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  // Base configuration
  base: '/static/',
  root: '.',
  
  // Input files
  build: {
    outDir: 'app/static/dist',
    emptyOutDir: true,
    assetsDir: 'assets',
    sourcemap: true,
    minify: 'terser',
    
    // Input configuration for multi-page application
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'app/static/js/main.js'),
        'ui-components': resolve(__dirname, 'app/static/js/ui-components.js'),
        'demo-system': resolve(__dirname, 'app/static/js/demo-system.js'),
        'ai-chat-popup': resolve(__dirname, 'app/static/js/ai-chat-popup.js'),
        styles: resolve(__dirname, 'app/static/css/style.css'),
        'design-tokens': resolve(__dirname, 'app/static/css/design-tokens.css')
      },
      
      // External dependencies (loaded via CDN)
      external: [
        'alpinejs',
        'gsap',
        'apexcharts',
        'lottie-web',
        'flatpickr',
        'choices.js',
        'chart.js'
      ],
      
      output: {
        // Chunk splitting for optimal loading
        manualChunks: {
          vendor: ['alpinejs'],
          animations: ['gsap'],
          charts: ['apexcharts', 'chart.js'],
          forms: ['flatpickr', 'choices.js'],
          utils: ['lottie-web']
        },
        
        // Asset naming
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `images/[name]-[hash].${ext}`;
          }
          if (/woff2?|eot|ttf|otf/i.test(ext)) {
            return `fonts/[name]-[hash].${ext}`;
          }
          return `css/[name]-[hash].${ext}`;
        }
      }
    },
    
    // Terser configuration for better minification
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info'],
        passes: 2
      },
      mangle: {
        safari10: true
      },
      format: {
        comments: false
      }
    },
    
    // CSS code splitting
    cssCodeSplit: true,
    
    // Asset inline threshold (8kb)
    assetsInlineLimit: 8192
  },
  
  // Development server configuration
  server: {
    host: '0.0.0.0',
    port: 3000,
    open: false,
    cors: true,
    strictPort: false,
    
    // Proxy to FastAPI backend
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/ai': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/demo': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  
  // CSS preprocessing
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "app/static/css/design-tokens.css";`
      }
    },
    devSourcemap: true,
    modules: {
      localsConvention: 'camelCaseOnly'
    }
  },
  
  // Plugins configuration
  plugins: [
    // PWA configuration for offline functionality
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheKeyWillBeUsed: async ({ request }) => {
                return `${request.url}?version=1`;
              }
            }
          },
          {
            urlPattern: /^https:\/\/cdn\.jsdelivr\.net\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'cdn-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              }
            }
          }
        ]
      },
      manifest: {
        name: 'ChatterFix CMMS',
        short_name: 'ChatterFix',
        description: '🚀 The Most Advanced AI-Powered Maintenance Management System',
        theme_color: '#667eea',
        background_color: '#1a1a2e',
        display: 'standalone',
        orientation: 'portrait-primary',
        start_url: '/demo',
        icons: [
          {
            src: '/static/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/static/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    }),
    
    // Legacy browser support
    legacy({
      targets: ['> 0.5%', 'last 2 versions', 'not dead', 'not ie 11'],
      additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
      modernPolyfills: true
    }),
    
    // Bundle analyzer
    visualizer({
      filename: 'bundle-analysis.html',
      open: false,
      gzipSize: true,
      brotliSize: true
    })
  ],
  
  // Optimization configuration
  optimizeDeps: {
    include: [
      'alpinejs',
      'gsap',
      'apexcharts',
      'chart.js',
      'flatpickr',
      'choices.js',
      'lottie-web'
    ],
    exclude: ['@vite/client', '@vite/env']
  },
  
  // Define global constants
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '2.0.0'),
    __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development')
  },
  
  // Resolve configuration
  resolve: {
    alias: {
      '@': resolve(__dirname, './app'),
      '@static': resolve(__dirname, './app/static'),
      '@css': resolve(__dirname, './app/static/css'),
      '@js': resolve(__dirname, './app/static/js'),
      '@images': resolve(__dirname, './app/static/images')
    }
  },
  
  // Environment variables
  envPrefix: 'VITE_',
  
  // Preview configuration (for production preview)
  preview: {
    host: '0.0.0.0',
    port: 4173,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  
  // Worker configuration
  worker: {
    format: 'es'
  },
  
  // JSON configuration
  json: {
    namedExports: true,
    stringify: false
  }
});