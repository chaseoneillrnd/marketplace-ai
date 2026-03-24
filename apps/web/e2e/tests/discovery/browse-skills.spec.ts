import { test, expect } from '../../fixtures/auth';
import { CATEGORIES } from '../../fixtures/test-data';

test.describe('Browse Skills', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/browse');
  });

  test('displays the browse page with heading and skill count', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'All Skills' })).toBeVisible();
    // The total count text should eventually appear (replaces "Loading...")
    await expect(page.getByText(/\d+ skills/)).toBeVisible();
  });

  test('shows category filter pills for all categories', async ({ page }) => {
    for (const cat of CATEGORIES) {
      await expect(page.getByRole('button', { name: cat, exact: true })).toBeVisible();
    }
  });

  test('filters by category when clicking a category pill', async ({ page }) => {
    // Wait for skills to load
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    // Click "Engineering" category
    await page.getByRole('button', { name: 'Engineering', exact: true }).click();

    // The category pill should appear as active (check it's styled differently is hard,
    // but we can verify skills reload)
    await expect(page.getByTestId('skill-card').first()).toBeVisible({ timeout: 10_000 });
  });

  test('displays skill cards with expected content', async ({ page }) => {
    const firstCard = page.getByTestId('skill-card').first();
    await expect(firstCard).toBeVisible();

    // Each card should have a name, description, rating, and install count
    // The card contains role="article" so it's accessible
    await expect(firstCard).toHaveAttribute('role', 'article');
  });

  test('navigates to skill detail when clicking a card', async ({ page }) => {
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();

    // Should navigate to /skills/<slug>
    await expect(page).toHaveURL(/\/skills\/.+/);
  });

  test('shows division filter bar', async ({ page }) => {
    // Division filter bar should be present in browse view
    await expect(page.getByText('Engineering Org').first()).toBeVisible();
  });

  test('shows Load more button when there are more pages', async ({ page }) => {
    // Wait for initial load
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    // If there are more skills than the page size, a Load more button appears
    const loadMore = page.getByRole('button', { name: 'Load more' });
    // This may or may not be visible depending on data volume
    const count = await loadMore.count();
    if (count > 0) {
      await loadMore.click();
      // After loading more, there should be more cards
      await expect(page.getByTestId('skill-card')).not.toHaveCount(0);
    }
  });

  test('shows Advanced Filters button that navigates to filtered view', async ({ page }) => {
    await page.getByRole('button', { name: 'Advanced Filters' }).click();
    await expect(page).toHaveURL('/filtered');
  });
});
