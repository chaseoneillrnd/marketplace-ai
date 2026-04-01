import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAdminRoadmap } from '../useAdminRoadmap';

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

const ROADMAP_RESPONSE = {
  items: [
    {
      id: 'rm-1',
      title: 'Skill versioning',
      body: 'Support multiple versions of the same skill.',
      status: 'planned',
      created_at: '2026-01-10T00:00:00Z',
    },
    {
      id: 'rm-2',
      title: 'Batch import',
      body: 'Allow bulk skill imports via CSV.',
      status: 'shipped',
      created_at: '2026-01-05T00:00:00Z',
      shipped_at: '2026-02-01T00:00:00Z',
      version_tag: 'v1.2.0',
    },
  ],
};

describe('useAdminRoadmap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue(ROADMAP_RESPONSE);
    mockPost.mockResolvedValue(undefined);
  });

  it('fetches items on mount', async () => {
    const { result } = renderHook(() => useAdminRoadmap());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/platform-updates');
    expect(result.current.items).toEqual(ROADMAP_RESPONSE.items);
    expect(result.current.items).toHaveLength(2);
  });

  it('starts with empty items array', () => {
    mockGet.mockImplementation(() => new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useAdminRoadmap());
    expect(result.current.items).toEqual([]);
  });

  it('uses empty array when items key is missing from response', async () => {
    mockGet.mockResolvedValue({});

    const { result } = renderHook(() => useAdminRoadmap());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.items).toEqual([]);
  });

  it('silently ignores fetch errors', async () => {
    mockGet.mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() => useAdminRoadmap());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.items).toEqual([]);
  });

  it('createItem POSTs and refetches', async () => {
    const { result } = renderHook(() => useAdminRoadmap());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.createItem('New Feature', 'Description of new feature.');
    });

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/platform-updates', {
      title: 'New Feature',
      body: 'Description of new feature.',
    });
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/platform-updates');
  });

  it('shipItem POSTs ship payload with version_tag and changelog_body', async () => {
    const { result } = renderHook(() => useAdminRoadmap());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.shipItem('rm-1', 'v2.0.0', 'Released skill versioning support.');
    });

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/platform-updates/rm-1/ship', {
      version_tag: 'v2.0.0',
      changelog_body: 'Released skill versioning support.',
    });
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/platform-updates');
  });

  it('exposes refetch function', async () => {
    const { result } = renderHook(() => useAdminRoadmap());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/platform-updates');
  });
});
