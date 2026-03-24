import { test, expect } from '../../fixtures/auth';

test.describe('Login Flow', () => {
  test('shows Sign In button when not authenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
  });

  test('clicking Sign In opens the auth modal', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByTestId('auth-modal')).toBeVisible();
  });

  test('auth modal has proper dialog role and aria attributes', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).click();

    const modal = page.getByTestId('auth-modal');
    await expect(modal).toHaveAttribute('role', 'dialog');
    await expect(modal).toHaveAttribute('aria-modal', 'true');
  });

  test('auth modal shows dev user list with user buttons', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByTestId('auth-modal')).toBeVisible();
    await expect(page.getByText('Dev Sign In')).toBeVisible();
    await expect(page.getByText('Choose a test identity')).toBeVisible();

    // Should show stub user buttons (loaded from API)
    await expect(page.getByTestId('dev-user-alice')).toBeVisible({ timeout: 10_000 });
  });

  test('clicking a dev user logs in and closes the modal', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByTestId('dev-user-alice')).toBeVisible({ timeout: 10_000 });

    await page.getByTestId('dev-user-alice').click();

    // Modal should close
    await expect(page.getByTestId('auth-modal')).not.toBeVisible({ timeout: 10_000 });
    // User menu trigger should appear
    await expect(page.getByTestId('user-menu-trigger')).toBeVisible();
  });

  test('after login, user menu shows name and division', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');

    // Click user menu trigger to open dropdown
    await page.getByTestId('user-menu-trigger').click();

    // Should see user info in the dropdown
    await expect(page.getByText('Sign out')).toBeVisible();
  });

  test('after login, nav shows division info', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');

    // The nav division indicator should be visible
    await expect(page.getByTestId('nav-division')).toBeVisible();
  });

  test('logout removes user menu and shows Sign In button', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');

    // Open user menu and click Sign out
    await page.getByTestId('user-menu-trigger').click();
    await page.getByRole('button', { name: 'Sign out' }).click();

    // Should redirect to home and show Sign In
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
    await expect(page.getByTestId('user-menu-trigger')).not.toBeVisible();
  });

  test('logging in as different users shows correct division', async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('alice');
    await expect(page.getByTestId('nav-division')).toBeVisible();

    // Logout
    await page.getByTestId('user-menu-trigger').click();
    await page.getByRole('button', { name: 'Sign out' }).click();

    // Login as bob
    await loginAs('bob');
    await expect(page.getByTestId('nav-division')).toBeVisible();
  });

  test('auth modal shows password hint text', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByText(/password is "user" for all accounts/)).toBeVisible();
  });

  test('clicking overlay closes the auth modal', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByTestId('auth-modal')).toBeVisible();

    // Click the overlay (the auth-modal div itself, not its inner content)
    await page.getByTestId('auth-modal').click({ position: { x: 10, y: 10 } });

    await expect(page.getByTestId('auth-modal')).not.toBeVisible();
  });
});
