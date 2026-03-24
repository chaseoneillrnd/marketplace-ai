import { test, expect } from '../../fixtures/auth';

test.describe('Skill Detail View', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to browse, wait for cards, click the first one
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();
    await expect(page).toHaveURL(/\/skills\/.+/);
  });

  test('displays skill name and metadata', async ({ page }) => {
    // The detail page has a heading with the skill name
    await expect(page.locator('h1').first()).toBeVisible();
    // Author info should be visible
    await expect(page.getByText(/^by /)).toBeVisible();
    // Version should be visible
    await expect(page.getByText(/^v\d/)).toBeVisible();
  });

  test('shows stats bar with installs, rating, forks, favorites', async ({ page }) => {
    await expect(page.getByText('Installs')).toBeVisible();
    await expect(page.getByText('Rating')).toBeVisible();
    await expect(page.getByText('Forks')).toBeVisible();
    await expect(page.getByText('Favorites')).toBeVisible();
  });

  test('shows tabs: Overview, How to Use, Install, Reviews', async ({ page }) => {
    for (const tabName of ['Overview', 'How to Use', 'Install', 'Reviews']) {
      await expect(page.getByRole('button', { name: tabName })).toBeVisible();
    }
  });

  test('displays overview tab with description and trigger phrases', async ({ page }) => {
    // Overview is the default tab
    // Description should be visible
    const overviewContent = page.locator('text=Authorized Divisions');
    await expect(overviewContent).toBeVisible();
  });

  test('switches to Install tab and shows install methods', async ({ page }) => {
    await page.getByRole('button', { name: 'Install' }).click();
    // Should see Claude Code CLI option
    await expect(page.getByText('Claude Code CLI')).toBeVisible();
    // Should see Manual Install option
    await expect(page.getByText('Manual Install')).toBeVisible();
  });

  test('switches to Reviews tab', async ({ page }) => {
    await page.getByRole('button', { name: 'Reviews' }).click();
    // Should see either reviews or "No reviews yet" message
    const hasReviews = await page.getByTestId('review-item').count();
    if (hasReviews > 0) {
      await expect(page.getByTestId('star-display').first()).toBeVisible();
    } else {
      await expect(page.getByText(/No reviews yet/)).toBeVisible();
    }
  });

  test('shows back button that navigates to previous page', async ({ page }) => {
    await page.getByText('\u2190 Back').click();
    // Should go back to browse
    await expect(page).toHaveURL('/browse');
  });

  test('shows division chips for authorized divisions', async ({ page }) => {
    // Divisions should be shown in the header and overview
    // At minimum we should see some division indicator
    await expect(page.getByText('Authorized Divisions')).toBeVisible();
  });

  test('shows Sign in to Install button when not authenticated', async ({ page }) => {
    // Since we did not log in, we should see a sign-in prompt
    await expect(page.getByRole('button', { name: 'Sign in to Install' })).toBeVisible();
  });
});
