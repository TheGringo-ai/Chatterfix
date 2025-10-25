const { test } = require('@playwright/test');

test('capture current colors', async ({ page }) => {
  await page.goto('https://chatterfix.com/dashboard');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'current-colors.png', fullPage: true });
});