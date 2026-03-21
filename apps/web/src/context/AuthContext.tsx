import { createContext, useCallback, useMemo, useState, type ReactNode } from 'react';
import type { UserClaims, TokenResponse } from '@skillhub/shared-types';
import { getToken, setToken, clearToken, decodeToken, isExpired } from '../lib/auth';
import { apiFetch } from '../lib/api';

export interface AuthContextValue {
  user: UserClaims | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserClaims | null>(() => {
    const token = getToken();
    if (token && !isExpired(token)) {
      return decodeToken(token);
    }
    return null;
  });

  const login = useCallback(async (username: string, password: string) => {
    const response = await apiFetch<TokenResponse>('/auth/token', {
      method: 'POST',
      body: { username, password },
    });
    setToken(response.access_token);
    const claims = decodeToken(response.access_token);
    setUser(claims);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      login,
      logout,
    }),
    [user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
