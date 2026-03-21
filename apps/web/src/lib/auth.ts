/**
 * Token management — memory-only storage.
 * Never stores tokens in localStorage/sessionStorage.
 */
import type { UserClaims } from '@skillhub/shared-types';

let _token: string | null = null;

export function getToken(): string | null {
  return _token;
}

export function setToken(token: string): void {
  _token = token;
}

export function clearToken(): void {
  _token = null;
}

/**
 * Decode a JWT token's payload without verification.
 * The server is the source of truth for validation.
 */
export function decodeToken(token: string): UserClaims {
  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid JWT format');
  }
  const payload = parts[1];
  const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
  return JSON.parse(decoded) as UserClaims;
}

/**
 * Check if a JWT token is expired based on the exp claim.
 */
export function isExpired(token: string): boolean {
  try {
    const claims = decodeToken(token);
    const now = Math.floor(Date.now() / 1000);
    return claims.exp <= now;
  } catch {
    return true;
  }
}
