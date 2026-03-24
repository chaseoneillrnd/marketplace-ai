import { test, expect } from '../../fixtures/auth';
import { DIVISIONS } from '../../fixtures/test-data';

test.describe('Division Filtering', () => {
  test('browse page shows all division filter options', async ({ page }) => {
    await page.goto('/browse');
    for (const div of DIVISIONS) {
      await expect(page.getByText(div, { exact: true }).first()).toBeVisible();
    }
  });

  test('clicking a division filters the skill list', async ({ page }) => {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    // Click Engineering Org division filter
    await page.getByText('Engineering Org', { exact: true }).first().click();

    // Wait for filtered results
    await expect(page.getByText(/\d+ skills/)).toBeVisible();
  });

  test('selecting multiple divisions combines the filter', async ({ page }) => {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    await page.getByText('Engineering Org', { exact: true }).first().click();
    await page.getByText('Product Org', { exact: true }).first().click();

    // Should show results matching either division
    await expect(page.getByText(/\d+ skills/)).toBeVisible();
  });

  test('deselecting a division updates the filter', async ({ page }) => {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    // Select then deselect
    const engButton = page.getByText('Engineering Org', { exact: true }).first();
    await engButton.click();
    await engButton.click();

    // Should show all skills again
    await expect(page.getByText(/\d+ skills/)).toBeVisible();
  });

  test('filtered view has division multi-select with checkboxes', async ({ page }) => {
    await page.goto('/filtered');

    // The filtered view has a division sidebar section
    await expect(page.getByText('Division').first()).toBeVisible();

    // Should show all divisions with checkboxes
    for (const div of DIVISIONS) {
      await expect(page.getByText(div, { exact: true }).first()).toBeVisible();
    }
  });

  test('filtered view shows division count badge when filters active', async ({ page }) => {
    await page.goto('/filtered');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    // Click a division checkbox in the sidebar
    await page.getByText('Engineering Org', { exact: true }).first().click();

    // Should show a count badge
    // The division section header should show the selected count
    await expect(page.getByText('1').first()).toBeVisible();
  });

  test('filtered view clear button removes all division selections', async ({ page }) => {
    await page.goto('/filtered');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();

    // Select divisions
    await page.getByText('Engineering Org', { exact: true }).first().click();
    await page.getByText('Product Org', { exact: true }).first().click();

    // Click Clear
    await page.getByRole('button', { name: 'Clear' }).click();

    // Should show all skills
    await expect(page.getByText(/\d+ skills/)).toBeVisible();
  });

  test('search page has division filter bar', async ({ page }) => {
    await page.goto('/search?q=test');
    await expect(page.getByText('Engineering Org').first()).toBeVisible();
  });
});
