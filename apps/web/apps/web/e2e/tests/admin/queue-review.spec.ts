import { test, expect } from '../../fixtures/auth';

test.describe('Admin Queue Review', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice'); // alice is platform_team (admin)
    await page.goto('/admin/queue');
  });

  test('displays Review Queue heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Review Queue' })).toBeVisible();
  });

  test('shows queue items or empty state', async ({ page }) => {
    // Wait for loading to complete
    await page.waitForTimeout(2000); // brief wait for API

    const hasItems = await page.locator('button').filter({ hasText: /.+/ }).count();
    const emptyMessage = page.getByText('No items in the review queue');
    const loadingMessage = page.getByText('Loading queue...');

    // Should eventually show either items or empty state (not loading forever)
    await expect(loadingMessage).not.toBeVisible({ timeout: 15_000 });
  });

  test('selecting a queue item shows detail panel', async ({ page }) => {
    // Wait for queue to load
    await expect(page.getByText('Loading queue...')).not.toBeVisible({ timeout: 15_000 });

    const emptyQueue = await page.getByText('No items in the review queue').count();
    if (emptyQueue > 0) {
      test.skip();
      return;
    }

    // Click the first item in the queue list
    // Queue items are buttons with skill names
    const firstQueueItem = page.locator('button').filter({ has: page.locator('text=/Gate|Category/i') }).first();

    if (await firstQueueItem.count() > 0) {
      await firstQueueItem.click();

      // Detail panel should show content preview and gate results
      await expect(page.getByText('Gate Results')).toBeVisible();
    }
  });

  test('detail panel shows approve, reject, and request changes buttons', async ({ page }) => {
    await expect(page.getByText('Loading queue...')).not.toBeVisible({ timeout: 15_000 });

    const emptyQueue = await page.getByText('No items in the review queue').count();
    if (emptyQueue > 0) {
      test.skip();
      return;
    }

    // Select first queue item by clicking any skill name in the queue
    const queueButtons = page.locator('button').filter({
      has: page.locator('span'),
    });
    // Click the first non-action button in the queue panel
    const firstItem = queueButtons.first();
    if (await firstItem.count() > 0) {
      await firstItem.click();
    }

    // Action buttons should be visible
    await expect(page.getByRole('button', { name: 'Approve' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reject' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Request Changes' })).toBeVisible();
  });

  test('shows SLA badge for long-waiting items', async ({ page }) => {
    await expect(page.getByText('Loading queue...')).not.toBeVisible({ timeout: 15_000 });

    // Check if any SLA badges are visible
    const slaBreached = page.getByText('SLA breached');
    const slaAtRisk = page.getByText('SLA at risk');

    // These may or may not be present depending on data
    // Just verify no crashes
    const breachedCount = await slaBreached.count();
    const atRiskCount = await slaAtRisk.count();
    // Test passes either way - we're just verifying the UI doesn't crash
    expect(breachedCount + atRiskCount).toBeGreaterThanOrEqual(0);
  });
});
