const { test, expect } = require('@playwright/test');

test('Check work-orders styling consistency', async ({ page }) => {
  console.log('🔍 Checking work-orders page styling...');
  
  await page.goto('https://chatterfix.com/work-orders');
  await page.waitForTimeout(3000);
  
  const workOrdersStyles = await page.evaluate(() => {
    return {
      bodyBg: window.getComputedStyle(document.body).backgroundColor,
      headerBg: document.querySelector('.header') ? window.getComputedStyle(document.querySelector('.header')).backgroundColor : 'not found',
      primaryBlue: getComputedStyle(document.documentElement).getPropertyValue('--primary-blue').trim(),
      bgSecondary: getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary').trim(),
      textPrimary: getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim()
    };
  });
  
  console.log('Work Orders Styles:');
  console.log('- Body BG:', workOrdersStyles.bodyBg);
  console.log('- Header BG:', workOrdersStyles.headerBg);
  console.log('- Primary Blue:', workOrdersStyles.primaryBlue);
  console.log('- BG Secondary:', workOrdersStyles.bgSecondary);
  console.log('- Text Primary:', workOrdersStyles.textPrimary);
  
  await page.screenshot({ path: 'work-orders-styling.png', fullPage: true });
  
  // Check if it matches our expected light theme
  const isConsistent = 
    workOrdersStyles.bodyBg === 'rgb(250, 251, 252)' &&
    workOrdersStyles.primaryBlue === '#006fee';
    
  console.log('Is styling consistent?', isConsistent ? '✅ YES' : '❌ NO');
});