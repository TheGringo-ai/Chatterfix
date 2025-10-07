const { test, expect } = require('@playwright/test');

test.describe('ChatterFix CMMS Platform Navigation', () => {
  
  test('should load main platform dashboard with module access', async ({ page }) => {
    await page.goto('/');
    
    // Check that the homepage loads
    await expect(page).toHaveTitle(/ChatterFix CMMS/);
    
    // Click Access Platform button
    await page.click('a:has-text("Access Platform")');
    
    // Should navigate to main platform dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('h1')).toContainText('Platform Module Access');
  });

  test('should display all 8 module cards', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check for all expected modules
    const expectedModules = [
      'Managers Dashboard',
      'Work Orders', 
      'Asset Management',
      'Parts Inventory',
      'AI Assistant',
      'Document Intelligence', 
      'Reports & Analytics',
      'System Settings'
    ];
    
    for (const module of expectedModules) {
      await expect(page.locator(`.module-card:has-text("${module}")`)).toBeVisible();
    }
  });

  test('should navigate to managers dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Click Managers Dashboard module
    await page.click('.module-card:has-text("Managers Dashboard")');
    
    // Should navigate to managers page with unified dashboard
    await expect(page).toHaveURL(/.*\/managers/);
    await expect(page.locator('.sidebar')).toBeVisible();
  });

  test('should show module status indicators', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Wait for status checks to complete
    await page.waitForTimeout(2000);
    
    // Check that module status indicators are present
    const statusIndicators = page.locator('.module-status');
    await expect(statusIndicators.first()).toBeVisible();
    
    // Most modules should show online status
    const onlineModules = page.locator('.status-online');
    expect(await onlineModules.count()).toBeGreaterThan(5);
  });

  test('should have functional quick actions', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check quick actions section
    await expect(page.locator('.quick-actions')).toBeVisible();
    await expect(page.locator('h3:has-text("Quick Actions")')).toBeVisible();
    
    // Verify quick action buttons
    const quickActions = [
      'Create Work Order',
      'Add Asset', 
      'Add Part',
      'Generate Report',
      'Ask AI Assistant',
      'Emergency Protocol'
    ];
    
    for (const action of quickActions) {
      await expect(page.locator(`.action-btn:has-text("${action}")`)).toBeVisible();
    }
  });

  test('should display platform statistics', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check statistics cards
    await expect(page.locator('.stat-card')).toHaveCount(4);
    
    // Verify stat labels
    await expect(page.locator('.stat-label:has-text("Active Modules")')).toBeVisible();
    await expect(page.locator('.stat-label:has-text("System Uptime")')).toBeVisible();
    await expect(page.locator('.stat-label:has-text("Active Users")')).toBeVisible();
    await expect(page.locator('.stat-label:has-text("Work Orders")')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    // Check that modules grid adapts to mobile
    await expect(page.locator('.modules-grid')).toBeVisible();
    await expect(page.locator('.module-card').first()).toBeVisible();
    
    // Check header on mobile
    await expect(page.locator('.header')).toBeVisible();
    await expect(page.locator('.logo')).toBeVisible();
  });

  test('should handle module click tracking', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Listen for console logs
    const logs = [];
    page.on('console', msg => logs.push(msg.text()));
    
    // Click a module card
    await page.click('.module-card:has-text("Work Orders")');
    
    // Should log the click
    await page.waitForTimeout(500);
    expect(logs.some(log => log.includes('Accessing module: Work Orders'))).toBeTruthy();
  });

  test('managers dashboard should have unified navigation', async ({ page }) => {
    await page.goto('/managers');
    
    // Check unified managers dashboard elements
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.main-content')).toBeVisible();
    
    // Check for service navigation in sidebar
    const services = [
      'Work Orders',
      'Assets', 
      'Parts',
      'AI Assistant',
      'Document Intelligence',
      'Reports',
      'Settings'
    ];
    
    for (const service of services) {
      await expect(page.locator(`.sidebar a:has-text("${service}")`)).toBeVisible();
    }
  });

});

test.describe('Navigation Flow Integration', () => {
  
  test('complete navigation flow from homepage to managers', async ({ page }) => {
    // Start from homepage
    await page.goto('/');
    await expect(page).toHaveTitle(/ChatterFix CMMS/);
    
    // Go to platform dashboard
    await page.click('a:has-text("Access Platform")');
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Access managers dashboard
    await page.click('.module-card:has-text("Managers Dashboard")');
    await expect(page).toHaveURL(/.*\/managers/);
    
    // Verify unified managers interface
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.main-content')).toBeVisible();
  });

});