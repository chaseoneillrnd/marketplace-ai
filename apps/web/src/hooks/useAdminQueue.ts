import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export interface ReviewQueueItem {
  submission_id: string;
  display_id: string | null;
  skill_name: string;
  short_desc: string;
  category: string;
  submitter_name: string | null;
  submitted_at: string | null;
  gate1_passed: boolean;
  gate2_score: number | null;
  gate2_summary: string | null;
  content_preview: string;
  wait_time_hours: number;
  divisions: string[];
}

export interface QueueResponse {
  items: ReviewQueueItem[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export function useAdminQueue() {
  const [data, setData] = useState<QueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.get<QueueResponse>('/api/v1/admin/review-queue');
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const claim = useCallback(async (id: string) => {
    await api.post(`/api/v1/admin/review-queue/${id}/claim`);
    await fetchQueue();
  }, [fetchQueue]);

  const decide = useCallback(async (id: string, decision: string, notes: string = '', score?: number) => {
    await api.post(`/api/v1/admin/review-queue/${id}/decision`, { decision, notes, score });
    await fetchQueue();
  }, [fetchQueue]);

  return { data, loading, error, refetch: fetchQueue, claim, decide };
}
