import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAdminFeedback } from '../useAdminFeedback';

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
const mockPatch = vi.mocked(api.patch);

const FEEDBACK_RESPONSE = {
  items: [
    {
      id: 'fb-1',
      category: 'bug',
      sentiment: 'negative',
      body: 'This skill breaks on edge cases.',
      upvotes: 3,
      status: 'open',
      skill_name: 'Test Skill',
      created_at: '2026-01-15T10:00:00Z',
      user_display_name: 'Bob',
    },
    {
      id: 'fb-2',
      category: 'feature',
      sentiment: 'positive',
      body: 'Would love pagination support.',
      upvotes: 10,
      status: 'open',
      skill_name: null,
      created_at: '2026-01-16T12:00:00Z',
      user_display_name: 'Carol',
    },
  ],
  total: 2,
  page: 1,
  per_page: 20,
};

describe('useAdminFeedback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue(FEEDBACK_RESPONSE);
    mockPatch.mockResolvedValue(undefined);
  });

  it('fetches on mount with no filter params', async () => {
    const { result } = renderHook(() => useAdminFeedback({}));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/feedback', {});
    expect(result.current.data).toEqual(FEEDBACK_RESPONSE);
    expect(result.current.data?.items).toHaveLength(2);
  });

  it('passes category as query param when provided', async () => {
    const { result } = renderHook(() => useAdminFeedback({ category: 'bug' }));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/feedback', { category: 'bug' });
  });

  it('passes sentiment as query param when provided', async () => {
    const { result } = renderHook(() => useAdminFeedback({ sentiment: 'negative' }));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/feedback', { sentiment: 'negative' });
  });

  it('passes both category and sentiment as query params', async () => {
    const { result } = renderHook(() =>
      useAdminFeedback({ category: 'feature', sentiment: 'positive' }),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/feedback', {
      category: 'feature',
      sentiment: 'positive',
    });
  });

  it('passes page as query param when provided', async () => {
    const { result } = renderHook(() => useAdminFeedback({ page: 2 }));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/feedback', { page: 2 });
  });

  it('silently ignores fetch errors', async () => {
    mockGet.mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() => useAdminFeedback({}));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
  });

  it('archive(id) PATCHes status to archived', async () => {
    const { result } = renderHook(() => useAdminFeedback({}));

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.archive('fb-1');
    });

    expect(mockPatch).toHaveBeenCalledWith('/api/v1/admin/feedback/fb-1/status', {
      status: 'archived',
    });
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/feedback', {});
  });

  it('refetches when filter params change', async () => {
    const { result, rerender } = renderHook(
      ({ category }: { category?: string }) => useAdminFeedback({ category }),
      { initialProps: { category: undefined as string | undefined } },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    rerender({ category: 'bug' });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/feedback', { category: 'bug' });
  });
});
