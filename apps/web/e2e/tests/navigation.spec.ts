import { test, expect } from '../fixtures/auth';

test.describe('Navigation Links', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Docs link is visible in the nav', async ({ page }) => {
    // The Docs link is an <a> element pointing to /docs/
    const docsLink = page.getByRole('link', { name: 'Docs' });
    await expect(docsLink).toBeVisible();
  });

  test('Docs link points to /docs/', async ({ page }) => {
    const docsLink = page.getByRole('link', { name: 'Docs' });
    await expect(docsLink).toHaveAttribute('href', '/docs/');
  });

  test('Feedback nav button is visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Feedback', exact: true })).toBeVisible();
  });

  test('clicking Feedback navigates to /feedback', async ({ page }) => {
    await page.getByRole('button', { name: 'Feedback', exact: true }).click();
    await expect(page).toHaveURL('/feedback');
  });

  test('Admin link is NOT visible for unauthenticated users', async ({ page }) => {
    // Not logged in — Admin link must be absent
    await expect(page.getByRole('link', { name: 'Admin' })).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Admin', exact: true })).not.toBeVisible();
  });

  test('Admin link is NOT visible for non-platform-team users', async ({ page, loginAs }) => {
    await loginAs('bob'); // bob is data_science, not platform_team

    // Admin link must not be shown
    await expect(page.getByRole('link', { name: 'Admin' })).not.toBeVisible();
  });

  test('Admin link IS visible for platform team users (alice)', async ({ page, loginAs }) => {
    await loginAs('alice'); // alice is platform_team (isAdmin: true)

    // NavLink with "Admin" text should now appear
    await expect(page.getByRole('link', { name: 'Admin' })).toBeVisible();
  });

  test('clicking Admin link navigates to /admin', async ({ page, loginAs }) => {
    await loginAs('alice');
    await page.getByRole('link', { name: 'Admin' }).click();
    await expect(page).toHaveURL(/\/admin/);
  });

  test('Discover nav button is visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Discover', exact: true })).toBeVisible();
  });

  test('Browse nav button is visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Browse', exact: true })).toBeVisible();
  });

  test('clicking Browse navigates to /browse', async ({ page }) => {
    await page.getByRole('button', { name: 'Browse', exact: true }).click();
    await expect(page).toHaveURL('/browse');
  });
});

test.describe('Skill Detail — "Add to My Claude" button', () => {
  async function navigateToFirstSkill(page: import('@playwright/test').Page) {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();
    await expect(page).toHaveURL(/\/skills\/.+/);
  }

  test('skill detail page does not show "Install" as the primary CTA label when unauthenticated', async ({ page }) => {
    await navigateToFirstSkill(page);

    // Unauthenticated users see "Sign in to Install"
    await expect(page.getByRole('button', { name: 'Sign in to Install' })).toBeVisible();

    // The primary CTA must NOT be a bare "Install" button
    await expect(page.getByRole('button', { name: 'Install', exact: true })).not.toBeVisible();
  });

  test('authenticated user with access sees "Add to My Claude" CTA, not "Install"', async ({
    page,
    loginAs,
  }) => {
    await page.goto('/');
    await loginAs('alice');
    await navigateToFirstSkill(page);

    // The primary install action button should say "Add to My Claude" (or "Added" if already installed)
    const addBtn = page.getByRole('button', { name: /Add to My Claude|Added/i }).first();
    const restricted = page.getByRole('button', { name: 'Restricted', exact: true });

    const addCount = await addBtn.count();
    const restrictedCount = await restricted.count();

    // Either "Add to My Claude"/"Added" or "Restricted" must be present — no bare "Install"
    expect(addCount + restrictedCount).toBeGreaterThan(0);

    // Bare "Install" must not appear as the primary heading CTA
    await expect(page.getByRole('button', { name: 'Install', exact: true })).not.toBeVisible();
  });

  test('skill detail Install tab still exists and can be clicked', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await navigateToFirstSkill(page);

    // The "Install" tab (for showing code snippets) should still be present
    await page.getByRole('button', { name: 'Install' }).click();

    // Install methods should appear in the tab panel
    await expect(page.getByText('Claude Code CLI')).toBeVisible();
    await expect(page.getByText('Manual Install')).toBeVisible();
  });

  test('Sign In button is visible in nav when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
  });

  test('user menu trigger is visible after login', async ({ page, loginAs }) => {
    await loginAs('bob');
    await expect(page.getByTestId('user-menu-trigger')).toBeVisible();
  });
});
