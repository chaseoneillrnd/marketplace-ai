import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface VersionItem {
  id: string;
  version: string;
  changelog: string | null;
  published_at: string;
}

export function useSkillVersions(slug: string | undefined) {
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchVersions = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<VersionItem[]>(`/api/v1/skills/${slug}/versions`);
      setVersions(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load versions');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchVersions();
  }, [fetchVersions]);

  return { versions, loading, error, refetch: fetchVersions };
}
