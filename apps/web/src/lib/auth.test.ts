import { describe, it, expect, beforeEach } from 'vitest';
import { getToken, setToken, clearToken, decodeToken, isExpired } from './auth';

// Helper: create a fake JWT with the given payload
function fakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload));
  const sig = 'fakesignature';
  return `${header}.${body}.${sig}`;
}

describe('auth token management', () => {
  beforeEach(() => {
    clearToken();
  });

  it('getToken returns null initially', () => {
    expect(getToken()).toBeNull();
  });

  it('setToken stores and getToken retrieves', () => {
    setToken('abc123');
    expect(getToken()).toBe('abc123');
  });

  it('clearToken removes the token', () => {
    setToken('abc123');
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe('decodeToken', () => {
  it('parses JWT claims correctly', () => {
    const payload = {
      user_id: '00000000-0000-0000-0000-000000000001',
      email: 'test@skillhub.dev',
      name: 'Test User',
      username: 'test',
      division: 'Engineering Org',
      role: 'Senior Engineer',
      is_platform_team: false,
      is_security_team: false,
      iat: 1700000000,
      exp: 1700003600,
    };
    const token = fakeJwt(payload);
    const claims = decodeToken(token);

    expect(claims.user_id).toBe('00000000-0000-0000-0000-000000000001');
    expect(claims.email).toBe('test@skillhub.dev');
    expect(claims.name).toBe('Test User');
    expect(claims.division).toBe('Engineering Org');
    expect(claims.is_platform_team).toBe(false);
  });

  it('throws on invalid JWT format', () => {
    expect(() => decodeToken('not.valid')).toThrow('Invalid JWT format');
    expect(() => decodeToken('single')).toThrow('Invalid JWT format');
  });
});

describe('isExpired', () => {
  it('returns true for past exp', () => {
    const token = fakeJwt({ exp: Math.floor(Date.now() / 1000) - 3600 });
    expect(isExpired(token)).toBe(true);
  });

  it('returns false for future exp', () => {
    const token = fakeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 });
    expect(isExpired(token)).toBe(false);
  });

  it('returns true for invalid token', () => {
    expect(isExpired('garbage')).toBe(true);
  });
});
