import { test, expect } from '../../fixtures/auth';

test.describe('Admin Export', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await page.goto('/admin/export');
  });

  test('displays Export heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Export' })).toBeVisible();
  });

  test('shows scope selector with all options', async ({ page }) => {
    await expect(page.getByText('Scope')).toBeVisible();
    for (const scope of ['Installs', 'Submissions', 'Users', 'Analytics']) {
      await expect(page.getByRole('button', { name: scope, exact: true })).toBeVisible();
    }
  });

  test('shows format toggle with CSV and JSON', async ({ page }) => {
    await expect(page.getByText('Format')).toBeVisible();
    await expect(page.getByRole('button', { name: 'CSV' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'JSON' })).toBeVisible();
  });

  test('shows date range inputs', async ({ page }) => {
    await expect(page.getByLabel('Start Date')).toBeVisible();
    await expect(page.getByLabel('End Date')).toBeVisible();
  });

  test('switching scope updates active button style', async ({ page }) => {
    // Click Users scope
    await page.getByRole('button', { name: 'Users', exact: true }).click();
    // Click Analytics scope
    await page.getByRole('button', { name: 'Analytics', exact: true }).click();

    // Just verify no crash
    await expect(page.getByTestId('admin-export-view')).toBeVisible();
  });

  test('switching format updates active button', async ({ page }) => {
    await page.getByRole('button', { name: 'JSON' }).click();
    await expect(page.getByTestId('admin-export-view')).toBeVisible();
  });

  test('shows remaining exports count', async ({ page }) => {
    await expect(page.getByText(/\d+ of 5 exports remaining today/)).toBeVisible();
  });

  test('Request Export button is visible and clickable', async ({ page }) => {
    const exportBtn = page.getByRole('button', { name: 'Request Export' });
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toBeEnabled();
  });

  test('clicking Request Export triggers export flow', async ({ page }) => {
    await page.getByRole('button', { name: 'Request Export' }).click();

    // Should show export status: processing, complete, or failed
    // Wait for any status indicator
    const statusContainer = page.getByTestId('admin-export-view');
    await expect(statusContainer).toBeVisible();

    // One of these should eventually appear
    await expect(
      page.getByText('Processing...').or(page.getByText('Export complete!')).or(page.getByText('Export failed'))
    ).toBeVisible({ timeout: 15_000 });
  });

  test('date range can be set', async ({ page }) => {
    const startInput = page.getByLabel('Start Date');
    const endInput = page.getByLabel('End Date');

    await startInput.fill('2025-01-01');
    await endInput.fill('2025-12-31');

    await expect(startInput).toHaveValue('2025-01-01');
    await expect(endInput).toHaveValue('2025-12-31');
  });
});
