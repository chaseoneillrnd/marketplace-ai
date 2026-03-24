import { test, expect } from '../../fixtures/auth';

test.describe('Protected Routes', () => {
  test('unauthenticated user is redirected from /admin to /', async ({ page }) => {
    await page.goto('/admin');
    // RequireAdmin redirects non-admin users to /
    await expect(page).toHaveURL('/');
  });

  test('unauthenticated user is redirected from /admin/queue', async ({ page }) => {
    await page.goto('/admin/queue');
    await expect(page).toHaveURL('/');
  });

  test('unauthenticated user is redirected from /admin/feedback', async ({ page }) => {
    await page.goto('/admin/feedback');
    await expect(page).toHaveURL('/');
  });

  test('unauthenticated user is redirected from /admin/export', async ({ page }) => {
    await page.goto('/admin/export');
    await expect(page).toHaveURL('/');
  });

  test('unauthenticated user is redirected from /admin/roadmap', async ({ page }) => {
    await page.goto('/admin/roadmap');
    await expect(page).toHaveURL('/');
  });

  test('unauthenticated user is redirected from /admin/skills', async ({ page }) => {
    await page.goto('/admin/skills');
    await expect(page).toHaveURL('/');
  });

  test('non-admin authenticated user is redirected from /admin', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob'); // bob is NOT platform_team

    await page.goto('/admin');
    // Should redirect back to home
    await expect(page).toHaveURL('/');
  });

  test('non-admin user is redirected from /admin/queue', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('dave'); // dave is regular user

    await page.goto('/admin/queue');
    await expect(page).toHaveURL('/');
  });

  test('admin user can access /admin', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice'); // alice IS platform_team

    await page.goto('/admin');
    await expect(page).toHaveURL('/admin');
    await expect(page.getByTestId('admin-sidebar')).toBeVisible();
  });

  test('admin user can access /admin/queue', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');

    await page.goto('/admin/queue');
    await expect(page).toHaveURL('/admin/queue');
    await expect(page.getByRole('heading', { name: 'Review Queue' })).toBeVisible();
  });

  test('public pages are accessible without auth', async ({ page }) => {
    // Home
    await page.goto('/');
    await expect(page.getByText('shared intelligence')).toBeVisible();

    // Browse
    await page.goto('/browse');
    await expect(page.getByRole('heading', { name: 'All Skills' })).toBeVisible();

    // Search
    await page.goto('/search?q=test');
    await expect(page.getByText(/Results for|All Skills/)).toBeVisible();

    // Filtered
    await page.goto('/filtered');
    await expect(page.getByText(/\d+ skills/)).toBeVisible({ timeout: 10_000 });
  });

  test('skill detail page is accessible without auth', async ({ page }) => {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();
    await expect(page).toHaveURL(/\/skills\/.+/);
    // Should load without errors
    await expect(page.locator('h1').first()).toBeVisible();
  });
});
