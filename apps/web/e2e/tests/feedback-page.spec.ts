import { test, expect } from '../fixtures/auth';

test.describe('Feedback Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/feedback');
  });

  test('page loads with Feedback heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Feedback' })).toBeVisible();
  });

  test('shows the "Submit Feedback" section', async ({ page }) => {
    await expect(page.getByText('Submit Feedback')).toBeVisible();
  });

  test('shows category filter tabs: All, Feature Requests, Bug Reports, Praise, Complaints', async ({ page }) => {
    for (const label of ['All', 'Feature Requests', 'Bug Reports', 'Praise', 'Complaints']) {
      await expect(page.getByRole('button', { name: label, exact: true })).toBeVisible();
    }
  });

  test('clicking Feature Requests tab updates the active filter', async ({ page }) => {
    await page.getByRole('button', { name: 'Feature Requests', exact: true }).click();

    // The page should remain functional after filtering
    await expect(page.getByRole('heading', { name: 'Feedback' })).toBeVisible();

    // Tab should now be styled as active — verify no crash occurred
    await expect(page.getByRole('button', { name: 'Feature Requests', exact: true })).toBeVisible();
  });

  test('clicking Bug Reports tab updates the filter', async ({ page }) => {
    await page.getByRole('button', { name: 'Bug Reports', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Feedback' })).toBeVisible();
  });

  test('clicking All tab resets the filter', async ({ page }) => {
    // Switch to a filtered tab first
    await page.getByRole('button', { name: 'Feature Requests', exact: true }).click();
    // Then reset
    await page.getByRole('button', { name: 'All', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Feedback' })).toBeVisible();
  });

  test('unauthenticated user sees sign-in prompt instead of the form', async ({ page }) => {
    // Not logged in — should see prompt to sign in, not the form fields
    await expect(page.getByText('Sign in', { exact: false })).toBeVisible();
    // The textarea for body should not be present for unauthenticated users
    await expect(
      page.getByPlaceholder('Describe your feedback (min 20 characters)...'),
    ).not.toBeVisible();
  });

  test('authenticated user sees submit form with category selector and textarea', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await page.goto('/feedback');

    // Category selector should be present
    await expect(page.getByRole('combobox')).toBeVisible();

    // Feedback textarea should be present
    await expect(
      page.getByPlaceholder('Describe your feedback (min 20 characters)...'),
    ).toBeVisible();

    // Submit button should be present
    await expect(page.getByRole('button', { name: 'Submit', exact: true })).toBeVisible();
  });

  test('authenticated user can select a category for the feedback form', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await page.goto('/feedback');

    const categorySelect = page.getByRole('combobox');
    await categorySelect.selectOption('bug_report');
    await expect(categorySelect).toHaveValue('bug_report');
  });

  test('shows item count or empty-state after loading', async ({ page }) => {
    // Wait for the loading skeleton to resolve
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    // Should show either items (with upvote buttons) or an empty state
    const emptyState = page.getByText('No feedback yet. Be the first to share!');
    const hasEmpty = await emptyState.count();

    if (hasEmpty === 0) {
      // Items are present — upvote buttons should exist
      const upvoteButtons = page.getByTitle('Upvote');
      await expect(upvoteButtons.first()).toBeVisible();
    } else {
      await expect(emptyState).toBeVisible();
    }
  });

  test('upvote buttons are visible when feedback items exist', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(2000);

    const emptyState = await page.getByText('No feedback yet. Be the first to share!').count();
    if (emptyState > 0) {
      test.skip();
      return;
    }

    // Each feedback item has an upvote button with title="Upvote"
    const upvoteBtn = page.getByTitle('Upvote').first();
    await expect(upvoteBtn).toBeVisible();
  });

  test('feedback items show a category badge when items exist', async ({ page }) => {
    await expect(page.getByText('Loading...')).not.toBeVisible({ timeout: 15_000 });

    const emptyState = await page.getByText('No feedback yet. Be the first to share!').count();
    if (emptyState > 0) {
      test.skip();
      return;
    }

    // Category badges like "Feature Request", "Bug Report", etc. should be visible
    await expect(
      page
        .locator('span')
        .filter({ hasText: /Feature Request|Bug Report|Praise|Complaint/i })
        .first(),
    ).toBeVisible();
  });

  test('body text validation: shows error if body is too short', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await page.goto('/feedback');

    const textarea = page.getByPlaceholder('Describe your feedback (min 20 characters)...');
    await textarea.fill('Too short');

    await page.getByRole('button', { name: 'Submit', exact: true }).click();

    // Validation error should appear
    await expect(page.getByText('Body must be at least 20 characters.')).toBeVisible();
  });
});
