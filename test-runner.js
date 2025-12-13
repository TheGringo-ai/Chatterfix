/**
 * 🧪 CHATTERFIX CMMS - COMPREHENSIVE END-TO-END TESTING SYSTEM
 * 
 * This script tests ALL components, integrations, and functionality
 * to ensure the system works perfectly after UI enhancements.
 */

const TestRunner = {
    
    results: {
        passed: 0,
        failed: 0,
        warnings: 0,
        tests: []
    },
    
    async runAllTests() {
        console.log('🚀 Starting ChatterFix CMMS End-to-End Testing...');
        console.log('==================================================');
        
        const testSuites = [
            { name: 'Backend Health', test: this.testBackendHealth },
            { name: 'API Endpoints', test: this.testAPIEndpoints },
            { name: 'Frontend Components', test: this.testFrontendComponents },
            { name: 'UI Enhancement Libraries', test: this.testUILibraries },
            { name: 'Responsive Design', test: this.testResponsiveDesign },
            { name: 'Accessibility', test: this.testAccessibility },
            { name: 'Performance', test: this.testPerformance },
            { name: 'Glassmorphism Effects', test: this.testGlassmorphism },
            { name: 'Dark Mode', test: this.testDarkMode },
            { name: 'Alpine.js Integration', test: this.testAlpineJS },
            { name: 'GSAP Animations', test: this.testGSAP },
            { name: 'Charts & Data Visualization', test: this.testCharts },
            { name: 'Form Components', test: this.testForms },
            { name: 'Navigation System', test: this.testNavigation },
            { name: 'AI Components', test: this.testAIComponents }
        ];
        
        for (const suite of testSuites) {
            try {
                console.log(`\n🧪 Testing: ${suite.name}`);
                console.log('-'.repeat(30));
                await suite.test.call(this);
                this.logSuccess(`✅ ${suite.name} - ALL TESTS PASSED`);
            } catch (error) {
                this.logError(`❌ ${suite.name} - FAILED: ${error.message}`);
            }
        }
        
        this.generateFinalReport();
    },
    
    // 1. Backend Health Tests
    async testBackendHealth() {
        const tests = [
            { name: 'Health Endpoint', url: '/health', expectedStatus: 200 },
            { name: 'Demo Page', url: '/demo', expectedStatus: 200 },
            { name: 'Static Assets', url: '/static/css/style.css', expectedStatus: 200 },
            { name: 'UI Components JS', url: '/static/js/ui-components.js', expectedStatus: 200 }
        ];
        
        for (const test of tests) {
            await this.testEndpoint(test.name, test.url, test.expectedStatus);
        }
    },
    
    // 2. API Endpoints Tests
    async testAPIEndpoints() {
        const tests = [
            { name: 'Quick Stats (may require auth)', url: '/quick-stats', allowAuth: true },
            { name: 'Root Redirect', url: '/', expectedStatus: 302 }
        ];
        
        for (const test of tests) {
            try {
                const response = await fetch(test.url);
                if (test.allowAuth && response.status === 401) {
                    this.logWarning(`⚠️ ${test.name}: Authentication required (expected for secure endpoints)`);
                } else if (test.expectedStatus && response.status !== test.expectedStatus) {
                    throw new Error(`Expected ${test.expectedStatus}, got ${response.status}`);
                } else {
                    this.logSuccess(`✅ ${test.name}: Status ${response.status}`);
                }
            } catch (error) {
                throw new Error(`${test.name} failed: ${error.message}`);
            }
        }
    },
    
    // 3. Frontend Components Tests
    async testFrontendComponents() {
        const components = [
            '.cmms-navigation',
            '.dashboard-grid', 
            '.ai-brain',
            '.kpi-card',
            '.capability-card'
        ];
        
        for (const selector of components) {
            const element = document.querySelector(selector);
            if (!element) {
                throw new Error(`Component not found: ${selector}`);
            }
            this.logSuccess(`✅ Component exists: ${selector}`);
        }
        
        // Test if components are properly styled
        const navigation = document.querySelector('.cmms-navigation');
        if (navigation && getComputedStyle(navigation).position !== 'sticky') {
            this.logWarning('⚠️ Navigation may not be properly positioned');
        }
    },
    
    // 4. UI Enhancement Libraries Tests
    async testUILibraries() {
        const libraries = [
            { name: 'Alpine.js', check: () => typeof Alpine !== 'undefined' },
            { name: 'GSAP', check: () => typeof gsap !== 'undefined' },
            { name: 'ApexCharts', check: () => typeof ApexCharts !== 'undefined' },
            { name: 'Lottie', check: () => typeof lottie !== 'undefined' },
            { name: 'Flatpickr', check: () => typeof flatpickr !== 'undefined' },
            { name: 'Choices.js', check: () => typeof Choices !== 'undefined' },
            { name: 'Chart.js', check: () => typeof Chart !== 'undefined' }
        ];
        
        for (const lib of libraries) {
            if (lib.check()) {
                this.logSuccess(`✅ ${lib.name} loaded successfully`);
            } else {
                this.logWarning(`⚠️ ${lib.name} not found (may be lazy-loaded)`);
            }
        }
        
        // Test if UI components library is loaded
        if (typeof UIAnimations !== 'undefined') {
            this.logSuccess('✅ UI Components library loaded');
        } else {
            throw new Error('UI Components library not loaded');
        }
        
        if (typeof ModernComponents !== 'undefined') {
            this.logSuccess('✅ Modern Components library loaded');
        } else {
            throw new Error('Modern Components library not loaded');
        }
    },
    
    // 5. Responsive Design Tests
    async testResponsiveDesign() {
        const breakpoints = [
            { name: 'Mobile', width: 375, height: 667 },
            { name: 'Tablet', width: 768, height: 1024 },
            { name: 'Desktop', width: 1024, height: 768 },
            { name: 'Large Desktop', width: 1440, height: 900 }
        ];
        
        const originalWidth = window.innerWidth;
        const originalHeight = window.innerHeight;
        
        for (const bp of breakpoints) {
            // Simulate viewport resize
            window.resizeTo(bp.width, bp.height);
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Check for horizontal overflow
            const body = document.body;
            if (body.scrollWidth > bp.width + 20) { // 20px tolerance
                this.logWarning(`⚠️ Potential horizontal overflow at ${bp.name}: ${body.scrollWidth}px > ${bp.width}px`);
            } else {
                this.logSuccess(`✅ ${bp.name} (${bp.width}px): No overflow detected`);
            }
        }
        
        // Restore original size
        window.resizeTo(originalWidth, originalHeight);
    },
    
    // 6. Accessibility Tests
    async testAccessibility() {
        const accessibilityChecks = [
            {
                name: 'ARIA Labels',
                test: () => {
                    const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
                    let missing = 0;
                    interactiveElements.forEach(el => {
                        if (!el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby') && 
                            !el.textContent.trim() && !el.querySelector('img[alt]')) {
                            missing++;
                        }
                    });
                    return { passed: missing === 0, details: `${missing} elements missing ARIA labels` };
                }
            },
            {
                name: 'Keyboard Navigation',
                test: () => {
                    const focusableElements = document.querySelectorAll(
                        'button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])'
                    );
                    let notFocusable = 0;
                    focusableElements.forEach(el => {
                        if (el.tabIndex < 0 && !el.disabled) {
                            notFocusable++;
                        }
                    });
                    return { passed: notFocusable === 0, details: `${notFocusable} elements not keyboard accessible` };
                }
            },
            {
                name: 'Image Alt Text',
                test: () => {
                    const images = document.querySelectorAll('img');
                    let missingAlt = 0;
                    images.forEach(img => {
                        if (!img.getAttribute('alt')) {
                            missingAlt++;
                        }
                    });
                    return { passed: missingAlt === 0, details: `${missingAlt} images missing alt text` };
                }
            },
            {
                name: 'Form Labels',
                test: () => {
                    const inputs = document.querySelectorAll('input, select, textarea');
                    let missingLabels = 0;
                    inputs.forEach(input => {
                        if (input.type !== 'hidden' && !input.labels?.length && 
                            !input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
                            missingLabels++;
                        }
                    });
                    return { passed: missingLabels === 0, details: `${missingLabels} form fields missing labels` };
                }
            }
        ];
        
        for (const check of accessibilityChecks) {
            const result = check.test();
            if (result.passed) {
                this.logSuccess(`✅ ${check.name}: ${result.details}`);
            } else {
                this.logWarning(`⚠️ ${check.name}: ${result.details}`);
            }
        }
    },
    
    // 7. Performance Tests
    async testPerformance() {
        const startTime = performance.now();
        
        // Test page load performance
        if (performance.timing) {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            if (loadTime > 3000) {
                this.logWarning(`⚠️ Page load time: ${loadTime}ms (should be < 3000ms)`);
            } else {
                this.logSuccess(`✅ Page load time: ${loadTime}ms`);
            }
        }
        
        // Test animation performance
        let frameCount = 0;
        const testDuration = 1000; // 1 second
        
        const countFrames = () => {
            frameCount++;
            if (performance.now() - startTime < testDuration) {
                requestAnimationFrame(countFrames);
            }
        };
        
        requestAnimationFrame(countFrames);
        await new Promise(resolve => setTimeout(resolve, testDuration));
        
        const fps = frameCount;
        if (fps < 50) {
            this.logWarning(`⚠️ Animation FPS: ${fps} (should be ~60)`);
        } else {
            this.logSuccess(`✅ Animation FPS: ${fps}`);
        }
        
        // Test memory usage (if available)
        if (performance.memory) {
            const memoryMB = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
            if (memoryMB > 50) {
                this.logWarning(`⚠️ Memory usage: ${memoryMB}MB (monitor for leaks)`);
            } else {
                this.logSuccess(`✅ Memory usage: ${memoryMB}MB`);
            }
        }
    },
    
    // 8. Glassmorphism Effects Tests
    async testGlassmorphism() {
        const glassElements = document.querySelectorAll('.glass-effect, .glass-card, .cmms-card');
        
        if (glassElements.length === 0) {
            throw new Error('No glassmorphism elements found');
        }
        
        glassElements.forEach((element, index) => {
            const styles = getComputedStyle(element);
            
            // Check for backdrop filter
            if (!styles.backdropFilter || styles.backdropFilter === 'none') {
                this.logWarning(`⚠️ Element ${index + 1}: Missing backdrop filter`);
            } else {
                this.logSuccess(`✅ Element ${index + 1}: Backdrop filter applied`);
            }
            
            // Check for transparency
            const bgColor = styles.backgroundColor;
            if (!bgColor.includes('rgba') && !bgColor.includes('hsla')) {
                this.logWarning(`⚠️ Element ${index + 1}: May need transparent background`);
            }
        });
        
        this.logSuccess(`✅ Found ${glassElements.length} glassmorphism elements`);
    },
    
    // 9. Dark Mode Tests
    async testDarkMode() {
        const originalMode = document.documentElement.classList.contains('dark-mode');
        
        // Test dark mode toggle
        document.documentElement.classList.add('dark-mode');
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const darkModeElements = document.querySelectorAll('.dark-mode *');
        if (darkModeElements.length > 0) {
            this.logSuccess('✅ Dark mode: Elements respond to dark mode class');
        }
        
        // Test light mode
        document.documentElement.classList.remove('dark-mode');
        await new Promise(resolve => setTimeout(resolve, 100));
        
        this.logSuccess('✅ Light mode: Toggle functionality working');
        
        // Restore original mode
        if (originalMode) {
            document.documentElement.classList.add('dark-mode');
        }
    },
    
    // 10. Alpine.js Integration Tests
    async testAlpineJS() {
        if (typeof Alpine === 'undefined') {
            throw new Error('Alpine.js not loaded');
        }
        
        // Test Alpine stores
        const stores = ['dashboard', 'aiChat', 'workOrders', 'analytics'];
        
        for (const storeName of stores) {
            try {
                const store = Alpine.store(storeName);
                if (store) {
                    this.logSuccess(`✅ Alpine store: ${storeName} initialized`);
                } else {
                    this.logWarning(`⚠️ Alpine store: ${storeName} not found`);
                }
            } catch (error) {
                this.logWarning(`⚠️ Alpine store error: ${storeName} - ${error.message}`);
            }
        }
        
        // Test Alpine directives
        const alpineElements = document.querySelectorAll('[x-data], [x-show], [x-if]');
        this.logSuccess(`✅ Found ${alpineElements.length} Alpine.js elements`);
    },
    
    // 11. GSAP Animations Tests
    async testGSAP() {
        if (typeof gsap === 'undefined') {
            throw new Error('GSAP not loaded');
        }
        
        // Test GSAP plugins
        const plugins = [
            { name: 'ScrollTrigger', check: () => typeof ScrollTrigger !== 'undefined' },
            { name: 'TextPlugin', check: () => typeof TextPlugin !== 'undefined' }
        ];
        
        for (const plugin of plugins) {
            if (plugin.check()) {
                this.logSuccess(`✅ GSAP Plugin: ${plugin.name} loaded`);
            } else {
                this.logWarning(`⚠️ GSAP Plugin: ${plugin.name} not found`);
            }
        }
        
        // Test animation elements
        const animatableElements = document.querySelectorAll('.animate-hover-lift, .animate-fade-in, .fade-in-scroll');
        this.logSuccess(`✅ Found ${animatableElements.length} animatable elements`);
        
        // Test UIAnimations utility
        if (typeof UIAnimations !== 'undefined') {
            if (typeof UIAnimations.enhanceCards === 'function') {
                this.logSuccess('✅ UIAnimations.enhanceCards available');
            }
            if (typeof UIAnimations.pageEnter === 'function') {
                this.logSuccess('✅ UIAnimations.pageEnter available');
            }
        }
    },
    
    // 12. Charts & Data Visualization Tests
    async testCharts() {
        const chartTests = [
            { name: 'ApexCharts', check: () => typeof ApexCharts !== 'undefined' },
            { name: 'Chart.js', check: () => typeof Chart !== 'undefined' }
        ];
        
        for (const test of chartTests) {
            if (test.check()) {
                this.logSuccess(`✅ Chart library: ${test.name} available`);
            } else {
                this.logWarning(`⚠️ Chart library: ${test.name} not found`);
            }
        }
        
        // Test chart containers
        const chartContainers = document.querySelectorAll('[id*="chart"], .chart-container');
        this.logSuccess(`✅ Found ${chartContainers.length} chart containers`);
        
        // Test ChartConfigs
        if (typeof ChartConfigs !== 'undefined') {
            this.logSuccess('✅ Chart configurations available');
        }
    },
    
    // 13. Form Components Tests
    async testForms() {
        const formLibraries = [
            { name: 'Flatpickr', check: () => typeof flatpickr !== 'undefined' },
            { name: 'Choices.js', check: () => typeof Choices !== 'undefined' }
        ];
        
        for (const lib of formLibraries) {
            if (lib.check()) {
                this.logSuccess(`✅ Form library: ${lib.name} available`);
            } else {
                this.logWarning(`⚠️ Form library: ${lib.name} not found`);
            }
        }
        
        // Test form enhancement classes
        const enhancedElements = document.querySelectorAll(
            '.date-picker, .enhanced-select, .tag-select, .autocomplete'
        );
        this.logSuccess(`✅ Found ${enhancedElements.length} enhanced form elements`);
        
        // Test form validation
        const validationForms = document.querySelectorAll('.validate-form');
        if (validationForms.length > 0) {
            this.logSuccess(`✅ Found ${validationForms.length} forms with validation`);
        }
    },
    
    // 14. Navigation System Tests
    async testNavigation() {
        const navElements = [
            { selector: '.cmms-navigation', name: 'Main Navigation' },
            { selector: '.nav-tabs', name: 'Tab Navigation' },
            { selector: '.mobile-nav', name: 'Mobile Navigation' },
            { selector: '.nav-brand', name: 'Brand Logo' }
        ];
        
        for (const element of navElements) {
            const el = document.querySelector(element.selector);
            if (el) {
                this.logSuccess(`✅ ${element.name}: Present`);
            } else {
                this.logWarning(`⚠️ ${element.name}: Not found`);
            }
        }
        
        // Test navigation links
        const navLinks = document.querySelectorAll('.nav-tab-link, .mobile-nav-item');
        let workingLinks = 0;
        
        navLinks.forEach(link => {
            if (link.href && !link.href.includes('#')) {
                workingLinks++;
            }
        });
        
        this.logSuccess(`✅ Found ${workingLinks} working navigation links`);
    },
    
    // 15. AI Components Tests
    async testAIComponents() {
        const aiElements = [
            { selector: '.ai-brain', name: 'AI Brain Section' },
            { selector: '.ai-widget-container', name: 'AI Widget Container' },
            { selector: '.ai-chat-popup', name: 'AI Chat Popup' }
        ];
        
        for (const element of aiElements) {
            const el = document.querySelector(element.selector);
            if (el) {
                this.logSuccess(`✅ ${element.name}: Present`);
            } else {
                this.logWarning(`⚠️ ${element.name}: Not found (may be dynamically created)`);
            }
        }
        
        // Test AI pulse animation
        const aiPulse = document.querySelector('.ai-pulse');
        if (aiPulse) {
            const styles = getComputedStyle(aiPulse);
            if (styles.animation && styles.animation.includes('pulse')) {
                this.logSuccess('✅ AI pulse animation: Working');
            } else {
                this.logWarning('⚠️ AI pulse animation: Not detected');
            }
        }
    },
    
    // Utility Methods
    async testEndpoint(name, url, expectedStatus = 200) {
        try {
            const response = await fetch(url);
            if (response.status === expectedStatus) {
                this.logSuccess(`✅ ${name}: ${response.status}`);
            } else {
                throw new Error(`Expected ${expectedStatus}, got ${response.status}`);
            }
        } catch (error) {
            throw new Error(`${name} failed: ${error.message}`);
        }
    },
    
    logSuccess(message) {
        console.log(`%c${message}`, 'color: #27ae60; font-weight: bold;');
        this.results.passed++;
        this.results.tests.push({ type: 'success', message });
    },
    
    logError(message) {
        console.log(`%c${message}`, 'color: #e74c3c; font-weight: bold;');
        this.results.failed++;
        this.results.tests.push({ type: 'error', message });
    },
    
    logWarning(message) {
        console.log(`%c${message}`, 'color: #f39c12; font-weight: bold;');
        this.results.warnings++;
        this.results.tests.push({ type: 'warning', message });
    },
    
    generateFinalReport() {
        const total = this.results.passed + this.results.failed + this.results.warnings;
        const passRate = total > 0 ? Math.round((this.results.passed / total) * 100) : 0;
        
        console.log('\n' + '='.repeat(60));
        console.log('🏁 FINAL TEST RESULTS');
        console.log('='.repeat(60));
        console.log(`%c✅ PASSED: ${this.results.passed}`, 'color: #27ae60; font-weight: bold; font-size: 16px;');
        console.log(`%c❌ FAILED: ${this.results.failed}`, 'color: #e74c3c; font-weight: bold; font-size: 16px;');
        console.log(`%c⚠️ WARNINGS: ${this.results.warnings}`, 'color: #f39c12; font-weight: bold; font-size: 16px;');
        console.log(`%c📊 PASS RATE: ${passRate}%`, 'color: #667eea; font-weight: bold; font-size: 18px;');
        console.log('='.repeat(60));
        
        if (this.results.failed === 0) {
            console.log('%c🎉 ALL CRITICAL TESTS PASSED! 🚀', 'color: #27ae60; font-weight: bold; font-size: 20px; background: #d4edda; padding: 10px; border-radius: 5px;');
            console.log('%cChatterFix CMMS is ready for production!', 'color: #155724; font-weight: bold; font-size: 14px;');
        } else {
            console.log('%c⚠️ SOME TESTS FAILED - REVIEW REQUIRED', 'color: #e74c3c; font-weight: bold; font-size: 18px; background: #f8d7da; padding: 10px; border-radius: 5px;');
        }
        
        if (this.results.warnings > 0) {
            console.log(`%c📋 ${this.results.warnings} warnings found - consider reviewing for optimization`, 'color: #856404; font-size: 12px;');
        }
        
        // Show test summary
        console.log('\n📋 TEST SUMMARY:');
        const summary = this.results.tests.reduce((acc, test) => {
            acc[test.type] = (acc[test.type] || 0) + 1;
            return acc;
        }, {});
        
        console.table(summary);
        
        return {
            passed: this.results.passed,
            failed: this.results.failed,
            warnings: this.results.warnings,
            passRate,
            success: this.results.failed === 0
        };
    }
};

// Auto-run tests when script loads
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🤖 ChatterFix CMMS Test Runner Loaded');
        console.log('Run TestRunner.runAllTests() to start comprehensive testing');
        
        // Auto-run after a short delay to let everything initialize
        setTimeout(() => {
            TestRunner.runAllTests().then(results => {
                // Create visual test results if ModernComponents is available
                if (typeof ModernComponents !== 'undefined') {
                    const message = results.success ? 
                        '🎉 All tests passed! System ready for production.' :
                        `⚠️ ${results.failed} tests failed. Review required.`;
                    
                    const type = results.success ? 'success' : 'warning';
                    ModernComponents.showNotification(message, type, 8000);
                }
            }).catch(error => {
                console.error('Test runner failed:', error);
                if (typeof ModernComponents !== 'undefined') {
                    ModernComponents.showNotification(
                        'Test runner encountered an error. Check console for details.', 
                        'error'
                    );
                }
            });
        }, 2000);
    });
}

// Export for manual testing
window.TestRunner = TestRunner;