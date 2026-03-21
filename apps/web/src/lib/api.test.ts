import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiFetch, ApiError } from './api';
import { setToken, clearToken, getToken } from './auth';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

// Mock location
const mockLocation = { href: '/' };
vi.stubGlobal('location', mockLocation);

describe('apiFetch', () => {
  beforeEach(() => {
    clearToken();
    mockFetch.mockReset();
    mockLocation.href = '/';
  });

  afterEach(() => {
    clearToken();
  });

  it('injects token when authenticated', async () => {
    setToken('my-token');
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'ok' }),
    });

    await apiFetch('/api/test');

    const [, init] = mockFetch.mock.calls[0];
    expect(init.headers['Authorization']).toBe('Bearer my-token');
  });

  it('does not inject token when not authenticated', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'ok' }),
    });

    await apiFetch('/api/test');

    const [, init] = mockFetch.mock.calls[0];
    expect(init.headers['Authorization']).toBeUndefined();
  });

  it('clears token on 401 response', async () => {
    setToken('expired-token');
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
    });

    await expect(apiFetch('/api/test')).rejects.toThrow(ApiError);
    expect(getToken()).toBeNull();
  });

  it('redirects to / on 401', async () => {
    setToken('expired-token');
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
    });

    await expect(apiFetch('/api/test')).rejects.toThrow();
    expect(mockLocation.href).toBe('/');
  });

  it('throws ApiError with detail on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: () => Promise.resolve({ detail: 'Skill not found' }),
    });

    await expect(apiFetch('/api/test')).rejects.toThrow('Skill not found');
  });

  it('returns parsed JSON on success', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ items: [], total: 0 }),
    });

    const result = await apiFetch<{ items: []; total: number }>('/api/test');
    expect(result.total).toBe(0);
  });

  it('builds URL with query params', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });

    await apiFetch('/api/skills', { params: { q: 'test', page: 2 } });

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain('q=test');
    expect(url).toContain('page=2');
  });

  it('handles array params', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });

    await apiFetch('/api/skills', {
      params: { divisions: ['Engineering Org', 'Product Org'] },
    });

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain('divisions=Engineering+Org');
    expect(url).toContain('divisions=Product+Org');
  });

  it('returns undefined for 204 responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    });

    const result = await apiFetch('/api/test', { method: 'DELETE' });
    expect(result).toBeUndefined();
  });
});
