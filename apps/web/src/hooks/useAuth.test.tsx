import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AuthProvider } from '../context/AuthContext';
import { useAuth } from './useAuth';
import { clearToken, getToken } from '../lib/auth';

// Mock fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

// Helper: create a fake JWT
function fakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.fakesig`;
}

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

const STUB_CLAIMS = {
  user_id: '00000000-0000-0000-0000-000000000001',
  email: 'test@skillhub.dev',
  name: 'Test User',
  username: 'test',
  division: 'Engineering Org',
  role: 'Senior Engineer',
  is_platform_team: false,
  is_security_team: false,
  iat: Math.floor(Date.now() / 1000),
  exp: Math.floor(Date.now() / 1000) + 3600,
};

describe('useAuth', () => {
  beforeEach(() => {
    clearToken();
    mockFetch.mockReset();
  });

  it('starts as unauthenticated', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('login sets isAuthenticated=true', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ access_token: token, token_type: 'bearer' }),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('test', 'user');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.name).toBe('Test User');
    expect(result.current.user?.division).toBe('Engineering Org');
    expect(getToken()).toBe(token);
  });

  it('logout clears auth state', async () => {
    const token = fakeJwt(STUB_CLAIMS);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ access_token: token, token_type: 'bearer' }),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('test', 'user');
    });
    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(getToken()).toBeNull();
  });

  it('throws when used outside AuthProvider', () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');
  });
});
