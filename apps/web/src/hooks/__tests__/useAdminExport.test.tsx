import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAdminExport } from '../useAdminExport';

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

describe('useAdminExport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts with correct remaining exports count of 5', () => {
    const { result } = renderHook(() => useAdminExport());

    expect(result.current.remainingExports).toBe(5);
    expect(result.current.exportStatus).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('requestExport posts correct body and decrements remainingExports', async () => {
    const exportStatusPending = {
      id: 'export-1',
      status: 'complete' as const,
      download_url: 'https://example.com/export.csv',
    };

    mockPost.mockResolvedValue(exportStatusPending);

    const { result } = renderHook(() => useAdminExport());

    await act(async () => {
      await result.current.requestExport({
        scope: 'all_skills',
        format: 'csv',
        start_date: '2026-01-01',
        end_date: '2026-03-01',
      });
    });

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/exports', {
      scope: 'all_skills',
      format: 'csv',
      start_date: '2026-01-01',
      end_date: '2026-03-01',
    });

    expect(result.current.exportStatus).toEqual(exportStatusPending);
    expect(result.current.remainingExports).toBe(4);
    expect(result.current.loading).toBe(false);
  });

  it('requestExport posts body without optional date fields', async () => {
    mockPost.mockResolvedValue({
      id: 'export-2',
      status: 'complete' as const,
    });

    const { result } = renderHook(() => useAdminExport());

    await act(async () => {
      await result.current.requestExport({ scope: 'my_skills', format: 'json' });
    });

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/exports', {
      scope: 'my_skills',
      format: 'json',
    });
  });

  it('polling stops when status is complete', async () => {
    const pendingStatus = { id: 'export-3', status: 'pending' as const };
    const completeStatus = {
      id: 'export-3',
      status: 'complete' as const,
      download_url: 'https://example.com/file.csv',
    };

    mockPost.mockResolvedValue(pendingStatus);
    mockGet.mockResolvedValueOnce({ ...pendingStatus, status: 'processing' as const });
    mockGet.mockResolvedValueOnce(completeStatus);

    const { result } = renderHook(() => useAdminExport());

    await act(async () => {
      await result.current.requestExport({ scope: 'all_skills', format: 'csv' });
    });

    // Status is pending — polling should have started
    expect(result.current.exportStatus?.status).toBe('pending');

    // Advance timer for first poll (processing)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/v1/admin/exports/export-3');
    expect(result.current.exportStatus?.status).toBe('processing');

    // Advance timer for second poll (complete)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.exportStatus).toEqual(completeStatus);

    // Advance again — no further poll calls expected
    mockGet.mockClear();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('polling stops when status is failed', async () => {
    const pendingStatus = { id: 'export-4', status: 'pending' as const };
    const failedStatus = { id: 'export-4', status: 'failed' as const };

    mockPost.mockResolvedValue(pendingStatus);
    mockGet.mockResolvedValue(failedStatus);

    const { result } = renderHook(() => useAdminExport());

    await act(async () => {
      await result.current.requestExport({ scope: 'all_skills', format: 'csv' });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(result.current.exportStatus?.status).toBe('failed');

    mockGet.mockClear();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('does not start polling when initial status is complete', async () => {
    mockPost.mockResolvedValue({
      id: 'export-5',
      status: 'complete' as const,
      download_url: 'https://example.com/file.csv',
    });

    const { result } = renderHook(() => useAdminExport());

    await act(async () => {
      await result.current.requestExport({ scope: 'all_skills', format: 'csv' });
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mockGet).not.toHaveBeenCalled();
    expect(result.current.exportStatus?.status).toBe('complete');
  });

  it('remainingExports decrements on each requestExport call', async () => {
    mockPost.mockResolvedValue({ id: 'e', status: 'complete' as const });

    const { result } = renderHook(() => useAdminExport());

    expect(result.current.remainingExports).toBe(5);

    await act(async () => {
      await result.current.requestExport({ scope: 'all_skills', format: 'csv' });
    });
    expect(result.current.remainingExports).toBe(4);

    await act(async () => {
      await result.current.requestExport({ scope: 'all_skills', format: 'csv' });
    });
    expect(result.current.remainingExports).toBe(3);
  });

  it('remainingExports does not go below 0', async () => {
    mockPost.mockResolvedValue({ id: 'e', status: 'complete' as const });

    const { result } = renderHook(() => useAdminExport());

    // Exhaust all 5 exports
    for (let i = 0; i < 6; i++) {
      await act(async () => {
        await result.current.requestExport({ scope: 'all_skills', format: 'csv' });
      });
    }

    expect(result.current.remainingExports).toBe(0);
  });
});
