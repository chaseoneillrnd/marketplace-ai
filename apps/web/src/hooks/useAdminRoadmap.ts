import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface RoadmapItem {
  id: string;
  title: string;
  body: string;
  status: string;
  created_at: string;
  shipped_at?: string;
  version_tag?: string;
}

export interface RoadmapResponse {
  items: RoadmapItem[];
}

export function useAdminRoadmap() {
  const [items, setItems] = useState<RoadmapItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.get<RoadmapResponse>('/api/v1/admin/platform-updates');
      setItems(result.items || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const createItem = useCallback(async (title: string, body: string) => {
    await api.post('/api/v1/admin/platform-updates', { title, body });
    await fetchData();
  }, [fetchData]);

  const shipItem = useCallback(async (id: string, versionTag: string, changelogBody: string) => {
    await api.post(`/api/v1/admin/platform-updates/${id}/ship`, {
      version_tag: versionTag,
      changelog_body: changelogBody,
    });
    await fetchData();
  }, [fetchData]);

  return { items, loading, refetch: fetchData, createItem, shipItem };
}
