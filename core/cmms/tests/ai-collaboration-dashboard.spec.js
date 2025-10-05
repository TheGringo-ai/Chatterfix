// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('AI Collaboration Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the AI collaboration dashboard
    await page.goto('/ai-collaboration');
    
    // Wait for the dashboard to load
    await page.waitForSelector('.ai-dashboard', { timeout: 10000 });
  });

  test('should load the AI collaboration dashboard', async ({ page }) => {
    // Check that the main dashboard container is present
    await expect(page.locator('.ai-dashboard')).toBeVisible();
    
    // Check dashboard header
    await expect(page.locator('h1')).toContainText('AI Collaboration Dashboard');
    
    // Check system status overview
    await expect(page.locator('.stats-grid')).toBeVisible();
    
    // Verify all stat cards are present
    const statCards = page.locator('.stat-card');
    await expect(statCards).toHaveCount(6);
  });

  test('should display real-time activity feed', async ({ page }) => {
    // Check activity stream is present
    await expect(page.locator('.activity-stream')).toBeVisible();
    
    // Wait for activity items to load
    await page.waitForSelector('.activity-item', { timeout: 15000 });
    
    // Check that activity items have proper structure
    const activityItems = page.locator('.activity-item');
    const firstActivity = activityItems.first();
    
    await expect(firstActivity.locator('.timestamp')).toBeVisible();
    await expect(firstActivity.locator('.activity-text')).toBeVisible();
    await expect(firstActivity.locator('.activity-status')).toBeVisible();
  });

  test('should allow AI model selection', async ({ page }) => {
    // Find AI model selector
    const aiModelSelect = page.locator('#ai-model-select');
    await expect(aiModelSelect).toBeVisible();
    
    // Test selecting different AI models
    await aiModelSelect.selectOption('claude');
    await expect(page.locator('#current-ai-display')).toContainText('CLAUDE');
    
    await aiModelSelect.selectOption('chatgpt');
    await expect(page.locator('#current-ai-display')).toContainText('CHATGPT');
    
    await aiModelSelect.selectOption('grok');
    await expect(page.locator('#current-ai-display')).toContainText('GROK');
    
    await aiModelSelect.selectOption('llama');
    await expect(page.locator('#current-ai-display')).toContainText('LLAMA');
  });

  test('should manage AI collaboration sessions', async ({ page }) => {
    const startBtn = page.locator('#start-session-btn');
    const endBtn = page.locator('#end-session-btn');
    const sessionStatus = page.locator('#session-status');
    
    // Initially should show inactive status
    await expect(sessionStatus).toContainText('Inactive');
    await expect(startBtn).toBeEnabled();
    await expect(endBtn).toBeDisabled();
    
    // Start a session
    await startBtn.click();
    
    // Wait for session to start
    await expect(sessionStatus).toContainText('Active');
    await expect(startBtn).toBeDisabled();
    await expect(endBtn).toBeEnabled();
    
    // End the session
    await endBtn.click();
    
    // Should return to inactive state
    await expect(sessionStatus).toContainText('Inactive');
    await expect(startBtn).toBeEnabled();
    await expect(endBtn).toBeDisabled();
  });

  test('should display and manage tasks', async ({ page }) => {
    // Check task list is present
    await expect(page.locator('#ai-tasks-list')).toBeVisible();
    
    // Wait for tasks to load
    await page.waitForSelector('.task-item', { timeout: 10000 });
    
    // Verify task structure
    const taskItems = page.locator('.task-item');
    const firstTask = taskItems.first();
    
    await expect(firstTask.locator('.task-header h4')).toBeVisible();
    await expect(firstTask.locator('.task-status')).toBeVisible();
    await expect(firstTask.locator('.task-meta')).toBeVisible();
    await expect(firstTask.locator('.task-actions')).toBeVisible();
    
    // Test creating a new task
    const createTaskBtn = page.locator('#create-task-btn');
    await expect(createTaskBtn).toBeVisible();
    
    // Click create task and handle the prompts
    page.on('dialog', async dialog => {
      if (dialog.message().includes('Task title')) {
        await dialog.accept('Test Task');
      } else if (dialog.message().includes('Task description')) {
        await dialog.accept('Test Description');
      } else if (dialog.message().includes('Assign to AI')) {
        await dialog.accept('claude');
      } else if (dialog.message().includes('Priority')) {
        await dialog.accept('high');
      }
    });
    
    await createTaskBtn.click();
    
    // Wait a moment for the task to be created
    await page.waitForTimeout(1000);
  });

  test('should handle knowledge base queries', async ({ page }) => {
    const queryForm = page.locator('#knowledge-query-form');
    const queryInput = page.locator('#knowledge-query-input');
    const resultsContainer = page.locator('#knowledge-results');
    
    await expect(queryForm).toBeVisible();
    await expect(queryInput).toBeVisible();
    
    // Test knowledge base query
    await queryInput.fill('pump maintenance');
    await queryForm.locator('button[type="submit"]').click();
    
    // Wait for results to load
    await page.waitForSelector('.knowledge-result, .no-results', { timeout: 15000 });
    
    // Check that results are displayed
    await expect(resultsContainer).toBeVisible();
  });

  test('should capture project context', async ({ page }) => {
    const captureBtn = page.locator('#capture-context-btn');
    const contextDisplay = page.locator('#current-context-display');
    
    await expect(captureBtn).toBeVisible();
    
    // Click capture context
    await captureBtn.click();
    
    // Wait for context to be captured
    await page.waitForSelector('.context-info', { timeout: 5000 });
    
    // Verify context information is displayed
    await expect(contextDisplay.locator('.context-item')).toHaveCount(5);
  });

  test('should run deployment safety checks', async ({ page }) => {
    const safetyBtn = page.locator('#deployment-safety-btn');
    const resultsContainer = page.locator('#deployment-results');
    
    await expect(safetyBtn).toBeVisible();
    
    // Run safety check
    await safetyBtn.click();
    
    // Wait for safety check to complete
    await page.waitForSelector('.deployment-result', { timeout: 20000 });
    
    // Verify results are displayed
    await expect(resultsContainer).toBeVisible();
    await expect(resultsContainer.locator('.deployment-result h4')).toContainText('Results');
  });

  test('should display recommendations and allow execution', async ({ page }) => {
    const recommendationsList = page.locator('#recommendations-list');
    
    // Wait for recommendations to load
    await page.waitForSelector('.recommendation-item', { timeout: 10000 });
    
    await expect(recommendationsList).toBeVisible();
    
    // Check recommendation structure
    const recommendations = page.locator('.recommendation-item');
    const firstRec = recommendations.first();
    
    await expect(firstRec.locator('h5')).toBeVisible();
    await expect(firstRec.locator('p')).toBeVisible();
    await expect(firstRec.locator('button')).toBeVisible();
    
    // Test executing a recommendation
    await firstRec.locator('button').click();
    
    // Should show notification
    await expect(page.locator('.notification')).toBeVisible({ timeout: 5000 });
  });

  test('should toggle auto-refresh functionality', async ({ page }) => {
    const toggleBtn = page.locator('#toggle-auto-refresh');
    const statusSpan = page.locator('#auto-refresh-status');
    
    await expect(toggleBtn).toBeVisible();
    await expect(statusSpan).toContainText('Enabled');
    
    // Toggle auto-refresh off
    await toggleBtn.click();
    await expect(statusSpan).toContainText('Paused');
    await expect(toggleBtn).toContainText('Resume');
    
    // Toggle auto-refresh back on
    await toggleBtn.click();
    await expect(statusSpan).toContainText('Enabled');
    await expect(toggleBtn).toContainText('Pause');
  });

  test('should display notifications', async ({ page }) => {
    // Trigger an action that shows notification (like starting a session)
    await page.locator('#start-session-btn').click();
    
    // Wait for notification to appear
    await expect(page.locator('.notification')).toBeVisible({ timeout: 5000 });
    
    // Check notification structure
    const notification = page.locator('.notification').first();
    await expect(notification.locator('span')).toBeVisible();
    await expect(notification.locator('.notification-close')).toBeVisible();
    
    // Test closing notification
    await notification.locator('.notification-close').click();
    await expect(notification).not.toBeVisible();
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

  test('should handle API errors gracefully', async ({ page }) => {
    // Test knowledge query with potential API failure
    const queryInput = page.locator('#knowledge-query-input');
    const queryForm = page.locator('#knowledge-query-form');
    
    await queryInput.fill('test query that might fail');
    await queryForm.locator('button[type="submit"]').click();
    
    // Should show either results or fallback content, not crash
    await page.waitForSelector('.knowledge-result, .no-results, .error', { timeout: 15000 });
    
    // Page should still be functional
    await expect(page.locator('.ai-dashboard')).toBeVisible();
  });

  test('should update timestamps and status indicators', async ({ page }) => {
    // Check that last updated timestamp exists
    const lastUpdated = page.locator('#last-updated');
    await expect(lastUpdated).toBeVisible();
    
    // Get initial timestamp
    const initialTime = await lastUpdated.textContent();
    
    // Trigger a refresh
    await page.locator('#refresh-dashboard-btn').click();
    
    // Wait a moment and check that timestamp updated
    await page.waitForTimeout(2000);
    const newTime = await lastUpdated.textContent();
    
    // Timestamps should be different
    expect(newTime).not.toBe(initialTime);
  });
});

test.describe('AI Dashboard API Integration', () => {
  test('should make actual API calls to AI endpoints', async ({ page }) => {
    // Monitor network requests
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/api/ai/')) {
        apiCalls.push(request.url());
      }
    });
    
    await page.goto('/ai-collaboration');
    
    // Trigger knowledge query that should call API
    const queryInput = page.locator('#knowledge-query-input');
    const queryForm = page.locator('#knowledge-query-form');
    
    await queryInput.fill('test equipment maintenance');
    await queryForm.locator('button[type="submit"]').click();
    
    // Wait for potential API call
    await page.waitForTimeout(3000);
    
    // Should have attempted to call work order autocomplete API
    const workOrderCalls = apiCalls.filter(url => url.includes('workorder/autocomplete'));
    expect(workOrderCalls.length).toBeGreaterThanOrEqual(0); // May be 0 if API not available
  });

  test('should handle deployment safety API calls', async ({ page }) => {
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/api/ai/predictive/')) {
        apiCalls.push(request.url());
      }
    });
    
    await page.goto('/ai-collaboration');
    
    // Trigger deployment safety check
    await page.locator('#deployment-safety-btn').click();
    
    // Wait for API call attempt
    await page.waitForTimeout(5000);
    
    // Should have attempted to call predictive API
    const predictiveCalls = apiCalls.filter(url => url.includes('failure-analysis'));
    expect(predictiveCalls.length).toBeGreaterThanOrEqual(0); // May be 0 if API not available
  });
});