import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAdminFlags } from '../useAdminFlags';

vi.mock('../../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { api } from '../../lib/api';

const mockGet = vi.mocked(api.get);
const mockPost = vi.mocked(api.post);
const mockPatch = vi.mocked(api.patch);
const mockDelete = vi.mocked(api.delete);

const FLAGS_DATA = [
  {
    key: 'llm_judge_enabled',
    enabled: true,
    description: 'Enables LLM judge',
    division_overrides: null,
  },
  {
    key: 'new_ui_enabled',
    enabled: false,
    description: null,
    division_overrides: { Engineering: true },
  },
];

describe('useAdminFlags', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue(FLAGS_DATA);
    mockPost.mockResolvedValue(undefined);
    mockPatch.mockResolvedValue(undefined);
    mockDelete.mockResolvedValue(undefined);
  });

  it('loads flags on mount', async () => {
    const { result } = renderHook(() => useAdminFlags());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/flags');
    expect(result.current.flags).toEqual(FLAGS_DATA);
    expect(result.current.flags).toHaveLength(2);
  });

  it('starts with empty flags array', () => {
    mockGet.mockImplementation(() => new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useAdminFlags());
    expect(result.current.flags).toEqual([]);
  });

  it('silently ignores fetch errors', async () => {
    mockGet.mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() => useAdminFlags());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.flags).toEqual([]);
  });

  it('createFlag POSTs and refetches', async () => {
    const { result } = renderHook(() => useAdminFlags());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.createFlag({ key: 'my_flag', enabled: true, description: 'My flag' });
    });

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/flags', {
      key: 'my_flag',
      enabled: true,
      description: 'My flag',
    });
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/flags');
  });

  it('createFlag POSTs without optional description', async () => {
    const { result } = renderHook(() => useAdminFlags());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.createFlag({ key: 'bare_flag', enabled: false });
    });

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/flags', {
      key: 'bare_flag',
      enabled: false,
    });
  });

  it('updateFlag PATCHes correct key', async () => {
    const { result } = renderHook(() => useAdminFlags());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.updateFlag('llm_judge_enabled', { enabled: false });
    });

    expect(mockPatch).toHaveBeenCalledWith('/api/v1/admin/flags/llm_judge_enabled', {
      enabled: false,
    });
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/flags');
  });

  it('updateFlag PATCHes with division_overrides', async () => {
    const { result } = renderHook(() => useAdminFlags());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.updateFlag('new_ui_enabled', {
        enabled: true,
        division_overrides: { Engineering: true, Sales: false },
      });
    });

    expect(mockPatch).toHaveBeenCalledWith('/api/v1/admin/flags/new_ui_enabled', {
      enabled: true,
      division_overrides: { Engineering: true, Sales: false },
    });
  });

  it('deleteFlag DELETEs and refetches', async () => {
    const { result } = renderHook(() => useAdminFlags());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.deleteFlag('llm_judge_enabled');
    });

    expect(mockDelete).toHaveBeenCalledWith('/api/v1/admin/flags/llm_judge_enabled');
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/flags');
  });
});
