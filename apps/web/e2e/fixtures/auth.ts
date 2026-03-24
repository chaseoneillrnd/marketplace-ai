/**
 * Authentication fixture for E2E tests.
 *
 * The app uses memory-only token storage (no localStorage/cookies).
 * Auth is performed via the UI: open auth modal, click dev user button.
 * For API-level auth, we call POST /auth/token directly.
 */
import { test as base, type Page } from '@playwright/test';
import { getAuthToken } from './api';
import { USERS, type StubUser } from './test-data';

/**
 * Extended test fixture that provides authenticated page contexts.
 */
export interface AuthFixtures {
  /** Login as a specific stub user via the UI auth modal */
  loginAs: (user: StubUser) => Promise<void>;
  /** Get API token for a stub user (for direct API calls in tests) */
  getToken: (user: StubUser) => Promise<string>;
}

/**
 * Perform UI login: click Sign In, then click the dev user button.
 * The app is in dev mode, so the auth modal shows stub user buttons.
 */
async function loginViaUI(page: Page, username: string): Promise<void> {
  // Click Sign In button in the nav
  await page.getByRole('button', { name: 'Sign In' }).click();

  // Wait for the auth modal
  await page.getByTestId('auth-modal').waitFor({ state: 'visible' });

  // Click the dev user button
  await page.getByTestId(`dev-user-${username}`).click();

  // Wait for the modal to close (login succeeded)
  await page.getByTestId('auth-modal').waitFor({ state: 'hidden', timeout: 10_000 });

  // Verify the user menu trigger is visible (proves we're logged in)
  await page.getByTestId('user-menu-trigger').waitFor({ state: 'visible' });
}

export const test = base.extend<AuthFixtures>({
  loginAs: async ({ page }, use) => {
    const fn = async (user: StubUser) => {
      await loginViaUI(page, USERS[user].username);
    };
    await use(fn);
  },

  getToken: async ({ request }, use) => {
    const tokenCache = new Map<string, string>();
    const fn = async (user: StubUser) => {
      const cached = tokenCache.get(user);
      if (cached) return cached;
      const token = await getAuthToken(request, USERS[user].username, USERS[user].password);
      tokenCache.set(user, token);
      return token;
    };
    await use(fn);
  },
});

export { expect } from '@playwright/test';
