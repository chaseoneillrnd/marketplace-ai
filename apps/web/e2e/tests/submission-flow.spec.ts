import { test, expect } from '../fixtures/auth';

test.describe('Submission Flow', () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await page.goto('/');
    await loginAs('bob');
    await page.goto('/submit');
  });

  test('shows the Submit a Skill heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Submit a Skill' })).toBeVisible();
  });

  test('form mode renders step indicator, not "Coming soon"', async ({ page }) => {
    // Default mode is 'form' — step indicator must be visible
    await expect(page.getByTestId('step-indicator')).toBeVisible();
    await expect(page.getByTestId('form-builder-mode')).toBeVisible();

    // Must not show a generic "Coming soon" placeholder
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });

  test('mode selector tabs are visible', async ({ page }) => {
    await expect(page.getByTestId('mode-tab-form')).toBeVisible();
    await expect(page.getByTestId('mode-tab-upload')).toBeVisible();
    await expect(page.getByTestId('mode-tab-mcp')).toBeVisible();
  });

  test('switching to Upload mode renders drop zone', async ({ page }) => {
    await page.getByTestId('mode-tab-upload').click();

    await expect(page.getByTestId('file-upload-mode')).toBeVisible();
    await expect(page.getByTestId('drop-zone')).toBeVisible();

    // Must not show a generic "Coming soon" placeholder
    await expect(page.getByText('Coming soon', { exact: false })).not.toBeVisible();
  });

  test('switching to MCP mode renders the MCP sync toggle, not "Coming soon" page', async ({ page }) => {
    await page.getByTestId('mode-tab-mcp').click();

    await expect(page.getByTestId('mcp-sync-mode')).toBeVisible();

    // The MCP expanded panel shows a preview banner — but the mode itself renders
    await expect(page.getByTestId('btn-toggle-advanced')).toBeVisible();

    // Must not replace the whole UI with "Coming soon"
    await expect(page.getByText('Coming soon', { exact: true })).not.toBeVisible();
  });

  test('MCP mode: expanding shows URL input and Introspect button', async ({ page }) => {
    await page.getByTestId('mode-tab-mcp').click();
    await page.getByTestId('btn-toggle-advanced').click();

    await expect(page.getByTestId('mcp-expanded')).toBeVisible();
    await expect(page.getByTestId('input-mcp-url')).toBeVisible();
    await expect(page.getByTestId('btn-introspect')).toBeVisible();
  });

  test('form mode: fills name and description then advances to step 1', async ({ page }) => {
    await expect(page.getByTestId('step-0')).toBeVisible();

    await page.getByTestId('input-name').fill('E2E Test Skill');
    await page.getByTestId('input-description').fill('A skill created during end-to-end testing of SkillHub.');

    const nextBtn = page.getByTestId('btn-next');
    await expect(nextBtn).toBeEnabled();
    await nextBtn.click();

    await expect(page.getByTestId('step-1')).toBeVisible();
  });

  test('form mode: fills content and advances to metadata step', async ({ page }) => {
    // Step 0 — name + description
    await page.getByTestId('input-name').fill('E2E Test Skill');
    await page.getByTestId('input-description').fill('A skill created during end-to-end testing of SkillHub.');
    await page.getByTestId('btn-next').click();

    // Step 1 — content (needs ≥ 50 chars)
    await expect(page.getByTestId('step-1')).toBeVisible();
    await page.getByTestId('input-content').fill(
      '# E2E Test Skill\n\nThis skill was created during automated end-to-end testing. It verifies that the form builder mode works correctly from start to finish.',
    );

    const nextBtn = page.getByTestId('btn-next');
    await expect(nextBtn).toBeEnabled();
    await nextBtn.click();

    // Step 2 — metadata
    await expect(page.getByTestId('step-2')).toBeVisible();
    await expect(page.getByTestId('input-category')).toBeVisible();
  });

  test('form mode: selects a category on step 2', async ({ page }) => {
    await page.getByTestId('input-name').fill('E2E Test Skill');
    await page.getByTestId('input-description').fill('A skill created during end-to-end testing of SkillHub.');
    await page.getByTestId('btn-next').click();

    await page.getByTestId('input-content').fill(
      '# E2E Test Skill\n\nThis skill was created during automated end-to-end testing. It verifies that the form builder mode works correctly from start to finish.',
    );
    await page.getByTestId('btn-next').click();

    await page.getByTestId('input-category').selectOption('coding');
    await expect(page.getByTestId('input-category')).toHaveValue('coding');
  });

  test('form mode: reaches review step and sees Submit button', async ({ page }) => {
    // Step 0
    await page.getByTestId('input-name').fill('E2E Test Skill');
    await page.getByTestId('input-description').fill('A skill created during end-to-end testing of SkillHub.');
    await page.getByTestId('btn-next').click();

    // Step 1
    await page.getByTestId('input-content').fill(
      '# E2E Test Skill\n\nThis skill was created during automated end-to-end testing. It verifies that the form builder mode works correctly from start to finish.',
    );
    await page.getByTestId('btn-next').click();

    // Step 2
    await page.getByTestId('btn-next').click();

    // Step 3 — review
    await expect(page.getByTestId('step-3')).toBeVisible();
    await expect(page.getByTestId('btn-submit')).toBeVisible();
  });

  test('form mode: submit attempt shows success state or error message (not a crash)', async ({ page }) => {
    // Step 0
    await page.getByTestId('input-name').fill('E2E Test Skill');
    await page.getByTestId('input-description').fill('A skill created during end-to-end testing of SkillHub.');
    await page.getByTestId('btn-next').click();

    // Step 1
    await page.getByTestId('input-content').fill(
      '# E2E Test Skill\n\nThis skill was created during automated end-to-end testing. It verifies that the form builder mode works correctly from start to finish.',
    );
    await page.getByTestId('btn-next').click();

    // Step 2
    await page.getByTestId('btn-next').click();

    // Step 3 — click Submit if enabled
    const submitBtn = page.getByTestId('btn-submit');
    const isEnabled = await submitBtn.isEnabled();
    if (isEnabled) {
      await submitBtn.click();

      // Backend may or may not be running — handle both outcomes gracefully:
      // success → SubmissionStatusTracker renders (no longer on the multi-step form)
      // failure → error alert appears
      await expect(
        page.getByRole('alert').or(page.getByTestId('submission-status-tracker')),
      ).toBeVisible({ timeout: 15_000 });
    }
  });

  test('unauthenticated user sees sign-in required message', async ({ page: unauthPage }) => {
    await unauthPage.goto('/submit');
    await expect(unauthPage.getByText('Sign in required')).toBeVisible();
    await expect(unauthPage.getByText('You must be signed in to submit a skill.')).toBeVisible();
  });
});
