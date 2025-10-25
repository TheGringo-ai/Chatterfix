const { test, expect } = require('@playwright/test');

test('AI Team Cache Bypass Investigation', async ({ browser }) => {
  console.log('🤖 AI TEAM CACHE INVESTIGATION');
  
  // Test 1: Incognito mode (bypasses all cache)
  console.log('\n1️⃣ Testing in Incognito Mode...');
  const incognitoContext = await browser.newContext();
  const incognitoPage = await incognitoContext.newPage();
  
  await incognitoPage.goto('https://chatterfix.com/dashboard');
  await incognitoPage.waitForTimeout(3000);
  
  const incognitoStyles = await incognitoPage.evaluate(() => {
    return {
      bodyBg: window.getComputedStyle(document.body).backgroundColor,
      primaryBlue: getComputedStyle(document.documentElement).getPropertyValue('--primary-blue').trim()
    };
  });
  
  console.log('Incognito Mode Results:');
  console.log('- Body BG:', incognitoStyles.bodyBg);
  console.log('- Primary Blue:', incognitoStyles.primaryBlue);
  
  await incognitoPage.screenshot({ path: 'incognito-dashboard.png', fullPage: true });
  await incognitoContext.close();
  
  // Test 2: Hard refresh with cache disabled
  console.log('\n2️⃣ Testing with Cache Disabled...');
  const cacheContext = await browser.newContext();
  const cachePage = await cacheContext.newPage();
  
  // Disable cache
  await cachePage.route('**/*', route => {
    route.continue({
      headers: {
        ...route.request().headers(),
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    });
  });
  
  await cachePage.goto('https://chatterfix.com/dashboard?nocache=' + Date.now());
  await cachePage.waitForTimeout(3000);
  
  const cacheStyles = await cachePage.evaluate(() => {
    return {
      bodyBg: window.getComputedStyle(document.body).backgroundColor,
      primaryBlue: getComputedStyle(document.documentElement).getPropertyValue('--primary-blue').trim()
    };
  });
  
  console.log('Cache Disabled Results:');
  console.log('- Body BG:', cacheStyles.bodyBg);
  console.log('- Primary Blue:', cacheStyles.primaryBlue);
  
  await cachePage.screenshot({ path: 'cache-disabled-dashboard.png', fullPage: true });
  await cacheContext.close();
  
  // Test 3: Direct service URL (bypass load balancer)
  console.log('\n3️⃣ Testing Direct Service URL...');
  const directContext = await browser.newContext();
  const directPage = await directContext.newPage();
  
  await directPage.goto('https://chatterfix-cmms-650169261019.us-central1.run.app/dashboard');
  await directPage.waitForTimeout(3000);
  
  const directStyles = await directPage.evaluate(() => {
    return {
      bodyBg: window.getComputedStyle(document.body).backgroundColor,
      primaryBlue: getComputedStyle(document.documentElement).getPropertyValue('--primary-blue').trim()
    };
  });
  
  console.log('Direct Service Results:');
  console.log('- Body BG:', directStyles.bodyBg);
  console.log('- Primary Blue:', directStyles.primaryBlue);
  
  await directPage.screenshot({ path: 'direct-service-dashboard.png', fullPage: true });
  await directContext.close();
  
  console.log('\n🔍 AI TEAM ANALYSIS COMPLETE');
});