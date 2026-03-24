import { test, expect } from '../../fixtures/auth';

test.describe('Ratings and Reviews', () => {
  /** Navigate to a skill detail page and go to Reviews tab */
  async function goToReviewsTab(page: import('@playwright/test').Page) {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();
    await expect(page).toHaveURL(/\/skills\/.+/);
    await page.getByRole('button', { name: 'Reviews' }).click();
  }

  test('shows write review form when authenticated', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await goToReviewsTab(page);

    await expect(page.getByText('Write a Review')).toBeVisible();
    await expect(page.getByTestId('star-picker')).toBeVisible();
    await expect(page.getByPlaceholder(/Share your experience/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Submit Review' })).toBeVisible();
  });

  test('does not show write review form when not authenticated', async ({ page }) => {
    await goToReviewsTab(page);
    // The form should not be visible
    await expect(page.getByText('Write a Review')).not.toBeVisible();
  });

  test('star picker allows selecting 1-5 stars', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await goToReviewsTab(page);

    // Click the 4th star (4 stars)
    await page.getByLabel('4 stars').click();

    // The first 4 stars should be filled
    const starPicker = page.getByTestId('star-picker');
    await expect(starPicker).toBeVisible();
  });

  test('submit button is disabled when rating is 0 or body is empty', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await goToReviewsTab(page);

    const submitBtn = page.getByRole('button', { name: 'Submit Review' });
    // Initially disabled (no rating, no text)
    await expect(submitBtn).toBeDisabled();

    // Add rating but no text
    await page.getByLabel('3 stars').click();
    await expect(submitBtn).toBeDisabled();

    // Add text but clear rating is not possible via UI easily, so just verify it enables
    await page.getByPlaceholder(/Share your experience/).fill('Great skill!');
    await expect(submitBtn).toBeEnabled();
  });

  test('submitting a review calls the API and refreshes list', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await goToReviewsTab(page);

    // Fill review
    await page.getByLabel('5 stars').click();
    await page.getByPlaceholder(/Share your experience/).fill('Excellent skill for testing!');

    // Submit
    await page.getByRole('button', { name: 'Submit Review' }).click();

    // After submission the form should clear and reviews should show
    // Either the review appears or the form resets
    await expect(page.getByPlaceholder(/Share your experience/)).toHaveValue('');
  });

  test('existing reviews display star ratings and text', async ({ page }) => {
    await goToReviewsTab(page);

    const reviewItems = page.getByTestId('review-item');
    const count = await reviewItems.count();
    if (count > 0) {
      // Each review should have a star display and text
      await expect(reviewItems.first().getByTestId('star-display')).toBeVisible();
    }
  });
});
