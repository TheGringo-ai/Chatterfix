const { test, expect } = require('@playwright/test');

test('inspect chatterfix.com dashboard styling', async ({ page }) => {
  console.log('🔍 Navigating to chatterfix.com/dashboard...');
  await page.goto('https://chatterfix.com/dashboard');
  await page.waitForTimeout(5000);
  
  console.log('📸 Taking screenshot...');
  await page.screenshot({ path: 'live-dashboard-styling.png', fullPage: true });
  
  console.log('🎨 Checking computed styles...');
  const bodyBg = await page.evaluate(() => {
    return window.getComputedStyle(document.body).backgroundColor;
  });
  
  const headerBg = await page.evaluate(() => {
    const header = document.querySelector('.header');
    return header ? window.getComputedStyle(header).backgroundColor : 'not found';
  });
  
  const primaryColor = await page.evaluate(() => {
    const element = document.querySelector('.logo');
    return element ? window.getComputedStyle(element).color : 'not found';
  });
  
  console.log('Current styles:');
  console.log('- Body background:', bodyBg);
  console.log('- Header background:', headerBg);
  console.log('- Primary color:', primaryColor);
  
  // Check if CSS variables are loaded
  const cssVars = await page.evaluate(() => {
    const root = document.documentElement;
    const primaryBlue = getComputedStyle(root).getPropertyValue('--primary-blue');
    const bgSecondary = getComputedStyle(root).getPropertyValue('--bg-secondary');
    return { primaryBlue, bgSecondary };
  });
  
  console.log('CSS Variables:');
  console.log('- --primary-blue:', cssVars.primaryBlue);
  console.log('- --bg-secondary:', cssVars.bgSecondary);
});