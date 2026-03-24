import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AuthProvider } from '../../../context/AuthContext';
import { SubmitSkillPage } from '../SubmitSkillPage';
import { setToken, clearToken } from '../../../lib/auth';

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

const MOCK_DIVISIONS = [
  { name: 'Engineering Org', slug: 'engineering-org', color: '#4b7dff' },
  { name: 'Data Science Org', slug: 'data-science-org', color: '#8b5cf6' },
];

function mockApi(overrides: Record<string, unknown> = {}) {
  mockFetch.mockImplementation(async (url: string) => {
    const path = typeof url === 'string' ? url : '';
    if (path.includes('/api/v1/divisions')) {
      return { ok: true, status: 200, json: async () => MOCK_DIVISIONS };
    }
    if (path.includes('/api/v1/flags')) {
      return { ok: true, status: 200, json: async () => [] };
    }
    if (overrides[path]) {
      return overrides[path];
    }
    return { ok: true, status: 200, json: async () => ({}) };
  });
}

describe('SubmitSkillPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearToken();
    mockApi();
  });

  it('shows sign-in required when not authenticated', () => {
    render(<SubmitSkillPage />, { wrapper });
    expect(screen.getByText('Sign in required')).toBeDefined();
  });

  it('renders ModeSelector tabs when authenticated', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    setToken(token);

    render(<SubmitSkillPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('mode-tab-form')).toBeDefined();
    });
    expect(screen.getByTestId('mode-tab-upload')).toBeDefined();
    expect(screen.getByTestId('mode-tab-mcp')).toBeDefined();
  });

  it('shows form builder by default', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    setToken(token);

    render(<SubmitSkillPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('form-builder-mode')).toBeDefined();
    });
    expect(screen.getByTestId('input-name')).toBeDefined();
  });

  it('switches to upload mode on tab click', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    setToken(token);
    const user = userEvent.setup();

    render(<SubmitSkillPage />, { wrapper });
    await waitFor(() => {
      expect(screen.getByTestId('mode-tab-upload')).toBeDefined();
    });
    await user.click(screen.getByTestId('mode-tab-upload'));

    expect(screen.getByTestId('file-upload-mode')).toBeDefined();
  });

  it('switches to MCP mode on tab click', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    setToken(token);
    const user = userEvent.setup();

    render(<SubmitSkillPage />, { wrapper });
    await waitFor(() => {
      expect(screen.getByTestId('mode-tab-mcp')).toBeDefined();
    });
    await user.click(screen.getByTestId('mode-tab-mcp'));

    expect(screen.getByTestId('mcp-sync-mode')).toBeDefined();
  });

  it('renders step indicator and first step of form', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    setToken(token);

    render(<SubmitSkillPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('step-indicator')).toBeDefined();
    });
    expect(screen.getByTestId('input-name')).toBeDefined();
    expect(screen.getByTestId('input-description')).toBeDefined();
  });

  it('navigates to next step after filling name and description', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    setToken(token);
    const user = userEvent.setup();

    render(<SubmitSkillPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('input-name')).toBeDefined();
    });
    await user.type(screen.getByTestId('input-name'), 'My Skill');
    await user.type(screen.getByTestId('input-description'), 'A short description');
    await user.click(screen.getByTestId('btn-next'));

    await waitFor(() => {
      expect(screen.getByTestId('input-content')).toBeDefined();
    });
  });
});
