/**
 * Direct API helpers for test setup/teardown.
 * These bypass the UI to set up preconditions or verify backend state.
 */
import { APIRequestContext } from '@playwright/test';
import { API_BASE } from './test-data';

export interface ApiHelper {
  request: APIRequestContext;
  token: string;
}

/**
 * Get a JWT token for a stub user via the API.
 */
export async function getAuthToken(
  request: APIRequestContext,
  username: string,
  password = 'user',
): Promise<string> {
  const response = await request.post(`${API_BASE}/auth/token`, {
    data: { username, password },
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok()) {
    throw new Error(`Auth failed for ${username}: ${response.status()} ${await response.text()}`);
  }
  const body = await response.json();
  return body.access_token;
}

/**
 * Make an authenticated API GET request.
 */
export async function apiGet<T = unknown>(
  request: APIRequestContext,
  token: string,
  path: string,
): Promise<T> {
  const response = await request.get(`${API_BASE}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok()) {
    throw new Error(`API GET ${path} failed: ${response.status()}`);
  }
  return response.json() as Promise<T>;
}

/**
 * Make an authenticated API POST request.
 */
export async function apiPost<T = unknown>(
  request: APIRequestContext,
  token: string,
  path: string,
  data?: unknown,
): Promise<T> {
  const response = await request.post(`${API_BASE}${path}`, {
    data,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok()) {
    throw new Error(`API POST ${path} failed: ${response.status()}`);
  }
  if (response.status() === 204) return undefined as T;
  return response.json() as Promise<T>;
}

/**
 * Make an authenticated API DELETE request.
 */
export async function apiDelete(
  request: APIRequestContext,
  token: string,
  path: string,
): Promise<void> {
  const response = await request.delete(`${API_BASE}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok() && response.status() !== 404) {
    throw new Error(`API DELETE ${path} failed: ${response.status()}`);
  }
}
