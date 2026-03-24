import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAdminQueue } from '../useAdminQueue';

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

const QUEUE_RESPONSE = {
  items: [
    {
      submission_id: 'sub-1',
      display_id: 'SKILL-001',
      skill_name: 'Test Skill',
      short_desc: 'A test skill',
      category: 'productivity',
      submitter_name: 'Alice',
      submitted_at: '2026-01-01T00:00:00Z',
      gate1_passed: true,
      gate2_score: 85,
      gate2_summary: 'Looks good',
      content_preview: '# Test Skill',
      wait_time_hours: 2,
      divisions: ['Engineering'],
      revision_number: 1,
      status: 'pending_review',
    },
  ],
  total: 1,
  page: 1,
  per_page: 20,
  has_more: false,
};

describe('useAdminQueue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue(QUEUE_RESPONSE);
    mockPost.mockResolvedValue(undefined);
  });

  it('fetches queue on mount and returns data', async () => {
    const { result } = renderHook(() => useAdminQueue());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/review-queue');
    expect(result.current.data).toEqual(QUEUE_RESPONSE);
    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].skill_name).toBe('Test Skill');
    expect(result.current.error).toBeNull();
  });

  it('sets error when fetch fails', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAdminQueue());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.data).toBeNull();
  });

  it('sets generic error message for non-Error failures', async () => {
    mockGet.mockRejectedValue('something went wrong');

    const { result } = renderHook(() => useAdminQueue());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to load queue');
  });

  it('claim() POSTs to correct endpoint and refetches', async () => {
    const { result } = renderHook(() => useAdminQueue());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();
    mockPost.mockResolvedValue(undefined);

    await act(async () => {
      await result.current.claim('sub-1');
    });

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/review-queue/sub-1/claim');
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/review-queue');
  });

  it('decide() POSTs correct payload and refetches', async () => {
    const { result } = renderHook(() => useAdminQueue());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();
    mockPost.mockResolvedValue(undefined);

    await act(async () => {
      await result.current.decide('sub-1', 'approve', 'Great skill', 90);
    });

    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/admin/review-queue/sub-1/decision',
      { decision: 'approve', notes: 'Great skill', score: 90 },
    );
    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/review-queue');
  });

  it('decide() uses empty string default for notes and undefined for score', async () => {
    const { result } = renderHook(() => useAdminQueue());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockPost.mockResolvedValue(undefined);

    await act(async () => {
      await result.current.decide('sub-2', 'reject');
    });

    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/admin/review-queue/sub-2/decision',
      { decision: 'reject', notes: '', score: undefined },
    );
  });

  it('exposes refetch function', async () => {
    const { result } = renderHook(() => useAdminQueue());

    await waitFor(() => expect(result.current.loading).toBe(false));

    mockGet.mockClear();

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/review-queue');
  });
});
