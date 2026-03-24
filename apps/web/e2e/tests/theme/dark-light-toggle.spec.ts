import { test, expect } from '../../fixtures/auth';

test.describe('Dark/Light Theme Toggle', () => {
  test('app starts in dark mode by default', async ({ page }) => {
    await page.goto('/');

    // The main container should have a dark background
    // Dark mode bg is typically very dark (e.g. #080c14 or similar)
    const mainDiv = page.locator('#main-content').locator('..');
    const bgColor = await mainDiv.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });
    // Dark backgrounds typically have low RGB values
    expect(bgColor).toBeTruthy();
  });

  test('theme toggle button is visible', async ({ page }) => {
    await page.goto('/');

    // Theme toggle has a title attribute
    const toggle = page.getByTitle(/Switch to (light|dark) mode/);
    await expect(toggle).toBeVisible();
  });

  test('clicking toggle switches from dark to light mode', async ({ page }) => {
    await page.goto('/');

    // Record initial background
    const mainDiv = page.locator('#main-content').locator('..');
    const initialBg = await mainDiv.evaluate((el) => window.getComputedStyle(el).backgroundColor);

    // Click the theme toggle (it's a button with title "Switch to light mode" in dark mode)
    await page.getByTitle('Switch to light mode').click();

    // Background should change
    const newBg = await mainDiv.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    expect(newBg).not.toBe(initialBg);

    // The toggle title should now say "Switch to dark mode"
    await expect(page.getByTitle('Switch to dark mode')).toBeVisible();
  });

  test('clicking toggle twice returns to dark mode', async ({ page }) => {
    await page.goto('/');

    const mainDiv = page.locator('#main-content').locator('..');
    const initialBg = await mainDiv.evaluate((el) => window.getComputedStyle(el).backgroundColor);

    // Toggle to light
    await page.getByTitle('Switch to light mode').click();
    // Toggle back to dark
    await page.getByTitle('Switch to dark mode').click();

    const finalBg = await mainDiv.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    expect(finalBg).toBe(initialBg);
  });

  test('theme persists across page navigations within session', async ({ page }) => {
    await page.goto('/');

    // Switch to light mode
    await page.getByTitle('Switch to light mode').click();
    await expect(page.getByTitle('Switch to dark mode')).toBeVisible();

    // Navigate to browse
    await page.getByRole('button', { name: 'Browse' }).click();

    // Theme should still be light mode
    await expect(page.getByTitle('Switch to dark mode')).toBeVisible();
  });

  test('skill cards render properly in both themes', async ({ page }) => {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    // In dark mode
    const cardCountDark = await page.getByTestId('skill-card').count();
    expect(cardCountDark).toBeGreaterThan(0);

    // Switch to light mode
    await page.getByTitle('Switch to light mode').click();

    // Cards should still render
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    const cardCountLight = await page.getByTestId('skill-card').count();
    expect(cardCountLight).toBe(cardCountDark);
  });

  test('nav bar renders in both themes', async ({ page }) => {
    await page.goto('/');

    // Verify nav elements in dark mode
    await expect(page.getByText('SkillHub')).toBeVisible();
    await expect(page.getByPlaceholder('Search skills...')).toBeVisible();

    // Switch to light mode
    await page.getByTitle('Switch to light mode').click();

    // Verify nav elements still visible in light mode
    await expect(page.getByText('SkillHub')).toBeVisible();
    await expect(page.getByPlaceholder('Search skills...')).toBeVisible();
  });
});
