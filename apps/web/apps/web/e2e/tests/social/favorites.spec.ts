import { test, expect } from '../../fixtures/auth';

test.describe('Favorites', () => {
  async function goToSkillDetail(page: import('@playwright/test').Page) {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();
    await expect(page).toHaveURL(/\/skills\/.+/);
  }

  test('shows Save button on skill detail page', async ({ page }) => {
    await goToSkillDetail(page);
    await expect(page.getByRole('button', { name: /Save/ })).toBeVisible();
  });

  test('toggling favorite changes the button text', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await goToSkillDetail(page);

    const saveBtn = page.getByRole('button', { name: /Save/ });
    await expect(saveBtn).toBeVisible();

    // If it says "Save" (unfavorited), click to favorite
    const initialText = await saveBtn.textContent();
    await saveBtn.click();

    // Button text should change
    if (initialText?.includes('Saved')) {
      // Was favorited, now should show "Save"
      await expect(page.getByRole('button', { name: /^\u2606 Save$/ })).toBeVisible();
    } else {
      // Was not favorited, now should show "Saved"
      await expect(page.getByRole('button', { name: /Saved/ })).toBeVisible();
    }
  });

  test('favorite count is displayed in the stats bar', async ({ page }) => {
    await goToSkillDetail(page);
    await expect(page.getByText('Favorites')).toBeVisible();
  });
});
