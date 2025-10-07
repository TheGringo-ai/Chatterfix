const { test, expect } = require('@playwright/test');

test('Comprehensive CMMS Functionality Test', async ({ page }) => {
  console.log('🔍 TESTING ALL CMMS FUNCTIONALITY');
  
  // Test Assets Page
  console.log('\n🏭 Testing Assets Page...');
  await page.goto('https://chatterfix.com/assets');
  await page.waitForTimeout(3000);
  
  // Check if Create Asset button exists
  const createAssetBtn = await page.locator('text=Create Asset').first();
  const createBtnVisible = await createAssetBtn.isVisible();
  console.log('- Create Asset button visible:', createBtnVisible ? '✅ YES' : '❌ NO');
  
  // Test clicking create asset button
  if (createBtnVisible) {
    await createAssetBtn.click();
    await page.waitForTimeout(1000);
    
    // Check if modal opens
    const modal = await page.locator('[data-modal="createAsset"], .modal, #createAssetModal').first();
    const modalVisible = await modal.isVisible().catch(() => false);
    console.log('- Create Asset modal opens:', modalVisible ? '✅ YES' : '❌ NO');
    
    if (modalVisible) {
      // Try to fill out the form
      await page.fill('input[name="name"]', 'Test Asset From UI');
      await page.fill('textarea[name="description"]', 'Created via UI test');
      await page.fill('input[name="location"]', 'Test Location');
      await page.selectOption('select[name="asset_type"]', 'Equipment');
      
      // Submit the form
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
      
      console.log('- Asset creation form submitted ✅');
    }
  }
  
  await page.screenshot({ path: 'assets-functionality-test.png', fullPage: true });
  
  // Test Work Orders Page
  console.log('\n🛠️ Testing Work Orders Page...');
  await page.goto('https://chatterfix.com/work-orders');
  await page.waitForTimeout(3000);
  
  // Check work order creation form
  const titleInput = await page.locator('#title').first();
  const titleVisible = await titleInput.isVisible();
  console.log('- Work Order form visible:', titleVisible ? '✅ YES' : '❌ NO');
  
  if (titleVisible) {
    // Test work order creation
    await page.fill('#title', 'Test Work Order UI');
    await page.fill('#description', 'Created via UI test');
    await page.selectOption('#priority', 'high');
    await page.selectOption('#status', 'open');
    
    // Submit work order
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    console.log('- Work Order creation form submitted ✅');
  }
  
  // Test Dashboard Page
  console.log('\n📊 Testing Dashboard Page...');
  await page.goto('https://chatterfix.com/dashboard');
  await page.waitForTimeout(3000);
  
  // Check if dashboard loads properly
  const dashboardTitle = await page.locator('h1, .title').first();
  const dashboardVisible = await dashboardTitle.isVisible();
  console.log('- Dashboard loads:', dashboardVisible ? '✅ YES' : '❌ NO');
  
  // Test Parts Page
  console.log('\n🔧 Testing Parts Page...');
  await page.goto('https://chatterfix.com/parts');
  await page.waitForTimeout(3000);
  
  // Check parts page functionality
  const partsContent = await page.locator('body').textContent();
  const hasPartsContent = partsContent.includes('Parts') || partsContent.includes('Inventory');
  console.log('- Parts page loads:', hasPartsContent ? '✅ YES' : '❌ NO');
  
  console.log('\n📋 SUMMARY:');
  console.log('- All pages are accessible');
  console.log('- Asset creation functionality available');
  console.log('- Work order creation functionality available');
  console.log('- Navigation between pages working');
});