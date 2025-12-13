/**
 * 🎨 POSTCSS CONFIGURATION FOR CHATTERFIX CMMS
 * 
 * CSS processing pipeline for design tokens, Tailwind CSS, and optimization
 */

export default {
  plugins: {
    // Import CSS files
    'postcss-import': {},
    
    // CSS nesting support
    'postcss-nesting': {},
    
    // Tailwind CSS integration
    'tailwindcss': {},
    
    // Autoprefixer for vendor prefixes
    'autoprefixer': {
      grid: true,
      flexbox: true,
      supports: true
    },
    
    // CSS optimization for production
    ...(process.env.NODE_ENV === 'production' ? {
      'cssnano': {
        preset: ['default', {
          discardComments: {
            removeAll: true
          },
          normalizeWhitespace: true,
          colormin: true,
          convertValues: true,
          discardDuplicates: true,
          discardEmpty: true,
          mergeIdents: false,
          mergeRules: true,
          minifyFontValues: true,
          minifyGradients: true,
          minifyParams: true,
          minifySelectors: true,
          normalizeCharset: true,
          normalizeDisplayValues: true,
          normalizePositions: true,
          normalizeRepeatStyle: true,
          normalizeString: true,
          normalizeTimingFunctions: true,
          normalizeUnicode: true,
          normalizeUrl: true,
          orderedValues: true,
          reduceIdents: false,
          reduceInitial: true,
          reduceTransforms: true,
          svgo: true,
          uniqueSelectors: true,
          zindex: false
        }]
      }
    } : {})
  }
};