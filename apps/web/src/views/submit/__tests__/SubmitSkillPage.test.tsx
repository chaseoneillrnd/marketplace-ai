import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AuthProvider } from '../../../context/AuthContext';
import { SubmitSkillPage } from '../SubmitSkillPage';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

function fakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.fakesig`;
}

const STUB_CLAIMS = {
  user_id: '00000000-0000-0000-0000-000000000001',
  email: 'test@skillhub.dev',
  name: 'Test User',
  username: 'test',
  division: 'Engineering Org',
  role: 'Senior Engineer',
  is_platform_team: false,
  exp: Math.floor(Date.now() / 1000) + 3600,
};

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter initialEntries={['/submit']}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('SubmitSkillPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('shows sign-in required when not authenticated', () => {
    render(<SubmitSkillPage />, { wrapper });
    expect(screen.getByText('Sign in required')).toBeDefined();
  });

  it('renders ModeSelector tabs when authenticated', () => {
    const token = fakeJwt(STUB_CLAIMS);
    localStorage.setItem('skillhub_token', token);

    render(<SubmitSkillPage />, { wrapper });

    expect(screen.getByTestId('mode-tab-form')).toBeDefined();
    expect(screen.getByTestId('mode-tab-upload')).toBeDefined();
    expect(screen.getByTestId('mode-tab-mcp')).toBeDefined();
  });

  it('shows form builder by default', () => {
    const token = fakeJwt(STUB_CLAIMS);
    localStorage.setItem('skillhub_token', token);

    render(<SubmitSkillPage />, { wrapper });

    expect(screen.getByTestId('skill-name-input')).toBeDefined();
    expect(screen.getByTestId('submit-skill-button')).toBeDefined();
  });

  it('switches to upload mode on tab click', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    localStorage.setItem('skillhub_token', token);
    const user = userEvent.setup();

    render(<SubmitSkillPage />, { wrapper });
    await user.click(screen.getByTestId('mode-tab-upload'));

    expect(screen.getByTestId('upload-mode')).toBeDefined();
  });

  it('switches to MCP mode on tab click', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    localStorage.setItem('skillhub_token', token);
    const user = userEvent.setup();

    render(<SubmitSkillPage />, { wrapper });
    await user.click(screen.getByTestId('mode-tab-mcp'));

    expect(screen.getByTestId('mcp-mode')).toBeDefined();
  });

  it('submits and shows status tracker on success', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    localStorage.setItem('skillhub_token', token);

    // POST /api/v1/submissions succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ display_id: 'SUB-0042' }),
    });

    // GET /api/v1/submissions/SUB-0042 for status polling
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ display_id: 'SUB-0042', status: 'gate1_passed', name: 'My Skill' }),
    });

    const user = userEvent.setup();
    render(<SubmitSkillPage />, { wrapper });

    await user.type(screen.getByTestId('skill-name-input'), 'My Skill');
    await user.type(screen.getByTestId('skill-content-textarea'), 'Some content here');
    await user.click(screen.getByTestId('submit-skill-button'));

    await waitFor(() => {
      expect(screen.getByTestId('submission-status-tracker')).toBeDefined();
    });
  });

  it('shows error message on submit failure', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    localStorage.setItem('skillhub_token', token);

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'Name is required' }),
    });

    const user = userEvent.setup();
    render(<SubmitSkillPage />, { wrapper });

    await user.click(screen.getByTestId('submit-skill-button'));

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toContain('Name is required');
    });
  });
});
