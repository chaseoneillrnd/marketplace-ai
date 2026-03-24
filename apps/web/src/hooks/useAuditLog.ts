import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface AuditLogEntry {
  id: string;
  actor_name: string;
  action: string;
  from_status: string | null;
  to_status: string | null;
  notes: string | null;
  created_at: string;
}

interface AuditLogResponse {
  entries: AuditLogEntry[];
}

export function useAuditLog(displayId: string | null) {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!displayId) {
      setEntries([]);
      return;
    }
    setLoading(true);
    try {
      const result = await api.get<AuditLogResponse>(
        `/api/v1/submissions/${displayId}/audit-log`,
      );
      setEntries(result.entries);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit log');
    } finally {
      setLoading(false);
    }
  }, [displayId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { entries, loading, error, refresh };
}
