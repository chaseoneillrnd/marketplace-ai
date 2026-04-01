import { test, expect } from '../fixtures/auth';

/**
 * Admin panel E2E tests.
 * All tests run as alice (platform_team admin).
 */

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin');
  });

  test('renders Dashboard heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('shows stat cards grid after loading', async ({ page }) => {
    // Wait for the loading skeleton to resolve
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    await expect(page.getByTestId('stat-cards-grid')).toBeVisible();
  });

  test('stat cards display known labels', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    for (const label of ['Daily Active Users', 'New Installs (7d)', 'Active Installs']) {
      await expect(page.getByText(label)).toBeVisible();
    }
  });

  test('shows charts area (Installs Over Time)', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('charts-area')).toBeVisible();
  });

  test('shows "Live data" label — not static mock data text', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    await expect(page.getByText('Live data')).toBeVisible();

    // Must not contain a generic "Coming soon" placeholder
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });
});

test.describe('Admin Skills Table', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin/skills');
  });

  test('renders Skills heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Skills' })).toBeVisible();
  });

  test('renders the admin skills view container', async ({ page }) => {
    await expect(page.getByTestId('admin-skills-view')).toBeVisible();
  });

  test('shows a search input', async ({ page }) => {
    await expect(page.getByTestId('skills-search-input')).toBeVisible();
  });

  test('does not show "Coming soon" placeholder', async ({ page }) => {
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });

  test('shows skill table or empty state after loading', async ({ page }) => {
    // Wait for any loading state to clear
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    const table = page.locator('table');
    const emptyMsg = page.getByText('No skills found.');

    const hasTable = await table.count();
    const hasEmpty = await emptyMsg.count();

    // One of these must be present
    expect(hasTable + hasEmpty).toBeGreaterThan(0);
  });

  test('table has expected column headers when skills are present', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    const table = page.locator('table');
    if (await table.count() === 0) {
      test.skip();
      return;
    }

    for (const header of ['Name', 'Category', 'Version', 'Installs', 'Status']) {
      await expect(page.getByRole('columnheader', { name: header })).toBeVisible();
    }
  });
});

test.describe('Admin Feature Flags', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin/flags');
  });

  test('renders Feature Flags heading', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: /Feature Flags/i }),
    ).toBeVisible();
  });

  test('does not show "Coming soon" placeholder', async ({ page }) => {
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });

  test('shows loading state then resolves', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });
  });

  test('shows Create Flag button or flag list', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    // Either a "Create" / "New Flag" button, or flag rows, must be present
    const createBtn = page.getByRole('button', { name: /Create|New Flag/i });
    const flagItem = page.locator('[data-testid^="flag-row-"]');
    const count = (await createBtn.count()) + (await flagItem.count());
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Admin Export', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin/export');
  });

  test('renders Export heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Export' })).toBeVisible();
  });

  test('shows scope buttons including date presets', async ({ page }) => {
    // These are the main scope buttons
    for (const scope of ['Installs', 'Submissions', 'Users', 'Analytics']) {
      await expect(page.getByRole('button', { name: scope, exact: true })).toBeVisible();
    }
  });

  test('shows date range inputs', async ({ page }) => {
    await expect(page.getByLabel('Start Date')).toBeVisible();
    await expect(page.getByLabel('End Date')).toBeVisible();
  });

  test('shows format toggle with CSV and JSON', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'CSV' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'JSON' })).toBeVisible();
  });

  test('does not show "Coming soon" placeholder', async ({ page }) => {
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });

  test('shows remaining exports count indicator', async ({ page }) => {
    await expect(page.getByText(/exports remaining today/i)).toBeVisible();
  });

  test('Request Export button is present', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Request Export' })).toBeVisible();
  });
});

test.describe('Admin Feedback List', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin/feedback');
  });

  test('renders Feedback heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Feedback' })).toBeVisible();
  });

  test('renders the admin feedback view container', async ({ page }) => {
    await expect(page.getByTestId('admin-feedback-view')).toBeVisible();
  });

  test('shows category filter buttons', async ({ page }) => {
    for (const label of ['All', 'Feature Request', 'Bug Report', 'Praise', 'Complaint']) {
      await expect(page.getByRole('button', { name: label, exact: true })).toBeVisible();
    }
  });

  test('shows sentiment filter buttons', async ({ page }) => {
    for (const label of ['Positive', 'Neutral', 'Critical']) {
      await expect(page.getByRole('button', { name: label, exact: true })).toBeVisible();
    }
  });

  test('does not show "Coming soon" placeholder', async ({ page }) => {
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });

  test('resolves loading state', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });
  });
});

test.describe('Admin Roadmap (Kanban)', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin/roadmap');
  });

  test('renders Roadmap heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Roadmap' })).toBeVisible();
  });

  test('renders the admin roadmap view container', async ({ page }) => {
    await expect(page.getByTestId('admin-roadmap-view')).toBeVisible();
  });

  test('shows all four kanban column labels', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    for (const col of ['PLANNED', 'IN PROGRESS', 'SHIPPED', 'CANCELLED']) {
      await expect(page.getByText(col, { exact: true })).toBeVisible();
    }
  });

  test('each kanban column has an item count badge', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    await expect(page.getByTestId('column-count')).toHaveCount(4);
  });

  test('shows a New Item button in the Planned column', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole('button', { name: '+ New Item' })).toBeVisible();
  });

  test('does not show "Coming soon" placeholder', async ({ page }) => {
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });
});
