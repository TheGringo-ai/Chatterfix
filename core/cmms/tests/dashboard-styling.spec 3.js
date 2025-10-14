const { test, expect } = require('@playwright/test');

test('inspect live dashboard styling', async ({ page }) => {
  console.log('🔍 Navigating to https://chatterfix.com/dashboard');
  await page.goto('https://chatterfix.com/dashboard');
  await page.waitForTimeout(5000);
  
  console.log('📸 Taking full page screenshot');
  await page.screenshot({ path: 'live-dashboard.png', fullPage: true });
  
  // Check computed styles
  const styles = await page.evaluate(() => {
    const body = document.body;
    const header = document.querySelector('.header');
    const logo = document.querySelector('.logo');
    
    return {
      bodyBg: window.getComputedStyle(body).backgroundColor,
      headerBg: header ? window.getComputedStyle(header).backgroundColor : 'not found',
      logoColor: logo ? window.getComputedStyle(logo).color : 'not found',
      primaryBlue: getComputedStyle(document.documentElement).getPropertyValue('--primary-blue').trim(),
      bgSecondary: getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary').trim()
    };
  });
  
  console.log('🎨 Current Dashboard Styles:');
  console.log('- Body background:', styles.bodyBg);
  console.log('- Header background:', styles.headerBg);
  console.log('- Logo color:', styles.logoColor);
  console.log('- CSS --primary-blue:', styles.primaryBlue);
  console.log('- CSS --bg-secondary:', styles.bgSecondary);
  
  // This test always passes - we're just inspecting
  expect(true).toBe(true);
});