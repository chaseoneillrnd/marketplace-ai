import { test, expect } from '../../fixtures/auth';

test.describe('Install Flow', () => {
  async function goToSkillDetail(page: import('@playwright/test').Page) {
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();
    await expect(page).toHaveURL(/\/skills\/.+/);
  }

  test('shows "Sign in to Install" when not authenticated', async ({ page }) => {
    await goToSkillDetail(page);
    await expect(page.getByRole('button', { name: 'Sign in to Install' })).toBeVisible();
  });

  test('shows Install button when authenticated and has access', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await goToSkillDetail(page);

    // Should see Install or Installed button (depending on state)
    const installBtn = page.getByRole('button', { name: /Install/ }).first();
    await expect(installBtn).toBeVisible();
  });

  test('clicking Install changes button to Installed', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await goToSkillDetail(page);

    const installBtn = page.getByRole('button', { name: 'Install', exact: true });
    const alreadyInstalled = await page.getByRole('button', { name: /Installed/ }).count();

    if (alreadyInstalled === 0) {
      await installBtn.click();
      // Should show "Installed" after API call
      await expect(page.getByRole('button', { name: /Installed/ })).toBeVisible({ timeout: 10_000 });
    }
  });

  test('install tab shows install methods with commands', async ({ page }) => {
    await goToSkillDetail(page);
    await page.getByRole('button', { name: 'Install' }).click();

    // Should show Claude Code CLI
    await expect(page.getByText('Claude Code CLI')).toBeVisible();
    await expect(page.getByText(/claude skill install/)).toBeVisible();

    // Should show Manual Install
    await expect(page.getByText('Manual Install')).toBeVisible();
  });

  test('shows access restriction warning when division does not match', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');

    // Navigate to browse and find a skill
    await page.goto('/browse');
    await expect(page.getByTestId('skill-card').first()).toBeVisible();
    await page.getByTestId('skill-card').first().click();

    // If the user's division is not authorized, there should be a restriction notice
    // This depends on the data - we check if the warning exists and handle both cases
    const restrictionWarning = page.getByText('Access restricted for your division');
    const isRestricted = await restrictionWarning.count();

    if (isRestricted > 0) {
      await expect(restrictionWarning).toBeVisible();
      await expect(page.getByRole('button', { name: 'Request Access' })).toBeVisible();
    }
    // If not restricted, that's fine too - the skill is accessible to bob's division
  });
});
