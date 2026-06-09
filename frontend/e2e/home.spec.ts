import { test, expect } from '@playwright/test';

test('has title and main heading', async ({ page }) => {
  await page.goto('/');

  await expect(page).toHaveTitle(/VyroPortify/);

  await expect(page.getByText('Powered by Claude AI')).toBeVisible();
});
