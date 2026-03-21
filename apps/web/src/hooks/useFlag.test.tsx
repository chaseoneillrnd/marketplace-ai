import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AuthProvider } from '../context/AuthContext';
import { FlagsProvider } from '../context/FlagsContext';
import { useFlag, useFlags } from './useFlag';
import { clearToken } from '../lib/auth';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

function wrapper({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <FlagsProvider>{children}</FlagsProvider>
    </AuthProvider>
  );
}

const FLAGS_RESPONSE = {
  flags: {
    mcp_install_enabled: true,
    llm_judge_enabled: false,
    new_ui_enabled: true,
  },
};

describe('useFlag', () => {
  beforeEach(() => {
    clearToken();
    mockFetch.mockReset();
    // Default: return flags response for /flags endpoint
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/v1/flags')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(FLAGS_RESPONSE),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('returns false for disabled flag', async () => {
    const { result } = renderHook(() => useFlag('llm_judge_enabled'), { wrapper });
    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it('returns true for enabled flag', async () => {
    const { result } = renderHook(() => useFlag('mcp_install_enabled'), { wrapper });
    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });

  it('returns false for unknown flag key', async () => {
    const { result } = renderHook(() => useFlag('nonexistent_flag'), { wrapper });
    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it('FlagsProvider fetches on mount', async () => {
    renderHook(() => useFlags(), { wrapper });
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/flags'),
        expect.any(Object),
      );
    });
  });

  it('throws if used outside FlagsProvider', () => {
    // Wrap only in AuthProvider, not FlagsProvider
    function authOnlyWrapper({ children }: { children: ReactNode }) {
      return <AuthProvider>{children}</AuthProvider>;
    }
    expect(() => {
      renderHook(() => useFlag('any'), { wrapper: authOnlyWrapper });
    }).toThrow('useFlags must be used within a FlagsProvider');
  });
});
