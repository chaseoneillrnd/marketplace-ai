import { test, expect } from '../../fixtures/auth';

test.describe('Search Skills', () => {
  test('navigates to search results when searching from home page hero', async ({ page }) => {
    await page.goto('/');
    const searchInput = page.getByPlaceholder('What do you need help with today?');
    await searchInput.fill('code review');
    await searchInput.press('Enter');

    await expect(page).toHaveURL(/\/search\?q=code\+review/);
    await expect(page.getByText(/Results for/)).toBeVisible();
    await expect(page.getByText('"code review"')).toBeVisible();
  });

  test('navigates to search results when searching from nav bar', async ({ page }) => {
    await page.goto('/browse');
    const navSearch = page.getByPlaceholder('Search skills...');
    await navSearch.fill('security');
    await navSearch.press('Enter');

    await expect(page).toHaveURL(/\/search\?q=security/);
    await expect(page.getByText(/Results for/)).toBeVisible();
  });

  test('shows total result count on search page', async ({ page }) => {
    await page.goto('/search?q=test');
    await expect(page.getByText(/\d+ skills/)).toBeVisible();
  });

  test('shows sort dropdown with all sort options', async ({ page }) => {
    await page.goto('/search?q=test');
    const sortSelect = page.getByLabel('Sort by');
    await expect(sortSelect).toBeVisible();

    // Verify all sort options exist
    await expect(sortSelect.locator('option')).toHaveCount(5);
    for (const label of ['Trending', 'Most Installed', 'Highest Rated', 'Newest', 'Recently Updated']) {
      await expect(sortSelect.locator(`option:text("${label}")`)).toHaveCount(1);
    }
  });

  test('changes sort order when selecting a different sort option', async ({ page }) => {
    await page.goto('/search?q=test');
    await expect(page.getByTestId('skill-card').first()).toBeVisible({ timeout: 10_000 });

    const sortSelect = page.getByLabel('Sort by');
    await sortSelect.selectOption('rating');

    // Skills should reload (may take a moment)
    await expect(page.getByTestId('skill-card').first()).toBeVisible({ timeout: 10_000 });
  });

  test('shows division filter bar on search page', async ({ page }) => {
    await page.goto('/search?q=test');
    await expect(page.getByText('Engineering Org').first()).toBeVisible();
  });

  test('shows empty state when no results match', async ({ page }) => {
    await page.goto('/search?q=zzzznonexistentskillzzzzz');
    // Should show empty state message
    await expect(page.getByText(/No skills found/)).toBeVisible({ timeout: 10_000 });
  });

  test('shows back arrow button that navigates home', async ({ page }) => {
    await page.goto('/search?q=test');
    // The back arrow is a button with text content of a left arrow
    await page.locator('button').filter({ hasText: '\u2190' }).click();
    await expect(page).toHaveURL('/');
  });
});
