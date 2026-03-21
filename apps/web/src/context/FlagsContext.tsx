import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { FlagsResponse } from '@skillhub/shared-types';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';

export interface FlagsContextValue {
  flags: Record<string, boolean>;
  loading: boolean;
}

export const FlagsContext = createContext<FlagsContextValue | null>(null);

export function FlagsProvider({ children }: { children: ReactNode }) {
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuth();

  const fetchFlags = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get<FlagsResponse>('/api/v1/flags');
      setFlags(response.flags);
    } catch {
      // Flags fetch failure is non-fatal; default to empty
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch on mount and when auth state changes
  useEffect(() => {
    fetchFlags();
  }, [fetchFlags, isAuthenticated]);

  const value = useMemo<FlagsContextValue>(
    () => ({ flags, loading }),
    [flags, loading],
  );

  return <FlagsContext.Provider value={value}>{children}</FlagsContext.Provider>;
}
