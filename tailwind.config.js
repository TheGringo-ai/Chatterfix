/**
 * 🌊 TAILWIND CSS CONFIGURATION FOR CHATTERFIX CMMS
 * 
 * Extended configuration with custom design tokens and glassmorphism utilities
 */

module.exports = {
  content: [
    './app/templates/**/*.html',
    './app/static/js/**/*.js',
    './app/**/*.py',
    './app/static/css/**/*.css'
  ],
  
  darkMode: ['class', '.dark-mode'],
  
  theme: {
    extend: {
      // 🌈 Color System with Design Tokens
      colors: {
        // Primary palette
        primary: {
          50: 'rgb(240 244 255)',
          100: 'rgb(224 231 255)',
          200: 'rgb(199 210 254)',
          300: 'rgb(165 180 252)',
          400: 'rgb(129 140 248)',
          500: 'rgb(102 126 234)', // Main accent
          600: 'rgb(91 33 182)',
          700: 'rgb(76 29 149)',
          800: 'rgb(55 48 163)',
          900: 'rgb(49 46 129)',
          DEFAULT: 'rgb(102 126 234)'
        },
        
        // Secondary palette
        secondary: {
          50: 'rgb(250 245 255)',
          100: 'rgb(243 232 255)',
          200: 'rgb(233 213 255)',
          300: 'rgb(216 180 254)',
          400: 'rgb(192 132 252)',
          500: 'rgb(118 75 162)', // Secondary accent
          600: 'rgb(147 51 234)',
          700: 'rgb(124 58 237)',
          800: 'rgb(107 33 168)',
          900: 'rgb(88 28 135)',
          DEFAULT: 'rgb(118 75 162)'
        },
        
        // CMMS Semantic Colors
        cmms: {
          blue: {
            light: 'rgb(133 193 233)',
            DEFAULT: 'rgb(52 152 219)',
            dark: 'rgb(41 128 185)'
          },
          green: {
            light: 'rgb(130 230 168)',
            DEFAULT: 'rgb(39 174 96)',
            dark: 'rgb(34 153 84)'
          },
          orange: {
            light: 'rgb(248 196 113)',
            DEFAULT: 'rgb(243 156 18)',
            dark: 'rgb(230 126 34)'
          },
          red: {
            light: 'rgb(241 148 138)',
            DEFAULT: 'rgb(231 76 60)',
            dark: 'rgb(192 57 43)'
          },
          purple: {
            light: 'rgb(187 143 206)',
            DEFAULT: 'rgb(155 89 182)',
            dark: 'rgb(142 68 173)'
          }
        },
        
        // Glass effect colors
        glass: {
          light: 'rgba(255, 255, 255, 0.1)',
          DEFAULT: 'rgba(255, 255, 255, 0.15)',
          heavy: 'rgba(255, 255, 255, 0.25)',
          dark: 'rgba(0, 0, 0, 0.1)'
        },
        
        // Status colors
        status: {
          success: 'rgb(39 174 96)',
          warning: 'rgb(243 156 18)',
          error: 'rgb(231 76 60)',
          info: 'rgb(52 152 219)',
          pending: 'rgb(155 89 182)'
        }
      },
      
      // 📐 Enhanced Spacing System
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '100': '25rem',
        '112': '28rem',
        '128': '32rem',
        '144': '36rem'
      },
      
      // 🔤 Typography System
      fontFamily: {
        sans: ['Outfit', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', 'monospace'],
        display: ['Outfit', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif']
      },
      
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '3rem' }],
        '6xl': ['3.75rem', { lineHeight: '3.75rem' }],
        '7xl': ['4.5rem', { lineHeight: '4.5rem' }],
        '8xl': ['6rem', { lineHeight: '6rem' }],
        '9xl': ['8rem', { lineHeight: '8rem' }]
      },
      
      // 📏 Border Radius System
      borderRadius: {
        '4xl': '2rem',
        '5xl': '3rem'
      },
      
      // 💫 Animation & Transitions
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'fade-out': 'fadeOut 0.3s ease-in',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.4s ease-out',
        'slide-left': 'slideLeft 0.4s ease-out',
        'slide-right': 'slideRight 0.4s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'scale-out': 'scaleOut 0.3s ease-in',
        'bounce-gentle': 'bounceGentle 0.6s ease-in-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'shimmer': 'shimmer 2s linear infinite'
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        fadeOut: {
          '0%': { opacity: '1', transform: 'translateY(0)' },
          '100%': { opacity: '0', transform: 'translateY(-10px)' }
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' }
        },
        slideDown: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(0)' }
        },
        slideLeft: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        slideRight: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' }
        },
        scaleOut: {
          '0%': { opacity: '1', transform: 'scale(1)' },
          '100%': { opacity: '0', transform: 'scale(0.9)' }
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(-5%)' },
          '50%': { transform: 'translateY(0)' }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        },
        glow: {
          '0%': { 'box-shadow': '0 0 5px rgba(102, 126, 234, 0.5)' },
          '100%': { 'box-shadow': '0 0 20px rgba(102, 126, 234, 0.8)' }
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        }
      },
      
      // 🌈 Gradient System
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-glass': 'linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05))',
        'gradient-primary': 'linear-gradient(135deg, rgb(102 126 234), rgb(118 75 162))',
        'gradient-cmms': 'linear-gradient(135deg, rgb(52 152 219), rgb(39 174 96))',
        'shimmer-gradient': 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)'
      },
      
      // 💎 Box Shadow System
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        'glass-light': '0 4px 16px rgba(0, 0, 0, 0.08)',
        'glass-heavy': '0 12px 48px rgba(0, 0, 0, 0.18)',
        'glass-inset': 'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
        'neon': '0 0 20px rgba(102, 126, 234, 0.5)',
        'neon-strong': '0 0 40px rgba(102, 126, 234, 0.8)',
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)'
      },
      
      // 🔥 Backdrop Filter Support
      backdropBlur: {
        'xs': '2px',
        '4xl': '72px',
        '5xl': '96px'
      },
      
      // 📱 Screen Sizes
      screens: {
        'xs': '475px',
        '3xl': '1600px',
        '4xl': '1920px'
      },
      
      // 🎯 Z-Index Scale
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100'
      },
      
      // 🔧 Layout & Component Tokens
      height: {
        'screen-small': '100dvh',
        'screen-large': '100lvh'
      },
      
      maxHeight: {
        '128': '32rem',
        '144': '36rem'
      },
      
      // 🎨 CSS Variables Integration
      textColor: {
        'primary': 'var(--text-primary)',
        'secondary': 'var(--text-secondary)',
        'muted': 'var(--text-muted)',
        'inverse': 'var(--text-inverse)'
      },
      
      backgroundColor: {
        'primary': 'var(--bg-primary)',
        'secondary': 'var(--bg-secondary)',
        'tertiary': 'var(--bg-tertiary)',
        'glass': 'var(--bg-glass)',
        'glass-light': 'var(--bg-glass-light)',
        'glass-heavy': 'var(--bg-glass-heavy)'
      },
      
      borderColor: {
        'glass': 'var(--border-glass)',
        'glass-light': 'var(--border-glass-light)',
        'glass-heavy': 'var(--border-glass-heavy)'
      },
      
      // 🔤 Letter Spacing
      letterSpacing: {
        'widest': '0.25em'
      },
      
      // 📐 Aspect Ratio
      aspectRatio: {
        '4/3': '4 / 3',
        '3/2': '3 / 2',
        '2/3': '2 / 3',
        '9/16': '9 / 16'
      }
    }
  },
  
  // 🔌 Plugins
  plugins: [
    // Forms plugin for better form styling
    require('@tailwindcss/forms')({
      strategy: 'class'
    }),
    
    // Typography plugin
    require('@tailwindcss/typography'),
    
    // Custom utilities plugin
    function({ addUtilities, theme }) {
      const glassmorphismUtilities = {
        // Glass effect utilities
        '.glass-effect': {
          'background': 'var(--bg-glass)',
          'backdrop-filter': 'blur(20px)',
          'border': 'var(--border-glass)',
          '-webkit-backdrop-filter': 'blur(20px)'
        },
        
        '.glass-card': {
          'background': 'var(--bg-glass-light)',
          'backdrop-filter': 'blur(20px)',
          'border': 'var(--border-glass)',
          'border-radius': theme('borderRadius.2xl'),
          'box-shadow': 'var(--shadow-glass)',
          '-webkit-backdrop-filter': 'blur(20px)'
        },
        
        '.glass-button': {
          'background': 'var(--bg-glass)',
          'backdrop-filter': 'blur(10px)',
          'border': 'var(--border-glass)',
          'border-radius': theme('borderRadius.xl'),
          'transition': 'all 200ms cubic-bezier(0, 0, 0.2, 1)',
          '-webkit-backdrop-filter': 'blur(10px)'
        },
        
        '.glass-input': {
          'background': 'var(--bg-glass)',
          'backdrop-filter': 'blur(10px)',
          'border': 'var(--border-glass)',
          'border-radius': theme('borderRadius.lg'),
          'transition': 'all 200ms cubic-bezier(0, 0, 0.2, 1)',
          '-webkit-backdrop-filter': 'blur(10px)'
        },
        
        // Text utilities
        '.text-gradient': {
          'background': 'var(--text-gradient)',
          '-webkit-background-clip': 'text',
          '-webkit-text-fill-color': 'transparent',
          'background-clip': 'text'
        },
        
        // Animation utilities
        '.gpu-layer': {
          'transform': 'translate3d(0, 0, 0)',
          'backface-visibility': 'hidden',
          'will-change': 'transform'
        },
        
        // Hover effects
        '.hover-lift': {
          'transition': 'transform 200ms cubic-bezier(0, 0, 0.2, 1)',
          '&:hover': {
            'transform': 'translateY(-2px)'
          }
        },
        
        '.hover-scale': {
          'transition': 'transform 200ms cubic-bezier(0, 0, 0.2, 1)',
          '&:hover': {
            'transform': 'scale(1.02)'
          }
        },
        
        // Shimmer effect
        '.shimmer': {
          'position': 'relative',
          'overflow': 'hidden',
          '&::after': {
            'content': '""',
            'position': 'absolute',
            'top': '0',
            'right': '0',
            'bottom': '0',
            'left': '0',
            'background': theme('backgroundImage.shimmer-gradient'),
            'animation': 'shimmer 2s linear infinite'
          }
        }
      };
      
      addUtilities(glassmorphismUtilities);
    }
  ]
};