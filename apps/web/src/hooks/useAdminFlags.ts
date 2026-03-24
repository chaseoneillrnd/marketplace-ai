import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface AdminFlag {
  key: string;
  enabled: boolean;
  description: string | null;
  division_overrides: Record<string, boolean> | null;
}

export interface AuditEntry {
  id: string;
  event_type: string;
  actor_id: string | null;
  target_id: string | null;
  metadata_: Record<string, unknown> | null;
  created_at: string;
}

export function useAdminFlags() {
  const [flags, setFlags] = useState<AdminFlag[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFlags = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.get<AdminFlag[]>('/api/v1/admin/flags');
      setFlags(result);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFlags();
  }, [fetchFlags]);

  const createFlag = useCallback(async (data: { key: string; enabled: boolean; description?: string }) => {
    await api.post('/api/v1/admin/flags', data);
    await fetchFlags();
  }, [fetchFlags]);

  const updateFlag = useCallback(async (key: string, data: Partial<Pick<AdminFlag, 'enabled' | 'description' | 'division_overrides'>>) => {
    await api.patch(`/api/v1/admin/flags/${key}`, data);
    await fetchFlags();
  }, [fetchFlags]);

  const deleteFlag = useCallback(async (key: string) => {
    await api.delete(`/api/v1/admin/flags/${key}`);
    await fetchFlags();
  }, [fetchFlags]);

  return { flags, loading, refetch: fetchFlags, createFlag, updateFlag, deleteFlag };
}
