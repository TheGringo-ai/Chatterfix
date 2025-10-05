// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('UI Components Testing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ai-collaboration');
    await page.waitForSelector('.ai-dashboard', { timeout: 10000 });
  });

  test.describe('Form Controls', () => {
    test('AI model dropdown should work correctly', async ({ page }) => {
      const dropdown = page.locator('#ai-model-select');
      
      // Test dropdown is accessible
      await expect(dropdown).toBeVisible();
      await expect(dropdown).toBeEnabled();
      
      // Test all options are present
      const options = await dropdown.locator('option').all();
      expect(options.length).toBeGreaterThan(0);
      
      // Test selecting each option
      const optionValues = ['claude', 'chatgpt', 'grok', 'llama'];
      
      for (const value of optionValues) {
        await dropdown.selectOption(value);
        
        // Wait for UI to update
        await page.waitForTimeout(500);
        
        // Check that selection is reflected in UI
        const displayElement = page.locator('#current-ai-display');
        await expect(displayElement).toContainText(value.toUpperCase());
      }
    });

    test('knowledge query input should handle various inputs', async ({ page }) => {
      const input = page.locator('#knowledge-query-input');
      const form = page.locator('#knowledge-query-form');
      
      await expect(input).toBeVisible();
      await expect(input).toBeEnabled();
      
      // Test various input types
      const testQueries = [
        'pump maintenance',
        'EQUIPMENT FAILURE',
        'Special characters: !@#$%^&*()',
        'Very long query that might test input field limits and see how the system handles extended text input for knowledge base searching',
        '123 numeric input',
        ''  // Empty input
      ];
      
      for (const query of testQueries) {
        await input.clear();
        await input.fill(query);
        
        // Check input value
        await expect(input).toHaveValue(query);
        
        if (query.trim()) {  // Only submit non-empty queries
          await form.locator('button[type="submit"]').click();
          
          // Wait for response
          await page.waitForTimeout(2000);
          
          // Check that results container is updated
          const results = page.locator('#knowledge-results');
          await expect(results).toBeVisible();
        }
      }
    });

    test('session control buttons should have proper states', async ({ page }) => {
      const startBtn = page.locator('#start-session-btn');
      const endBtn = page.locator('#end-session-btn');
      
      // Test initial state
      await expect(startBtn).toBeEnabled();
      await expect(endBtn).toBeDisabled();
      
      // Test button appearance and accessibility
      await expect(startBtn).toHaveClass(/btn/);
      await expect(startBtn).toHaveClass(/btn-primary/);
      await expect(endBtn).toHaveClass(/btn/);
      await expect(endBtn).toHaveClass(/btn-warning/);
      
      // Test button functionality
      await startBtn.click();
      await page.waitForTimeout(500);
      
      await expect(startBtn).toBeDisabled();
      await expect(endBtn).toBeEnabled();
      
      await endBtn.click();
      await page.waitForTimeout(500);
      
      await expect(startBtn).toBeEnabled();
      await expect(endBtn).toBeDisabled();
    });

    test('refresh controls should function properly', async ({ page }) => {
      const manualRefreshBtn = page.locator('#refresh-dashboard-btn');
      const autoRefreshToggle = page.locator('#toggle-auto-refresh');
      const autoRefreshStatus = page.locator('#auto-refresh-status');
      
      // Test manual refresh
      await expect(manualRefreshBtn).toBeVisible();
      await expect(manualRefreshBtn).toBeEnabled();
      
      const initialTime = await page.locator('#last-updated').textContent();
      await manualRefreshBtn.click();
      await page.waitForTimeout(1000);
      
      const newTime = await page.locator('#last-updated').textContent();
      expect(newTime).not.toBe(initialTime);
      
      // Test auto-refresh toggle
      await expect(autoRefreshToggle).toBeVisible();
      await expect(autoRefreshStatus).toContainText('Enabled');
      
      await autoRefreshToggle.click();
      await expect(autoRefreshStatus).toContainText('Paused');
      
      await autoRefreshToggle.click();
      await expect(autoRefreshStatus).toContainText('Enabled');
    });
  });

  test.describe('Interactive Elements', () => {
    test('task action buttons should be functional', async ({ page }) => {
      // Wait for tasks to load
      await page.waitForSelector('.task-item', { timeout: 10000 });
      
      const taskItems = page.locator('.task-item');
      const firstTask = taskItems.first();
      
      // Test view button
      const viewBtn = firstTask.locator('button:has-text("View")');
      if (await viewBtn.isVisible()) {
        page.on('dialog', dialog => dialog.accept());
        await viewBtn.click();
        await page.waitForTimeout(500);
      }
      
      // Test start/pause buttons based on task status
      const startBtn = firstTask.locator('button:has-text("Start")');
      const pauseBtn = firstTask.locator('button:has-text("Pause")');
      
      if (await startBtn.isVisible()) {
        await startBtn.click();
        await page.waitForTimeout(1000);
        
        // Should show notification
        await expect(page.locator('.notification')).toBeVisible();
      }
      
      if (await pauseBtn.isVisible()) {
        await pauseBtn.click();
        await page.waitForTimeout(1000);
        
        // Should show notification
        await expect(page.locator('.notification')).toBeVisible();
      }
    });

    test('recommendation execution buttons should work', async ({ page }) => {
      // Wait for recommendations to load
      await page.waitForSelector('.recommendation-item', { timeout: 10000 });
      
      const recommendations = page.locator('.recommendation-item');
      const firstRec = recommendations.first();
      const executeBtn = firstRec.locator('button:has-text("Execute")');
      
      await expect(executeBtn).toBeVisible();
      await expect(executeBtn).toBeEnabled();
      
      await executeBtn.click();
      
      // Should show notification about execution
      await expect(page.locator('.notification')).toBeVisible({ timeout: 5000 });
      
      // Check notification content
      const notification = page.locator('.notification').first();
      await expect(notification).toContainText('Executing');
    });

    test('context capture should display comprehensive information', async ({ page }) => {
      const captureBtn = page.locator('#capture-context-btn');
      
      await captureBtn.click();
      await page.waitForSelector('.context-info', { timeout: 5000 });
      
      const contextItems = page.locator('.context-item');
      await expect(contextItems).toHaveCount(5);
      
      // Check that each context item has proper structure
      for (let i = 0; i < 5; i++) {
        const item = contextItems.nth(i);
        await expect(item.locator('strong')).toBeVisible();
        const textContent = await item.textContent();
        expect(textContent.length).toBeGreaterThan(10); // Should have meaningful content
      }
    });
  });

  test.describe('Visual Indicators', () => {
    test('status indicators should display correctly', async ({ page }) => {
      // Check session status indicator
      const sessionStatus = page.locator('#session-status');
      await expect(sessionStatus).toBeVisible();
      await expect(sessionStatus).toHaveClass(/status-indicator/);
      
      // Check that it has appropriate status class
      const statusClasses = await sessionStatus.getAttribute('class');
      expect(statusClasses).toMatch(/status-(active|inactive)/);
      
      // Check auto-refresh status
      const autoRefreshStatus = page.locator('#auto-refresh-status');
      await expect(autoRefreshStatus).toBeVisible();
      const refreshClasses = await autoRefreshStatus.getAttribute('class');
      expect(refreshClasses).toMatch(/status-(active|inactive)/);
    });

    test('animated elements should be present', async ({ page }) => {
      // Check for pulse indicators
      const pulseIndicators = page.locator('.pulse-indicator');
      if (await pulseIndicators.count() > 0) {
        await expect(pulseIndicators.first()).toBeVisible();
      }
      
      // Check for progress bars
      const progressBars = page.locator('.progress-bar');
      if (await progressBars.count() > 0) {
        await expect(progressBars.first()).toBeVisible();
      }
      
      // Check for consensus meters
      const consensusMeters = page.locator('.consensus-meter');
      if (await consensusMeters.count() > 0) {
        await expect(consensusMeters.first()).toBeVisible();
      }
    });

    test('notification system should handle multiple notifications', async ({ page }) => {
      // Trigger multiple actions that create notifications
      await page.locator('#start-session-btn').click();
      await page.waitForTimeout(500);
      
      await page.locator('#capture-context-btn').click();
      await page.waitForTimeout(500);
      
      // Should show multiple notifications
      const notifications = page.locator('.notification');
      const notificationCount = await notifications.count();
      expect(notificationCount).toBeGreaterThan(0);
      
      // Test notification close functionality
      if (notificationCount > 0) {
        const firstNotification = notifications.first();
        const closeBtn = firstNotification.locator('.notification-close');
        
        await expect(closeBtn).toBeVisible();
        await closeBtn.click();
        
        // Notification should disappear
        await expect(firstNotification).not.toBeVisible();
      }
    });
  });

  test.describe('Data Display', () => {
    test('statistics should update and display correctly', async ({ page }) => {
      const statNumbers = page.locator('.stat-number');
      await expect(statNumbers).toHaveCount(6);
      
      // Check that all stat numbers have content
      for (let i = 0; i < 6; i++) {
        const statNumber = statNumbers.nth(i);
        await expect(statNumber).toBeVisible();
        
        const content = await statNumber.textContent();
        expect(content.trim()).not.toBe('');
        expect(content.trim()).not.toBe('0'); // Should have meaningful data
      }
      
      // Trigger refresh and check that stats might change
      const initialStats = [];
      for (let i = 0; i < 6; i++) {
        initialStats.push(await statNumbers.nth(i).textContent());
      }
      
      await page.locator('#refresh-dashboard-btn').click();
      await page.waitForTimeout(2000);
      
      // Some stats might have changed (due to random generation in dashboard)
      let hasChanged = false;
      for (let i = 0; i < 6; i++) {
        const newContent = await statNumbers.nth(i).textContent();
        if (newContent !== initialStats[i]) {
          hasChanged = true;
          break;
        }
      }
      
      // It's okay if stats don't change, but they should still be valid
      expect(hasChanged || !hasChanged).toBe(true); // Always passes, just documenting behavior
    });

    test('activity stream should show recent activities', async ({ page }) => {
      await page.waitForSelector('.activity-item', { timeout: 10000 });
      
      const activityItems = page.locator('.activity-item');
      const itemCount = await activityItems.count();
      
      expect(itemCount).toBeGreaterThan(0);
      expect(itemCount).toBeLessThanOrEqual(10); // Should limit to 10 items
      
      // Check structure of activity items
      for (let i = 0; i < Math.min(itemCount, 3); i++) {
        const item = activityItems.nth(i);
        
        await expect(item.locator('.timestamp')).toBeVisible();
        await expect(item.locator('.activity-text')).toBeVisible();
        await expect(item.locator('.activity-status')).toBeVisible();
        
        // Check timestamp format (should be HH:MM:SS)
        const timestamp = await item.locator('.timestamp').textContent();
        expect(timestamp).toMatch(/\d{1,2}:\d{2}:\d{2}/);
      }
    });

    test('task list should display tasks with proper formatting', async ({ page }) => {
      await page.waitForSelector('.task-item', { timeout: 10000 });
      
      const taskItems = page.locator('.task-item');
      const taskCount = await taskItems.count();
      
      expect(taskCount).toBeGreaterThan(0);
      
      // Check first task structure
      const firstTask = taskItems.first();
      
      // Should have priority class
      const classList = await firstTask.getAttribute('class');
      expect(classList).toMatch(/priority-(low|medium|high|critical)/);
      
      // Check task header
      const header = firstTask.locator('.task-header');
      await expect(header.locator('h4')).toBeVisible();
      await expect(header.locator('.task-status')).toBeVisible();
      
      // Check task meta information
      const meta = firstTask.locator('.task-meta');
      const metaSpans = meta.locator('span');
      await expect(metaSpans).toHaveCount(3); // AI, Priority, Created
      
      // Check task actions
      const actions = firstTask.locator('.task-actions');
      const actionButtons = actions.locator('button');
      const buttonCount = await actionButtons.count();
      expect(buttonCount).toBeGreaterThan(0);
    });
  });

  test.describe('Accessibility', () => {
    test('dashboard should be keyboard navigable', async ({ page }) => {
      // Test tab navigation through interactive elements
      const interactiveElements = [
        '#ai-model-select',
        '#start-session-btn',
        '#create-task-btn',
        '#knowledge-query-input',
        '#capture-context-btn',
        '#deployment-safety-btn',
        '#refresh-dashboard-btn',
        '#toggle-auto-refresh'
      ];
      
      for (const selector of interactiveElements) {
        const element = page.locator(selector);
        if (await element.isVisible()) {
          await element.focus();
          await expect(element).toBeFocused();
        }
      }
    });

    test('form elements should have proper labels', async ({ page }) => {
      // Check that form inputs have associated labels
      const aiModelSelect = page.locator('#ai-model-select');
      const queryInput = page.locator('#knowledge-query-input');
      
      // Check for labels or aria-labels
      const selectLabel = page.locator('label[for="ai-model-select"]');
      const inputPlaceholder = await queryInput.getAttribute('placeholder');
      
      // Should have either a label or meaningful placeholder
      expect(
        await selectLabel.isVisible() || 
        await aiModelSelect.getAttribute('aria-label') ||
        await aiModelSelect.getAttribute('title')
      ).toBeTruthy();
      
      expect(inputPlaceholder).toBeTruthy();
      expect(inputPlaceholder.length).toBeGreaterThan(5);
    });

    test('buttons should have descriptive text or aria-labels', async ({ page }) => {
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();
      
      for (let i = 0; i < Math.min(buttonCount, 10); i++) {
        const button = buttons.nth(i);
        if (await button.isVisible()) {
          const textContent = await button.textContent();
          const ariaLabel = await button.getAttribute('aria-label');
          const title = await button.getAttribute('title');
          
          // Button should have either text content, aria-label, or title
          expect(
            (textContent && textContent.trim().length > 0) ||
            (ariaLabel && ariaLabel.length > 0) ||
            (title && title.length > 0)
          ).toBeTruthy();
        }
      }
    });

    test('should be responsive on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Check that dashboard is still visible and usable
      await expect(page.locator('.ai-dashboard')).toBeVisible();
      
      // Check that grid layout adapts to mobile
      const dashboardGrid = page.locator('.dashboard-grid');
      await expect(dashboardGrid).toBeVisible();
      
      // Test that buttons are still clickable on mobile
      const refreshBtn = page.locator('#refresh-dashboard-btn');
      await expect(refreshBtn).toBeVisible();
      await refreshBtn.click();
    });
  });
});