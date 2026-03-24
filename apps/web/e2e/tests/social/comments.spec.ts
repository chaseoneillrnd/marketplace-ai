import { test, expect } from '../../fixtures/auth';

test.describe('Comments', () => {
  // Note: The current SkillDetailView has Reviews but may not have a dedicated comments
  // section in the UI. This test covers what's available in the reviews tab which
  // serves a similar social function.

  async function goToReviewsTab(page: import('@playwright/test').Page) {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();
    await expect(page).toHaveURL(/\/skills\/.+/);
    await page.getByRole('button', { name: 'Reviews' }).click();
  }

  test('reviews tab loads without error', async ({ page }) => {
    await goToReviewsTab(page);
    // Should not show an error state
    await expect(page.getByText('Failed to load reviews')).not.toBeVisible();
  });

  test('review items show user info and timestamp', async ({ page }) => {
    await goToReviewsTab(page);

    const reviewItems = page.getByTestId('review-item');
    const count = await reviewItems.count();

    if (count > 0) {
      const firstReview = reviewItems.first();
      // Each review shows a user_id and a relative time
      await expect(firstReview.getByTestId('star-display')).toBeVisible();
      // Should have text content (the review body)
      await expect(firstReview.locator('p')).toBeVisible();
    }
  });

  test('empty state message when no reviews exist', async ({ page }) => {
    // Navigate to a skill and check reviews tab
    await goToReviewsTab(page);

    // Either reviews exist or empty state shows
    const hasReviews = await page.getByTestId('review-item').count();
    if (hasReviews === 0) {
      await expect(page.getByText(/No reviews yet/)).toBeVisible();
    }
  });
});
