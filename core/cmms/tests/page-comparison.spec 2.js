const { test, expect } = require('@playwright/test');

test('Compare Assets vs Dashboard Styling', async ({ page }) => {
  console.log('🔍 COMPARING STYLING DIFFERENCES');
  
  // Test Dashboard page
  console.log('\n📊 Testing /dashboard page...');
  await page.goto('https://chatterfix.com/dashboard');
  await page.waitForTimeout(3000);
  
  const dashboardStyles = await page.evaluate(() => {
    return {
      bodyBg: window.getComputedStyle(document.body).backgroundColor,
      headerBg: document.querySelector('.header') ? window.getComputedStyle(document.querySelector('.header')).backgroundColor : 'not found',
      primaryBlue: getComputedStyle(document.documentElement).getPropertyValue('--primary-blue').trim(),
      bgSecondary: getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary').trim(),
      textPrimary: getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim()
    };
  });
  
  console.log('Dashboard Styles:');
  console.log('- Body BG:', dashboardStyles.bodyBg);
  console.log('- Header BG:', dashboardStyles.headerBg);
  console.log('- Primary Blue:', dashboardStyles.primaryBlue);
  console.log('- BG Secondary:', dashboardStyles.bgSecondary);
  console.log('- Text Primary:', dashboardStyles.textPrimary);
  
  await page.screenshot({ path: 'dashboard-comparison.png', fullPage: true });
  
  // Test Assets page
  console.log('\n🏭 Testing /assets page...');
  await page.goto('https://chatterfix.com/assets');
  await page.waitForTimeout(3000);
  
  const assetsStyles = await page.evaluate(() => {
    return {
      bodyBg: window.getComputedStyle(document.body).backgroundColor,
      headerBg: document.querySelector('.header') ? window.getComputedStyle(document.querySelector('.header')).backgroundColor : 'not found',
      primaryBlue: getComputedStyle(document.documentElement).getPropertyValue('--primary-blue').trim(),
      bgSecondary: getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary').trim(),
      textPrimary: getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim()
    };
  });
  
  console.log('Assets Styles:');
  console.log('- Body BG:', assetsStyles.bodyBg);
  console.log('- Header BG:', assetsStyles.headerBg);
  console.log('- Primary Blue:', assetsStyles.primaryBlue);
  console.log('- BG Secondary:', assetsStyles.bgSecondary);
  console.log('- Text Primary:', assetsStyles.textPrimary);
  
  await page.screenshot({ path: 'assets-comparison.png', fullPage: true });
  
  // Compare and report differences
  console.log('\n⚖️ STYLE COMPARISON RESULTS:');
  
  if (dashboardStyles.bodyBg !== assetsStyles.bodyBg) {
    console.log('❌ BODY BACKGROUND DIFFERS:');
    console.log('  Dashboard:', dashboardStyles.bodyBg);
    console.log('  Assets:', assetsStyles.bodyBg);
  } else {
    console.log('✅ Body backgrounds match');
  }
  
  if (dashboardStyles.primaryBlue !== assetsStyles.primaryBlue) {
    console.log('❌ PRIMARY BLUE DIFFERS:');
    console.log('  Dashboard:', dashboardStyles.primaryBlue);
    console.log('  Assets:', assetsStyles.primaryBlue);
  } else {
    console.log('✅ Primary blue colors match');
  }
  
  if (dashboardStyles.headerBg !== assetsStyles.headerBg) {
    console.log('❌ HEADER BACKGROUND DIFFERS:');
    console.log('  Dashboard:', dashboardStyles.headerBg);
    console.log('  Assets:', assetsStyles.headerBg);
  } else {
    console.log('✅ Header backgrounds match');
  }
});