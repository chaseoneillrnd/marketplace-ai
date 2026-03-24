import { test, expect } from '../../fixtures/auth';

test.describe('Admin User Management', () => {
  test('admin sidebar is visible after login', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin');

    await expect(page.getByTestId('admin-sidebar')).toBeVisible();
  });

  test('admin sidebar shows navigation links', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin');

    const sidebar = page.getByTestId('admin-sidebar');
    await expect(sidebar).toBeVisible();
  });

  test('admin dashboard shows stat cards', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin');

    // Dashboard should have the stat cards grid
    await expect(page.getByTestId('stat-cards-grid')).toBeVisible();

    // Verify key metrics are displayed
    await expect(page.getByText('Daily Active Users')).toBeVisible();
    await expect(page.getByText('New Installs (7d)')).toBeVisible();
    await expect(page.getByText('Published Skills')).toBeVisible();
    await expect(page.getByText('Pending Reviews')).toBeVisible();
    await expect(page.getByText('Pass Rate')).toBeVisible();
  });

  test('admin dashboard shows charts section', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin');

    await expect(page.getByText('Installs Over Time')).toBeVisible();
    await expect(page.getByText('By Division')).toBeVisible();
    await expect(page.getByText('Submission Funnel (30d)')).toBeVisible();
  });

  test('admin skills page shows coming soon', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin/skills');

    await expect(page.getByRole('heading', { name: 'Skills' })).toBeVisible();
    await expect(page.getByText('Coming soon')).toBeVisible();
  });

  test('admin nav shows Admin link for platform team users', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');

    // The nav should show an Admin link
    await expect(page.getByRole('link', { name: 'Admin' })).toBeVisible();
  });

  test('admin nav does NOT show Admin link for non-platform-team users', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');

    // Bob is not platform_team, so Admin link should not be visible
    await expect(page.getByRole('link', { name: 'Admin' })).not.toBeVisible();
  });
});
